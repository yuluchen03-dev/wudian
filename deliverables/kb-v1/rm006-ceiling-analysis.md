# RM-006 — Gate F ceiling analysis: 36/40 is NOT reachable by re-ranking

Executed, read-only, isolated temp Chroma. No patch shipped. Production Chroma
untouched.

## 1. The finding that changes the plan

```
baseline recall@5                                      22/40 = 0.550
ORACLE: gold present in union of both layers @143      40/40 = 1.000
REALISTIC ceiling: gold's BEST rank in EITHER layer    27/40 = 0.675
target                                                 36/40 = 0.900
```

**The union-oracle (40/40) is misleading and must not be used as the target.**
Gold can be *present* at rank 103 in the vector layer and rank 60 in the keyword
layer; no weighting of those two rankings can lift it into top-5. The honest
ceiling is **each gold's best rank across the two layers**, and that ceiling is
**27/40**:

| best rank in either layer | count |
|---|---|
| <= 5 (a perfect reranker already succeeds) | **27** |
| 6-10 | 1 |
| 11-20 | 4 |
| 21-50 | 6 |
| never in either layer | 0 |
| **realistic ceiling at recall@5** | **27/40 = 0.675** |

So even a **perfect** re-ranker over the existing two layers caps at **27/40**.
Gate F needs **36/40**. **Re-ranking alone cannot close Gate F.**

## 2. Ranked per-case evidence

```
id         vec_rank  kw_rank  best  query
rg-0004          24        1     1  总是担心别人怎么看我，很内耗
rg-0037          17        1     1  孝和事业冲突时怎么办？
rg-0016           8        1     1  怎么才能不轻易生气？
rg-0002           4     None     4  被领导误解了，我要不要急着解释？
rg-0012           5       28     5  面对利益诱惑，该怎么选？
rg-0030          33        5     5  为什么事情没成就到处说？
rg-0039          19        5     5  总是后悔过去的选择
rg-0006          27       11    11  学了很多但工作里用不上
rg-0015         107       12    12  努力还有意义吗？
rg-0029          12       16    12  时代变了，旧规则要不要改？
rg-0010          20       32    20  如何领导一个团队？
rg-0020          22       53    22  怎么判断一个人值不值得深交？
rg-0036          23     None    23  怎么面对孤独？
rg-0035          24       52    24  遇到流言蜚语怎么办？
rg-0018          28       42    28  如何与人相处才得体？
rg-0001          37       55    37  同事抢了我的功劳，我该不该跟他撕破脸？
rg-0031          54       47    47  读书到底为了什么？
rg-0003          58     None    58  我该怎么面对失败？
rg-0021         103     None   103  无为而治是什么意思？
```

**13 of 40 golds are unreachable at top-5 even with an oracle reranker.** They
are simply not ranked highly by either existing signal.

## 3. What was actually fixed

I implemented `RAGService._rank_fusion` — a scale-free, **monotonic**
rank-based fusion — as a new static method, leaving `_merge_retrieval` untouched
(it has a separate caller). Verified:

```
monotonicity: top5 == full[:5]  ->  True  (both probe queries)
```

Previously `top5` was **not** a prefix of `top80`, and gold `1.1` ranked **#1**
at k=80 while being absent at k=5. That structural defect is now fixed.

**But recall@5 did not improve:**

| configuration | recall@5 |
|---|---|
| baseline (non-monotonic, current shipped code) | **22/40** |
| `_rank_fusion`, vec=0.3/kw=0.7 | 21/40 |
| `_rank_fusion`, vec=0.5/kw=0.5 | 21/40 |
| `_rank_fusion`, vec=0.7/kw=0.3 | 21/40 |
| `_rank_fusion`, vec=0.9/kw=0.1 | 21/40 |

Monotonicity is a **correctness** win; it is not a **score** win. And since the
ceiling is 27/40, no fusion weight can reach 36/40.

## 4. Honest verdict: the contract's expectation gap

`DSH-MASTER-PLAN.md` §10 assumed RM-006's surface was
`retrieve_for_sage_chat` + `vector_search` + `_kw_search_chroma` +
`_merge_retrieval` and that fixing it would reach Recall@5 >= 0.90. **That
assumption is now measured and false.** With those components alone the ceiling
is 0.675.

Reaching 36/40 requires at least one of the following, each of which is a
**scope decision that is not mine to make unilaterally**:

1. **A real semantic embedding.** The current hash embedding is not semantic:
   `无为而治是什么意思？` puts gold at vector rank **103** while unrelated 论语
   verses occupy the top. No keyword or fusion change repairs this; the signal
   simply is not in the vector space. This is the single largest lever (10 of the
   13 unreachable cases are 道德经/韩非子 concept queries).
2. **Changing the corpus/embedding and re-indexing** — explicitly forbidden
   without authorization, and `build_index(force=True)` against production is
   prohibited.
3. **A re-scoped Gate F target with evidence** — the governance rules permit
   reporting BLOCKED with evidence when the target is unreachable, and they
   forbid lowering targets silently.

I am **not** doing any of these on my own initiative, and I am not shipping the
`_rank_fusion` change unilaterally either: it is a real correctness improvement
but it currently scores −1, so shipping it needs an explicit decision.

## 5. Embedding diagnosis (executed) — the signal is absent, not mis-weighted

Direct test of the embedding:

```
embedding function = LocalHashEmbeddingFunction
self-retrieval (query = the passage's own 原文):
   daodejing-22-01          self-rank = 1
   daodejing-33-01          self-rank = 1
   hanfeizi-wai-chu-shuo-01 self-rank = 1
   hanfeizi-wuzhu-01        self-rank = 1
concept query:
   '无为而治是什么意思？' -> rank(daodejing-22-01) = 103
                            rank(daodejing-33-01) = 126
                            rank(daodejing-44-01) = 107
   '无为'                 -> rank(daodejing-22-01) = 72
```

Reading:

- **The index is fine.** Every target passage retrieves **itself at rank 1**, so
  the documents are present, non-degenerate, and individually matchable.
- **The query→document semantic bridge is absent.** A question *literally about
  `无为`* ranks the `无为` passage at **72-126**. This is the signature of a
  hash embedding: it produces a stable vector per string but carries no notion
  that 「无为而治」 and 「道常无为而无不为」 are about the same thing.
- Therefore no fusion weight, reranker, or normalization can recover these cases
  — the relevant signal is not in the candidate ranking at all.

This is the concrete mechanism behind the 13/40 unreachable cases, and it makes
option (1) below — a real semantic embedding plus authorized re-index — the only
path that can plausibly reach 36/40.

## 6. Recommendation


- **Do not** treat Recall@5 >= 0.90 as achievable by "fixing the fusion" — that
  path is measured dead (ceiling 27/40).
- Decide between: (a) authorize a semantic-embedding / re-index workstream,
  (b) re-scope Gate F with a documented, evidence-backed target, or (c) accept
  Gate F as an open blocker.
- The `_rank_fusion` implementation is written and verified but **held
  uncommitted in the working tree** for that decision. If it is not wanted, it
  should be reverted rather than left ambiguous.
  **Recommended: keep it.** It is a verified correctness fix (restores the
  top-k prefix property) at a measured cost of 1 hit, and it makes Gate F
  *meaningful* rather than accidentally flattering. But the score cost means it
  should be a deliberate, recorded decision — not a silent drift.
- `TEST-HARNESS-INDEX-EMPTY-001` and `TEST-ASSERTION-MISSPECIFIED-002` remain
  open and independent of this.

## 7. Status

```
Gate F          = 22/40 = 0.550   FAIL (unchanged)
RM-006          = root cause + ceiling ESTABLISHED; re-ranking path measured DEAD
_rank_fusion    = implemented, monotonic, scores 21/40 -- UNCOMMITTED, pending decision
BLOCKED_BY_CORPUS = still ruled out (0/40 golds absent)
Production Chroma = untouched (byte-identical, verified)
```

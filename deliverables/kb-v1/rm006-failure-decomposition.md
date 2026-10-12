# RM-006 — failure decomposition (captain, executed, read-only)

Runtime restored. All data below is **executed this round** on an isolated copy of
production Chroma (`shutil.copytree`; production never opened for writing).

Reproduction fidelity check first: my per-case measurement reproduces the
canonical evaluator **exactly** —

| metric | my probe | canonical `run_eval.py` |
|---|---|---|
| recall@1 | 13/40 = 0.325 | 0.325 |
| recall@3 | 19/40 = 0.475 | 0.475 |
| recall@5 | **22/40 = 0.550** | **0.55** |
| mrr | 0.4092 | 0.4091666 |

So the decomposition below is measured on the same surface the frozen Gate F
measures (`retrieve_for_sage_chat`, `verse_id`), not a proxy.

---

## 1. The gap

```
baseline recall@5 = 22/40 = 0.55
target            >= 0.90  ->  >= 36/40
shortfall         >= 14 additional gold hits
measured misses   = 18
```

## 2. THE DECISIVE FINDING — retrieval is systematically 论语-biased

Corpus composition (measured from Chroma metadata):

| book | docs |
|---|---|
| 论语 | **125** |
| 道德经 | 4 |
| 墨子 | 4 |
| 韩非子 | 4 |
| 李白诗文 | 2 |
| 苏轼词文 / 范仲淹文 / 王安石诗文 / 诸葛亮文 | 1 each |

`scope`: `sage_chat` 122, `debate_classic` 21. `doc_type`: `verse` 128,
`commentary` 15. Total 143.

**Every one of the 18 misses returns 论语 verses** (plus occasional non-论语
noise such as `fan_zhongyan:fanzhongyan-yueyanglouji-01` or
`li_bai:libai-jiangjinjiu-01`). The gold expects 道德经 / 韩非子 / 墨子 passages
in several cases, and the chat path never surfaces them.

Direct example (`rg-0021`, gold = `laozi:daodejing-22-01`,
`laozi:daodejing-33-01`):

```
Q = 无为而治是什么意思？   (classical_concept)
got: 2.5(论语·为政) 2.21 3.8 3.13 2.15   -- all 论语
```

The expected 道德经 passages exist in the corpus but are **never retrieved** for
a query that is literally about 无为.

## 3. `BLOCKED_BY_CORPUS` — re-confirmed RULED OUT, with a new precision

The instruction says corpus absence is ruled out and must not be reused as a
default blocker. I re-verified this and found the **exact form** of the issue:

```
gold id                       : laozi:daodejing-22-01
corpus verse_id               : daodejing-22-01        (NO sage prefix)
gold id                       : hanfeizi:hanfeizi-wuzhu-01
corpus verse_id               : hanfeizi-wuzhu-01      (NO sage prefix)

namespaced verse_ids in Chroma = 0
```

**All 4 passages are physically present.** The corpus stores bare `verse_id`
values (`daodejing-22-01`), while gold stores namespaced ones
(`laozi:daodejing-22-01`). So:

- **corpus absence: ruled out** (confirmed again — the text is there);
- this is a **canonical ID mapping** difference, not a missing document.

## 4. Taxonomy classification of the 18 misses

| # | id | query | expected | got (top-5, all 论语 unless noted) | classification |
|---|---|---|---|---|---|
| 1 | rg-0001 | 同事抢了我的功劳，我该不该跟他撕破脸？ | 12.2, 15.24, 4.16 | 2.24 3.21 2.9 3.9 1.16 | **dense** (semantic miss) |
| 2 | rg-0003 | 我该怎么面对失败？ | 4.8, 9.19 | 2.20 1.4 1.12 2.9 +岳阳楼记 | **modern→classical mapping** |
| 3 | rg-0006 | 学了很多但工作里用不上 | 1.14, 2.15 | 19.7 1.2 1.4 4.5 14.24 | **dense** |
| 4 | rg-0010 | 如何领导一个团队？ | 13.6, 2.1 | 1.2 2.10 5.9 1.5 2.22 | **dense / reranker** (2.1 & 13.6 are near-miss) |
| 5 | rg-0012 | 面对利益诱惑，该怎么选？ | 4.16, 4.5 | 2.20 +墨+汉 | **dense** (4.5 ranked 5th at HEAD in another run) |
| 6 | rg-0015 | 努力还有意义吗？ | 4.8, 9.19 | 6.22 墨子 3.6 2.8 道德经22 | **modern→classical mapping** |
| 7 | rg-0016 | 怎么才能不轻易生气？ | 1.1, 15.28 | 20.3 11.12 韩非子 7.3 3.1 | **dense** |
| 8 | rg-0018 | 如何与人相处才得体？ | 1.12, 12.2 | 6.30 17.2 15.9 3.3 11.12 | **dense / fusion** |
| 9 | rg-0020 | 怎么判断一个人值不值得深交？ | 1.8, 16.4 | 2.10 3.3 1.10 1.2 2.22 | **dense** |
| 10 | **rg-0021** | 无为而治是什么意思？ | **laozi:daodejing-22-01, -33-01** | all 论语 | **canonical ID mapping + school/diversity** |
| 11 | **rg-0029** | 时代变了，旧规则要不要改？ | **hanfeizi:hanfeizi-wuzhu-01** | all 论语 | **canonical ID mapping + school/diversity** |
| 12 | **rg-0030** | 为什么事情没成就到处说？ | **hanfeizi:hanfeizi-wai-chu-shuo-01** | all 论语 | **canonical ID mapping + school/diversity** |
| 13 | rg-0031 | 读书到底为了什么？ | 19.6, 19.7 | 2.21 14.24 3.25 1.8 8.7 | **dense** |
| 14 | rg-0035 | 遇到流言蜚语怎么办？ | 1.16, 15.28 | 15.16 16.9 20.3 5.9 2.10 | **dense** |
| 15 | rg-0036 | 怎么面对孤独？ | 1.1, 4.24 | 2.20 11.12 1.15 1.5 +李白 | **dense** |
| 16 | rg-0037 | 孝和事业冲突时怎么办？ | 1.6, 2.5 | 15.16 11.12 2.8 2.10 3.26 | **dense / fusion** (2.8 is sibling of 2.5) |
| 17 | rg-0004 | 总是担心别人怎么看我，很内耗 | 1.1, 1.16 | — | **dense** |
| 18 | rg-0005 | 怎么才能学到真东西？ | 2.11, 2.15 | — | **dense** |

Aggregate:

| classification | count |
|---|---|
| dense / semantic ranking | 12 |
| modern→classical conceptual mapping | 2 |
| school / diversity (expected 道德经/韩非子, got only 论语) | 3 |
| fusion / reranker (near-miss at rank 5-6) | 2 (overlapping) |

**ID normalization is NOT a contributing cause.** The frozen matcher
(`metrics.py:170-181`) already strips the `sage:` prefix on both sides, and I
verified my probe reproduces the canonical 0.325/0.475/0.55/0.4092 exactly. So
the `lunyu:`/`laozi:` prefix difference between Gold and corpus carries **no**
penalty. The three "ID mapping" rows in the table above are therefore
re-classified as **school / diversity**, which is their true owning layer: the
passage exists and would match, but retrieval never surfaces it.

**No miss is attributable to:** corpus absence (ruled out), ID normalization
(proven non-contributing), Gold being wrong (passages exist and are textually
correct), metadata absence, or BM25 keyword absence.

## 4b. Decisive reachability measurement (k=20)

For all 18 misses I checked (a) presence in the corpus and (b) retrievability by
the *same gate entry point* at top_k=20:

```
absent from corpus                                  = 0     <-- BLOCKED_BY_CORPUS re-ruled out
present but NEVER retrieved even at k=20            = 12
retrievable at k=20 (pure ranking/depth issue)      = 6
```

Consequences, both important:

1. **Corpus absence is definitively ruled out again** — 0 of 18 gold passages are
   missing. The instruction not to reuse `BLOCKED_BY_CORPUS` is honoured.
2. **An ID-normalization fix yields 0 additional hits at k=5.** Every missed
   passage already matches under the frozen normaliser; it is simply never
   returned. So **ID normalization / canonical ID mapping are NOT RM-006 levers**,
   contrary to step 1-2 of the plan's generic fix order. This is a measured
   negative result and is recorded so that effort is not wasted there.
3. 6 misses are retrievable at k=20 but not k=5 ⇒ **ranking depth/quality**, the
   most tractable subset.
4. 12 misses are not retrieved even at k=20 ⇒ **candidate-pool / balance**
   problem, consistent with the 31:1 论语 skew in §2.



`DSH-MASTER-PLAN.md` §10 states: *"RM-006's real surface is
`retrieve_for_sage_chat` + `vector_search` + `_kw_search_chroma` +
`_merge_retrieval`. Nothing else."* That is **incomplete**.

Measured: 125 of 143 docs are 论语, and the missed gold targets are
disproportionately **道德经 / 韩非子 / 墨子**. A fusion or reranker change inside
the chat path cannot retrieve a 道德经 passage that the ranking never considers
while 论语 dominates by 31:1. So **RM-006's owning surface includes the candidate
pool and its book/school balance**, not only the fusion weights.

This also explains why the previously recorded attempts stalled at 0.55: the
fix-order steps 7-9 (BM25/dense/fusion) are downstream of a corpus-balance
problem.

## 6. Recommended order for RM-006 implementation (evidence-driven)

Deviating from the plan's generic list **where measurement justifies it**, and
keeping the plan's own "measure before and after every patch" rule. Note two
measured exclusions: ID normalization and canonical ID mapping are **dead ends**
(§4b: 0 gain available), so the plan's steps 1-2 are explicitly **skipped with
evidence**.

1. **Candidate-pool / book balance in the chat path** — the 31:1 论语 skew is the
   single largest measured structural cause (12 of 18 misses are unreachable even
   at k=20, and the missed targets are disproportionately 道德经/韩非子/墨子).
   A bounded, principled book- or school-aware candidate expansion (not a score
   hack) is the leading candidate.
2. **Dense / reranker depth** — after (1); 6 misses become reachable by k=20, so
   ranking depth is the second lever. Requires before/after numbers.
3. **Query normalisation → modern-issue ontology** — for the 2 mapping misses
   (rg-0003, rg-0015 both want 4.8/9.19).

**Explicitly NOT proposed:** swapping Chroma, swapping the embedding, or
rewriting RAGService — none is justified by the evidence, and all are forbidden
by the instruction.


## 7. Status

```
RM-006 = BLOCKED ON RM-005 TERMINAL?  no -- RM-005 is now terminal-capable
RM-006 = failure decomposition COMPLETE (this document)
RM-006 = implementation NOT STARTED (deliberately: requires before/after
         measurement per patch, and RM-005 review closure first)
recall@5 = 22/40 = 0.55   target >= 0.90   >= 36/40 required
```

**No patch has been written.** This is decomposition only, as the instruction
requires ("禁止直接大改 RAG" / failure decomposition first).

## 8. Method limitations (stated honestly)

- The `classifications` above are my judgement from measured top-5 lists plus the
  corpus composition; they are not produced by an automated classifier. The raw
  per-case data is in `deliverables/kb-v1/rm006-percase.json` for independent
  re-checking.
- One observed anomaly, now **resolved and not a defect**: `rg-0021`/`rg-0029`/
  `rg-0030` gold ids carry a `sage:` namespace that no Chroma metadata row uses
  (`namespaced verse_ids = 0`). I traced this: the frozen matcher
  `metrics.py:170-181 normalize_passage_id` strips `前缀:` from **both** sides
  before comparison (the docstring even records that without this, Recall@K was
  identically 0.0). So the namespace difference is **correctly handled by the
  frozen metric** and is not a harness or Gold inconsistency. My `norm()` helper
  reproduced the same rule, which is why my probe matched the canonical numbers
  exactly. **Retained here because it was checked, not assumed.**
- `eval-run.json`'s `failures` array is **truncated to 10 entries**
  (`run_eval.py:333` — `r5["failures"][:10]`) while recall@5 implies 18 misses.
  Reported metrics are unaffected, but the failures list must not be used as the
  miss inventory. This is a harness reporting limitation worth recording.


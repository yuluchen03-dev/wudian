# RM-006 — root cause established (executed, read-only, no patch)

Supersedes §4b/§5/§6 of `rm006-failure-decomposition.md`, which rested on a
probe whose id handling did not replicate the production output layer. The
correction is documented in §5 below.

## 1. Headline

```
baseline recall@5                        = 22/40 = 0.550
ORACLE recall@5 in union@143 of both layers = 40/40 = 1.000
target                                   >= 36/40 = 0.90

=> Gate F is REACHABLE BY RE-RANKING ALONE.
   No corpus change, no new embedding, no Chroma swap, no Gold edit is needed.
```

The oracle is computed honestly: for each gold record I take the **union of the
two existing retrieval layers at full pool** (`vector_search(q, top_k=143)` and
`_kw_search_chroma(q, top_k=143)`), apply the *same id alignment the production
output layer applies* (`rag_service.py:1371-1372`), normalise with the frozen
`normalize_passage_id`, and ask whether any expected id is present at all.

**0 of 40 gold records are absent.** So every miss is a **ranking** failure, not
a recall/corpus failure. This also definitively closes `BLOCKED_BY_CORPUS`.

## 2. Real defect #1 — fusion is NON-MONOTONIC in `top_k`

Measured (query `怎么才能不轻易生气？`, gold = `1.1`):

```
top5      = 20.3, 11.12, hanfeizi-youdu-01, 7.3, 3.1
top80[:5] = 1.1,  11.12, 20.3, 2.8, 2.21
PREFIX_EQUAL = False
gold 1.1 : rank@80 = 1     <-- but invisible at k=5
```

A correct top-k retrieval must be a **prefix** of a larger top-k. Here it is not,
and the consequence is severe: gold ranks **#1** at k=80 yet misses at k=5.

Root cause (`rag_service.py:1332-1334` → `1202-1242`):

```
vec_results = self.vector_search(expanded_query, top_k=top_k * 2)
kw_results  = self._kw_search_chroma(expanded_query, top_k=top_k * 2)
results     = self._merge_retrieval(vec_results, kw_results, limit=top_k * 2)
```

`_merge_retrieval` scores `0.7*vec_sim + 0.3*kw_sim`, but **each component exists
only if that document survived that layer's own `top_k*2` truncation**. So a
document's fused score *depends on `top_k`*. At `top_k=5` a doc present only in
the keyword layer scores `0.3*kw`; at `top_k=80` the same doc also lands in the
vector layer and suddenly scores `0.7*vec + 0.3*kw`, jumping it to rank 1.

**This means the k=5 ranking the frozen Gate F measures is systematically worse
than the ranking the very same scorer is capable of.**

## 3. Real defect #2 — the two layers are not on a common scale

Measured for the same query:

```
vector_search     similarity range : 0.0000 .. 0.2110
_kw_search_chroma similarity range : 0.0833 .. 0.2917     <-- max EXCEEDS vector
fused                              : 0.7*vec + 0.3*kw
```

A single keyword hit at `0.2917` contributes `0.0875`, which beats the **entire**
vector contribution of any document below `vec = 0.125`. The `min(score/12.0, 1.0)`
divisor at line 1196 is an arbitrarily calibrated constant, and its own comment
records that `/8.0` had already been replaced by `/12.0` to stop keyword hits
evicting vector hits — i.e. the constant is being tuned to compensate for the
missing scale normalisation.

`vector_search` is also called in a **second place** with a different argument
(`line 1262`, `top_k=top_k`, not `top_k*2`) inside `hybrid_search`, so the two
call sites are not even consistent with each other.

## 4. Measured fix attempts (prototypes, outside the repo)

| configuration | recall@5 |
|---|---|
| **current code (non-monotonic)** | **22/40 = 0.550** |
| monotonic fusion, fixed pool 20/40/60/100/143 | 15/40 = 0.375 |
| monotonic + per-layer max normalisation, vec0.5/kw0.5 | 15/40 |
| monotonic + normalisation, vec0.7/kw0.3 | 16/40 |
| monotonic + normalisation, vec0.8/kw0.2 | 15/40 |
| monotonic + normalisation, vec1.0/kw0.0 | 14/40 |
| vector layer only (no keyword) | 14/40 = 0.350 |
| keyword layer only | 16/40 = 0.400 |

Two important readings:

1. **Making fusion monotonic, by itself, LOSES 7 hits (22 → 15).** The current
   non-monotonic truncation is accidentally *helping* on this dataset: by
   clamping each layer to 10 candidates it suppresses the keyword layer's
   oversized scale. So "fix the monotonicity" is not a safe isolated patch — it
   must be done together with the scale normalisation.
2. **Even so, neither layer alone nor any normalized fusion exceeds 16/40**,
   while the baseline reaches 22/40 and the oracle reaches 40/40. That gap is
   the real engineering target: the fused ranker is leaving ~18 recoverable
   hits on the table.

A naive weight sweep does **not** solve this, and I am not proposing to ship one.
Reaching 36/40 needs a ranker that can actually separate the 40/40 available
candidates, which is a genuine implementation task with before/after measurement
— not a constant tweak.

## 5. Correction to my own earlier decomposition

`rm006-failure-decomposition.md` §4b reported *"12 present but never retrieved
even at k=20"* and concluded the owning layer was **candidate-pool/book balance**
(the 31:1 论语 skew). That conclusion is **wrong**, and here is the precise error:

- The layers `vector_search` / `_kw_search_chroma` return the **raw** metadata
  `verse_id` (`daodejing-22-01`), because the `debate:{sage}:{bare}` prefix is
  added **later**, in `retrieve_for_sage_chat` at line 1371-1372.
- My oracle compared raw layer ids against gold's `debate:{sage}:{bare}` form
  without applying that prefix, so all 10 `debate:`-prefixed golds looked absent.
- Applying the production prefix rule moves the oracle from **30/40 → 40/40**.

What survives from the earlier work: corpus absence is ruled out (now provably,
0/40 absent), and the 18-miss inventory and per-case ranks in
`rm006-percase.json` / `rm006-rankcurve.json` are still valid measurements of the
**current** ranker.

What is retracted: the *"candidate-pool / book balance is the owning layer"*
conclusion. Book skew is real (125/143 论语) and may still cap what a *fair*
ranker can do, but it is **not** what blocks Gate F — the ranker is.

## 6. Recommended RM-006 implementation (evidence-driven)

Owning surface: `rag_service.py` `retrieve_for_sage_chat` (1332-1334) and
`_merge_retrieval` (1202-1242). Blast radius is **Gate F only** — verified by
grep: `_merge_retrieval` has exactly **one** caller (line 1334), and
`retrieve_for_sage_chat` is the Gate F entry point.

1. Make the candidate pool **independent of `top_k`** (retrieve a fixed large
   pool from both layers), so top-k becomes a genuine prefix — restores
   monotonicity and makes the metric meaningful.
2. Put the two layers on a **common scale** before weighting, so the keyword
   layer cannot outrank the vector layer by construction.
3. Then improve actual separation, measuring `recall@1/3/5`, `mrr`,
   `source_attribution` and `school_leakage` before and after every step.
4. Guard the known regression risk (Gate J shares
   `retrieve_for_debate_sage`, not this path — but `school_leakage` and
   `source_attribution` must be re-measured after each change).

**Do not ship a monotonicity-only patch** (measured −7 hits).

## 7. Status

```
RM-006 = root cause ESTABLISHED, oracle ceiling 40/40, target reachable
RM-006 = NO patch written (deliberate: the fix is a ranker change requiring
         before/after measurement, and a naive patch measurably regresses)
Gate F = 22/40 = 0.550 (unchanged, still FAIL)
```

Evidence scripts (all read-only, isolated temp Chroma):
`rm006_proto.py`, `rm006_proto2.py`, `rm006_oracle.py`, `rm006_oracle2.py`,
`rm006_scale.py`, `rm006_monotonic.py`, `rm006_rankcurve.py`.

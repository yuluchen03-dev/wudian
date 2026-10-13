# DSH-RM-005 — t3 implementation findings, cycle 1 (trust-verification)

Attempt: `61420ff2-f0d7-4fbb-8fbb-8971ce0ada42`
Status after cycle 1: **the target is not reachable with a retrieval-layer-only
change.** This document records why, with measurements, instead of shipping a
gamed or reject-all fix.

All probes used an isolated temporary copy of production Chroma. Production
fingerprints are unaffected.

## 1. Root cause: CONFIRMED, and it is two layers, not one

Classification **C — weak evidence binder**, as the captain and t2 both found. My
independent reproduction additionally shows there are **two** weak layers, and the
second one is the one that actually blocks Gate E.

### Layer 1 — `_debate_keyword_search` (rag_service.py:526-570)

Scores +3.0/+1.5/+1.0 for terms that are substrings of the query. Because
`_extract_keywords` (rag_service.py:1491-1524) emits **single characters**, and
rag_service.py:538 concatenates the query term list with the expanded-query term
list (identity when `SYNONYM_MAP` does not fire → the list is duplicated), an
unrelated query accrues score > 0 and survives `if score <= 0: continue`
(rag_service.py:564), which is the *only* admissibility gate — there is no
relevance floor.

Every one of `uq-0009`'s 9 hits is carried by a single character:

| sage | id | score | firing term |
|---|---|---|---|
| confucius | lunyu-taibo-01 | 2.0 | `人` |
| confucius | lunyu-weilinggong-01 | 2.0 | `人` |
| laozi | daodejing-22-01 | 2.0 | `人` |
| laozi | daodejing-33-01 | 3.0 | `人` |
| laozi | daodejing-08-01 | 2.0 | `世` |
| mozi | mozi-feile-01 | 2.0 | `人` |
| mozi | mozi-jianai-01 | 2.0 | `人` |
| mozi | mozi-feigong-01 | 2.0 | `对` |
| hanfeizi | hanfeizi-wuzhu-01 | 3.0 | `世` |

Applying the evidence-bearing rule to **this layer alone** reduces uq-0009 from
9 hits to **3** and keeps Gate J at exactly **19 citations** (measured, see §3).

### Layer 2 — the confucius fallback (`retrieve_for_sage_chat`, rag_service.py:1278-1296)

With layer 1 fixed, `retrieve_for_debate_sage` for confucius falls through to the
`retrieve_for_sage_chat` fallback, which admits **3** uq-0009 hits:

| id | similarity | original text |
|---|---|---|
| lunyu-bazhi(3.3) | 0.2191 | 《论语·八佾》 |
| lunyu-xueer(1.5) | 0.1544 | 《论语·学而》 |
| lunyu-weizheng(2.20) | 0.1375 | 《论语·为政》 |

These are **hash-embedding coincidences**, not relevance. The project's own code
comments concede the local embedding is non-semantic
(`rag_service.py:633-637`). The proof that this layer has no relevance signal is
the negative control: `请问地铁几点停运` (subway timetables, zero philosophical
content) returns **4 hits** through the same route — `《论语》3.5 sim=0.1195`,
`9.19 sim=0.1091`, `15.16 sim=0.1005`, plus `mozi-jianai-01 sim=0.1044`. The layer
admits arbitrary unrelated text at the 0.10–0.12 band.

## 2. The decisive separation problem

`sc-0003`'s legal confucius citation — `《论语·为政》2.20` — arrives through **the
same fallback**, at similarity **0.1125**, only **0.0125 above**
`DEBATE_MIN_SIMILARITY = 0.10`.

So the legal control and the unsupported case occupy the **same similarity band
(0.10–0.22) on the same code path**, distinguished only by hash noise:

| | legal control sc-0003 | unsupported uq-0009 |
|---|---|---|
| confucius fallback top similarity | 0.1125 | 0.2191 |
| negative control 地铁几点停运 | — | 0.1195 |

Note that **uq-0009 scores higher than the legal control and higher than the pure
noise negative control.** Any threshold on this signal therefore orders the
unsupported case *above* both the legal case and gibberish. A scalar fix is
mathematically incapable of separating them in the required direction.

Measured rule search (prototype11, prototype17, prototype20):

| rule | uq-0009 hits | sc-0003 hits | J citations | school reachable |
|---|---|---|---|---|
| R0 baseline | 9 | 3 | 19 | 12/17 |
| R2 evidence-bearing, layer 1 only | **3** | 2 | **19** | 12/17 |
| R2 applied to both layers | **3** | 1 | **18** ← shrink | 11/17 |
| R5 (chars allowed if in a query term) | 10 | 2 | 19 | 15/17 |
| min_len=2 (t2's isolation) | 0 | 0 ← collapse | — | 7/17 |

No rule achieves `uq-0009 == 0` while preserving both the legal control and the
Gate J denominator. The only rules that zero uq-0009 also zero the legal control
and/or shrink J from 19 to 18.

## 3. Why the two layers cannot both be fixed at the retrieval layer

Fixing layer 1 **exposes** layer 2: removing the junk keyword hits for confucius
lets the query fall through to `:1278`, where the non-semantic embedding admits
it. Fixing layer 2 as well (by removing single-character and whole-query tokens
from `_kw_search_chroma`) then also removes `sc-0003`'s legal `2.20` citation,
because that citation is produced by the very same mechanism — dropping Gate J's
denominator from 19 to 18, which the earlier round was already rejected for.

The two cases are not separable by any signal available in these layers, because
the signal *is* character-ngram/embedding coincidence and both cases are made of
the same thing.

## 4. What this means — honest statement

**`uq-0009` cannot be refused by a retrieval-layer fix without either
(a) collapsing the legal control `sc-0003`, or (b) shrinking the Gate J
denominator — both forbidden by the task contract.**

The reason is structural, and it matches the corpus reality independently
established by both t2 and me: the debate corpus contains **no** death, grief,
mourning, or bereavement vocabulary (0 of 90 concept tags; the only near-misses
are false friends `痛→痛快`, `命→非命`, `家→家国`). There is genuinely nothing to
retrieve.

But the frozen Gate E metric does not measure relevance — it measures
`hits == 0` across four sages (run_eval.py:250-254). It therefore asks the
retrieval layer to prove a **negative** ("no evidence exists") using a **positive**
mechanism ("what resembles this query"). A non-semantic embedding cannot do that.
The task's own framing acknowledges this: the goal document states that refusal
requires answering *why* the evidence is insufficient, which is an
**evidence-sufficiency** judgement, not a retrieval-ranking one.

## 5. Recommendation

Two honest options, both requiring a scope decision above my authority:

**Option A — real sufficiency gate (recommended, larger scope; later approved and
implemented as t3 cycle 2).** Introduce an
explicit evidence-sufficiency boundary in the trust layer: a retrieved passage
must share a *content concept* with the query (corpus concept tags ∪
`SYNONYM_MAP` expansions that show **concept-space overlap with the curated
corpus**) before it counts as
supporting evidence. Under the measured data this accepts `sc-0003`
(`失败 → 败` → overlaps `hanfeizi-wai-chu-shuo-01`) and rejects `uq-0009` (nothing
overlaps), and it is corpus-grounded rather than fixture-shaped. It is a
different layer from RM-005's declared retrieval scope and overlaps the
claim-evidence binder, so it needs the captain's explicit re-scoping.

> **Wording note (documentation correction — no command executed):** the match
> blob includes the curated `keywords` field, so all descriptions must say
> "concept-space overlap with the curated corpus", never "the term occurs in the
> corpus text".

**Option B — report BLOCKED honestly.** Declare that `unsupported_correct_refusal`
cannot exceed 11/12 = 0.9167 under the current architecture and measurement
contract, state that the residual 1/12 requires the semantic embedding PHASE 4
already contemplated in the code comments (`rag_service.py:636-637`), and record
the corpus-vocabulary evidence as the justification. This preserves every
constraint and fabricates nothing.

I have NOT shipped any patch, because every candidate I measured violates a hard
prohibition. I am reporting rather than forcing a green number.

## 6. Incidental correctness findings worth keeping (not part of the Gate E fix)

1. `rag_service.py:538` duplicates the term list whenever `SYNONYM_MAP` does not
   fire (uq-0009: 28 = 14+14; sc-0003: 20 = 10+10), doubling every score against a
   `/8.0` constant calibrated for single counting. This is a real defect.
2. `_kw_search_chroma` uses the **entire raw query string** as a
   `where_document={"$contains": ...}` token. A full modern sentence will match
   essentially nothing, so the token is dead weight; and its single-character
   tokens are the same non-evidence as in layer 1.
3. A character coincidence is surfaced as **similarity 0.7500**
   (`libai-jiangjinjiu-01`, score 6.0 from `对`+`人`). Presenting that to a user
   as 75% relevance is a trust-signal defect independent of any gate.
4. `compute_school_leakage` derives its denominator from *retrieved citations*,
   so any change that reduces reachability silently shrinks Gate J's denominator
   rather than failing the gate. That is a measurement vulnerability: it makes
   "return nothing" a way to look clean. Worth an RFC.

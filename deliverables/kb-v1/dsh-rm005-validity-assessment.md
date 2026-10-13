# DSH-RM-005 — validity assessment of the landed fix (captain, static)

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Reviewer: captain, **source-level reading only**
Status: **STATIC ANALYSIS — no command executed.**

The shell outage prevents execution. This document records what can be
established by reading source and diff, because the qa-reviewer's t17 static
review raised two findings that decide whether RM-005 is a valid fix at all. I
verified both against the source myself rather than accepting them on trust.

## Finding A — the sufficiency gate is BYPASSED by the vector layer

**VERIFIED TRUE.** Control flow in `retrieve_for_debate_sage`
(`rag_service.py:1409-1464`):

```
:1409  out_of_scope = self._query_out_of_scope(query)      # G1-G4 guards
:1418  results = self._debate_vector_search(sage_key, query, top_k=top_k)
:1419  if results:
:1420      return self._format_debate_results(results)      # <-- EARLY RETURN
:1422  results = self._debate_keyword_search(sage_key, query, top_k=top_k)
...
:1435  if not results and sage_key == "confucius":
:1441      if not self._query_has_corpus_support(query):    # <-- NEW GATE
:1446          return {"verses": [], "commentaries": []}
```

The new `_query_has_corpus_support` gate is reached **only** when the vector
layer returned nothing. A vector hit short-circuits at `:1419-1420` and never
consults the sufficiency boundary.

**Consequence:** `uq-0009` passes Gate E because it happens to draw **zero vector
hits**. The fix does not make the vector layer support-aware. The captain's own
earlier probe measured exactly this exposure: `retrieve_for_sage_chat` (the same
hash-embedding global lookup) admitted `uq-0009` at similarity **0.2191** — the
highest of all six probes, above the legal control `sc-0003` (0.1125) and above
the junk control (0.1195).

So the correct statement of the fix is narrow and must be recorded as such:

> RM-005 closes the **keyword layer** and the **confucius fallback** against
> non-evidence. It does **not** close the vector layer. `uq-0009` currently
> refuses because the vector layer produces no hit for it — which is a
> **contingent** outcome, not an enforced invariant.

That is a materially weaker claim than "the evidence sufficiency boundary is
enforced." Naming matters: an invariant that holds by luck on one case is not an
invariant.

## Finding B — the gate is ASYMMETRIC across sages

**VERIFIED TRUE.** The gate sits inside `if not results and sage_key ==
"confucius"` (`:1435`). `laozi`, `mozi` and `hanfeizi` get **no equivalent
admission gate**. For those three sages the fallback path does not exist at all,
so the only protection is the keyword-layer fix.

This is defensible on one reading — the fallback *is* confucius-specific, because
only confucius has a separate `retrieve_for_sage_chat` index — but it means the
sufficiency boundary is not a uniform property of retrieval. A reviewer should
state that plainly rather than describing RM-005 as enforcing a general boundary.

## Finding C — `concept_resolves_in_corpus` proves CONCEPT overlap, not TEXTUAL support

**VERIFIED TRUE, and the predicate's own docstring is explicit about it.**
`rag_service.py:255-273` builds a match blob from
`original + translation + text + keywords` and substring-tests the term against
it. Because `keywords` are the **curated corpus tags**, a term that appears *only*
as a tag counts as "resolving" even if it never occurs in any original text.

The docstring at `:256` says exactly this ("原文 / 译文 / 检索文本 / 概念标签"), so
this is **honest and self-consistent**, not a hidden flaw. But the acceptance
wording must therefore say **"concept-space overlap with the curated corpus"** and
must not say "the term occurs in the corpus text."

Residual risk: a 2-character concept can substring-hit incidentally. The predicate
is corpus-driven rather than semantic. This is the single remaining gaming-adjacent
vector, and it is testable by paraphrase probes.

## Finding D — the "10-point behaviour matrix" claim is overstated

**VERIFIED TRUE by my own independent reading** of
`backend/tests/test_rm005_evidence_sufficiency.py` (256 lines). I audited all ten
required behaviours against the file:

| # | Required | Actually present |
|---|---|---|
| 1 | uq-0009 → refusal | yes (`:95`), asserts hits==0 **and** predicate False |
| 2 | sc-0003 → supported | yes (`:102`) |
| 3 | no evidence → refusal | **partial** (`:109`) — asserts predicate False only, never four-sage hits==0 |
| 4 | irrelevant evidence → refusal | **partial** (`:116`) — asserts the *keyword layer* returns `[]`, which does **not** imply refusal, because `:1419-1420` still lets the vector layer return hits |
| 5 | verified but irrelevant quote → refusal | **ABSENT** |
| 6 | supported evidence → supported | partial — only sc-0003 individually; the 19-query sweep is in behaviour 10 |
| 7 | wrong-school evidence → refusal | **ABSENT** |
| 8 | generic fallback quote must not upgrade support | **ABSENT** |
| 9 | multiple weak evidence must not auto-suffice | **ABSENT** |
| 10 | one strong relevant evidence keeps support | yes (`:124`), all 19 reachable legal queries |

So **4 behaviours are entirely absent and 2 are only partially asserted.** The
task record's claim to have covered "the 10-point behaviour matrix" must be
corrected. It is not accurate as written.

Behaviours 5/7/8/9 plausibly belong to a different owning layer (binder / school
filter / citation guard) rather than to the retrieval predicate — but then they
must be **explicitly re-homed with a reason**, not silently dropped while the
matrix is described as complete.

## What remains genuinely sound in the change

Credit where due — the following were verified and are real:

- **Not gamed.** No conditional anywhere uses `uq-`/`sc-0`/`离世`/`亲人`/`地铁`
  text (all 17 occurrences are comments/docstrings). `DEBATE_MIN_SIMILARITY` is
  still `0.10` (`:297` region); no new numeric floor. Weights and the `/8.0`
  constant unchanged.
- **Named and isolated.** Module-level `evidence_terms`, `query_concept_space`,
  `concept_resolves_in_corpus`; class-level `_evidence_terms`,
  `_query_has_corpus_support`, `_corpus_concept_vocab` (cached).
- **Tests do not read Gold.** All 12 `must_refuse`, 19 legal and 2 negative
  queries are hard-coded literals, so editing `eval/*.jsonl` cannot make them pass.
- **Paraphrase generality is tested** (`:181-187`): `失败了怎么办` must stay
  supported, `亲人去世了很难过` must stay refused. Neither string is in any dataset.
- **The reject-all guard is correctly shaped** (`:210-226`) and pins
  `len(BASELINE_REACHABLE) == 19`.
- **Corpus-absence is independently confirmed** by the captain: all 90 curated
  tags across 9 schools contain only the false friends `家→家国`, `痛→痛快`;
  text-level `死/亡/丧/哀/悲/悼/逝/祭/葬/泪/孤/寡` = **zero**. Refusing `uq-0009`
  is correct product behaviour.

## Verdict on RM-005 (captain, static)

**NOT TERMINAL PASS. Status: implementation landed, unverified, with two
substantive design limitations.**

The fix is honest, non-gamed, and corpus-grounded, and it does move Gate E from
`11/12` to `12/12` with Gate J's denominator preserved at `19` — no earlier
attempt achieved that. But three things must be corrected before it can be
accepted:

1. **The Gate E pass is contingent on the vector layer drawing zero hits for
   `uq-0009`.** It is not an enforced invariant. Either the vector layer must be
   brought under the boundary, or the limitation must be stated explicitly in the
   acceptance record and carried to RM-006.
2. **The "10-point behaviour matrix" claim is inaccurate.** Four behaviours are
   absent, two partial. Correct the claim, and either add the tests or re-home
   them with reasons.
3. **Acceptance wording must say "concept-space overlap with the curated corpus"**,
   not "textual support."

None of these is dishonesty by the implementer, who disclosed the vector-layer
residual plainly and declined to claim unexecuted tests passed. They are
limitations of the fix, found by an independent reviewer doing its job.

## Consequence for the DAG

Because the Gate E pass is contingent rather than enforced, **RM-006 (retrieval
recall) should absorb the vector-layer question**, and the RM-005 acceptance
record must state the contingency explicitly so RM-011's final eval cannot
present `12/12` as an unconditional result.

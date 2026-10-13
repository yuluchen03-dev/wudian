# DSH-RM-005 — static (non-executing) coverage audit of the test suite

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Reviewer: captain, **file-level only**
Status: **STATIC REVIEW — no command executed. NOT independent verification.**

The shell outage made execution impossible for every session. This document is
therefore an *audit by reading*, and is explicitly **not** a substitute for t17.
Its purpose is to determine whether the test suite, if it runs, would actually
prove the RM-005 requirement — the one question that can be meaningfully answered
without executing anything.

## 1. Coverage of the 10-point behaviour matrix

The goal's §十四 requires at least 10 behaviours. Mapping to
`backend/tests/test_rm005_evidence_sufficiency.py`:

| # | Required behaviour | Test | Verdict |
|---|---|---|---|
| 1 | `uq-0009` → refusal | `test_behaviour_1_uq0009_refused` (`:95`) | covered — asserts four-sage hits == 0 **and** predicate False |
| 2 | `sc-0003` → supported | `test_behaviour_2_legal_control_sc0003_supported` (`:102`) | covered — asserts hits > 0 **and** predicate True |
| 3 | no evidence → refusal | `test_behaviour_3_no_evidence_refused` (`:109`) | covered — both negative controls |
| 4 | irrelevant evidence → refusal | `test_behaviour_4_irrelevant_evidence_not_admitted` (`:116`) | covered — asserts keyword search returns `[]` for all 4 sages |
| 5 | verified but irrelevant quote → refusal | — | **NOT directly covered** (see §3) |
| 6 | supported evidence → supported | `test_behaviour_10_...` (`:124`) | covered — all 19 reachable legal queries |
| 7 | wrong-school evidence → refusal/not sufficient | — | **NOT directly covered here** (see §3) |
| 8 | generic fallback quote must not upgrade support | `RejectAllGuardTest.test_negative_control_is_not_admitted_by_keyword_layer` (`:236`) + `test_negative_control_is_refused_by_sufficiency_boundary` (`:248`) | partially covered — the fallback gate is exercised, but no test constructs a *generic fallback quote* and asserts it fails to upgrade support |
| 9 | multiple weak evidence must not auto-suffice | — | **NOT directly covered** (see §3) |
| 10 | one strong relevant evidence keeps support | `test_behaviour_10_...` (`:124`) | covered |

Score: **6 of 10 clearly covered, 1 partially, 3 not directly covered.**

## 2. What the suite does well (credit where due)

- **It does not read Gold.** All 12 `must_refuse` queries, all 19 legal queries
  and both negative controls are **hard-coded literals** (`:34-76`). Editing
  `eval/*.jsonl` therefore cannot make these tests pass. This is a genuinely
  robust choice and closes the most obvious gaming vector.
- **Paraphrase generality is tested** (`:181-187`): `失败了怎么办` must stay
  supported and `亲人去世了很难过` must still be refused. Because neither string
  appears in any dataset, these are the strongest available evidence that the
  rule is not literal-matching.
- **The reject-all guard is real and correctly shaped** (`:210-226`): it enumerates
  the 19 baseline-reachable queries and fails if *any one* is lost, and it pins
  `len(BASELINE_REACHABLE) == 19` so a later edit cannot quietly shrink the set to
  hide a collapse. This directly implements the goal's §十五 requirement.
- **The negative-control assertion is honestly scoped** (`:236-246`): it fixes the
  *keyword* layer only and states in the comment why the vector layer is excluded
  (RM-006 scope), rather than silently weakening the claim.
- **The deduplication fix is unit-tested** (`:170-175`), which covers the
  `rag_service.py:538` term-doubling defect the captain and t2 independently
  found.

## 3. The three gaps, and why they matter

Gap 5 — "verified but irrelevant quote → refusal":
RM-005's boundary is about *corpus support for the query*, not about quote
verification. The test suite exercises retrieval admissibility only. A quote can
be perfectly verified (exists, correct source) yet be irrelevant to the question;
nothing in this suite asserts that case is refused. **For RM-005 specifically this
is arguably out of the owning layer** — relevance-of-a-verified-quote is a binder
concern — but the goal lists it as a required behaviour, so it must be either
tested or explicitly reclassified. It is currently neither.

Gap 7 — "wrong-school evidence → refusal/not sufficient":
School whitelisting lives in `retrieve_for_debate_sage`'s `_keep` filter, which
this suite does not drive directly. Gate J covers school leakage at the frozen
level (and reports `0/19`), so there is indirect coverage, but there is no
behavioural test asserting that wrong-school evidence fails to satisfy the
sufficiency boundary. Given that the goal requires it, this is a real gap.

Gap 9 — "multiple weak evidence must not auto-suffice":
There is no test that deliberately accumulates several weak/incidental hits and
asserts the total does **not** reach sufficiency. This is the classic
quantity-becomes-quality error, and it is exactly the failure mode RM-005 was
about (nine single-character hits summing to "evidence"). The `test_behaviour_4`
test shows single characters produce `[]`, which is a *stronger* result than
"don't auto-suffice" — but it proves the mechanism differently and does not
exercise an accumulate-weak-hits path.

## 4. Gaming vectors examined and found closed

| Vector | Finding |
|---|---|
| Hard-coded `case_id` branch | **closed** — qa-reviewer grep-verified zero conditionals using dataset text |
| New numeric threshold tuned to the fixture | **closed** — `DEBATE_MIN_SIMILARITY` still `0.10` (line 297); no new floor introduced |
| Shrinking Gate J's denominator | **closed** — suite pins 19; implementation declined the entry-point placement that measured `19 → 12` |
| Shrinking the legal-query denominator | **closed** — `test_supported_acceptance_denominator_is_documented` asserts exactly 19 |
| Editing Gold to make tests pass | **closed** — test literals are independent of Gold |
| Literal-string matching instead of a general rule | **closed** — paraphrase tests at `:181-187` pass through the real predicate |
| Reject-all (refuse everything) | **closed at test level** — reject-all guard requires all 19 reachable queries to stay reachable |

The one residual the reviewer already flagged: `concept_resolves_in_corpus`
(`rag_service.py:255`) substring-matches concept terms against corpus text, so a
2-character concept could in principle hit incidentally. Its generality rests on
the corpus vocabulary rather than on semantics. **Probe queries a shell-capable
reviewer should run** (written here, not executed):

1. `如何面对亲人的离世呢` — paraphrase with a particle; must still be refused.
2. `亲人走了我很难受` — synonym paraphrase avoiding `离世`; must be refused.
3. `失败了` — minimal legal fragment; must remain supported.
4. `请问高铁几点停运` — a *different* logistics query than the dataset's subway
   one; must be refused. Tests whether refusal is about the concept or the string.
5. `量子计算机如何改变儒家伦理` — dataset query, as control.
6. A nonsense 2-char string that happens to appear inside a corpus translation,
   to test the incidental-substring risk directly.

## 5. What CANNOT be concluded without execution

Everything about runtime behaviour:

- Whether the tests **pass**. Reading a test proves intent, not outcome.
- Whether `_query_has_corpus_support` actually returns the claimed values.
- Whether Gate E is truly `12/12` and Gate J's denominator truly `19` — those
  remain **author-reported**.
- Whether the module imports cleanly, whether the cached `_corpus_concept_vocab`
  invalidates correctly, and whether performance regressed.
- Whether `test_fix002_refusal.py`'s reachability invariant holds.

**Therefore RM-005 is NOT accepted on this document.** This audit reduces risk and
identifies three concrete coverage gaps; only t17 can close the verification.

## 6. Recommendation to the reviewer gate (t4)

t4 should require, before TERMINAL PASS:

1. t17 execution results (E `12/12`, J denominator `19`, Recall@5 unchanged).
2. Either tests for gaps 5/7/9 **or** an explicit written reclassification
   justifying why each is outside the RM-005 owning layer.
3. The six paraphrase/probe queries in §4 executed, with results.
4. An explicit judgement on the disclosed residual (subway control returns 1, not
   0, from the untouched vector layer).

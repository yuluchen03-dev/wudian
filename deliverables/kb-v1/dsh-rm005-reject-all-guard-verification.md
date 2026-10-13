# DSH-RM-005 — reject-all guard and baseline-dead cases (captain, static)

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Method: **source reading only — no command executed**
Purpose: verify the reject-all guard that the goal makes a **hard FAIL condition**
("如果 refusal = 1.0 但 supported acceptance 大幅坍塌，任务 FAIL"), and correct one
part of my own earlier audit that was too harsh.

## The guard's arithmetic, verified by counting

`LEGAL` (`test_rm005_evidence_sufficiency.py:50-70`) contains exactly **19**
entries: `sc-0001` … `sc-0017` (17) plus `t-PUA` and `t-辞职` (2).

`BASELINE_REACHABLE` (`:200-204`) lists exactly the same 19 ids, and
`test_supported_acceptance_denominator_is_documented` (`:223-226`) asserts
`len(BASELINE_REACHABLE) == 19`.

So the guard's structure is sound: all 19 legal queries are enumerated, the count is
pinned, and any future attempt to shrink the set fails an explicit assertion. **That
is a real anti-gaming control**, not decoration.

## Correction to my earlier audit — the "silently skipped" claim was too harsh

My earlier `dsh-rm005-static-coverage-audit.md` recorded behaviour 6 as a partial
gap partly because "nothing pins the sc-0009/sc-0017 drop-out". Reading further, that
is **only half right**, and the record should be corrected:

- `test_behaviour_10_strong_relevant_evidence_keeps_support` (`:124-139`) does
  `continue` on `baseline_dead = {"sc-0009", "sc-0017"}` — so yes, it skips them.
- **But** `test_baseline_dead_queries_are_not_newly_killed` (`:141-148`) explicitly
  asserts that **both** are `False` from `_query_has_corpus_support` and documents
  why: "sc-0009 / sc-0017 在基线上就无可支撑落点，属既知状态而非本次回归".

So the two cases are **not silently dropped — they are explicitly pinned as
baseline-dead**, with an assertion that fails if either *becomes* supported. The
distinction matters: the failure mode I was worried about was an unreachable case
disappearing from view. Instead it is named, counted, and asserted in the opposite
direction.

**The genuinely remaining gap is narrower than I recorded:** nothing asserts these
two stay unreachable *end-to-end through* `retrieve_for_debate_sage` (the assertions
are at the predicate level). That is a weaker gap than "unpinned", and the
distinction is now recorded accurately.

## What the guard does and does not protect

**Protects against:**
- A blanket refusal that breaks the 19 known-reachable legal queries — fails loudly.
- Denominator shrinking by editing `BASELINE_REACHABLE` — fails at `:225`.
- Newly refusing the two baseline-dead queries in the *wrong* direction — fails at
  `:145`.

**Does not protect against:**
- A case that was reachable and becomes unreachable **via the vector layer**, since
  `_four_sage_hits` measures the whole entry point while behaviour 4 asserts only the
  keyword layer. Partially mitigated by `:216`, which does use `_four_sage_hits`.
- Any legal query outside the enumerated 19 — the set is closed by construction.
- End-to-end reachability of the two baseline-dead cases (predicate-level only).

## Why this matters for the goal's FAIL condition

The goal's reject-all FAIL is specifically about `refusal = 1.0` masking collapsed
supported acceptance. On the evidence available:

- **The refusal side is asserted total** (`:228-234` asserts all 12 must_refuse have
  zero hits).
- **The acceptance side is asserted complete for all 19 baseline-reachable legal
  queries** (`:210-221`).
- The guard covers the exact failure mode the goal names.

That is a genuinely good guard, and I want it recorded as such. The caveat is that
**none of it has executed** — so it is a well-designed guard with no evidence behind
it, which is why RM-005 remains `CONDITIONAL`/`IMPL — UNVERIFIED` and not a pass.

## Corrected 10-behaviour accounting

My earlier audit scored behaviour 6 as "partial — only sc-0003 individually". With
`:124-139` and `:210-221` both read, the accurate statement is:

| # | Behaviour | Status |
|---|---|---|
| 6 | supported evidence → supported | **asserted across all 19 reachable legal queries** (`:210-221`), with the 2 baseline-dead ones pinned separately (`:141-148`) |

So behaviour 6 is **better covered than I recorded**. The confirmed gaps remain
behaviours **5, 7, 8, 9** (absent) and **3, 4** (partial, predicate/keyword-layer
only). Final count: **7 covered or adequately asserted, 3 absent, 2 partial** —
revised upward from 6, and the correction is recorded here rather than quietly
applied.

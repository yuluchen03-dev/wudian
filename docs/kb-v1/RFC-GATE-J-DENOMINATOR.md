# RFC-GATE-J-DENOMINATOR — `school_leakage` denominator is a reachability count

Status: **OPEN** (proposed, not implemented)
Raised by: captain, from independent findings by trust-verification (t3) and
evaluator (t5 scope)
Severity: **measurement integrity** — affects how Gate J can be legitimately
satisfied
Affected file: `eval/scripts/metrics.py:240-272` (`compute_school_leakage`)

## The problem

`compute_school_leakage` derives its denominator from the citations that were
**actually retrieved**, not from the dataset:

```python
total = 0
leaked = 0
for rec, got in zip(records, retrieved):
    allowed   = set(rec.get("allowed_books") or [])
    forbidden = set(rec.get("forbidden_books") or [])
    for ref in got:          # <-- iterates over what came back
        total += 1           # <-- denominator grows per retrieved citation
        book = book_of_ref(ref)
        ...
        if out_of_school:
            leaked += 1
value = leaked / total
```

The denominator is therefore **19 only because 19 citations currently come
back**. It is not a constant of the dataset.

## Why this is dangerous rather than merely unusual

A change that reduces retrieval reachability **silently shrinks the denominator**
instead of failing the gate. In the limit, a system that retrieves nothing scores
`0/0` — and Gate J is "clean" precisely because it stopped doing anything.

This is not hypothetical. It bit RM-005 during implementation: the first gate
placement produced Gate E `12/12` but collapsed Gate J's denominator from **19 to
12**, because the vector layer legitimately carries 14 of the 19 citations. That
is a **denominator shrink, i.e. a hard FAIL**, and it was caught only because an
explicit denominator check was run. On the ratio alone it looked like a pass
(`0/12 = 0.0`).

The same trap will apply to **RM-006**, whose entire purpose is to change what is
retrieved. A retrieval change that drops hard queries could reduce J's
denominator and read as neutral or improving.

## Interaction with the "no denominator shrink" rule

The goal and `AGENTS.md` both forbid shrinking a denominator. For Gate E the
denominator is structurally fixed (count of `expected.must_refuse == true`), so
the rule is enforceable. For Gate J the denominator is **emergent**, so the rule
is not enforceable by the metric itself — it depends on a human or an
out-of-band check remembering to compare 19 before and after.

## Recommended treatment (options, none yet chosen)

1. **Record the reachable-citation count as a first-class reported number** for
   every Gate J computation, so a denominator change is visible in the output
   rather than only in the ratio. This is the minimal, non-breaking fix and is
   already what the captain required of RM-005.
2. **Add an out-of-band invariant test** that asserts the total retrieved
   citation count across the `school_consistency` records equals a recorded
   baseline, and fails loudly on any change. trust-verification has already
   written a 17-query reachability invariant in
   `backend/tests/test_fix002_refusal.py` in this spirit.
3. **Normalize the denominator over the dataset** rather than over retrieved
   items (i.e. count expected citations per record). This is the semantically
   correct fix but it **changes a frozen metric's definition**, so it must not be
   done unilaterally — it needs contract-level review and would invalidate
   historical Gate J values.

## Why it is NOT being implemented in this goal

`eval/scripts/metrics.py` is a **frozen** artifact and its git diff is empty.
Per the goal's own governance, frozen targets and formula definitions are
read-only, and rewriting a frozen metric to make a gate behave is exactly the
"rewrite the metric to turn it green" failure mode the goal forbids. Changing the
denominator definition would also invalidate the recorded historical J values
across every prior acceptance document.

So the correct action is to **document it, preserve the current denominator
explicitly in every report, and defer the definition change** to a contract-level
decision.

## Evidence trail

- Inspector: captain (`docs/kb-v1/DSH-CURRENT-STATE.md` §7c).
- Independently hit by trust-verification during RM-005 implementation
  (`deliverables/kb-v1/rm005-t3-implementation-record.md`,
  `rm005-t3-cycle1-findings.md` finding #4).
- Corroborating measurement: `0/19` baseline, and a measured `19 → 12` collapse
  when the sufficiency gate was placed at method entry.
- The implementation deliberately avoided sinking the guard to the entry point
  for this exact reason (`rag_service.py:1405-1407` documents the decision).

# DSH-RM-008 addendum — RFC-3 evidence correction (captain-verified)

Current Gate: DSH-RM-008
Functional Task: FIDELITY-OPEN-ISSUES
Historical Reference: RFC-3 / FIX-001-FINAL-REVIEW.md:220

## Why this addendum exists

`deliverables/kb-v1/rm008-text-type-fidelity-assessment.md` correctly flagged that
`docs/kb-v1/FIX-001-FINAL-REVIEW.md:220` contains a claim about RFC-3 that does
not survive measurement. It then proposed a correction. On independent
re-measurement the **proposed correction is itself partly wrong**, so neither
the original line nor the proposed replacement should be adopted as written.
This addendum records the measured truth so nobody burns a fix cycle on a false
premise.

## The original claim (FIX-001-FINAL-REVIEW.md:220)

> **RFC-3**：重复且不一致的 `_T2S` 表（backend `normalize_text` vs
> `metrics.py:52-61`），已造成真实假阴性（如 `溫`/`則` 未映射、`aq-0009`
> 繁体 `萬`/`爭` miss）。

This bundles two different phenomena into one sentence and asserts a specific
per-character mapping status that is **false for `萬`**.

## Measured truth (captain, independent run)

Method: loaded the backend normalizer (`app.services.quote_verifier.normalize_text`)
and the frozen eval normalizer (`eval/scripts/metrics.py::normalize`) in the same
process, then compared them character by character and on the real `aq-0009`
quote.

Per-character mapping status:

| char | mapped by backend `normalize_text` | mapped by eval `metrics.normalize` |
|---|---|---|
| `萬` | **True** | **False** |
| `爭` | False | False |
| `溫` | False | False |
| `則` | False | False |

`aq-0009` quote as stored in `eval/adversarial_quotes.jsonl`:

```
上善若水，水善利萬物而不爭。
```

Normalization result:

| normalizer | result |
|---|---|
| backend `normalize_text` | `上善若水水善利万物而不爭` |
| eval `metrics.normalize` | `上善若水水善利萬物而不爭` |
| equal? | **False** |

## Consequences — the three distinct facts that must stop being conflated

1. **`萬` IS handled by the backend table but NOT by the eval table.** So the
   original line's implicit claim that `萬` simply "misses" is wrong for the
   backend path, while the divergence between the two tables on `萬` is real.
   The RM-008 proposed correction ("`萬` IS mapped in BOTH") is therefore also
   wrong: it is mapped in backend only.
2. **`爭`, `溫`, `則` are unmapped in BOTH tables.** These are a
   **shared-coverage gap**, not a two-table inconsistency. Unifying the two
   tables will NOT fix them, and any test asserting they are fixed by
   unification will stay red. They need the shared table extended, which is a
   coverage decision with its own implications for `quote_exactness` (Gate D) —
   not a mechanical dedup.
3. **`aq-0009` genuinely normalizes differently under the two normalizers**
   (verified above: `equal=False`), because `萬` is the sole differing character.

## Additional measurement: aq-0009 corpus reachability

I also checked whether the `aq-0009` quote matches any corpus entry under
either normalizer. Under both, the answer was **no direct `original` substring
hit**. This means the `aq-0009` outcome is not determined by the `萬` divergence
alone — the quote does not land on a corpus entry by simple substring match
under either normalizer. Any fix reasoning that "aligning `萬` will repair
`aq-0009`" is therefore unproven and must be checked against the actual frozen
metric path before being claimed.

## Net effect on RFC-3 status

**RFC-3 remains OPEN.** Neither the original line nor the RM-008 proposed
replacement is accurate as written. The corrected statement is:

> RFC-3: the backend and eval `_T2S` tables are duplicated and inconsistent.
> Measured divergence is at least `萬` (backend maps it, eval does not), which
> makes the `aq-0009` quote normalize differently under the two paths. Separately,
> `爭`/`溫`/`則` are unmapped in **both** tables — a shared-coverage gap that
> unification cannot fix. Table sizes: backend 148 entries, eval 47 entries,
> with 106 backend-only and 5 eval-only keys. `eval/scripts/metrics.py` is frozen
> and its git diff is empty.

This addendum is recorded rather than edited into `FIX-001-FINAL-REVIEW.md`,
because that document is a historical review record and rewriting it would
destroy the audit trail. The correction lives here and in
`docs/kb-v1/DSH-TASK-ACCEPTANCE.md`.

## Governance note

Two independent agents reached two different, partly-incorrect conclusions about
the same line. That is precisely why the goal's source-of-truth order puts
measurable repository behaviour above agent prose. The measured table above is
the authority; the prose in the original review and in the RM-008 report are
both superseded on this specific point.

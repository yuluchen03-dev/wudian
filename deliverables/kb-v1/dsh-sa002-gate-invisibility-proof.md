# DSH-SA-002 — L2 trust bypass: why no frozen gate detects it (captain, static)

Current Gate: DSH-SA-002
Functional Task: L2-COMMENTARY-TRUST-BYPASS
Method: **source reading only — no command executed**
Status: defect confirmed at source; the reason it is gate-invisible is now proven.

Purpose: the defect is already reproduced and recorded. What was *not* established
is the precise reason **every frozen gate stays green while the bypass is wide
open**. That is the part that makes this dangerous rather than merely untidy, and it
is answerable by reading the frozen metric.

## The defect, restated exactly

`citation_guard.guard_citations` (`citation_guard.py:388-397`):

```python
_supporting = None
for _ref in refs:
    _ref_orig = str(_ref.get("original", ""))
    _qn = normalize_text(original)
    if _qn and _qn in normalize_text(_ref_orig):
        _supporting = _ref
        break
is_l1 = True                                          # <-- default is TRUE
if _supporting is not None and _supporting.get("text_type") is not None:
    is_l1 = _supporting.get("text_type") == "original"
```

`is_l1 = True` is assigned **unconditionally** (`:395`), and is only narrowed when
`text_type` is *present* (`:396-397`). The in-source comment at `:381-387` discloses
this honestly: `RAGReference` has no `text_type`, `rag_service` does not propagate
it, so the function **cannot** determine L1 from refs — and therefore "保守视为 L1"
(falls back to treating everything as L1).

That fallback is **fail-open in the wrong direction**: it grants original-text
(L1) trust to commentary (L2) content.

## Why this matters: the eval exercises the fail-open path BY DEFAULT

`eval/scripts/run_eval.py:139-143` (`_production_refs`) **deliberately omits
`text_type`** to mirror the production `RAGReference` shape:

> 这里从语料构造 refs，并**刻意省略 `text_type`**，以镜像生产路径实际 feed
> 给 guard 的 `RAGReference`（生产 `RAGReference` 没有 `text_type`…）

So in the frozen eval, `_supporting.get("text_type")` is **always `None`**, the
condition at `:396` is never satisfied, and `is_l1` stays `True` for **every**
citation. The fail-open branch is not an edge case in the harness — it is the
**only** branch the harness takes.

## Why Gate I cannot see it — the precise mechanism

`compute_fabricated_classical_quote` (`metrics.py:147-164`) fires on a single
conjunct (`:157`):

```python
if rec["expected"].get("quote_exists") is False and pred.get("verifiable") is True:
```

Gate I counts a fabricated quote **only when the corpus does not contain the quote**
(`quote_exists is False`) yet the system called it verifiable.

For L2 commentary the situation is different in a way that makes it invisible:

| | Fabricated quote (Gate I's target) | L2 commentary mislabeled verified |
|---|---|---|
| Does the text exist in the corpus? | **No** | **Yes** — the commentary genuinely exists |
| `expected.quote_exists` | `False` | **`True`** |
| Condition at `:157` met? | **yes** | **no** |
| Gate I outcome | counts as a failure | **passes silently** |

**This is the crux, and it is a structural blind spot, not a tuning gap.** Gate I is
defined as "did we call a *nonexistent* quote verifiable?" The L2 bypass is "did we
call an *existing commentary* an *original*?" Those are different questions. A
commentary that genuinely exists can be misattributed as original text indefinitely,
and `fabricated_classical_quote` remains **0 — a passing score**.

So the accurate statement is stronger than "Gate I might miss it":

> **Gate I cannot detect this defect by construction.** `fabricated_classical_quote
> = 0` is fully consistent with the L2 bypass being wide open, because the bypass
> does not involve a nonexistent quote. The metric's numerator is zero *by
> definition* for this class of error.

## Why the other gates do not cover it either

- **Gate D (`quote_exactness`)** compares quote text against the corpus; commentary
  text matches commentary text, so exactness is unaffected.
- **Gate H (`source_attribution`)** — the `source` field can be correct while
  `text_type` is wrong; attribution and stratification are orthogonal here.
- **Gate E / J** are retrieval-side (debate path) and never consult `is_l1`.
- **Gate G** counts claims with a `supported` evidence entry, which depends on
  `quote_exists and source_correct` (`run_eval.py:361`) — again not on `is_l1`.

**No frozen gate's numerator depends on `is_l1`.** That is why the defect survived a
fully green D/G/H/I/J baseline.

## The asymmetry that makes it a real trust bypass

The two implementations disagree on identical input, and the *weaker* one is the
production guard:

| Path | Verdict on identical L2 commentary |
|---|---|
| `quote_verifier.verify_quote` (contract authority) | `citation_corrected` — **correctly downgrades** |
| `citation_guard.guard_citations` (production guard) | **`verified`** — fail-open |

The in-source comment at `:385-386` states this plainly: *"RC4（注疏不得判 verified）
在 citation_guard 这条路径上尚未强制"* — the rule is enforced only by the contract's
authoritative implementation, not by the guard that actually runs in production.

## Assessment against the goal's own criteria

The goal (section 26) says: if the gap *would cause a real production trust bypass*,
escalate to a blocking safety task; if it is an untriggered limitation, write an RFC.

**This is the first case, not the second**, for three reasons:
1. It is triggered by **default**, not exceptionally — the harness always takes the
   fail-open branch because `text_type` is always absent.
2. It affects **trust verdicts**, the product's core promise ("每个观点，都能追到原典").
3. **No frozen gate can detect it**, so a green scoreboard gives false assurance.

## What is NOT claimed

- No claim that this is currently exploited in production. It is a **latent** bypass
  whose reachability depends on whether L2 commentary reaches `guard_citations` in
  the live path — which requires execution to confirm.
- No implementation was attempted. `citation_guard.py` is **not** in this goal's
  authorised change set, and t14 (which owns the fix) has not run.
- The fix design (make `is_l1` fail-closed when `text_type` is absent) is **not**
  applied, because a fail-closed default would change existing behaviour and must be
  measured, not guessed. The in-source comment warns exactly this: a conservative
  default "等于改变既有行为".

## Verdict

**Defect: CONFIRMED at source. Gate invisibility: PROVEN.** The correct status
remains **open, blocking-class**, owned by t14, and it must **not** be described as
closed on the strength of a green `fabricated_classical_quote`. The honest summary
for the final report: *Gate I is green and structurally incapable of seeing this
defect.*

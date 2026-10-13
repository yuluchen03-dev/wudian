# DSH — RFC re-validation (captain, static)

Current Gate: DSH-RM-008
Functional Task: OPEN-FIDELITY-ISSUES — RFC re-validation
Method: **source and corpus reading only — no command executed**

The goal requires RFC-1, RFC-2, RFC-3 and the `RAGReference.text_type` limitation to
be **re-verified and NOT auto-closed**. A green metric must not close them. This
document re-verifies each from source, and states explicitly that **all remain
OPEN**.

---

## RFC-2 — short genuine quotes are classified as fragments: **CONFIRMED, OPEN**

**Status: real defect, reproduced from source and corpus. Not closed.**

`quote_verifier.py:55` defines `MIN_FULL_QUOTE_CHARS = 6`. The classification in
`_find_matches` (`:386-400`) is:

```python
if entry.original.strip() == raw_stripped:
    match_type = "exact"                              # :388
elif entry.norm == quote_norm:
    match_type = "normalized"                         # :391
elif len(quote_norm) >= MIN_FULL_QUOTE_CHARS:
    match_type = "normalized"                         # :395  full-length excerpt
else:
    match_type = "partial"                            # :398  <-- short genuine quotes
```

**The `else` branch at `:397-399` catches every quote shorter than 6 characters**,
regardless of whether it is a complete classical sentence. And `:377` documents the
consequence: a `partial` match is **"不计入 verified"** — excluded from `verified`.

**Corpus verification — this is not hypothetical.** `data/processed/lunyu.json:647`
contains:

```json
"original": "子曰：「君子不器。」"
```

`君子不器` is a **complete, genuine, well-known** 论语 sentence. Its normalized
length is **4 characters < 6**, so it cannot take the `:393` branch, and unless the
quote happens to equal the whole corpus entry verbatim (it does not — the entry
includes 子曰：「…。」), it falls to `partial` and is **denied verified status**.

So the product tells a user that a correct, verbatim, canonical quotation is *not*
verifiable — the precise opposite of the product promise ("每个观点，都能追到原典").
The gate's intent (reject tiny fragments like a bare 仁) is sound, but the
implementation uses **length as a proxy for completeness**, and length does not
measure completeness for a language whose canonical sentences are famously terse.

**Cross-check:** `:631` confirms the completeness gate shares the same constant
("共享常量，不另造阈值"), so the same threshold propagates. The comment at `:615`
attributes the gate to the display contract §3.1/§3.2 — so **this is a contract
question, not a bug to patch unilaterally.** Changing the constant would alter
contract behaviour and must go through the RFC, not a silent edit.

**Not closed. No change made.**

---

## RFC-3 — duplicated, inconsistent `_T2S` tables: **CONFIRMED, OPEN**

**Status: real, already evidenced. Not closed.**

The captain previously verified by reading that the traditional→simplified mapping
tables are **duplicated and inconsistent** between `backend` and `eval`:

- `萬` is mapped in **backend** but **not in eval**.
- `爭`, `溫`, `則` are mapped in **neither**.

Consequence: the same quote can normalize differently on the two paths, so an
equality that holds in production may fail in the frozen evaluator, or vice versa.
That is a **measurement-fidelity** defect: the eval can disagree with production for
reasons that have nothing to do with retrieval or trust quality.

This directly compounds SA-002 and EVAL-FIDELITY-001: if the two paths disagree on
normalization, then "the guard says verified but the verifier says corrected" can be
caused by table divergence rather than by the L2 logic gap.

**Not closed. No change made** — deduplicating the tables changes normalization
behaviour on both paths and must be measured, not merged blind.

---

## RFC-1 — frozen `exact_match` / `trust_state` labels conflict with contract semantics: **OPEN**

**Status: not re-verified in depth this round; remains OPEN.**

Carried forward unchanged. The recorded substance: three genuine classical quotes are
**absent from the current corpus**, and the frozen labels treat them in a way that
conflicts with the contract's semantics. The critical point already established is
that **missing from the corpus ≠ fabricated** — a distinction the metric must not
blur.

**Deliberately NOT closed.** Closing it requires either corpus authority (Q3-blocked)
or a contract decision. Neither is available this round.

---

## `RAGReference.text_type` limitation: **CONFIRMED, blockingly OPEN**

**Status: confirmed defect, escalated. See `dsh-sa002-gate-invisibility-proof.md`.**

Re-verified this goal: `citation_guard.py:395` sets `is_l1 = True` unconditionally
and narrows it only when `text_type` is present. `run_eval.py:139-143` deliberately
omits `text_type`, so **the fail-open branch is the only branch the harness takes**.

The decisive new finding is that this is **structurally invisible to Gate I**:
`metrics.py:157` requires `expected.quote_exists is False`, but L2 commentary
genuinely exists, so `quote_exists` is `True` and the conjunct never fires. Therefore
`fabricated_classical_quote = 0` is **fully consistent with the bypass being wide
open**. No other gate's numerator depends on `is_l1` either.

**Not closed. Escalated to blocking-class safety work (t14).**

---

## RFC-GATE-J — emergent denominator: **OPEN**

`compute_school_leakage` (`metrics.py:256-270`) increments its `total` **per
retrieved citation**, making the denominator emergent and reachability-dependent
(currently 19). Verified this goal that the attack is real in principle: a change
that reduces retrieval reachability shrinks the denominator and can make the ratio
look cleaner while measuring less.

**Mitigating fact, verified:** RM-005 **preserved the denominator at 19** while
reaching Gate E `12/12` — the first attempt to do so, where earlier attempts
collapsed it to 12. So the specific exploit was avoided in practice, but the
**mechanism remains unguarded**, which is why the RFC stays open.

**Not closed.** `metrics.py` is frozen and not in this goal's change set.

---

## Summary — nothing was auto-closed

| Item | Re-verified this goal | Status | Verification method |
|---|---|---|---|
| RFC-1 | partially | **OPEN** | carried forward |
| RFC-2 | **yes — reproduced** | **OPEN** | source `:393/:397` + corpus `lunyu.json:647` |
| RFC-3 | **yes** | **OPEN** | duplicated `_T2S`, prior read |
| `text_type` / SA-002 | **yes — proven invisible** | **OPEN, blocking** | source + frozen metric trace |
| RFC-GATE-J | **yes** | **OPEN** | mechanism confirmed; exploit avoided in practice |
| EVAL-FIDELITY-001 | **yes** | **OPEN** | wiring real (`:133`), `text_type` omitted (`:139`) |
| Q3 | **yes** | **BLOCKED_EXTERNAL_EVIDENCE** | unchanged |
| Q5 | **yes** | **FAIL** | unchanged |

**The goal's rule is honoured: no RFC was closed by virtue of a green metric.** Six
of the seven items are defects that a fully green D/G/H/I/J scoreboard cannot detect
— which is precisely why they must stay open in the final report.

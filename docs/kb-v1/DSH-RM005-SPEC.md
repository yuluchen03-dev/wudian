# DSH-RM005-SPEC

## Task

Implement `WUDIAN-RM-005`: improve unsupported-question refusal so the frozen
`unsupported_correct_refusal` gate can distinguish the unsupported case
`uq-0009` (`如何面对亲人的离世？`) from the legal control `sc-0003`
(`如何面对失败`) without changing the evaluation contract.

The current reproduced baseline is `11/12 = 0.9167`; only `uq-0009` fails.
The current local hash embedding is known to make these two queries look alike,
so the implementation must use an explainable, bounded signal or a local
deterministic retrieval improvement. Do not claim semantic understanding that
the available model does not provide.

## Required reading

- `AGENTS.md`
- `docs/kb-v1/ZCODE-HANDOFF.md`
- `docs/kb-v1/contracts/QUOTE-VERIFICATION-CONTRACT.md`
- `docs/kb-v1/RM-004-FROZEN-GATE-REBASELINE.md`
- `docs/kb-v1/FIX-002-FINAL-REVIEW.md`
- `backend/app/services/rag_service.py`
- `backend/tests/test_fix002_refusal.py`
- `eval/scripts/run_eval.py`
- `eval/scripts/metrics.py`
- `eval/unsupported_questions.jsonl`

## Scope

DeepSeek may modify only:

- `backend/app/services/rag_service.py`
- `backend/tests/test_fix002_refusal.py`

DeepSeek may add a narrowly scoped helper test file under `backend/tests/` only
if the existing targeted test cannot express the invariant. Do not modify any
Gold JSONL, `TARGETS`, frozen metric functions, contracts, production Chroma
files, frontend files, or unrelated services.

## Behavioral requirements

1. `uq-0009` must produce zero debate hits across all four sages, so the frozen
   refusal path returns `insufficient_evidence` and the required refusal phrase.
2. `sc-0003` (`如何面对失败`) and the existing legal controls in
   `test_fix002_refusal.py` must remain reachable with positive hits.
3. Do not shrink the denominator of Gate E or Gate J. Do not special-case a
   dataset id, read the Gold file at runtime, or hard-code a single expected
   metric result.
4. Preserve existing G1-G4 out-of-scope guards and their explanations.
5. The change must be deterministic, bounded to query/retrieval behavior, and
   fail closed when it cannot establish support. It must not generate a quote,
   alter trust-state semantics, or bypass citation verification.
6. Add or update tests that state the `uq-0009` refusal invariant and the
   `sc-0003` non-regression invariant. Keep the tests isolated through
   `backend/tests/conftest.py`; never point them at `backend/chroma_db`.

## Required validation by implementer

Run from `backend`:

```text
.venv/Scripts/python.exe -m pytest tests/test_fix002_refusal.py -q
```

Also run a focused probe or the isolated evaluator showing the Gate E numerator
and denominator. Do not pass `--use-production-chroma`. Report the exact model
identity used by Paseo, files changed, tests, and any remaining limitation.

## Handoff status

The implementer may report only `IMPLEMENTATION_COMPLETE`,
`READY_FOR_CODEX_REVIEW`, or `BLOCKED`. Codex independently checks the diff,
reruns the targeted test, reruns the frozen isolated evaluation, checks all
other gates for regression, and decides `PASS`, `FAIL`, or `BLOCKED`.

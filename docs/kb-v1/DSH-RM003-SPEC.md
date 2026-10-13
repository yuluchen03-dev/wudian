# DSH Implementation SPEC: WUDIAN-RM-003

## Task

Close `EVAL-FIDELITY-001` by wiring the frozen fabricated-classical-quote evaluation to the production trust/citation verdict. Start with a baseline, then implement the smallest adapter and tests needed to prove the wiring.

## Allowed Scope

- `eval/scripts/run_eval.py`
- `eval/scripts/metrics.py` only for read-only inspection; do not change it
- `backend/app/services/quote_verifier.py`
- `backend/app/services/trust_state.py`
- `backend/app/services/citation_guard.py`
- `backend/tests/test_eval_fidelity.py` (new)
- `deliverables/kb-v1/rm003-fidelity-baseline.json`
- `deliverables/kb-v1/rm003-fidelity-report.md`

Do not modify frozen JSONL, `TARGETS`, the quote contract, production Chroma, frontend files, or unrelated FIX-002/003/004 files. Do not read the production Chroma through a client; use isolated copies only.

## Required Baseline Before Patching

For every record in `eval/adversarial_quotes.jsonl`, record:

```json
{"case_id":"...","quote":"...","claimed_source":"...","harness_verdict":{},"production_verdict":{},"difference":{},"root_cause":"..."}
```

The baseline must identify the current synthetic `verifiable` calculation in `run_eval.py` and the exact production verdict function(s) that should replace it. Do not patch before saving this baseline.

## Required Production Adapter

Use the existing production trust/citation path. The adapter must pass the actual production verdict into the frozen metric prediction shape. It may only map fields; it must not duplicate matching, source, completeness, L1, or trust-state logic. If production `RAGReference` lacks `text_type`, document that limitation and preserve conservative behavior rather than inventing metadata.

## Mandatory Tests

Add focused tests for: absent/fake quote, exact correct quote, wrong source, short fragment, commentary/L2 quote, cross-sentence fusion, traditional/simplified punctuation variant, and a real corpus quote. Assert that the metric consumes the production verdict and that no synthetic `verifiable` field can override it. Tests must use isolated fixtures and must not write production Chroma.

## Verification

Run the focused fidelity tests, then the canonical eval with an isolated Chroma copy and a temporary output path. Record D/E/F/G/H/I/J with unchanged denominators, plus backend/frontend regression results if applicable. Report any pre-existing `agnes` environment failure separately. Do not pass `--use-production-chroma`.

## Completion Contract

Return exactly: task status, baseline evidence, files changed, tests and outputs, frozen metrics before/after, regression, limitations, commit SHA if a commit was explicitly made, and `READY_FOR_CODEX_REVIEW`. Do not call the task or project PASS.

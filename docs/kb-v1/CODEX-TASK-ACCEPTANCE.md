# Codex Task Acceptance

## RM-003 / EVAL-FIDELITY-001

**Verdict: PASS (task scope only)**

The frozen `fabricated_classical_quote` evaluation now consumes the production
`citation_guard.guard_citations` verdict through a field-only adapter. The
adapter does not reimplement matching, source, completeness, L1, or trust-state
logic. `metrics.py`, `TARGETS`, frozen JSONL, Gold data, and production Chroma
were not changed.

### DeepSeek routing

- Requested `deepseek-harness/["xiaobai","deepseek-v4.1-flash"]`: repeated
  Paseo sessions returned `xiaobai API error (404)`.
- Same-provider fallback used for implementation and report review:
  `deepseek-harness/["shushen","deepseek-v4-flash-0731"]`.
- The fallback result is recorded as fallback evidence, not as a successful
  exact-model run.

### Independent verification

- Focused backend tests: `133 passed` (`test_eval_fidelity.py`,
  `test_citation_guard.py`, `test_quote_verifier.py`).
- Python compilation: exit `0`.
- Isolated canonical eval: `used_production=false`, temporary Chroma copy,
  runner exit `0`.
- Frozen metrics: D `18/18 = 1.0` PASS; E `11/12 = 0.9166666667` FAIL;
  F Recall@5 `0.55/40` FAIL; G `40/40 = 1.0` PASS; H `18/18 = 1.0` PASS;
  I `0/20` PASS; J `0/19` PASS. The runner's zero exit code does not override
  failed metric values.
- Backend regression: `522 passed, 1 failed, 297 subtests passed`. The only
  failure is `test_default_provider_is_openai`, caused by the existing `.env`
  resolving `LLM_PROVIDER=agnes` while the test expects `openai`.
- Frontend regression: `23` files / `41` tests passed; `npx tsc --noEmit`
  exit `0`; runtime asset checks skipped because no frontend server was
  running.
- Production Chroma was not opened by client and was not passed to the eval.
  Six production files had identical before/after SHA-256 fingerprints.
- `git diff --check` and the changed-file credential scan produced no errors or
  credential matches.

### Open limitations

E and F remain below their frozen targets. The production `RAGReference` path
still lacks `text_type`, so the citation guard's RC4 L1/L2 distinction is not
uniformly enforced. The guard path also does not yet enforce the contract's
cross-sentence boundary rule. RFC-1/2/3, Q3 corpus provenance, and Q5 real-LLM
credentials/E2E remain open. These do not invalidate the RM-003 wiring result,
but they prevent a project-level PASS or production-readiness claim.

**Commit:** none (no commit was authorized or created).

## RM-005 / Unsupported Refusal (Independent Acceptance, 2026-10-12)

**Verdict: BLOCKED**

The current repository contains no RM-005 implementation diff beyond the
previous G1-G4 guards. The independent isolated reproduction still reports
`unsupported_correct_refusal = 11/12 = 0.9166666667`; the sole failure is
`uq-0009` (`如何面对亲人的离世？`). The legal control `sc-0003` remains
reachable, and the existing targeted test passes (`6 passed, 41 subtests`).
The other frozen values in the same isolated run are D `18/18 = 1.0`, F
Recall@5 `22/40 = 0.55`, G `40/40 = 1.0`, H `18/18 = 1.0`, I `0/20`, and J
`0/19`. No Gold, TARGETS, metric formula, contract, or denominator was
changed.

### DeepSeek execution evidence

- Exact requested route `deepseek-harness/["xiaobai","deepseek-v4.1-flash"]`
  was retried in workspace `wks_d8d4424e0c405c7d`; Paseo returned
  `xiaobai API error (404)` before a turn ran.
- Same-provider fallback
  `deepseek-harness/["shushen","deepseek-v4-flash-0731"]` reached the
  repository but failed on continuation with `429 quota_exceeded` before an
  edit or report.
- `deepseek-harness/["deepseek-official","deepseek-v4-flash"]` was also
  attempted and failed because the `deepseek-official` route has no configured
  API key. A second `shushen` model probe reproduced the same quota block.
- No DeepSeek agent changed RM-005 files. Exact-model implementation and
  terminal acceptance therefore cannot be claimed.

### Independent verification

- Isolated canonical evaluator (no `--use-production-chroma`) exited `0` and
  wrote to a temporary output. Frozen metrics were reproduced as listed above.
- Backend targeted test: `6 passed, 2 warnings, 41 subtests passed`.
- Full backend regression: `522 passed, 1 failed, 297 subtests passed`; the
  sole failure is the pre-existing `LLM_PROVIDER=agnes` environment conflict
  in `test_default_provider_is_openai`.
- Production Chroma was not used as the evaluator client target. The six
  production files retained the previously captured SHA-256/size fingerprints
  after the run; no production build or force rebuild was executed.
- `git diff --check` passed and no new authorized source or test file was
  produced by this round.

### Required next step

RM-005 remains the active gate. Do not start RM-006, RM-007, or final
remediation acceptance until a DeepSeek implementation is available and Codex
can independently reproduce E >= 0.95 without shrinking J or E denominators.
RFC-1/2/3, EVAL-FIDELITY-001/text-type limitations, Q3, Q5, and the existing
F ceiling remain open.

### Codex revalidation after DeepSeek fallback round (2026-10-12)

The requested exact Paseo route `deepseek-harness/["xiaobai","deepseek-v4.1-flash"]`
remained unavailable (`xiaobai API error (404)`). The continuation that did reach
the repository used the configured fallback `deepseek-harness/["shushen","Agents-A1"]`.
That fallback briefly introduced a G5 `"离世"` word guard and matching test
expectations, then, after the required generalization review, removed the G5 code
and restored the honest `uq-0009` positive-hit test. The final working tree has no
G5 guard and no net change from that round outside the already authorized files.

Fresh Codex evidence after the rollback:

- `backend/.venv/Scripts/python.exe -m pytest tests/test_fix002_refusal.py -q`:
  `6 passed, 2 warnings, 41 subtests passed`.
- Isolated evaluator (default temporary Chroma copy, no production flag):
  D `18/18 = 1.0`; E `11/12 = 0.9166666667` (fails only `uq-0009`); F
  Recall@5 `0.55`; G `40/40 = 1.0`; H `18/18 = 1.0`; I `0`; J `0/19 = 0`.
  The output was written outside the repository.
- Full backend regression: `522 passed, 1 failed, 297 subtests passed`; the sole
  failure remains `tests/test_ai_provider.py::test_default_provider_is_openai`
  (`Settings().LLM_PROVIDER == "agnes"` from the existing ignored `.env`).
- A before/after SHA-256 probe around a fresh isolated evaluation showed all six
  production Chroma files unchanged during the run. The current
  `chroma.sqlite3` hash (`4c97b5d03991e436457206d7d26682c71c634d2c09f93f639e769172479eda31`)
  differs from the older handoff snapshot; that mismatch pre-dates this isolated
  run and remains an integrity caveat, not a new change attributed to RM-005.

These results confirm the prior independent verdict: RM-005 is **BLOCKED**, not a
Terminal PASS. The requested generalization cannot be demonstrated with the
current hash embedding; a G5 word-level rule would be a Gold-shaped special case
and would risk clearing legal `sc-0003` hits and shrinking J's denominator.

### Exact-model retry (2026-10-12, current Codex turn)

Codex retried the requested Paseo route twice using the exact model identity
`deepseek-harness/["xiaobai","deepseek-v4.1-flash"]` in workspace
`D:\\systemDir\\Desktop\\悟典`. Agent `ba02d708-c590-40ab-8bda-94dd4f632ef2`
failed during ACP turn initialization both times with the raw
`xiaobai API error (404)` HTML response. No repository read, edit, test, or
fallback model execution occurred in those turns. This is an external execution
blocker, not implementation evidence; the previously recorded fallback round is
not credited as deepseek-v4.1-flash work.

Codex independently reran the authorized targeted test and canonical isolated
evaluation after the retry. The targeted test remained `6 passed, 2 warnings,
41 subtests passed`; frozen metrics remained D `18/18`, E `11/12`, F `22/40`, G
`40/40`, H `18/18`, I `0`, and J `0/19`. No source/test diff was produced by the
retry, and the production Chroma SHA-256 remained
`4C97B5D03991E436457206D7D26682C71C634D2C09F93F639E769172479EDA31` before and
after the isolated evaluation.

The earlier execution bullets above describe the pre-fallback attempt; this
revalidation section supersedes their statement that no DeepSeek agent made a
temporary RM-005 edit. The temporary edit was confined to the authorized files
and was fully removed before the measurements recorded here.

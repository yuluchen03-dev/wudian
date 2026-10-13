# WUDIAN-KB-V1 Codex Master Plan

## Current State

- Branch: `codex/overall-optimization`; HEAD: `34afd1d` (`fix(ai): verify citations before streaming output`); branch is 23 commits ahead of `origin/main`.
- Working tree is intentionally dirty: current FIX-002/003/004 implementation files and FIX-005A security/streaming changes are present, plus untracked governance and review artifacts. These changes are preserved and are not reset.
- FIX-001 has a recorded independent `TERMINAL PASS`; FIX-002 and FIX-003 are recorded `BLOCKED` because E=11/12 and F=22/40 under the current hash retrieval model; FIX-004 is recorded `PASS` for G=40/40; FIX-005/Q5 is recorded `FAIL` and remains deferred.
- Paseo Desktop daemon is running. `deepseek-harness` is available and exposes `xiaobai/deepseek-v4.1-flash`; this is the selected implementation route. Codex remains the planner and acceptance authority.

## Source of Truth and Constraints

`AGENTS.md`, `docs/kb-v1/ZCODE-HANDOFF.md`, `docs/kb-v1/contracts/QUOTE-VERIFICATION-CONTRACT.md`, the frozen JSONL datasets, and `eval/scripts/metrics.py` are authoritative. No target, Gold case, denominator, contract, production Chroma data, or historical report may be weakened or rewritten. Production Chroma is read only through isolated copies; no `--use-production-chroma` and no `build_index(force=True)`.

## Dependency DAG

```text
RM-001 repository baseline (verified from current tree)
  -> RM-002 security redaction freeze (existing patch requires acceptance)
  -> RM-003 EVAL-FIDELITY-001 (current task)
  -> RM-004 frozen gate rebaseline
  -> RM-005 unsupported refusal
  -> RM-006 Recall@5 / semantic retrieval
  -> RM-007 core claim evidence coverage
  -> RM-008 streaming semantics assessment
  -> RM-009 full regression
  -> RM-010 final frozen evaluation
  -> RM-011 Codex final acceptance
```

RM-003 is the next task because the current reports leave the harness-synthesized `verifiable` gap open. RM-005 through RM-007 cannot be called terminal until their production verdict wiring and frozen metrics are independently demonstrated.

## RM-003 Definition of Done

The frozen fabricated-quote metric must consume the production trust/citation verdict through a thin adapter. The adapter may normalize the production result into the metric schema, but may not implement a second trust engine. `TARGETS`, Gold JSONL, and metrics formulas remain byte-for-byte unchanged. Every case must record both harness and production verdicts, differences, and root cause. Production `text_type` limitations, RFC-1/2/3, Q3, and Q5 remain explicitly open unless independently resolved.

Machine gates: canonical `run_eval.py` executes through the production verdict path; fabricated count is measured with the frozen function; D/H/I/J and all denominators remain unchanged; targeted quote/citation tests pass; backend/frontend regressions and Chroma isolation are recorded. Codex independently samples fake, real, wrong-source, fragment, commentary, cross-sentence, traditional/simplified, and absent quotes before accepting.

## Delegation Protocol

DeepSeek receives one bounded SPEC at a time through Paseo using `deepseek-harness/["xiaobai","deepseek-v4.1-flash"]`. It may edit only files listed in that SPEC, must report `IMPLEMENTATION_COMPLETE` or `BLOCKED`, and must not claim project PASS. Codex reviews the diff, reruns gates, and either accepts, requests exact rework, or records BLOCKED. No automatic push, merge, rebase, reset, or broad staging.

## Final Deliverables

- `docs/kb-v1/CODEX-MASTER-PLAN.md` (this plan)
- `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md` (per-task Codex decisions)
- `docs/kb-v1/FINAL-REMEDIATION-ACCEPTANCE.md` (only after every reachable task is independently verified)
- `deliverables/kb-v1/rm003-fidelity-baseline.json` and task-specific evidence for later RM tasks

## Explicit Blockers

Q3 (corpus provenance/license), Q5 (real application LLM credentials/E2E), the citation `text_type` propagation gap, RFC-1/2/3, and the current E/F ceilings are not silently closed by model availability or by a green harness run.

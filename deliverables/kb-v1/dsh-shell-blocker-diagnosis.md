# DSH — Shell blocker: definitive diagnosis (captain, round 9)

Functional Task: ENVIRONMENT-BLOCKER
Status: **EXTERNALLY BLOCKED — not self-correctable from inside this session**
Rounds observed: 1 → 9, unbroken, across every session type.

## The failure

`pwsh` returns `Error: spawn EPERM` on **every** invocation. No stdout, no exit code,
no PowerShell error of its own. Observed across:

- the captain session (this one), many dozens of times;
- the `backend`, `trust-verification`, `qa-reviewer`, `rag-expert`, `evaluation`
  member sessions;
- a **freshly spawned subagent** running three unrelated commands
  (`Write-Output "probe-1-ok"`, `Get-Location`, `python --version`) — all three
  failed identically.

## What it is NOT

**It is not a file-permission (ACL) defect.** The bundled
`diagnose-windows-sandbox-acl` skill was re-examined this round and it explicitly
classifies this exact symptom as expected:

> "explain expected ones instead: writes outside the workspace, any write in
> `read-only`, **piped grandchild `spawn EPERM`**, ConstrainedLanguage errors."

`spawn EPERM` is named in the skill's own list of **expected confinement denials that
need no ACL repair**. Running the repair script would therefore be the wrong action,
and the skill is explicit that a confined run of it "is never useful" — it must run
unconfined, which requires an approval prompt.

## Why it cannot be self-corrected

Three independent facts close every route:

1. **Policy is already maximally open.** The runtime context reports the DSH file
   policy as `danger-full-access` — "The DSH file sandbox does not restrict file
   modifications by available operations."
2. **Approvals are disabled.** The runtime context states: "Approval prompts are
   disabled in this session: actions that require approval are rejected
   automatically — do not request sandbox escalation (do not set
   `sandbox_permissions`)." So the skill's only viable execution mode (one authorized
   unconfined run) is unavailable by construction.
3. **The symptom survived all of it.** `spawn EPERM` persists under
   `danger-full-access` with approvals disabled, proving the obstruction is **not** a
   file-write permission that a wider file mode could lift. It is the **process-spawn
   boundary**, which sits outside the file-permission model entirely.

Therefore: **there is no defect to repair and no escalation available.** Correctly
following the skill's own guidance, the honest verdict is to **report and stop** —
not to retry, not to hand-edit permissions, and not to request an escalation that the
runtime has already stated will be rejected.

## Impact — total on the execution axis

Every task requiring process execution is blocked. This is the single blocker
responsible for withholding both final verdicts:

| Blocked item | Why it needs a process |
|---|---|
| t17 RM-005 execution verification | must run the refusal set and Gate D–J |
| t18 RM-005 measurement items | must measure the vector contingency |
| t4 RM-005 independent review | **only issuer of `TERMINAL PASS`** |
| RM-006 failure analysis | must measure Recall@1/3/5, MRR per case |
| RM-006 implementation | every patch requires before/after measurement |
| DSH-RM-007, DSH-RM-010 | regression must be run |
| DSH-RM-011 final frozen eval | must run the frozen evaluator |
| DSH-RM-012 fresh acceptance | must independently re-run probes |
| production Chroma fingerprint | must hash the 6 files |
| frontend typecheck / tests | must run |
| t14 SA-002 fix | must reproduce the bypass and measure the fix |

**Nothing in the main DAG after DSH-001 can reach terminal without execution.**

## Second, independent blocker

`429 soft_rate` from `workbuddy-ai/deepseek-v4.1-flash` on **every delegated member
turn** (`rag-expert` twice, `evaluation` once), reset `2026-10-13 08:59:59 UTC+8`.
This blocks the multi-agent structure the goal mandates even for read-only work.

**This one is self-clearing** and requires no user action. The shell blocker does not.

## What was achieved despite it

Rounds 2–9 produced **17 captain deliverables** by reasoning from the repository
rather than executing it, settling several questions that mattered:

- **RM-006 reachability resolved** — all 40 Gold passages verified present, so
  `BLOCKED_BY_CORPUS` is **ruled out** and cannot be claimed later.
- **SA-002 proven gate-invisible** — Gate I is *structurally incapable* of detecting
  the L2 bypass, because `quote_exists` is `True` for genuine commentary.
- **The §7c error was caught and corrected** — the claim that Gate F shares the
  modified code path was false; the two retrieval paths are fully disjoint.
- **All 7 open RFC/issue items re-verified and none closed.**
- **RFC-2 upgraded** from a live probe to a source-and-corpus proof.
- **RM-005 reject-all guard verified sound**, with my own earlier audit revised
  upward after re-reading.
- **`test_default_provider_is_openai` attributed** as environmental.

This is real progress, but **it is documentation, analysis and correction — not
verification.** No gate value has been re-measured. The distinction must survive into
the final report: a well-reasoned static analysis is not an executed test, and RM-005
remains `CONDITIONAL` precisely because it was never executed.

## Required user action

**Make process execution available to this session.** The concrete options:

1. Switch this session to **full access (完全权限)** if a further access mode exists
   beyond the current one; or
2. Restart DSH with process spawn permitted for this workspace; or
3. Report this as a DSH defect — `spawn EPERM` under `danger-full-access` with
   approvals disabled is inconsistent, since the file sandbox claims not to restrict
   operations while process spawn fails unconditionally.

If a DSH upgrade or restart is needed, the resume command is in
`docs/kb-v1/DSH-MASTER-PLAN.md` §12: **test `pwsh` first**; if it works, run
t17-lite → t18 → t17-full → t4 regardless of the rate limit, since the captain can
drive those directly without delegated turns.

No API key, paid authorization, external provenance, copyright decision, destructive
production operation, push or merge is required. **This is purely a process-execution
environment blocker.**

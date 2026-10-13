# DSH commit ledger — precise staging only

Current Gate: DSH-001
Functional Task: WORKTREE-OWNERSHIP / FREEZE
Historical Reference: FIX-001, RM-003

Governance: **NO PUSH.** No `git add .`, no `git add -A`, no merge, no rebase,
no `reset --hard`, no `clean -fd`. Every commit below stages an explicit path
list. The index was verified empty before the first commit.

## Commits created by DSH

Starting HEAD: `34afd1d`

| # | Commit | Subject | Paths | Authority |
|---|---|---|---|---|
| 1 | `775fc8f` | `docs(governance): track AGENTS.md agent-team governance` | `AGENTS.md` | DSH-000 recovery risk: the file existed **only untracked**, so any unauthorized `reset --hard` would have destroyed the project's team governance rules |
| 2 | `fda9da0` | `fix(trust): FIX-001 quote exactness and L1/match_type alignment` | `backend/app/services/quote_verifier.py`, `backend/app/services/citation_guard.py` | **FIX-001 TERMINAL PASS** — `docs/kb-v1/FIX-001-FINAL-REVIEW.md:12` (11/11 acceptance criteria) |
| 3 | `9f158b7` | `test(eval): RM-003 wire frozen fabricated metric to production citation_guard` | `eval/scripts/run_eval.py`, `backend/tests/test_eval_fidelity.py` | **RM-003 / EVAL-FIDELITY-001 PASS (task scope only)** — `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md:5` |
| 4 | `ed9f74d` | `fix(security): stop logging provider exception payloads` | `backend/app/api/ai.py`, `backend/app/api/debate.py`, `backend/app/services/ai_service.py`, `backend/app/services/debate_engine.py` | **DSH-SA-001** — `deliverables/kb-v1/dsh-sa001-security-review.md`: AST sweep → 0 remaining exception-payload log calls; synthetic-marker probe leaks `Bearer sk-…` before the patch and not after |
| 5 | `888b0bc` | `chore: ignore .zcode/ and .agent-teams/ tool state` | `.gitignore` | DSH-000: `git check-ignore` previously exited 1 for both paths |

## Deliberately NOT committed (and why)

| Path | Reason | Unblock condition |
|---|---|---|
| `backend/app/services/rag_service.py` | **Actively being modified by t3 (DSH-RM-005)**. The t1 ownership audit classifies it as the **only genuinely mixed file**: it carries FIX-002 hunks (142-183, 1246-1260, 1315-1397) *and* FIX-003 hunks (973-1085, 1171-1176, 1206-1214) on top of the in-progress RM-005 evidence-sufficiency work. Committing it now would bind an unfinished, unreviewed change to a PASS commit | t3 implementation → t4 independent review → TERMINAL PASS |
| `backend/tests/conftest.py` | **Actively being modified by t15 (DSH-SA-003)** | t15 verify green + review |
| `backend/tests/test_rm005_evidence_sufficiency.py` | t3's new RED test; belongs with the RM-005 commit | t4 TERMINAL PASS |
| `backend/tests/test_fix002_refusal.py` | Belongs to **RM-005, which is BLOCKED** (`CODEX-TASK-ACCEPTANCE.md:57`). Goal §八: "BLOCKED task 的实验代码：不要与 PASS task 混 commit" | RM-005 terminal |
| `backend/tests/test_fix003_recall.py` | Belongs to **RM-006 (pending)**. Same rule | RM-006 terminal |
| `backend/tests/test_fix004_claim_coverage.py` | Belongs to RM-007, whose revalidation (t6) has not run in this goal. Holding so the commit is tied to a task terminal state rather than to a historical claim | t6 revalidation |
| `backend/init_db.py` | t16 (DSH-SA-004) not started | t16 verify green |
| `backend/_sa003_chroma_before.json` | **t15 probe artifact** written into `backend/` root. A fingerprint snapshot, not source; must not be committed | t15 to relocate or remove |
| `eval/eval-run.json` | Transient eval **output artifact**; rewritten by every eval run and will change again at RM-011 | RM-011 final frozen eval |

## Untracked deliverable/evidence tree (not committed by design)

`deliverables/kb-v1/**` holds the audit, probe and acceptance evidence
(`worktree-ownership.md`, `dsh-sa001-security-review.md`,
`rm005-uq0009-vs-sc0003.md`, `rm008-*`, `rm009-*`, `dsh-q3-q5-revalidation.md`,
`dsh-rm005-*` probes). These are **evidence**, deliberately left uncommitted so
that the final acceptance round can commit the complete evidence set once, after
the last task reaches terminal state. They are on disk and unmodified.

## Verification of this ledger

- Index verified empty immediately before commit 1.
- Every `git add` used an explicit path list; no wildcard, no `-A`, no `.`.
- `rag_service.py` and `conftest.py` are **still unstaged** after all five
  commits, confirming the staging was precise rather than sweeping.
- No push was performed. `origin/main` remains 23+ commits behind.

## Model-route discrepancy (recorded, not acted on)

`AGENTS.md` (now committed as `775fc8f`) states the main agent and six specialists
use **GPT-6 Luna**. This goal's explicit instruction is the **configured DeepSeek
model** ("不要切换模型"), and the team is running on
`workbuddy-ai/deepseek-v4.1-flash`. Per the source-of-truth order, the user's
direct instruction for this goal outranks the workspace governance document, so
no model switch was made. Recorded here so the discrepancy is visible rather than
silently resolved. Whether `AGENTS.md` should be updated is a user decision.

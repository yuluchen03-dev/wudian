# DSH MASTER PLAN — WUDIAN-KB-V1 Remediation

Owner: DSH AgentTeams captain (`wudian-dsh-remediation`).
Authority order: repository > latest acceptance/contracts > canonical frozen
metrics > independent test results > current code > historical handoff > prose.

NO PUSH for the entire goal. Production Chroma `backend/chroma_db` is a
read-only data asset.

## 1. Team structure

| Role | Member | Responsibility | Write boundary |
|---|---|---|---|
| Captain / Lead Architect | captain + `lead-architect` | recovery, state, DAG, scope, SPEC, gates, dispatch, verdicts | plan + coordination; may take over a task only on explicit request |
| Explorer (read-only) | `classical-knowledge`, `evaluation` | call chains, tests, contracts, frozen metrics, data, history | read-only |
| Implementer | `trust-verification`, `rag-expert` | minimal patch, tests, docs, precise staging | declared inScope only |
| Tester / Eval Engineer | `evaluation`, `backend` | targeted tests, frozen metrics, regression, before/after | read + eval artifacts |
| Security Reviewer | `backend` (SA-001) | secrets, prod DB, prod Chroma, exception logging, credentials, destructive ops | read-only |
| Independent QA Reviewer | `qa-reviewer` | fresh context, skeptical, read-only, own probes, own metric reruns, own diff inspection | read-only; sole `TERMINAL PASS` authority |

An implementer never awards its own final PASS. Only `qa-reviewer` may issue
`TERMINAL PASS`.

## 2. Task ID governance

Historical RM/FIX numbering has drifted. Old documents are NOT renamed. From
this goal forward every task is reported with three labels:

```text
Current Gate:        DSH-RM-005
Functional Task:     UNSUPPORTED-REFUSAL
Historical Reference: FIX-002 / earlier RM-005
```

## 3. Main execution DAG

```text
DSH-000  Repository Recovery           [captain, DONE this session]
   ↓
DSH-001  Worktree Ownership / Freeze   [t1 lead-architect]
   ↓
DSH-RM-005 Unsupported Refusal         [t2 trace → t3 impl → t4 review]
   ↓
DSH-RM-006 Retrieval Recall            [t5 analysis → impl → independent review]
   ↓
DSH-RM-007 Claim Evidence Revalidation [t6 — regression verification only]
   ↓
DSH-RM-008 Open Fidelity / text_type    [t7 assessment]
   ↓
DSH-RM-009 Streaming Semantics          [t8 assessment]
   ↓
DSH-RM-010 Full Regression              [t11]
   ↓
DSH-RM-011 Final Frozen Eval
   ↓
DSH-RM-012 Fresh Independent Acceptance
   ↓
Final Report
```

Read-only analysis may run in parallel. Core code writes follow the dependency
order strictly. RM-005 must be terminal before RM-006 implementation starts,
because both edit `backend/app/services/rag_service.py` and the Team runtime
enforces non-overlapping write scope.

Parallel read-only streams that do not touch the core write path:

- `DSH-SA-001` security review (t9)
- `DSH-Q35` Q3/Q5 status revalidation (t10)

## 4. Frozen targets (must not be modified)

| Gate | Metric | Target |
|---|---|---|
| D | `quote_exactness` | >= 0.99 |
| E | `unsupported_correct_refusal` | >= 0.95 |
| F | `recall_at_5` | >= 0.90 |
| G | `core_claim_evidence_coverage` | >= 0.95 |
| H | `source_attribution` | >= 0.98 |
| I | `fabricated_classical_quote` | == 0 (absolute count) |
| J | `school_leakage` | < 0.01 |

Authority: `eval/scripts/metrics.py` frozen functions and `TARGETS`.

## 5. Verified starting state

From `docs/kb-v1/DSH-CURRENT-STATE.md`:

| Gate | Last recorded | Notes |
|---|---|---|
| D | 18/18 = 1.0 PASS | re-measure required |
| E | 11/12 = 0.9167 FAIL | **primary blocker**; 0.95 with denominator 12 means 12/12 |
| F | 22/40 = 0.55 FAIL | target needs >= 36/40; 35/40 = 0.875 fails |
| G | 40/40 = 1.0 PASS | revalidate after RM-006 |
| H | 18/18 = 1.0 PASS | re-measure required |
| I | 0/20 PASS | now driven by production `citation_guard` (EVAL-FIDELITY-001) |
| J | 0/19 PASS | denominator 19 must not shrink |

Backend: `522 passed, 1 failed, 297 subtests` — the failure is the pre-existing
`LLM_PROVIDER=agnes` environment mismatch in
`test_default_provider_is_openai`. It must never be reported as "all backend
tests pass".

Frontend: TypeScript PASS, 41 tests PASS (historical; re-run required).

## 6. Root cause established for RM-005 (captain probe)

`uq-0009` (`如何面对亲人的离世？`) retains 9 verses across the four sages while
`sc-0003` retains 3. Vector search returns **zero** for `uq-0009` on all four
sages, so every surviving hit comes from the keyword layer
`_debate_keyword_search` (`rag_service.py:526-570`), which scores
`score += 3.0` for each corpus keyword that is a substring of the query and then
keeps anything with `score > 0`. Because `_extract_keywords` also emits
single-character and bigram fragments, a semantically unrelated query still
scores above zero.

Primary classification: **C — weak evidence binder** (the keyword layer treats
character-level overlap as evidence). Secondary factors are recorded by the
trace task `t2`.

The fix must therefore be **structural** (which lexical overlaps count as
evidence), not a tuned scalar. A previous word-level guard round was rejected
because it cleared legal `sc-0003` hits and would have shrunk Gate J's
denominator from 19 to 18.

## 7. Repair loop policy

Per task: at most 3 implementation/rework cycles.

```text
PLAN → IMPLEMENT → TARGETED TEST → SELF REVIEW → INDEPENDENT REVIEW
```

On `FIX_REQUIRED` the reviewer must return the exact defect, the exact failing
case and the exact gate; the implementer fixes only that. Three failed cycles
yields `BLOCKED_ENGINEERING` rather than unbounded refactoring.

## 8. Honest-blocker policy

Autonomous execution — the captain does not ask the user whether to create a
team, run tests, add a reviewer, take a minimal patch, write a report, continue
to the next task, or commit an independently-PASSed task.

A task may stop as BLOCKED only for: a real API key, paid authorization,
external provenance, a copyright/licensing decision, a destructive production
operation, a push/merge, or a real fact unobtainable from the repository.

A blocker never terminates the goal. Record it and continue all independent
tasks.

## 9. Standing non-goals

- No push, merge, rebase, `reset --hard`, `clean -fd`, `git add .`, `git add -A`.
- No Gold/TARGETS/contract modification to force a pass.
- No denominator shrinking.
- No `build_index(force=True)` against production.
- No secret printing, saving or committing.
- No unrelated refactors, no corpus expansion, no UI changes.
- No closing RFC-1/2/3 by virtue of a green metric.

## 10. Gate entry-point map (verified by call graph)

Established by reading `eval/scripts/run_eval.py` and `rag_service.py`. This
determines which task owns which gate, and it corrected a captain error.

| Gate | Metric | Call site | Entry point |
|---|---|---|---|
| D | `quote_exactness` | `:177` | `_quote_prediction` → `verify_quote` (`:114`) |
| E | `unsupported_correct_refusal` | `:252` | `retrieve_for_debate_sage` |
| F | `recall_at_5` | `:320` | **`retrieve_for_sage_chat`** |
| G | `core_claim_evidence_coverage` | `:370` | `_load("retrieval_gold")` + `load_corpus`, **no retrieval** |
| H | `source_attribution` | `:178` | `_quote_prediction` → `verify_quote` |
| I | `fabricated_classical_quote` | `:199` | `_production_adversarial_prediction` → **production** `guard_citations` |
| J | `school_leakage` | `:296` | `retrieve_for_debate_sage` |

Three distinct surfaces, not two:

1. **Retrieval-dependent:** E, F, J (two disjoint paths as below).
2. **Quote-verifier-dependent:** D, H (`_quote_prediction`, `:114-130`).
3. **Guard-dependent:** I (`:150-166`, the only gate that consumes the *production*
   citation guard — this is what EVAL-FIDELITY-001 is about).

Gate G is **retrieval-independent**: `eval_claim_coverage` (`:341-371`) loads the
corpus and Gold directly and never calls a retrieval function. Its denominator is
**claims, not passages** (`metrics.py:333-336`), and `run_eval.py:363-368` emits
exactly one core claim per record — so G's denominator is structurally **40**, one
per query, and its result is 40/40.

**Note on G's silent-skip behaviour (checked, not a defect):** `:356-357` skips a
Gold `expected_passage_id` that is absent from the corpus, which would mark the
claim uncovered. That is fail-closed and correct, and the coverage gap is already
guarded by `backend/tests/test_eval_baseline.py:115`
`test_all_expected_passage_ids_resolve`, which asserts every Gold passage id
resolves against the real corpus. No new guard is needed here.

**The debate path (E, J) and the chat path (F) are fully disjoint.** Every
RM-005 helper — `_debate_keyword_search` (`:672`), `_query_has_corpus_support`
(`:634`), `_debate_vector_search` (`:769`) — has exactly one call site, all inside
`retrieve_for_debate_sage`. `retrieve_for_sage_chat` instead uses `vector_search` +
`_kw_search_chroma` (`:1333`) + `_merge_retrieval` (`:1334`).

Consequences that constrain the DAG:

- RM-005 **cannot** regress Gate F; RM-006 **cannot** fix Gate E. The tasks own
  disjoint surfaces.
- RM-006's real surface is `retrieve_for_sage_chat` + `vector_search` +
  `_kw_search_chroma` + `_merge_retrieval`. Nothing else.
- Gate J's denominator is driven by **debate-path** reachability, so only changes
  to `retrieve_for_debate_sage` can move it (see RFC-GATE-J).
- Fix-order steps 7-9 (BM25/dense/fusion) are **not greenfield**:
  `retrieve_for_sage_chat:1329-1334` already implements two-layer fusion, added by
  FIX-003 because the pure-vector baseline was 0.325. They must be **measured
  before being changed**; re-tuning unmeasured fusion weights is how 0.55 becomes
  0.40.

Full record: `deliverables/kb-v1/dsh-gate-entrypoint-isolation.md`.

## 11. Environment blocker — shell (round 9 status: EXTERNALLY BLOCKED, not self-correctable)

`pwsh` returns `spawn EPERM` on every invocation for every session tested: the
captain, backend, trust-verification, qa-reviewer, rag-expert, evaluation, and a fresh
subagent probe. This is the documented DSH sandbox confinement boundary for process
spawning — the `diagnose-windows-sandbox-acl` skill explicitly classifies `spawn
EPERM` as **expected** confinement behaviour requiring no ACL repair, so it is not a
correctable permission fault.

Independently confirmed in round 4 by a **freshly spawned subagent** (separate
session): three unrelated commands (`Write-Output`, `Get-Location`,
`python --version`) all returned `spawn EPERM` at process-spawn time with no
stdout, no exit code and no PowerShell error. Environment-level, not per-command.

### Round 9: every remaining route is now closed

1. **Policy is already maximal.** The runtime reports the DSH file policy as
   `danger-full-access`: "The DSH file sandbox does not restrict file modifications
   by available operations."
2. **Approvals are disabled.** The runtime states approval prompts "are rejected
   automatically — do not request sandbox escalation (do not set
   `sandbox_permissions`)". The ACL skill's only useful mode (one authorized
   unconfined run) is therefore unavailable by construction.
3. **The symptom survived all of it.** `spawn EPERM` persists under
   `danger-full-access` with approvals disabled, proving the obstruction is **not** a
   file-write permission a wider file mode could lift. It is the **process-spawn
   boundary**, outside the file-permission model entirely.

**Verdict: there is no defect to repair and no escalation available.** Per the skill's
own guidance the correct action is to **report and stop** — not to retry, not to
hand-edit permissions, and not to request an escalation the runtime has already said
will be rejected. Full record:
`deliverables/kb-v1/dsh-shell-blocker-diagnosis.md`.

Blocked by it: t17, t18 (measurements), t11, t12, t13, t15/t16 verification, t19,
t4 (the sole `TERMINAL PASS` issuer), all of RM-006, and the fresh Chroma
fingerprint. **Nothing in the main DAG after DSH-001 can reach terminal without
execution.** Everything shell-free has been completed; see
`docs/kb-v1/FINAL-REMEDIATION-ACCEPTANCE.md` §9.

**Required user action:** make process execution available — switch this session to
full access (完全权限) if a further mode exists, restart DSH with process spawn
permitted for this workspace, or report it as a DSH defect (`spawn EPERM` under
`danger-full-access` with approvals disabled is inconsistent with a sandbox that
claims not to restrict operations).

## 12. Second blocker — model-route rate limit (round 4)

Distinct from the spawn failure and must not be confused with it:

| | Spawn blocker | Rate-limit blocker |
|---|---|---|
| Symptom | `spawn EPERM` on every `pwsh` call | `429 soft_rate` from the provider |
| Scope | all sessions, all members, all commands | **delegated member turns only** |
| Captain affected | yes | **no — captain turns still work** |
| Self-correctable | no | no — requires the limit to reset |
| Reset | unknown | **2026-10-13 08:59:59 UTC+8** (reported) |

Member `rag-expert` failed t20's turn with *"usage exceeds frequency limit … reset
at 2026-10-13 08:59:59 UTC+8"*.

**Switching model route is forbidden by the goal** ("不要切换模型。不要降级成单
Agent"). No switch was made. Work that requires a member turn is suspended until
the limit resets; work the captain can do directly (documentation, source tracing,
static audit) continues.

**Resume rule for the next round:** test `pwsh` first. If it works, run
t17-lite → t18 → t17-full → t4 regardless of the rate limit, since the captain can
drive those. If `pwsh` is still dead, check whether the rate limit has reset
before dispatching any member task, and prefer captain-direct static work.

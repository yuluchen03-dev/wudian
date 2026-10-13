# DSH-001 — Dirty-Worktree Ownership Classification

Task: **t1 / DSH-001**. Scope: classify, do not commit, do not stage.
This document is the only artifact produced by this task.

## 0. Method and evidence basis

Read-only inspection of the repository at

- branch `codex/overall-optimization`, HEAD `34afd1d8b4c9150e0cdf2fa1c72612a83e905299`
  (`fix(ai): verify citations before streaming output`)
- `git status --porcelain=v1` → 8 unstaged modified + 22 untracked (1 dir, 21 files)
- **staged index is EMPTY**: `git rev-parse :backend/app/services/citation_guard.py`
  returns blob `6a33f05…`, which is HEAD's blob, not the worktree blob `64148af…`.
  No path in this classification is staged. Nothing was committed in this task.
- per-file `git diff` (full hunks, including `-U0` anchors), per-file reads of every
  untracked file, and cross-reference to the task-authority documents listed in §3.

Totals reconcile exactly with `docs/kb-v1/DSH-CURRENT-STATE.md` §1:
`8 files changed, 401 insertions(+), 30 deletions(-)` and 22 untracked paths.

Classification vocabulary (per task contract): `FIX-001` / `RM-003 (EVAL-FIDELITY-001)` /
`refusal (FIX-002)` / `retrieval (FIX-003)` / `claim evidence (FIX-004)` / `security` /
`acceptance docs` / `tool-state` / `unknown`.

Commit recommendation vocabulary: `precise-stage-and-commit` (legitimate, separable,
highest-FIX-number-first ordering) / `precise-stage-and-commit (with dependency caveat)` /
`keep-uncommitted` / `never-commit`.

**Global rule applied:** in every file that carries more than one logical change, the
hunks are provably disjoint — they sit in different functions/methods, and no hunk's
line range is a prerequisite for another hunk's correctness. No "hunk-splitting beyond
`git add -p`" is required anywhere: `git add -p` alone is sufficient to stage exactly the
recommended hunks in all three shared files. Files that cannot be safely separated are
recommended `keep-uncommitted` per the hard rules.

---

## 1. Master table — tracked (unstaged modified) paths

| Path | Tracked state | Owning logical change | Evidence (diff hunk / test / report) | Verifiable? | Commit recommendation |
|---|---|---|---|---|---|
| `backend/app/services/citation_guard.py` | modified, unstaged | **RM-003 (EVAL-FIDELITY-001)** | Hunks at new lines **255–288**, **372–375**, **402**, **421–422**, **453**. Adds `GuardedCitation.exact_match`/`.match_type` + pure adapter `metric_prediction_from_guarded`; header comment names EVAL-FIDELITY-001. Proof: `backend/tests/test_eval_fidelity.py` (imports `metric_prediction_from_guarded`); `deliverables/kb-v1/rm003-fidelity-report.md` §Files Changed item 1; `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md` RM-003 verdict PASS. The `exact_match` refactor at L372–375/402 is behaviour-preserving (`decide_trust_state` receives the same predicate value, previously inlined). | **Yes** — test-verifiable and diff-verifiable | `precise-stage-and-commit` |
| `eval/scripts/run_eval.py` | modified, unstaged | **RM-003 (EVAL-FIDELITY-001)** (all 4 hunks, no FIX-003 content) | Hunks at new lines **133–168** (`_production_refs`, `_production_adversarial_prediction`), **187–192**, **196–197**, **217–225**. `eval_adversarial()` switches to the production verdict path. Proof: `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md` RM-003 (isolated canonical eval, I `0/20`); `rm003-fidelity-report.md` §Files Changed item 2. No FIX-003/D2 keyword-fusion code is present in this diff. | **Yes** — diff-verifiable | `precise-stage-and-commit` |
| `backend/app/services/quote_verifier.py` | modified, unstaged | **claim evidence (FIX-004)** | Hunks at new lines **234** (`_sage_key` → `sage_key`) and **240–247** (`passage_id=f"debate:{sage_key}:{verse_id}"`), plus comment at **250**. Proof: `backend/tests/test_fix004_claim_coverage.py` (the in-code comment at L240–247 cites FIX-004 and its test); `docs/kb-v1/FIX-004-FINAL-REVIEW.md` §0 PASS with G `40/40`; `CODEX-TASK-ACCEPTANCE.md` G `40/40 = 1.0`. | **Yes** — test-verifiable | `precise-stage-and-commit` |
| `backend/app/api/ai.py` | modified, unstaged | **security** (FIX-005A credential-redaction follow-up) | Hunk at new lines **166–169**: `except Exception as e:` → `except Exception:`, drops `%s`, `e`, adds the "不记录异常负载…Authorization/Bearer" comment. Proof: `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1 table row `backend/app/api/ai.py:168`, and its 401/403 sentinel-leak probe (L188–192). **Baseline note:** HEAD already rewrote this file (103 lines) for streaming citation verification; this one hunk is the redaction delta on top. | **Yes** — diff-verifiable; runtime leak probe recorded in FIX-005 doc (not re-run in t1) | `precise-stage-and-commit (with dependency caveat)` |
| `backend/app/api/debate.py` | modified, unstaged | **security** | 10 identical hunks at new lines **119, 151, 188, 197, 224, 264, 293, 333, 362, 386**: each drops the `%s`/`e` exception payload from `logger.error(...)`. Proof: `FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1 lists the residual-leak sweep; no functional/response change is present in this file (HTTP status and `detail` strings untouched). | **Yes** — diff-verifiable | `precise-stage-and-commit` |
| `backend/app/services/ai_service.py` | modified, unstaged | **security** | Hunks at new lines **120–122** (`explain_verse`) and **595–597** (`generate_quiz`): `except Exception as e` → `except Exception`, payload removed, same comment. Proof: `FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1 rows `ai_service.py:121` and `:595`. **Baseline note:** HEAD already rewrote this file (276 lines); these are the redaction deltas. | **Yes** — diff-verifiable | `precise-stage-and-commit (with dependency caveat)` |
| `backend/app/services/debate_engine.py` | modified, unstaged | **security** (with an outward-contract facet) | Hunks at new lines **514–516**, **596–598**, **833–835**. Two facets: (a) redaction — `logger.error("...: %s", e)` → no payload; (b) **response change** — `"error": str(e)` → `"error": "llm_unavailable"` on the two streaming `sage_error` events. Evidence: `FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1 rows `debate_engine.py:514` and `:595` ("记录 `e` 并把 `str(e)` 回传客户端" → "对外改为稳定错误码 `llm_unavailable`"). This facet touches the client-visible wire format, so it is RM-008 (streaming semantics) adjacent — classified `security` because the redaction is the primary intent and the code comment says so, but flagged for RM-008 review. | **Yes** — diff-verifiable | `precise-stage-and-commit (with dependency caveat)` |
| `backend/app/services/rag_service.py` | modified, unstaged | **MIXED: refusal (FIX-002) + retrieval (FIX-003)** | Hunks at new lines **142–183** (FIX-002 module constants `_OUT_OF_SCOPE_*`, `_MODERN_TECH_TERMS`, `_GEN_VERB_RE`), **973–1085** (FIX-003 `_kw_search_chroma` + `_merge_retrieval`), **1171–1176** (FIX-003 vector+lexical fusion in `retrieve_for_sage_chat`), **1206–1214** (FIX-003 D1 id alignment), **1246–1260** (FIX-002 guard call in `retrieve_for_debate_sage`), **1315–1397** (FIX-002 `_cn_to_int` + `_query_out_of_scope`). Proof: `backend/tests/test_fix002_refusal.py` (FIX-002 hunks) and `backend/tests/test_fix003_recall.py` (FIX-003 hunks); `docs/kb-v1/FIX-002-FINAL-REVIEW.md` (**BLOCKED**, E `11/12`) and `docs/kb-v1/FIX-003-FINAL-REVIEW.md` (**BLOCKED**, F `22/40`). See §2 — this single file spans **two different verdict classes**. | **Yes** — the two hunk groups are disjoint and independently testable | `keep-uncommitted` (single-file mixed status; see §2) |

### Tracked-path notes

- `FIX-002` is **BLOCKED** and `FIX-003` is **BLOCKED** as recorded verdicts
  (`FIX-002-FINAL-REVIEW.md` §0, `FIX-003-FINAL-REVIEW.md` §0, restated in
  `CODEX-TASK-ACCEPTANCE.md` §RM-005 and `CODEX-MASTER-PLAN.md` §Current State).
  FIX-004 is separately recorded **PASS** (`FIX-004-FINAL-REVIEW.md` §0, G `40/40`) and
  RM-003 **PASS for task scope only** (`CODEX-TASK-ACCEPTANCE.md` §RM-003).
- The hard rule "BLOCKED-task experimental code must not be mixed into a PASS-task
  commit" is therefore decisive: FIX-002 and FIX-003 code must never be bundled with
  the FIX-004/RM-003 PASS material.
- `citation_guard.py` and `quote_verifier.py` were last changed by commits
  `31afdc8` / `d35bb17` (trust layer), not by HEAD; their worktree diffs are purely the
  RM-003 and FIX-004 deltas above. `ai.py` and `ai_service.py` **were** rewritten by HEAD,
  so their working-tree diffs must be read as redaction deltas stacked on that rewrite.

---

## 2. The one mixed file — why `rag_service.py` is `keep-uncommitted`

`backend/app/services/rag_service.py` is the only path whose hunks belong to **two
different logical changes with two different verdict classes**:

| Hunk group (new-file lines) | Logical change | Recorded verdict | Must be committed with |
|---|---|---|---|
| 142–183; 1246–1260; 1315–1397 | refusal (FIX-002) | **BLOCKED** (E `11/12`) | `backend/tests/test_fix002_refusal.py` only |
| 973–1085; 1171–1176; 1206–1214 | retrieval (FIX-003) | **BLOCKED** (F `22/40`) | `backend/tests/test_fix003_recall.py` only |

The hunk groups are **technically disjoint** — `_query_out_of_scope` and
`_kw_search_chroma`/`_merge_retrieval` touch different methods and different line
regions, and neither calls the other. So `git add -p backend/app/services/rag_service.py`
*could* in principle stage one group without the other. I nevertheless recommend
**`keep-uncommitted`**, for these recorded reasons:

1. **Both owners are BLOCKED.** Committing either group would create a commit whose
   task-level verdict is BLOCKED. Per the profile protocol, only Gate-passing phases are
   committed, and a BLOCKED task must not be presented as landed work.
2. **Neither group is a clean standalone artifact.** The FIX-003 D2 fusion hunks
   (`973–1085`, `1171–1176`) depend on module-level state introduced by the FIX-002
   constant block only in the sense of shared file position, but the FIX-003 test file
   `test_fix003_recall.py` also asserts the FIX-002 guard semantics
   (`Fix003GuardRegressionTest`, L202–232) and hard-codes FIX-002-dependent recall
   expectations (`sc-0003` hits preserved, L226–232). Staging FIX-003 without FIX-002
   would make `test_fix003_recall.py` fail against the new commit — i.e. the commit would
   not be self-consistent.
3. **Consequently the two groups form a bidirectional test coupling**, not a clean
   separation: FIX-002's test file does not need FIX-003, but FIX-003's test file needs
   FIX-002. The dependency runs one way only, so a strictly-FIX-002 commit is *possible*;
   yet it would still be a BLOCKED-verdict commit, so rule (1) already settles the
   recommendation.
4. If the captain later authorizes committing a BLOCKED-but-honest partial improvement,
   the correct minimal action is: `git add -p` the FIX-002 hunks **plus** the whole
   `test_fix002_refusal.py`, never the FIX-003 hunks. That authorization does **not**
   exist in this task, so the recommendation stands as `keep-uncommitted`.

The corresponding untracked tests are therefore also `keep-uncommitted` (§3), so that
code and its only proof stay together and nothing BLOCKED enters history.

---

## 3. Master table — untracked paths

| Path | Tracked state | Owning logical change | Evidence | Verifiable? | Commit recommendation |
|---|---|---|---|---|---|
| `.zcode/` (dir: `team/`, `workflow-drafts/`, `workflow-runs/`; 24 files) | untracked | **tool-state** | ZCode agent/team config (`team/agents/*.md`) and workflow drafts/runs (`.dwf.ts`, `dwfrun-*.mjs`, mtimes 2026-09-25…10-09). Not referenced by any source, test, or eval file. Hard rule: `.zcode/` must be `never-commit`. `git check-ignore` returns nothing → **currently NOT gitignored**, so it appears as an untracked hazard in every `git status`. | N/A — not project content | `never-commit` (recommend the captain add `.zcode/` to `.gitignore` in a later, separately-authorized task) |
| `AGENTS.md` | untracked | **acceptance docs** (governance) | Repo-root governance file read by the team; declares gates, scope, Chroma safety, git rules, and the explicit open items. Its own content is consistent with `docs/kb-v1/CODEX-MASTER-PLAN.md` §Source of Truth. Note: it is the authoritative governance text for this goal, and it is **untracked** — a real recovery finding, not a defect of its content. | **Yes** — content-verifiable; but see caveat | `keep-uncommitted` (see caveat) |
| `backend/tests/test_eval_fidelity.py` | untracked | **RM-003 (EVAL-FIDELITY-001)** | Imports exactly `guard_citations` + `metric_prediction_from_guarded` (L22–25); asserts `verdict_basis == "production citation_guard.guard_citations"` (L160); counts `133 passed` in `CODEX-TASK-ACCEPTANCE.md` §RM-003. Uses isolated fixtures, no production Chroma. | **Yes** — test-verifiable | `precise-stage-and-commit` |
| `backend/tests/test_fix002_refusal.py` | untracked | **refusal (FIX-002)** | Docstring names the FIX-002 guard set and the captain's G5 prohibition; asserts 11 guarded queries, honest `uq-0009` positive-hit behaviour (L122–128), and `sc-0003` preservation (L164–167). Evidence of record: `CODEX-TASK-ACCEPTANCE.md` §RM-005 (`6 passed, 41 subtests`) and `FIX-002-FINAL-REVIEW.md` (BLOCKED). | **Yes** — test-verifiable | `precise-stage-and-commit` — **only if** the captain authorizes landing the BLOCKED FIX-002 partial and jointly stages the FIX-002 hunks of `rag_service.py`; otherwise `keep-uncommitted` |
| `backend/tests/test_fix003_recall.py` | untracked | **retrieval (FIX-003)** | Docstring cites FIX-003 D1/D2 and the `0.325 → 0.55` measurement; `Fix003GuardRegressionTest` (L202–232) re-asserts FIX-002 semantics, so it cannot be committed before FIX-002. Evidence: `FIX-003-FINAL-REVIEW.md` (BLOCKED, F `22/40`). | **Yes** — test-verifiable | `keep-uncommitted` (same BLOCKED rationale as §2; also coupled to FIX-002) |
| `backend/tests/test_fix004_claim_coverage.py` | untracked | **claim evidence (FIX-004)** | Docstring cites FIX-004 key alignment; asserts `debate:{sage_key}:` keys (L100–108), 73/73 resolvable ids (L110–117), G `40/40` (L138–148). Matches `FIX-004-FINAL-REVIEW.md` PASS. | **Yes** — test-verifiable | `precise-stage-and-commit` |
| `deliverables/kb-v1/dsh-rm005-probe.py` | untracked | **unknown** (diagnostic probe authored in this session) | Read in full: read-only probe that copies production Chroma to a temp dir, sets `CHROMA_PERSIST_DIR`, and prints per-sage hit counts for `uq-0009`/`sc-0003`. No task ID, no acceptance doc, no test references it. It is cited only by `DSH-CURRENT-STATE.md` §6 as *this session's* probe. | Partially — script is readable, but it has **no recorded acceptance** and belongs to no delivered task | `keep-uncommitted` — `unknown` MUST NOT be committed; retain as working evidence only |
| `deliverables/kb-v1/dsh-rm005-probe-out.txt` | untracked | **unknown** (raw probe output) | 3230-byte raw transcript of the probe above; summarised in `DSH-CURRENT-STATE.md` §6 table. Same provenance gap: no acceptance, no owning task. | Partially — raw output readable, unaccepted | `keep-uncommitted` — `unknown` MUST NOT be committed |
| `deliverables/kb-v1/rm003-fidelity-baseline.json` | untracked | **RM-003 (EVAL-FIDELITY-001)** | Self-describes `"task": "RM-003 / EVAL-FIDELITY-001"`; per-case harness-vs-production verdicts for all 20 adversarial records. **Honesty caveat recorded inside the file**: `"measurement_status": "runtime NOT executed"` — verdicts are `static_reasoned`, not measured (L8–9, L35). | **Yes** for provenance; **NO** as measurement evidence (self-declared static) | `precise-stage-and-commit` — bind it to the RM-003 commit and preserve the `runtime NOT executed` marker verbatim |
| `deliverables/kb-v1/rm003-fidelity-report.md` | untracked | **RM-003 (EVAL-FIDELITY-001)** | Title/§TASK ID name RM-003; §Files Changed maps 1:1 onto the `citation_guard.py` and `run_eval.py` hunks; §Baseline vs 本轮复现 explicitly separates the static baseline from Codex's independent re-run (L26–40). | **Yes** — report-verifiable | `precise-stage-and-commit` |
| `deliverables/kb-v1/rm004-frozen-gate-rebaseline.json` | untracked | **acceptance docs** (RM-004 baseline record) | `"task": "RM-004 frozen gate rebaseline"`, `"verdict": "BASELINE_RECORDED"`, seven gate values, `used_production_chroma: false`, plus read-only SHA-256 fingerprints of six production files. Cross-checks exactly with `CODEX-TASK-ACCEPTANCE.md` §RM-005 numbers. | **Yes** — structured, cross-checkable | `precise-stage-and-commit` |
| `docs/kb-v1/CODEX-MASTER-PLAN.md` | untracked | **acceptance docs** (plan) | Declares the RM-001…RM-011 DAG, the intentional-dirty-tree policy, and the delegation protocol; its §Current State matches the observed worktree. | **Yes** — content-verifiable | `precise-stage-and-commit` |
| `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md` | untracked | **acceptance docs** (acceptance ledger) | The source-of-truth acceptance file per `DSH-CURRENT-STATE.md` §2; carries RM-003 PASS (task scope) and **RM-005 BLOCKED** with full verification bullets. | **Yes** — content-verifiable | `precise-stage-and-commit` |
| `docs/kb-v1/DSH-RM003-SPEC.md` | untracked | **RM-003 (EVAL-FIDELITY-001)** | Named as `grading_authority` by `rm003-fidelity-baseline.json` L4; bounds the RM-003 scope. | **Yes** — content-verifiable | `precise-stage-and-commit` |
| `docs/kb-v1/DSH-RM005-SPEC.md` | untracked | **acceptance docs** (RM-005 spec) | SPEC for the RM-005 refusal task whose recorded verdict is BLOCKED. A spec is not implementation code; committing it does not land BLOCKED behaviour. | **Yes** — content-verifiable; **never** committable as proof of RM-005 success | `precise-stage-and-commit` — as documentation only; must not be read as RM-005 closure |
| `docs/kb-v1/FIX-001-FINAL-REVIEW.md` | untracked | **FIX-001** (acceptance docs) | Title/verdict header; FIX-001 is recorded `TERMINAL PASS` in `CODEX-MASTER-PLAN.md` §Current State. | **Yes** — report-verifiable | `keep-uncommitted` — see caveat below |
| `docs/kb-v1/FIX-002-FINAL-REVIEW.md` | untracked | **refusal (FIX-002)** acceptance docs | Verdict **BLOCKED** (E `11/12`); document review only. | **Yes** — report-verifiable | `precise-stage-and-commit` — the review document is legitimate history; it must not be committed as FIX-002 success |
| `docs/kb-v1/FIX-003-FINAL-REVIEW.md` | untracked | **retrieval (FIX-003)** acceptance docs | Verdict **BLOCKED** (F `22/40`); document review only. | **Yes** — report-verifiable | `precise-stage-and-commit` — same caveat |
| `docs/kb-v1/FIX-004-FINAL-REVIEW.md` | untracked | **claim evidence (FIX-004)** acceptance docs | Verdict **PASS — FIX-004 / GATE-G**, G `40/40`; also records the reviewer-substitution limitation (quantum failure → captain completed it). | **Yes** — report-verifiable | `precise-stage-and-commit` |
| `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md` | untracked | **security** acceptance docs | §7.1 maps every redaction change to its exact file:line and records the 401/403 sentinel probe; §7.1 also discloses 18 residual unscoped log sites. It is the primary evidence for the `ai.py`/`debate.py`/`ai_service.py`/`debate_engine.py` security diffs. | **Yes** — report-verifiable; its Q5 verdict remains **FAIL/unresolved** | `precise-stage-and-commit` — as security-redaction evidence; Q5 must stay explicitly open |
| `docs/kb-v1/RM-004-FROZEN-GATE-REBASELINE.md` | untracked | **acceptance docs** (RM-004 baseline) | Narrative companion to `rm004-frozen-gate-rebaseline.json`; states isolation method and explicitly refuses to close E/F. | **Yes** — report-verifiable | `precise-stage-and-commit` |
| `docs/kb-v1/ZCODE-HANDOFF.md` | untracked | **acceptance docs** (handoff) | Handoff record at HEAD `899519b`, listing the pre-existing gate table and the "do not reset the dirty tree" instruction. Note it names `899519b`, i.e. it **pre-dates** `34afd1d`. | **Yes** — content-verifiable; snapshot is stale relative to HEAD | `keep-uncommitted` — see caveat below |
| `docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json` | untracked | **acceptance docs** (handoff snapshot) | JSON snapshot companion to the handoff; same `899519b` provenance. | **Yes** — content-verifiable; stale vs HEAD | `keep-uncommitted` — see caveat below |
| `docs/kb-v1/ZCODE-START-PROMPT.md` | untracked | **acceptance docs** (bootstrap prompt) | Start prompt for the ZCode team; governance bootstrap text. | **Yes** — content-verifiable | `keep-uncommitted` — see caveat below |

### Untracked-path caveat (handoff cluster)

`AGENTS.md`, `ZCODE-HANDOFF.md`, `ZCODE-HANDOFF-SNAPSHOT.json` and
`ZCODE-START-PROMPT.md` are governance/handoff material describing HEAD `899519b`,
which is **one commit behind the current HEAD `34afd1d`**. They are classified
`acceptance docs` (not `unknown`), and their content is verifiable — but their
suitability for inclusion in *this* remediation's Phase-0 commit is a captain/QA
decision, not an automatic one, because they document a superseded snapshot and
`AGENTS.md` additionally hard-codes the old seven-role ZCode team model. I therefore
recommend `keep-uncommitted` for this cluster until the captain either refreshes the
snapshot fields to `34afd1d` or explicitly authorizes committing them as historical
records. This is a deliberate conservatism, not an `unknown` classification: the
`unknown` rule (never commit) is applied separately and strictly to the two
`dsh-rm005-probe*` artifacts.

---

## 4. Commit-granularity summary

Grouped by owning logical change, with the exact paths each commit would contain.
**No commit is created by this task.** Ordering follows the rule "highest FIX/RM number
first" only where a dependency forces it; otherwise order is by readiness.

| Order | Proposed commit subject | Files (exact staging set) | Status class | Blocked by |
|---|---|---|---|---|
| 1 | `fix(trust): wire fabricated metric to production citation verdict (RM-003)` | `backend/app/services/citation_guard.py`, `eval/scripts/run_eval.py`, `backend/tests/test_eval_fidelity.py`, `docs/kb-v1/DSH-RM003-SPEC.md`, `deliverables/kb-v1/rm003-fidelity-baseline.json`, `deliverables/kb-v1/rm003-fidelity-report.md` | RM-003 **PASS (task scope)** | Nothing (self-contained). Do **not** add `rag_service.py` or `quote_verifier.py`. |
| 2 | `fix(evidence): align debate corpus ids with Gold double-layer prefixes (FIX-004)` | `backend/app/services/quote_verifier.py`, `backend/tests/test_fix004_claim_coverage.py`, `docs/kb-v1/FIX-004-FINAL-REVIEW.md` | FIX-004 **PASS** (G `40/40`) | Nothing. Independent of RM-003 (different file, different metric). |
| 3 | `fix(security): redact LLM provider exception payloads from logs` | `backend/app/api/ai.py`, `backend/app/api/debate.py`, `backend/app/services/ai_service.py`, `backend/app/services/debate_engine.py`, `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md` | security; Q5 itself **FAIL/unresolved** | `ai.py`/`ai_service.py` are applied on top of HEAD's rewrite — commit only if the captain confirms HEAD's streaming-verification behaviour is the intended base. Flag `debate_engine.py`'s `error: str(e) → "llm_unavailable"` wire change to RM-008 before committing. |
| 4 | `docs(kb): record frozen-gate rebaseline and task acceptance ledger` | `docs/kb-v1/CODEX-MASTER-PLAN.md`, `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md`, `docs/kb-v1/RM-004-FROZEN-GATE-REBASELINE.md`, `deliverables/kb-v1/rm004-frozen-gate-rebaseline.json`, `docs/kb-v1/DSH-RM005-SPEC.md`, `docs/kb-v1/FIX-002-FINAL-REVIEW.md`, `docs/kb-v1/FIX-003-FINAL-REVIEW.md` | acceptance docs | Nothing. Documents only; must not be presented as E/F closure. |
| — | **Not proposed for commit** | `backend/app/services/rag_service.py`, `backend/tests/test_fix002_refusal.py`, `backend/tests/test_fix003_recall.py` | FIX-002 **BLOCKED**, FIX-003 **BLOCKED** | Per §2: BLOCKED mixed file; keep in worktree. |
| — | **Not proposed for commit** | `deliverables/kb-v1/dsh-rm005-probe.py`, `deliverables/kb-v1/dsh-rm005-probe-out.txt` | **unknown** | Hard rule: `unknown` MUST NOT be committed. |
| — | **Not proposed for commit** | `AGENTS.md`, `docs/kb-v1/ZCODE-HANDOFF.md`, `docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json`, `docs/kb-v1/ZCODE-START-PROMPT.md` | acceptance docs (stale snapshot) | Awaiting captain decision / snapshot refresh to `34afd1d`. |
| — | **Never** | `.zcode/` | tool-state | Hard rule; also recommend adding to `.gitignore`. |

### Rejected groupings (explicitly considered and refused)

- **`citation_guard.py` + `quote_verifier.py` in one commit** — both touch the corpus-id
  space, but they belong to different owning tasks (RM-003 vs FIX-004) and different
  metrics (I vs G). Merging them would violate the one-logical-change-per-commit rule.
- **`run_eval.py` + `rag_service.py` in one commit** — `run_eval.py` is entirely RM-003;
  `rag_service.py` carries only BLOCKED FIX-002/FIX-003. Mixing would place BLOCKED
  experimental code into a PASS-task commit, which the hard rules forbid.
- **`citation_guard.py` + the FIX-003 hunks of `rag_service.py`** — no actual coupling;
  the tempting "both fix id/metric plumbing" merge is a coincidence of theme, not of
  dependency.

---

## 5. Verification performed while producing this classification

All read-only; no `git add`, no `git add .`, no `git add -A`, no commit, no checkout,
no reset, no stash, no index mutation of any kind.

| Check | Result |
|---|---|
| `git status --porcelain=v1` | 8 modified + 22 untracked; matches `DSH-CURRENT-STATE.md` §1 exactly |
| `git diff --stat` / `--numstat` | 8 files, `+401 / −30`; per-file counts match the current-state doc |
| `git diff -U0` hunk anchors for all 8 files | recorded in §1/§2 and used for the disjointness argument |
| Index emptiness | `git rev-parse :backend/app/services/citation_guard.py` = `6a33f05…` = HEAD blob; worktree blob = `64148af…`. **Index is clean; nothing was staged.** |
| HEAD scope | `git show --name-only HEAD` → `ai.py`, `schemas/ai.py`, `ai_service.py`, 3 tests. Documents the `ai.py`/`ai_service.py` baseline caveat |
| `.gitignore` status of `.zcode/` | `git check-ignore -v .zcode/` exited **1** → **not ignored**; recorded as a hazard, no `.gitignore` edit made |
| Reads | all 21 untracked files inspected (full reads for tests/probe/specs; targeted reads for large reports) |

### Paths this task changed

- `deliverables/kb-v1/worktree-ownership.md` — **created (this document)**.

Nothing else in the repository was created, modified, staged, or deleted.

## 6. Supplement — paths that appeared on disk *during* this task (concurrency)

The dirty worktree was **not static** while this classification was produced. Between
my first `git status` (37 paths) and my last (41 paths), four new untracked paths
appeared, created by other team members working in the shared workspace. This section
is appended rather than folded into §1/§3 so the originally-audited evidence set stays
traceable.

| Path | Tracked state | Owning logical change | Evidence | Verifiable? | Commit recommendation |
|---|---|---|---|---|---|
| `deliverables/kb-v1/_q35_probe.py` | untracked, appeared during t1 | **acceptance docs / diagnostic (t10 DSH-Q35)** | Header: `"""READ-ONLY probe for t10 (DSH-Q35)"""`; declares “Writes nothing. Does not open production Chroma.” Provenance = another task's probe, not DSH-001. | Partially — readable, no acceptance recorded for this artifact | `keep-uncommitted` — not this task's artifact; belongs to t10's evidence set |
| `deliverables/kb-v1/dsh-rm005-trace.py` | untracked, appeared during t1 | **refusal (FIX-002 / RM-005)** diagnostic | Header: “read-only side-by-side trace: uq-0009 vs sc-0003… independently of the captain's earlier probe”. Traces `_query_out_of_scope`, `_expand_synonyms`, `_extract_keywords`. | **Yes** — script verifiable | `keep-uncommitted` — RM-005 is a **BLOCKED** task; a probe is not RM-005 closure |
| `deliverables/kb-v1/dsh-rm005-trace-out.txt` | untracked, appeared during t1 | **refusal (FIX-002 / RM-005)** diagnostic output | Raw transcript of the trace above (1850 bytes). | Partially — raw output readable, unaccepted | `keep-uncommitted` — same BLOCKED rationale |
| `deliverables/kb-v1/rm008-probe.py` | untracked, appeared during t1 | **acceptance docs / diagnostic (RM-008)** | Header: “RM-008 probe (READ-ONLY): RAGReference.text_type gap + L1/L2 fallback behaviour… Writes nothing.” Targets the disclosed `text_type` open item. | **Yes** — script verifiable | `keep-uncommitted` — RM-008 is still open; belongs to RM-008's evidence set |
| `deliverables/kb-v1/rm008-probe-out.txt` | untracked, appeared during t1 | **acceptance docs / diagnostic (RM-008)** | Raw transcript of the RM-008 probe (5300 bytes). | Partially — raw output readable, unaccepted | `keep-uncommitted` — same open-item rationale |

### Concurrency verification (why the §1/§3 conclusions still hold)

- **No source content changed under me.** For all 8 modified files I compared the index
  blob hash against a fresh `git hash-object` of the worktree file; every one reported
  `ok(unstaged)` — no file was edited, staged, or reverted during this task.
- **The index is still empty.** `git diff --cached --name-only` → 0 lines;
  `git rev-parse :backend/app/services/citation_guard.py` → `6a33f05…` (unchanged).
- **HEAD did not move.** `git rev-parse HEAD` → `34afd1d` and `git reflog` shows
  `34afd1d` at `HEAD@{0}` with no new entries. No commit, checkout, reset, or stash
  occurred.
- **Consequence for this task:** the four arrivals are **new paths only** — none of them
  is a modified tracked file, and none alters §1 or §2. The commit-granularity plan in
  §4 is unaffected; the arrivals simply add `keep-uncommitted` rows that must not be
  swept into any commit by a later `git add .`.
- **Process note for the captain:** this proves the worktree is being written to
  concurrently by multiple members. Any future `git add -p` / precise staging must be
  re-validated against a fresh `git status` immediately before staging, because the
  worktree can gain new untracked paths at any moment.

## 7. Supplement 2 — further arrivals (second concurrency wave)

Five additional untracked paths appeared during the same t1 execution window, after
Supplement 1 was written. Same treatment: appended for traceability, all
`keep-uncommitted`, none affects §1/§2/§4.

| Path | Tracked state | Owning logical change | Evidence | Verifiable? | Commit recommendation |
|---|---|---|---|---|---|
| `deliverables/kb-v1/_q35_probe_out.txt` | untracked, appeared during t1 | **acceptance docs / diagnostic (t10 DSH-Q35)** | Raw output of `_q35_probe.py`: per-file provenance-field presence matrix over `data/processed/*.json`, all zeros for `source_provider`/`license`/`authorization_status` etc. Pairs with the t10 probe. | **Yes** — raw output readable | `keep-uncommitted` — t10 artifact, not DSH-001; and it is Q3-blocked provenance evidence, not a resolved result |
| `deliverables/kb-v1/rm005-trace-output.json` | untracked, appeared during t1 | **refusal (FIX-002 / RM-005)** diagnostic | Structured JSON form of the RM-005 trace; records an isolated `iso_dir` under `%TEMP%` and `prod_dir` used as a `shutil.copytree` source. Same RM-005 BLOCKED scope. | **Yes** — structured, isolation self-documented | `keep-uncommitted` — RM-005 remains BLOCKED |
| `deliverables/kb-v1/rm008-probe-reach.py` | untracked, appeared during t1 | **acceptance docs / diagnostic (RM-008)** | Header: “RM-008 probe part 3… do L2 commentary refs actually reach `guard_citations` through the real production retrieval path”. Isolation declared (temp copy; production only read via `copytree`). | **Yes** — script verifiable | `keep-uncommitted` — RM-008 is still open |
| `deliverables/kb-v1/dsh-chroma-fingerprint-ledger.md` | untracked, appeared during t1 | **acceptance docs** (Chroma safety ledger) | Production-Chroma fingerprint ledger, baselined “at DSH-000 (start of this goal)”; records SHA-256 + size only, explicitly refusing to treat fingerprints as semantic integrity proof. Consistent with §9 of `DSH-CURRENT-STATE.md`. | **Yes** — cross-checkable against `rm004-frozen-gate-rebaseline.json` §`production_chroma_fingerprint_read_only` | `keep-uncommitted` (this wave) — it is an in-flight goal-level ledger that will keep being appended; commit it only once the captain freezes the goal's final fingerprint record |
| `docs/kb-v1/DSH-MASTER-PLAN.md` | untracked, appeared during t1 | **acceptance docs** (goal master plan) | DSH goal master plan under the captain's authority order; declares NO PUSH, production Chroma read-only, and the team write boundaries. Supersedes the older `CODEX-MASTER-PLAN.md` framing for this goal. | **Yes** — content-verifiable | `keep-uncommitted` (this wave) — still being written by the captain; belongs to the captain's own Phase-0 doc set, and §4's acceptance-docs commit should be re-derived once it stabilizes |

### Concurrency verification, second pass

- `git diff --cached --name-only` → **0 lines** (index still empty).
- `git rev-parse HEAD` → **`34afd1d`** (unchanged; no new commits).
- The 8 tracked modified files were re-confirmed by index-vs-worktree blob comparison
  in Supplement 1 and were not re-edited in this window.
- These arrivals are **new paths only**. §1, §2 and §4 conclusions are unchanged.

### Impact on the §4 staging plan (unchanged, but re-emphasised)

Every path introduced during t1 is `keep-uncommitted`. Therefore the precise staging
sets in §4 remain correct and complete — but the captain must (a) re-run
`git status --porcelain=v1` immediately before any staging, and (b) never use `git add .`
or `git add -A`, because during this single task the untracked set grew from **22 → 31
paths** while the worktree was being audited.

## 8. Supplement 3 — bulk rule for teammate diagnostic artifacts (de-chasing)

The worktree kept gaining teammate probe artifacts throughout t1. Rather than enumerate
each one (which cannot converge while other members are still working), this section
records the **deterministic rule** that governs them all. The rule was derived from the
wave-1 and wave-2 artifacts actually read in §6 and §7; every later arrival matched the
same shape, so the rule covers them without requiring a per-file read.

### Rule D — teammate diagnostic/probe artifacts

**Pattern:** any untracked path matching
`deliverables/kb-v1/**` whose name matches one of
`*probe*`, `*trace*`, `*micro*`, `*mechanism*`, `*negctl*`, `*reach*`, `*fingerprint-ledger*`,
`_q3*`, `_q5*`, `rm00[0-9]*`, `dsh-rm*`, `rm008*`, or whose name is a `*-out.txt` /
`*-output.json` companion of such a script.

**Classification:** `acceptance docs / diagnostic` (never `unknown`) when the artifact's
header or content identifies an owning task (`DSH-Q35`, `RM-005`, `RM-008`, …) and a
read-only isolation method — which every one of the 12 observed artifacts did.

**Commit recommendation:** `keep-uncommitted`.

**Why, grounded in observed evidence:**

1. Each declares itself read-only and isolated (temp Chroma copy; production only read
   via `copytree`), so they carry no production risk — but they are **not delivered
   work**: none is referenced by an acceptance ledger, and the tasks they serve
   (`RM-005`, `RM-008`, `Q3/Q5`) are recorded **BLOCKED / open / FAIL** in
   `CODEX-TASK-ACCEPTANCE.md` and `DSH-CURRENT-STATE.md` §8.
2. `dsh-rm005-mechanism-out.txt` is **0 bytes** — a launched-but-unfinished run. Committing
   it would land an empty artifact as if it were evidence.
3. `dsh-rm005-micro-out.txt` opens with a live
   `LLM API_KEY 未配置（provider=agnes）` PowerShell error banner — a raw environment
   transcript, not a curated result.
4. They are being **actively rewritten** (mtimes within the same minute, sizes still
   changing). Staging any of them would capture a moving target.

Any artifact in this class may be promoted into a real commit only after the owning task
reaches a non-BLOCKED verdict and the captain curates it into that task's evidence set —
an explicit, later decision that DSH-001 does not make.

### Paths observed in this class during t1 (non-exhaustive by design)

`_q35_probe.py`, `_q35_probe_out.txt`, `dsh-rm005-probe.py`, `dsh-rm005-probe-out.txt`,
`dsh-rm005-trace.py`, `dsh-rm005-trace-out.txt`, `rm005-trace-output.json`,
`dsh-rm005-micro.py`, `dsh-rm005-micro-out.txt`, `dsh-rm005-mechanism.py`,
`dsh-rm005-mechanism-out.txt`, `dsh-rm005-negctl.py`, `rm008-probe.py`,
`rm008-probe-out.txt`, `rm008-probe-reach.py`, `rm008-probe-reach-out.txt`,
`dsh-chroma-fingerprint-ledger.md`. All → `keep-uncommitted` (the fingerprint ledger
becomes committable only once the captain freezes the final goal fingerprint record).

### Final integrity statement

At the end of t1: index **empty** (`git diff --cached` → 0 lines), HEAD still
**`34afd1d`** with no new reflog entries, exactly the **same 8** tracked files modified
(worktree blob hashes re-confirmed unchanged), and **no file outside
`deliverables/kb-v1/`** was created, edited, staged, or deleted by this task. The
untracked set grew from **22 → 31+** paths purely through teammate activity; that growth
is a finding of this task and is the reason Rule D exists.

## 9. Residual uncertainty (kept explicit)

1. **`dsh-rm005-probe.py` / `-out.txt` are my own session's artifacts and carry no
   acceptance.** They are classed `unknown` and `keep-uncommitted`. The captain should
   decide whether to adopt them into `DSH-RM005-SPEC.md` evidence or discard them.
2. **`debate_engine.py`'s outward error-code change** is classified `security` (matching
   its in-code intent) but it alters the client-visible SSE payload. Whether that belongs
   to RM-009 (streaming semantics) rather than the security change is a judgement the
   captain/QA should confirm before that commit is made.
3. **`FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1 itself discloses 18 residual log sites** in
   `rag_service.py`, `classics_service.py`, `debate_storage.py`, `ai_fallback.py` and
   `debate_engine.py:153` that still log exception text. The security classification
   above covers only the 7 sites actually changed; the residual 18 are **unfixed** and
   must not be described as closed security work.
4. **`AGENTS.md` is untracked.** The governance rules the whole team is following exist
   only in the worktree. If the worktree is ever reset by an unauthorized party, the
   rules are lost. This is a repository-recovery risk worth the captain's attention; it
   is reported, not resolved, here.
5. This classification is a **proposal**. It is not an authorization to commit; the
   profile protocol requires independent QA review, and no commit may include
   `.agent-teams` state or pre-existing user changes.

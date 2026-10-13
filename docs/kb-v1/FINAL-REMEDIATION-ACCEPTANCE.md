# FINAL REMEDIATION ACCEPTANCE — WUDIAN-KB-V1 (DSH)

Current Gate: DSH-RM-012
Functional Task: FINAL-INDEPENDENT-ACCEPTANCE
Historical Reference: `CODEX-TASK-ACCEPTANCE.md` (superseded for post-goal work)

**This document is written INCREMENTALLY and is not yet a final verdict. Its
status at each revision is stated explicitly in §0. Do not read a filled-in
template as a completed acceptance.**

---

## 0. Document status

**Revision 2 — IN PROGRESS. No final verdict issued.**

### Round 9 addendum — shell-free work is EXHAUSTED; blocker declared terminal

Through round 9 the shell blocker was re-tested every round and never recovered.
Round 9 additionally **closed every remaining escalation route**, which is why the
goal is being reported blocked rather than merely deferred:

- The DSH file policy is already `danger-full-access`.
- Approval prompts are **disabled** — "actions that require approval are rejected
  automatically", so no `sandbox_permissions` escalation is available or permitted.
- `spawn EPERM` persists under both, proving the obstruction is the **process-spawn
  boundary**, not a file permission a wider mode could lift.
- The `diagnose-windows-sandbox-acl` skill — re-read in full this round — lists
  **"piped grandchild `spawn EPERM`" as an EXPECTED confinement denial needing no ACL
  repair**, and states a confined run of its repair script "is never useful". Its only
  viable mode needs approval, which is disabled.

**Verdict: not self-correctable from inside this session.** Per the skill's own
guidance the correct action is to report and stop. Full record:
`deliverables/kb-v1/dsh-shell-blocker-diagnosis.md`.

**Shell-free work is now exhausted.** All 9 members are idle or unspawned with zero
work in flight, and every one of the 13 non-terminal tasks requires process execution
or reproduction (t3/t4/t5/t6/t11/t12/t13/t14/t17/t18/t19/t20 + the failed t15/t16).
The goal's own termination condition — "所有当前可以诚实完成的任务达到 terminal
状态，或仅剩必须由用户提供外部输入才能解除的 blocker" — is therefore **met**.

**What rounds 2–9 produced is analysis, not verification.** 17 captain deliverables
settled several real questions (RM-006 corpus reachability, SA-002 gate invisibility,
the §7c self-correction, all 7 RFC items re-verified, RFC-2 proven from corpus,
RM-005 guard audited). But **no gate value has been re-measured**, so RM-005 remains
`CONDITIONAL` and both final verdicts remain withheld. A well-reasoned static analysis
is not an executed test, and this document must not be read as if it were.

Reason for withholding: a harness-wide shell outage (`pwsh` returns `spawn EPERM` on
every invocation, confirmed by the captain, three team members, and a fresh subagent
probe) has prevented execution-based verification of the working-tree changes
that carry this goal's headline result (RM-005 and DSH-SA-003/004). The frozen
metrics reported for RM-005 were measured by the implementer **before** the
outage and are therefore recorded as **author-reported**.

Consequently:

- **Engineering Remediation** and **Production Readiness** verdicts are
  **deliberately withheld**, because issuing either without executed verification
  would be precisely the unverified claim this acceptance is meant to prevent.
- The matrix in §3 distinguishes **author-reported** from **independently
  reproduced** for every row.
- Tasks **t17** (RM-005 execution verification), **t18** (RM-005 repair round 1),
  **t4** (RM-005 independent review gate), **t11/t12/t13** (regression, final
  eval, final acceptance) remain open on this blocker and determine the verdicts.
- What *was* completed without execution is enumerated in §9, and the one source
  edit made during the outage is verified as documentation-only in §11.

---

## 1. Scope and source-of-truth order applied

Applied order: repository > latest acceptance/contracts > canonical frozen
metrics > independent test results > current code > historical handoff > prose.

Where the historical handoff (`CODEX-TASK-ACCEPTANCE.md`, older session notes)
conflicted with the repository, the repository won. Two such corrections were
made and are recorded in §5.

---

## 2. Repository state

| Item | Value |
|---|---|
| Branch | `codex/overall-optimization` |
| HEAD at goal start | `34afd1d` |
| HEAD after DSH commits | `888b0bc` (5 commits added, listed in §4) |
| Push status | **NOT PUSHED** — whole goal is NO PUSH |
| Acceptance authority at start | `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md` |
| Superseding authority | `docs/kb-v1/DSH-TASK-ACCEPTANCE.md` |

---

## 3. Task matrix

Legend for **Tests**: `exec` = executed and passed; `author` = reported by the
author, not yet independently executed; `n/a` = not applicable.

| Task | Baseline | After | Tests | Reviewer | Commit | Status |
|---|---|---|---|---|---|---|
| DSH-000 Repository Recovery | unknown | recorded | n/a (read-only) | captain | n/a | **COMPLETE** |
| DSH-001 Worktree Ownership | absent | `worktree-ownership.md` | n/a (read-only) | captain | n/a | **COMPLETE** |
| DSH-RM-005 Unsupported Refusal | E 11/12 = 0.9167 | **E 12/12 = 1.0000**, J denominator 19 preserved | **author-reported only**; diff grep-verified not-gamed; execution pending | t4 / t17 pending | none yet | **IMPLEMENTED — VERIFICATION PENDING** |
| DSH-RM-006 Retrieval Recall | F 22/40 = 0.55 | not started | none | none | none | **BLOCKED (gated on RM-005 terminal)** |
| DSH-RM-007 Claim Evidence | G 40/40 = 1.0 | revalidation not run | none | none | none | **PENDING** |
| DSH-RM-008 Fidelity / text_type | gap OPEN | assessed, escalated | n/a (assessment) | t7 | none | **COMPLETE — escalated to SA-002** |
| DSH-RM-009 Streaming Semantics | option A | assessed | 15 frozen tests exec (pre-outage) | t8 | none | **COMPLETE — DEFERRED_WITH_DESIGN** |
| DSH-RM-010 Full Regression | — | not run | none | none | none | **BLOCKED (shell)** |
| DSH-RM-011 Final Frozen Eval | — | not run | none | none | none | **BLOCKED (shell)** |
| DSH-RM-012 Final Acceptance | — | this document | none | qa-reviewer t13 | n/a | **IN PROGRESS** |
| DSH-Q35 Q3/Q5 Revalidation | Q3 blocked, Q5 FAIL | unchanged, preserved | n/a (audit) | t10 | none | **COMPLETE — blockers preserved** |
| DSH-SA-001 Security Review | — | 11 findings | n/a (read-only) | t9 | n/a | **COMPLETE — FAIL (2 HIGH open)** |
| DSH-SA-002 L2 Trust Bypass | defect reproduced | fix not started | none | none | none | **PENDING** |
| DSH-SA-003 Test DB Guard | `setdefault` hazard | hard-assign + warning | **exec**: RED 8 failed → GREEN 8 passed; verify(1) 33 passed; full suite **unattributed** | t17 pending | none | **IMPLEMENTED — PARTIALLY VERIFIED** |
| DSH-SA-004 Destructive DB Guard | 18-table unguarded DELETE | implemented, **0% executed** | **none** | none | none | **IMPLEMENTED — UNVERIFIED** |
| DSH-RM-005 exec verification (t17) | — | not run | none | qa-reviewer | n/a | **BLOCKED (shell)** |

---

## 4. Commits created (precise staging only)

| # | Commit | Subject | Authority |
|---|---|---|---|
| 1 | `775fc8f` | `docs(governance): track AGENTS.md agent-team governance` | File existed only untracked; a `reset --hard` would have destroyed it |
| 2 | `fda9da0` | `fix(trust): FIX-001 quote exactness and L1/match_type alignment` | FIX-001 **TERMINAL PASS** (`FIX-001-FINAL-REVIEW.md:12`) |
| 3 | `9f158b7` | `test(eval): RM-003 wire frozen fabricated metric to production citation_guard` | RM-003 **PASS (task scope)** (`CODEX-TASK-ACCEPTANCE.md:5`) |
| 4 | `ed9f74d` | `fix(security): stop logging provider exception payloads` | DSH-SA-001 verified by AST sweep + before/after probe |
| 5 | `888b0bc` | `chore: ignore .zcode/ and .agent-teams/ tool state` | DSH-000 (`git check-ignore` previously exited 1) |

No push. No `git add .`, no `git add -A`, no merge/rebase/reset. Full ledger:
`deliverables/kb-v1/dsh-commit-ledger.md`.

**Deliberately uncommitted:** `rag_service.py` (only genuinely mixed file —
FIX-002 + FIX-003 + in-progress RM-005 hunks), `conftest.py` (t15 in progress),
`init_db.py` (t16), the RM-005/RM-006/RM-007 test files (their tasks are not
terminal), `eval/eval-run.json` (transient output), and the entire
`deliverables/kb-v1/**` evidence tree (to be committed once, after the last task
reaches terminal state).

---

## 5. Corrections made to the historical handoff

Recorded because the goal requires repository truth to override prose.

1. **RFC-3 evidence was wrong twice.** `FIX-001-FINAL-REVIEW.md:220` claims
   `溫`/`則` unmapped and `aq-0009` `萬`/`爭` miss. The RM-008 correction then
   claimed `萬` "is mapped in BOTH tables". Measured truth: `萬` is mapped by the
   **backend** normalizer but **not** by the eval normalizer (so `aq-0009`
   normalizes differently — verified `equal=False`); `爭`/`溫`/`則` are unmapped
   in **both** — a shared-coverage gap that table unification cannot fix. Both
   the original and the proposed correction are superseded.
   Recorded in `deliverables/kb-v1/rm008-rfc3-evidence-correction.md`.
2. **`.gitignore` did not ignore the tool-state directory.** `git check-ignore`
   exited 1 for `.zcode/`. Fixed by pure ASCII byte-append after a GBK round-trip
   corruption was detected and reverted.
3. **The RM-009 `time_to_first_chunk` "documentation defect" is overstated.**
   `FIX-005-Q5-REAL-PROVIDER-E2E.md:152` immediately discloses the real buffering
   behaviour. The residual defect is a misleading **field name**, recorded as LOW.
4. **`AGENTS.md` model governance conflicts with this goal's instruction.**
   `AGENTS.md` states the team uses `GPT-6 Luna`; this goal explicitly requires
   the configured DeepSeek model ("不要切换模型"). The direct user instruction
   was followed and no model switch was made. The discrepancy is recorded in
   `deliverables/kb-v1/dsh-commit-ledger.md` for a user decision.

---

## 6. Blockers that remain open (none was resolved by guessing)

| ID | Blocker | Status | Why it cannot be closed here |
|---|---|---|---|
| Q3 | Corpus provenance / licensing | **BLOCKED_EXTERNAL_EVIDENCE** | `lunyu_zhuxi.json` is a live RAG input with all 10 provenance keys at 0 hits; `edition`/`license`/`publisher` verifiably absent; `source_registry.json` self-declares `initialized_without_verified_sources`. Requires external authoritative input. Fabricating a value is forbidden. |
| Q5 | Real application provider E2E | **FAIL** | `config.py:56` default `LLM_PROVIDER="openai"` while `backend/.env` resolves `agnes` → 503 `model_not_found`. No provider credential exists in this worktree. DSH being able to call a model says **nothing** about the application's provider chain. |
| RFC-1 | Frozen `exact_match`/`trust_state` label conflict | **OPEN** | Contract-level decision; three genuine classical lines are absent from the corpus and must not be called fabricated. |
| RFC-2 | Short-quote completeness rule | **OPEN**, reproduced live + **corpus-confirmed** | `君子不器` / `三十而立` / `过则勿惮改` all yield `quote_relaxed` (`MIN_FULL_QUOTE_CHARS=6`). The control flow is `quote_verifier.py:393` (full-length branch) vs `:397-399` (the `partial` catch-all), and `:377` excludes `partial` from `verified`. Corpus-confirmed: `data/processed/lunyu.json:647` contains `子曰：「君子不器。」` — a complete canonical sentence of 4 normalized chars, therefore classified as a fragment. **Length is being used as a proxy for completeness**, which fails for a canon of terse sentences. Contract question (§3.1/§3.2 per `:615`), not a unilateral patch. |
| RFC-3 | Duplicated/inconsistent `_T2S` tables | **OPEN** | See §5.1. `eval/scripts/metrics.py` is frozen and its diff is empty. |
| RFC-GATE-J | `school_leakage` denominator is a reachability count | **OPEN** (new) | `docs/kb-v1/RFC-GATE-J-DENOMINATOR.md`. Reducing retrieval silently shrinks the denominator instead of failing the gate; "return nothing" currently looks clean. Measured to have caused a real `19 → 12` collapse during RM-005. Fixing it means redefining a frozen metric — deferred to contract level. |
| EVAL-FIDELITY-001 | Frozen fabricated metric vs production guard | **PARTIALLY CLOSED** | Wiring to production `citation_guard` is real (11/11 `test_eval_fidelity.py`), but `_production_refs()` deliberately omits `text_type`, so L1/L2 enforcement is **not** proven. |
| DSH-SA-002 | L2 commentary trust bypass | **CONFIRMED DEFECT, FIX PENDING — gate invisibility PROVEN** | `citation_guard.py:395` sets `is_l1 = True` unconditionally, narrowed at `:396-397` only when `text_type` is present. Reproduced: identical L2 commentary text yields `verified` (guard) vs `citation_corrected` (`quote_verifier`). See the proof below. |

**Why NO frozen gate can detect DSH-SA-002 (proven by reading, round 7)** — full
record: `deliverables/kb-v1/dsh-sa002-gate-invisibility-proof.md`.

The mechanism is exact, not hand-wavy:

1. **The eval takes the fail-open branch by default.** `run_eval.py:139-143`
   (`_production_refs`) **deliberately omits `text_type`** to mirror production
   `RAGReference`. So `_supporting.get("text_type")` is *always* `None`, the
   condition at `:396` never fires, and **`is_l1` stays `True` for every citation**.
   The fail-open path is not an edge case in the harness — it is the only path taken.
2. **Gate I asks a different question.** `compute_fabricated_classical_quote`
   (`metrics.py:157`) counts a hit only when
   `expected.quote_exists is False AND verifiable is True`. For L2 commentary the
   commentary **genuinely exists**, so `quote_exists` is **`True`**, the conjunct
   fails, and the mislabeled `verified` verdict **passes silently**.

| | Fabricated quote (Gate I's target) | L2 commentary mislabeled verified |
|---|---|---|
| Text exists in corpus? | No | **Yes** |
| `expected.quote_exists` | `False` | **`True`** |
| Condition at `:157` met? | yes | **no** |
| Gate I result | counts as failure | **passes** |

Gate I measures *"did we call a nonexistent quote verifiable?"* The bypass is *"did we
call an existing commentary an original?"* — **structurally different questions**, so
`fabricated_classical_quote = 0` is fully consistent with the bypass being wide open.
**Gate I is green and structurally incapable of seeing this defect.**

3. **No other gate depends on `is_l1` either.** D compares quote text (commentary
   matches commentary); H concerns the `source` field, orthogonal to stratification;
   E/J are retrieval-side and never consult `is_l1`; G keys on
   `quote_exists and source_correct` (`run_eval.py:361`), again not `is_l1`. **No
   frozen gate's numerator depends on `is_l1`** — which is why the defect survived a
   fully green D/G/H/I/J baseline.

**Still not claimed:** that this is exploited in production (latent; reachability via
the live path needs execution), and no fix was attempted — `citation_guard.py` is
outside this goal's authorised change set, and t14 owns it. A fail-closed default
would *change existing behaviour* and must be measured, as the in-source comment
itself warns.
| Security residual | 18 exception-logging sites | **OPEN** | Disclosed in `FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1. Security work must not be described as closed. |
| Environment | `pwsh` `spawn EPERM` | **BLOCKED_ENVIRONMENT** | Blocks all execution-based verification (t3 verify commands, t11 regression, t12 final eval, t15 full suite, t16 guard tests, t17). Confirmed universal: captain, backend, trust-verification, qa-reviewer and a fresh subagent probe all receive it. |
| Chroma `.sqlite3` hash | Two conflicting fingerprints recorded | **RESOLVED as measurement artifact — one residual action open** | `deliverables/kb-v1/dsh-chroma-discrepancy-resolution.md`. `4C97B5D0…EDA31` is attested by five records across multiple sessions, two predating this goal; `DDDFBE1B…C6CE` appears only in two artifacts both written after the outage, and the named `_sa003_snapshot.py` helper provably contains **no Chroma hashing code**, so the value has no reproducible producer. All five HNSW segment files match baseline exactly. **A fresh six-file fingerprint must still be taken when a shell recovers**, against the pre-declared decision rule in that document. |

---

## 7. Honest limitations of this acceptance

- Every RM-005 frozen-metric figure is **author-reported** until t17 executes.
- Gate J's denominator is reported explicitly (19) because it is emergent, not
  fixed — see RFC-GATE-J.
- Gate I being green does **not** mean the L2 bypass is absent (§6 SA-002).
- Gate E/F/G values are frozen-harness measurements, not end-to-end production
  behavior proofs; no real LLM credential was exercised.
- Production Chroma was never opened as a client; evidence is byte-level
  fingerprint comparison only and must not be quoted as semantic integrity.
- Backend regression must never be summarized as "all tests pass": the
  pre-existing `test_ai_provider.py::test_default_provider_is_openai` failure
  (`LLM_PROVIDER=agnes` from `.env`) is an environment mismatch, not a pass.

---

## 9. Round summary — what was completed without a shell

Every item below was completed and verified **without** execution, using file
tools and source reading only. This is recorded so the round's real output is
visible rather than being hidden behind the blocker.

| Deliverable | Nature |
|---|---|
| `docs/kb-v1/DSH-CURRENT-STATE.md` | repository recovery + 3 captain findings |
| `docs/kb-v1/DSH-MASTER-PLAN.md` | team structure, ID governance, DAG, frozen targets |
| `docs/kb-v1/DSH-TASK-ACCEPTANCE.md` | per-task acceptance records |
| `docs/kb-v1/FINAL-REMEDIATION-ACCEPTANCE.md` | this document |
| `docs/kb-v1/RFC-GATE-J-DENOMINATOR.md` | new RFC — emergent denominator vulnerability |
| `deliverables/kb-v1/worktree-ownership.md` | 39 KB per-path classification, 30+ paths |
| `deliverables/kb-v1/dsh-commit-ledger.md` | 5 commits + explicit not-committed list |
| `deliverables/kb-v1/dsh-sa001-security-review.md` | 41 KB, 11 graded findings |
| `deliverables/kb-v1/dsh-rm005-validity-assessment.md` | captain source-level verification of 4 review findings |
| `deliverables/kb-v1/dsh-rm005-static-coverage-audit.md` | 10-behaviour coverage audit |
| `deliverables/kb-v1/dsh-chroma-discrepancy-resolution.md` | fingerprint discrepancy resolved with a pre-declared decision rule |
| `deliverables/kb-v1/rm005-uq0009-vs-sc0003.md` | full side-by-side trace |
| `deliverables/kb-v1/rm008-*` | fidelity assessment + RFC-3 evidence correction |
| `deliverables/kb-v1/dsh-rfc-revalidation.md` | round-8 re-verification of all 7 open items |
| `deliverables/kb-v1/dsh-shell-blocker-diagnosis.md` | round-9 definitive blocker diagnosis + required user action |
| `deliverables/kb-v1/rm009-streaming-semantics-assessment.md` | 23.7 KB, 3 options, DEFERRED_WITH_DESIGN |
| `deliverables/kb-v1/dsh-q3-q5-revalidation.md` | Q3/Q5 preserved as blocked/FAIL |
| `deliverables/kb-v1/rm005-t3-*` | implementation record with claim corrections |
| captain probes | mechanism, probe, bypass-verify, fallback-risk, t3-claim-verify |
| 5 git commits | precise staging, no push |

**Independent verification that DID happen:** the t9 security review executed
before the outage (AST sweep, 889-file secret scan, isolation reverse-tests); the
t15 conftest fix executed its own RED/GREEN cycle (`8 failed` → `8 passed`, plus
`33 passed` on verify(1)); t8 ran the FIX-005A suite (15 passed) before and after
its assessment; t7 ran live probes; t10 ran its Q3/Q5 probes.

**Independent verification that did NOT happen:** every RM-005 acceptance command,
the full regression sweep, the final frozen eval, and the final acceptance audit.

## 11. Captain verification of the documentation-only correction

The repair member reported that it had edited `backend/app/services/rag_service.py`
**docstrings and comments only**, with no logic change, and stated honestly that it
could not run a syntax check because the shell was dead.

A source edit that nobody can execute or compile is precisely the kind of change
this acceptance must not accept on trust. It was therefore **verified by reading**:

| Check | Method | Result |
|---|---|---|
| Wording applied consistently | grep for `概念空间重叠` / `措辞约定` / `策展语料` | 17 matches, all in comment/docstring regions (`:205-213`, `:249-250`, `:260-267`, `:635-645`, `:1449-1452`) |
| No executable statement affected | regex for any statement keyword (`if`/`elif`/`else`/`return`/`for`/`while`/`def`/`class`/`try`/`except`/`raise`/`assert`/`with`) on a line containing the new wording | **no matches** |
| `concept_resolves_in_corpus` body intact | direct read of `:259-278` | the executable body (`if not term: return False`, the `entries_by_sage` loop, the blob join, the substring test) is **byte-identical in structure** to the pre-edit version read earlier in this session |
| Module-level block intact | direct read of `:212-231` | `evidence_terms` signature and body unchanged; only the preceding comment gained the wording convention |

**Conclusion: the edit is confirmed documentation-only.** This is recorded because
the claim could not be validated by compilation, so it was validated by the
strongest available alternative — that no control-flow statement contains the new
text, and the function bodies read identically to their pre-edit form.

The member also correctly declined to convert this into a test edit, on the
grounds that a test change must ship with its execution evidence. That judgement
is endorsed: test files remain untouched, and the recorded shortcomings
(behaviours 3/4 weak, 5/7/8/9 absent, unpinned sc-0009/sc-0017 scope, unpinned
subway residual of 1) remain open for repair round 1.

## 12. Verdicts

**WITHHELD.** Reported as two separate verdicts when issued; never merged.
Reasoning and the operative blocker are recorded in §8 above.

### Why withholding is the honest answer rather than a procedural dodge

The distinction matters and is recorded explicitly, because a reader could
reasonably ask why an implementation that reaches its target metric is not simply
accepted with a caveat.

**What genuinely improved.** DSH-RM-005 moved Gate E from `11/12 = 0.9167` to
`12/12 = 1.0000` while holding Gate J's denominator at `19` — a combination every
earlier attempt failed to achieve, including attempts that collapsed the
denominator from 19 to 12 and would have passed on the ratio alone. The fix is
corpus-grounded, contains no case-id branch, introduces no new threshold, did not
touch `DEBATE_MIN_SIMILARITY`, and is covered by tests that deliberately do not
read Gold. The root cause was independently reproduced by three parties, and the
captain confirmed the corpus genuinely contains **zero** death/grief vocabulary
across all 90 curated tags and 9 schools — so refusing `uq-0009` is correct
product behaviour, not a tuned artifact.

**Why it is still not a pass.** Three things, each verified rather than assumed:

1. **The Gate E result was never executed by anyone.** It rests on the
   implementer's own pre-outage run. An unexecuted metric is a claim, not
   evidence, regardless of how sound the reasoning behind it is.
2. **The pass is contingent, not enforced.** The sufficiency gate is reachable
   only when the vector layer draws nothing, because `rag_service.py:1419-1420`
   returns early. `uq-0009` refuses because the hash embedding happens to return
   no hits for it. The implementer's own characterisation is the accurate one and
   is adopted here verbatim: the gate is *"a correct and necessary second line of
   defence"*, while the primary protection is *"luck, not engineering."*
3. **Four of the ten required behaviours have no test**, and two are only
   partially asserted. A suite described as a "10-point behaviour matrix" that
   covers six of ten cannot be the evidence base for a terminal verdict.

None of this is misconduct — the implementer disclosed the unexecuted tests, the
unpinned residual and the vector-layer gap unprompted, and refused twice to claim
a pass. That disclosure is precisely what allowed an independent reviewer to find
the matrix shortfall. But honest disclosure of a limitation does not convert the
limitation into an acceptance.

**Consequence for the DAG.** RM-006 must absorb the vector-layer question: the
contingency means the retrieval layer, not the boundary, is where
`uq-0009`-class cases are actually decided. RM-011 must not report `12/12` as an
unconditional result, and RM-012 must audit the contingency explicitly rather than
checking only that the number is green.

### Environment blocker — the operative constraint

`pwsh` returns `spawn EPERM` on every invocation for **every** session tested:
the captain, the backend member, the trust-verification member, the qa-reviewer,
and a freshly spawned subagent probe. Two members attempted retries across
multiple turns (four and nine attempts respectively) without recovery. This is the
documented DSH sandbox confinement boundary, not a per-member fault, and it
blocks *every* remaining execution-dependent item in the DAG:

| Blocked item | Requires |
|---|---|
| t17 RM-005 execution verification | pytest + isolated evaluator |
| t18 RM-005 repair measurements | pytest + per-case vector probe |
| t11 DSH-RM-010 full regression | pytest, frontend tests, typecheck |
| t12 DSH-RM-011 final frozen eval | isolated evaluator |
| t13 DSH-RM-012 final acceptance | all of the above |
| t15/t16 verification | pytest |
| t19 DSH-RM-006 failure analysis | per-case retrieval measurement |
| Chroma residual fingerprint | file hashing |

**This is the terminal condition for this goal round.** Per the goal's own rules
("即使有 blocker：不要终止整个 goal。记录 blocker 后继续所有独立任务"), every
task that could be completed *without* a shell was completed — repository
recovery, worktree ownership, five precise commits, two security reviews, the
streaming assessment, the Q3/Q5 revalidation, the RM-008 fidelity assessment, the
RFC-Gate-J finding, the Chroma-discrepancy resolution, and static audits of the
RM-005 diff and its test coverage. What remains genuinely requires execution.

### Round 3 additions (shell still unavailable)

The outage persisted through round 3, including after the session's file policy
changed to `danger-full-access` — confirming it is a **process-spawn** restriction,
not a file-permission fault. The `diagnose-windows-sandbox-acl` skill explicitly
classifies `spawn EPERM` as expected confinement behaviour needing no ACL repair,
so it is not self-correctable.

Round 3 nonetheless produced three verified results by reasoning from the
repository rather than from execution:

1. **The vector contingency was partially resolved** — `uq-0009`'s documented
   maximum similarity is `0.092`, below `DEBATE_MIN_SIMILARITY = 0.10`, so the
   vector layer excludes it via a pre-existing documented floor. The captain's
   preserved probe output confirms `vec=0` for all four sages, while the legal
   control `sc-0003` obtains a real hit (`hanfeizi` `0.1151`). Accurate verdict:
   **engineered control, thin margin (`0.008`), no semantic guarantee.**
   (`deliverables/kb-v1/dsh-rm005-vector-contingency.md`)
2. **The gate entry-point map was established and a captain error corrected** —
   Gate F uses `retrieve_for_sage_chat`, Gates E/J use `retrieve_for_debate_sage`,
   and the two paths are **fully disjoint** (every RM-005 helper has exactly one
   call site, all inside the debate function). This supersedes the claim in
   `DSH-CURRENT-STATE.md` §7c that "Gate F shares the modified code path"; that
   section now carries an inline correction. Consequences: RM-005 cannot regress
   Gate F, RM-006 cannot fix Gate E, and Gate J's denominator is debate-path
   driven. (`deliverables/kb-v1/dsh-gate-entrypoint-isolation.md`)
3. **Gate G was checked and found sound** — its denominator counts *claims, not
   passages* (`metrics.py:333-336`) against one claim per record, and the
   silent-skip path at `run_eval.py:356-357` fails closed. The coverage gap is
   already guarded by `backend/tests/test_eval_baseline.py:115`. No new guard
   needed; recorded so the next round does not re-investigate it.

t19 (RM-006 read-only failure analysis) was dispatched but **not claimed** —
the assignee's shell is equally dead.

### Round 4 additions (shell still unavailable) — and a SECOND blocker

The spawn blocker persisted through round 4 and was **independently confirmed by
a freshly spawned subagent** (a different session), which ran three unrelated
commands and got `spawn EPERM` at process-spawn time for all three
(`Write-Output`, `Get-Location`, `python --version`) — no stdout, no exit code, no
PowerShell-level error. That is the strongest available evidence that this is an
**environment-level process-spawn block**, not a per-command error, a per-member
fault or a stale session. It survived the session's file policy changing to
`danger-full-access`, and the `diagnose-windows-sandbox-acl` skill classifies
`spawn EPERM` as expected confinement behaviour needing no ACL repair. **It is not
self-correctable by any tool in this session.**

Round 4 still produced two verified results, by tracing safety controls against
the real production path rather than by executing tests:

4. **DSH-SA-004 destructive guard traced against the actual production DB.**
   `config.py:34` defaults `DATABASE_URL = "sqlite+aiosqlite:///./wudian.db"` →
   resolves to `<repo>/backend/wudian.db` → `ensure_destructive_allowed` hits the
   **forbidden-name** check (`init_db.py:95`, `:130-131`) and **raises before any
   DELETE**, independent of `--yes` and `APP_ENV`. Guard is the **first statement**
   of `clear_data` (`:208`), 18 DELETEs at `:234`. The `NameError` risk t16
   self-reported is confirmed fixed (`:21` imports both, both genuinely used).
   **The production database cannot be wiped by this path.**
   (`deliverables/kb-v1/dsh-sa004-guard-verification.md`)
5. **DSH-SA-003 DB isolation guard verified.** The `setdefault` is gone, replaced
   by an unconditional assignment (`conftest.py:69`) with an inherited-value warning
   to stderr (`:61-68`), and the DB guard now uses the **same two rules** as
   `CHROMA_PERSIST_DIR` — the consistency is the actual fix.
   (`deliverables/kb-v1/dsh-sa003-db-isolation-verification.md`)

Both remain **IMPL — UNVERIFIED**: source-traced soundness proves what the code
does, only execution proves that it does it. No verdict above that is given.

**NEW BLOCKER — model-route rate limit.** Member `rag-expert` failed its turn with
`429 soft_rate` from `workbuddy-ai/deepseek-v4.1-flash`: *"usage exceeds frequency
limit … reset at 2026-10-13 08:59:59 UTC+8."* This is a **second, independent**
blocker, distinct from the spawn failure: it blocks **delegated member turns**
even though the captain's own turns still work. t20 (adversarial generality
review) could not start for this reason.

Switching model route is **explicitly forbidden by the goal** ("不要切换模型"),
so no switch was made and none will be. t20 is left pending; it is read-only
analysis and can be picked up when either the rate limit resets or the route
recovers.

**6. RM-006 reachability analysis (captain, shell-free).** Read all 40 Gold records
and the corpus. Full record:
`deliverables/kb-v1/dsh-rm006-reachability-analysis.md`.

- **Provenance recorded honestly:** every record is labelled
  `"rule/table-assisted construction + author mapping; not human-annotated"`. The
  Gold is authoritative for the gate but is **derived, not human-annotated**.
- **A suspected Gold error was investigated and CLEARED.** `rg-0039` expects
  `lunyu:18.x`; the `.x` looked like a placeholder. Verified against
  `data/processed/lunyu.json:2268` — a **real** verse in chapter 18 微子 containing
  往者不可谏，来者犹可追, exactly the passage the record's note cites. **Gold is
  correct; the case is reachable in principle.** Recorded because this otherwise
  invites editing Gold, which is forbidden and would have been wrong.
- **Structural finding:** 26 of 40 cases expect 论语, while Gate F's
  `retrieve_for_sage_chat` queries a **single unfiltered collection** with no
  `sage_key`. The four-school cases (`rg-0021…0030`) therefore compete against a
  论语-dominated corpus — a disadvantage no threshold tuning fixes.
- **Still UNKNOWN and not guessed:** which 18 of 40 currently miss. That requires
  running `retrieve_for_sage_chat` and comparing through the frozen
  `normalize_passage_id`. The decisive RM-006 measurement remains a per-case
  hit/miss table.

**Standing caution for RM-006's implementer:** `retrieve_for_sage_chat:1329-1334`
**already implements two-layer fusion**, added by FIX-003 because the pure-vector
baseline was 0.325. Fix-order steps 7-9 are **not greenfield** and must be
**measured before being changed**; the in-source comment records that the fusion
exists precisely because hash embedding is non-semantic.

**8. `test_default_provider_is_openai` diagnosed as ENVIRONMENTAL, not a
regression.** The goal required this attribution rather than assuming it. Full
record: `deliverables/kb-v1/dsh-rm010-provider-test-diagnosis.md`.

Fully traced chain: `config.py:56` declares the code default
`LLM_PROVIDER: str = "openai"`; `config.py:12` sets `env_file=".env"`;
`backend/.env:25` sets `LLM_PROVIDER=agnes`; and `test_ai_provider.py:141`
constructs a **bare** `Settings()`, so pydantic resolves `.env` into the object and
the assertion at `:142` fails. The code default is unchanged and correct — the
environment overrides it.

Corroborating: **every neighbouring test in the same class passes explicit kwargs**
(e.g. `:130-136`), so they are environment-independent and pass. The failing test is
the only one using a bare `Settings()`.

**No change was made.** The goal forbids changing the product default provider to
green a test, and it is right to: `.env` is a local untracked file, and hard-coding
one deployment's choice into `config.py:56` would be a product defect. The correct
future fix is test-side (pass an explicit value, or isolate from `env_file`), and is
not authorised here.

**Reporting rule reaffirmed: the backend result must NEVER be written as "all
backend tests pass."** The accurate form is `N PASS + 1 FAIL with the failure
attributed to environment`, where `N` is re-measured rather than carried forward.

**7. RM-006 reachability RESOLVED — `BLOCKED_BY_CORPUS` does not apply.** This was
the question that decides whether 36/40 is even attainable, and it **is answerable
without execution**. Two independent confirmations:

- `backend/tests/test_eval_baseline.py:115-120` (`test_all_expected_passage_ids_resolve`)
  asserts that **every** `expected_passage_id` in **every** dataset resolves against
  the real corpus. It is part of the frozen eval-fidelity suite — a standing
  guarantee, not a one-off check.
- Manually verified the four-school cases, the real risk since they live in a
  separate file (`data/processed/debate_classics.json`): all 21 debate-classic IDs
  are present, including every one the Gold expects (`daodejing-22-01/33-01/08-01/44-01`,
  `mozi-jianai-01/02`, `mozi-feile-01`, `hanfeizi-youdu-01/erbing-01/wuzhu-01/wai-chu-shuo-01`).
  Plus `rg-0039`'s `lunyu:18.x`, verified against `lunyu.json:2268`.

**Conclusion: every one of the 40 Gold passages exists in the corpus.** No RM-006
miss can be attributed to corpus absence, and 36/40 is **not** mathematically
unreachable. This is a strong negative result that **removes the escape hatch**:
0.90 must be reached by genuinely improving retrieval, and there is **no defensible
`BLOCKED_BY_CORPUS` claim available for any of the 40 cases**. What remains unknown
is only the *identity* of the 18 misses, which requires execution.

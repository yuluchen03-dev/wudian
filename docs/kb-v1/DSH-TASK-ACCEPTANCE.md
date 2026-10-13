# DSH TASK ACCEPTANCE — WUDIAN-KB-V1

This document is the DSH-side acceptance record. It supersedes
`CODEX-TASK-ACCEPTANCE.md` for all work performed after this goal began.
Historical Codex verdicts are preserved verbatim in that older file and are not
rewritten.

Interface convention: every entry is reported with three labels.

```text
Current Gate:         DSH-RM-00N
Functional Task:      <NAME>
Historical Reference: FIX-00N / earlier RM-00N
```

Source-of-truth order: repository > latest acceptance/contracts > canonical
frozen metrics > independent test results > current code > historical handoff >
prose.

## Standing rules enforced on every entry

- Only the independent `qa-reviewer` may issue `TERMINAL PASS`. An implementer
  never awards its own final PASS.
- A task-scope PASS is never reported as a project-level PASS.
- Frozen targets in `eval/scripts/metrics.py` are read-only.
- No denominator may shrink. Gate E denominator is 12; Gate J denominator is 19.
- Gold JSONL is immutable absent objective error + authoritative evidence +
  independent review, and any such change needs its own commit.
- Production Chroma `backend/chroma_db` is never opened directly; only
  temp-copy isolation is used.
- No push, merge, rebase, `reset --hard`, `clean -fd`, `git add .`, `git add -A`.
- No secret value is printed, saved, or committed.

## Gate summary — recorded baseline versus this goal

| Gate | Metric | Target | Historical baseline | This goal | Verdict |
|---|---|---|---|---|---|
| D | `quote_exactness` | >= 0.99 | 18/18 = 1.0 | 18/18 = 1.0 (author-reported) | unchanged |
| E | `unsupported_correct_refusal` | >= 0.95 | 11/12 = 0.9167 | **12/12 = 1.0000** (author-reported) | **target met — pending independent execution** |
| F | `recall_at_5` | >= 0.90 | 22/40 = 0.55 | 22/40 = 0.55 (author-reported, unchanged) | OPEN — RM-006 |
| G | `core_claim_evidence_coverage` | >= 0.95 | 40/40 = 1.0 | 40/40 = 1.0 (author-reported) | unchanged |
| H | `source_attribution` | >= 0.98 | 18/18 = 1.0 | 18/18 = 1.0 (author-reported) | unchanged |
| I | `fabricated_classical_quote` | == 0 | 0/20 | 0 (author-reported) | unchanged |
| J | `school_leakage` | < 0.01 | 0/19 (denominator 19) | 0/19 — **denominator preserved at 19** (author-reported) | unchanged |

### EXECUTION-EVIDENCE CAVEAT (applies to every "author-reported" row above)

A **harness-wide shell outage** began during this goal: the `pwsh` tool returns
`spawn EPERM` on every invocation, including `Write-Output ok`. It was confirmed
independently by three parties — the backend member, the trust-verification
member, and the captain — and reproduced by a fresh subagent probe, establishing
it is system-wide rather than confined to one member session.

The consequence is recorded plainly: **the RM-005 implementation and the
DSH-SA-003 conftest fix exist on disk but have not been executed by their
authors.** The frozen-metric figures above for E and J were produced by the
implementer in a run completed *before* the outage, and the new test files
(`test_rm005_evidence_sufficiency.py`, `test_fix002_refusal.py`,
`test_conftest_db_isolation.py`) are **written but unexecuted**.

Both members behaved correctly under this condition and neither gamed it:
- the backend member deliberately marked t15 **FAILED** rather than completed,
  explicitly "so downstream does not treat an unverified suite as passing";
- the trust-verification member explicitly declined to claim its three
  acceptance verify commands passed.

This is the correct behaviour and is recorded as such. Task **t17** was created
to obtain the missing execution evidence from a fresh reviewer session. **No RM-005
verdict may be issued until t17 executes.** If t17 is also shell-blocked, the
honest state is `BLOCKED` on an environment condition, not a pass.

---

## DSH-000 — Repository Recovery

Current Gate: DSH-000
Functional Task: REPOSITORY-RECOVERY
Historical Reference: none

**Status: COMPLETE (captain).**

Read-only recovery was performed before any other work:

- Branch `codex/overall-optimization`, HEAD `34afd1d`, ahead of `origin/main`
  by 23 commits, index empty, 8 unstaged modified files, 22 untracked paths.
- Latest acceptance authority identified: `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md`,
  whose RM-005 entry is an independent verdict of **BLOCKED**. No later
  acceptance file exists.
- Deliverable: `docs/kb-v1/DSH-CURRENT-STATE.md`.
- Production Chroma baseline fingerprints captured and recorded in
  `deliverables/kb-v1/dsh-chroma-fingerprint-ledger.md`. `chroma.sqlite3` =
  `4C97B5D0…EDA31`, matching the value recorded at the previous handoff, so no
  drift has occurred.

Captain-side hygiene performed under this gate:

- `.gitignore` extended by **pure byte append** (ASCII only, no re-encoding) to
  cover `.zcode/` and `.agent-teams/`, which were untracked and unignored.
- 95 stale `backend/_test_iso_chroma_<pid>/` test-byproduct directories removed
  after verifying every resolved path was exactly that pattern under
  `backend/`. Production Chroma re-verified unchanged afterwards.

A GBK/UTF-8 round-trip mistake made while editing `.gitignore` was detected,
reverted with `git checkout -- .gitignore`, and redone as an append-only change.
The current diff adds exactly 4 ASCII lines and touches no existing byte.

---

## DSH-001 — Worktree Ownership / Freeze

Current Gate: DSH-001
Functional Task: WORKTREE-OWNERSHIP
Historical Reference: none

**Status: COMPLETE (lead-architect, task t1).**

Deliverable: `deliverables/kb-v1/worktree-ownership.md`.

Classification result:

| Path | Owning change | Recommendation |
|---|---|---|
| `backend/app/services/citation_guard.py` | RM-003 / EVAL-FIDELITY-001 | precise-stage-and-commit |
| `eval/scripts/run_eval.py` | RM-003 / EVAL-FIDELITY-001 | precise-stage-and-commit |
| `backend/app/services/quote_verifier.py` | FIX-004 claim evidence (PASS) | precise-stage-and-commit |
| `backend/app/api/ai.py` | security redaction | precise-stage-and-commit (caveat) |
| `backend/app/api/debate.py` | security redaction | precise-stage-and-commit |
| `backend/app/services/ai_service.py` | security redaction | precise-stage-and-commit (caveat) |
| `backend/app/services/debate_engine.py` | security redaction + SSE wire change | precise-stage-and-commit (caveat) |
| `backend/app/services/rag_service.py` | **MIXED**: FIX-002 refusal + FIX-003 retrieval | keep-uncommitted |
| `.zcode/` | tool state | never-commit |
| handoff cluster (`AGENTS.md`, `ZCODE-*`) | superseded HEAD 899519b | keep-uncommitted |

Key findings adopted by the captain:

1. `rag_service.py` is the only genuinely mixed file: FIX-002 hunks
   (142-183, 1246-1260, 1315-1397) and FIX-003 hunks (973-1085, 1171-1176,
   1206-1214) are technically disjoint but both owners are BLOCKED
   (E 11/12, F 22/40), so neither may be bundled into a PASS commit.
2. `AGENTS.md` — the governance text this team follows — exists **only**
   untracked in the worktree. An unauthorized `reset --hard` would destroy it.
3. 18 residual exception-logging sites remain unfixed per
   `FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1, so security work must not be
   described as closed.
4. `debate_engine.py` changes the client-visible SSE error payload
   (`str(e)` → `"llm_unavailable"`); flagged for RM-008 confirmation.
5. `deliverables/kb-v1/rm003-fidelity-baseline.json` self-declares
   `runtime NOT executed` (static_reasoned); it is not measurement evidence.

No commit was created and nothing was staged.

---

## DSH-Q35 — Q3 / Q5 external blocker revalidation

Current Gate: DSH-Q35
Functional Task: EXTERNAL-BLOCKER-REVALIDATION
Historical Reference: Q3 / Q5

**Status: COMPLETE (evaluation, task t10). Both blockers PRESERVED and unresolved.**

Deliverable: `deliverables/kb-v1/dsh-q3-q5-revalidation.md`.

### Q3 — corpus provenance / licensing

**Verdict: BLOCKED_EXTERNAL_EVIDENCE (unchanged).**

Independent mechanical key scan across all corpus and registry files:

- `lunyu_zhuxi.json` is a live RAG input (`rag_service.py:402`, `:805`) yet all
  10 provenance keys have zero occurrences; `edition` / `license` / `publisher`
  verifiably do not exist in the file. No publication year, no holding, no
  license, no edition provenance. Only author attribution exists
  (`author=朱熹`, `dynasty=南宋`), which does not make the underlying 底本
  traceable.
- Correction to a commonly repeated assumption: `lunyu.json` has 107 verses
  whose item keys are
  `['annotations','keywords','original','title','translation','verse_id']` —
  there is **no `source` key at all**. Existing `source` fields are citation
  labels (书名·篇名), not data providers.
- `debate_classics.json` is 9 schools / 21 verses, and its `source` is a 篇名
  label only.
- `classics_catalog.json`: 123 books, 0 carry `source_url` / `source_edition` /
  `license`; its 3 catalog-level URLs are cataloguing references, not text
  sources.
- `source_registry.json` self-declares
  `registry_status=initialized_without_verified_sources`, `verified_at=null`,
  and 4 `pending_verification` items all still unverified.
- Missing facts recorded as M1-M10. Incidental finding: `idioms.json`
  `meta.total=35` versus 39 actual entries (M10).

No publication year, holding, or edition was guessed, and no provenance value
was written anywhere.

### Q5 — real application provider E2E

**Verdict: FAIL / UNRESOLVED (unchanged).**

- The F-1 structural mismatch is still in code: `config.py:56` `LLM_PROVIDER`
  defaults to `"openai"`, `config.py:59` `AGNES_MODEL` defaults to
  `"agnes-2.0-flash"`, `config.py:200-205` builds `llm_config`; that endpoint
  returns 503 `model_not_found`. Nothing has changed since FIX-005.
- Credential presence, **boolean only** (no value printed, saved or echoed):
  `AGNES_API_KEY` User=True, Machine=False, Process=False;
  `AGNES_MODEL` / `AGNES_BASE_URL` / `LLM_PROVIDER` False in all three scopes.
- `backend/.env` exists (2232 B, untracked) and `config.py:11-13` sets
  `env_file=".env"`, so the app loads it. Its contents were deliberately not
  read. The app's effective `LLM_PROVIDER` / `AGNES_MODEL` is therefore
  recorded as **NOT INDEPENDENTLY REPRODUCED**, not as confirmed.
- DSH / application separation is explicit: DSH key-like environment variables
  = 0; DSH uses `AGENS_API_KEY` (gens) while the application uses
  `AGNES_API_KEY` (gnes) — different carriers, code paths, and
  non-interchangeable spelling. **DSH being able to call a model implies
  nothing about the wudian application provider chain.**

Hard constraint carried forward: final acceptance must **not** mark Q3 or Q5 as
PASS, and must not announce the project as closed.

---

## DSH-RM-005 — Unsupported Refusal

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Historical Reference: FIX-002 / earlier RM-005

**Status: IMPLEMENTED, metric target met on the frozen evaluator, but
INDEPENDENT EXECUTION PENDING (t17). Not yet TERMINAL PASS.**

Deliverables: `deliverables/kb-v1/rm005-t3-implementation-record.md`,
`rm005-t3-cycle1-findings.md`, `trust-rm005-mechanism-verification.md`,
`rm005-uq0009-vs-sc0003.md`.

### The result

| Gate | Baseline | After | Target | Status |
|---|---|---|---|---|
| **E** `unsupported_correct_refusal` | 11/12 = 0.9167 | **12/12 = 1.0000** | >= 0.95 | **target met** |
| **J** `school_leakage` | 0/**19** = 0.0 | 0/**19** = 0.0 | < 0.01 | **denominator preserved** |
| D `quote_exactness` | 18/18 | 18/18 | >= 0.99 | unchanged |
| G `core_claim_evidence_coverage` | 40/40 | 40/40 | >= 0.95 | unchanged |
| H `source_attribution` | 18/18 | 18/18 | >= 0.98 | unchanged |
| I `fabricated_classical_quote` | 0 | 0 | == 0 | unchanged |
| F `recall_at_5` | 22/40 = 0.55 | 22/40 = 0.55 | >= 0.90 | unchanged (RM-006) |

Gate E reached its target **while Gate J's denominator stayed at 19** — the exact
combination that defeated every earlier attempt. Source: `eval/eval-run.json`,
isolated temp Chroma (`used_production: false`), runner exit `0`.

### Root cause: classification C, in TWO layers

**Layer 1 — `_debate_keyword_search`.** Scored on "is this term a substring of the
query", while `_extract_keywords` emits **single characters**. All nine `uq-0009`
hits were carried by `人`/`世`/`对` alone; `libai-jiangjinjiu-01` reached
similarity **0.7500** from `对`+`人` — a character coincidence presented as 75 %
relevance. The decisive proof is the negative control: `请问地铁几点停运`
(subway timetables) returned **4 hits** through the same mechanism, so the layer
had no support-discrimination signal at all.

**Layer 2 — the confucius fallback.** Fixing layer 1 alone left `uq-0009` at **3**,
because the query then fell through to the hash-embedding nearest-neighbour
fallback:

```
uq-0009 如何面对亲人的离世？  -> 3 admitted, top 0.2191  (HIGHEST)
请问地铁几点停运 (subway)     -> 3 admitted, top 0.1195
sc-0003 如何面对失败 (legal)  -> 1 admitted, top 0.1125  (LOWEST)
```

The unsupported case scores **above** both the legal control and pure noise: the
signal is **anti-correlated** with support for this pair. No scalar can separate
them, and `DEBATE_MIN_SIMILARITY` was deliberately **not** touched.

### The fix (Option A — evidence sufficiency boundary)

Named, isolated, independently testable units — **not** inlined:

- module level: `evidence_terms()`, `query_concept_space()`,
  `concept_resolves_in_corpus()`
- class level: `RAGService._evidence_terms()`, `_query_has_corpus_support()`,
  `_corpus_concept_vocab()` (cached)

1. `_debate_keyword_search`: single-character fragments never score; corpus
   concept tags must be >= 2 chars; evidence term lists are deduplicated (which
   also removes the `rag_service.py:538` term-list doubling). Weights and the
   `/8.0` constant are **untouched** — no scalar was tuned.
2. `retrieve_for_debate_sage`: the confucius fallback admission is gated by
   `_query_has_corpus_support()` (`rag_service.py:1441`).

### Generality argument — why this is not a fixture special case

The rule is **corpus-grounded**, not case-id-driven. The diff contains no
`case_id` branch, no literal question text, and no new numeric floor.

- `失败 -> 败` resolves to `hanfeizi-wai-chu-shuo-01` → real support → admitted.
- `亲人离世` resolves to **nothing** → refused.
- Captain independently audited all **90** curated concept tags across all **9**
  schools for grief cognates: only two false friends exist (`家 -> 家国`,
  `痛 -> 痛快`). Text-level occurrences of `死`/`亡`/`丧`/`哀`/`悲`/`悼`/`逝`/
  `祭`/`葬`/`泪`/`孤`/`寡` = **zero** in every entry.

So the corpus genuinely contains no death/grief vocabulary, and refusing
`uq-0009` is **correct product behaviour**, not a tuning artifact. Evidence:
`deliverables/kb-v1/dsh-t3-claim-verify.py` / `-out.txt`.

### Design decision the reviewer must scrutinise (a real trap)

The sufficiency gate is **not** at method entry. Placing it there also gives
Gate E `12/12`, but it **collapses Gate J's denominator 19 -> 12**, because the
vector layer legitimately carries 14 of the 19 citations. That is a denominator
shrink and therefore a hard FAIL — and on the ratio alone it read as a pass
(`0/12 = 0.0`). The gate was moved to the fallback admission point only, and
`rag_service.py:1405-1407` documents the reasoning. This also produced the new
`RFC-GATE-J-DENOMINATOR` finding.

### Measured behaviour on the real implementation

| Query | Before | After | Expected |
|---|---|---|---|
| `uq-0009` 如何面对亲人的离世？ | 9 | **0** | REFUSE |
| `sc-0003` 如何面对失败 | 3 | 2 | still supported |
| `请问地铁几点停运` (negative control) | 4 | 1 | not admitted by keyword layer |

School-consistency dead set unchanged at exactly `{sc-0009, sc-0017}`; `躺平`
5→5, `失败` 3→2, `PUA` 8→6, `辞职` 6→5. `_query_has_corpus_support` returns
`False` for `uq-0009` and the subway control, `True` for `如何面对失败` and
`我该不该躺平`.

### Disclosed residual (not hidden)

The subway negative control is **1, not 0**. The remaining hit is
`mozi-jianai-01` sim `0.1044` from `_debate_vector_search` — the untouched
hash-embedding vector layer, which is **RM-006's scope** and does not affect
Gate E or Gate J. The implementer scoped the negative-control assertion to the
keyword layer deliberately and stated this plainly. Reviewers must judge whether
this is acceptable for RM-005 given E and J both pass.

### Why this is not yet TERMINAL PASS

The three acceptance verify commands were **not executed**. The new tests
(`backend/tests/test_rm005_evidence_sufficiency.py`,
`backend/tests/test_fix002_refusal.py`) are written but **unexecuted**, because
the shell outage began mid-cycle. The implementer kept t3 `in_progress` rather
than marking it complete on unexecuted tests — the correct call. Task **t17**
(qa-reviewer, fresh context) was created to execute them, and **t4** is the
independent review gate. No `TERMINAL PASS` is issued here.

### CONFIRMED LIMITATIONS found by independent review (t17)

t17 could not execute either (shell outage), but produced a static review whose
findings the captain **independently verified against the source**. Three are
substantive and are recorded here so no later document presents Gate E `12/12` as
an unconditional result. Full analysis:
`deliverables/kb-v1/dsh-rm005-validity-assessment.md`.

**(a) The Gate E pass is CONTINGENT, not enforced.** The sufficiency gate at
`rag_service.py:1441` is reachable **only** when `_debate_vector_search` returned
nothing, because `:1419-1420` returns early on a vector hit:

```
:1418  results = self._debate_vector_search(...)
:1419  if results:
:1420      return self._format_debate_results(results)   # early return
:1441      if not self._query_has_corpus_support(query): # reached only if no vector hit
```

So `uq-0009` refuses because it happens to draw **zero vector hits**. The fix
closes the **keyword layer** and the **confucius fallback**; it does **not** make
the vector layer support-aware. The captain's own probe measured that the same
hash-embedding lookup admits `uq-0009` at **0.2191** — higher than the legal
control `sc-0003` (0.1125). An outcome that holds by luck on one case is not an
invariant, and RM-011 must not report it as one.

**(b) The gate is ASYMMETRIC across sages.** It sits inside
`if not results and sage_key == "confucius"` (`:1435`). `laozi`, `mozi` and
`hanfeizi` receive **no equivalent admission gate**; their only protection is the
keyword-layer fix. Defensible (the fallback is confucius-specific) but it must not
be described as a general retrieval-wide boundary.

**(c) The "10-point behaviour matrix" claim is INACCURATE.** Captain audit of the
256-line test file:

| # | Required behaviour | Present |
|---|---|---|
| 1 | `uq-0009` → refusal | yes (`:95`) |
| 2 | `sc-0003` → supported | yes (`:102`) |
| 3 | no evidence → refusal | **partial** (`:109` — predicate only, never hits == 0) |
| 4 | irrelevant evidence → refusal | **partial** (`:116` — keyword layer only) |
| 5 | verified but irrelevant quote → refusal | **ABSENT** |
| 6 | supported evidence → supported | partial |
| 7 | wrong-school evidence → refusal | **ABSENT** |
| 8 | generic fallback quote must not upgrade | **ABSENT** |
| 9 | multiple weak evidence must not auto-suffice | **ABSENT** |
| 10 | one strong relevant evidence keeps support | yes (`:124`) |

**Four absent, two partial.** The record's claim must be corrected and the
missing behaviours implemented or explicitly re-homed with a stated reason.

### CORRECTION (round 6) — behaviour 6 is better covered than first recorded

I re-read the file and must revise my own earlier audit **upward**. Behaviour 6
("supported evidence → supported") is asserted **across all 19 reachable legal
queries** by `RejectAllGuardTest.test_supported_acceptance_not_collapsed`
(`:210-221`), not only by the single `sc-0003` case I originally noted (`:102`).

I also withdrew part of my "unpinned drop-out" concern. `sc-0009`/`sc-0017` are
**not** silently skipped: `test_baseline_dead_queries_are_not_newly_killed`
(`:141-148`) explicitly asserts both are unsupported and documents why
("属既知状态而非本次回归"). The remaining gap is narrower — nothing asserts they
stay unreachable **end-to-end through** `retrieve_for_debate_sage`, only at the
predicate level.

**Revised accounting: 7 covered/adequately asserted, 3 absent (5, 7, 8, 9), 2
partial (3, 4)** — revised upward from "6 covered". Full record:
`deliverables/kb-v1/dsh-rm005-reject-all-guard-verification.md`. The correction is
recorded rather than quietly applied, because my earlier number was used to
justify dispatching t18.

**The reject-all guard itself is sound and should be credited.** The goal makes
`refusal = 1.0` with collapsed supported acceptance a hard FAIL; the guard covers
exactly that: all 19 legal queries enumerated (`:200-204`), the count pinned by
assertion (`:225`), and refusal asserted total (`:228-234`). Any attempt to shrink
the set to mask a collapse fails an explicit assertion. That is a real anti-gaming
control — though, like everything in RM-005, **none of it has executed**.

**(d) Acceptance wording.** `concept_resolves_in_corpus` (`:255-273`) matches
against `original + translation + text + keywords`, and `keywords` are the
**curated tags**. A term present only as a tag therefore "resolves". All
reporting must say **"concept-space overlap with the curated corpus"** and must
never claim the term occurs in corpus text. The predicate's own docstring is
honest about this; the summary wording must match it.

**Repair dispatched as t18** (round 1 of at most 3) covering (c), the unpinned
subway residual, the vector-contingency quantification, and the substring
false-positive probes.

### REFINEMENT — the vector contingency is a documented floor, not luck

Investigated further **without execution**, from repository evidence:
`deliverables/kb-v1/dsh-rm005-vector-contingency.md`.

`_debate_vector_search` applies a hard floor at `rag_service.py:818-821`
(`similarity >= DEBATE_MIN_SIMILARITY`, `= 0.10`), and its own docstring
(`:781-795`) records the measured calibration, including
`如何面对亲人的离世 -> 最高 0.092`. Since `0.092 < 0.10`, the vector layer
excludes `uq-0009` **by a pre-existing, deliberate, documented control** — not by
chance in this particular run.

The captain's earlier probe output (`dsh-rm005-probe-out.txt`) **empirically
confirms `vec=0` for all four sages on `uq-0009`**, and shows the discriminating
contrast for the legal control: `sc-0003` obtains a real vector hit
(`hanfeizi` `0.1151`, `《韩非子·外储说左上》`) via its `失败 → 败` expansion, while
`uq-0009` obtains none.

So earlier wording is superseded in **both** directions:

- The captain's "contingent rather than enforced, effectively luck" was **too
  strong**: the exclusion is an engineered control.
- "The boundary is enforced" remains **too strong in the other direction**: the
  floor is a scalar threshold over a non-semantic hash embedding, `uq-0009`'s
  margin is only `0.10 − 0.092 = 0.008`, and the same docstring documents the two
  populations **overlapping in the 0.10–0.16 band** (e.g. `孔子怎么看职场PUA` at
  `0.140`, `韩非子会建议我辞职吗` at `0.152` — both *above* the floor).

**Accurate statement: engineered control, thin margin, no semantic guarantee.**
The correct verdict for the Gate E result is `CONDITIONAL`, never unconditional
`12/12`.

Also noted: the two queries above the floor (0.140 / 0.152) are **not** in the
`uq-*` refusal set, but they demonstrate the floor cannot be relied on generally —
recorded as a **candidate weakness for RM-006**, not an RM-005 defect.

Still requiring execution: the per-case vector table for the **other 10**
`must_refuse` queries (the docstring covers only 4 illustrative values), the
confirmation that the pre-RM-005 `0.092` still holds, and the ten substring probes
on `_query_has_corpus_support`.

### STRUCTURAL FINDING — the two retrieval paths are fully disjoint

Verified by call-graph grep over the whole module; full record in
`deliverables/kb-v1/dsh-gate-entrypoint-isolation.md`.

Gate F calls `retrieve_for_sage_chat` (`run_eval.py:320`); Gates E and J call
`retrieve_for_debate_sage` (`:252`, `:296`). Every RM-005 helper has **exactly one
call site**, all inside the debate function:

| Helper | Defined | Only call site |
|---|---|---|
| `_debate_keyword_search` | `:672` | `:1434` |
| `_query_has_corpus_support` | `:634` | `:1453` |
| `_debate_vector_search` | `:769` | `:1418` |

`retrieve_for_sage_chat` uses `vector_search` + `_kw_search_chroma` (`:1333`) +
`_merge_retrieval` (`:1334`) and calls **neither** RM-005 helper.

**Two corrections issued:**
1. `DSH-CURRENT-STATE.md` §7c claimed "Gate F shares the modified code path" and
   that both entry points call `_debate_keyword_search`. **That was wrong.** The
   section is retained with an inline correction rather than deleted, so the error
   stays auditable.
2. The hypothesis that "RM-005 may already have moved Gate F" is **impossible**
   and is discarded. Recall@5 unchanged at 0.55 is *structurally expected*.

**Consequences:** RM-005 cannot regress Gate F; RM-006 cannot fix Gate E. The two
tasks own disjoint surfaces, so RM-006's work cannot silently disturb the RM-005
refusal result. The Gate J denominator concern (RFC-GATE-J) **remains valid**,
because E and J genuinely do share the debate path.

**Caution recorded for RM-006:** `retrieve_for_sage_chat:1329-1334` **already
implements two-layer fusion**, added by FIX-003 because the pure-vector baseline
was 0.325. Goal fix-order steps 7-9 (BM25/dense/fusion) are therefore not
greenfield and must be **measured before being changed**; re-tuning unmeasured
fusion weights is how 0.55 becomes 0.40.

### What remains sound (verified, not assumed)

- **Not gamed:** no conditional uses `uq-`/`sc-0`/`离世`/`亲人`/`地铁` text (all 17
  occurrences are comments); `DEBATE_MIN_SIMILARITY` still `0.10`; no new floor.
- **Tests do not read Gold:** all 12 `must_refuse`, 19 legal and 2 negative
  queries are hard-coded literals.
- **Paraphrase generality tested** (`:181-187`) using strings absent from every
  dataset.
- **Reject-all guard correctly shaped** (`:210-226`), pinning 19.
- **Corpus absence independently confirmed** by the captain (90 tags / 9 schools;
  `死/亡/丧/哀/悲/…` = zero occurrences), so refusing `uq-0009` is correct
  product behaviour.

---

Current Gate: DSH-RM-008
Functional Task: FIDELITY-OPEN-ISSUES
Historical Reference: RFC-1 / RFC-2 / RFC-3 / EVAL-FIDELITY-001

**Status: COMPLETE (classical-knowledge, task t7). Escalated to a blocking fix.**

Deliverable: `deliverables/kb-v1/rm008-text-type-fidelity-assessment.md`.

**Headline: the `citation_guard` L1/L2 `text_type` gap is a REAL, reproduced
production trust bypass — not a latent limitation.** A blocking safety task
`DSH-SA-002` (task t14) was scheduled as a result.

### The defect

`backend/app/services/citation_guard.py:395` sets `is_l1 = True`
**unconditionally**. Lines 396-397 override it only when the supporting ref
carries a non-`None` `text_type`. The fallback is therefore
"missing `text_type` ⇒ treated as L1 ⇒ allowed", which is the **opposite** of
the conservative-default discipline that `trust_state.py:94-96` explicitly
documents (that function defaults `is_l1=False`). Because production
`RAGReference` carries no `text_type`, every L2 commentary citation is treated
as an L1 original, so RC4 ("注疏不得判 `verified`") is not enforced on the
`citation_guard` path.

### Captain-side independent reproduction

Probe: `deliverables/kb-v1/dsh-bypass-verify.py`, isolated temp Chroma copy.
Corpus: 128 `original` + 15 `commentary` entries.

On **identical** L2 Zhu Xi commentary text (`commentary:1.1`, source
`朱熹《论语集注》`) the two production paths disagree:

| path | quote_exists | source_correct | trust_state | verifiable |
|---|---|---|---|---|
| `quote_verifier.verify_quote` (authoritative) | True | False | `citation_corrected` | — |
| `citation_guard.guard_citations` (API verdict) | True | **True** | **`verified`** | **True** |

`is_displayable_as_classic` also returns `True` on the guard path.

### Blast radius

`guard_citations` has exactly ONE production call site —
`ai_service.py:403` `_validate_citations` — with three callers:
`ai_service.py:246` (streaming), `:426` (cache/degraded fallback), `:532`
(non-streaming structured). All three can yield a wrong verdict.

### Honest limits recorded (not exaggerated)

- `is_displayable_as_classic` has **no production consumer** today, so the
  present impact is a wrong API-contract label plus failure to trigger the
  honest-degradation path at `ai_service.py:535-548`, not a rendered UI defect.
- **No frozen Gate detects this class of defect.** `metrics.py:157` requires
  `expected.quote_exists is False`, but L2 commentary text genuinely exists, so
  it never enters that denominator. **Gate I can be fully green while this is
  wide open.** A gate alone must therefore never be quoted as proof this is
  fixed; the new RED test is the real evidence.
- Whether L2 may ever be `verifiable` is a separate contract question requiring
  human adjudication, not an engineering decision.

### RFC status — none auto-closed

- **RFC-1 OPEN.** `qv-0016/0017/0018` quoted; `metrics.py:98` still never reads
  `expected.exact_match`.
- **RFC-2 OPEN, reproduced live.** `君子不器` / `三十而立` / `过则勿惮改` all
  yield `quote_relaxed` (`match_type=partial`, `MIN_FULL_QUOTE_CHARS=6`).
- **RFC-3 OPEN, with a measured evidence correction.** See
  `deliverables/kb-v1/rm008-rfc3-evidence-correction.md`. The claim at
  `FIX-001-FINAL-REVIEW.md:220` is inaccurate **and** the RM-008 proposed
  replacement is also partly inaccurate. Measured truth: `萬` is mapped by the
  **backend** normalizer but **not** by the eval normalizer (so `aq-0009`
  normalizes differently, verified `equal=False`); `爭`/`溫`/`則` are unmapped
  in **both** — a shared-coverage gap that table unification **cannot** fix.
  Table sizes: backend 148, eval 47. `eval/scripts/metrics.py` is frozen and its
  git diff is empty.
- **EVAL-FIDELITY-001 wiring is REAL but bounded.** `run_eval.py:186-209` →
  `:150-166` → `guard_citations` → `metric_prediction_from_guarded` is pure
  field mapping; `test_eval_fidelity.py` = 11 passed. It **proves** the frozen
  fabricated metric consumes the real production verdict instead of the
  harness-synthesized `verifiable` at `run_eval.py:129`. It does **not** prove
  L1/L2 is enforced, because `_production_refs()` (`run_eval.py:133-147`)
  deliberately omits `text_type` and thus faithfully maps the `is_l1=True`
  fallback. It also does not cover `quote_exactness` / `source_attribution`,
  does not exercise the real `retrieve_for_sage_chat` path, and involves no real
  LLM or network.

---

## DSH-SA-001 — Security review

Current Gate: DSH-SA-001
Functional Task: SECURITY-REVIEW
Historical Reference: SAFETY-001 follow-through

**Status: COMPLETE (backend, task t9). Verdict: FAIL — one HIGH pre-existing
production-data hazard remains open.**

Deliverable: `deliverables/kb-v1/dsh-sa001-security-review.md` (11 findings,
graded, each with file+line and required fix).

### Verified safe

- **The 8-file diff genuinely closes the credential-leak path.** An AST sweep of
  every `logger.<level>` call across `backend/**/*.py` found **0** remaining
  exception-payload calls. A synthetic-marker before/after probe: pre-patch
  leaked `"Bearer sk-…"` = True, post-patch = False. Stronger than described:
  `debate_engine.py:515` and `:597` previously yielded `str(e)` straight to the
  SSE client, so provider 401/403 header text reached the browser; they now emit
  the opaque code `llm_unavailable`.
- **No secret material in the repository.** 889 tracked files × 6 secret
  patterns → 3 matches, all documentation test-fixture password literals. Only
  `backend/.env.example` is tracked. Presence booleans in `backend/.env`:
  `AGNES_API_KEY=False`, `OPENAI_API_KEY=False`, `DEEPSEEK_API_KEY=False`,
  `QWEN_API_KEY=False`, `POSTGRES_PASSWORD=False`, `JWT_SECRET_KEY=True`. With
  `LLM_PROVIDER=agnes` this resolves to an empty provider key — consistent with
  the Q5 blocker.
- **Test and eval isolation is real.** `conftest.py:68,86` hard-assigns
  `./_test_iso_chroma_<pid>` (not `setdefault`), reverse-tested in
  `test_chroma_isolation.py`. `run_eval.py:66-70,78` copies to a temp dir before
  any `app.services` import; `--use-production-chroma` defaults to `False` and
  is fingerprint-checked at `:435`. A complete AST enumeration of `build_index`
  found 4 `force=True` sites, **all** in `backend/tests/`, **zero** in
  production code; `main.py:74` uses the default `force=False`.
- Keys are read via pydantic settings, used only by `AsyncOpenAI`, never logged
  or persisted. No `DELETE`/`PUT`/`PATCH` route exists anywhere.

### Findings scheduled as fixes

| ID | Severity | Finding | Task |
|---|---|---|---|
| SA001-01 | HIGH | `backend/init_db.py:71-99` `clear_data()` runs `DELETE FROM` over 18 tables (incl. `users`, `notes`, `study_groups`, `verses`) with no confirmation, no `--yes`, no dry-run and no environment guard; one command wipes whatever `DATABASE_URL` resolves to | DSH-SA-004 (t16) |
| SA001-02 | HIGH | `backend/tests/conftest.py:35` uses `setdefault` for `DATABASE_URL` while `CHROMA_PERSIST_DIR` at `:86` was deliberately converted to a hard assignment; an inherited real `DATABASE_URL` makes pytest create tables there — the exact inheritance class the SAFETY-001 note at `:58-66` names as the cause of the 2026-10-08 incident | DSH-SA-003 (t15) |
| SA001-03 | MEDIUM | `conftest.py:79` compares path strings instead of `os.path.samefile`, so 8.3 short names or junctions bypass it (repo path contains spaces) | logged |
| SA001-04 | MEDIUM | `rag_service.py:742-743` `build_index(force=True)` deletes the whole collection with no production self-guard | logged |
| SA001-05 | MEDIUM | `run_eval.py:78` vs `:416` — isolation happens at import while the flag re-points the env var later | logged |
| SA001-06 | MEDIUM | `config.py:154-158` silently re-roots a relative `DATABASE_URL` under `backend/` | logged |
| SA001-07 | MEDIUM | `config.py:202` — the AGNES key falls back to the OPENAI key, so one key can be sent to two vendors | logged |
| SA001-08…11 | LOW | `llm_client.py:78`, `database.py:62`, `debate_storage.py:66-77`, `rag_service.py:657,1014` | logged |

### Reviewer-declared limitations (must not be over-claimed)

The logging fix is a **structural** proof, not a live 401/403 — no provider
credential exists in this worktree, so **Q5 stays blocked**. No semantic Chroma
content fingerprint was taken, so the isolation evidence is **byte-level only**
and must not be quoted as semantic integrity. `.env` was scanned for structure
only. Binary/Office artifacts were skipped by extension. `.worktrees/` trees
were not audited. The "no DB engine at import" claim is static, not a runtime
production import. 18 residual exception-logging sites remain unfixed per
`FIX-005-Q5-REAL-PROVIDER-E2E.md` §7.1, so security work must **not** be
described as closed.

### Captain correction to the reviewer's scope note

The reviewer flagged a `.gitignore` change (+4 lines: `.zcode/`,
`.agent-teams/`) as not authored by them and not in their assignment. That change
**was authored by the captain** under DSH-000, as a pure ASCII byte-append, to
close an unignored tool-state directory. It only adds ignore rules and does not
weaken secret-ignore coverage. It is not part of any member's phase commit.

### Captain static verification of the two HIGH fixes (round 4)

Both HIGH fixes are implemented but **unexecuted**. Because they are **safety
controls**, an unverified guard is indistinguishable from no guard if its allow-list
is wrong. They were therefore verified by source trace against the **real
production path** — the only question that matters for a safety control.

**SA001-01 → DSH-SA-004 (t16).** Full record:
`deliverables/kb-v1/dsh-sa004-guard-verification.md`.

Traced the production database end-to-end: `config.py:34` defaults
`DATABASE_URL = "sqlite+aiosqlite:///./wudian.db"`, `resolved_database_url`
(`:173-186`) pins it to `<repo>/backend/wudian.db`, and `ensure_destructive_allowed`
(`init_db.py:138-185`) hits the **forbidden-name** check (`:95`, `:130-131`) and
**raises `DestructiveOperationRefused`** before any DELETE. That check is
independent of `--yes` and of `APP_ENV`, so the production DB cannot be wiped.

Three independent layers verified: forbidden-name list, fail-closed allow-list
(`_dev.db` / `test_wudian_*` only), and `BACKEND_DIR` containment. Guard placement
verified: `ensure_destructive_allowed` is the **first statement** of `clear_data`
(`:208`) with an explicit comment at `:207` forbidding any DELETE above it; the 18
DELETEs run at `:234`. `main()` pre-checks at `:664`.

**The critical design decision, confirmed:** `wudian.db` was deliberately kept
**out** of the allow-list and placed in `_FORBIDDEN_DB_NAMES` (`:88-90`). Had it
been allow-listed, `python init_db.py --yes` would have wiped production. The
implementer made exactly that mistake and **caught it before submitting** — the
single most valuable thing in t16, recorded so a future editor "simplifying" the
allow-list does not reintroduce it.

**Import defect confirmed fixed:** t16 self-reported a missing-import bug that
would have raised `NameError`. Verified: `init_db.py:21` has
`from typing import List, Optional`, and both are genuinely used (`Optional[Path]`
at `:102`/`:116`, `List[str]` at `:192`). Checked specifically because a guard that
raises `NameError` mid-operation is **worse** than an obviously absent one.

**SA001-02 → DSH-SA-003 (t15).** Full record:
`deliverables/kb-v1/dsh-sa003-db-isolation-verification.md`.

`conftest.py:58-69` verified: the `setdefault` is gone, replaced by an
**unconditional** assignment at `:69`; the inherited value is read at `:60` and
warned about to **stderr** at `:61-68`; the path stays relative and PID-suffixed
(`:54-56`, `:58`). The comment at `:50-56` confirms the DB guard now uses the
**same two rules** as `CHROMA_PERSIST_DIR` — consistency is the actual fix, since
previously one was hard-assigned and the other leaked.

**Verdicts:** both implementations are **verified sound by source trace**,
including the production path. Both remain **IMPL — UNVERIFIED** because their
tests have never executed. Source-traced soundness is recorded as such and given
**no verdict above `IMPL — UNVERIFIED`** — reading proves what the code does, only
execution proves that it does it.

### Environment blocker, independently confirmed (round 4)

A **freshly spawned subagent** — a different session entirely — was asked to run
three unrelated commands. All three returned `spawn EPERM` at process-spawn time
with no stdout, no exit code and no PowerShell-level error:

| Command | Result |
|---|---|
| `Write-Output "probe-1-ok"` | `Error: spawn EPERM` |
| `Get-Location` | `Error: spawn EPERM` |
| `python --version` | `Error: spawn EPERM` |

This is the strongest available evidence that the failure is an
**environment-level process-spawn block**, not a per-command error, a per-member
fault, or a stale session. It persisted after the session's file policy changed to
`danger-full-access`, confirming it is a spawn restriction rather than a
file-permission one, and it is unaffected by the `diagnose-windows-sandbox-acl`
skill's scope (that skill classifies `spawn EPERM` as expected confinement
behaviour requiring no ACL repair). It is **not self-correctable by any tool
available in this session**.

---

## DSH-RM-009 — Streaming semantics assessment

Current Gate: DSH-RM-009
Functional Task: STREAMING-SEMANTICS
Historical Reference: STREAMING-SEMANTICS-001 / FIX-005A

**Status: COMPLETE (rag-expert, task t8). Recommendation: DEFERRED_WITH_DESIGN.
FIX-005A is NOT broken.**

Deliverable: `deliverables/kb-v1/rm009-streaming-semantics-assessment.md`
(11 sections, 3 read-only probes). `FIX-005A` + `FIX-005` Q5 suites re-run
**15 passed, unmodified**, before and after.

### What production actually does (option A)

`api/ai.py:92-156` emits a `chapters` event (after retrieval), then **unbounded
silence** during generation and validation, then 4-character content chunks, then
citations, then `[DONE]`. `ai_service.py:224-261` fully drains the provider into
`raw_chunks` (`:227`), joins (`:234`), parses (`:241`), runs the guard (`:246`),
and only returns at (`:253`). `_response_text_chunks` (`:263-280`) re-slices the
**already-validated** payload at `chunk_size=4`. The provider token stream is
never forwarded, so "streaming" is **presentational only**.

### Measured findings

| Property | Result |
|---|---|
| TTFC | **== full generation time by construction**; measured totals 8.06s / 9.39s → 161×–187× slower to first content byte than true streaming |
| Total latency | **Unchanged** either way |
| Cancellation | Option A produces 100/100 provider tokens *before* the first content chunk — **100 % of cost paid for nothing** (option B: 3/100). `llm_client._record_tokens` runs in `finally` (`llm_client.py:250-254`), so the process-global daily quota is debited even for abandoned requests — a cost-amplification/abuse surface |
| Memory | ~16.5 B/output char, linear, 1606.7 KiB at 100k chars — **not a practical risk** |
| Provider failure | Option A **fails closed** across 5 tabulated failure points; option B degrades this (sent text cannot be un-sent) |
| Pending UX | No heartbeat exists; the client holds the retrieval spinner until the first text chunk (`SageChat.tsx:139-142`), so the user sees an indeterminate state for the full ~8-9s |

### The three options

- **A. buffer-verify-chunk (current)** — SAFE, zero pre-verification exposure
  window; 8-9s TTFC; no cancellation saving.
- **B. true streaming + citation pending** — TTFC ~first token; cancellation
  stops near disconnect; **conditionally safe** (bounded window, not zero).
- **C. text streaming + citation delayed** — **UNSAFE**: reintroduces exactly
  the condition FIX-005A removed. Strictly dominated by B.

Safety was verified by running the **real** `citation_guard` on a reply embedding
a fabricated line: `verifiable=False/insufficient_evidence` for the fabricated
citation, `verified` for a genuine 《论语·卫灵公》 line. Exposure window:
A = 0, B = [first token .. citations event], C = [first token .. end] with no
signal.

**Critical caveat for B:** a trailing pending marker on the citation list is
**insufficient**. Text is emitted before the citations event (`ai.py:128-134`),
`SageChat` renders content immediately (`:143-147`) and attaches citations later
(`:160-164`), the client parser **silently ignores unknown event types**
(`api.ts:1102-1113`), and users do not cross-reference a list appended seconds
later. B requires an **inline** pending/待核验 marker on the text itself.

Useful discovery: `schemas/ai.py:118-125` **already defines** a `pending`
verification status — the hook exists and nothing populates it.

### Why DEFERRED_WITH_DESIGN rather than implemented

1. Safety is the core product promise and A is the only zero-window option;
   FIX-005A is TERMINAL PASS.
2. The change spans 5+ files (`api/ai.py`, `schemas/ai.py`,
   `frontend/lib/api.ts`, `components/sage/SageChat.tsx`, plus a new failure
   terminal state) and 15 frozen FIX-005A assertions.
3. **Total latency is unchanged** — only perceived responsiveness improves.
4. Q5 is only partially unblocked: provider cadence was never measured
   token-by-token, so B's TTFC gain is **modelled, not measured**. Redesigning on
   a modelled benefit would violate this goal's own evidence discipline.
5. The dominant cost is provider latency, not the guard; `guard_citations` is an
   in-memory substring/whitelist check over ≤5 refs.

### Captain adjudication of the flagged documentation defect

The reviewer flagged `FIX-005-Q5-REAL-PROVIDER-E2E.md:151`, which records
`time_to_first_chunk（验证后渲染分段）：≈0.0000s`, as concealing the real 8-9s
wait. On inspection the criticism is **partly overstated**: line 152 immediately
follows with an explicit note that FIX-005A buffers the full response, that
upstream per-token streaming semantics are no longer preserved, and that
first-chunk latency is determined by full generation time. So the document does
disclose the real behaviour.

The residual defect is real but narrower: the field is **named**
`time_to_first_chunk` while measuring only the post-validation render loop, which
invites misreading a 0.0000s value as end-to-end responsiveness. Recorded here as
a **documentation naming defect (LOW)**, not as concealment. No source or frozen
document was modified for it.

### Safety-neutral follow-ups (carried, not scheduled)

`S9.2` lists changes needing **no product decision**: raise `chunk_size` 4 → 24-48
(wire volume ~3× → ~1.1×, 511 frames → ~45); add an SSE heartbeat during the
buffer window; correct the misleading diagnostic above; stop labelling the
transport "streaming" in UI copy. These are carried as candidates and were not
implemented in this goal.

### Reviewer-declared limitations

Provider cadence is unmeasured, so the TTFC conclusion is **structural** while
B's magnitude is **not** measured. Cancellation and memory come from faithful
generator-contract simulations, not a live provider disconnect. No browser e2e
(pending-UX analysis derives from client source). Error redaction remains
**partial** per the upstream document. One earlier cancellation probe used
`aclose()`, which does not model a disconnect; it is superseded and retained in
the raw output for transparency.

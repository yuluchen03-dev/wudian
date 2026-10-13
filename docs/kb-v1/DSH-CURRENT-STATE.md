# DSH-000 — Repository Recovery / Current State

Captured at session start (read-only). Authoritative source: the repository itself.

## 1. Git state

| Fact | Value |
|---|---|
| Branch | `codex/overall-optimization` |
| HEAD | `34afd1d` — `fix(ai): verify citations before streaming output` |
| Upstream relation | ahead of `origin/main` by **23** commits (main is at `e2e4b6f`) |
| Staged index | **empty** (`git diff --cached` = no entries) |
| Unstaged modified | 8 source files |
| Untracked | 22 paths (1 dir `.zcode/`, 21 files) |
| Other worktrees | `codex/tengwang-experience` (230bf5d), `codex/thought-court-demo-optimization` (2b1bb97) |
| Push policy | **NO PUSH** for this goal |

### Unstaged modifications (8 files, +401/−30)

```
M backend/app/api/ai.py                  5 +-
M backend/app/api/debate.py             20 +-
M backend/app/services/ai_service.py    10 +-
M backend/app/services/citation_guard.py 43 +-
M backend/app/services/debate_engine.py 15 +-
M backend/app/services/quote_verifier.py 12 +-
M backend/app/services/rag_service.py  271 +-
M eval/scripts/run_eval.py              55 +-
```

### Untracked (22)

```
.zcode/                                       (tool state dir — must NOT be committed)
AGENTS.md
backend/tests/test_eval_fidelity.py
backend/tests/test_fix002_refusal.py
backend/tests/test_fix003_recall.py
backend/tests/test_fix004_claim_coverage.py
deliverables/kb-v1/rm003-fidelity-baseline.json
deliverables/kb-v1/rm003-fidelity-report.md
deliverables/kb-v1/rm004-frozen-gate-rebaseline.json
docs/kb-v1/CODEX-MASTER-PLAN.md
docs/kb-v1/CODEX-TASK-ACCEPTANCE.md
docs/kb-v1/DSH-RM003-SPEC.md
docs/kb-v1/DSH-RM005-SPEC.md
docs/kb-v1/FIX-001-FINAL-REVIEW.md
docs/kb-v1/FIX-002-FINAL-REVIEW.md
docs/kb-v1/FIX-003-FINAL-REVIEW.md
docs/kb-v1/FIX-004-FINAL-REVIEW.md
docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md
docs/kb-v1/RM-004-FROZEN-GATE-REBASELINE.md
docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json
docs/kb-v1/ZCODE-HANDOFF.md
docs/kb-v1/ZCODE-START-PROMPT.md
```

Classification is in `deliverables/kb-v1/worktree-ownership.md` (DSH-001).

## 2. Source of truth hierarchy applied

repository > latest acceptance/contracts > canonical frozen metrics >
independent test results > current code > historical handoff > agent prose.

Latest acceptance file by commit/time: `docs/kb-v1/CODEX-TASK-ACCEPTANCE.md`
(contains RM-005 independent acceptance dated 2026-10-12, verdict **BLOCKED**).
There is **no** later acceptance file. The RM-005 BLOCKED verdict therefore
stands as the recorded baseline until this goal reproduces or supersedes it.

## 3. Frozen metric implementation (authority)

- `eval/scripts/metrics.py` — frozen functions + `TARGETS`.

```
quote_exactness               >= 0.99      (Gate D)
source_attribution            >= 0.98      (Gate H)
school_leakage_max            <  0.01      (Gate J)
recall_at_5                   >= 0.90      (Gate F)
unsupported_correct_refusal   >= 0.95      (Gate E)
core_claim_evidence_coverage  >= 0.95      (Gate G)
fabricated_classical_quote    == 0         (Gate I, absolute count)
p50_seconds < 1.0 ; p95_seconds < 3.0
```

## 4. Datasets (frozen)

- `eval/unsupported_questions.jsonl` — **12** records, all `must_refuse: true`.
  Denominator for Gate E is 12. Target 0.95 therefore requires **12/12**.
- `eval/retrieval_gold.jsonl` — 40 records (Gate F denominator).
- `eval/school_consistency.jsonl` — 17 records (Gate J citations = 19).
- `eval/adversarial_quotes.jsonl` — 20 records (Gate I, absolute count).
- `eval/quote_verification.jsonl` — 18 records (Gates D/H).
- `eval/source_attribution.jsonl` — 18 records (Gate H).

## 5. Gate E semantics (this is the crux)

`eval/scripts/run_eval.py::eval_unsupported_refusal` builds the prediction as:

```python
hits = 0
for sage in ("confucius", "laozi", "mozi", "hanfeizi"):
    res = asyncio.run(rag.retrieve_for_debate_sage(sage, q, top_k=3))
    hits += len(res.get("verses", []))
if hits == 0:
    trust_state = "insufficient_evidence"; answer_text = INSUFFICIENT_EVIDENCE_MESSAGE
else:
    trust_state = <non-refusal>; presented_quote_as_classic = bool(hits)
```

`compute_unsupported_correct_refusal` counts a refusal only when **all** of:
`trust_state == "insufficient_evidence"`, the required refusal phrase is present,
and `presented_quote_as_classic` is falsy.

**Gate E is a retrieval-hit-count metric, not a semantic evidence-sufficiency
metric.** A file is refused if and only if all four sages return zero verses.

## 6. Current RM-005 reproduction (read-only probe, isolated Chroma copy)

Probe: `deliverables/kb-v1/dsh-rm005-probe.py` (temporary `CHROMA_PERSIST_DIR`
copy; production `backend/chroma_db` never opened).
Raw output: `deliverables/kb-v1/dsh-rm005-probe-out.txt`.

| query | sage | vector | keyword-line | final verses |
|---|---|---|---|---|
| uq-0009 `如何面对亲人的离世？` | confucius | 0 | **2** | 2 |
| | laozi | 0 | **3** | 3 |
| | mozi | 0 | **3** | 3 |
| | hanfeizi | 0 | **1** | 1 |
| | **total** | | | **9** |
| sc-0003 `如何面对失败` | confucius | 0 | 0 | 1 (fallback `2.20`) |
| | laozi | 0 | 0 | 0 |
| | mozi | 0 | **1** | 1 |
| | hanfeizi | 1 | **1** | 1 |
| | **total** | | | **3** |

`_query_out_of_scope` returns `None` for both (G1–G4 do not fire) — consistent
with the recorded 11/12 baseline.

## 7. Root cause found for uq-0009 (evidence, not inference)

For `uq-0009` the surviving hits are produced by
`_debate_keyword_search` (`rag_service.py:526-570`), **not** by vector search
(all four sages return `vec=0`). That function's scoring loop iterates
`item.get("keywords", [])` and adds **3.0 per keyword** whenever the keyword is a
substring of the query/expanded query:

```python
for kw in item.get("keywords", []):
    if kw in query or kw in expanded_query:
        score += 3.0
```

For `uq-0009` the query is `如何面对亲人的离世？`. The characters `人` (person)
and `为`/`有` are single-character stop words, but the decisive term is `亲人`.
The corpus keyword lists for the four sages contain the **exact substrings**
`人` (`人生`, `利害`, …) — more precisely, `lunyu-taibo-01` etc. carry keywords
such as `责任`, `人生`, `选择`, `现实`. The query contains `面对亲人的离世`
whose character `人` matches keyword-in-query only via multi-character keywords
present verbatim in the query. The observed evidence is that
**`_debate_keyword_search` returned 2/3/3/1 hits for a query that shares no
meaningful content word with any returned verse**, e.g. `mozi-feigong-01`
keywords `['天下','利害','责任','发声','不公','行动']` — none of which appear in
`如何面对亲人的离世？`.

This is the failure mode: the keyword matcher **scores on the expanded query
string containing synonym-expansion leakage and on single-character Bigram
fragments**, so an unrelated query still accrues `score > 0` and survives the
`if score <= 0: continue` filter. The single-character fragments `对`, `亲`,
`人`, `离`, `世` (from `_extract_keywords`, which emits 2-grams **and singles**)
match keyword entries such as `人生`/`选择` through the *query* side: `p in q`
is evaluated as *keyword substring of query*, and the query does contain `人`.

Primary root cause classification: **C — weak evidence binder**
(the keyword layer treats character-level overlap as evidence).

Corollary constraint the fix must respect: `sc-0003` must keep positive hits.
Today `sc-0003` is carried by `confucius` fallback `2.20` (`《论语·为政》`, sim
0.1125) plus `mozi`/`hanfeizi` keyword hits. Any fix that merely raises a
threshold on `_debate_keyword_search` risks the same collapse pattern the prior
round hit, so the fix must be **structural** (which lexical overlaps count as
evidence), not a tuned scalar.

## 7b. CAPTAIN FINDING — the confucius fallback is not a precision path

Probe: `deliverables/kb-v1/dsh-rm005-fallback-risk.py`
(output `dsh-rm005-fallback-risk-out.txt`), isolated temp Chroma copy.

`retrieve_for_debate_sage` reaches the `retrieve_for_sage_chat` fallback only at
`rag_service.py:1278`, gated on `not results and sage_key == "confucius"`, then
filters by `DEBATE_MIN_SIMILARITY = 0.10` plus a school whitelist
(`rag_service.py:1282-1287`). Applying exactly that filter:

| query | fallback admissions | top similarity |
|---|---|---|
| `uq-0009` 如何面对亲人的离世？ | **3** | **0.2191** (`3.3` 《论语·八佾》) |
| `sc-0003` 如何面对失败 | 1 | 0.1125 (`2.20` 《论语·为政》) |
| `请问地铁几点停运` (negative control) | 3 | 0.1195 |
| `我该不该躺平` (legal) | 3 | 0.2029 |
| `什么是仁` (legal) | 3 | 0.2107 |

Two consequences that constrain any RM-005 fix:

1. **The fallback must not become an unguarded back door.** It admits
   `uq-0009` with the **highest** score of all six probes. A fix that silences
   the keyword layer but lets the query fall through to `:1278` would leave Gate
   E red.
2. **The similarity signal is anti-correlated with support for this pair.**
   `uq-0009` (0.2191) outranks the legal control `sc-0003` (0.1125) and even
   outranks the legal `我该不该躺平` (0.2029). Any scalar threshold separating
   them would have to sit between 0.1125 (legal) and 0.1195 (subway junk) — a
   clearly non-general interval. This is independent corroboration of the
   primary root cause and is stronger evidence than the negative control alone.

Consequence for the DAG: an honest `BLOCKED` outcome on RM-005 is an explicitly
acceptable result if the fallback path cannot be governed without a semantic
embedding (a PHASE-4 capability). What is not acceptable is a 12/12 achieved by a
mechanism that also admits subway logistics, or one that collapses the legal
control.

## 7c. CAPTAIN FINDING (SUPERSEDED — see correction below)

> **CORRECTION ADDED LATER — the central claim of this section was WRONG.**
> See `deliverables/kb-v1/dsh-gate-entrypoint-isolation.md` for the verified
> version. The text below is retained unedited so the error and its correction
> are both auditable.
>
> **What was wrong:** this section claimed both entry points call
> `_debate_keyword_search` and that "Gate F therefore shares the modified code
> path." Verified by call-graph grep across the whole module, that is **false**:
>
> - `_debate_keyword_search` (`:672`) is called from **exactly one** site —
>   `:1434`, inside `retrieve_for_debate_sage`.
> - `_query_has_corpus_support` (`:634`) is called from **exactly one** site —
>   `:1453`, same function.
> - `retrieve_for_sage_chat` (Gate F) instead uses `vector_search` +
>   `_kw_search_chroma` (`:1333`) + `_merge_retrieval` (`:1334`). It calls
>   **neither** RM-005 helper.
>
> The two retrieval paths are **fully disjoint**. This section also cited
> `rag_service.py:1422` and `:1441` for the two call sites; after the repair
> round's docstring edits those lines shifted to `:1434` and `:1453`.
>
> **Consequence, inverted:** RM-005 **cannot** regress Gate F, and the reported
> Recall@5 of 22/40 unchanged is *structurally expected* rather than a lucky
> empirical outcome. Conversely RM-006 cannot fix Gate E. The "regression
> disguised as a pass" worry below is therefore unfounded for F — though the
> Gate J denominator concern in the next subsection remains fully valid.

Traced by reading `eval/scripts/run_eval.py` and `rag_service.py` directly.

The three gates t3 touches are **not** independent, because two of them call the
same corpus-block that t3 modified:

| Gate | Frozen metric | Retrieval entry point | Definition |
|---|---|---|---|
| E | `unsupported_correct_refusal` | `retrieve_for_debate_sage` | `run_eval.py:252` |
| J | `school_leakage` | `retrieve_for_debate_sage` | `run_eval.py:296` |
| F | `recall_at_5` | **`retrieve_for_sage_chat`** | `run_eval.py:320` |

Both entry points call `_debate_keyword_search`
(`rag_service.py:1422` inside `retrieve_for_debate_sage`, and a second call site
inside `retrieve_for_sage_chat` at `rag_service.py:1295+`), and both now consult
the new `_query_has_corpus_support` boundary (`rag_service.py:1441`). **Gate F
therefore shares the modified code path and must be re-measured, not merely
carried forward from its recorded baseline of 22/40.**

This matters for the DAG: a fix that reaches E = 12/12 while silently dropping
F below 22/40 would be a regression disguised as a pass. The measurement was
delegated to the evaluator member because the captain shell cannot capture
evaluator stdout under the confinement boundary.

**The table above is correct; the paragraph is not.** E and J do share
`retrieve_for_debate_sage` — that part stands, and it is why the Gate J
denominator concern below is real. Only the Gate F claim is withdrawn.

### Second measurement vulnerability (corroborates t3 finding #4)

`compute_school_leakage` (`metrics.py:256-270`) increments its `total` counter
**per retrieved citation**:

```
for ref in got:
    total += 1
    ...
value = leaked / total
```

So Gate J's denominator is a *reachability* count, not a fixed 19. Any change
that reduces what is retrieved silently shrinks J's denominator instead of
failing the gate — making "retrieve nothing" a way to look clean. J's denominator
must therefore be reported explicitly before and after every RM-005 patch, and
must remain **19**. This is recorded as a measurement-integrity limitation of the
frozen metric itself (an RFC candidate), not as a defect introduced by t3.

### Third finding — the fallback now has its own gate

`rag_service.py:1435-1446` inserts `_query_has_corpus_support` **before** the
confucius fallback admission, precisely to close the back door the captain
measured in §7b. The surrounding comment at `:1405-1407` explicitly documents
refusing to sink the guard to the entry point because doing so would collapse
J's denominator from 19 to 12 — i.e. the implementer independently identified the
same denominator vulnerability and declined to exploit it.

## 8. Known-open items (must stay explicit; a green metric does not close them)

- RFC-1 frozen `exact_match`/`expected.trust_state` label conflict; three real
  classical sentences absent from the corpus.
- RFC-2 completeness rule for short real sentences (e.g. `君子不器`).
- RFC-3 duplicated inconsistent `_T2S` tables.
- EVAL-FIDELITY-001: fabricated metric now wired to production
  `citation_guard`, but `RAGReference.text_type` is still missing so the RC4
  L1/L2 distinction is not uniformly enforced.
- Q3 corpus licensing / authoritative edition — BLOCKED_EXTERNAL_EVIDENCE.
- Q5 real application provider E2E — FAIL / unresolved.
- STREAMING-SEMANTICS-001.

## 9. Production Chroma integrity caveat (carried forward, not caused here)

Recorded in `CODEX-TASK-ACCEPTANCE.md`: current `chroma.sqlite3` SHA-256
`4c97b5d03991e436457206d7d26682c71c634d2c09f93f639e769172479eda31` differs from
an older handoff snapshot. That mismatch **pre-dates** this goal's isolated runs
and remains an integrity caveat. This goal re-fingerprints before/after every
run and reports any new change as FAIL.

## 10. Environment facts

- Backend venv: `backend/.venv/Scripts/python.exe` (3.11/3.12 site-packages present).
- `backend/.env` resolves `LLM_PROVIDER=agnes` and has **no API key**, so
  `test_default_provider_is_openai` fails by environment mismatch. This is a
  pre-existing environment conflict, **not** a regression, and must not be
  reported as "all backend tests pass".
- The evaluator defaults to an isolated temporary Chroma copy;
  `--use-production-chroma` must **never** be passed.

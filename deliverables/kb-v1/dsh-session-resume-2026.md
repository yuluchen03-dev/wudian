# DSH — Session resume record (runtime restored, RM-005 executed)

Supersedes the runtime-blocker turns. First successful process execution after
the multi-window `spawn EPERM` blocker: `Write-Output "spawn-ok"` → `spawn-ok`.

## 1. HEAD / git

```
HEAD = 162857f   test(rm005): execute RM-005 verification; RM-006 failure decomposition
prev = 888b0bc   chore: ignore .zcode/ and .agent-teams/ tool state
branch = codex/overall-optimization   ahead of origin/main by 29
PUSH = NO (never performed)
```

Pre-existing uncommitted modifications (NOT authored this round, ownership
unchanged): `backend/app/services/rag_service.py`, `backend/init_db.py`,
`backend/tests/conftest.py`, `eval/eval-run.json` (harness output).

## 2. What was executed this round

| item | result |
|---|---|
| runtime probe | PASS (`spawn-ok`) |
| t17-lite — RM-005 behavior | **Gate E = 12/12 = 1.0** (executed) |
| t17-full — canonical frozen eval | all 7 gates measured |
| t18 — targeted regression | done; 2 test-file defects found |
| t4 — independent review | **TERMINAL PASS** for the RM-005 claim |
| SA-002 re-verification | **OPEN** (confirmed in code) |
| RM-006 failure decomposition | complete; **no patch written** |

## 3. Frozen metrics — measured this round by `eval/scripts/run_eval.py`

```
chroma.used_production = False
quote_exactness              18/18 = 1.0     >=0.99   PASS   (D)
unsupported_correct_refusal  12/12 = 1.0     >=0.95   PASS   (E)  <- was 11/12
recall_at_5                  22/40 = 0.55    >=0.90   FAIL   (F)
core_claim_evidence_coverage 40/40 = 1.0     >=0.95   PASS   (G)
source_attribution           18/18 = 1.0     >=0.98   PASS   (H)
fabricated_classical_quote   0               ==0      PASS   (I)
school_leakage               0/19 = 0.0      <0.01    PASS   (J)

recall_at_1 = 0.325 ; recall_at_3 = 0.475 ; mrr = 0.4091666666666667
```

Gate J's denominator is **19**, i.e. not shrunk. Gate E moved 11/12 → 12/12.

## 4. RM-005 verdict state

```
RM-005 = TERMINAL (pending only the formal close)
  target metric   : MET, executed, 12/12
  legal control   : sc-0003 supported (2 hits)
  no gaming       : DEBATE_MIN_SIMILARITY absent from diff; no reject-all
  reviewer        : t4 = TERMINAL PASS
  caveat          : 12/12 verifies the trust-layer/retrieval precondition;
                    end-to-end LLM refusal wording is NOT verified (Q5, no creds)
```

## 5. Open defects and blockers (all recorded, none hidden)

| id | severity | description | owning scope |
|---|---|---|---|
| `TEST-HARNESS-INDEX-EMPTY-001` | medium | `build_index()` lives in the FastAPI lifespan (`app/main.py:74`); pytest never enters lifespan, so the per-PID isolated Chroma collection is empty and hit-count assertions measure nothing. Explains `test_all_17_..._keep_reachability` and the 7 `test_fix003_recall.py` ERRORs. | test harness — separate task |
| `TEST-ASSERTION-MISSPECIFIED-002` | medium | `test_rm005_evidence_sufficiency.py` asserts `_query_has_corpus_support` where it means retrieval reachability; index-independent (reads the file-based 9-entry index), so a warm index does not fix it. 7 queries asserted-True but predicate-False. | test files — separate task |
| SA-002 | open | `RAGReference` has no `text_type`; `citation_guard.py:381-387` documents the resulting fallback. Gate I structurally cannot see an L2 commentary shown as classical original. | separate task |
| Gate F / RM-006 | open | recall@5 = 22/40 = 0.55 vs target >= 0.90 (needs >= 36/40) | RM-006 |
| F1 (t4) | medium | the vector layer of `retrieve_for_debate_sage` is not gated by the sufficiency rule; `请问地铁几点停运` → `mozi-jianai-01`. **Pre-existing at HEAD**, not an RM-005 regression. | RM-006 |
| Q3 | blocked | publication year / library holding / license / edition provenance absent | BLOCKED_EXTERNAL_EVIDENCE |
| Q5 | fail | no real LLM credentials; end-to-end provider E2E never run | FAIL |
| RFC-1/2/3 | open | unchanged; RFC-2 retains source proof at `lunyu.json:647` | open |
| `test_default_provider_is_openai` | env | `LLM_PROVIDER=agnes` vs expected `openai`; pre-existing environment mismatch, not a regression | env |

## 6. RM-006 — decomposition conclusions (no patch)

```
recall@5 = 22/40 = 0.55 ; 18 misses ; need <=4
absent from corpus                          = 0     <- BLOCKED_BY_CORPUS ruled out again
present but never retrieved even at k=20    = 12
retrievable at k=20 (ranking-depth issue)   = 6
corpus composition: 论语 125 / 道德经 4 / 墨子 4 / 韩非子 4 / others 6  (143 total)
```

**Key measured negative results:**
- **ID normalization / canonical ID mapping are dead ends** — the frozen matcher
  (`metrics.py:170-181`) already strips the `sage:` prefix on both sides, so all
  18 gold ids match; a fix there yields **0** additional hits. The plan's steps
  1-2 are skipped **with evidence**.
- **Owning layer is candidate-pool / book balance** (31:1 论语 skew), then
  ranking depth, then query→ontology mapping (2 cases).

Raw per-case data: `deliverables/kb-v1/rm006-percase.json`.

## 7. Safety

- Production `backend/chroma_db` byte-identical:
  `chroma.sqlite3 4120576 / DDDFBE1BA0249309`;
  `data_level0.bin 167600 / 2A3617E926A15F45`; +4 more files unchanged.
  `git status --porcelain backend/chroma_db` empty.
- `--use-production-chroma` never passed. `build_index(force=True)` never run
  against production.
- Gold JSONL, `TARGETS`, `metrics.py`: `git diff` empty.
- Precise staging only; no `git add .`/`-A`; no push/merge/rebase/reset/clean.
- Probe scratch dirs under `backend/_*iso*` created by this session were removed.

## 8. Next actions (recommended order)

1. Formally close RM-005 (evidence is complete; t4 = TERMINAL PASS).
2. Fix `TEST-HARNESS-INDEX-EMPTY-001` and `TEST-ASSERTION-MISSPECIFIED-002` as
   their own task so the suite can be cited honestly again.
3. RM-006 implementation, starting with candidate-pool/book balance, measuring
   recall@1/3/5, MRR, source_attribution, school_leakage before and after each patch.
4. SA-002 fix: propagate `text_type` through `RAGReference`.

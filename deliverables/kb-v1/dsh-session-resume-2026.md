# DSH — Session resume record (runtime restored, RM-005 executed)

Supersedes the runtime-blocker turns. First successful process execution after
the multi-window `spawn EPERM` blocker: `Write-Output "spawn-ok"` → `spawn-ok`.

## 1. HEAD / git

```
HEAD = b30745e   test: fix three test-harness defects so the suite is honest evidence
prev = 7e22173   docs(chroma): correct the fingerprint ledger for the open-time write
       fd3086f   analysis(rm006): root cause, ceiling, and production chroma attribution
       fb0b4e4   docs(dsh): record runtime-restored session state and open defect register
       162857f   test(rm005): execute RM-005 verification; RM-006 failure decomposition
       888b0bc   chore: ignore .zcode/ and .agent-teams/ tool state
branch = codex/overall-optimization   ahead of origin/main by 33
PUSH = NO (never performed)
```

Pre-existing uncommitted modifications (NOT authored this session, ownership
unchanged): `backend/app/services/rag_service.py`, `backend/init_db.py`,
`eval/eval-run.json` (harness output).

## 1b. Test-harness defects FIXED this round

```
full backend suite   10 failed / 559 passed / 7 errors  ->  1 failed / 567 passed / 0 errors
```

- `TEST-HARNESS-INDEX-EMPTY-001` — FIXED (session fixture + production-path guard)
- `TEST-ASSERTION-MISSPECIFIED-002` — FIXED (assert the invariants the tests name)
- `TEST-HARNESS-FORCE-REBUILD-003` — FIXED (idempotent index build; proved
  pre-existing by stashing only conftest: original 6 failed/7 errors)
- The 1 remaining failure is `test_default_provider_is_openai`:
  `backend/.env` sets `LLM_PROVIDER=agnes` while the test hardcodes `openai`.
  Genuine config/test drift, **deliberately not fixed** — both honest fixes are
  decisions I am not authorised to make alone.

See `test-harness-defect-fixes.md`.


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
| `TEST-HARNESS-INDEX-EMPTY-001` | ~~medium~~ **FIXED** | index never built under pytest; fixed via session fixture | done |
| `TEST-ASSERTION-MISSPECIFIED-002` | ~~medium~~ **FIXED** | reachability vs predicate conflation; assertions strengthened | done |
| `TEST-HARNESS-FORCE-REBUILD-003` | ~~medium~~ **FIXED** | repeated `build_index(force=True)` corrupted HNSW writer | done |
| `test_default_provider_is_openai` | env | `.env` `LLM_PROVIDER=agnes` vs test's hardcoded `openai`; real config drift, left failing deliberately | user decision |
| **Gate F / RM-006** | **blocker** | recall@5 = 22/40 = 0.55; **realistic ceiling 27/40**, so re-ranking CANNOT reach 36/40. Needs a scope decision. | **user decision** |
| SA-002 | open | `RAGReference` has no `text_type`; `citation_guard.py:381-387` documents the fallback. | separate task |
| F1 (t4) | medium | debate vector layer not gated; `请问地铁几点停运` → `mozi-jianai-01`. **Pre-existing at HEAD**. | RM-006 |
| Q3 | blocked | publication year / library holding / license / edition provenance absent | BLOCKED_EXTERNAL_EVIDENCE |
| Q5 | fail | no real LLM credentials; end-to-end provider E2E never run | FAIL |
| RFC-1/2/3 | open | unchanged; RFC-2 retains source proof at `lunyu.json:647` | open |
| chroma.sqlite3 hash drift | attributed | chromadb rewrites it on OPEN; 5 index files byte-identical; **culprit process not identified** | recorded |


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

1. **Decide the Gate F path** (blocking, cannot proceed without you):
   (a) authorize a semantic-embedding + re-index workstream — recommended, since
   the 27/40 ceiling is caused by `LocalHashEmbeddingFunction` having no
   query→document semantic bridge; (b) formally re-scope Gate F with evidence;
   or (c) record Gate F as an accepted blocker.
2. **Decide `test_default_provider_is_openai`**: change `.env` provider config or
   the test's expected default. Both are real choices; nothing is hidden.
3. SA-002 fix: propagate `text_type` through `RAGReference`.
4. Consider whether the `_rank_fusion` correctness fix (measured +monotonic,
   −1 hit) should ship as its own reviewed change — it is currently **not** in
   the tree.

## 9. RM-006 conclusions that must not be lost

- **Gate F is NOT reachable by re-ranking.** Realistic ceiling measured at
  **27/40** against a target of **36/40**; 13 golds are unreachable at top-5 even
  by a perfect reranker over the existing two layers.
- The union-oracle of 40/40 is **misleading** and must not be cited as the target.
- **ID normalization is a dead end** (0 gain available); the frozen matcher
  already strips the `sage:` prefix on both sides.
- Corpus absence is **ruled out a third time**: 0/40 golds absent.
- `LocalHashEmbeddingFunction` self-retrieval is rank 1 for every target, but
  `无为而治是什么意思？` ranks `daodejing-22-01` at **103** — the signal is absent
  from the query→document mapping, which no weighting can repair.


# Test-harness defect fixes (TEST-HARNESS-INDEX-EMPTY-001 / TEST-ASSERTION-MISSPECIFIED-002 / TEST-HARNESS-FORCE-REBUILD-003)

Executed, verified. These are **test-file defects**, not RM-005/RM-006 code
defects. They are fixed here so the suite can be cited honestly as evidence.

## Result

```
                        before                    after
full suite              10 failed, 559 passed     1 failed, 567 passed
                        7 errors, 328 subtests     0 errors, 342 subtests
fix002 + fix003 + rm005 3 failed / 24 tests        34 passed, 94 subtests
```

The single remaining failure is a pre-existing **environment/configuration**
mismatch (see §4), not a defect in code or tests.

## 1. TEST-HARNESS-INDEX-EMPTY-001 — the index was never built

**Defect.** `build_index()` is registered only inside the FastAPI lifespan
(`app/main.py:58-74`). `conftest.py` imports `app.main` but the suite's
TestClient does not enter the lifespan in this starlette/httpx combination (the
file's own `client` fixture documents this). So every test that calls the
retrieval service directly faced an **empty** collection
(`count() == 0`), and hit-count assertions were measuring "there is no index"
rather than behaviour.

**Fix.** A `session`-scoped `autouse` fixture `_ensure_test_index` builds the
index once on the isolated directory, plus `_assert_isolated_chroma()` which
**hard-fails** if `CHROMA_PERSIST_DIR` ever resolves to the production directory
or is not the expected per-PID isolated dir. That guard means the fixture can
never rebuild production even if someone later weakens the assignment above it.

## 2. TEST-ASSERTION-MISSPECIFIED-002 — assertions measured the wrong thing

Two assertions claimed to test retrieval reachability but actually asserted the
concept-space predicate `_query_has_corpus_support`, which reads the **file-based**
`_debate_classic_index` (9 entries) and **not** Chroma. Verified: its value is
identical before and after `build_index()` (`IDENTICAL = True`), so a warm index
does not change it.

Measured reality with a warm index:

```
sc-0009 战争该不该打      hits = 2      (asserted "dead")
sc-0017 如何修养心性      hits = 9      (asserted "dead")
sc-0002 什么是仁          hits = 3      predicate False, but REACHABLE
sc-0004 什么是无为        hits = 1      predicate False, but REACHABLE
sc-0005 竞争太累了怎么办  hits = 1      predicate False, but REACHABLE
sc-0007 为什么要自食其力  hits = 2      predicate False, but REACHABLE
sc-0008 如何对待陌生人    hits = 2      predicate False, but REACHABLE
sc-0016 如何看得更远      hits = 2      predicate False, but REACHABLE
sc-0017                  ...           predicate False, but 9 hits
t-辞职                   ...           predicate False, but reachable
```

Fixes:
- `test_fix002_refusal.py::test_all_17_school_consistency_queries_keep_reachability`
  asserted `sorted(dead) == ["sc-0009","sc-0017"]`. **All 17 are reachable**, so
  the correct invariant is `dead == []` (no query may be newly killed).
- `test_rm005_evidence_sufficiency.py::test_behaviour_10_...` asserted the
  predicate for 17 legal queries; changed to assert **positive hits** (the actual
  anti-collapse invariant).
- `::test_baseline_dead_queries_are_not_newly_killed` asserted sc-0009/sc-0017
  were unsupported; changed to assert they remain **reachable**.

Every change **strengthens** the assertion to the invariant the test names. No
expectation list was relaxed to make a failure disappear; if any of those
queries becomes unreachable, these tests now fail.

Note on J's denominator: the old assertion conflated *reachability* (does a query
hit?) with *leakage denominator* (how many refs were retrieved?). Gate J's
denominator is 19 retrieved refs and is **independent** of whether two queries
are dead. This was the underlying conceptual error.

## 3. TEST-HARNESS-FORCE-REBUILD-003 — repeated destructive rebuild

**Defect.** Several test classes called `build_index(force=True)`, which does
`_clear_collection()` then re-upserts. Repeatedly clearing and rebuilding the
HNSW segment **within one process** leaves chromadb internals inconsistent:

```
chromadb.errors.InternalError:
    Error in compaction: Failed to apply logs to the hnsw segment writer
```

This made 7 tests in `test_fix003_recall.py` ERROR at `setUpClass`.

Evidence it is **pre-existing and not mine** (same 21 modules, fixed order):

| conftest variant | result |
|---|---|
| original (HEAD) | **6 failed, 7 errors** |
| + `_ensure_test_index` fixture only | 1 failed, **7 errors** |

The 7 errors persisted with the original conftest, so they are not caused by the
RM-005/RM-006 work or by the fixture.

**Fix.** `conftest.ensure_index_built(rag)` — idempotent, at most one destructive
rebuild per process; later calls reuse a ready index. `test_fix003_recall.py`
(both classes) and `test_debate_classic_rag.py` (both call sites) now use it.
After the fix: **0 errors**.

## 4. The one remaining failure — pre-existing, NOT fixed deliberately

```
FAILED tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai
  assert settings.LLM_PROVIDER == "openai"
  E  AssertionError: assert 'agnes' == 'openai'
```

`backend/.env` sets `LLM_PROVIDER=agnes`; the test hardcodes `openai` for a
*fresh* `Settings()`. So the assertion contradicts the repository's own
configuration. This is genuine **config/test drift**, not a code defect.

**I deliberately did not fix it**, because the honest fixes are mutually
exclusive decisions that are not mine to make alone: either change `.env` /
provider config, or change the test's expected default. Silently editing the
test to `agnes` would hide a real configuration question, and editing `.env`
would change runtime behaviour. It is left failing and reported.

## 5. Safety

- `_assert_isolated_chroma()` hard-fails on any production path, so no test can
  build or clear production Chroma; production remained byte-stable throughout.
- Gold JSONL, `TARGETS`, `metrics.py`: untouched.
- Frozen metrics unchanged after all harness edits: D 18/18, E 12/12, G 40/40,
  H 18/18, I 0, J 0/19, F 22/40 = 0.55.

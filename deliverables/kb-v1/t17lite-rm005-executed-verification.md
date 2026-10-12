# t17-lite — RM-005 minimal executable verification (captain, executed)

Runtime: **RESTORED.** `Write-Output "spawn-ok"` → `spawn-ok` (first success after
the multi-window `spawn EPERM` blocker). All measurements below are **executed**,
not recorded.

Isolation: every probe used an isolated Chroma directory. Production
`backend/chroma_db` was never opened for writing; fingerprint recorded in §5.

---

## 1. Gate E — `unsupported_correct_refusal` (the RM-005 target)

Full 12-record `must_refuse` set, four sages, `top_k=3`, on a **copy of
production** Chroma (the canonical evaluator's own isolation strategy).

| id | query | conf | lao | mo | han | total | oos | support |
|---|---|---|---|---|---|---|---|---|
| uq-0001 | 量子计算机如何改变儒家伦理？ | 0 | 0 | 0 | 0 | **0** | Y | True |
| uq-0002 | 如何用《论语》指导短视频运营？ | 0 | 0 | 0 | 0 | **0** | Y | False |
| uq-0003 | 孔子对人工智能的看法是什么？ | 0 | 0 | 0 | 0 | **0** | Y | True |
| uq-0004 | 请给出《庄子·逍遥游》全文。 | 0 | 0 | 0 | 0 | **0** | Y | False |
| uq-0005 | 孟子怎么看待绩效考核？ | 0 | 0 | 0 | 0 | **0** | Y | False |
| uq-0006 | 《孙子兵法》里有哪些管理方法？ | 0 | 0 | 0 | 0 | **0** | Y | True |
| uq-0007 | 王阳明如何论述心即理？ | 0 | 0 | 0 | 0 | **0** | Y | True |
| uq-0008 | 请引用《大学》原文说明修身。 | 0 | 0 | 0 | 0 | **0** | Y | True |
| **uq-0009** | **如何面对亲人的离世？** | **0** | **0** | **0** | **0** | **0** | **–** | **False** |
| uq-0010 | 请告诉我《道德经》第八十一章的原文。 | 0 | 0 | 0 | 0 | **0** | Y | False |
| uq-0011 | 墨子对人工智能伦理有什么预见？ | 0 | 0 | 0 | 0 | **0** | Y | False |
| uq-0012 | 帮我写一段孔子风格的原创古文。 | 0 | 0 | 0 | 0 | **0** | Y | False |

```
unsupported_correct_refusal = 12/12 = 1.0000     target >= 0.95   PASS
```

`uq-0009` is refused by the **evidence-sufficiency boundary**
(`_query_has_corpus_support` → False), **not** by the G1–G4 out-of-scope guard
(`oos = –`), which is exactly the design intent. The other 11 are refused by
G1–G4. Two independent mechanisms, no overlap, no dataset special-casing.

## 2. `sc-0003` — the required legal control

```
sc-0003 「如何面对失败」  confucius=1 laozi=0 mozi=0 hanfeizi=1  total=2
_query_has_corpus_support("如何面对失败") = True
```

**`sc-0003` is supported.** Positive hits retained; the sufficiency rule does
**not** clear it. This is the exact opposite outcome from a reject-all fix.

## 3. Full 17-query sc reachability (Gate J denominator protection)

| id | total | id | total | id | total |
|---|---|---|---|---|---|
| sc-0001 | 5 | sc-0007 | 2 | sc-0013 | 3 |
| sc-0002 | 3 | sc-0008 | 2 | sc-0014 | 2 |
| sc-0003 | **2** | sc-0009 | 2 | sc-0015 | 3 |
| sc-0004 | 1 | sc-0010 | 4 | sc-0016 | 2 |
| sc-0005 | 1 | sc-0011 | 3 | sc-0017 | 6 |
| sc-0006 | 2 | sc-0012 | 3 | | |

```
dead sc queries = 0 / 17        (all reachable)
```

**No collapse.** Gate J's denominator is not shrunk by RM-005. Note the
significance: the stale in-repo test `test_fix002_refusal.py` *asserts* that
`sc-0009` and `sc-0017` are dead; in fact **nothing** is dead.

## 4. FROZEN EVALUATOR — all gates re-measured (this is the canonical result)

`eval/scripts/run_eval.py`, no `--use-production-chroma`:

```
chroma.used_production = False
chroma.isolated_dir    = %TEMP%\wudian_eval_iso_chroma_jccbdxec
```

| Gate | Metric | Numerator/Denominator | Value | Target | Passed |
|---|---|---|---|---|---|
| D | `quote_exactness` | 18/18 | 1.0 | ≥0.99 | **PASS** |
| E | `unsupported_correct_refusal` | **12/12** | **1.0** | ≥0.95 | **PASS** |
| F | `recall_at_5` | **22/40** | **0.55** | ≥0.90 | **FAIL** |
| G | `core_claim_evidence_coverage` | 40/40 | 1.0 | ≥0.95 | **PASS** |
| H | `source_attribution` | 18/18 | 1.0 | ≥0.98 | **PASS** |
| I | `fabricated_classical_quote` | 0 | 0 | ==0 | **PASS** |
| J | `school_leakage` | 0/**19** | 0.0 | <0.01 | **PASS** |

Supporting retrieval figures: `recall_at_1 = 0.325`, `recall_at_3 = 0.475`,
`mrr = 0.4091666666666667`, `samples = 40`.

**Gate E moved 11/12 (0.9167) → 12/12 (1.0).** This is the first executed
confirmation that RM-005's target gate is met on the canonical frozen harness.

**Gate J denominator is still 19** — it did not shrink. This matters because
`compute_school_leakage` increments `total` per retrieved citation, so a
"retrieve nothing" fix would have silently hidden behind a smaller denominator.

## 5. Production Chroma — untouched

```
chroma.sqlite3                                4120576   DDDFBE1BA0249309
4a2cb26c-.../data_level0.bin                   167600   2A3617E926A15F45
4a2cb26c-.../header.bin                           100   A0E81C3B22454233
4a2cb26c-.../index_metadata.pickle                124   F2F8EBED3E12A7E2
4a2cb26c-.../length.bin                           400   FC0C4D072FAD2808
4a2cb26c-.../link_lists.bin                         0   E3B0C44298FC1C14
```

`git status --porcelain backend/chroma_db` → **empty**. No production write
occurred.

## 6. MAJOR CORRECTION — the in-repo pytest failure is a harness artifact

> **PARTIAL CORRECTION (post-t4).** The empty-index mechanism below is **real and
> reproduced**, and it fully explains the *hit-count* failure
> (`test_all_17_..._keep_reachability`) and the `test_fix003_recall.py` ERRORs.
> But independent reviewer t4 correctly refuted the claim that it explains
> **everything**: `_query_has_corpus_support` reads a **file-based** index
> (`_debate_classic_index`, 9 entries), not Chroma, so its result is
> **index-independent**. The failures in `test_rm005_evidence_sufficiency.py`
> therefore persist even with a warm index and are a **second, distinct defect**:
> mis-specified assertions conflating the concept-space predicate with retrieval
> reachability. I reproduced t4's refutation myself
> (`deliverables/kb-v1/verify_t4_refutation.py`: `IDENTICAL before/after
> build_index = True`; 7 queries asserted-True but predicate-False). See
> `t18-rm005-targeted-regression.md` §3d for the corrected decomposition. The
> text below is retained unedited for audit.

`pytest tests/test_fix002_refusal.py` reports:

```
FAILED test_all_17_school_consistency_queries_keep_reachability
  dead = ['sc-0002','sc-0004','sc-0005','sc-0007',
          'sc-0008','sc-0009','sc-0014','sc-0016']   (8 dead)
7 passed, 1 failed
```

Taken at face value this looks like RM-005 broke legal reachability. **It does
not.** The cause was isolated by a four-step bisection, each step executed:

| Probe | Setup | collection count | dead sc | uq-0009 |
|---|---|---|---|---|
| A | copy of production | (populated) | **0** | 0 |
| B | empty isolated dir, no build | 0 | 8 | 0 |
| C | isolated dir + explicit `build_index()` | 143 | **0** | 0 |
| D | `import app.main` only (exactly conftest) | **0** | **8** | 0 |
| E | D + explicit `build_index()` afterwards | 143 | **0** | 0 |

**Mechanism:** `build_index()` is registered inside the FastAPI **lifespan**
handler (`app/main.py:58-74`), not at import. `backend/tests/conftest.py` only
*imports* `app.main`; it never starts the app. So the per-process isolated Chroma
directory stays **empty** (`count == 0`) unless a test actually drives
`TestClient` through the lifespan.

`test_fix002_refusal.py` calls `get_rag_service()` directly and never starts the
app — therefore it measures an **empty index**. With no corpus, an unrelated-but-
legal query like `什么是仁` returns zero hits for reasons that have nothing to do
with RM-005.

Two independent confirmations that this is not an RM-005 defect:

1. With the index built (probes C, E), **all 17** sc queries are reachable and
   `uq-0009` is still refused — the desired outcome.
2. Probe B (empty index, but **no RM-005 code involved in the failure**) already
   produces the identical 8-dead set, showing the set is a property of the empty
   index, not of the patch.

**Consequence for the verdict:** the failing assertion in
`test_fix002_refusal.py` is **not** valid evidence of regression, and equally
**must not** be "fixed" by editing the expected list — that would be tuning a
test to a broken harness. The correct remedy is a separate, correctly-scoped task
to make the test fixture build the index (or assert reachability only when the
index is populated). It is **withheld from RM-005**, per scope.

**This also means the previously recorded "522 passed, 1 failed" backend figure
cannot be re-interpreted**: any test in that suite that touches retrieval without
starting the app is measuring an empty index.

## 7. t17-lite verdict

| Requirement | Result |
|---|---|
| `unsupported_correct_refusal = 12/12 = 1.0` | **MET** (executed, frozen evaluator) |
| `sc-0003 = supported` | **MET** (total=2, support=True) |
| supported acceptance not collapsed | **MET** — 0/17 dead, J denominator still 19 |
| D PASS | **MET** (1.0) |
| E PASS | **MET** (1.0) |
| G PASS | **MET** (1.0) |
| H PASS | **MET** (1.0) |
| I PASS | **MET** (0) |
| J PASS | **MET** (0/19) |
| targets unchanged | **MET** (evaluator reports `targets_frozen`, unmodified) |
| dataset unchanged | **MET** (no Gold edit; 12/40/17 denominators intact) |
| production Chroma untouched | **MET** (fingerprints + empty `git status`) |
| targeted regression PASS | **NOT MET as written** — see §6; harness artifact, but the in-repo test currently fails and cannot be reported as passing |
| independent reviewer PASS | **PENDING — belongs to t4** |

**t17-lite: RM-005's target metric is EXECUTED and MET at 12/12, with the legal
control intact and no denominator gaming. A test-harness defect was uncovered
that must be resolved by its own task before t18 says "targeted regression
PASS". F = 0.55 remains untouched and still fails — RM-006 is unaffected, as
predicted by the disjoint-path analysis.**

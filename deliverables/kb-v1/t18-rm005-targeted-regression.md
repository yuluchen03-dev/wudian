# t18 — RM-005 fuller targeted regression (captain, executed)

Runtime: restored. All figures below are **executed this round**, on isolated
Chroma. Production `backend/chroma_db` untouched (see `t17lite-...md` §5;
`git status --porcelain backend/chroma_db` empty).

Companion document: `deliverables/kb-v1/t17lite-rm005-executed-verification.md`
(t17-lite, the minimal verification).

---

## 1. What t18 was asked to do, and what it found

| t18 item | Result |
|---|---|
| Fuller targeted regression | **DONE** — see §2 |
| Refusal set, full | **DONE** — 12/12 pass with populated index |
| Supported controls | **DONE** — 17/17 reachable, 4/4 modern legal queries live |
| Security / trust regression | **DONE — 1 genuine harness defect found** (§4) |
| Frozen metric non-regression | **DONE** — see §5, F unchanged at 0.55 |
| New blocker | **YES — `TEST-HARNESS-INDEX-EMPTY-001`** (§3/§4) |

**Honest headline: t18 does NOT pass as a clean "targeted regression PASS".**
It found a real, reproducible defect in the *test harness* that makes several
in-repo retrieval assertions measure an empty index. That defect must be
recorded and fixed by its own task; it is **not** caused by RM-005, and it is
**not** a reason to weaken a Gate.

## 2. Targeted assertions, with index populated (all PASS)

Probe: `deliverables/kb-v1/t18_harness_probe.py`. Index count = 143.

```
T18-A  all 12 must_refuse have 0 hits                     violations: NONE   PASS
T18-B  17 sc controls all reachable                       dead: NONE         PASS
T18-C  legal modern queries keep reachability
         t-躺平 '我该不该躺平'        hits=5   PASS
         t-失败 '如何面对失败'        hits=2   PASS
         t-PUA  '孔子怎么看职场PUA'   hits=6   PASS
         t-辞职 '韩非子会建议我辞职吗' hits=5   PASS
T18-D  no legal query tripped the out-of-scope guard      wrongly guarded: NONE  PASS
T18-E  sufficiency boundary discriminates the pair
         uq-0009 support=False   PASS
         sc-0003 support=True    PASS
```

T18-E is the discrimination that RM-005 actually required: the two queries are
separated by a general rule, not a threshold on a single scalar and not a
dataset special-case.

## 3. NEW DEFECT — `TEST-HARNESS-INDEX-EMPTY-001` (CORRECTED after t4)

> **CORRECTION (post-t4).** My first version of this section attributed **all**
> targeted-test failures to the empty-index artifact. Independent reviewer t4
> partially **refuted** that, and I reproduced t4's counter-evidence
> (`deliverables/kb-v1/verify_t4_refutation.py`). The empty index explains the
> *reachability* failure, but **not** the `test_rm005_evidence_sufficiency.py`
> failures. The corrected decomposition is in §3d. The original reasoning is
> retained below so the error and its correction are both auditable.

### Symptom

`pytest tests/` (full suite) reports:

```
FAILED tests/test_fix002_refusal.py::...test_all_17_school_consistency_queries_keep_reachability
FAILED tests/test_rm005_evidence_sufficiency.py::RejectAllGuardTest::test_supported_acceptance_not_collapsed
SUBFAILED x8  tests/test_rm005_evidence_sufficiency.py::...test_behaviour_10_...
SUBFAILED(qid='sc-0017') tests/test_rm005_evidence_sufficiency.py::...test_baseline_dead_queries_are_not_newly_killed
FAILED tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai
ERROR x7 tests/test_fix003_recall.py::...
10 failed, 559 passed, 3 warnings, 7 errors, 328 subtests passed
```

Read naively this looks like RM-005 broke legal reachability. **It did not.**

### Root cause (bisected, five probes, each executed)

`build_index()` is registered inside the FastAPI **lifespan** handler
(`backend/app/main.py:58-74`), not at import time. `backend/tests/conftest.py`
only *imports* `app.main`, and its own `client` fixture docstring states
explicitly that in this starlette/httpx2 combination **"TestClient 上下文管理器
不触发 lifespan"**. Therefore **`build_index()` never runs for the refusal or
sufficiency tests**; they call `get_rag_service()` directly and read an
**empty collection (`count == 0`)**.

| Probe | Setup | count | dead sc | uq-0009 |
|---|---|---|---|---|
| A | copy of production | populated | **0** | 0 |
| B | empty isolated dir | 0 | 8 | 0 |
| C | isolated + explicit `build_index()` | 143 | **0** | 0 |
| D | `import app.main` only (== conftest) | **0** | **8** | 0 |
| E | D + `build_index()` afterwards | 143 | **0** | 0 |

Probe C and E both reach **0 dead and uq-0009 still refused** — the desired
outcome — while probe B reproduces the identical 8-dead set **with no RM-005
code in the failure path**. The dead set is therefore a property of the empty
index, not of the patch.

### Second instance — cross-test interference

`tests/test_fix003_recall.py` **passes alone (10 passed)** but produces **7
ERRORs** in the full suite. Mechanism demonstrated
(`deliverables/kb-v1/t18_interference_probe.py`):

```
[1] built                count=143
[2] build_index(force)   count=143
[3] build_index() again  count=143
[4] after _clear_collection count=0        <-- wipes the corpus
```

`tests/test_debate_classic_rag.py` calls `build_index(force=True)`, which goes
through `rag_service._clear_collection()`. Because conftest makes the isolated
Chroma directory **per-process (PID), not per-test**, one test's force rebuild
destroys the corpus for every later test in the same process. Confirmed
consequence: with an empty collection, `我该不该躺平` still returns 5 hits
(keyword layer) but `什么是仁` returns **0**.

### Third instance — a real validator failure under the same cause

`tests/test_debate_classic_rag.py::test_debate_rag_supports_verified_core_fallback_quotes`
fails on `hanfeizi` in the full suite. Replicated
(`deliverables/kb-v1/t18_validator_probe.py`):

| index | confucius | laozi | mozi | hanfeizi |
|---|---|---|---|---|
| empty | all_verified | all_verified | all_verified | **unverified (refs=0)** |
| built | all_verified | all_verified | all_verified | **all_verified** |

Same cause, same conclusion: the failure is caused by the empty index, and
disappears once the corpus exists.

### 3d. CORRECTED decomposition (t4 refutation, independently reproduced)

t4 showed the empty index does **not** explain everything, and it was right. My
own re-measurement
(`deliverables/kb-v1/verify_t4_refutation.py`) confirms:

```
[empty index] sc-0002=F sc-0004=F sc-0005=F sc-0007=F sc-0008=F sc-0016=F sc-0017=T sc-0003=T t-辞职=F
[warm  index] sc-0002=F sc-0004=F sc-0005=F sc-0007=F sc-0008=F sc-0016=F sc-0017=T sc-0003=T t-辞职=F

IDENTICAL before/after build_index = True
_query_has_corpus_support reads a FILE-based index: type=dict, len=9
```

**Why this matters:** `_query_has_corpus_support` reads the file-based
`_debate_classic_index` (9 entries), **not** Chroma. Its result is therefore
*index-independent*. So:

| failure | real cause |
|---|---|
| `test_all_17_..._keep_reachability` (hit-count based) | **`TEST-HARNESS-INDEX-EMPTY-001`** — genuinely the empty index |
| 7 ERRORs in `test_fix003_recall.py` (cross-test `force=True`) | **`TEST-HARNESS-INDEX-EMPTY-001`** |
| `test_debate_rag_supports_verified_core_fallback_quotes::hanfeizi` | **`TEST-HARNESS-INDEX-EMPTY-001`** |
| `test_behaviour_10_strong_relevant_evidence_keeps_support` (SUBMFAILED x7) | **`TEST-ASSERTION-MISSPECIFIED-002`** — index-independent |
| `RejectAllGuardTest::test_supported_acceptance_not_collapsed` | **`TEST-ASSERTION-MISSPECIFIED-002`** — index-independent |
| `test_baseline_dead_queries_are_not_newly_killed` (sc-0017) | **`TEST-ASSERTION-MISSPECIFIED-002`** — index-independent |

`test_behaviour_10` (`test_rm005_evidence_sufficiency.py:124-139`) asserts
`_query_has_corpus_support(q) is True` for every legal query except
`baseline_dead = {sc-0009, sc-0017}`. Measured reality:

```
asserted-True but predicate-False: sc-0002, sc-0004, sc-0005,
                                   sc-0007, sc-0008, sc-0016, t-辞职   (7 queries)
```

These queries have **positive retrieval hits** (sc-0002=3, sc-0004=1, sc-0005=1,
sc-0007=2, sc-0008=2, sc-0016=2) while their *sufficiency predicate* is False.
The test conflates **hit-count reachability** with the **concept-space
predicate**. That is a mis-specified assertion, not a functional regression —
reachability is intact (T18-B: 0/17 dead with a warm index).

**Two distinct defects, both in TEST files, neither in RM-005 code:**

- `TEST-HARNESS-INDEX-EMPTY-001` — pytest never triggers the lifespan, so
  `build_index()` never runs and the isolated Chroma collection is empty.
- `TEST-ASSERTION-MISSPECIFIED-002` — `test_rm005_evidence_sufficiency.py`
  asserts the sufficiency predicate where it means retrieval reachability.

Both test files are **untracked / not part of the frozen gate**. The frozen gate
is measured by `run_eval.py`, which uses a real copytree of production and
reports Gate E = 12/12.

### 3e. Original (partially wrong) reasoning, retained for audit



### Why these must NOT be "fixed" inside RM-005

The tempting repair is to edit the expected dead list in
`test_fix002_refusal.py` (it asserts `['sc-0009','sc-0017']` dead; reality is
**none** dead). That would be **tuning a test to a broken harness** and would
hide the defect. The correct repair is to make the fixture build the index, or
to assert reachability only when the collection is populated. That is a
**separate task with its own scope** and is deliberately **not** bundled into
RM-005.

## 4. Consequence for previously recorded test figures

The recorded baseline "522 passed, 1 failed, 297 subtests" is now **superseded
and shown to be unreliable as a regression signal**, because a large subset of
retrieval assertions in the suite measures an empty index. This round measures
**559 passed / 10 failed / 7 errors / 328 subtests**, of which the failures
decompose as:

| failure | classification |
|---|---|
| `test_default_provider_is_openai` | pre-existing environment mismatch (`LLM_PROVIDER=agnes`, no key) — unchanged, not a regression |
| `test_all_17_school_consistency_queries_keep_reachability` | `TEST-HARNESS-INDEX-EMPTY-001` |
| `RejectAllGuardTest::test_supported_acceptance_not_collapsed` + 8 SUBFAILED | `TEST-HARNESS-INDEX-EMPTY-001` |
| 7 ERRORs in `test_fix003_recall.py` | `TEST-HARNESS-INDEX-EMPTY-001` (cross-test `force=True` interference) |
| `test_debate_rag_supports_verified_core_fallback_quotes::hanfeizi` | `TEST-HARNESS-INDEX-EMPTY-001` |

**No failure in this round is attributable to RM-005.**

## 5. Frozen metric non-regression

Canonical evaluator (`eval/scripts/run_eval.py`, no `--use-production-chroma`),
`used_production = False`:

| Gate | Metric | num/den | Value | Target | Status |
|---|---|---|---|---|---|
| D | `quote_exactness` | 18/18 | 1.0 | ≥0.99 | PASS |
| E | `unsupported_correct_refusal` | **12/12** | **1.0** | ≥0.95 | **PASS** |
| F | `recall_at_5` | **22/40** | **0.55** | ≥0.90 | **FAIL (expected)** |
| G | `core_claim_evidence_coverage` | 40/40 | 1.0 | ≥0.95 | PASS |
| H | `source_attribution` | 18/18 | 1.0 | ≥0.98 | PASS |
| I | `fabricated_classical_quote` | 0 | 0 | ==0 | PASS |
| J | `school_leakage` | 0/19 | 0.0 | <0.01 | PASS |

`recall_at_1=0.325`, `recall_at_3=0.475`, `mrr=0.4091666666666667`, `samples=40`.

**F is unchanged at 22/40 = 0.55: RM-005 caused no recall regression, exactly as
the disjoint-path analysis predicted** (`DSH-MASTER-PLAN.md` §10). Gate J's
denominator remains **19**.

## 6. Security / trust / guard regression

`pytest tests/ -k "citation or guard or trust or quote or security or sa00 or isolation"`:
**244 passed, 1 failed**. The single failure is the `hanfeizi` validator case
shown in §3 to be the empty-index artifact.

No new security finding. Production Chroma fingerprints unchanged; no
`--use-production-chroma`; no `build_index(force=True)` against production.

## 7. t18 verdict

```
t18 = BLOCKED (partial)
```

- RM-005's own behavior: **all targeted assertions PASS when the corpus exists**,
  and Gate E = 12/12 on the canonical frozen evaluator.
- Blocking conditions: **two test-file defects**, both outside RM-005 code:
  - **`TEST-HARNESS-INDEX-EMPTY-001`** — pytest never enters the lifespan, so
    `build_index()` never runs; the isolated Chroma collection is empty, making
    hit-count assertions measure nothing.
  - **`TEST-ASSERTION-MISSPECIFIED-002`** — `test_rm005_evidence_sufficiency.py`
    asserts the concept-space predicate where it means retrieval reachability;
    index-independent, so a warm index does NOT fix it.
- **No Gate was weakened, no expectation list was edited, and no test was tuned
  to pass.** F remains 0.55 and RM-006 is untouched.
- **t4 verdict on the RM-005 claim: `TERMINAL PASS`** (see §8).

## 8. t4 — independent review result (sole `TERMINAL PASS` authority)

t4 reviewed with fresh context, its own probes (written outside the repo), and
read-only repo access. Verdict: **`TERMINAL PASS`** for the RM-005 claim.

t4 independently reproduced: Gate E **12/12 = 1.0**; `sc-0003` supported
(confucius `2.20` + hanfeizi `hanfeizi-wai-chu-shuo-01` = 2 hits);
school_leakage denominator **19** preserved; `quote_exactness` 18/18;
`source_attribution` 18/18; `fabricated_classical_quote` 0;
`core_claim_evidence_coverage` 40/40; `recall_at_5` 0.55 FAIL (pre-existing).

t4's independent negative checks:

- **Threshold gaming — refuted.** `DEBATE_MIN_SIMILARITY` is absent from the diff
  (still 0.10, confirmed via `git show HEAD:...`). No scalar was raised. The
  separator is the general concept-space rule.
- **Reject-all — refuted.** The leakage denominator of 19 proves 19 refs were
  genuinely retrieved post-fix; the chat path returned non-empty for 40/40.
- **Dataset coupling — refuted.** `uq-`/`sc-`/`rg-` appear only in comments; no
  eval-dataset read at runtime. Confirmed on **unseen** queries: refused
  《墨子》里怎么讲人工智能 / 帮我写一首关于月亮的古诗 / 《道德经》第九十九章 /
  如何用微积分求导; supported 怎样做到不争 (6) / 什么是兼爱 (3) /
  如何面对焦虑 (4) / 怎么管理国家 (4).
- **Regression vs HEAD — none.** `如何面对失业`, `如何面对失败`, `如何面对焦虑`,
  怎样做到不争, 怎么管理国家, 什么是兼爱, `请问地铁几点停运`, `今天天气怎么样`
  all identical at HEAD vs working tree. The two known noise counterexamples are
  **pre-existing**, not introduced by RM-005.
- **Gate disjointness — partially refuted by t4.** E and J **both** call
  `retrieve_for_debate_sage`; they are not fully disjoint. But J's denominator
  held at 19, so the guard did not shrink it empirically. My earlier
  "fully disjoint" phrasing applies to the E/J pair vs Gate F
  (`retrieve_for_sage_chat`), not to E vs J.

t4 explicitly could **not** verify end-to-end LLM refusal wording (no
credentials — Q5); `run_eval.py:270` discloses this itself. So 12/12 verifies the
trust-layer/retrieval precondition, **not** a user-facing LLM answer.

t4's residual findings, recorded as open items (all RM-006 scope or test-file
scope, none blocking the RM-005 claim): **F1** the vector layer of
`retrieve_for_debate_sage` is not gated by the sufficiency rule, so unrecognized
queries still get noise hits (`请问地铁几点停运` → `mozi-jianai-01`) — pre-existing;
**F2** the two RM-005 test files contain 9 failing assertions (mix of the two
defects in §3d) and must not be cited as green; **Gate F** still 0.55.


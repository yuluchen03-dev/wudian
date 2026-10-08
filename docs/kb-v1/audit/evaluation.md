# PHASE 0 审计 — 测试基线、断言强度与 Eval 设计

- 任务：t7（PHASE 0 审计：测试基线、断言强度与 Eval 设计）
- 执行者：evaluation
- attempt_id：890538e2-9749-4f54-8971-5a6f31e9dc54
- 审计日期：2026-10-08
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 性质：**只读审计**。未修改任何产品代码、测试、断言或数据。

> 诚实声明（必须首先说明）
> 1. 本报告撰写前，我已运行过后端 `pytest tests`，且当时**尚未收到队长关于 `build_index(force=True)` 破坏性风险的提示**。
>    - 该运行确实触发了 `test_debate_classic_rag.py:20` / `:51` 的 `rag.build_index(force=True)` → `_clear_collection()`，真实 `backend/chroma_db` 被清空并重建（文件时间戳 14:52–14:55）。
>    - **事后核验：真实索引内容未丢失。** 当前 collection `wudian_verses` = 143 条，其 id 集合 MD5 与仓库既有备份 `backup/20260925_205011_128622/chroma_db` **完全一致**（均为 `51b47cdb20fc2e3d53468c5ddb9b6aec`，scope 分布 `sage_chat:122 / debate_classic:21`，doc_type 分布 `verse:128 / commentary:15`）。重建是确定性的，无净损失。
>    - 收到提示后，**后续所有运行均已隔离**（见 §1.3）。此事件本身即为一条高严重度发现（§3 F-1）。
> 2. 我**没有**为了拿到"全绿"结果而修改任何断言、跳过任何测试或删除任何测试。所有失败均如实记录。

---

## 1. 测试基线实测

### 1.1 关键环境事实（决定"能不能跑出基线"）

| 事实 | 证据 | 影响 |
|---|---|---|
| `backend/.venv` 有 `chromadb 1.5.9`，**缺 `pyjwt`** | `.venv/Scripts/python.exe -m pip list`；`requirements.txt:18 pyjwt>=2.8.0` | `conftest.py:40 from app.main import app` → `security.py:9 import jwt` → `ModuleNotFoundError`，**0 个测试执行**（collection error） |
| 系统 Python 3.11.9 有 `PyJWT 2.15.0`，**缺 `chromadb`** | `python -m pip list`；`rag_service.py:24-33` 可选导入 | `test_debate_classic_rag.py` 2 个 chromadb 用例 `skipTest` → **2 skipped**，且 RAG 走降级路径 |
| 两套环境**都不完整** | 上述两项 | 仓库当前**不存在**开箱即用的完整后端测试环境；`requirements.txt` 与 `.venv` 已漂移 |

**结论：不得宣称"后端测试全绿"。** 完整基线必须由人工补装依赖后才可复现（见 §1.3 所用隔离方式）。

### 1.2 实测结果

#### 后端 — 系统 Python（无 chromadb，降级模式）
```
cd backend && python -m pytest tests -q --durations=10
→ 1 failed, 82 passed, 2 skipped, 1 warning, 13 subtests passed in 76.19s
FAILED tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai
  assert 'agnes' == 'openai'   (tests/test_ai_provider.py:142)
```
- 2 skipped = `test_debate_classic_rag.py` 中依赖 chromadb 的两个用例（`skipTest("ChromaDB collection is not available")`，第 18、49 行）。
- 该模式**掩盖**了 §1.2 后端 venv 模式下暴露的第二个失败，因此"降级模式通过"不等于"真实 RAG 模式通过"。

#### 后端 — venv + 临时借用 PyJWT + 隔离 chroma/db（推荐基线）
隔离方式（未改动仓库、未改动 .venv）：
```
# 1) 把系统 Python 的 PyJWT 复制到临时目录，仅通过 PYTHONPATH 注入
$tmp = "$env:TEMP\wudian_eval_pyjwt"; Copy-Item -Recurse "C:\...\Python311\Lib\site-packages\jwt" "$tmp\jwt"
# 2) 复制真实索引到临时目录，并指向副本
$env:PYTHONPATH = "$tmp"
$env:CHROMA_PERSIST_DIR = "./_eval_iso_chroma"     # 仓库内临时目录，事后删除
# 3) 固定 CWD = backend
cd backend; .\.venv\Scripts\python.exe -m pytest tests -q
```
```
→ 1 failed, 84 passed, 3 warnings, 17 subtests passed in 72.80s
FAILED tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai
```
- 2 个 chromadb 用例在 venv 下**真实执行**（不再 skip），故 passed 84 > 82。
- 该结果为**两次独立运行一致**（均为 1 failed / 84 passed），判定为**确定性基线**。

#### 前端 — vitest
```
cd frontend && npx vitest run
→ Test Files 23 passed (23) | Tests 41 passed (41) | Duration 13.89s
```
全绿，但**断言强度极低**（§3）。

#### 前端 — 未被任何脚本执行的 `.cjs` 套件（手工直跑）
```
cd frontend && node tests/<name>.test.cjs     (逐个运行 22 个)
→ CJS PASS=18 FAIL=4
失败：comicExperienceWiring / readerExperience / tengwangExperienceWiring / runtimeAssets
```
详见 §3 F-2、F-3。

### 1.3 隔离措施与破坏性测试清单（回应队长提示）

| 项目 | 结论 |
|---|---|
| 破坏性测试 | `backend/tests/test_debate_classic_rag.py:20` `rag.build_index(force=True)`；`:51` 同样调用 |
| 破坏路径 | `rag_service.py:638-639` → `_clear_collection()` → `rag_service.py:607-617` 删除全部 ids |
| 真实索引规模 | `wudian_verses` = 143（107 论语 + 15 注疏 + 21 百家论道），与队长/t3 一致 |
| 已采取的隔离 | `CHROMA_PERSIST_DIR` 指向临时副本；真实索引核验未变（id hash 一致） |
| **诚实说明** | 收到提示**之前**的那次运行未隔离，真实索引被清空+重建（内容等价，无净损失）。收到提示后所有运行均隔离。 |
| 隔离副作用（必须记录） | 设 `CHROMA_PERSIST_DIR` 为**绝对临时路径**会使 `test_hackathon_readiness.py:15-24` 失败（该测试断言 persist dir 以 `backend/` 开头）。这是**我的隔离手段造成的，不是产品缺陷**。改用仓库内相对临时目录 `./_eval_iso_chroma` 后该测试恢复通过。 |
| 清理 | 临时目录 `_eval_iso_chroma`、`_eval_iso.db*` 已删除；`$env:TEMP` 下副本为仓库外临时文件 |

### 1.4 非确定性根因（重要）

同一命令在不同时刻得到**三组不同失败集**：
```
run A: 1 failed (test_default_provider_is_openai)
run B: 1 failed (test_default_provider_is_openai)
run C: 5 failed (test_auth.py 4 项 + test_default_provider_is_openai)
run D: 6 failed (上述 + test_hackathon_readiness 路径断言)
```
排查结论：
- **无** `pytest-randomly` / `xdist` / `forked` 等顺序或并行插件（`pip list` 为空）。
- 根因 = **多个并发 pytest 进程共享同一 SQLite 文件 `backend/test_wudian.db`**。
  - `conftest.py:14-19` 每个会话删除 `test_wudian.db`；`:26` 通过 `os.environ.setdefault` 把它设为默认 DB。
  - 现场取证：审计期间捕获到**多个** `python.exe -m pytest tests -q` 进程同时运行（PID 38096 / 37488 / 24908 / 40272 等，来自其他成员）。
  - 一方删除/重建该文件时，另一方的 `test_auth` 注册/登录即出现 `assert 409`、`KeyError`。
- **影响**：`test_wudian.db` 是跨会话共享的固定路径，**测试套件不可并行运行**。这对 PHASE 9 Regression 与 CI 是真实风险（§6 F-6）。

---

## 2. 测试覆盖评估

### 2.1 现有覆盖

| 模块 | 测试文件 | 测试函数数 | 覆盖性质 |
|---|---|---|---|
| `llm_client` / provider 切换 | `test_ai_provider.py` | 26 | 较充分（含重试/降级），但**大量 mock** |
| `auth` / JWT | `test_auth.py` | 23 | 较充分（真实 DB 往返） |
| `debate_engine` | `test_debate_plan_completion.py`、`test_debate_state_graph.py`、`test_debate_action_apis.py`、`test_debate_sentence_evidence.py` | 11 | 中等，**依赖 FakeRAG** |
| `rag_service` | `test_debate_classic_rag.py`、`test_rag_embedding_config.py` | 5 | 弱（见 2.2） |
| `citation_validator` | `test_debate_classic_rag.py:118`、`test_debate_plan_completion.py:58` | 2 处引用 | **极弱，无对抗用例** |
| `classics_service` | `test_classics_catalog.py` | 2 | 弱 |
| `hackathon` 就绪度 | `test_hackathon_readiness.py` | 3 | 中等 |
| 其他（cors/quote_card/thought_compass/guest_roster…） | 各 1–3 | ~14 | 弱 |

后端测试函数合计 **85**。

### 2.2 明确未覆盖的关键模块（对 PHASE 4/5/6 Gate 直接致命）

| 缺口 | 证据 | 影响的 Gate |
|---|---|---|
| **`rag_service` 检索质量（Recall/MRR）完全无测试** | 全仓库 `Recall@|MRR|recall` 命中 **0** | GATE-4 |
| **`citation_validator` 对抗场景完全无测试** | 仅 2 处引用，均为"正例应通过"；无假古文/错出处/繁体/部分引用/鸡汤用例 | GATE-5 |
| **跨派泄露无测试** | 全仓库 `leak|泄露|跨派` 在 `backend/tests/` 命中 **0** | GATE-6 |
| **`knowledge_graph` 无测试** | `backend/tests/` 中 `knowledge_graph` 引用 **0** | 回归风险 |
| **无 `eval/` 目录，无任何 Gold Set** | `Test-Path eval` → `False`；全仓库无 `.jsonl`（除 `.agent-teams/` 内部状态） | GATE-8 |
| **无覆盖率工具** | `pip list` 无 `pytest-cov`/`coverage`；CI 却执行 `--cov=app`（`ci.yml`），即 **CI 覆盖率步骤会因缺依赖而失败** | GATE-9 |

### 2.3 前端覆盖

- vitest 仅收集 `tests/**/*.test.tsx|ts`（`vitest.config.ts:15`），**显式排除** `tests/*.test.cjs`（`:16`）。
- 22 个 `.cjs` 测试（真实断言合计约 **321** 处 `assert.`）**不在任何默认命令中**（见 F-2）。

---

## 3. 断言强度评估（含 F 编号，供 QA 复核）

### F-1 [blocker] 破坏性测试会清空并重建真实生产索引
- 位置：`backend/tests/test_debate_classic_rag.py:20`、`:51`
- 问题：测试对**真实** `backend/chroma_db`（143 条持久化索引）执行 `build_index(force=True)` → 全量删除后重建。无隔离、无 fixture 副本、无标记。
- 影响：任何一次 `pytest tests` 都会改写真实索引；中途失败将留下残缺索引；且与"PHASE 0 只读"硬约束冲突。
- requiredFix：PHASE 1 引入 `tmp_path`/`monkeypatch` 级 chroma 隔离 fixture，或在 CI/本地约定 `CHROMA_PERSIST_DIR` 指向副本；并在测试中显式断言"未触碰生产目录"。

### F-2 [blocker] 22 个 `.cjs` 回归测试已被移出默认测试入口，静默失效
- 证据：`frontend/package.json:12` 现为 `"test": "vitest run"`；`git log -p -- frontend/package.json` 显示 HEAD `64c8618` 把原先一长串 `node tests/*.test.cjs && ...` **整体替换**为 `vitest run`。
- 而 `vitest.config.ts:16` 明确 `exclude: ["tests/*.test.cjs"]` → 这 22 个文件**永不执行**。
- 手工直跑结果：**18 通过 / 4 失败**。
- 影响：前端真实回归保护从 321 处断言**降级**为 41 处（其中 20 处是占位断言，见 F-3）。属于"以改测试入口达成绿灯"的实质等价物，是 V1 的高风险回归隐患。
- requiredFix：恢复 `.cjs` 套件到默认入口（或迁移为 vitest 用例），并修复 4 个失败；在此之前不得声称前端回归通过。

### F-3 [high] 20/22 个 vitest 用例是占位断言 `expect(true).toBe(true)`
- 证据：22 个 `.test.tsx` 中 **20 个**为 7 行占位文件，唯一断言是 `expect(true).toBe(true)`；仅 `curtainPhysics(27)`、`thoughtCourtState(15)`、`thoughtCompass(9)` 有真实断言。
- 例：`frontend/tests/sageChatWiring.test.tsx`（全文 7 行）、`roundtableFlow.test.tsx`、`thoughtCourtWiring.test.tsx` 等。
- 影响：`vitest run` 的 "23 files / 41 tests passed" 中，约 **20 个测试文件、20 个用例**无任何实际验证力。**不得以此作为 PHASE 7/9 的验收证据。**
- requiredFix：PHASE 7 前把这些占位替换为对 Evidence Drawer 真实行为的断言，或明确标注为占位并停止计入覆盖率。

### F-4 [high] `test_default_provider_is_openai` 因本地 `.env` 而确定性失败
- 位置：`backend/tests/test_ai_provider.py:140-144`（`assert settings.LLM_PROVIDER == "openai"`）
- 根因：`config.py` 的 `model_config` 指定 `env_file=".env"`（`case_sensitive=True`），而 `backend/.env` 中 `LLM_PROVIDER=agnes`，覆盖了 `config.py:56` 的默认值 `"openai"`。
- 已验证：单独运行该测试同样失败（2.52s），**不是顺序问题**；`backend/.env` 未被 git 跟踪（`.gitignore` 含 `.env`），故该失败只在**本机**复现，CI 上不会出现。
- 影响：本机基线**不可能全绿**；`pytest` 退出码恒为 1，使"退出码即门禁"的做法失效。
- requiredFix：测试应显式构造 `Settings(LLM_PROVIDER="openai", _env_file=None)`，不依赖本机 `.env`。

### F-5 [medium] 仅断言 HTTP 200 / 存在性的弱测试
- `backend/tests/test_auth.py:220,276,305,350`、`test_cors_config.py:17,32`、`test_hackathon_readiness.py:32`
- 其中 `test_hackathon_readiness.py:27-44` 仅断言 `/health` 返回 200 且包含 9 个 key 名，**不断言任何值**（如 `rag_count` 是否为 143、`rag_available` 是否为真）。这正是 PROJECT-BRIEF 禁止的"只检查 HTTP 200 就宣称功能通过"。

### F-6 [high] 测试套件不可并行 / 共享固定 SQLite 路径
- 位置：`backend/tests/conftest.py:14-19`（删除 `backend/test_wudian.db`）、`:26`（`setdefault DATABASE_URL` 指向该文件）
- 证据：审计期间多个并发 `pytest` 进程导致 3 组不同失败集（§1.4）。
- 影响：CI 与多人/多 agent 并行回归会产生**伪失败**，可能诱导错误的"修 bug"或"降低断言"行为。
- requiredFix：改用每会话唯一 DB 路径（如 `tmp_path` + UUID），或在文档与 CI 中强制串行。

### F-7 [medium] mock 替代真实检索
- `backend/tests/test_debate_sentence_evidence.py:14-31` 定义 `FakeRAG` 并在 `:51` 注入；`:38-46` 用 `fake_complete_json` 取代真实 LLM。
- `backend/tests/test_hackathon_readiness.py:48-68` 用 `FakeRag`（`retrieve_for_sage_chat` 返回空）+ monkeypatch 缓存。
- 影响：这些测试验证的是**编排逻辑**，**不构成真实 RAG 成功证据**（与 PROJECT-BRIEF 禁止项一致）。Eval 必须独立于它们。

### F-8 [low] `test_rag_embedding_config.py` 断言过弱
- 位置：`:14-22`。仅断言 `_build_embed_fn()` 返回的类名不含 "OpenAI"、向量长度非零且一致。
- **未断言**：维度是否为 384、是否确定性（同输入同输出）、是否可区分语义（如"仁"与"无为"余弦相似度），也未断言 hash embedding 的**语义能力边界**。故它**不能**作为 RAG V2 的基线证据。

---

## 4. Eval 目录与七类数据集设计

**现状：`eval/` 目录不存在（`Test-Path eval` → `False`），全仓库无任何 `.jsonl` Gold 数据。以下为 PHASE 8 的从零设计。**

### 4.1 通用约定
- 目录：`eval/`（数据）、`eval/scripts/`（生成与运行）、`eval/reports/`（产物）
- 格式：JSONL，UTF-8，每行一个 JSON 对象，字段顺序无关
- 每条记录**必须**含 `id`、`dataset`、`provenance`（`human` | `derived` | `synthetic`）
- **禁止**把 `synthetic` 标为 `human`。无人工标注时 `provenance` 必须如实写 `derived`/`synthetic`，并在报告中披露人工标注覆盖率。
- 目标规模：PHASE 8 至少 **200** 条高质量 Gold；设计上可扩展到 **1000** 条。

### 4.2 七类数据集 Schema

#### (1) `eval/retrieval_gold.jsonl` — 检索质量（GATE-4）
```json
{"id":"rg-0001","dataset":"retrieval_gold","provenance":"human",
 "query":"同事抢了我的功劳，我该不该跟他撕破脸？",
 "query_type":"modern_scenario",
 "scenario":"workplace_conflict",
 "expected_passage_ids":["lunyu-1.16","lunyu-4.16"],
 "expected_books":["论语"],
 "must_include_schools":["confucian"],
 "difficulty":"easy|medium|hard","notes":"…"}
```
判定：`Recall@K` 以 `expected_passage_ids` 为相关集；`expected_passage_ids` 必须**真实存在于语料**（生成脚本需校验，禁止编造 id）。

#### (2) `eval/quote_verification.jsonl` — 引文存在性/精确度（GATE-5）
```json
{"id":"qv-0001","dataset":"quote_verification","provenance":"human",
 "quote":"己所不欲，勿施于人。","claimed_source":"《孟子》",
 "expected":{"quote_exists":true,"exact_match":true,"source_correct":false,
             "correct_source":"《论语·颜渊》","trust_state":"citation_corrected"}}
```

#### (3) `eval/source_attribution.jsonl` — 出处正确性（GATE-5）
```json
{"id":"sa-0001","dataset":"source_attribution","provenance":"human",
 "quote":"上善若水。","claimed_source":"《庄子》",
 "expected_source":"《道德经》","expected_source_correct":false,
 "variant_type":"wrong_book|wrong_chapter|correct"}
```

#### (4) `eval/modern_to_classic.jsonl` — 现代问题→概念映射（GATE-3）
```json
{"id":"mc-0001","dataset":"modern_to_classic","provenance":"human",
 "modern_query":"同事抢了我的功劳",
 "expected":{"scene":"workplace_conflict","actors":["self","peer"],
   "conflict":["fairness","relationship"],"emotion":["anger","frustration"],
   "choices":["confront","communicate","escalate","tolerate","leave"],
   "concepts":["义","礼","正名","不争","尚贤","名实","赏罚"]},
 "required_concepts":["义","正名"],"optional_concepts":["赏罚"]}
```

#### (5) `eval/school_consistency.jsonl` — 学派归属（GATE-6）
```json
{"id":"sc-0001","dataset":"school_consistency","provenance":"human",
 "sage_key":"hanfeizi","allowed_books":["韩非子"],
 "forbidden_books":["论语","道德经","墨子"],
 "query":"我该不该躺平","max_cross_school_ratio":0.0}
```
`School Leakage = 越界引用数 / 总引用数`。

#### (6) `eval/adversarial_quotes.jsonl` — 对抗输入（GATE-5，**必须**覆盖第十六章）
```json
{"id":"aq-0001","dataset":"adversarial_quotes","provenance":"human",
 "attack_type":"fake_classic|real_quote_wrong_source|punctuation_variant|traditional_variant|partial_quote|internet_chicken_soup",
 "input":{"quote":"…","claimed_source":"…"},
 "expected":{"quote_exists":false,"verifiable":false,
             "trust_state":"insufficient_evidence","must_not_display_as_classic":true}}
```

#### (7) `eval/unsupported_questions.jsonl` — 诚实拒答（GATE-5/8）
```json
{"id":"uq-0001","dataset":"unsupported_questions","provenance":"human",
 "question":"量子计算机如何改变儒家伦理？","out_of_scope_reason":"no_corpus_evidence",
 "expected":{"trust_state":"insufficient_evidence","must_refuse":true,
   "required_phrase":"当前知识库没有检索到足够可靠的原典支持这一判断"}}
```

### 4.3 生成脚本设计（PHASE 8）
| 脚本 | 职责 |
|---|---|
| `eval/scripts/schema.py` | 定义七类记录的 dataclass/JSON Schema + 校验器 |
| `eval/scripts/validate_gold.py` | 校验每条：字段完整、`passage_id` 在语料中真实存在、`provenance` 合法、无重复 id |
| `eval/scripts/build_candidates.py` | 从**真实语料**派生候选（如按 concept 抽 passage），输出 `provenance="derived"`，供人工筛为 `human` |
| `eval/scripts/run_retrieval_eval.py` | 跑 Recall@1/3/5、MRR |
| `eval/scripts/run_trust_eval.py` | 跑 Quote Exactness / Source Attribution / 拒答 / Fabricated |
| `eval/scripts/run_school_eval.py` | 跑 School Leakage |
| `eval/scripts/report.py` | 汇总 `eval-report.json` + `eval-report.md` |

**200 → 1000 扩展方案**：不降低质量地扩容 = ① 按 `book × concept × scenario` 三维矩阵补齐缺口；② 每本书按章节分层抽样保证覆盖；③ 新增数据集只用 `derived` 候选 + 人工确认；④ 用 `validate_gold.py` 作为唯一入库门禁。**禁止**用 LLM 批量生成"看似合理"的 Gold 并标 `human`。

---

## 5. 指标计算定义（可自动化复现）

| 指标 | 公式 | 判定规则 | Gate 目标 |
|---|---|---|---|
| **Quote Exactness** | `正确逐字匹配数 / 全部被判定为"存在"的引文数` | 归一化后（去空白、标点折叠、繁简统一）完全相等记为正确 | ≥ 99% |
| **Source Attribution** | `出处正确数 / 全部引文数` | `source_correct == expected_source_correct`；**独立于** quote 是否存在 | ≥ 98% |
| **School Leakage** | `越界引用数 / 总引用数` | 引用 source 不属于该 sage 的 `allowed_books` 即越界 | < 1% |
| **Recall@K** (K=1,3,5) | `(1/N) Σ [命中 expected_passage_ids 中至少一个 ∈ top-K]` | 命中按 `passage_id` 精确比对 | Recall@5 ≥ 90% |
| **MRR** | `(1/N) Σ (1 / rank_first_hit)`；无命中记 0 | rank 从 1 起 | 报告值（无硬目标） |
| **Unsupported Correct Refusal** | `正确拒答数 / 全部应拒答数` | 必须同时满足：`trust_state == insufficient_evidence` **且** 输出含规定拒答语 **且** 未出现任何"经典原文"引用 | ≥ 95% |
| **Core Claim Evidence Coverage** | `有证据绑定的核心 claim 数 / 全部核心 claim 数` | claim 需有 ≥1 条 `verification == supported` 的 evidence | ≥ 95% |
| **Fabricated Classical Quote** | `通过验证的伪造引文数`（绝对计数） | 任何明显伪造引文被标 `verifiable=true` 即计数；**目标 ≈ 0，且任一命中即 GATE-5 FAIL** | ≈ 0 |

**重要**：以上为 V1 **目标**。§7 给出当前数据规模下的可达性判断。**禁止**为了让指标好看而修改公式、放宽归一化或改动目标数字。

---

## 6. 对抗测试用例清单（PROJECT-BRIEF 第十六章全覆盖）

我已在真实语料中核验了关键引文的存在性（`data/processed/lunyu.json` + `debate_classics.json` + `lunyu_quotes.json` + `quote_cards.json` + `lunyu_zhuxi.json` 全文串查）：

| # | 输入 | 真实语料核验 | 期望输出 | 判定规则 |
|---|---|---|---|---|
| 1 | "己所不欲勿施于人是不是孟子说的？" | `己所不欲，勿施于人` **在语料中**；正确出处 = 论语（非孟子） | `quote_exists=true, source_correct=false, correct_source=《论语》`, `trust_state=citation_corrected` | 必须纠正出处，不得接受"孟子" |
| 2 | "上善若水是不是庄子？" | `上善若水` **在语料中**（道德经） | `source_correct=false, correct_source=《道德经》`, `citation_corrected` | 不得接受"庄子" |
| 3 | "孔子怎么看职场PUA？" | 无直接原典 | 需经 Modern Issue Ontology 映射到概念后检索；**不得编造**孔子论 PUA 的古文 | 输出不得含伪造古文；须给出映射后的真实原典或拒答 |
| 4 | "韩非子会建议我辞职吗？" | 无直接原典 | 从《韩非子》真实语料推理，或 `insufficient_evidence` | 不得伪造韩非子语录 |
| 5 | "老子说努力就一定成功吗？" | 无"努力必成功"原文 | 须**否证**或拒答，不得虚构 | 禁止把现代鸡汤归给老子 |
| 6 | "以德报怨出自孟子吗？" | `以德报怨` 在 `lunyu.json` 中**未命中**（我实测 NOT-FOUND；需 t2/QA 复核是否为版本差异） | 按语料真实情况：不存在则 `quote_exists=false` + `insufficient_evidence` | **不得**因"听起来像经典"而放行 |
| 7 | 输入假的古文（如"学而不厌，诲人不倦，仁者无敌于天下"拼凑句） | 不存在 | `quote_exists=false, verifiable=false` | 任一放行即 GATE-5 FAIL |
| 8 | 真实古文 + 错误出处 | 存在但出处错 | `quote_exists=true, source_correct=false` | 两个指标必须分离 |
| 9 | 同一句不同标点（如"己所不欲。勿施于人"） | 存在（标点变体） | 归一化后 `exact_match=true` | 标点折叠后应命中 |
| 10 | 繁体版本（如"己所不欲，勿施於人"） | 存在（繁体） | 繁简统一后命中 | 需有繁简归一化 |
| 11 | 部分引用（如"勿施于人"） | 存在（子串） | 命中但应标注为 partial；`exact_match=false` | 不得把部分引用当作完整原文 |
| 12 | 现代网络鸡汤冒充孔子（如"你要悄悄拔尖，然后惊艳所有人——孔子"） | 不存在 | `quote_exists=false, insufficient_evidence`，不得展示为"经典原文" | 任一放行即 FAIL |

**注**：第 6 项的 `以德报怨` 我的全文串查为 NOT-FOUND，但这依赖我所查文件集合，需 t2（古籍）与 t9（QA）独立复核后再定稿；本报告不把它当作既成事实。

---

## 7. 性能测试方案与实测基线

### 7.1 方案
- 查询集：固定 ≥ 30 条（覆盖 12 个现代场景），存于 `eval/retrieval_gold.jsonl` 的 `query` 字段，保证可复现。
- 重复：每条查询重复 ≥ 5 次，取全部样本（n ≥ 150）。
- 排除外部 LLM：只对本地检索函数计时（`retrieve` / `vector_search` / `retrieve_for_sage_chat` / `retrieve_for_debate_sage`），不调用 `llm_client`。
- 记录：P50、P95、max；同时记录 `collection.count()` 与 `embed_fn` 类型，确保在**真实索引**下测量。
- 预热：先跑一轮丢弃（首次调用含模型/集合初始化）。

### 7.2 实测基线（CWD=backend，venv，真实索引 143 条，n=60）
```
retrieve() [当前恒空路径]      P50=10.6ms  P95=14.5ms  max=16.7ms
vector_search()                P50= 4.9ms  P95= 7.0ms  max= 8.4ms
retrieve_for_sage_chat()       P50= 7.7ms  P95=10.0ms  max=12.1ms
retrieve_for_debate_sage()     P50= 7.6ms  P95= 9.9ms  max=10.6ms
```
**结论**：当前本地检索**远优于** P50<1s / P95<3s 目标（约 100 倍余量）。
**警告**：此基线是在 **143 条** 索引上取得的，且 `retrieve()` 因 §8 C1 缺陷**恒返回空**（空路径最快）。引入 BM25 + dense + rerank 后必须**重新测量**；在 PHASE 4 用真实规模语料重测前，不得宣称性能 Gate 通过。

---

## 8. 真实结论：可达性判断（不修改目标数字）

### 8.1 独立复现的 C1（关键缺陷，已三方互证）
我独立复现并**定位到机制**：
- `rag_service.py:893` 构造 `RAGReference(verse_no=...)`，而 `RAGReference.verse_no` 为 `int`。
- 真实语料中 `verse_no` 是**字符串**（如 `'1.16'`、`'16.4'`、`'mozi-feile-01'`）→ pydantic `int_parsing` 校验失败 → `hybrid_search()` 抛 `ValidationError`。
- `retrieve()`（`rag_service.py:906-912`）用 `except Exception` 吞掉异常并 `return []`。
- 实测：`retrieve()` **12/12 查询返回空**；`verse_no` 非整数 **143/143**。
- **与 t1、t3 及队长独立复现一致。** 请 t9 记为三方确认。

### 8.2 数据规模（决定 Gate 可达性的硬约束）
| 数据 | 实测规模 |
|---|---|
| `lunyu.json` | 20 章 / **107** 条 |
| `debate_classics.json` | 9 圣贤 / **21** 条（confucius 3、laozi 4、mozi 4、hanfeizi 4、其余各 1–2） |
| `backend/data/commentaries/lunyu_zhuxi.json` | **15** 条（仅朱熹一家） |
| 真实向量索引 | **143** 条（107 + 15 + 21） |
| `classics_catalog.json` | 123 本书 → **仅目录元数据，0 条正文**（无 `verses/chapters/passages/content` 字段） |
| 合计"原典正文" | **128** 条 |

**关键澄清**：`classics_catalog.json` 列出 123 本书（含孟子/庄子/墨子/韩非子/传习录/孙子兵法…）会让覆盖率检查**误判为"已覆盖 V1 书目"**。实测 `books with inline passage content = 0` —— 它只是**书目元数据**，不构成语料。PHASE 2 必须从零接入正文。

### 8.3 Gate 可达性

| Gate | 目标 | 当前可达性 | 依据 |
|---|---|---|---|
| GATE-4 Recall@5 | ≥ 90% | **不可达（且当前无法测量）** | `retrieve()` 恒空（C1）；语料 128 条原典、仅 1 部完整书（论语） |
| GATE-5 Quote Exactness | ≥ 99% | **当前不可达** | 无 QuoteVerifier 实现；`citation_validator` 仅做子串匹配（无繁简/标点归一化、无出处独立判定） |
| GATE-5 Source Attribution | ≥ 98% | **当前不可达** | 无独立"出处正确性"指标（现状只返回 verifiable 布尔） |
| GATE-5 伪造引文放行 | ≈ 0 | **当前极可能失败** | `_match_citation` 用子串双向包含（`citation_validator.py:83-91`），假古文可被"包含关系"误放行；无对抗测试 |
| GATE-6 School Leakage | < 1% | **当前不可达** | 非儒家各派仅 3–4 条语料，检索必然大量回退到"score=0.25 兜底"（`rag_service.py:495-496`），跨派风险高；无泄露测试 |
| GATE-8 Unsupported Refusal | ≥ 95% | **当前不可达** | 无 Trust State 实现（无 `insufficient_evidence` 状态） |
| GATE-8 Claim Evidence Coverage | ≥ 95% | **当前不可达** | 无 Claim-Evidence 绑定实现 |
| 性能 P50<1s / P95<3s | — | **可达（当前）** | 实测 P50≈5–11ms；但需在 RAG V2 后重测 |
| GATE-8 ≥200 Gold | 200 条 | **当前 0 条** | `eval/` 不存在 |

**结论：以当前数据规模，GATE-4/5/6 与 GATE-8 的多数指标明确不可达。** 必须先把语料从 128 条扩到 V1 书目规模（PHASE 2）、实现 Trust Layer（PHASE 5），才能进入指标验收。**不得修改目标数字、不得放宽公式、不得用 mock 或占位断言冒充通过。**

### 8.4 未验证 / 阻塞项（如实列出）
1. **后端测试环境不完整**：`requirements.txt` 与 `.venv` 漂移（缺 pyjwt），仓库无一条命令能开箱跑出完整后端基线。属环境阻塞，需人工补装。
2. **CI 覆盖率步骤会失败**：`ci.yml` 执行 `pip install pytest pytest-cov` 后 `--cov=app`，但本仓库未验证该步骤通过；且 CI 从不运行 `.cjs` 套件，故 CI 绿灯**不代表**前端回归通过。
3. **`以德报怨` 是否在语料中**：我的串查为 NOT-FOUND，待 t2/t9 复核。
4. **前端 Evidence Drawer 相关断言**：20 个占位测试无验证力，PHASE 7 前无法据其判断现状。
5. **真实 LLM 质量、真实人工标注、来源授权**：本次未验证（无密钥、无人工标注资源）；PHASE 8 前不得宣称人工 Gold 覆盖。

---

## 9. 交付与命令清单（可复现）

```bash
# 后端（降级模式，系统 Python，缺 chromadb → 2 skipped）
cd backend && python -m pytest tests -q

# 后端（推荐基线，venv + 临时 PyJWT + 隔离索引）
$env:PYTHONPATH="$env:TEMP\wudian_eval_pyjwt"
$env:CHROMA_PERSIST_DIR="./_eval_iso_chroma"
cd backend && .\.venv\Scripts\python.exe -m pytest tests -q
# → 1 failed, 84 passed, 17 subtests passed in 72.80s

# 前端（默认入口）
cd frontend && npx vitest run          # → 23 files / 41 tests passed

# 前端（被排除的 .cjs 套件，手工逐个运行）
cd frontend && foreach ($f in Get-ChildItem tests\*.test.cjs) { node $f.FullName }
# → PASS=18 FAIL=4

# 索引完整性核验
.\.venv\Scripts\python.exe -c "import chromadb;c=chromadb.PersistentClient(path=r'...\backend\chroma_db');print([(x.name,x.count()) for x in c.list_collections()])"
# → [('wudian_verses', 143)]
```

- 产出文件：`docs/kb-v1/audit/evaluation.md`（本文件）
- 未修改任何产品代码 / 测试 / 断言 / 数据；`git status` 仅新增 `docs/kb-v1/`（及运行测试产生的 `backend/wudian.db-shm/-wal`，为 SQLite 运行时副作用，未跟踪）。

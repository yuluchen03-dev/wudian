# 03 — 任务依赖图与 Gate 定义（PHASE 1–10）

> 本文件是 PHASE 0 的第 4 份文档（原 t8 拆分任务）。**唯一写入文件**为 `docs/kb-v1/03-task-dag.md`。
> 严格只读：未修改 `backend/`、`frontend/`、`data/`、`PROJECT-BRIEF.md`；未 commit / push / deploy。
>
> 依据（全部为已复核产物，本文以它们为准，不引用分享会话）：
> - `docs/kb-v1/PROJECT-BRIEF.md`（第二十章 Phase/Gate、第二十一章工作协议、第二十二章 Git 规则、第十七章指标）
> - `docs/kb-v1/00-current-state.md`（t10，45,451 B）
> - `docs/kb-v1/01-gap-analysis.md`（t11，48,951 B）
> - `docs/kb-v1/02-architecture.md`（t12，42,231 B）
> - `docs/kb-v1/audit/evaluation.md`（t7，本文件作者）
>
> 本文**不创建任何代码文件**。所有路径均为提案，已实测确认不存在（见 §9 核对记录）。

---

## 0. 阅读约定

| 符号 | 含义 |
|---|---|
| `P<phase>-<n>` | 任务 ID |
| `E-<n>` | Eval 数据集工作流任务（跨 Phase 交付） |
| inScope | 该任务**唯一允许写入**的 workspace 相对 POSIX 路径；越界即视为流程违规 |
| verify | 该任务必须实际执行并贴出原始输出的命令 |
| acceptance | 可自动化判定或可被 QA 独立复核的验收判据 |
| **质量类任务** | kind ∈ {implementation, repair}，必须同时具备 objective / acceptance / inScope / verify |

**角色代码**：LA=lead-architect，PR=product-research，CK=classical-knowledge，RG=rag-expert，
TV=trust-verification，BE=backend，FE=frontend，EV=evaluation，QA=qa-reviewer。

**全局纪律（对每个任务生效）**
1. PHASE 0 之外的一切写入都必须限定在任务 inScope 内；多任务共享同一文件时必须**串行**（本文已标注）。
2. 任何任务不得删除测试、降低断言、隐藏失败、大规模推翻既有架构（PROJECT-BRIEF 禁止项）。
3. 禁止 AI 生成古籍当权威原典、禁止编造 source、禁止 mock 冒充真实 RAG、禁止未达标宣称完成。
4. 每个通过的 Phase 独立本地 commit，仅含该 Phase 明确文件；不推送、不部署、不执行生产迁移（第二十二章）。

---

## 1. 前置阻断层：PHASE 0-R（Blocker 修复，**必须排在 PHASE 1 之前**）

> 依据 `01-gap-analysis.md` §2 G-A/G-B/G-C（3 个 blocker）与 §4 阻断关系。
> **不修则 PHASE 4 的任何指标测量都在测"异常吞没"或"兜底假证据"，GATE-4/5/6 结构性不可达。**

### ⚠️ 开工前必须解除的决策阻塞（来自 `02-architecture.md` §12，**不自行决定**）

| ID | 阻塞项 | 影响 | 需要谁决定 |
|---|---|---|---|
| **Q1** | `verse_no` 修复方向：(a) `schemas/ai.py:17` 改 `Optional[str]`（最小改动，保留 `'1.1'` 语义）／(b) 写入侧改整数（**需重建索引**，丢失章.节语义）／(c) 拆 `chapter_no`+`section_no` | 决定 P0R-01 实现方式 | **用户/队长**（最终决策仍是用户的，因涉及公共 API schema 类型变更）。前置核查**已完成**（队长复核）：前端**无**整数依赖——`frontend/lib/types.ts:356` 声明为 `verse_no?: number`（可选）、`roundtableFlow.ts:180` 真实归一化器对每条 citation 都设 `verse_no: undefined`、`sage-chat/page.tsx:130` 仅用作 React list key 兜底；全前端对 `verse_no` 的算术/排序/比较用法**零命中**。故 **(a) 方案可行且无需重建索引** |
| **Q2** | V1 语料是否收窄（**12 部中 4 部有数据、8 部零语料**——注：`00`/`01` 早期写作"3 部/9 部"，t9 复核为 4/8，已由 t14/t15 修正） | 决定 PHASE 2 范围与 GATE-2/4 可达性 | **用户** |
| **Q3** | 底本授权（当前零 `source_provider/url/edition/license`，`data/raw` 为空） | 决定 PHASE 2 能否满足 GATE-2；无授权不得标 A/B | **用户** |
| **Q4** | 是否接入外部 embedding（无密钥只能 hash 非语义） | 决定 GATE-4 能否达 90% | **用户** |
| **Q5** | LLM 凭证（`.env` 有 `LLM_PROVIDER=agnes` 但无 API_KEY） | 决定 PHASE 6/8 端到端验证 | **用户** |
| **Q6** | PHASE 0 期间 `docs/kb-v1/audit/_rag_probe_enviro.py` 曾以只读查询打开真实索引，是否接受该披露 | 是否需要在计划中追加额外防护 | **队长/qa-reviewer** — **已闭合**：qa-reviewer 在 t9 中判定"索引内容完整、143 条不变、可接受"；队长亦复核 `collection wudian_verses count = 143`、`scope {sage_chat:122, debate_classic:21}` 未变。结论：**披露可接受，无需追加措施**；但由此暴露的破坏性测试风险（见 P0R-00 安全硬约束与 §11）必须按 F-01/F-02 处理 |

**Q1 未决则 P0R-01 不得开工**；Q2/Q3 未决则 PHASE 2 不得宣称完成；Q4 未决则 GATE-4 只能标注 `degraded=true`。
**Q6 已闭合**（qa-reviewer 判定可接受，队长复核一致）。

### ⚠️ 本 Phase 的第一步是 P0R-00（环境引导），不是 P0R-01

> 原因（t9 独立审查 F-01/F-02，队长双重复核）：计划中所有后端 verify 都写 `.venv/Scripts/python.exe -m pytest`，
> 但 `backend/.venv` **缺 `pyjwt`**（而 `requirements.txt:18` 已声明 `pyjwt>=2.8.0`），
> `conftest.py:40` 导入 `app.main` 即 `ModuleNotFoundError: No module named 'jwt'`，
> **collect 阶段 exit 4、0 个测试执行**。这些 verify 在补齐依赖前**结构性无法 PASS**。
>
> **实测陷阱（必须记录，防止误判）**：把最简 `def test_ok(): assert True` 放在 `backend/tests/` **之内**运行
> 同样 collect 失败（exit 4，因为加载 `conftest.py`）；放在 `backend/tests/` **之外**却 PASS（exit 0，不加载 conftest）。
> **因此任何环境探测必须位于 `backend/tests/` 之下，否则会得出"环境可用"的错误结论。**

### P0R-00【repair · blocker】环境引导：补齐 `.venv` 使后端测试可 collect
- **负责**：BE ｜ **依赖**：无（**PHASE 0-R 的第一步**）｜ **Gate 归属**：GATE-1 / GATE-9 前置
- **objective**：把 `backend/.venv` 补齐到能够 collect 并运行后端测试套件——安装 `requirements.txt` 已声明但缺失的 `pyjwt`（>=2.8.0）。当前两套解释器各缺一半：`.venv` 3.12.10 有 `chromadb 1.5.9` 但缺 `pyjwt`；系统 Python 3.11.9 有 `jwt 2.15.0` 但无 `chromadb`，**故不存在能跑完整后端套件的单一解释器**。本任务以 `.venv` 为唯一受支持解释器，把它补齐为完整环境。
- **inScope**：`backend/.venv/**`（仅依赖安装）、`backend/requirements-dev.txt`（如需记录测试依赖）、`docs/kb-v1/gates/ENV-BOOTSTRAP.md`（新增，记录环境状态与命令）
- **产出物**：可 collect 的 `.venv`；环境状态记录
- **安全硬约束（必须遵守，违反将破坏生产数据）**：
  1. **补齐 `pyjwt` 后，`backend/tests/test_debate_classic_rag.py:20/51` 的 `build_index(force=True)` 将变得可 collect**，它会经 `rag_service.py:638-639` → `_clear_collection()`（`:607-617`）**删除真实 `wudian_verses` 的全部 143 条**。因此**在运行任何后端测试之前必须设置 `CHROMA_PERSIST_DIR=./_regression_iso_chroma`（相对路径）**或等价隔离；**绝对路径不可用**，会使 `test_hackathon_readiness.py:15-24` 失败。此要求与 **§11 PHASE 9 的隔离要求一致**（交叉引用，勿重复发明）。
  2. **必须串行**：`conftest.py:14-19/26` 固定共享 `backend/test_wudian.db`，并发 pytest 会产生**伪失败**（实测 4 组不同失败集）。运行前先确认无其他 backend pytest 进程。
  3. **不得**为让测试变绿而删除/跳过测试或降低断言。
- **verify**：
  ```powershell
  # 1) 补齐依赖（仅 .venv；不改动系统 Python）
  cd backend && .venv\Scripts\python.exe -m pip install -r requirements.txt
  .venv\Scripts\python.exe -c "import jwt, chromadb; print('jwt ok, chromadb ok')"

  # 2) 证明 collect 已可用（探测必须位于 backend/tests/ 之下，否则会误判）
  cd backend && .venv\Scripts\python.exe -m pytest tests --collect-only -q

  # 3) 隔离索引后跑一次套件（串行；先确认无并发进程）
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'pytest' } | Select-Object ProcessId, CommandLine
  cd backend; $env:CHROMA_PERSIST_DIR="./_regression_iso_chroma"
  .venv\Scripts\python.exe -m pytest tests -q

  # 4) 复核真实索引未被触碰
  .venv\Scripts\python.exe -c "import chromadb;c=chromadb.PersistentClient(path=r'D:\systemDir\Desktop\悟典\backend\chroma_db');print([(x.name,x.count()) for x in c.list_collections()])"
  # 期望：[('wudian_verses', 143)]

  # 5) 清理
  Remove-Item -Recurse -Force _regression_iso_chroma
  ```
- **acceptance**：① `import jwt` 与 `import chromadb` 在 `.venv` 中**同时成功**；② `pytest tests --collect-only -q` **exit 0 且收集到 > 0 个测试**（修复前 exit 4）；③ 第 3 步输出被**如实记录**（含既有失败 `test_default_provider_is_openai`，该失败源于本机 `.env` 的 `LLM_PROVIDER=agnes`，**不得通过改断言消除**）；④ 第 4 步真实索引仍为 **143**；⑤ 环境状态写入 `ENV-BOOTSTRAP.md`，含两个解释器的能力差异说明。
- **失败回退**：若 `pip install -r requirements.txt` 在 Windows 上因 `chromadb` 编译失败，则只安装缺失的 `pyjwt`（`pip install "pyjwt>=2.8.0"`）并如实记录其余依赖状态；不得因此宣称环境完整。
- **解除的阻塞**：本任务完成后，F-01 所述的"所有后端 verify 结构性无法 PASS"即被解除；**GATE-1「schema test 全 PASS」在计划层面重新变为可达**。

### P0R-01【repair · blocker】修复 C1：`RAGReference.verse_no` 类型冲突
- **负责**：BE ｜ **依赖**：Q1 决策 ｜ **Gate 归属**：GATE-4 前置
- **objective**：消除 `schemas/ai.py:17 verse_no: Optional[int]` 与索引实存字符串（`rag_service.py:325/690/721` 写入 `'1.1'` 类值，实测 **143/143 非整数**）的冲突，使 `hybrid_search`（`rag_service.py:893`）不再抛 pydantic `ValidationError` 被 `:910-912` 吞掉。
- **inScope**：`backend/app/schemas/ai.py`、`backend/app/services/rag_service.py`、`backend/tests/test_rag_reference_type.py`（新增）
- **产出物**：类型一致的 `RAGReference`；回归测试
- **verify**：
  ```
  cd backend && .venv/Scripts/python.exe -m pytest tests/test_rag_reference_type.py -q
  cd backend && .venv/Scripts/python.exe -c "import asyncio,sys;sys.path.insert(0,'.');from app.services.rag_service import get_rag_service;r=asyncio.run(get_rag_service().retrieve('己所不欲，勿施于人',top_k=5));print('N=',len(r))"
  ```
- **acceptance**：① 上述探针 `N >= 1`（修复前恒为 `N=0`）；② 全库无 `ValidationError` 逃逸；③ 143 条全部可构造 `RAGReference`；④ `git grep -n "Optional\[int\]" app/schemas/ai.py` 结果与 Q1 决策一致。
- **失败回退**：若 (b) 方案需重建索引且失败，回退 (a) 方案并记录；不得为让测试通过而放宽类型为 `Any`。

### P0R-02【repair · blocker】修复 C3：删除 `score=0.25` 兜底
- **负责**：BE ｜ **依赖**：P0R-01（同文件串行）｜ **Gate 归属**：GATE-5 前置
- **objective**：删除 `rag_service.py:493-498` 的 `if score == 0: score = 0.25` + 无条件 `append`，使「检索不到」成为可达状态，恢复核心承诺「找不到就不硬编」，并让 `insufficient_evidence` 路径可达。
- **inScope**：`backend/app/services/rag_service.py`、`backend/tests/test_retrieval_emptiness.py`（新增）
- **verify**：
  ```
  cd backend && .venv/Scripts/python.exe -m pytest tests/test_retrieval_emptiness.py -q
  cd backend && .venv/Scripts/python.exe -c "import asyncio,sys;sys.path.insert(0,'.');from app.services.rag_service import get_rag_service;print(len(asyncio.run(get_rag_service().retrieve_for_debate_sage('mozi','asdfghjkl',top_k=3))['verses']))"
  ```
- **acceptance**：① 对语料外查询返回 **0** 条（修复前实测返回 3 条 `sim=0.0`）；② 语料内查询仍返回 ≥1 条（不得过度删除导致召回归零）；③ `is_low_confidence` 对空结果返回 `True`。
- **失败回退**：若删除后召回显著下降，改用显式 `relevance < threshold` 过滤而非恢复常数兜底。

### P0R-03【repair · blocker】修复 B2：`CHROMA_PERSIST_DIR` 相对/绝对不一致与健康检查误报
- **负责**：BE ｜ **依赖**：P0R-02（同文件串行）｜ **Gate 归属**：GATE-1 前置
- **objective**：消除 `config.py:89` 相对值 `./chroma_db` 与 `:189-190` `resolved_chroma_persist_dir` 绝对值的分歧（`rag_service.py:237` 用相对、`main.py:39` 用绝对），并让 `is_available`/`rag_available` 在 `count == 0` 时不再误报可用。
- **inScope**：`backend/app/core/config.py`、`backend/app/services/rag_service.py`、`backend/app/main.py`、`backend/tests/test_rag_persist_path.py`（新增）
- **verify**：
  ```
  cd backend && .venv/Scripts/python.exe -m pytest tests/test_rag_persist_path.py -q
  # 以仓库根为 CWD 启动，断言不新建空索引
  cd D:\systemDir\Desktop\悟典 && backend\.venv\Scripts\python.exe -c "import sys;sys.path.insert(0,'backend');from app.services.rag_service import get_rag_service;r=get_rag_service();print('count',r.collection.count() if r.collection else None,'avail',r.is_available)"
  ```
- **acceptance**：① 以仓库根为 CWD 时 `count == 143`（修复前会静默新建空索引）；② `count == 0` 时 `rag_available == false`；③ `main.py:39` 与 `rag_service.py:237` 解析到**同一绝对路径**（测试断言相等）。
- **失败回退**：若统一为绝对路径破坏既有启动脚本，改为在 `config.py` 统一 `resolved_*` 并在两处引用同一属性。

### PHASE 0-R Gate（非独立编号，并入 GATE-1 前置）
`P0R-00/01/02/03` 全部 acceptance 通过 + QA 独立复现各探针 → 方可进入 PHASE 1。
**任一未过不得进入 PHASE 1**（PROJECT-BRIEF 第二十一章：任何阶段失败不得进入下一阶段）。

**verify 可执行性前置（F-01 修正）**：`P0R-01/02/03` 及 PHASE 1–10 全部后端 verify 均以
`.venv/Scripts/python.exe -m pytest` 为解释器，**其可执行性以 P0R-00 完成为前提**。
在 P0R-00 完成前，这些 verify 会以 `ModuleNotFoundError: No module named 'jwt'` 在 **collect 阶段 exit 4、0 测试执行**，
**不构成有效验证**，任何据此判定的 Gate 一律不得判 PASS。P0R-00 完成后该前置解除。

---

## 2. Eval 数据集工作流（跨 Phase 交付，**Gate 的前置条件**）

> 依据 `audit/evaluation.md` §4（七类 Schema）、§5（指标公式）、§6（对抗用例）。
> **关键原则：Gate 需要数据集才具备判定依据；无数据集的 Gate 一律不得判定 PASS。**
> **provenance 纪律**：每条记录必须标 `human` / `derived` / `synthetic`。
> **禁止**把 `derived`/`synthetic` 标为 `human`；人工确认条数必须单独统计并在报告中披露。

| ID | 任务 | 负责 | 依赖 | 交付物（inScope） | 服务的 Gate |
|---|---|---|---|---|---|
| **E-01** | `retrieval_gold` 数据集 + `eval/scripts/run_retrieval_eval.py` | EV | P1-01（需 passage_id 稳定） | `eval/retrieval_gold.jsonl`、`eval/scripts/run_retrieval_eval.py` | **GATE-4 前置** |
| **E-02** | `adversarial_quotes` 数据集（第十六章 12 类全覆盖 + **§7 "P5-05 必含对抗用例" A1/A2/B1/B2/C1/C2/C3/D1**） | EV | P1-01, P2-02 | `eval/adversarial_quotes.jsonl` | **GATE-5 前置（硬性）** |
| **E-03** | `quote_verification` 数据集 | EV | E-02 | `eval/quote_verification.jsonl` | GATE-5 |
| **E-04** | `source_attribution` 数据集 | EV | E-02 | `eval/source_attribution.jsonl` | GATE-5 |
| **E-05** | `modern_to_classic` 数据集 | EV | P3-01 | `eval/modern_to_classic.jsonl` | GATE-3/4 |
| **E-06** | `school_consistency` 数据集 | EV | P1-01 | `eval/school_consistency.jsonl` | **GATE-6 前置** |
| **E-07** | `unsupported_questions` 数据集 | EV | P5-04 | `eval/unsupported_questions.jsonl` | GATE-8 |
| **E-08** | `eval/scripts/schema.py` + `validate_gold.py`（唯一入库门禁） | EV | — | `eval/scripts/schema.py`、`eval/scripts/validate_gold.py` | 全部 Eval |
| **E-09** | `eval/scripts/report.py`（`eval-report.json` / `.md`） | EV | — | `eval/scripts/report.py` | GATE-8 |

**E-08 为强制门禁**：任何 Gold 记录必须通过 `validate_gold.py` 才可入库；该校验必须断言
`expected_passage_ids` **真实存在于语料**（禁止编造 id）、`provenance` 合法、无重复 `id`。

**E-02 硬性要求（PROJECT-BRIEF 第十六章全覆盖）**：`己所不欲勿施于人是否孟子`、`上善若水是否庄子`、
`孔子怎么看职场PUA`、`韩非子会建议我辞职吗`、`老子说努力就一定成功吗`、`以德报怨出自孟子吗`、
假古文、真古文+错误出处、同句不同标点、繁体、部分引用、网络鸡汤冒充孔子。
**E-02 未建成前 GATE-5 不得判定**（无判定依据）。

---

## 3. PHASE 1 — Data Architecture

**Gate**：GATE-1 ｜ **前置**：PHASE 0-R 全过
**并行点**：P1-01 完成后 P1-02 / P1-03 / P1-04 / P1-05 可并行（P1-05 独立无依赖）

| ID | 任务 | 负责 | 依赖 | inScope（唯一写入） | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P1-01** | Passage / Commentary / SourceRecord / EvidencePack / QuoteVerification 模型 | CK | P0R-03 | `backend/app/schemas/knowledge.py` | Pydantic 模型 | `cd backend && .venv/Scripts/python.exe -m pytest tests/test_knowledge_schema.py -q` | 覆盖第六章 29 字段；`text_type ∈ {original,commentary,translation,modern_explanation}`；`verification_level ∈ {A,B,C,D}` |
| **P1-02** | Source Registry（**拒绝无来源条目入库**） | CK | P1-01 | `backend/app/services/source_registry.py`、`data/sources/source_registry.json` | 注册表 + 校验器 | `pytest tests/test_source_registry.py -q` | 无 `source_provider/url/edition` 的条目**被拒绝**；`license: unknown` 时 `verification_level != A` |
| **P1-03** | Ingestion pipeline（校验式导入 + 拒绝清单） | BE | P1-01, P1-02 | `backend/app/services/ingestion.py` | 导入器 | `pytest tests/test_ingestion.py -q` | fixture 可 ingest；非法条目进拒绝清单且**不静默丢弃** |
| **P1-04** | ORM 模型 + Alembic 迁移（**原典/注疏分表**） | BE | P1-01 | `backend/app/models/knowledge.py`、`backend/migrations/versions/<rev>_knowledge_passage.py` | `knowledge_passage` / `knowledge_commentary` | `cd backend && alembic upgrade head && .venv/Scripts/python.exe -m pytest tests/test_knowledge_schema.py -q` | 两表分离；L2 以 FK 引用 L1，**不内嵌原文副本** |
| **P1-05** | 测试隔离：`CHROMA_PERSIST_DIR` + 每会话唯一 DB | BE | — | `backend/tests/conftest.py` | 隔离 fixture | `pytest tests -q`（串行） | 测试**不触碰** `backend/chroma_db`；每次会话 DB 路径唯一（消除 F-6 并发伪失败） |
| **P1-06** | Schema / ingestion / registry 单元测试 | BE | P1-02, P1-03, P1-04 | `backend/tests/test_knowledge_schema.py`、`backend/tests/test_ingestion.py`、`backend/tests/test_source_registry.py` | 测试套件 | `cd backend && .venv/Scripts/python.exe -m pytest tests/test_knowledge_schema.py tests/test_ingestion.py tests/test_source_registry.py -q` | **全 PASS**；断言强度须覆盖字段缺失/非法枚举/无来源拒绝，不得仅断言对象可构造 |
| **P1-07** | **GATE-1 独立验证** | QA | P1-06 | `docs/kb-v1/gates/GATE-1.md` | Gate 报告 | 独立复跑 P1-06 命令 + 检查 fixture 实际入库 | 见 §4 GATE-1；QA 不得参与 P1-01…P1-06 实现 |

**串行约束**：P1-01 是 P1-02/03/04 的共同前置（schema 未定则其余无法写）。
**Phase commit**：`feat(kb): add canonical knowledge schema`（仅含 PHASE 1 文件）。

---

## 4. PHASE 2 — Core Corpus

**Gate**：GATE-2 ｜ **前置**：PHASE 1 全过 + **Q2/Q3 决策**
**阻塞提示**：Q3（授权）未决时，P2-01 无法诚实完成 → GATE-2 不得判定 PASS。

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P2-01** | 来源注册表补全（**真实来源与授权**） | CK | P1-02, Q3 | `data/sources/source_registry.json` | 来源记录 | `pytest tests/test_source_registry.py -q` | 每条有 `provider/url/edition/license`；**无法核验的一律标 `unknown`，禁止编造** |
| **P2-02** | 论语 L1 迁移（107 条 → `knowledge_passage`） | CK | P2-01, P0R-00 | `data/processed/lunyu_passages.json`、`backend/app/services/ingestion.py`（如需适配） | L1 数据 | `python -c` 统计 + `pytest tests/test_ingestion.py -q` | ① 107 条全部有 `source_id`、`text_type='original'`、**不含 LLM 生成文本**；② **去重不得只做 exact-equality**——必须显式处理已枚举的**恰好 1 对部分包含**：`debate_classics[confucius]`「士不可以不弘毅，任重而道远。」与 `lunyu.json` 8.7「曾子曰：士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？死而后已，不亦远乎？」必须被识别为**同一 passage 的全句/摘句关系**，**或**在 L1 中显式标注为独立 passage 并**记录理由**；验收时**必须能列出该对的处置结果**；③ **不得**存在归一化后完全相等的重复（实测 exact-duplicate = **0** 条） |
| **P2-03** | 注疏 L2 迁移（15 条，去内嵌原文副本） | CK | P2-01 | `data/processed/lunyu_commentaries.json` | L2 数据 | 同上 | 15 条以 FK 引用 L1；**删除重复 `original` 副本**（现 13/15 重复） |
| **P2-04** | 其余 V1 书目接入（道德经/孟子/庄子/墨子/韩非子/…） | CK | P2-01, Q2, Q3 | `data/processed/<book>_passages.json` | 各书 L1 | 逐书 `validate_gold.py` 式校验 | 每部书**均有真实来源**；无来源的书目**如实记为缺口**，不得填充占位文本 |
| **P2-05** | 入库完整性审计（所有 passage 必须有 source；原典非 LLM 生成） | EV | P2-02, P2-03, P2-04 | `eval/scripts/audit_corpus_provenance.py` | 审计脚本 + 输出 | `python eval/scripts/audit_corpus_provenance.py` | 输出 `passages_without_source = 0`；并如实报告"是否 LLM 生成"**无法证实也无法证伪**（无生成日志、无 raw 底本） |
| **P2-06** | **GATE-2 独立验证** | QA | P2-05 | `docs/kb-v1/gates/GATE-2.md` | Gate 报告 | 独立复跑 P2-05 + 抽查 10 条来源 | 见 §4 GATE-2 |

**诚实边界（必须写入 GATE-2 报告）**：「原典不得来自 LLM 生成」当前**无法证实也无法证伪**——
`data/raw` 为空、无生成日志、`ctext.org`/维基文库在本环境访问被拒（non-public IP）。
因此 GATE-2 只能判定**来源字段完整性**，对"非 LLM 生成"必须标 **未验证**，不得据此宣称满足。

**⚠️ 下游影响（摘句/全句重复 passage_id，与 `02-architecture.md` §9 契约冻结交叉引用）**：
若 P2-02 把 `debate_classics[confucius]`「士不可以不弘毅，任重而道远。」与 `lunyu.json` 8.7 的**全句**
均作为独立 L1 passage 入库，则**同一句会产生两个 `passage_id`**，导致：
1. Quote Verifier 的 `quote_exists` **候选集出现重复来源**（同一文本两个 id）；
2. `02-architecture.md` §9.4 的 **`candidates[]` 契约必须能表达「同一 passage 的全句与摘句」关系**
   （即需要显式的包含/被包含标注，而不是两条互不相干的候选）。

因此本任务必须在 L1 中显式记录该对关系（或合并为单条并保留摘句出处），
**P5-01（Quote Verifier）的 acceptance 与 §13 GATE-5 判定必须据此校验 `candidates[]` 不产生重复来源**。

---

## 5. PHASE 3 — Modern Issue Ontology

**Gate**：GATE-3 ｜ **前置**：PHASE 1

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P3-01** | `modern_issue_ontology.json`（第七章 21 类情境 + 概念映射） | CK | P1-01 | `data/processed/modern_issue_ontology.json` | 本体数据 | `pytest tests/test_issue_ontology.py -q` | 覆盖 21 类 scene；每类有 actors/conflict/emotion/choices/concepts |
| **P3-02** | `issue_structurer` + schema（**不直接丢给 embedding**） | BE | P3-01 | `backend/app/services/issue_structurer.py`、`backend/app/schemas/issue.py` | 结构化服务 | `pytest tests/test_issue_ontology.py -q` | 输入「同事抢了我的功劳…」输出 scene/actors/conflict/emotion/choices/concepts（对齐第七章示例） |
| **P3-03** | ≥50 个现代问题分类测试 | BE + EV | P3-02 | `backend/tests/test_issue_ontology.py`、`eval/modern_to_classic.jsonl` | 测试 + 数据集 | `pytest tests/test_issue_ontology.py -q` | **≥50 条分类用例全 PASS** |
| **P3-04** | **GATE-3 独立验证** | QA | P3-03, E-05 | `docs/kb-v1/gates/GATE-3.md` | Gate 报告 | 独立复跑 | 见 §4 GATE-3 |

---

## 6. PHASE 4 — RAG V2

**Gate**：GATE-4 ｜ **前置**：PHASE 0-R + PHASE 3 + **E-01**（`retrieval_gold`）
**并行点（本 Phase 最大并行度）**：P4-01…P4-09 均为**独立新文件**，可并行；
P4-10（改 `rag_service.py`）必须**在所有新模块就绪后串行**执行。

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P4-01** | Stage 1 Query Analyzer | RG | P3-02 | `backend/app/services/retrieval/query_analyzer.py` | 分析器 | `pytest tests/test_retrieval_pipeline.py -q` | 输出结构化 query（scene/concepts/时间约束），非原串直传 |
| **P4-02** | Stage 2 现代→古典概念扩展（保留 `SYNONYM_MAP` 作 fallback） | RG | P3-01 | `backend/app/services/retrieval/query_expander.py` | 扩展器 | 同上 | 现代词→概念映射命中率可测；fallback 路径有显式标记 |
| **P4-03** | Stage 3 真实 BM25 | RG | P1-01 | `backend/app/services/retrieval/bm25.py` | BM25 索引 | 同上 | 替代 `keyword_search` 的 `keywords[0]` 单键过滤；k1/b 参数显式 |
| **P4-04** | Stage 3 Dense 语义检索（hash 仅作**明确标记**的 fallback） | RG | P1-01 | `backend/app/services/retrieval/dense.py` | 向量检索 | 同上 | 无外部密钥时输出 `degraded=true` 并**显式标注**；不得把 hash 结果当语义结果 |
| **P4-05** | Stage 4 Metadata Filtering | RG | P1-01 | `backend/app/services/retrieval/filters.py` | 过滤器 | 同上 | 支持 school/book/text_type/person/concept 过滤 |
| **P4-06** | Stage 5 Reranker | RG | P4-03, P4-04 | `backend/app/services/retrieval/reranker.py` | 重排器 | 同上 | 有可复现的排序变化证据（rerank 前后对比） |
| **P4-07** | Stage 6 Diversification（禁止同章霸榜） | RG | P4-05 | `backend/app/services/retrieval/diversity.py` | 去重器 | 同上 | 断言 Top-5 **不全部**来自同一 passage/同一章 |
| **P4-08** | Stage 1–6 编排 pipeline | RG | P4-01…P4-07 | `backend/app/services/retrieval/pipeline.py`、`backend/app/services/retrieval/__init__.py` | 编排层 | 同上 | 端到端可调用；每 Stage 可单独关闭以做消融 |
| **P4-09** | Stage 7 Evidence Pack 组装 + 白名单 | RG | P4-08 | `backend/app/services/evidence_pack.py` | EvidencePack | 同上 | `evidence[]` 含 evidence_id/original/source/school/text_type/commentary/relevance/verification（对齐第九章） |
| **P4-10** | `rag_service` 接入 pipeline（**保留全部既有签名与返回类型**） | RG | P4-08, P4-09, P0R-01, P0R-02 | `backend/app/services/rag_service.py` | 接入改造 | `pytest tests -q`（串行） | `retrieve`/`retrieve_for_sage_chat`/`retrieve_for_debate_sage`/`hybrid_search` 签名不变；既有调用方零改动 |
| **P4-11** | 检索回归测试（**真实链路，禁用 FakeRag**） | RG + EV | P4-10 | `backend/tests/test_retrieval_pipeline.py` | 测试套件 | `pytest tests/test_retrieval_pipeline.py -q` | 无 `FakeRag`/`monkeypatch` 替代检索；断言 Recall 与排序 |
| **P4-12** | **GATE-4 独立验证**（跑 `retrieval_gold`，输出 Recall@1/3/5、MRR） | QA | P4-11, E-01 | `docs/kb-v1/gates/GATE-4.md` | Gate 报告 | `python eval/scripts/run_retrieval_eval.py --dataset eval/retrieval_gold.jsonl` | 见 §4 GATE-4 |

**性能重测（并入 P4-12）**：RAG V2 后必须**重新测量** P50/P95（当前基线仅 143 条且 `retrieve()` 恒空，见 `evaluation.md` §7）。
**Phase commit**：`feat(rag): add hybrid retrieval`。

---

## 7. PHASE 5 — Trust Layer

**Gate**：GATE-5 ｜ **前置**：PHASE 1 + **E-02（adversarial_quotes，硬性）** + **E-03/E-04**

> **GATE-5 前置条件（不可省略）**：**必须先建立 `eval/adversarial_quotes.jsonl`，否则该 Gate 无判定依据。**
> **契约硬性要求**：`quote_verifier` 必须把 `quote_exists` 与 `source_correct` 作为**两个独立字段**，
> **必须允许 `quote_exists=true` 且 `source_correct=false`**（即 `citation_corrected`）。
> 禁止把二者合并为单一布尔，禁止用 `verifiable` 一个字段同时表达两个语义。

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P5-01** | Quote Verifier（全库回查 + 逐字/归一化 + **独立**出处判定） | TV | E-02, E-03, E-04, P1-01 | `backend/app/services/quote_verifier.py` | 验证器 | `pytest tests/test_quote_verifier.py -q` | 输出含 `quote_exists` / `exact_match` / `normalized_match` / `source_correct` / `correct_source` / `similarity` / `match_type` / `candidates[]` / `trust_state`；**繁简与标点归一化可测** |
| **P5-02** | Citation Guard（Evidence Pack 白名单） | TV | P4-09, P5-01 | `backend/app/services/citation_guard.py` | 白名单校验 | `pytest tests/test_citation_guard.py -q` | Evidence Pack 外的 source 一律 `verifiable=false`；**不得放行** |
| **P5-03** | Claim → Evidence 绑定 | TV | P5-02 | `backend/app/services/claim_evidence.py` | 绑定器 | `pytest tests/test_claim_evidence.py -q` | 每个核心 claim 有 ≥1 条 `supported` evidence；无证据 claim 显式标 `unsupported` |
| **P5-04** | Trust State 四态（单一真值来源） | TV | P5-01 | `backend/app/services/trust_state.py` | 状态机 | `pytest tests/test_trust_state.py -q` | `verified` / `citation_corrected` / `quote_relaxed` / `insufficient_evidence` 四态与 `02-architecture.md` §9.2 冻结表一致 |
| **P5-05** | `citation_validator` 收紧（**保留 `validate()` 签名与 `SAGE_CLASSICS`**） | TV | P5-01, P0R-00 | `backend/app/services/citation_validator.py` | 收紧后的匹配 | `pytest tests -q`（串行） | ① 单向子串 + 长度阈值（消除 `:83/:90` 双向子串导致短片段通过）；② 补齐空出处分支（`:99-100` 现直接放行）；③ **必须通过以下显式对抗用例**（详见下方"P5-05 必含对抗用例"）；④ **公平性回归**：纯假古文、繁体、网络鸡汤必须**继续判 False**（t9 确认这三类当前被正确拒绝），不得因收紧而误伤 |
| **P5-06** | 移除硬编码 `verifiable=True` | BE | P5-05 | `backend/app/api/ai.py`、`backend/app/services/ai_service.py`、`backend/app/services/debate_engine.py` | 真实校验接入 | `git grep -n "verifiable=True" backend/app` + `pytest tests -q` | 实测 4 处无条件硬编码（`api/ai.py:146/159/208/265`）**全部移除**；`ai_service.py:424`、`debate_engine.py:105` 改为真实计算 |
| **P5-07** | `Citation.verifiable` 默认值改为**必填/False** | BE | P5-06 | `backend/app/schemas/ai.py`、`backend/app/schemas/debate.py` | schema 修正 | `pytest tests -q` | 消除「缺省即通过」（现 `ai.py:108`/`debate.py:100` 默认 `True`） |
| **P5-08** | `/api/knowledge/{verify-quote,search,evidence}` | BE | P5-01, P5-04 | `backend/app/api/knowledge.py` | 新路由 | `pytest tests/test_knowledge_api.py -q` | `verify-quote` 输入 `{quote, claimed_source}`；输出**分别**含 `quote_exists` 与 `source_correct`（对齐 `02-architecture.md` §9.4） |
| **P5-09** | `main.py` **仅追加** `knowledge.router` | BE | P5-08 | `backend/app/main.py` | 路由注册 | `curl -s localhost:8000/openapi.json \| python -c "import sys,json;print('/api/knowledge/verify-quote' in sys.stdin.read())"` | 既有 8 个 router 全部保留；新增仅 1 行 include |
| **P5-10** | 对抗套件（`test_quote_verifier` / `test_citation_guard` / `test_adversarial_quotes`） | TV + EV | P5-08, E-02 | `backend/tests/test_quote_verifier.py`、`backend/tests/test_citation_guard.py`、`backend/tests/test_adversarial_quotes.py` | 对抗测试 | `pytest tests/test_adversarial_quotes.py -q` | 第十六章 12 类全部覆盖；**任何明显伪造名言通过验证即 FAIL** |
| **P5-11** | **GATE-5 独立验证** | QA | P5-10 | `docs/kb-v1/gates/GATE-5.md` | Gate 报告 | 独立复跑对抗套件 + 手工注入假古文 | 见 §4 GATE-5 |

**串行约束**：`citation_validator.py` 被 P5-05 独占；`schemas/*.py` 被 P5-07 独占；`api/ai.py`+`ai_service.py`+`debate_engine.py` 被 P5-06 独占。

### P5-05 必含对抗用例（F-05 修正 · 作为 E-02 `adversarial_quotes` 的必含条目）

> 背景（t9 独立实测 + 队长独立复现，双方一致）：PROJECT-BRIEF 第十六章**第一例当前直接失败**——
> `citation_validator.validate("mencius", [{"出处":"《孟子·公孙丑上》","原文":"己所不欲，勿施于人。"}], refs)` →
> **`verifiable=True`、`status="all_verified"`**，且错误出处《孟子·公孙丑上》被**原样保留**。
> 根因：`SAGE_CLASSICS["mencius"]=["孟子"]` 使学派检查通过，而 `_match_citation` **只与 `rag_refs` 比子串、
> 从不校验"出处与文本是否一致"**。另外「君子」等 2 字片段亦被判 `True`。

| # | 用例 | 期望输出 | 判定规则 |
|---|---|---|---|
| **A1** | 真古文 + **同书错篇**：`己所不欲，勿施于人。` 声称出自《论语·学而》（正确为《论语·卫灵公》/颜渊） | `quote_exists=true` 且 `source_correct=false`，并给出 `correct_source` | **两个字段必须独立**；`trust_state=citation_corrected` |
| **A2** | 真古文 + **跨书错派**：`己所不欲，勿施于人。` 声称出自《孟子·公孙丑上》 | 同 A1（`quote_exists=true`、`source_correct=false`、`correct_source=《论语·卫灵公》`） | **不得**因 `SAGE_CLASSICS` 含"孟子"而放行；当前此例 **FAIL** |
| **B1** | **2 字片段**：`君子` 声称出自《论语·学而》 | `verifiable=false` | 必须设**长度下限**；当前此例 **FAIL** |
| **B2** | 3 字片段（如 `不亦说乎` 截断） | `verifiable=false` 或标为 partial 且不计入 verified | 短片段不得判 verified |
| **C1** | **纯假古文**（拼凑句） | `quote_exists=false`、`verifiable=false` | 当前**已被正确拒绝**，必须保持 |
| **C2** | **繁体**版本（如 `己所不欲，勿施於人`） | 归一化后应命中（`normalized_match=true`） | 当前行为需按 t9 记录核实；不得因收紧而误伤 |
| **C3** | **网络鸡汤冒充孔子** | `quote_exists=false`、`insufficient_evidence` | 当前**已被正确拒绝**，必须保持 |
| **D1** | **`candidates[]` 不产生重复来源**：查询 P2-02 枚举的摘句「士不可以不弘毅，任重而道远。」 | `candidates[]` 必须表达全句/摘句关系，**不得**出现同一文本的两个互不相干 `passage_id` | 与 §4 P2-02 下游影响及 `02-architecture.md` §9.4 契约一致 |

**公平性要求（不得"为了通过而过度收紧"）**：C1/C3 当前**已正确拒绝**，收紧后必须继续拒绝；
C2 若当前命中则不得因长度阈值而破坏。**任何用例的期望值不得被下调以适配现状。**

**Phase commit**：`feat(trust): add quote verifier`。


---

## 8. PHASE 6 — Debate Integration

**Gate**：GATE-6 ｜ **前置**：PHASE 4 + PHASE 5 + **E-06（school_consistency）**

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P6-01** | 各派 Evidence Pack 隔离（sage_key + school 过滤） | RG | P4-10, P4-05 | `backend/app/services/rag_service.py`、`backend/app/services/evidence_pack.py` | 隔离检索 | `pytest tests/test_school_isolation.py -q` | 修复 G-D（sage-chat 无 scope 过滤，实测孔子路径返回《道德经·第八章》0.68 排第一）；各派仅返回本派 source |
| **P6-02** | `debate_engine` 从 Evidence Pack 发言 | TV | P6-01, P5-02 | `backend/app/services/debate_engine.py` | 发言绑定 | `pytest tests/test_debate_sentence_evidence.py -q` | 删除死代码 `_validate_citations`（`:86-111` 无调用点）；`_bind_sentence_evidence` 接入 Evidence Pack；**保留 `SentenceEvidence` 字段**；修复 `:149` 对无关句恒判 `True` |
| **P6-03** | 跨派泄露测量（跑 E-06） | EV | P6-02, E-06 | `eval/scripts/run_school_eval.py` | 泄露率 | `python eval/scripts/run_school_eval.py --dataset eval/school_consistency.jsonl` | 输出 `School Leakage = 越界引用数 / 总引用数` |
| **P6-04** | **GATE-6 独立验证** | QA | P6-03 | `docs/kb-v1/gates/GATE-6.md` | Gate 报告 | 独立复跑 P6-03 + 手工抽查 | 见 §4 GATE-6 |

**Phase commit**：`feat(debate): bind speeches to evidence packs`。

---

## 9. PHASE 7 — Frontend

**Gate**：GATE-7 ｜ **前置（硬性）**：**PHASE 1 + PHASE 5 全部完成**（`02-architecture.md` §10.1）
**另有两个独立前置任务必须排在 PHASE 7 之前**：**P7-00（前端回归门禁修复）**、**P7-09（前端伪造数据修复）**

> **为什么 PHASE 7 不得早于 PHASE 1 与 PHASE 5**：Evidence Drawer 要显示的
> `source_provider`/`text_type`/`commentator`/`verification_level`/`proofread_status` 由 PHASE 1 提供，
> `TrustState` 四态由 PHASE 5 提供。在二者完成前开发 Drawer 只能渲染空字段或**继续伪造**。

### P7-00【repair】前端回归门禁修复（**独立任务，必须排在 PHASE 7 之前**）
- **负责**：FE ｜ **依赖**：无（可早于 PHASE 1 启动）｜ **Gate 归属**：GATE-9 前置
- **objective**：恢复前端真实回归保护。现状：`vitest.config.ts:16` exclude 22 个 `.cjs`；
  HEAD `64c8618` 把 `package.json` 的 `test` 从 `.cjs` 链换成 `vitest run`；20/41 为占位断言；
  `tsc --noEmit` **26 errors（全部在 `tests/curtainPhysics.test.tsx`，已实测）**；**无 eslint 配置**（`npx eslint` 报 "couldn't find a configuration file"，CI lint 必然失败）。
- **inScope**：`frontend/package.json`、`frontend/vitest.config.ts`、`.eslintrc.json`（新增）、`frontend/tests/*.test.tsx`、`frontend/tests/*.test.cjs`、`frontend/tests/curtainPhysics.test.tsx`
- **产出物**：可执行的门禁链
- **verify**：
  ```
  cd frontend && npx vitest run
  cd frontend && foreach ($f in Get-ChildItem tests\*.test.cjs) { node $f.FullName }
  cd frontend && npx tsc --noEmit
  cd frontend && npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0
  ```
- **acceptance**：① 22 个 `.cjs` **全部被默认入口执行**且全 PASS（现 4 个失败）；② `tsc --noEmit` **exit 0**（现 26 errors）；③ `eslint` 能运行且 **exit 0**；④ 20 个占位断言替换为真实断言或**明确标注为占位并停止计入覆盖**。
- **失败回退**：若 `.cjs` 与 vitest 无法共存，保留 `.cjs` 为独立 `test:legacy` 并**写入 CI**，禁止直接删除。

### P7-01…P7-08 前端 Evidence Drawer

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P7-01** | 类型扩展（`TrustState`/`QualityGrade`/`TextType`/`EvidenceProvenance`） | FE | P1-01, P5-04 | `frontend/lib/thoughtCourtTypes.ts` | 类型定义 | `npx tsc --noEmit` | 与 `02-architecture.md` §9.1/9.2/9.3 冻结字段**逐一对应**，不得另造同义字段 |
| **P7-02** | 修复 `normalizeCitations` | FE | P7-01 | `frontend/lib/roundtableFlow.ts` | 修复 | `node tests/roundtableFlow.test.cjs` | 修复 `chapter: source` 错误、硬编码 `type:"verse"`（`:182`）、**伪造 similarity**；缺失字段透传 `undefined` |
| **P7-03** | 修复 `normalizeEvidence` | FE | P7-01 | `frontend/lib/thoughtCourtSession.ts` | 修复 | `node tests/thoughtCourtSession.test.cjs` | 移除写死文案与「默认已核验」 |
| **P7-04** | `CitationStatus` 三态 → 四态 | FE | P7-01 | `frontend/lib/thoughtCourtState.ts` | 状态对齐 | `node tests/thoughtCourtState.test.cjs` | 四态与后端 `TrustState` 一致 |
| **P7-05** | Evidence Drawer 渲染 + **Desktop/Mobile 双布局** | FE | P7-02, P7-03, P7-04 | `frontend/components/thought-court/EvidenceDock.tsx`、`frontend/components/thought-court/ThoughtCourt.module.css` | Drawer | `npx vitest run` + 手工双端核对 | 显示 原文/出处/书名/篇章/文本类型/注疏者/数据来源/校验状态/可信等级（PROJECT-BRIEF 第七章角色要求） |
| **P7-06** | 共享徽标组件 | FE | P7-01 | `frontend/components/ui/EvidenceBadge.tsx` | 组件 | `npx tsc --noEmit` | **D 与 A 不得显示成同一等级**（第十四章） |
| **P7-07** | 移除伪造「相关度」，改显 Trust State | FE | P7-01 | `frontend/components/roundtable/CitationPanel.tsx`、`frontend/components/sage/CitationSidebar.tsx` | 修复 | `node tests/sageChatWiring.test.cjs` | 移除硬编码 similarity（`:214` 「相关度 N%」）；保留注疏徽标逻辑 |
| **P7-08** | 真实渲染断言（**非 `includes` 字符串匹配**） | FE | P7-05, P7-06 | `frontend/tests/evidenceDrawer.test.cjs` | 测试 | `node tests/evidenceDrawer.test.cjs` | 断言实际渲染出的字段值，不得只断言源码字符串存在 |

### P7-09【repair】前端伪造证据数据修复（G-E，**独立于 PHASE 7**）
- **负责**：FE + CK ｜ **依赖**：P1-02, P2-02（需真实语料对照）｜ **Gate 归属**：GATE-7 前置
- **objective**：清除伪造可信信息——`roundtableData` 32 条中 **16 条出自零语料书目、22/32 无法定位、similarity 硬编码 0.87–0.97**；`sageData` 19 条中 **10 条无法核验**、similarity 手写 0.78–0.95（`01-gap-analysis.md` G-E，可复现命令见其 §5）。
- **inScope**：`frontend/lib/roundtableData.ts`、`frontend/lib/sageData.ts`
- **verify**：
  ```
  cd backend && $env:PYTHONIOENCODING="utf-8"; python ../eval/scripts/audit_frontend_citations.py
  ```
- **acceptance**：① 无法在语料中定位的引用**全部移除或显式标注为"非原典/AI 生成"**；② 不存在硬编码 similarity；③ 正文既有「非历史人物原话」声明（`sageData.ts:163`）在**引用区**也有等价声明（现状引用区无）。
- **失败回退**：若无法补齐真实数据，必须**删除**而非保留伪造条目。

### P7-10【verification】GATE-7 独立验证
- **负责**：QA ｜ **依赖**：P7-00, P7-05, P7-07, P7-08, P7-09 ｜ **inScope**：`docs/kb-v1/gates/GATE-7.md`
- **verify**：`npx vitest run`、`.cjs` 全跑、`tsc`、`eslint`、桌面与移动视口手工核对
- **acceptance**：见 §4 GATE-7

**Phase commit**：`feat(ui): add evidence drawer`。

---

## 10. PHASE 8 — Full Eval

**Gate**：GATE-8 ｜ **前置**：PHASE 4 + PHASE 5（+ PHASE 6）
**硬性纪律**：**必须走真实链路，禁止用 `FakeRag`/`monkeypatch` 冒充**（反例：`backend/tests/test_hackathon_readiness.py:49/66`、`test_debate_sentence_evidence.py:14-31`）。

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P8-01** | Eval 执行框架与 schema 校验接入 | EV | E-01…E-09 | `eval/scripts/schema.py`、`eval/scripts/validate_gold.py`、`eval/scripts/report.py` | 框架 | `python eval/scripts/validate_gold.py --all` | 全部数据集通过校验；`expected_passage_ids` 真实存在 |
| **P8-02** | Gold Set 达 **≥200 条**（如实标 provenance） | EV | P8-01 | `eval/*.jsonl` | Gold 数据 | `python eval/scripts/validate_gold.py --all --count` | ≥200 条；**`human` 条数单独统计并披露**；无人工确认的不得标 `human` |
| **P8-03** | 运行七类 Eval，产出报告 | EV | P8-02, P4-12, P5-11, P6-04 | `eval/reports/eval-report.json`、`eval/reports/eval-report.md` | 报告 | `python eval/scripts/report.py --out eval/reports/` | 输出 8 项指标（`evaluation.md` §5 公式）+ Recall@1/3/5 + MRR；**如实报告失败，不得只报通过项** |
| **P8-04** | 真实链路审计（禁 mock 冒充） | QA | P8-03 | `docs/kb-v1/gates/GATE-8.md` | 审计结论 | `git grep -n "FakeRag\|monkeypatch" backend/tests` + 核对 Eval 调用路径 | Eval 执行路径中**无** FakeRag/monkeypatch 替代检索 |
| **P8-05** | **GATE-8 独立验证** | QA | P8-04 | `docs/kb-v1/gates/GATE-8.md` | Gate 报告 | 独立复跑 `report.py` | 见 §4 GATE-8 |

---

## 11. PHASE 9 — Regression

**Gate**：GATE-9 ｜ **前置**：全部前置 Phase

> **⚠️ 必须写明的执行前提（否则 GATE-9「回归 PASS」不可复现）**
> 1. **串行执行 + 先确认无其他 backend 进程**：`conftest.py:15-19` 固定共享 `backend/test_wudian.db`，
>    并发运行会产生**伪失败**（实测 4 组不同失败集，见 `evaluation.md` §1.4 / F-6）。
> 2. **必须隔离 `CHROMA_PERSIST_DIR`**：`test_debate_classic_rag.py:20/51` 的 `build_index(force=True)`
>    会**清空并重建真实索引**（`rag_service.py:638-639` → `:607-617`）。
> 3. **不得删除/跳过测试**来让回归变绿。

| ID | 任务 | 负责 | 依赖 | inScope | verify | acceptance |
|---|---|---|---|---|---|---|
| **P9-01** | 后端回归（串行 + 进程检查 + 索引隔离） | BE | P1-05, P4-10, P5-09, P6-02 | `backend/tests/**`（仅修复，不得删测试） | 见下 P9-01 verify 块 | 全绿或**如实报告失败**；真实索引 `wudian_verses` 计数前后一致（143） |
| **P9-02** | 前端回归（vitest + `.cjs` + `tsc` + `eslint`） | FE | P7-00, P7-08 | `frontend/**` | `npx vitest run` + `.cjs` 全跑 + `npx tsc --noEmit` + `npx eslint . --ext .ts,.tsx --max-warnings 0` | 四项全 exit 0 |
| **P9-03** | Build | FE | P9-02 | `frontend/**` | `cd frontend && npm run build` | exit 0 |
| **P9-04** | **GATE-9 独立验证** | QA | P9-01, P9-02, P9-03 | `docs/kb-v1/gates/GATE-9.md` | 独立复跑全部四项 + `git diff --stat` | 见 §4 GATE-9 |

**P9-01 verify 块（必须原样执行）**：
```powershell
# 1) 确认无其他 backend pytest 进程
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'pytest' } | Select-Object ProcessId, CommandLine
# 期望：仅当前进程（或为空）

# 2) 隔离索引副本，保护真实索引
$iso = Join-Path $env:TEMP "wudian_regression_chroma"
if (Test-Path $iso) { Remove-Item -Recurse -Force $iso }
Copy-Item -Recurse "backend\chroma_db" $iso

# 3) 串行执行
cd backend
$env:CHROMA_PERSIST_DIR = "./_regression_iso_chroma"   # 仓库内相对临时目录（绝对路径会破坏 test_hackathon_readiness.py:15-24 的路径断言）
.venv\Scripts\python.exe -m pytest tests -q

# 4) 复核真实索引未被触碰
.venv\Scripts\python.exe -c "import chromadb;c=chromadb.PersistentClient(path=r'D:\systemDir\Desktop\悟典\backend\chroma_db');print([(x.name,x.count()) for x in c.list_collections()])"
# 期望：[('wudian_verses', 143)]

# 5) 清理临时产物
Remove-Item -Recurse -Force _regression_iso_chroma
```

**已知基线失败（必须在 GATE-9 报告中如实处理，不得隐藏）**：
- `tests/test_ai_provider.py:140-144` `assert settings.LLM_PROVIDER == "openai"` 因本机 `.env`（`LLM_PROVIDER=agnes`）**确定性失败**（F-4）。修复方式：测试显式构造 `Settings(_env_file=None)`。
- 后端完整环境**当前不存在**：`.venv` 缺 `pyjwt`（`requirements.txt:18` 已声明）→ collect 阶段 `ModuleNotFoundError`，0 测试执行。

**Phase commit**：`chore(kb): regression hardening`（仅含回归修复文件）。

---

## 12. PHASE 10 — Independent Acceptance

**Gate**：GATE-10 ｜ **前置**：GATE-1…GATE-9 全过

| ID | 任务 | 负责 | 依赖 | inScope | 产出物 | verify | acceptance |
|---|---|---|---|---|---|---|---|
| **P10-01** | 独立验收 | QA | 全部 | `docs/kb-v1/FINAL-ACCEPTANCE.md` | 验收报告 | 读取 `git diff`、tests、eval report、coverage、failure logs | 结论只能 `PASS` / `CONDITIONAL PASS` / `FAIL`；**`CONDITIONAL PASS` 不能当作最终完成**（用户明确要求） |

**P10-01 必须核对的输入**：`git diff`（实际改动）、测试结果、`eval-report.json/md`、覆盖率、失败日志、
数据来源审计（P2-05）、需求覆盖（PR 报告）。QA **不参与任何核心功能实现**。

---

## 13. GATE 定义（可自动化判定 · 失败回退 · 当前可达性）

> 判定规则：**每条 Gate 的所有条件均为 AND**；任一条件无法自动化判定即**不得判定 PASS**。
> **禁止修改目标数字**；未运行/未复核/缺证据一律标 **未验证**，不得计入通过。

### GATE-0 — 仓库审计（已完成）
- **通过条件**：`00-current-state.md` 列明当前 数据/RAG/embedding/citation/tests 五项真实状态，且每条结论可追溯。
- **可达性**：**已达成**（t10/t11/t12 产物 + 本文件 + `04-gate-0-review.md` 待 QA 出具）。
- **回退**：QA 若判 FAIL → 补齐证据后重审。

### GATE-1 — Data Architecture
- **通过条件（可自动化）**：① `pytest tests/test_knowledge_schema.py tests/test_ingestion.py tests/test_source_registry.py -q` 全 PASS；② fixture 数据成功 ingest 且条数 > 0；③ 无来源条目**被拒绝**（负例测试存在且通过）；④ `alembic upgrade head` exit 0 且 L1/L2 分表。
- **前置**：**P0R-00 必须已完成**。否则上述 pytest 在 collect 阶段 `exit 4`（`ModuleNotFoundError: No module named 'jwt'`）、**0 测试执行**，"全 PASS"无法判定（t9 F-01/F-02）。
- **当前可达性**：**不可达**（`schemas/knowledge.py`、`ingestion.py`、`models/knowledge.py` 均不存在，实测 `Test-Path` = False；且 P0R-00 未完成）。
- **失败回退**：schema 字段争议 → 回到 `02-architecture.md` §9 契约冻结表裁决，不得在实现中临时改字段名。

### GATE-2 — Core Corpus
- **通过条件（可自动化）**：① `python eval/scripts/audit_corpus_provenance.py` 输出 `passages_without_source = 0`；② 抽查 10 条可追溯到 `source_registry.json` 条目；③ 无占位/生成文本混入（人工抽查 + 关键词审计）；④ P2-02 的去重处置结果可列出（含枚举的 1 对全句/摘句关系）。
- **当前可达性**：**不可达**。**12 部中 4 部有数据、8 部零语料**（论语/道德经/墨子/韩非子有数据；孟子/荀子/大学/中庸/庄子/商君书/传习录/孙子兵法为零。注：`00`/`01` 早期写作"3 部/9 部"，t9 复核为 4/8，已由 t14/t15 修正）；零 `source_provider/url/edition/license`；`data/raw` 为空。
- **诚实边界**：「原典不得来自 LLM 生成」**无法证实也无法证伪** → 该子项必须标 **未验证**。
- **失败回退**：Q3 授权未解决 → 收窄 V1 范围（Q2 选项 a）并**如实标注覆盖范围**，禁止填充占位文本。

### GATE-3 — Modern Issue Ontology
- **通过条件（可自动化）**：`pytest tests/test_issue_ontology.py -q` 全 PASS 且用例数 **≥50**（`pytest --collect-only -q | tail -1` 核对）。
- **当前可达性**：**不可达**（Ontology 0 实现）。
- **失败回退**：分类准确率不足 → 扩充 ontology 而非放宽判定。

### GATE-4 — RAG V2 检索
- **通过条件（可自动化）**：`python eval/scripts/run_retrieval_eval.py --dataset eval/retrieval_gold.jsonl` 输出
  **Recall@1 / Recall@3 / Recall@5 / MRR**；**Recall@5 ≥ 90%**；且性能 **P50 < 1s、P95 < 3s**（不含外部 LLM）。
- **当前可达性**：**不可达（且当前无法测量）**。G-A 使 `retrieve()` 恒空 → Recall 结构性为 0；L1 仅 128 条、仅 1 部完整书。
- **失败回退**：无外部 embedding 密钥（Q4）时 → 标注 `degraded=true` 并**如实报告未达标**，禁止改公式或改目标。

### GATE-5 — Trust Layer 对抗
- **通过条件（可自动化）**：① **`eval/adversarial_quotes.jsonl` 已建成**（否则本 Gate 无判定依据，直接不得判定）；② `pytest tests/test_adversarial_quotes.py -q` 全 PASS；③ **Quote Exactness ≥ 99%**；④ **Source Attribution ≥ 98%**；⑤ **Fabricated Classical Quote ≈ 0**（任何明显伪造名言通过验证 → **立即 FAIL**，无例外）；⑥ `verify-quote` 契约断言存在 `quote_exists=true & source_correct=false` 的用例；⑦ **§7 "P5-05 必含对抗用例" A1/A2/B1/B2/C1/C2/C3/D1 全部通过**——特别是 **A2（真古文 + 跨书错派）当前 FAIL**，修复前本 Gate 不可能 PASS；⑧ `candidates[]` 对摘句/全句**不产生重复来源**。
- **当前可达性**：**不可达**。无 QuoteVerifier；`citation_validator` 仅双向子串匹配（`citation_validator.py:83-91`）；无白名单；无 Trust State。**t9 实测第十六章第一例直接失败**（`己所不欲勿施于人` 谎称《孟子》→ `verifiable=True, all_verified`）。
- **失败回退**：任一伪造引文放行 → 回退 PHASE 5 修复，**不得通过放宽匹配来"通过"**。

### GATE-6 — Debate Integration
- **通过条件（可自动化）**：① `eval/school_consistency.jsonl` 已建成；② `python eval/scripts/run_school_eval.py` 输出 **School Leakage < 1%**；③ 各派发言引用的 source 全部属于本派。
- **当前可达性**：**不可达**。G-D（sage-chat 无学派过滤，实测孔子路径返回《道德经》排第一）；非儒家各派仅 3–4 条语料。
- **失败回退**：语料不足 → 扩充各派语料，禁止放宽 `allowed_books`。

### GATE-7 — Frontend Evidence Drawer
- **通过条件（可自动化）**：① `npx vitest run` + 全部 `.cjs` PASS；② `npx tsc --noEmit` exit 0；③ `npx eslint ... --max-warnings 0` exit 0；④ Evidence Drawer 在 Desktop 与 Mobile 双视口渲染 9 个必需字段；⑤ 无硬编码 similarity；⑥ D 与 A 不显示为同一等级。
- **当前可达性**：**不可达**。G-F（分层无法表达）、无 A/B/C/D、无 Trust State、G-H（回归门禁失效：`.cjs` 被排除、20 占位断言、tsc 26 errors、无 eslint 配置）。**强依赖 PHASE 1 与 PHASE 5**。
- **失败回退**：字段缺失 → 回到 PHASE 1/5 补齐，**禁止前端继续伪造字段**。

### GATE-8 — Full Eval
- **通过条件（可自动化）**：① **≥200 gold questions**（并披露其中 `human` 条数）；② `eval-report.json` + `eval-report.md` 均存在且含 8 项指标；③ **Unsupported Correct Refusal ≥ 95%**；④ **Core Claim Evidence Coverage ≥ 95%**；⑤ Eval 执行路径**无** FakeRag/monkeypatch 冒充。
- **当前可达性**：**不可达**。`eval/` 不存在、0 条样本；无 Trust State；无 Claim-Evidence 绑定。
- **失败回退**：Gold 不足 → 如实报告实际条数与 provenance，**禁止把 AI 生成样本标为人工 Gold**。

### GATE-9 — Regression
- **通过条件（可自动化）**：① 后端 `pytest tests -q` 在**串行 + 无其他 backend 进程 + 索引隔离**下执行；② 前端 vitest + `.cjs` + `tsc` + `eslint` 四项 exit 0；③ `npm run build` exit 0；④ 真实索引 `wudian_verses` 计数前后一致（143）；⑤ 无测试被删除/跳过以达成绿灯（`git diff --stat` 核对 `backend/tests/`、`frontend/tests/`）。
- **当前可达性**：**不可达**。
  **解除条件 = P0R-00 完成（补齐 `.venv` 的 `pyjwt`，使后端测试可 collect）且前端门禁修复（P7-00）完成。**
  当前阻断：后端环境缺 `pyjwt` → collect 阶段 `exit 4`、0 测试执行；`test_default_provider_is_openai` 因本机 `.env` 确定性失败；前端门禁失效（G-H：`.cjs` 被排除、20 占位断言、tsc 26 errors、无 eslint 配置）。
- **失败回退**：出现伪失败 → 先排除并发与索引污染，**不得改断言**。
- **⚠️ 安全前置**：P0R-00 补齐 `pyjwt` 后，破坏性测试（`test_debate_classic_rag.py:20/51` 的 `build_index(force=True)`）即变得**可执行**，会清空真实 143 条索引。**本 Gate 的任何后端运行必须强制隔离 `CHROMA_PERSIST_DIR`**（相对路径），与 P0R-00 安全硬约束及 §11 verify 块一致。

### GATE-10 — Independent Acceptance
- **通过条件**：QA 出具 `FINAL-ACCEPTANCE.md`，结论为 **PASS**（`CONDITIONAL PASS` 不构成完成）。
- **当前可达性**：**不可达**（前置 Gate 全部未通过）。
- **回退**：FAIL → 回到对应 Phase 修复，最多 3 次修复 / 4 轮审查，达上限明确升级。

### Gate 可达性总表

| Gate | 目标 | 当前可达性 | 主要阻断 |
|---|---|---|---|
| GATE-0 | 列明五项真实状态 | **可达（已达成）** | — |
| GATE-1 | fixture 可 ingest；schema test 全 PASS | 不可达 | schema/ingestion/models 均不存在 |
| GATE-2 | 所有 passage 有 source；原典非 LLM 生成 | 不可达 | 9/12 书目零语料；零来源字段；生成方式**无法证实/证伪** |
| GATE-3 | ≥50 分类测试 | 不可达 | Ontology 0 实现 |
| GATE-4 | Recall@1/3/5、MRR；**Recall@5 ≥ 90%** | 不可达（无法测量） | G-A；语料 128 条；`eval/` 不存在 |
| GATE-5 | **Quote Exactness ≥ 99%**、**Source Attribution ≥ 98%**、伪造 ≈ 0 | 不可达 | G-B；无 QuoteVerifier/白名单/TrustState；E-02 未建 |
| GATE-6 | **School Leakage < 1%** | 不可达 | G-D；各派仅 3–4 条语料 |
| GATE-7 | Desktop + Mobile Evidence Drawer | 不可达 | G-F；无 A/B/C/D；无 Trust State；G-H |
| GATE-8 | **≥200 gold**、**拒答 ≥ 95%**、**Claim Coverage ≥ 95%** | 不可达 | `eval/` 不存在；无 Trust State；无 Claim-Evidence |
| GATE-9 | tests/build/lint/typecheck 全过 | 不可达 | 后端缺 pyjwt；F-4 恒失败；前端门禁失效 |
| GATE-10 | 独立验收 PASS | 不可达 | 前置全未通过 |
| 性能 | P50<1s / P95<3s | **当前达标**（实测 P50≈5–11ms、P95≈7–15ms） | 仅 143 条规模且 `retrieve()` 恒空；**RAG V2 后必须重测** |

---

## 14. 关键路径与可并行点

### 14.1 关键路径（最长链）
```
P0R-01 → P0R-02 → P0R-03
  → P1-01 → P1-03 → P2-01(Q3) → P2-02
  → P4-08 → P4-09 → P4-10
  → P5-01 → P5-08 → P5-10 → E-02 → P5-11(GATE-5)
  → P6-02 → P7-00 → P7-05 → P7-08
  → P8-02 → P8-03 → P9-01 → P10-01
```
**关键路径长度**：约 22 个串行任务。**Q3（授权）与 Q1（verse_no 方向）是关键路径上的决策阻塞点**。

### 14.2 可并行点
| 并行组 | 任务 | 说明 |
|---|---|---|
| A | P1-02 / P1-03 / P1-04 / P1-05 | P1-01 完成后可并行（不同文件） |
| B | E-01 / E-06 / E-08 / E-09 | 与 PHASE 1 并行（Eval 工作流） |
| C | **P4-01…P4-09** | **最大并行组**：9 个独立新文件 |
| D | P5-01 / P5-02 / P5-03 / P5-04 | 不同新文件可并行；P5-05/06/07 需串行（改既有文件） |
| E | P7-00 / P7-09 | 可在 PHASE 1/5 期间并行准备 |
| F | P2-05 / E-05 / E-07 | 数据与 Eval 准备并行 |

### 14.3 文件冲突串行约束（防止多写者）
| 文件 | 被哪些任务写入 | 串行要求 |
|---|---|---|
| `backend/app/services/rag_service.py` | P0R-01, P0R-02, P0R-03, P4-10, P6-01 | **严格串行**，按编号顺序 |
| `backend/app/schemas/ai.py` | P0R-01, P5-07 | 串行（P0R 先） |
| `backend/tests/conftest.py` | P1-05 | 独占 |
| `backend/app/services/citation_validator.py` | P5-05 | 独占 |
| `backend/app/main.py` | P0R-03, P5-09 | 串行 |
| `backend/app/services/debate_engine.py` | P5-06, P6-02 | 串行 |

---

## 15. 第二十一章工作协议在任务结构中的体现

PROJECT-BRIEF 第二十一章要求每个任务走 **PLAN → IMPLEMENT → TEST → SELF REVIEW → INDEPENDENT REVIEW → FIX → GATE**。

| 阶段 | 在本 DAG 中的载体 |
|---|---|
| **PLAN** | 每个任务的 `objective` + `inScope` + `acceptance` 必须在开工前写入任务描述（本文件即总计划） |
| **IMPLEMENT** | 任务本体（仅写 inScope 内路径） |
| **TEST** | 任务自带的 `verify` 命令；质量类任务必须**实际执行并贴原始输出** |
| **SELF REVIEW** | 任务完成后由负责人自查：`git diff --stat` 是否越界、断言是否被削弱 |
| **INDEPENDENT REVIEW** | **每个 Phase 末的 QA 任务**（P1-07 / P2-06 / P3-04 / P4-12 / P5-11 / P6-04 / P7-10 / P8-05 / P9-04 / P10-01），QA 不参与该 Phase 实现 |
| **FIX** | QA 判 `needs_revision`/`reject` 后回到原任务修复；**最多 3 次修复、4 轮审查**，达上限明确升级 |
| **GATE** | §13 各 Gate 的可自动化判定条件 |

**硬性规则**
- 任一阶段失败**不得进入下一阶段**。
- QA 判 FAIL 不得由实现者自行改为 PASS。
- `CONDITIONAL PASS` 不能当作最终完成（用户明确要求）。
- 完成定义（第二十三章）只有 `FINAL-ACCEPTANCE.md = PASS` 才成立。

---

## 16. Git 规则（第二十二章）

| Phase | commit message | 允许文件 |
|---|---|---|
| 0-R | `fix(rag): resolve verse_no type and fallback blockers` | P0R 三个任务的 inScope |
| 1 | `feat(kb): add canonical knowledge schema` | PHASE 1 inScope |
| 2 | `feat(kb): add core corpus` | PHASE 2 inScope |
| 3 | `feat(kb): add modern issue ontology` | PHASE 3 inScope |
| 4 | `feat(rag): add hybrid retrieval` | PHASE 4 inScope |
| 5 | `feat(trust): add quote verifier` | PHASE 5 inScope |
| 6 | `feat(debate): bind speeches to evidence packs` | PHASE 6 inScope |
| 7 | `feat(ui): add evidence drawer` | PHASE 7 inScope |
| 8 | `feat(eval): add retrieval gold set` | PHASE 8 inScope |
| 9 | `chore(kb): regression hardening` | PHASE 9 修复文件 |

**禁止**：一个 commit 修改数百个无关文件；提交用户既有改动；提交 `.agent-teams/` 状态；推送；部署；执行生产迁移。

---

## 17. 不可达 Gate 清单（诚实结论，禁止改数字）

**当前数据与能力下明确不可达**：
1. **GATE-4**：`Recall@5 ≥ 90%` —— G-A 使 Recall 结构性为 0（无法测量）+ 语料仅 128 条。
2. **GATE-5**：`Quote Exactness ≥ 99%`、`Source Attribution ≥ 98%` —— 无 QuoteVerifier，现状仅双向子串匹配。
3. **GATE-6**：`School Leakage < 1%` —— sage-chat 无学派过滤 + 各派仅 3–4 条语料。
4. **GATE-8**：`Unsupported Correct Refusal ≥ 95%`、`Core Claim Evidence Coverage ≥ 95%`、`≥200 gold` —— 无 Trust State、无 Claim-Evidence、`eval/` 不存在。
5. **GATE-1/2/3/7/9/10**：均不可达（缺实现 / 缺来源 / 缺门禁）。

**当前达标但需重测**：性能 `P50 < 1s` / `P95 < 3s`（实测 P50≈5–11ms），但仅 143 条规模且 `retrieve()` 恒空，**RAG V2 后必须重测**。

**使其可达的必要条件**（不得绕过）：
- GATE-4 → 修复 G-A（P0R-01）+ 扩充语料（PHASE 2）+ 真实语义 embedding（Q4）
- GATE-5 → PHASE 5 全部 + **E-02 先建成**
- GATE-6 → 修复 G-D（P6-01）+ 扩充各派语料
- GATE-8 → PHASE 5（Trust State + Claim-Evidence）+ P8-02（≥200 Gold）

---

## 18. 未验证与不可核验项（诚实声明）

| 项 | 状态 | 原因 |
|---|---|---|
| 本文所有新增文件路径的实际创建与行为 | **未验证** | PHASE 0 只读，未创建任何代码文件 |
| Q1–Q5 决策 | **未决** | 需用户/队长决策 |
| 语义 embedding 质量 | **未验证** | 无密钥；本地模型未安装未测试 |
| BM25 / reranker / diversity 实际效果 | **未验证** | 尚未实现 |
| 外部来源（ctext.org / 维基文库）授权与可用性 | **未核验** | 访问被拒（non-public IP） |
| 语料是否曾由 LLM 生成或改写 | **无法证实也无法证伪** | 无生成日志、无 raw 底本 |
| 真实 LLM 端到端输出质量 | **未验证** | `.env` 无 API_KEY |
| 前端对 `verse_no` 的整数依赖 | **未验证** | 决定 Q1，需前端确认 |
| 各 Phase 实际工期 | **未估算** | 无基准数据，本文不编造工期 |

---

## 19. 本文件核对记录（可复现）

```powershell
# 目标路径全部不存在（实测）
foreach($p in 'backend/app/schemas/knowledge.py','backend/app/services/source_registry.py',
  'backend/app/services/ingestion.py','backend/app/models/knowledge.py',
  'backend/app/services/quote_verifier.py','backend/app/services/citation_guard.py',
  'backend/app/services/claim_evidence.py','backend/app/services/trust_state.py',
  'backend/app/api/knowledge.py','backend/app/services/issue_structurer.py',
  'backend/app/services/evidence_pack.py','data/processed/modern_issue_ontology.json',
  'data/sources/source_registry.json','frontend/components/ui/EvidenceBadge.tsx'){
  "$p : $(Test-Path $p)" }   # 全部 False

# 既有迁移仅 1 个
Get-ChildItem backend/migrations/versions -File | Select-Object Name
# → 601e9ee0d57f_initial_schema.py

# 前端门禁实测
cd frontend && npx tsc --noEmit            # → 26 errors，全部在 tests/curtainPhysics.test.tsx
cd frontend && npx eslint . --ext .ts,.tsx --max-warnings 0
# → "ESLint couldn't find a configuration file"（无 eslint 配置）
Test-Path frontend/.eslintrc.json           # → False

# 写入边界
git status --short                          # → ?? docs/kb-v1/
git diff --stat                             # → (空)
```

---

## 20. 交付摘要

- **文档**：`docs/kb-v1/03-task-dag.md`（本文件，唯一写入）
- **任务总数**：**78** 个（唯一任务 ID 计数，可复现命令见下）
  - PHASE 0-R：**4**（含本次新增的 **P0R-00 环境引导**，t9 F-02 修正）｜ Eval 工作流：9 ｜ PHASE 1：7 ｜ PHASE 2：6 ｜ PHASE 3：4
  - PHASE 4：12 ｜ PHASE 5：11 ｜ PHASE 6：4 ｜ PHASE 7：11 ｜ PHASE 8：5 ｜ PHASE 9：4 ｜ PHASE 10：1
  - 计数说明：原为 **77**（PHASE 0-R=3）；t9 F-02 要求新增环境引导任务 **P0R-00**，故总数 **77 → 78**、PHASE 0-R **3 → 4**。
  - 核对命令：
    ```powershell
    Select-String -Path docs/kb-v1/03-task-dag.md -Pattern '\b(P0R-\d{2}|E-\d{2}|P\d{1,2}-\d{2})\b' -AllMatches |
      ForEach-Object { $_.Matches } | ForEach-Object { $_.Value } | Sort-Object -Unique
    # → 78 个唯一 ID（P0R=4, E=9, P1=7, P2=6, P3=4, P4=12, P5=11, P6=4, P7=11, P8=5, P9=4, P10=1）
    ```
- **Gate 数**：GATE-1…GATE-10（含 GATE-0 已完成）
- **关键路径**：约 22 个串行任务（§14.1），阻塞点为 Q1 与 Q3 决策
- **不可达 Gate**：GATE-4 / GATE-5 / GATE-6 / GATE-8（及 GATE-1/2/3/7/9/10）
- **已写入的既定前置项**：C1/C3/B2 修复排在 PHASE 1 前；GATE-5 强制 E-02 先建 + `quote_exists`/`source_correct` 两独立字段；
  PHASE 7 不早于 PHASE 1/5 + 前端门禁修复独立前置；PHASE 9 串行 + 进程检查 + 索引隔离；PHASE 8 禁 FakeRag 冒充；每 Phase 独立 commit。

**声明**：本文件为 PHASE 0 产物，未创建任何代码文件，未修改 `backend/`、`frontend/`、`data/`、`PROJECT-BRIEF.md`，
未 commit / push / deploy。所有"现状"陈述均来自七份审计报告与三份 PHASE 0 文档，带 `文件:行号` 或可复现命令。

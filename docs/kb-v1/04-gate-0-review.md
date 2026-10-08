# 04 — GATE-0 独立审查报告（Independent QA Review）

- 任务：t9 / attempt 1 / attempt_id `9845efcd-a57e-4609-8bb0-e2aa21c03338`
- 审查者：qa-reviewer（独立 QA，未参与任何 PHASE 0 文档写作，未参与任何实现）
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c861828eb8f1ec8816eb8d95212f78cdc7faeb`
- 审查日期：2026-07（本机系统日期）
- 审查性质：**只读**。唯一写入文件为本报告。未修改 `backend/`、`frontend/`、`data/`、`PROJECT-BRIEF.md`；未 commit / push / deploy。

---

## 0. 结论

# 结论：CONDITIONAL PASS（有条件的通过）

**GATE-0 的"真实状态已列明"这一核心要求，达成。**

四份文档（`00`–`03`）对 GATE-0 五项（当前数据 / RAG / embedding / citation / tests）的记述，经我独立复跑与源码复核，**与真实状态一致，未发现任何伪造、淡化或"未达标宣称完成"**。特别地：

- 7 项 Gate 指标被明确判定为**不可达**，且未修改任何目标数字；
- `eval/` 不存在、0 条 Gold、零来源字段、零人工复核 → 全部如实标注；
- 外部核验通道不可用被如实声明，市场/竞品结论被降级为"未核验假设"；
- 未把 AI 生成文本当权威原典，未编造 source，未用 mock 冒充真实 RAG。

**但**存在 **2 项 blocker 级计划缺陷**（见 F-01、F-02），它们会使 PHASE 1 的实际执行**立即失败或无法验收**，必须在启动 PHASE 1 前修正。此外发现 **3 项事实性/计划性缺陷**：**1 项 PHASE 0 文档未记录的新数据缺陷**（F-03）、**1 项文档数字与事实不符**（F-06：V1 书目覆盖 3/9 应为 4/8）、以及对抗验证发现的额外放行情形（F-05）。

**为什么是 CONDITIONAL PASS 而不是 PASS**：GATE-0 要求的是"列明真实状态"，这一点已满足；但 `03-task-dag.md` 中 **PHASE 1 的 verify 命令使用了本机无法执行的解释器**（F-01），且**没有任何任务修复该环境**（F-02），导致"PHASE 1 的 schema test 全 PASS"这一 GATE-1 判据在计划层面就不可达。这是可修复的计划缺陷，不是伪造，故不判 FAIL；但在修正前**不得进入 PHASE 1 实施**。

**为什么不是 FAIL**：没有任何证据表明文档作者隐瞒、伪造或降低标准；除 F-06 外，所有我抽查的数字均能复现，且 F-06 属**内部自相矛盾的事实性错误**（文档自身表格与脚本输出即为 4/8），非掩盖性造假。FAIL 应保留给"证据造假或未达标宣称完成"，本报告未发现此类情形。

> **CONDITIONAL PASS 不等于完成。** 本结论仅表示 PHASE 0 的审计产出可信、可作为后续基础；PHASE 1–10 尚未开始，项目远未 DONE。

---

## 1. 审查范围与方法

### 1.1 实际执行的独立取证（非转述文档）

| # | 命令 / 方法 | 目的 |
|---|---|---|
| 1 | `python -m pytest tests -q`（系统 Python 3.11.9，`CHROMA_PERSIST_DIR=./_regression_iso_chroma`，串行） | 后端基线复跑 |
| 2 | `.venv/Scripts/python.exe -m pytest tests -q` | venv 基线复跑 |
| 3 | `npm --prefix frontend test` | 前端基线复跑 |
| 4 | `node_modules/.bin/tsc.cmd --noEmit` | tsc 错误数 |
| 5 | 逐个 `node tests/*.test.cjs`（22 个） | `.cjs` 套件真实通过/失败数 |
| 6 | 独立 python 脚本统计语料条目数 / verse_id / 索引 metadata | 语料与索引事实 |
| 7 | 独立 python 脚本对 `citation_validator` 做 8 类对抗输入 | 可信层结论对抗验证 |
| 8 | 独立 python 脚本比对 `sageData` / `roundtableData` 与真实语料 | 前端伪造证据核验 |
| 9 | `git show 64c8618 -- frontend/package.json` | 测试入口变更取证 |
| 10 | `git status --porcelain` / `git diff --stat` / `Get-FileHash PROJECT-BRIEF.md` | 写入边界取证 |

### 1.2 前置声明（诚实披露）

- **串行前提**：执行前已确认无其他 `python`/`pytest` 进程（`Get-Process python*` 为空）。`conftest.py:14-19/26` 固定共享 `backend/test_wudian.db`，并发会产生伪失败。
- **索引隔离**：`test_debate_classic_rag.py:20/51` 调用 `build_index(force=True)` → `_clear_collection()`，会清空真实 collection。我**全程使用隔离副本** `./_regression_iso_chroma`（相对路径），跑完后**已删除**副本，并复核真实索引仍为 **143**。
- **未执行的破坏性操作**：未执行 `init_db.py`（会清空 18 张表）；未对真实索引执行任何 `force=True` 重建。
- **我在审查中新增/删除的文件**：仅 `backend/_regression_iso_chroma/`（临时副本，已删除）与 `docs/kb-v1/04-gate-0-review.md`（本报告）。探针脚本写在仓库外 TEMP 目录。

---

## 2. GATE-0 五项判据核对表

PROJECT-BRIEF GATE-0 要求列明：**当前数据 / RAG / embedding / citation / tests** 的真实状态。

| # | 判据 | 文档是否列明 | 我的独立复核结果 | 判定 |
|---|---|---|---|---|
| ① | **当前数据** | ✅ `00-current-state.md` §1 | 独立复算：lunyu **107**、debate_classics **21**、union **128**（零重叠）、注疏 **15**、索引组成 107+15+21=**143**。与文档**完全一致** | **PASS** |
| ② | **RAG** | ✅ §2 | 独立复现 C1（`retrieve` 0/5 vs `vector_search` 5/5，`hybrid_search` 抛 `ValidationError`）、C2、C3、B2。与文档一致 | **PASS** |
| ③ | **embedding** | ✅ §3 | 源码复核：`LocalHashEmbeddingFunction(dimensions=384)`、`blake2b(digest_size=8)` 分桶、非语义。与文档一致 | **PASS** |
| ④ | **citation** | ✅ §4 | 独立跑 8 类对抗输入；确认 `verifiable` 语义 = 双向子串、出处正确性零校验、空出处放行（`:99-100`）。与文档一致，且**我额外发现更严重情形**（见 F-05） | **PASS** |
| ⑤ | **tests** | ✅ §5 | 独立复跑：后端系统 Python **1 failed / 82 passed / 2 skipped / 13 subtests / 72.22s**；venv **0 executed**（exit 4）；前端 **23 files / 41 tests**；tsc **26 errors / exit 1**；`.cjs` **18 pass / 4 fail / 22**。与文档**逐项一致** | **PASS** |

**GATE-0 五项全部已列明且经独立验证。** 这是本次结论为 CONDITIONAL PASS（而非 FAIL）的主要依据。

### 2.1 与文档逐项对账（无差异）

| 数字 | 文档值 | 我实测 | 一致 |
|---|---|---|---|
| L1 原典 | 128（107+21） | 128 | ✅ |
| 注疏 | 15（仅朱熹） | 15 | ✅ |
| 索引 `wudian_verses` | 143 | 143 | ✅ |
| `retrieve()` vs `vector_search` | 0 / 5（5 查询） | 0 / 5（5 查询） | ✅ |
| `hybrid_search` | 抛 `ValidationError` | 抛 `ValidationError` | ✅ |
| C3 `top_k=3` 四派 | n=3 | n=3 | ✅ |
| C3 `top_k>=4` | laozi/mozi/hanfeizi n=4、confucius n=3 | 同 | ✅ |
| 后端系统 Python | 1 failed / 82 passed / 2 skipped | 同（72.22s） | ✅ |
| 后端 venv | 0 executed | 0 executed（exit 4） | ✅ |
| 前端 vitest | 23 files / 41 tests | 同 | ✅ |
| tsc | 26 errors，全在 `curtainPhysics.test.tsx`，exit 1 | 同 | ✅ |
| `.cjs` 套件 | 22 个，18 通过 / 4 失败 | 22 个，18/4 | ✅ |
| 占位断言 | 20 / 41 | 20 | ✅ |
| `sageData` 兜底 | 19 条，10 无法核验 | 19 条，**10** 无法核验 | ✅ |
| `roundtableData` | 32 条，16 出自零语料书目 | 32 条，**16** 出自零语料书目（孟子 8 + 传习录 8） | ✅ |
| 12 部目标书目覆盖 | — | 文档称「3 部有数据 / 9 部零语料」 | **4 部有数据 / 8 部零语料**（论语/道德经/墨子/韩非子） | ❌ **不一致（F-06）** |
| 任务总数 | 77（P0R3/E9/P1 7/P2 6/P3 4/P4 12/P5 11/P6 4/P7 11/P8 5/P9 4/P10 1） | 77，分布**完全相同** | ✅ |
| HEAD 变更 | 64c8618 把 `.cjs` 链换成 `vitest run` | 确认（21 套件链 → `vitest run`） | ✅ |

**除 F-06（V1 书目覆盖 3/9 vs 4/8）外，未发现其他数字与文档不符。**

---

## 3. Findings

### F-01【blocker】PHASE 1 及后续所有任务的 `verify` 命令使用无法执行的解释器

- **问题**：`03-task-dag.md` 中几乎所有任务的 `verify` 都写成 `cd backend && .venv/Scripts/python.exe -m pytest ...`（如 `:63`、`:75`、`:87`、`:136`、`:141`）。但 `backend/.venv` 缺 `pyjwt`，pytest 在 **collect 阶段**即 `ModuleNotFoundError: No module named 'jwt'`，**0 个测试执行、exit code 4**。即：这些 verify 命令**永远无法产生 PASS**，无论实现多正确。
- **证据**：
  ```
  $ cd backend && .venv\Scripts\python.exe -m pytest tests/_qa_probe_temp_test.py -q
  app\core\security.py:9: in <module>
      import jwt
  E   ModuleNotFoundError: No module named 'jwt'
  EXITCODE=4
  ```
  （用一个内容为 `def test_ok(): assert True` 的临时测试文件验证——**连最简测试都无法 collect**，证明问题在环境而非测试。）
  链路：`conftest.py:40` → `main.py:199` → `api/ai.py:18` → `core/deps.py:15` → `core/security.py:9`。
- **影响**：GATE-1 判据是"schema test 全 PASS"。按当前计划，PHASE 1 的 P1-06/P1-07 无法验收 → **PHASE 1 结构性无法通过**，后续 PHASE 2–10 全部被阻塞。
- **requiredFix**：在 PHASE 0-R 增加环境修复任务（见 F-02），并把所有 `verify` 中的解释器统一为**已验证可执行**的那个；或在任务中显式写明"先 `pip install -r requirements.txt` 到 `.venv`"。**不得**把 verify 写成无法执行的命令后仍宣称通过。

### F-02【blocker】计划中不存在任何修复后端测试环境的任务

- **问题**：`03-task-dag.md` §11 已**如实记录**"后端完整环境当前不存在：`.venv` 缺 `pyjwt`（`requirements.txt:18` 已声明）→ 0 测试执行"（`:370`），但**全计划 77 个任务中没有任何一个负责修复它**。搜索 `pip install` / `requirements.txt` / 环境修复 类任务：**零命中**。
- **证据**：
  - `backend/requirements.txt:18` = `pyjwt>=2.8.0`（已声明）；
  - `backend/.venv` 实测 `pip list`：有 `chromadb 1.5.9`、`pydantic 2.13.4`、`pytest 9.1.1`，**无 pyjwt**；
  - 系统 Python 3.11.9：有 `jwt 2.15.0`，**无 chromadb**；
  - 即"两个解释器各缺一半"，而计划未安排任何任务补齐。
- **影响**：与 F-01 同源。GATE-9 已判定"不可达"，但未给出达成路径；`03-task-dag.md:443/464` 只描述"不可达"，未定义"如何变为可达"。
- **requiredFix**：在 PHASE 0-R（或 PHASE 1 前置）新增明确任务：objective = 让**单一解释器**能完整执行后端套件；inScope = `backend/.venv` 依赖安装（不改 `requirements.txt` 语义）；acceptance = `pytest tests -q` 能 collect 且产出真实 82+ passed。并明确该任务的 verify 命令。

### F-03【high】PHASE 0 文档未记录的新数据缺陷：`verse_id` 存在非数字占位 `'10.x'` / `'18.x'`

- **问题**：`data/processed/lunyu.json` 的 107 条中有 **2 条** `verse_id` 不是"章.节"数字格式，而是 `'10.x'`（乡党）与 `'18.x'`（微子）。这两条已进入向量索引（`verse_no` 亦为 `'10.x'`/`'18.x'`）。
- **证据**：
  ```
  $ python -c "统计 lunyu.json 的 verse_id"
  non-numeric verse_ids: ['10.x', '18.x']
    chapter: 乡党 | id: 10.x | original: 孔子于乡党，恂恂如也，似不能言者。...
    chapter: 微子 | id: 18.x | original: 楚狂接舆歌而过孔子曰：「凤兮凤兮！...
  $ 索引复核：NOT matching \d+\.\d+ pattern 中包含 '10.x', '18.x'
  ```
  四份文档中检索 `10\.x|18\.x`：**零命中**（未记录）。
- **影响**：
  1. `'10.x'` 携带**不确定的节号**语义（"某节"），若 PHASE 1/2 迁移时按数字解析会失败或误映射；
  2. Q1 决策方案 (c)"拆为 `chapter_no` + `section_no`"会**直接无法处理**这两条；
  3. 这两条既是 `verse_id` 又是 `verse_no`，会一并进入 PHASE 1 的 passage 迁移，若不处理将把占位符带入权威层。
- **requiredFix**：在 `00-current-state.md` §1 补记该缺陷（2 条、具体章节、来源行）；在 Q1 决策与 P2-02（论语迁移）的 acceptance 中明确**这两条如何处理**（补齐真实节号，或显式标记为 `section=null` 并记录），**禁止**让占位符静默进入 L1。

### F-04【medium】`02-architecture.md` 的开放问题 Q6 未传递到 `03-task-dag.md`

- **问题**：`02-architecture.md` §12 列出 **Q1–Q6** 共 6 个待决问题，其中 **Q6** 专门要求确认 `_rag_probe_enviro.py` 曾以只读方式打开真实索引的披露是否可接受（决定人写为「队长/qa-reviewer」）。但 `03-task-dag.md` §0 只列 **Q1–Q5**，**Q6 未被承接**。
- **证据**：`02-architecture.md:583` 有 Q6；`grep 'Q6' docs/kb-v1/03-task-dag.md` → **零命中**。
- **影响**：低-中。该问题本身不阻断任何 Phase（我已复验索引内容完整，143 条不变），但"待决问题清单"在文档间不闭合，执行者按 `03` 推进时会遗漏一项已登记的待确认事项。
- **requiredFix**：在 `03-task-dag.md` §0 补入 Q6（或明确标注"已由 qa-reviewer 于 04-gate-0-review.md 处理完毕，无需决策"）。

### F-05【high】对抗验证发现的额外放行情形（比文档记载更宽）

- **问题**：`00-current-state.md` §4 与 `trust.md` 已记录"双向子串使真实短句内嵌伪造长文通过"。我做了 8 类对抗输入，确认该结论，并额外量化了**两个更宽的口子**：
  1. **PROJECT-BRIEF 第十六章第一例直接失败**：「己所不欲，勿施于人」被谎称出自《孟子·梁惠王上》、以 `sage_key=mencius` 提交时，`verifiable=**True**`、`status=all_verified`。原因是 `SAGE_CLASSICS["mencius"]=["孟子"]`，出处串含"孟子"即通过学派检查；而**文本匹配只与 rag_refs 比子串，从不校验出处是否与文本一致**。这正是 brief 要求系统必须能区分的场景，当前**不能**。
  2. **2 字片段即判 verified**：「君子」→ `verifiable=True`。
- **证据**（独立脚本，真实 `citation_validator` + 真实 107 条 rag_refs）：
  ```
  1) 己所不欲勿施于人 谎称出自《孟子》 sage=mencius
     期望 verifiable=False  实际=True  status=all_verified   [!!! MISMATCH !!!]
  2) 真实短句 + 伪造长尾
     期望 verifiable=False  实际=True  status=all_verified   [!!! MISMATCH !!!]
  3) 两字片段「君子」
     期望 verifiable=False  实际=True  status=all_verified   [!!! MISMATCH !!!]
  4) 空出处 + 伪造文本          → False  status=unverified  [ok]
  5) 空出处 + 道德经冒充孔子     → False  status=unverified  [ok]
  ```
  另：纯假古文（A）、繁体（C）、网络鸡汤（E）均被正确判 `False` —— 说明**部分**对抗能力存在，不可全盘否定。
- **影响**：GATE-5「伪造引文放行 ≈ 0」当前**明确失败**。文档已判定该 Gate 不可达，方向正确；但 F-05 说明**即使**将来补上 QuoteVerifier，若只做"文本存在性"而不做"出处正确性"独立判定，第十六章第一例仍会失败。`02-architecture.md` §9.2 已冻结 `quote_exists` / `source_correct` 双字段（正确），此 finding 用于**强化该约束的必要性**。
- **requiredFix**：在 PHASE 5 的 P5-05 acceptance 中，除"单向子串 + 长度阈值"外，**必须**加入针对"真古文 + 错误出处"的显式测试用例（即 brief 第十六章第一例），并断言 `source_correct=false` 时 `trust_state=citation_corrected` 而非 `verified`。

### F-06【medium】PHASE 0 文档中的 V1 书目覆盖数字与事实不符（3/9 → 应为 4/8）

- **问题**：多处以「12 部中 **3 部**有数据 / **9 部**零语料」表述 V1 书目覆盖，但**实际为 4 部有数据 / 8 部零语料**。该数字与文档**自身引用的脚本输出**及**自身的覆盖表**均矛盾。
- **证据**：
  1. `00-current-state.md:71` 标题「V1 目标书目覆盖：12 部中仅 **3 部**有数据」；但紧接其下 `:76-87` 的脚本原始输出列出 **论语 110、道德经 4、墨子 4、韩非子 4** → **4 部**非零。
  2. `00-current-state.md:90-103` 的覆盖表同样列出《论语》《道德经》《墨子》《韩非子》**4 部**有语料。
  3. `00-current-state.md:26` 另称 L1「覆盖 **3 部**书」，而 L1 实含 论语/道德经/墨子/韩非子 **4 部**思想类书目。
  4. `01-gap-analysis.md:57`「12 部中 **9 部零语料**」、`:385`「§1.1（9 部零语料）」同样为 9，应为 **8**。
  5. 我独立运行文档引用的脚本并复算：
     ```
     $ python docs/kb-v1/audit/classical_audit_2_scale.py
     论语 110 / 道德经 4 / 墨子 4 / 韩非子 4  → 非零
     孟子 荀子 大学 中庸 庄子 商君书 传习录 孙子兵法 → 0
     books with data: 4 ; books zero: 8 ; total: 12
     ```
     独立复算亦为 `WITH data (4): ['论语','道德经','墨子','韩非子']`、`ZERO (8)`。
- **影响**：**不改变任何 Gate 结论**（无论 3 部还是 4 部，GATE-2/GATE-4 依然不可达），故定级 medium 而非 blocker。但 PHASE 0 文档的唯一价值就是"数字准确"，且该错误在 `00`/`01` 两处重复出现、并与文档自身表格/脚本输出自相矛盾——属必须修正的事实性错误，否则后续 Phase 会以错误基线做范围决策（例如 Q2「收窄到有数据的 N 部」）。
- **requiredFix**：把 `00-current-state.md:26`、`:71` 与 `01-gap-analysis.md:57`、`:385` 的「3 部 / 9 部」更正为「**4 部 / 8 部**」，并说明 4 部 = 论语、道德经、墨子、韩非子（其中道德经/墨子/韩非子各仅 4 条摘句）。

---

## 4. 对 PHASE 1–10 计划的可执行性评估

### 4.1 通过审查的部分

| 审查项 | 结论 | 依据 |
|---|---|---|
| **是否真增量（不重写）** | ✅ **通过** | `02-architecture.md` §1.2 逐项论证 8 项既有能力保留方式，且**我核对全部引用的行号/文件真实存在**：`main.py:199-228` 注册块、`rag_service.py` 4 个入口签名、`config.py:196-229`、`debate_engine.py:78-83`、`knowledge_graph.json`。§1.3 给出 5 条否决重写的实质理由（前端契约耦合、测试信号、索引已持久化、缺口在数据层、风险收益）。**未见推翻既有架构的意图。** |
| **PHASE 7 不早于 PHASE 1/5** | ✅ **通过** | `02-architecture.md:538-540` 明确"PHASE 7（前端）不得早于 PHASE 1（Schema）与 PHASE 5（Trust Layer）"；`03-task-dag.md:433` 复述"强依赖 PHASE 1 与 PHASE 5"。 |
| **EvidenceProvenance 字段冻结** | ✅ **通过** | `02-architecture.md` §9.1 冻结 15 个字段（book_id…proofread_status），且明确"前端必须透传、缺失即 `undefined`、**禁止回退到写死文案**"——直指 G-E 伪造证据根因。 |
| **TrustState 四态冻结** | ✅ **通过** | §9.2 冻结四态且**触发条件可自动化判定**：`verified`(exists∧correct)、`citation_corrected`(exists∧¬correct，须返回 correct_source)、`quote_relaxed`(归一化匹配)、`insufficient_evidence`(¬exists，禁止编造)。与 brief 第十一/十二章一致。 |
| **PHASE 9 串行 + 隔离前提** | ✅ **通过（且计划正确）** | `03-task-dag.md:330-365` 给出可执行 verify 块：先查进程 → 复制副本 → `CHROMA_PERSIST_DIR="./_regression_iso_chroma"` → 串行 pytest → 复核 143 → 清理。**我实测验证该路径选择正确**：绝对路径会破坏 `test_hackathon_readiness.py:23` 的 `startswith(backend_root)` 断言（我复现了该失败），而**相对路径下该测试 3 passed**。计划的判断准确。 |
| **PHASE 8 禁 FakeRag 冒充** | ✅ **通过** | `03-task-dag.md:34` 禁止 mock 冒充；并引 `test_hackathon_readiness.py:49/66`、`test_debate_sentence_evidence.py:14-31` 的 `FakeRAG` 为反例。我确认这些 FakeRAG 确实存在。 |
| **Gate 判据可自动化** | ✅ **大体通过** | §13 各 Gate 给出可执行命令与量化阈值（如 GATE-2 `passages_without_source = 0`、GATE-9 四项 exit 0）。未发现"无法验证的验收条件"。 |
| **质量类任务有 objective/acceptance/inScope/verify** | ✅ **通过** | P0R-01/02/03 三个 blocker 修复任务均含四要素，且 acceptance 具体到可断言（如 P0R-02"对语料外查询返回 0 条"）。**我实测该基线**：`asdfghjkl` 当前返回 `n=3 sims=[0.0,0.0,0.0]`，与 P0R-02 描述的"修复前返回 3 条"一致。 |
| **inScope 与现有文件冲突** | ✅ **通过** | 我实测 `services/retrieval`、`api/knowledge.py`、`schemas/knowledge.py`、`quote_verifier.py`、`data/sources`、以及 5 个新测试文件**全部不存在** → 无命名冲突。§14.3 给出文件级串行约束表，避免多写者。 |
| **Eval 诚实性** | ✅ **通过** | `03-task-dag.md:105` 明确"**禁止**把 `derived`/`synthetic` 标为 `human`，人工确认条数必须单独统计并披露"；`:119-120` E-08 强制断言 `expected_passage_ids` 真实存在于语料。**未发现"AI 样本冒充人工 Gold"**。 |
| **PHASE 0 写入边界** | ✅ **通过** | 见 §5。 |

### 4.2 必须修正项（进入 PHASE 1 前）

1. **F-01 + F-02（blocker）**：补齐后端测试环境并统一 verify 解释器。否则 PHASE 1 无法验收。
2. **F-03（high）**：补记 `'10.x'`/`'18.x'` 缺陷并明确处理方式。
3. **F-05（high）**：在 PHASE 5 acceptance 中加入"真古文 + 错误出处"显式用例。
4. **F-06（medium）**：更正 V1 书目覆盖数字「3 部/9 部」→「**4 部/8 部**」（`00:26`、`00:71`、`01:57`、`01:385`）。
5. **F-04（medium）**：把 `02` 的 Q6 承接进 `03` 的待决清单（或标注已由本报告处理）。

### 4.3 Gate 可达性复核（我独立判断，未调整任何目标数字）

| Gate | 目标 | 我的独立判断 | 依据 |
|---|---|---|---|
| GATE-4 Recall@5 | ≥90% | **不可达** | `retrieve()` 恒空（C1）→ 结构性无法测量；且 12 部目标书目 8 部零语料。属**数据缺口 + 缺陷**，非算法问题 |
| GATE-5 Quote Exactness / Source Attribution | ≥99% / ≥98% | **不可达** | 无 QuoteVerifier；`citation_validator` 仅双向子串，无出处独立判定（F-05 实测第一例即失败） |
| GATE-6 School Leakage | <1% | **不可达** | sage-chat 主路径无学派过滤（C2）；非儒家各派仅 3–4 条语料 + `score=0.25` 兜底使"无证据"不可达（C3） |
| GATE-8 拒答 / Claim Coverage / ≥200 Gold | ≥95% / ≥95% / 200 | **不可达** | 无 Trust State 四态、无 Claim-Evidence 绑定、`eval/` 不存在（0 条） |
| 性能 P50<1s / P95<3s | — | **当前可达，但无意义** | 我实测 `vector_search` P50≈1.9ms / P95≈3.8ms（30 次，隔离副本，不含外部 LLM）。但仅 143 条规模且 `retrieve()` 恒空，**不构成 RAG V2 的性能证据**，必须在 PHASE 4 后重测 |

**文档对上述可达性的判断与我的独立结论一致，且未修改任何目标数字。** 这一点是 GATE-0 通过的关键。

---

## 5. PHASE 0 写入边界核查

```powershell
$ git status --porcelain
?? docs/kb-v1/

$ git status --porcelain --untracked-files=no
(空)                       # 无任何 tracked 文件被修改

$ git diff --stat
(空)

$ (Get-FileHash docs/kb-v1/PROJECT-BRIEF.md -Algorithm SHA256).Hash
38F19DCA52E573864D6D0276B6B6E8E88D1E6E5C542B8DBD85F95D4A212366B0
```

- **PROJECT-BRIEF.md 未被修改**（SHA256 与 PHASE 0 开始时一致，长度仍 15817 B）。
- **产品代码 / 测试 / 数据未被修改**：`git status --porcelain -uno` 为空。
- **新增全部限于 `docs/kb-v1/`**（4 份文档 + 7 份审计 + 探针脚本 + 本报告）。
- **未 commit / push / deploy**。
- **真实索引未被破坏**：全程隔离副本，复核 `wudian_verses` 仍为 **143**；临时副本 `_regression_iso_chroma` 已删除。

**边界合规。**

---

## 6. 不可核验 / 证据不足清单（禁止用推断填充）

| 项 | 状态 | 原因 |
|---|---|---|
| 全部文本与权威底本（通行本）的一致性 | **未核验** | `ctext.org` / `zh.wikisource.org` 返回 `non-public IP address`；`web_search` 缺 `DEEPSEEK_API_KEY`。**我在自己这一层同样复现了该限制**，故此项**不可由本环境解决** |
| 语料是否为 LLM 生成 | **无法证实/否证** | 生成器 `build_lunyu.py` 为内置字典、无网络导入；`data/raw/` 为空且未被 git 跟踪。**缺证据链，不作断言** |
| 真实 LLM 回答质量 | **未验证** | `.env` 有 `LLM_PROVIDER=agnes` 但无 API_KEY；PHASE 0 未发起任何真实 LLM 请求 |
| 来源授权 / 版权 | **不存在** | 零 `license` 字段；无人工确认记录 |
| 市场 / 竞品结论 | **未核验假设** | 外部检索通道不可用。**不得写入 `00`/`01`/`02` 作为事实**（文档已如此处理） |
| `'言必信，行必果'` 归属（论语 13.20 vs 墨子·兼爱下） | **未裁决** | 仓库内自相矛盾；外部无法核验，**不替其裁决** |
| `lunyu 4.5`「不以其道得之，不去也」是否应作「去之」 | **未核验** | 外部通道不可用 |
| 朱熹注疏底本与点校版权 | **未核验** | 同上 |
| CI（GitHub Actions）实际是否通过 | **未验证** | 本地无法复现 3.12 + pytest-cov + ruff 组合 |
| PostgreSQL + pgvector 分支 | **未验证** | 本地仅 SQLite |
| `以德报怨` 是否在 L1 语料中 | **已复核（本报告新增结论）** | 见下 |

### 6.1 我完成的 `待 t9 复核` 项

`00-current-state.md:699` 标记「`以德报怨` 是否在语料中 — 待 t2/t9 复核」。**复核结论**：

- `data/processed/idioms.json:351-358` **有**该词条，且 `original_text` 为「或曰：以德报怨，何如？子曰：何以报德？以直报怨，以德报德。」并附正确释义「孔子实际上主张「以直报怨」」；
- 但该章句（论语 14.34）**不在** `lunyu.json` 的 L1 语料中（实测 `14.34` 不存在；`lunyu.json` 内检索「以德报怨/以直报怨/报德」均为 `False`）。
- **准确表述**：「`以德报怨` 存在于 `idioms.json` 的典故元数据层，但其出处章句不在 L1 原典语料中」。这解释了 brief 第十六章该用例为何当前无法正确回答——**不是判断错误，而是语料缺失**。

---

## 7. 未达标宣称完成 / 伪造行为核查

| 禁止项 | 核查结果 | 证据 |
|---|---|---|
| AI 生成古籍当权威原典 | ✅ **未发现** | 文档明确"无法证明/否证语料来源"（`00:692`），未把任何文本断言为权威底本 |
| 编造 source | ✅ **未发现** | 文档反复强调"零 source 字段、禁止编造"；`03:156` "无法核验的一律标 `unknown`，禁止编造" |
| mock 冒充真实 RAG | ✅ **未发现**（且被主动禁止） | `03:34` 禁 mock；`00:646-651` 主动**揭发**既有 `FakeRAG` 测试不构成真实 RAG 证据 |
| 降低断言 / 删测试 | ✅ **未发现** | `03:33` 明令禁止；`03:274` 要求占位断言"替换为真实断言或明确标注并停止计入覆盖" |
| 未达标却宣称完成 | ✅ **未发现** | 7 项指标判"不可达"、GATE-1/2/3/7/9/10 判"不可达"，**未改目标数字** |
| 修改目标数字假装 PASS | ✅ **未发现** | 所有 Gate 目标与 brief 第十七章一致 |

**未发现任何一类禁止行为。** 这是本报告给出 CONDITIONAL PASS 而非 FAIL 的决定性依据。

---

## 8. 审查方法局限（诚实声明）

1. 本报告**未**逐行复核 4 份文档的全部 2468 行；采用"抽查关键数字 + 复跑全部基线 + 对抗验证可信层 + 核对边界"的方式。未复核部分不构成背书。
2. 后端基线复跑受本机环境限制：**不存在**单一能跑完整套件的解释器。故"82 passed"是**系统 Python 且 chromadb 用例被 skip** 下的数字，不等于完整回归通过。
3. 性能测量在 143 条小索引 + 隔离副本上进行，**不可外推到 V1 规模**。
4. 本报告不评价 PHASE 1–10 的**技术方案优劣**（如 BM25 参数、reranker 选型），仅评价其**可执行性与验收可判定性**。

---

## 9. 结论摘要

- **GATE-0：CONDITIONAL PASS**
- **Blocker：2**（F-01 verify 命令不可执行；F-02 无环境修复任务）→ 均在计划层，可修复
- **High：2**（F-03 未记录的 `10.x`/`18.x` 数据缺陷；F-05 对抗验证发现的额外放行情形）
- **Medium：2**（F-04 `02` 的 Q6 未承接进 `03`；F-06 V1 书目覆盖数字 3/9 应为 4/8）
- **GATE-0 五项真实状态**：全部已列明并经独立验证一致
- **PHASE 0 写入边界**：合规（PROJECT-BRIEF 未变、tracked 文件零修改、仅新增 `docs/kb-v1/`）
- **伪造/降低标准行为**：未发现

**放行条件**：修正 F-01、F-02（必须），补记 F-03（必须），更正 F-06（必须）。在修正前**不得进入 PHASE 1 实施**。

**明确声明**：本结论**不表示项目完成**。PHASE 1–10 未开始；7 项 Gate 指标不可达；`eval/` 为空；零来源授权；外部核验通道不可用。项目远未达到 PROJECT-BRIEF 第二十三章的 DONE 定义。

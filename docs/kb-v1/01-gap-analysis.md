# PHASE 0 差距分析（Gap Analysis）

- 文档：`docs/kb-v1/01-gap-analysis.md`
- 任务：t11（product-research）
- 审计日期：2026-02-12（本地）
- 基准：`docs/kb-v1/PROJECT-BRIEF.md`
- 证据来源：`docs/kb-v1/audit/` 下七份专家审计报告（product-research / classical-knowledge / rag / trust / backend / frontend / evaluation）
- 性质：**只读分析**。未修改 backend/、frontend/、data/、PROJECT-BRIEF.md；未 commit/push/deploy。

## 阅读约定

- 严重度：`blocker`（阻断 Gate，必须先修）/ `high`（决定指标不可达）/ `medium` / `low`。
- 「所属 Phase」指该 gap 必须在哪个 Phase 解决，而非建议顺序。
- 每条 gap 均可追溯到审计证据或源码（给出 `文件:行号` 或可复现命令）。
- **市场/竞品结论一律不进入本文档作为事实**（外部核验在本环境不可用：web_search 无 API key、web_fetch 被拒）。相关自述保留在 `audit/product-research.md` §4，标记为「未核验假设」。
- **指标只作目标记录**。不可达的如实写明，不修改数字、不放宽公式。

---

## 0. 执行摘要

### 0.1 总体判断

当前代码基线与 PROJECT-BRIEF V1 的差距**不是"完成度不足"，而是三层结构性断裂**：

1. **数据层断裂**：V1 要求 12 部书目，**4 部有语料、8 部零语料**，且其中只有 1 部（论语 107 条）有实质规模。Passage Schema 29 字段中 23 个缺失，全部来源/授权/复核/分层字段为零。**没有任何一条 passage 能追溯到具体底本。**
2. **能力层断裂**：Evidence Pack、Citation Guard 白名单、Quote Verifier、Trust State、Claim-Evidence 绑定、Modern Issue Ontology —— PROJECT-BRIEF 第九~十三章要求的六项核心能力**全部为 0 实现**。
3. **可信层断裂**：`retrieve()` 恒空（C1）；检索永不返回空（C3）；默认对话路径不做任何引用校验（T-01）；citations 的 `verifiable` 硬编码为 `True`（T-02）；前端存在伪造的相关度与硬编码「已核验」（C-5/C-8）。**核心承诺「每个观点都能追到原典；找不到，就不硬编」当前双向失效。**

### 0.2 统计

| 项 | 数量 |
|---|---|
| 逐章对照条目（§1） | 15 章（第四~十九） |
| 单列高危 gap（§2） | **10 条**（G-A … G-J） |
| 其中 blocker | **3 条**（G-A、G-B、G-C） |
| 其中 high | **7 条**（G-D … G-J） |
| 明确不可达的 Gate 指标 | 7 项 |
| 当前可达的 Gate 指标 | 1 项（性能，但仅 143 条规模） |

### 0.3 三句话结论

1. **GATE-4/5/6/8 的多数指标在当前基线上结构性不可达**，原因是数据缺口 + 能力缺失，**不是算法调优问题**。
2. **在修复 G-A/G-B/G-C 之前，任何 RAG 指标测量都无意义**——测的是"抛异常→返回空"或"兜底注入的假证据"。
3. **PHASE 7（前端）不能早于 PHASE 1（Schema 来源字段）与 PHASE 5（Trust State）**，否则 Evidence Drawer 无字段可显示。

---

## 1. 逐章对照（第四 ~ 第十九章）

### 1.1 第四章 — V1 知识库范围（12 部书目）

| 项 | 内容 |
|---|---|
| **要求** | 优先支持 12 部：论语、孟子、荀子、大学、中庸（儒）；道德经、庄子（道）；墨子（墨）；韩非子、商君书（法）；传习录（后世）；孙子兵法（可选） |
| **现状** | 实测 `python docs/kb-v1/audit/classical_audit_2_scale.py`：论语 107 条、道德经 **4** 条、墨子 **4** 条、韩非子 **4** 条；孟子/荀子/大学/中庸/庄子/商君书/传习录/孙子兵法 **全部 0 条**。`classics_catalog.json` 声明 123 部书，但**实测 `any book with inline passages = 0`** —— 它只是书目元数据，不含正文。 |
| **差距** | 12 部中 **8 部零语料**（孟子、荀子、大学、中庸、庄子、商君书、传习录、孙子兵法）；**4 部有语料**（论语、道德经、墨子、韩非子）里，**3 部仅 4 条摘句**（道德经缺 ~95%、墨子缺 ~92%、韩非子缺 ~93%）；论语自身仅 107/512 章（缺 ~79%） |
| **语料内部关系（已完全枚举，lead-architect 复算 + 队长复核 + 本文件作者独立复现）** | `lunyu.json` 107 条 × `debate_classics.json` 21 条，归一化后**完全相等重复 0 条**；**部分包含恰好 1 对**：`debate_classics[confucius]`「士不可以不弘毅，任重而道远。」⊂ `lunyu.json` **8.7**「曾子曰：士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？死而后已，不亦远乎？」（不是「存在部分包含」，是**恰好 1 对**） |
| **`论语 110` 的构成** | **107（`lunyu.json`）+ 3（`debate_classics[confucius]`）= 110**。其中**恰 1 条为上条的部分包含**（`lunyu-taibo-01` → 8.7），**另 2 条为独立摘句**：`lunyu-shuer-01`「用之则行，舍之则藏。」、`lunyu-weilinggong-01`「君子谋道不谋食。」。这解释了为何按书目归并的脚本显示「论语 110」而 `lunyu.json` 实为 107 |
| **占位符 `verse_id`（新增缺陷，t9 F-03）** | `lunyu.json` 107 条中 **2 条 `verse_id` 为占位符**（非 `章.节` 格式）：**`10.x`**（乡党 / 恂恂如也）、**`18.x`**（微子 / 凤兮凤兮），且**已进入向量索引**（`verse_no` 亦为 `'10.x'`/`'18.x'`）。复现：<br>`python -c "import json,re;d=json.load(open('data/processed/lunyu.json',encoding='utf-8'));print([v['verse_id'] for c in d['chapters'] for v in c['verses'] if re.search(r'\.x$',v['verse_id'])])"`<br>→ `['10.x', '18.x']` |
| **影响** | ①GATE-2 无法通过；②多学派差异无数据基础（见 G-D）；③Recall@5 上限被语料量硬约束；④**部分包含的 1 对**：若摘句与 8.7 均作为独立 L1 passage 入库，同一句将有**两个 `passage_id`**，Quote Verifier 的 `quote_exists` 候选集会出现重复来源，`02-architecture.md` §9 的 `candidates[]` 需表达「同一 passage 的全句与摘句」关系；⑤**占位符 `10.x`/`18.x`**：使 `03-task-dag.md` 的 **Q1 方案 (c)**（拆 `chapter_no` + `section_no`）**无法解析**这两个 id，且 PHASE 2 的论语迁移（P2-02）会**静默**把占位符带入 L1 `knowledge_passage`，须在 ingestion 增加 id 格式校验并显式拒绝或映射 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 2（Core Corpus） |

### 1.2 第五章 — 五层知识结构 L1–L5

| 项 | 内容 |
|---|---|
| **要求** | L1 权威原典 / L2 历代注疏 / L3 人物·学派·概念 / L4 思想概念 / L5 现代问题；**禁止把这些层混成普通 chunk** |
| **现状** | L1：论语 107 + debate_classics 21（含 6 条非思想类文学人物：李白 2、苏轼 1、范仲淹 1、王安石 1、诸葛亮 1）。L2：朱熹一家 **15 条**。L3：`knowledge_graph.json` 21 node（16 人物 + 5 概念）/ 24 edge，**16 人物全为儒家一系，无老子/庄子/墨子/韩非**。L4：67 个自由文本 tag，**无受控词表**。L5：`scene` 36 / `modern_usage` 39 / `modern_interpretation` 22 等，**全为自由文本散文，无枚举** |
| **差距** | ①**无 `text_type` 字段**，L1/L2 仅靠"文件位置 + `doc_type` 字符串约定"区分；②L3 是"儒家单线"图谱，用它做 `school` filter 会**系统性漏检道家/墨家/法家**；③L4 与 L3 的 5 个 concept 节点**互不关联**；④L5 无法用于结构化查询；⑤**D 级 AI 内容与 L1 原典无等级区分** |
| **影响** | 违反第五章"禁止混成普通 chunk"；metadata filter（Stage 4）无可用字段；第十四章 A/B/C/D 分级无数据基础 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 1（Schema）+ PHASE 2（语料）+ PHASE 3（Ontology） |

### 1.3 第六章 — Passage Schema（29 字段）

| 项 | 内容 |
|---|---|
| **要求** | 29 个字段，含 `passage_id`、`book_id/book_title`、`chapter_id/chapter_title`、`section/line_no`、`original/original_traditional/original_simplified`、`source_provider/source_url/source_edition`、`author/dynasty`、`text_type`、`commentator/commentary_dynasty`、`school`、`concepts[]/modern_topics[]/modern_scenarios[]`、`stance`、`verification_level`、`proofread_status`、`license`、`embedding_version`、`created_at/updated_at`；**原典和注疏必须分开储存** |
| **现状** | 实测判定表（`audit/classical-knowledge.md` §2.3）：**仅 6 个以结构化形式存在**（`chapter_id`、`chapter_title`、`original`、`author`、`dynasty`、`created_at`/`updated_at`，且后三者仅在 `lunyu.json` 容器级）。**23 个缺失** |
| **差距** | ①**全部来源字段缺失**（`source_provider`/`source_url`/`source_edition`）→ 无一条 passage 可追溯底本；②**全部授权字段缺失**（`license`）；③**全部复核字段缺失**（`verification_level`/`proofread_status`）→ 无人工复核记录（全文检索 `校对/复核/人工/审定/proofread/verified/reviewed` **零命中**）；④**分层字段 `text_type` 缺失**（最严重）；⑤`passage_id` 无统一 ID——`verse_id` 只覆盖论语，`debate_classics` 用 `daodejing-08-01` 另一套空间，注疏用 `verse_id`，**三套不统一**；⑥`school` 缺失（`debate_classics` 各派容器 `v.get("school") → None` × 9）；⑦原文/译文/注释混在同一 chunk（`rag_service.py:314` 拼 `【篇章】【原文】【译文】【注释】`），**且这是当前 RAG 的直接输入** |
| **影响** | GATE-2「所有 passage 必须有 source」无法通过；Quote Verifier 无 `passage_id` 可返回；Evidence Pack 无字段可填 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 1 |

### 1.4 第七章 — Modern Issue Ontology（21 类情境）

| 项 | 内容 |
|---|---|
| **要求** | 至少覆盖 21 类：career / workplace_conflict / leadership / achievement / money / competition / family / parent_child / marriage / friendship / anxiety / failure / anger / loneliness / self_doubt / choice / responsibility / justice / fairness / meaning / ambition。用户输入**不能直接丢给 embedding**，须先结构化（scene / actors / conflict / emotion / choices / concepts） |
| **现状** | **完全不存在**。现有最接近的是 `lunyu_quotes.scene`（36 条自由文本）、`idioms.modern_usage`（39 条散文）、`theater_scripts.modern_setting`（职场/校园，6 条）。无枚举、无本体、无 `modern_scenarios` 结构化字段 |
| **差距** | 21 类情境 0 实现；scene/actors/conflict/emotion/choices/concepts 六要素 0 实现；无 scenario→concept 映射表 |
| **影响** | Stage 2（Modern→Classical Query Expansion）无输入；GATE-3（≥50 个现代问题分类测试）无被测对象 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 3 |

### 1.5 第八章 — RAG V2（Stage 1–7）

| Stage | 要求 | 现状 | 判定 | 增量策略 |
|---|---|---|---|---|
| 1 | Query Analyzer | 无。仅 `_expand_synonyms`（`rag_service.py:503-509`）字符串拼接 | **缺失** | 新增独立模块 |
| 2 | Modern→Classical Query Expansion | `SYNONYM_MAP` **52** 条词级替换；PROJECT-BRIEF 示例问题 **0 命中** | **部分**（不足以支撑第七章） | 新增概念映射层，保留 `SYNONYM_MAP` 作 fallback |
| 3 | Hybrid: BM25 + Dense | `hybrid_search` 存在但**恒返回 `[]`**（G-A）；`keyword_search` 非 BM25（无 IDF/长度归一化，且只用 `keywords[0]`，`rag_service.py:843`）；Dense 为 **hash 非语义** | **形式有、实质无** | 先修 G-A，再新增真 BM25 + 语义 embedding |
| 4 | Metadata Filtering | **无**。`scope`/`school`/`book`/`text_type`/`concept` 均未用于过滤（`rag_service.py:812-816`） | **缺失** | 新增过滤层（`scope`/`sage_key` 已在 metadata，可复用） |
| 5 | Reranker | **无** | **缺失** | 新增 |
| 6 | Diversification（禁止 Top5 同章） | **无** | **缺失** | 新增 MMR / 同章去重 |
| 7 | Evidence Pack | **无** `EvidencePack` 结构；`build_sage_chat_context`（`rag_service.py:1020`）拼字符串 | **缺失** | 新增，`build_*_context` 保留作兼容 |

**embedding 现状**：`RAG_EMBEDDING_PROVIDER = "local"`（`config.py:86`）→ `LocalHashEmbeddingFunction`，384 维，blake2b 哈希分桶，**非语义模型**。实测稀疏性：5 字短语仅 9/384 维非零。语义边界（`audit/rag.md` §3）：

```
-0.0334  '同事抢了我的功劳我该不该撕破脸' vs '君子喻于义小人喻于利'
+0.6974  '同事抢了我的功劳我该不该撕破脸' vs '同事抢了我的功劳'   (字面重叠)
+0.0000  '我很焦虑怎么办' vs '君子坦荡荡小人长戚戚'              (语义相关→0)
+0.2010  '学而时习之' vs '學而時習之'                          (繁体/简体)
```

- **严重度**：Stage 1/2/4/5/6/7 缺失 = **blocker**（Stage 3 部分 = high）
- **所属 Phase**：PHASE 4
- **必须新增而非改写**：Stage 1/2/4/5/6/7 与 `EvidencePack`
- **必须保留**：`RAGService` 单例、`retrieve_for_sage_chat`、`retrieve_for_debate_sage`、`build_sage_chat_context`、`build_debate_context`、`is_low_confidence` 的对外签名（第十九章）

### 1.6 第九章 — Evidence Pack

| 项 | 内容 |
|---|---|
| **要求** | 生成 `EvidencePack { query, scenario, concepts, evidence[{evidence_id, original, source, school, text_type, commentary, relevance, verification}] }`；**LLM 只能引用 Evidence Pack 中存在的 source** |
| **现状** | **不存在**。无 `EvidencePack` 模型（`backend/app/schemas/` 无 `knowledge.py`）；`build_sage_chat_context` 把结果拼成**字符串**注入 prompt（`rag_service.py:1020-1048`） |
| **差距** | 8 个 evidence 字段 0 实现；无 `evidence_id`；无白名单约束 |
| **影响** | 第十章 Citation Guard 失去前置依赖；LLM 可直接引用检索结果之外的 source |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 4（生成）+ PHASE 5（消费） |

### 1.7 第十章 — Citation Guard 白名单

| 项 | 内容 |
|---|---|
| **要求** | Quote 必须 ①存在于 Evidence Pack，或 ②被 QuoteVerifier 在原始知识库中精确找到；否则 `verifiable=false`，**不得展示成「经典原文」** |
| **现状** | **无白名单**。`_match_citation` 把 `原文` 与本次 `rag_refs` 做双向子串比对（`citation_validator.py:83-91`），构成一个很弱的「文本在本次检索结果内」约束，但**作用在 `原文` 上，不作用在 `出处` 上**。且默认对话路径（SSE，`stream` 默认 `True`，`schemas/ai.py:98`；前端固定 `stream: true`，`api.ts:1064`）**完全不做任何引用校验**，逐字转发 LLM 输出 |
| **差距** | ①无白名单；②**5 处硬编码 `verifiable=True`**：`api/ai.py:146,159,208,265`、`ai_service.py:424`；③`schemas/ai.py:109` 与 `schemas/debate.py:100` 的 `verifiable` 默认值为 `True`；④默认路径不校验；⑤空 `出处`/`"无"` 使跨派检查直接放行（`citation_validator.py:99-100`，实测 C10 `verifiable=True`） |
| **影响** | T-01/T-02/T-05 漏洞；核心承诺「找不到就不硬编」失效 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 5 |

### 1.8 第十一章 — Quote Verifier

| 项 | 内容 |
|---|---|
| **要求** | 新增 `POST /api/knowledge/verify-quote`；输入 `{quote, claimed_source}`；输出 `{quote_exists, exact_match, source_correct, correct_source, similarity, trust_state}`；**必须区分「这句话存在」与「出处正确」两个指标** |
| **现状** | **接口不存在**。实测 OpenAPI 导出：**81 个 path，无 `/api/knowledge/*`**；`app/` 全目录搜索 `api/knowledge|verify.quote|trust_state|whitelist` → **零命中**。**两个指标完全未区分**：`Citation` 只有单一布尔 `verifiable`（`schemas/ai.py:103-111`、`schemas/debate.py:95-102`）；`_match_citation` 全程只读 `原文`，从不读 `出处`（`citation_validator.py:71-93`）；全仓不存在 `quote_exists`/`source_correct`/`correct_source`/`trust_state` 标识符 |
| **差距** | 接口 0 实现；两指标 0 实现。实测证据：**C7**（真实古文+同派错误篇章 `《论语·学而》`）→ `verifiable=True, all_verified`，**错误出处被完全放过并原样保留**；**C2** 被拦下不是因为发现出处错，而是因为「孟子」不在孔子书名白名单——**该拦截不具备出处正确性语义** |
| **影响** | GATE-5 的 Source Attribution ≥98% 无实现基础；`citation_corrected` 状态无法产生 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 5 |

### 1.9 第十二章 — Trust State（四态）

| 项 | 内容 |
|---|---|
| **要求** | 所有 AI 回答必须存在 `trust_state`，至少 `verified` / `citation_corrected` / `quote_relaxed` / `insufficient_evidence`；无可靠证据时必须输出「当前知识库没有检索到足够可靠的原典支持这一判断。」 |
| **现状** | **无**。全仓 grep `trust_state\|trustState\|insufficient_evidence\|quote_relaxed\|citation_corrected` → **零命中**。最接近的是 `CitationValidator.validate` 的三值字符串 `all_verified/partial_verified/unverified`（`citation_validator.py:64-67`），**且该状态在 debate 链路被全部丢弃**（`debate_engine.py:391,502,579,730` 均写作 `_, _ = ...`）。空引用时语义错误：`validate("confucius", [], []) → 'all_verified'`（初值 `True`，`citation_validator.py:42`）。前端 `citationStatus` 三态（`thoughtCourtState.ts:7`）由前端自行推算（`thoughtCourtSession.ts:66`），非后端判定 |
| **差距** | 四态 0 实现；拒答文案 0 实现；**且 G-B 使 `insufficient_evidence` 路径结构性不可达** |
| **影响** | GATE-5/GATE-8 拒答指标无实现基础；第十四章 A/B/C/D 无 Trust 落点 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 5 |

### 1.10 第十三章 — Claim Evidence

| 项 | 内容 |
|---|---|
| **要求** | 最终答案拆成 claim，每个核心思想结论必须有 evidence 绑定与 verification 状态 |
| **现状** | **无 claim 级绑定**。现有 `sentence_evidence`（`debate_engine.py:130-155`）是「按句检索」：把发言按 `。！？` 切句，**每句单独检索 top_k=1**，判定为 `verifiable=bool(refs and original != "无" and source != "无")`（`debate_engine.py:149`）—— **不比较句子与原文之间是否存在任何文本关系** |
| **差距** | ①无 claim 拆分；②无 claim→evidence→verification 链路；③`verifiable` 判定**严重误报**。实测（`audit/trust.md` §5.2）：`今天天气不错，我打算去打球。` → `verifiable=True`，绑定到 `《论语·卫灵公》君子谋道不谋食`；`股价暴跌让我很焦虑。` → `verifiable=True`，绑定到 `《论语·述而》用之则行，舍之则藏` |
| **影响** | GATE-8 Core Claim Evidence Coverage ≥95% 无实现基础 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 5 |

### 1.11 第十四章 — 数据质量等级 A/B/C/D

| 项 | 内容 |
|---|---|
| **要求** | A 权威文本+人工确认 / B 权威来源+机器处理 / C 来源可靠但尚未复核 / D AI 解释；**前端不得把 D 和 A 显示成同一等级** |
| **现状** | **无任何等级字段**。全仓 grep `qualityGrade\|verification_level\|可信等级\|数据质量` → **前端 0 命中**；后端也无 `verification_level`/`proofread_status`。且**无人工复核记录**（全文检索 `校对/复核/人工/审定` **零命中**）→ 现有全部语料**只能定为 C 级或 D 级，不能定为 A 级** |
| **差距** | 等级体系 0 实现；D 级内容（`quote_cards.modern_interpretation`、`comics`、`theater_scripts.moral`）与 L1 原典**在数据上无区分**；前端把 mock 与精选案例以「已核验」呈现（C-8） |
| **影响** | 直接违背「前端不得把 D 和 A 显示成同一等级」 |
| **严重度** | **high** |
| **所属 Phase** | PHASE 1（字段）+ PHASE 5（判定）+ PHASE 7（展示） |

### 1.12 第十五章 — 七类 Eval

| 项 | 内容 |
|---|---|
| **要求** | 创建 `eval/`：`retrieval_gold.jsonl`、`quote_verification.jsonl`、`source_attribution.jsonl`、`modern_to_classic.jsonl`、`school_consistency.jsonl`、`adversarial_quotes.jsonl`、`unsupported_questions.jsonl`；第一阶段允许 ≥200 条高质量 Gold Set，但**必须设计扩展到 1000 条的脚本和 Schema** |
| **现状** | **`eval/` 目录不存在**（实测 `Test-Path eval → False`）；**0 条样本**；无 JSONL Schema；无生成脚本；无指标计算脚本 |
| **差距** | 7 类数据集 0 实现；0/200 条 Gold；无扩展方案 |
| **影响** | GATE-4/5/6/8 全部无法测量 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 8（Schema 可在 PHASE 4 前置定义） |

### 1.13 第十六章 — 12 条对抗测试

| 项 | 内容 |
|---|---|
| **要求** | 必须能区分：己所不欲是否孟子 / 上善若水是否庄子 / 孔子怎么看职场PUA / 韩非子会建议我辞职吗 / 老子说努力就一定成功吗 / 以德报怨出自孟子吗 / 假古文 / 真古文+错误出处 / 同句不同标点 / 繁体 / 部分引用 / 网络鸡汤冒充孔子 |
| **现状** | **无对抗测试套件**。`citation_validator` 的实测对抗结果（`audit/trust.md` §1.2，另经队长与 qa-reviewer 独立复现）：C1 伪造古文 → 正确拦截；C2 真古文+错出处（跨书）→ 拦截但**语义错误**；C3 同句不同标点 → **误判假阴性**；C4 繁体 → **误判假阴性**；C5 部分引用 → 命中；C6 网络鸡汤 → 正确拦截；**C7 真古文+同派错误篇章 → 未拦截**；C8 真古文但未进本次 rag_refs → **误判假阴性**；**C9 真实短句内嵌伪造长文 → 未拦截（`verifiable=True`）**；**C10 空出处 → 未拦截** |
| **首要失败例证（已实测确认，brief 明列的第一条对抗用例）** | **brief 第十六章第一例「己所不欲勿施于人是不是孟子说的？」直接失败。** 实测：`citation_validator.validate("mencius", [{"出处":"《孟子·公孙丑上》","原文":"己所不欲，勿施于人。"}], refs=[真《论语·卫灵公》文本])` → **`verifiable=True`、`status=all_verified`**，且错误出处 **《孟子·公孙丑上》被原样保留**。根因：①`SAGE_CLASSICS["mencius"]=["孟子"]`（`citation_validator.py:18-30`）使**学派检查通过**；②`_match_citation`（`citation_validator.py:70-93`）只把原文与 `rag_refs` 比子串，**从不校验出处是否与文本一致**；③`_check_classic_belonging` 在出处为空时直接 `return True`（`:99-100`）。另有「同书错篇」（C7）与「空出处」（C10）同样被放行 |
| **差距** | 12 条中至少 **5 条当前判定错误**（C3/C4/C7/C8/C9/C10），**含 brief 明列的第一条**。另实测：`以德报怨`/`报怨以德` 在语料中 **0 命中**（无法验证"是否孟子"）；`事在四方` 0 命中。**公平表述**：纯假古文、繁体、网络鸡汤三类**被正确判 False**，故对抗能力**部分存在、并非全盘失效** |
| **影响** | GATE-5「任何明显伪造名言通过验证即 FAIL」当前**极可能失败**。本失败例**强化** `02-architecture.md` §9.2 已冻结的 `quote_exists` / `source_correct` 双字段必要性——单一布尔 `verifiable` 无法表达「文本真而出处假」 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 5（实现）+ PHASE 8（套件） |

### 1.14 第十七章 — 质量指标（Gate Target）

| 指标 | 目标 | 当前可达性 | 依据 |
|---|---|---|---|
| Quote Exactness | ≥ 99% | **不可达** | 无 QuoteVerifier；`citation_validator` 仅子串匹配，无繁简/标点归一化、无出处独立判定 |
| Source Attribution | ≥ 98% | **不可达** | 无独立「出处正确性」指标（现状只返回 `verifiable` 布尔） |
| School Leakage | < 1% | **不可达** | 非儒家各派仅 3–4 条语料；`score=0.25` 兜底使跨派风险高；无泄露测试（详见 G-D） |
| Retrieval Recall@5 | ≥ 90% | **不可达（且当前无法测量）** | `retrieve()` 恒空（G-A）；语料 128 条原典、仅 1 部完整书 |
| Unsupported Correct Refusal | ≥ 95% | **不可达** | 无 Trust State，无 `insufficient_evidence` 状态；且 G-B 使其路径不可达 |
| Core Claim Evidence Coverage | ≥ 95% | **不可达** | 无 Claim-Evidence 绑定实现 |
| Fabricated Classical Quote | ≈ 0 | **当前极可能失败** | 双向子串包含可被「伪造长文内嵌真实短句」绕过（C9 实测 `verifiable=True`） |

**结论**：7 项指标中 **7 项当前不可达**。原因是**数据缺口 + 能力缺失**，非算法调优问题。**不得修改目标数字、不得放宽公式、不得用 mock 或占位断言冒充通过。**

- **严重度**：**blocker**
- **所属 Phase**：PHASE 4/5/6/8 联合

### 1.15 第十八章 — 性能要求

| 项 | 内容 |
|---|---|
| **要求** | RAG 本地 P50 < 1s、P95 < 3s（不含外部 LLM）；索引必须持久化；启动不得每次全量重建 |
| **现状** | **实测远优于目标**（warm，40 次/方法，不含外部 LLM）：`vector_search` P50=1.3ms/P95=1.7ms；`keyword_search` P50=1.7ms/P95=2.4ms；`retrieve_for_sage_chat` P50=2.2ms/P95=2.9ms；`retrieve_for_debate_sage` P50=2.7ms/P95=3.5ms。冷启动（首次构造 `RAGService`）P50=48.0ms/P95=119.9ms。索引已持久化（`chroma.sqlite3` 4.1MB，collection `wudian_verses` = 143 条），**启动不重建** |
| **差距** | ①`retrieve` 的 4.3ms **不代表检索有效**——测的是"抛异常→返回空列表"的耗时；②**该基线是 143 条文档规模下的结果**，引入语义 embedding 与 reranker 后必然显著上升；③**无索引版本管理**（无 `embedding_version`；换 embedding 后不会失效重建，`_collection_has_persisted_debate_classics` 只检查 `scope=debate_classic` 是否存在，`rag_service.py:592-605`）；④metadata 截断 200 字符（`rag_service.py:533-534,691-692,722-723`），注疏文本超 200 字即被静默截断，会破坏逐字引用校验；⑤B2：`CHROMA_PERSIST_DIR` 相对路径依赖 CWD，以仓库根启动会创建**空的新索引**并静默降级，而健康检查仍报 `rag_available`（见 G-C） |
| **影响** | 性能当前**无风险但未验证**；G-A 使该指标失去意义 |
| **严重度** | **medium**（性能本身）/ 但 B2 相关为 **blocker**（见 G-C） |
| **所属 Phase** | PHASE 4（重测） |

### 1.16 第十九章 — 兼容性

| 项 | 内容 |
|---|---|
| **要求** | 已有 API 尽量保持兼容；已有 Debate「问证辩判」不能删除；Evidence Pack 应增强「证」；Trust State 应增强「判」 |
| **现状** | 已有 81 个 path。**必须保持不变**（有真实调用方）：`POST /api/ai/chat-sage` 的 SSE 事件格式（`chapters`/`content`/`citations`/`[DONE]`）、SSE citations 中文 key（`id/出处/原文/chapter/translation/verifiable`）、非流式 `ChatSageResponse`、`POST /api/ai/explain` 的 `VerseExplanation`、`POST /api/auth/refresh`、`POST /api/debate/{id}/{action}?stream=true`、`SageSpeech.citations/sentence_evidence/quote/source`、`GET /health` 的 `llm_available/rag_available/rag_count/...`、`verifiable: bool`（可扩展不可删）、`confidence`/`honest_note` |
| **差距** | 前端实际调用的后端端点**只有 3 类**（`/ai/chat-sage`、`/auth/refresh`、`/debate/`），故 community/content/learning/exploration 等大量端点的兼容性风险低于表面。**可安全扩展**：`Citation`/`SentenceEvidence` 新增可选 `trust_state`/`evidence_id`/`verification_level`/`text_type`/`commentator`；`RAGReference` 新增 `passage_id`/`school`/`source_provider`（Pydantic 默认忽略额外输入，新增带默认值字段向后兼容） |
| **影响** | 无阻断；但 G-A 的修复方式需二选一并记录（改 schema 为 `Optional[str]`，或改写入侧为整数——后者需重建索引且丢失 `"1.1"` 的章.节语义） |
| **严重度** | **low** |
| **所属 Phase** | 全阶段遵守 |

---

## 2. 高危 gap 单列（G-A … G-J）

### G-A【blocker】`retrieve()` 恒空 → GATE-4 的 Recall@5 当前**结构性为 0**

| 项 | 内容 |
|---|---|
| **机制** | `backend/app/schemas/ai.py:17` 声明 `verse_no: Optional[int]`；索引中 `verse_no` **全部为字符串**（`'1.1'`、`'15.16'`、`'daodejing-33-01'`），写入点 `rag_service.py:325,532,690,721`；`rag_service.py:897` 构造 `RAGReference(verse_no=r["metadata"].get("verse_no"))` → pydantic `int_parsing` 校验失败；`retrieve()`（`rag_service.py:906-912`）用 `except Exception` 吞掉异常并 `return []` |
| **量化** | `stored verse_no values: total=143 non-integer=143 integer=0`；`RAGService.retrieve(): 32/32 queries returned ZERO references`（t3）；`retrieve()` 12/12 查询返回空（t7）；我本人复现 5/5 全 `n=0`（t1）。**四方互证** |
| **影响面** | `POST /api/ai/retrieve`（`api/ai.py:326`）恒返回空 `results`；生成 quiz 的 `references`（`:305`）恒空；`explain_verse` 的 RAG 上下文（`ai_service.py:99`）恒为「（无匹配原文）」；`ai_service.py:563` 同上；`is_low_confidence()`（`rag_service.py:1077`）**恒返回 True** → `DISCLAIMER_LOW_CONFIDENCE` 成为**无条件输出**而非低置信度信号 |
| **关键澄清** | 未受影响的是 `retrieve_for_sage_chat` / `retrieve_for_debate_sage`（返回 dict，不经 `RAGReference`）。**这正是现有测试全部通过的原因**——测试只覆盖 dict 路径，`retrieve()` 路径**零测试** |
| **影响** | GATE-4 的 Recall@1/3/5 与 MRR **当前无法测量**（不是"偏低"）；第十八章性能指标失去意义 |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 4 前置（或 PHASE 1 收尾） |
| **要求** | 修复类型不匹配 **并补 `retrieve()` 回归测试**（否则会再次静默失效）；修复方式二选一并在架构文档记录 |

### G-B【blocker】`score = 0.25` 兜底使「检索不到」不可达 → 违反核心承诺，GATE-5 的 `insufficient_evidence` 路径不可达

| 项 | 内容 |
|---|---|
| **机制** | `rag_service.py:493-498`：`if score == 0: score = 0.25`，随后**无条件 append**。即任何查询在任何派别索引上**必然返回结果** |
| **量化** | `query='zzzz完全不相关的问题xyz'` → 3 verses（sims 0.099/0.082/0.051）；`query='量子计算机如何优化神经网络'` → 3 verses（0.071/0.037/0.0）；`query='asdfghjkl'` → 3 verses（**0.0/0.0/0.0**）。我本人复现：`如何面对亲人的离世？` 在孔子/老子/墨子/韩非子四条路径**均返回 3 条**（sims 0.0–0.066） |
| **连带后果** | 孔子 fallback 是**死代码**——因 L1 永不返回空，`rag_service.py:1006-1007` 分支不可达（清空 `_debate_classic_index` 后结果完全一致） |
| **影响** | ①系统**不会拒答**，而是把 0.0 相似度的段落当作「检索到的原典」注入 prompt；②`insufficient_evidence` 状态**结构性不可达**；③`_bind_sentence_evidence` 因此对无关句恒判 `verifiable=True`（见 §1.10）；④这属于**「用 mock 假装真实 RAG 成功」的变体** |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 4 前置 + PHASE 5 |
| **要求** | 移除无条件兜底，改为显式返回空并由 Trust Layer 判定 `insufficient_evidence` |

### G-C【blocker】空索引仍报 `rag_available` 且无降级兜底

| 项 | 内容 |
|---|---|
| **机制** | ①`rag_service.py:237` 用 `settings.CHROMA_PERSIST_DIR`（相对 `'./chroma_db'`），而 `main.py:39` 用 `Path(settings.resolved_chroma_persist_dir)`（绝对）。实测：`CWD=backend` → 真实索引；`CWD=repo root` → `D:\systemDir\Desktop\悟典\chroma_db`（**不同且不存在**）。②`is_available` 只判断 `collection is not None or len(_file_index) > 0`，**不判断 count > 0**，因此**空索引也报 available**。③`main.py:148-159` 健康检查读同一实例，故 `rag_available` 与 `rag_count` 会报「可用 + 0 条」或掩盖问题 |
| **连带后果** | `_file_index`/`_commentary_index` **仅在 `HAS_CHROMADB=False` 分支加载**（`rag_service.py:231-233`）；chromadb 可用时二者为 **0**（实测 `file_index=0 commentary_index=0`）→ `vector_search` 的降级路径 `_file_keyword_search`（`:809`）在查询失败时返回 **0 条**，**降级形同虚设** |
| **影响** | 以仓库根启动后端会**静默降级为空检索**，而健康检查仍报 `rag_available`；CI 的 `working-directory: ./backend` 使该缺陷在 CI 中**不可见** |
| **严重度** | **blocker** |
| **所属 Phase** | PHASE 4 前置 |
| **要求** | 改用 `settings.resolved_chroma_persist_dir`；`is_available` 纳入 count 判断；始终加载文件索引作 fallback |

### G-D【high】sage-chat 无学派过滤 → GATE-6 School Leakage < 1% 不可达

| 项 | 内容 |
|---|---|
| **机制** | `retrieve_for_sage_chat`（`rag_service.py:914-990`）调用 `vector_search`（`:801-820`），后者 `collection.query` **不带 `where` 过滤** → 返回全库结果。而 `retrieve_for_debate_sage`（`:992-1009`）**有** `sage_key` 过滤（隔离已验证有效） |
| **量化（我本人复现）** | 孔子对话路径问「上善若水，水善利万物而不争」→ 第 1 位是 **`《道德经·第八章》`（0.68）**；「兼相爱，交相利」→ 第 1 位 `《墨子·兼爱上》`（0.519）；「法不阿贵，绳不挠曲」→ 第 1 位 `《韩非子·有度》`（0.52）。另实测「我该不该躺平」top-5 含 `scope=debate_classic` 的《论语·述而》（t3 L2） |
| **校验不对称** | `citation_validator.validate()`（**含**学派检查）仅用于 debate（`debate_engine.py:391,502,579,730`）；`ai_service._validate_citations()`（**不含**学派检查）用于 sage chat（`ai_service.py:519`）。因此 sage-chat 路径**完全不做归属检查** |
| **UI 不可识别** | 即使后端判定跨派并置 `verifiable=False`，前端也**没有学派维度的呈现**；用户只会看到该条引用从列表消失或变成「待核验」，无法得知「孔子引了《韩非子》」（C-17） |
| **附加风险** | `_check_classic_belonging` 在 `source` 为空/`"无"` 时**返回 True（放行）**（`citation_validator.py:99-100`，实测 `src=''`/`'无'`/`'<missing>'` 全部 `belongs=True`）→ **不填出处即可绕过学派归属检查** |
| **影响** | GATE-6 跨派引用泄露率 < 1% 不可达；且非儒家各派仅 3–4 条语料，检索必然大量回退到 G-B 的兜底 |
| **严重度** | **high** |
| **所属 Phase** | PHASE 4（检索层过滤）+ PHASE 6（验证） |

### G-E【high】前端伪造证据（零语料书目 + 硬编码可信标记）

| 项 | 内容 |
|---|---|
| **要求** | 「每个观点都能追到原典」；前端不得把无来源数据展示为「已核验」 |
| **证据 1 — `roundtableData.ts`（我本人实测）** | 共 **32** 条引用，书目分布：论语 7、**孟子 8**、**传习录 8**、道德经 3、墨子 3、韩非子 3。**其中 16 条（孟子 8 + 传习录 8）出自当前零语料书目**。全部 `similarity` **硬编码 0.87–0.97**（如 `:138` `similarity: 0.96`）。按归一化文本比对，**22/32 条无法在当前语料中定位** |
| **证据 2 — `sageData.ts`** | `localSageCitations` 共 **19** 条，书目分布：论语 4、孟子 3、传习录 3、道德经 3、墨子 3、韩非子 3。**6 条出自零语料书目**；按归一化比对，**10/19 条无法核验**（含 `《韩非子·扬权》事在四方，要在中央`、`《传习录》致良知`、`《孟子》我善养吾浩然之气` 等）。`similarity` 为**手写常量 0.78–0.95**（`sageData.ts:106-137`），非检索得分 |
| **证据 3 — 展示路径** | `SageChat.tsx:167-182` 的 `catch` 块在真实请求失败时调用 `getLocalSageCitations(sage.id)` 并经 `onCitationsChange` / `setMessages` 推给用户；`CitationSidebar.tsx:83` 标题为 **「本次可溯源证据」**，`:214` 显示 **「相关度 N%」** |
| **关键区分（必须注意）** | `generateSageReply` 生成的**正文**末尾有声明「以上为基于经典思想的现代演绎，非历史人物原话。」（`sageData.ts:163`）。**但引用区（CitationSidebar）没有任何等价声明**——用户看到的是「本次可溯源证据 + 相关度 95%」，而该引用与本次提问**毫无检索关系**。**二者必须分别处理**：正文声明不能为引用区的可信度主张背书 |
| **证据 4 — mock 路径** | `api.ts:2012` 与 `api.ts:2034-2039` 硬编码 `verifiable: true`；`roundtable/page.tsx:571,590` 异常时回退 mock 且 `similarity: 0.98` 硬编码。精选案例 `thoughtCourtCases.ts:13,14,15,45,46,47,77,78,79` 同样写死，并被测试**强制断言**为 `true`（`frontend/tests/thoughtCourtCases.test.cjs:20`） |
| **影响** | ①直接违背核心可信承诺；②这些数据**不得**作为 Evidence Drawer 的验收样本，也**不得**用于证明 RAG 或引用校验真实有效；③若 PHASE 7 沿用这些数据，GATE-7 的「验证」子项即为伪证 |
| **严重度** | **high** |
| **所属 Phase** | 独立修复任务（建议 PHASE 1 或单独任务，不混入 PHASE 7 的 UI 工作） |

### G-F【high】原文/注疏分层在设计与实现上无法表达

| 项 | 内容 |
|---|---|
| **要求** | 第五章五层分离；第十四章 D 与 A 不得同级；第七章 Evidence Drawer 须显示「文本类型」「注疏者」 |
| **证据链（逐点）** | ①`ai_service.py:340-346` 把注疏与原文**拼进同一个 `text` 字符串**（`f"{original}（{commentary}）"`）；②`ai_service.py:512-518` 把 verses 与 commentaries **合并进无区分的 `rag_refs`**；③`api/ai.py:149-158` 用 `translation` 字段承载 `commentary` 内容，**而非用 `type` 字段**；④`Citation` 契约（`schemas/ai.py:103-111`、`schemas/debate.py:95-102`）**无 `type` 字段**；⑤`CitationSidebar.tsx:305` 恒为 `type: citation.type === "commentary" ? "commentary" : "verse"`，但上游从未传 `type`；⑥`roundtableFlow.ts:182` **硬编码 `type: "verse"`** |
| **连带** | `CitationSidebar.tsx:208-212` 的「注疏」徽标在 roundtable 链路上**永远无法触发**（C-6）；`EvidenceDock.tsx:92-106` 把 AI 生成释义（`item.interpretation`）与原文并列在同一卡片内，且释义缺省时回退到写死文案「该原文为当前观点提供思想依据。」（`thoughtCourtSession.ts:33`） |
| **影响** | 违反第五章与第十四章；GATE-7 的「注疏」子项不可达 |
| **严重度** | **high** |
| **所属 Phase** | PHASE 1（Schema `text_type`）+ PHASE 5（契约）+ PHASE 7（展示） |

### G-G【high】出处自相矛盾（数据内部冲突）

| 项 | 内容 |
|---|---|
| **要求** | 「每个观点都能追到原典」；出处必须唯一且正确 |
| **冲突 1（跨文件）** | 「言必信，行必果」：`idioms.json` 归 **《论语·子路》13.20**（`original_text` 为"言必信，行必果，硁硁然小人哉！抑亦可以为次矣。"），而 `debate_classics.json` 的 `mozi-jianai-02` 归 **《墨子·兼爱下》**（原文仅"言必信，行必果。"）。**同一句在两个文件中归属不同书**。附带：`idioms.json` 的 13.20 条目本身**悬空**——`13.20` 不在 `lunyu.json` 的 107 条中（该篇只收 13.6 与 13.17） |
| **冲突 2（跨文件）** | 「事在四方，要在中央」：`sageData.ts:136` 归 **《韩非子·扬权》**，`roundtableData.ts:199` 归 **《韩非子·物权》**。**我本人实测**：「扬权」「物权」「事在四方」在全部语料中 **0 命中** —— 两个出处都无语料支撑，且「物权」并非《韩非子》篇名 |
| **附带不一致** | `idioms.json` 的 `meta.total: 35` ≠ 实际 **39** 条 |
| **悬空引用汇总** | `idioms.json` **16/39** 悬空（`chapter_num.verse_num` 指向 `lunyu.json` 中不存在的章节）；`lunyu_quotes.json` **2/36**；`quote_cards.json` **9/22** 无法逐字定位 |
| **关键含义** | `lunyu.json` 只收 107/512 章，而下游文件按**完整论语**编号引用 → 大量真实存在的论语章句**落在语料之外**，会被判 `verifiable=false`。这是**知识库不完整导致的假阴性，不是模型幻觉**——Quote Verifier 必须区分「语料缺失」与「引文伪造」，否则会误伤真实引文 |
| **严重度** | **high** |
| **所属 Phase** | PHASE 1（引用完整性校验 + 人工复核队列）+ PHASE 2（补全语料） |

### G-H【high】回归门禁不可信

| 项 | 内容 |
|---|---|
| **F-2【blocker】** | `frontend/package.json:12` 现为 `"test": "vitest run"`；`git log -p -- frontend/package.json` 显示 HEAD `64c8618` 把原先一长串 `node tests/*.test.cjs && ...` **整体替换**为 `vitest run`。而 `vitest.config.ts:16` 明确 `exclude: ["tests/*.test.cjs"]` → **22 个文件永不执行**。手工直跑：**18 通过 / 4 失败**。前端真实回归保护从 **321 处断言降级为 41 处** |
| **F-3【high】** | 22 个 `.test.tsx` 中 **20 个**是 7 行占位文件，唯一断言为 `expect(true).toBe(true)`。即 `vitest run` 的「23 files / 41 tests passed」中约 20 个用例**无任何验证力** |
| **C-13【high】** | `npx tsc --noEmit` **失败，26 个错误**全部在 `tests/curtainPhysics.test.tsx`，CI 的 typescript-check job 会红 |
| **C-14【high】** | 前端**不存在 ESLint 配置文件**，CI 的 lint job（`npx eslint . --ext .ts,.tsx --max-warnings 0`）以 **exit 2** 失败；`npm run lint` 进入交互式向导 |
| **F-4【high】** | `test_default_provider_is_openai`（`test_ai_provider.py:140-144`）因本机 `backend/.env` 的 `LLM_PROVIDER=agnes` 而**确定性失败** → 本机 `pytest` 退出码**恒为 1**，使"退出码即门禁"失效 |
| **F-5【medium】** | 仅断言 HTTP 200 / 存在性的弱测试：`test_auth.py:220,276,305,350`、`test_cors_config.py:17,32`、`test_hackathon_readiness.py:32`。其中 `test_hackathon_readiness.py:27-44` 仅断言 `/health` 返回 200 且含 9 个 key 名，**不断言任何值**（如 `rag_count` 是否为 143）——**这正是 PROJECT-BRIEF 禁止的「只检查 HTTP 200 就宣称功能通过」** |
| **影响** | PHASE 9 回归门禁**当前不可信**；CI 绿灯**不代表**前端回归通过（CI 从不运行 `.cjs` 套件） |
| **严重度** | **high** |
| **所属 Phase** | 独立任务（PHASE 9 前置） |

### G-I【high】测试基线不完整、非并发安全、且存在 FakeRag 冒充真实 RAG

| 项 | 内容 |
|---|---|
| **环境不完整** | `backend/.venv` 缺 `jwt`（`pip list` 无 PyJWT）→ `conftest.py:40` 导入 `app.main` 即 `ModuleNotFoundError`，**0 个测试执行**（我本人实测 exit code 1）。t5/t7 通过临时注入 PyJWT 得到基线：**1 failed, 82~84 passed, 2 skipped**。仓库**无一条命令能开箱跑出完整后端基线** |
| **F-1【blocker】** | `backend/tests/test_debate_classic_rag.py:20,51` 对**真实** `backend/chroma_db`（143 条持久化索引）执行 `build_index(force=True)` → **全量删除后重建**。无隔离、无 fixture 副本。任何一次 `pytest tests` 都会改写真实索引，与 PHASE 0 只读约束冲突 |
| **F-6【high】** | `conftest.py:14-19` 删除 `backend/test_wudian.db`、`:26` `setdefault DATABASE_URL` 指向该固定文件 → **测试套件不可并行**。审计期间多个并发 `pytest` 进程产生 3 组不同失败集 |
| **F-7【medium】** | `test_hackathon_readiness.py:49,66` 与 `test_chat_sage_schema.py:43` 使用 **FakeRag** 冒充真实 RAG（`async def retrieve_for_sage_chat(...)` 返回固定数据） |
| **覆盖缺口** | `retrieve()` 路径**零测试**（这正是 G-A 长期未被发现的原因）；`citation_validator` 对抗场景**零测试**；debate 跨派泄露**零测试** |
| **影响** | 无可用回归基线；G-A/G-B 无测试保护 |
| **严重度** | **high**（F-1 为 blocker） |
| **所属 Phase** | 独立任务（PHASE 1 引入 chroma 隔离 fixture；PHASE 9 前置） |

### G-J【high】数据缺口决定指标不可达（非算法问题）

| 项 | 内容 |
|---|---|
| **硬约束** | 原典正文合计 **128 条**（论语 107 + debate_classics 21，后者含 6 条非思想类文学人物；**归一化后完全相等重复 0 条、部分包含恰好 1 对**，见 §1.1）；注疏 15 条；真实向量索引 **143 条**。`classics_catalog.json` 的 123 部书**0 条正文**。V1 目标 12 部中 **4 部有语料、8 部零语料** |
| **不可达清单** | ①**Retrieval Recall@5 ≥ 90%**：`retrieve()` 恒空（G-A）→ 当前**无法测量**；②**Quote Exactness ≥ 99%**：无 QuoteVerifier；③**Source Attribution ≥ 98%**：无出处正确性指标；④**School Leakage < 1%**：各派 3–4 条 + `score=0.25` 兜底（G-B/G-D）；⑤**Unsupported Correct Refusal ≥ 95%**：无 Trust State，`insufficient_evidence` 不可达；⑥**Core Claim Evidence Coverage ≥ 95%**：无 Claim-Evidence 绑定；⑦**≥200 Gold**：`eval/` 不存在，当前 **0 条** |
| **可达项** | **性能 P50<1s / P95<3s 当前达标**（实测 P95 ≤ 6.3ms，不含外部 LLM），**但仅 143 条规模**，引入语义 embedding 与 reranker 后必须重测 |
| **关键判断** | 这些指标的不可达是**数据缺口 + 能力缺失**的叠加结果，**不是算法调优问题**。必须先扩语料（PHASE 2）、实现 Trust Layer（PHASE 5），才能进入指标验收 |
| **严重度** | **high** |
| **所属 Phase** | PHASE 2 + PHASE 4/5/6/8 |

---

## 3. Gate 可达性总表

| Gate | 目标 | 当前可达性 | 主要阻断项 |
|---|---|---|---|
| GATE-0 | 列明当前数据/RAG/embedding/citation/tests 真实状态 | **可达** | 无（七份审计报告已覆盖） |
| GATE-1 | fixture 可 ingest；schema test 全 PASS | **不可达** | §1.3（Schema 23/29 字段缺失）；`ingestion` 不存在；`schemas/knowledge.py` 不存在 |
| GATE-2 | 所有 passage 必须有 source；原典不得来自 LLM 生成 | **不可达** | §1.1（8 部零语料 / 4 部有语料）；§1.3（无来源字段）；生成方式**无法证实也无法证伪**（无生成日志、无 raw 底本） |
| GATE-3 | ≥50 个现代问题分类测试 | **不可达** | §1.4（Ontology 0 实现） |
| GATE-4 | 运行 retrieval_gold，输出 Recall@1/3/5、MRR | **不可达** | G-A（`retrieve()` 恒空）；`eval/` 不存在；语料仅 128 条 |
| GATE-5 | 对抗套件；任何伪造名言通过即 FAIL | **不可达** | G-B；§1.7/1.8/1.9/1.13（白名单、QuoteVerifier、TrustState、对抗套件全缺）；C9/C7/C10 实测未拦截 |
| GATE-6 | 跨派引用泄露率 < 1% | **不可达** | G-D（sage-chat 无过滤）；G-B；各派仅 3–4 条语料 |
| GATE-7 | Evidence Drawer 显示 原文/出处/注疏/来源/验证/TrustState；Desktop+Mobile | **不可达** | G-F；§1.11（无 A/B/C/D）；§1.9（无 Trust State）；`/demo` 不在导航（C-2）；前端回归门禁失效（G-H）。**强依赖 PHASE 1 与 PHASE 5** |
| GATE-8 | ≥200 gold；eval-report.json/md | **不可达** | `eval/` 不存在，0 条样本 |
| GATE-9 | backend/frontend tests、build、lint、typecheck 全通过 | **不可达** | G-H（tsc 26 errors、无 eslint 配置、22 套件静默失效、20 占位断言）；G-I（后端基线缺依赖、F-1 破坏真实索引、F-4 恒失败） |
| GATE-10 | 独立验收 PASS | **不可达** | 前置 Gate 全部未通过 |
| 性能 | P50<1s / P95<3s | **当前可达**（P95 ≤ 6.3ms） | 仅 143 条规模；G-A 使其失去意义；需 RAG V2 后重测 |

---

## 4. 对后续 Phase 的阻断关系

```
G-A / G-B / G-C (blocker)
   └─ 不修则：任何 RAG 指标测量无意义（测的是异常吞没或兜底假证据）
       ├─ PHASE 4 (RAG V2) 无法产生可信基线
       ├─ GATE-4 / GATE-5 / GATE-6 结构性不可达
       └─ PHASE 8 的 eval 报告会是「测错误的东西」

PHASE 1 (Passage Schema + Source Registry)
   └─ 阻塞 PHASE 2（语料无字段可写）
      └─ 阻塞 PHASE 7（Evidence Drawer 无来源字段可显示）

PHASE 5 (Trust Layer)
   └─ 阻塞 PHASE 7（无 TrustState 可显示）
      └─ 阻塞 GATE-5 全部指标

前端数据完整性缺陷 (G-E) + 回归门禁 (G-H)
   └─ 必须独立修复，否则 PHASE 7/9 的验收证据不可信
```

---

## 5. 诚实声明：未核验与不可核验项

| 项 | 状态 | 原因 |
|---|---|---|
| 任何文本「与通行本一致」 | **未核验** | `ctext.org` / `zh.wikisource.org` 访问被拒（non-public IP）；web_search 缺 API key |
| 「言必信，行必果」的正确归属 | **未裁决** | 同上；仅确认**仓库内自相矛盾** |
| 语料是否曾由 LLM 生成或改写 | **无法证实也无法证伪** | 无生成日志、无 raw 底本；`git log --diff-filter=A` 显示语料在 `a275867` 一次性引入 |
| `quote_cards`/`comics`/`theater_scripts` 的 AI 生成性质 | **高度可疑但未确证** | 文本风格明显为现代 AI 生成；无生成记录 |
| 是否存在人工复核 | **确认不存在** | 关键词全文检索零命中 |
| LLM 实际输出质量 | **未端到端验证** | `backend/.env` 未配置对应 API key（启动日志 `LLM API_KEY 未配置，provider=agnes`）。T-01 等结论为**代码路径推导 + 前端渲染路径核对** |
| 朱熹注疏所据底本与点校版权 | **未核验** | 无版本记录；外部受限 |
| 市场/竞品/用户痛点 | **未核验** | 本环境无外部网络；相关自述不作为本文档事实 |
| `frontend/lib/roundtableData.ts` 全部条目是否存在于语料 | **本次已核验**（22/32 无法定位） | 我本人按归一化文本比对，命令见下 |

**本报告的可复现核验命令**：

```powershell
cd backend
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8
# G-E：roundtableData / sageData 引用与语料比对
@'
import json, re
from collections import Counter
corpus = []
for c in json.load(open("../data/processed/lunyu.json", encoding="utf-8"))["chapters"]:
    for v in c["verses"]: corpus.append(v["original"])
for k, val in json.load(open("../data/processed/debate_classics.json", encoding="utf-8"))["classics"].items():
    for v in val["verses"]: corpus.append(v["original"])
for it in json.load(open("data/commentaries/lunyu_zhuxi.json", encoding="utf-8"))["commentaries"]:
    corpus.append(it.get("original",""))
norm = lambda s: re.sub(r"[，。！？；、\s「」『』\"'（）()【】]", "", s or "")
cn = [norm(t) for t in corpus if norm(t)]
for name, path in [("roundtableData","../frontend/lib/roundtableData.ts"), ("sageData","../frontend/lib/sageData.ts")]:
    cits = re.findall(r'\{ text: "([^"]+)", source: "([^"]+)"', open(path, encoding="utf-8").read())
    nf = [t for t,_ in cits if not any(norm(t) in c or c in norm(t) for c in cn if len(norm(t))>=4)]
    print(name, "total=", len(cits), "unverifiable=", len(nf))
'@ | .venv/Scripts/python.exe -
# 期望输出：roundtableData total= 32 unverifiable= 22 ；sageData total= 19 unverifiable= 10

# G-G：出处冲突关键词命中
@'
import json
texts=[]
for c in json.load(open("../data/processed/lunyu.json", encoding="utf-8"))["chapters"]:
    for v in c["verses"]: texts.append(v["original"])
for k,val in json.load(open("../data/processed/debate_classics.json", encoding="utf-8"))["classics"].items():
    for v in val["verses"]: texts.append(v["original"])
for t in ["言必信","事在四方","物权","扬权","以德报怨"]:
    print(t, sum(1 for x in texts if t in x))
'@ | .venv/Scripts/python.exe -
# 期望输出：言必信 1 / 事在四方 0 / 物权 0 / 扬权 0 / 以德报怨 0
```

---

## 6. 交付说明

- 本文档为 PHASE 0 的差距分析，**与 t10（`00-current-state.md`）并行且互不依赖**，两者共同构成 GATE-0 的证据基础。
- 本文档**不包含**架构方案（见 `02-architecture.md`）与任务依赖图（见 `03-task-dag.md`）。
- 本文档**不修改**任何产品代码、测试、数据或 PROJECT-BRIEF。
- 所有指标不可达的结论均基于实测，**未修改任何目标数字**。
- 建议 `04-gate-0-review.md` 重点独立复核：G-A 的四方互证、G-E 的 22/32 与 10/19 计数、G-G 的出处冲突、G-H 的门禁失效、G-I 的 F-1 破坏性测试。

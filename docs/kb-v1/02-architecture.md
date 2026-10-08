# 悟典可信中国思想知识库 V1 — 增量架构方案

- 文档：`docs/kb-v1/02-architecture.md`（PHASE 0 文档③）
- 任务：t12（由原 t8 拆分）
- 作者：rag-expert
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 状态：**设计文档，未创建任何代码文件，未 commit / push / deploy**

## 依据来源

| 来源 | 用途 |
|---|---|
| `docs/kb-v1/PROJECT-BRIEF.md` | 需求规范（第四~二十四章） |
| `docs/kb-v1/00-current-state.md` | 现状事实（t10） |
| `docs/kb-v1/01-gap-analysis.md` | 差距与 Gate 可达性（t11） |
| `docs/kb-v1/audit/rag.md` | 检索链路、embedding 边界、多学派隔离（t3，本人） |
| `docs/kb-v1/audit/trust.md` §8 | 可信层最小增量约束、verify-quote 契约（t4） |
| `docs/kb-v1/audit/classical-knowledge.md` §2/§8/§10 | Schema 字段判定、L1–L5 映射（t2） |
| `docs/kb-v1/audit/backend.md` §5/§6/§8 | API 现状、两条数据通道、兼容红线（t5） |
| `docs/kb-v1/audit/frontend.md` §5/§9 | Evidence Drawer 约束、字段冻结要求（t6） |

**阅读约定**：本文所有"现状"陈述均可追溯到上述审计证据（带 `文件:行号` 或命令）。
凡本文提出的**新设计**均为提案，标注为「新增」或「修改」，**不代表已实现**。
无法核验的内容一律标注「未验证」。本文不改变任何指标目标数字。

---

## 1. 核心约束：增量升级，不重写

### 1.1 结论

本项目采用**增量升级（incremental upgrade）**，不采用重写。所有新增能力以**并列新模块 + 可选字段扩展**的方式接入，
既有 8 项能力全部保留并继续对外服务。

### 1.2 既有能力如何保留（逐项论证）

| # | 既有能力 | 保留方式 | 关键证据 / 风险 |
|---|---|---|---|
| 1 | **FastAPI** | 保持 `backend/app/main.py` 的应用对象、`lifespan`、`_validate_config`、CORS、`/health` 不变；仅**追加** `app.include_router(knowledge.router)` | 现有 8 个 router 已在 `main.py:199-228` 注册，实测 81 条路径（`backend.md` §1.2）。新增 router 不修改既有注册块 |
| 2 | **ChromaDB** | 继续使用现有 `PersistentClient` 与 collection `wudian_verses`（实测 143 条，dim=384，启动不重建）；新增 collection 与既有 collection **并存**，不迁移、不清空 | `rag.md` §4；`backend/chroma_db/chroma.sqlite3` 4,120,576 B |
| 3 | **当前 RAGService** | 保留类、单例 `get_rag_service()` 与 4 个对外入口签名（`retrieve` / `retrieve_for_sage_chat` / `retrieve_for_debate_sage` / `build_*_context`）；RAG V2 作为**内部编排层**，在 `retrieve` 内部可切换，旧路径仍可用 | `rag_service.py:906/914/992/1011/1020/1050/1077`；`backend.md` §5「可安全扩展」 |
| 4 | **多 Provider LLM** | `llm_client.py` 与 `settings.llm_config`（openai/agnes/deepseek/qwen/local）**不改**；Evidence Pack 通过 prompt 注入，不改变 provider 抽象 | `config.py:196-229`；`backend.md` §9 未验证真实调用质量 |
| 5 | **debate engine** | 保留 `debate_engine.py` / `debate_orchestrator.py` / `debate_state_graph.py` / `debate_storage.py`；`SageSpeech` **追加可选字段**，不重命名不删除；各派仍从 `retrieve_for_debate_sage` 取料 | `backend.md` §5 兼容红线；`debate_engine.py:78-83` |
| 6 | **citation validator** | 保留 `citation_validator.py` 与 `SAGE_CLASSICS`、保留 `validate()` 签名；**收紧** `_match_citation` 的双向子串并补齐空出处分支（消除 T-04/T-13）；新增 `quote_verifier.py` 承载全库回查 | `trust.md` §8.2 |
| 7 | **knowledge graph** | `knowledge_graph.py` 与 `data/processed/knowledge_graph.json` **不改**；L3 扩层以**新增数据文件 + 新增加载器**实现，不就地改写既有 21 节点 | `classical-knowledge.md` §8.2（L3 现为儒家单线） |
| 8 | **前端「问→证→辩→判」** | 保留路由、页面、组件与既有 props；Evidence Drawer 以**扩展 `CourtEvidence` 字段**实现，不新建并行数据模型；SSE 事件名与中文 citation key 不变 | `frontend.md` §5.1/§5.2；`backend.md` §5 |

### 1.3 为什么不做重写（明确的否决理由）

1. **契约已被前端消费，重写等于破坏生产接口。** `frontend/lib/api.ts:1053` 直接消费 `/api/ai/chat-sage` 的 SSE 事件名
   （`chapters` / `content` / `citations` / `[DONE]`）与**中文 citation key**（`出处` / `原文`）；
   `roundtable` 消费 `SageSpeech.citations` / `sentence_evidence`。重写这些结构会同时打断前端主流程。
2. **现有测试虽弱但非零，重写会一次性丢弃全部回归信号。** 后端 82 passed / 前端 23 files（`00-current-state.md` §5）。
   即便其中部分是弱断言，也比"归零后重来"更能约束改动。
3. **ChromaDB 索引已持久化且启动不重建（实测 143→143）。** 重写索引层会引入一次全量重建，
   与 PROJECT-BRIEF 第十八章「启动不得每次全量重建」直接冲突，且在没有来源字段的情况下重建**无法改善**数据质量。
4. **真正的缺口在数据与可信层，不在框架层。** 三个 blocker 是 `verse_no` 类型冲突（G-A）、
   相关性兜底（G-B）、路径不一致（G-C），均为**局部代码缺陷**；Schema/来源缺失是**数据层**问题。
   重写框架并不能解决其中任何一个，反而会掩盖它们。
5. **风险与收益不对称。** 增量路径每步都可独立测试与回滚；重写路径在完成前没有可验收的中间态，
   与 PROJECT-BRIEF 第二十一章「任何阶段失败不得进入下一阶段」的 Gate 机制不兼容。

### 1.4 增量纪律（对后续所有 Phase 生效）

- **只追加，不重命名**：既有字段、路由、事件名、中文 key 一律保留。
- **新能力独立成模块**：`services/retrieval/`、`services/quote_verifier.py`、`api/knowledge.py` 等均为新文件。
- **旧入口保持可用**：`retrieve()` 修复后仍返回 `List[RAGReference]`；RAG V2 结果可映射回该类型。
- **每个 Phase 独立 commit**（PROJECT-BRIEF 第二十二章），仅包含该 Phase 明确文件。
- **不顺手改无关端点**：约 65/81 条路径无 `response_model`（`backend.md` §8.9），不在本次范围内。

---

## 2. 目标数据流

```
用户输入（现代现实问题，自然语言）
   │
   ▼
[1] 问题结构化  Modern Issue Ontology          ← 新增 services/issue_structurer.py
   │   scene / actors / conflict / emotion / choices / concepts
   │   （PROJECT-BRIEF 第七章：禁止直接丢给 embedding）
   ▼
[2] 中国思想概念映射  Modern→Classical Expansion ← 新增 services/retrieval/query_expander.py
   │   现代词 → 受控概念（义/礼/正名/不争/尚贤/名实/赏罚…）
   ▼
[3] Query Analyzer                              ← 新增 services/retrieval/query_analyzer.py
   │   归一化、意图、检索范围、filter 意图（school / book / text_type）
   ▼
[4] 权威原典检索 (L1)  ┐
[5] 历代注疏检索 (L2)  ┴─ Hybrid Retrieval      ← 新增 services/retrieval/{bm25,dense}.py
   │   BM25 + Dense（语义）→ 融合
   │   ⚠ L1 与 L2 使用**不同 collection / 不同表**，不混成同一 chunk
   ▼
[6] Metadata Filtering                          ← 新增 services/retrieval/filters.py
   │   school / book_id / text_type / person / concept
   ▼
[7] Reranker                                    ← 新增 services/retrieval/reranker.py
   ▼
[8] Diversification                             ← 新增 services/retrieval/diversity.py
   │   禁止 Top-K 全来自同一 passage / 同一章
   ▼
[9] 多学派 Evidence Pack                        ← 新增 services/evidence_pack.py
   │   EvidencePack { query, scenario, concepts, evidence[] }
   │   ★ 唯一允许 LLM 引用的 source 白名单
   ▼
[10] LLM 推理（多 Provider，既有 llm_client 不变）
   │   仅可引用 Evidence Pack 内 source
   ▼
[11] Citation Guard                             ← 新增 services/citation_guard.py
   │   quote 必须 ∈ Evidence Pack，或经 QuoteVerifier 全库命中
   │   否则 verifiable=false，不得展示为"经典原文"
   ▼
[12] Quote Verifier                             ← 新增 services/quote_verifier.py
   │   POST /api/knowledge/verify-quote
   │   两个独立指标：quote_exists（这句话存在）≠ source_correct（出处正确）
   ▼
[13] Trust State                                ← 新增（四态）
   │   verified / citation_corrected / quote_relaxed / insufficient_evidence
   ▼
[14] Claim-Evidence 绑定                        ← 新增 services/claim_evidence.py
   │   答案拆 claim，每个核心结论必须有 evidence
   ▼
可追溯回答（前端 Evidence Drawer 展示原文/出处/注疏/来源/验证/TrustState/等级）
```

**与现状的差异（关键）**：现状 `[1]`–`[9]` 中除 `[4]` 的部分向量检索外**全部缺失或不成立**
（`01-gap-analysis.md` §1.5–§1.9）。现状 `[3]`→`[9]` 是"现代问题直接丢给 embedding"，
`[9]` 不存在，`[10]` 的 LLM 可自由引用（无白名单）。

---

## 3. 新增 / 修改模块清单

> 全部为**提案**，本文未创建任何文件。路径相对仓库根。已核对：`services/retrieval/`、`api/knowledge.py`、
> `schemas/knowledge.py` 当前**均不存在**。

### 3.1 PHASE 1 — Schema / Source Registry / Ingestion

| 路径 | 类型 | 用途 | 依赖 |
|---|---|---|---|
| `backend/app/schemas/knowledge.py` | **新增** | `Passage` / `Commentary` / `SourceRecord` / `EvidencePack` / `QuoteVerification` 的 Pydantic 模型 | 无（纯新增） |
| `backend/app/services/source_registry.py` | **新增** | 底本来源注册表（provider / url / edition / license / 授权状态），**拒绝无来源条目入库** | `schemas/knowledge.py` |
| `backend/app/services/ingestion.py` | **新增** | JSON → Passage 的**校验式**导入；带 schema 校验与拒绝清单 | `schemas/knowledge.py`, `source_registry.py` |
| `backend/app/models/knowledge.py` | **新增** | Passage / Commentary 的 ORM 模型，**原典与注疏分表** | `models/base.py` |
| `backend/migrations/versions/<rev>_knowledge_passage.py` | **新增** | 对应 Alembic 迁移（既有迁移仅 `601e9ee0d57f_initial_schema.py`） | `models/knowledge.py` |
| `data/sources/source_registry.json` | **新增** | 来源注册表数据（**不得编造**；无授权来源标 `license: unknown` 且 `verification_level` 不得为 A） | — |
| `backend/tests/test_knowledge_schema.py` | **新增** | Schema 单元测试（GATE-1「schema test 全 PASS」） | 上述 |
| `backend/tests/conftest.py` | **修改** | 将 `CHROMA_PERSIST_DIR` 覆盖到临时目录，隔离索引（消除 `backend.md` §8.3 的污染隐患） | — |

### 3.2 PHASE 3 — Modern Issue Ontology

| 路径 | 类型 | 用途 |
|---|---|---|
| `data/processed/modern_issue_ontology.json` | **新增** | scene / actors / conflict / emotion / choices / concepts 本体，覆盖 PROJECT-BRIEF 第七章 21 类 |
| `backend/app/services/issue_structurer.py` | **新增** | 现代问题 → 结构化（**不直接丢给 embedding**） |
| `backend/app/schemas/issue.py` | **新增** | 结构化结果的 Pydantic 模型 |
| `backend/tests/test_issue_ontology.py` | **新增** | ≥50 个分类测试（GATE-3） |

### 3.3 PHASE 4 — RAG V2

| 路径 | 类型 | 用途 | 依赖 |
|---|---|---|---|
| `backend/app/services/retrieval/__init__.py` | **新增** | 包入口 | — |
| `backend/app/services/retrieval/query_analyzer.py` | **新增** | Stage 1 Query Analyzer | `schemas/issue.py` |
| `backend/app/services/retrieval/query_expander.py` | **新增** | Stage 2 现代→古典概念扩展（保留 `SYNONYM_MAP` 作 fallback） | `modern_issue_ontology.json` |
| `backend/app/services/retrieval/bm25.py` | **新增** | Stage 3 真实 BM25（替代 `keyword_search` 的 `keywords[0]` 单键过滤） | 新增依赖（见 §7.3） |
| `backend/app/services/retrieval/dense.py` | **新增** | Stage 3 Dense 语义检索（含 hash fallback 标记） | embedding 方案 §7 |
| `backend/app/services/retrieval/filters.py` | **新增** | Stage 4 Metadata Filtering | `schemas/knowledge.py` |
| `backend/app/services/retrieval/reranker.py` | **新增** | Stage 5 Reranker | — |
| `backend/app/services/retrieval/diversity.py` | **新增** | Stage 6 Diversification（禁止同章霸榜） | — |
| `backend/app/services/retrieval/pipeline.py` | **新增** | Stage 1–6 编排；`RAGService.retrieve` 内部可调用 | 上述 |
| `backend/app/services/evidence_pack.py` | **新增** | Stage 7 Evidence Pack 组装与白名单 | `retrieval/pipeline.py` |
| `backend/app/services/rag_service.py` | **修改** | 修 G-A/G-B/G-C；`retrieve` 内部接入 pipeline；**保留全部既有签名与返回类型** | — |
| `backend/app/schemas/ai.py` | **修改** | `RAGReference.verse_no` 类型修正（方向见 §12 Q1）；**追加**可选字段 | — |
| `backend/tests/test_retrieval_pipeline.py` | **新增** | 检索回归（**不得用 FakeRag**，必须真实链路） | — |

### 3.4 PHASE 5 — Trust Layer

| 路径 | 类型 | 用途 |
|---|---|---|
| `backend/app/services/quote_verifier.py` | **新增** | 全库回查 + 逐字/归一化匹配 + **独立**出处判定 |
| `backend/app/services/citation_guard.py` | **新增** | Evidence Pack 白名单校验 |
| `backend/app/services/claim_evidence.py` | **新增** | Claim → Evidence 绑定 |
| `backend/app/services/trust_state.py` | **新增** | 四态映射（单一真值来源） |
| `backend/app/services/citation_validator.py` | **修改** | 收紧 `_match_citation`（单向 + 长度阈值）；补齐空出处分支；**保留 `validate()` 签名与 `SAGE_CLASSICS`** |
| `backend/app/services/ai_service.py` | **修改** | `_validate_citations` 改为委托 `citation_validator`（消除 T-12 分歧）；接入 Trust State |
| `backend/app/services/debate_engine.py` | **修改** | 删除死代码 `_validate_citations`（`:86-111`，无调用点）；`_bind_sentence_evidence` 接入 Evidence Pack；**保留 `SentenceEvidence` 字段** |
| `backend/app/schemas/ai.py` / `schemas/debate.py` | **修改** | `Citation.verifiable` 默认值从 `True` 改为**必填**（或默认 `False`），消除"缺省即通过" |
| `backend/app/api/ai.py` | **修改** | 移除硬编码 `verifiable=True`；**SSE 事件名与中文 key 不变** |
| `backend/app/api/knowledge.py` | **新增** | `/api/knowledge/{verify-quote,search,evidence}` 路由 |
| `backend/app/main.py` | **修改** | 仅**追加** `app.include_router(knowledge.router)` |
| `backend/tests/test_quote_verifier.py` / `test_citation_guard.py` / `test_adversarial_quotes.py` | **新增** | 对抗套件（GATE-5） |

**硬编码 `verifiable=True` 的实测位置**（全部需处理，`grep 'verifiable=True' app/api app/services`）：

```
api/ai.py:146            SSE citations 硬编码 True
api/ai.py:159            SSE citations 硬编码 True
api/ai.py:208            SSE citations 硬编码 True
api/ai.py:265            fallback citations 硬编码 True
ai_service.py:424        构造 Citation 时传 verifiable=True
debate_engine.py:105     匹配循环内 verifiable = True（计算后赋值，非白名单）
```

注：`ai_service.py:394` 与 `debate_engine.py:105` 是**循环内计算赋值**，其值取决于子串匹配结果；
其余为**无条件硬编码**。两者语义不同，修复方式也不同（前者改匹配逻辑，后者删除硬编码并接真实校验）。

### 3.5 PHASE 7 — 前端 Evidence Drawer

| 路径 | 类型 | 用途 |
|---|---|---|
| `frontend/lib/thoughtCourtTypes.ts` | **修改** | 扩展 `CourtEvidence`；新增 `TrustState` / `QualityGrade` / `TextType` / `EvidenceProvenance` |
| `frontend/lib/roundtableFlow.ts` | **修改** | **修复** `normalizeCitations`（`chapter: source` 错误、硬编码 `type:"verse"`、伪造 similarity） |
| `frontend/lib/thoughtCourtSession.ts` | **修改** | **修复** `normalizeEvidence`（移除写死文案与默认已核验） |
| `frontend/lib/thoughtCourtState.ts` | **修改** | `CitationStatus` 三态 → 四态 Trust State |
| `frontend/components/thought-court/EvidenceDock.tsx` | **修改** | 渲染新增字段；Desktop/Mobile 双布局 |
| `frontend/components/ui/EvidenceBadge.tsx` | **新增** | 共享 文本类型 / 校验状态 / 质量等级 徽标 |
| `frontend/components/roundtable/CitationPanel.tsx` | **修改** | 移除伪造「相关度」，改显 Trust State |
| `frontend/components/sage/CitationSidebar.tsx` | **修改** | 同上；保留「注疏」徽标逻辑 |
| `frontend/components/thought-court/ThoughtCourt.module.css` | **修改** | 新增字段样式 + 双端布局 |
| `frontend/tests/evidenceDrawer.test.cjs` | **新增** | **真实渲染断言**（非 `includes` 字符串匹配） |

**明确不改**：`api/community.py`、`api/content.py`、`api/learning.py`、`api/exploration.py`、
既有 `models/*`、`migrations/versions/601e9ee0d57f_*`、`core/config.py` 既有键名、`llm_client.py`、
`knowledge_graph.py`、前端既有路由与页面结构。

---

## 4. 存储设计：L1–L5 分层与原典/注疏分离

### 4.1 现状问题

- **五层没有在数据模型上分离**：无 `text_type` 字段，L1/L2 仅靠"文件位置 + `doc_type` 字符串约定"区分
  （`classical-knowledge.md` §8.3）。
- **原文/译文/注释被拼进同一 chunk**：`rag_service.py:677-681` 把
  `【篇章】…【原文】…【译文】…【注释】…【关键词】…` 拼成一个文档再入库；
  `ai_service.py:340-346` 与 `:512-518` 继续拼接与合并。
  这直接违背 PROJECT-BRIEF 第六章「原典和注疏必须分开储存」与第五章「禁止混成普通 chunk」。
- **注疏内嵌原文副本**：`lunyu_zhuxi.json` 15 条中 13 条重复存储 `original`（`classical-knowledge.md` §10.3）。
- **D 级内容与 L1 无等级区分**：`quote_cards.modern_interpretation` 等 AI 解释与原典无 `verification_level` 区分。

### 4.2 目标：按层分表 / 分 collection

**存储原则：不同层不共用同一张表、不共用同一 collection、不共用同一文档。**

| 层 | 存储载体（提案） | 关键字段 | 与现状关系 |
|---|---|---|---|
| **L1 权威原典** | 新表 `knowledge_passage` + 新 collection `wudian_passage_l1` | `passage_id`(PK), `book_id`, `book_title`, `chapter_id`, `chapter_title`, `section`, `line_no`, `original`, `original_traditional`, `original_simplified`, `text_type='original'`, `source_id`, `school`, `concepts[]`, `verification_level`, `proofread_status`, `license`, `embedding_version` | **新增**；既有 `wudian_verses` 保留不动 |
| **L2 历代注疏** | 新表 `knowledge_commentary` + 新 collection `wudian_passage_l2` | `commentary_id`(PK), `target_passage_id`(FK → L1), `commentator`, `commentary_dynasty`, `commentary_text`, `text_type='commentary'`, `source_id`, `verification_level` | **新增**；**不内嵌原文副本**，改为外键引用 L1 |
| **L3 人物/学派/概念** | 新文件 `data/processed/ontology_l3.json`（**不改** `knowledge_graph.json`） | `person` / `school` / `concept` 节点 + `school` 字段 | **新增**；修复"儒家单线"缺口（补老子/庄子/墨子/韩非） |
| **L4 思想概念** | 受控词表 `data/processed/concept_ontology.json` | `concept_id`, `label`, `school_affinity[]`, `aliases[]`, `parent_id` | **新增**；与 L3 建立映射（现状 L3 的 5 concept 与 67 tag 互不关联） |
| **L5 现代问题** | `data/processed/modern_issue_ontology.json` | `scene`, `actors[]`, `conflict[]`, `emotion[]`, `choices[]`, `concepts[]` | **新增**；现状 `scene`/`modern_usage` 是散文，无法结构化查询 |

**关键设计决策**：

1. **L1 与 L2 物理分离**（不同表 + 不同 collection）。理由：PROJECT-BRIEF 第六章明文要求；
   且逐字引用校验必须能明确"命中的是原典还是注疏"，否则 Trust State 无法判定。
2. **L2 通过 `target_passage_id` 引用 L1**，不再复制 `original`。理由：消除 13/15 重复存储，
   避免"注疏里的原文"与"原典"出现第二套真值。
3. **`text_type` 强制枚举** ∈ `{original, commentary, translation, modern_explanation}`。
   理由：PROJECT-BRIEF 第十四章要求前端不得把 D 与 A 同级展示，而这需要先能在数据上区分。
4. **`original` 不可变且可溯源**。任何修复（如已发现的 `lunyu.json` 3.22 缺陷）必须走独立变更流程并留痕，
   **不得就地静默改写**（`classical-knowledge.md` §10.3）。
5. **既有 `wudian_verses` collection 不迁移、不清空**。RAG V2 读新 collection；
   旧 collection 在过渡期保留，作为 `retrieve_for_sage_chat` 的既有路径（保证前端不中断）。

### 4.3 与既有 ChromaDB 文档格式的关系

现状文档格式（`【篇章】…【原文】…`）**保留给旧 collection**，供旧路径继续工作。
新 collection 的文档文本**仅含该层自身内容**：
- L1 文档：`original`（+ 可选 `original_simplified`）
- L2 文档：`commentary_text`（+ `commentator`）

不再把译文/注释/关键词拼进被检索文本。译文与关键词改为**独立 metadata 或独立层**，
由 Evidence Pack 在展示阶段组装，而不是在检索阶段混入。

---

## 5. 索引持久化与版本化

### 5.1 现状（实测）

- 已持久化：`backend/chroma_db/chroma.sqlite3`，collection `wudian_verses`，dim 384，**count=143**。
- 启动**不重建**：`build_index(force=False)` 实测 `143→143`（`rag.md` §4.1）。
- **无 `embedding_version`、无 `schema_version`**：换 embedding 后不会失效重建；
  `_collection_has_debate_classics()`（`rag_service.py:592-605`）只检查 `scope=debate_classic` 是否存在。
- **路径不一致（G-C）**：`rag_service.py:237` 用相对 `'./chroma_db'`，`main.py:39` 用绝对路径。

### 5.2 目标设计（不每次全量重建）

1. **路径统一（修 G-C）**：`rag_service.py` 改用 `settings.resolved_chroma_persist_dir`
   （`config.py:189-190`）。同时 `is_available` 应判断 `count > 0`，避免空索引报 `rag_available`。
2. **版本三元组写入 collection metadata**：
   `{schema_version, embedding_version, embedding_provider, embedding_dim, corpus_revision}`。
3. **启动时的一致性检查（替代"每次全量重建"）**：
   - 读取 collection metadata 的 `schema_version` / `embedding_version`；
   - 与当前代码/配置期望值比较；
   - **一致 → 跳过**（保持现状的"启动不重建"优点）；
   - **不一致 → 不静默重建**，而是标记 `index_stale=true` 并在 `/health` 暴露，由显式命令重建。
   理由：静默重建在生产上是不可接受的副作用；且当前测试已实测出"测试直写生产索引"的危害（`backend.md` §8.3）。
4. **增量更新（upsert 语义）**：以 `passage_id` 为主键 upsert，新增语料只写入变更条目；
   删除语料走显式 tombstone 流程，不整库清空。
5. **per-collection 版本**：L1 与 L2 collection 各自独立版本化，允许分别重建。
6. **重建命令**：`python -m app.scripts.rebuild_index --collection l1|l2 --force`（提案），
   需显式 `--force`，默认拒绝重建。
7. **测试隔离**：`conftest.py` 覆盖 `CHROMA_PERSIST_DIR` 到临时目录，使
   `test_debate_classic_rag.py:20,51` 的 `build_index(force=True)` 不再污染真实索引。

### 5.3 未验证项

- 新 collection 的实际创建、维度与 HNSW 参数**未验证**（本 Phase 只读，未创建）。
- 增量 upsert 在 ChromaDB 1.5.9 上的行为**未验证**。

---

## 6. embedding 方案

### 6.1 现状（实测）

| 项 | 值 | 证据 |
|---|---|---|
| 默认 provider | `local` | `config.py:86` |
| 实际类 | `LocalHashEmbeddingFunction` | `rag.md` §3 |
| 维度 | 384 | `rag_service.py:44`；`collections.dimension=384` |
| 算法 | blake2b 哈希分桶 + 符号 + L2 归一化 | `rag_service.py:61-74` |
| 语义能力 | **非语义**；5 字短语仅 9/384 维非零 | `rag.md` §3 |
| 公平测试 | 现代问题→原典 Recall@5 = **2/5**；逐字引用 top1 = **5/5** | `rag.md` §3 |
| 繁简 | 余弦仅 0.13–0.20 | 同上 |
| 切 OpenAI 条件 | `RAG_EMBEDDING_PROVIDER=="openai"` **且** `OPENAI_API_KEY` 非空 | `rag_service.py:273` |
| 当前 `.env` | 未设 `RAG_EMBEDDING_PROVIDER`；`OPENAI_API_KEY` 被注释 | `rag.md` §3 |

### 6.2 定位：hash 只能作**明确标注的 fallback**

`LocalHashEmbeddingFunction` **不是**语义检索方案。它在**逐字引用**场景可用（top1 5/5），
在"现代问题→古典思想"场景**不可用**（Recall@5 2/5），而后者正是产品核心场景
（PROJECT-BRIEF 第一章、第七章）。

因此：

- **保留** `LocalHashEmbeddingFunction`，但**必须显式标记**：
  返回结果与 `/health` 中标注 `embedding_provider: "local_hash"`、
  `semantic_retrieval: false`、`degraded: true`。
- **禁止**在 hash embedding 下宣称语义检索可用或报告 Recall@K 为有效质量指标。
- 在 `degraded=true` 时，Trust State 的默认上限应受约束（建议：不得输出 `verified` 以外的强断言，
  具体规则由 PHASE 5 定义）。

### 6.3 正式方案：语义 embedding（需外部依赖）

| 方案 | 依赖 | 状态 |
|---|---|---|
| A. 外部 API（OpenAI / 兼容端点，`text-embedding-3-small`） | `OPENAI_API_KEY` 或兼容 key | **未验证**：`.env` 中 key 被注释，本次审计未发起任何真实调用 |
| B. 本地语义模型（如 sentence-transformers / 本地 embedding 服务） | 本地模型权重 + 依赖 | **未验证**：仓库未声明该依赖，未安装、未测试 |
| C. 继续 hash | 无 | **可用但非语义**，只能作 fallback |

**诚实声明**：**当前无任何可用的语义 embedding 路径已被验证。**
方案 A 缺密钥、方案 B 未安装未测试。因此 RAG V2 的 Dense 阶段在**无密钥环境下无法达到设计质量**。

### 6.4 无外部密钥时的可行路径与降级策略

1. **接口先行**：`retrieval/dense.py` 定义 `EmbeddingProvider` 抽象，
   实现 `LocalHashProvider`（fallback）与 `APIProvider`（待密钥）；**不改** `llm_client` 的 provider 抽象模式。
2. **降级必须显式、可观测**：
   - 无密钥 → 自动使用 hash，并在响应与 `/health` 标注 `degraded: true`、`embedding_provider: "local_hash"`；
   - **禁止**静默降级后仍报告"语义检索通过"。
3. **降级下的可交付范围**（诚实界定）：
   - **可交付**：BM25（词面）+ metadata filter + reranker + diversity + Evidence Pack + 引用白名单 + Quote Verifier + Trust State。
     这些**不依赖语义 embedding**，且能修复 G-B（无关证据注入）与提升可解释性。
   - **不可交付（在无密钥时）**：现代问题→古典思想的语义召回质量。
     GATE-4 的 `Recall@5 >= 90%` 在无密钥 + 143 条语料下**不可达**（双重原因：语料缺口 + 无语义 embedding）。
4. **验收口径**：PHASE 4 若在降级模式下运行，`eval-report` **必须**标注
   `embedding_provider=local_hash, degraded=true`，并**不得**将结果表述为"达到 V1 质量目标"。

---

## 7. 兼容性策略

### 7.1 真实注册路由（实测）

`main.py:199-228` 实际注册 **8 个 router**，OpenAPI 实测 **81 条路径**：

| router | 注册行 | 内部 prefix |
|---|---|---|
| `ai` | `main.py:199-200` | `/api/ai` |
| `community` | `main.py:203-204` | `/api/community` |
| `content` | `main.py:207-208` | `/api/content` |
| `learning` | `main.py:211-212` | `/api/learning` |
| `exploration` | `main.py:215-216` | `/api/exploration` |
| `auth` | `main.py:219-220` | `/api/auth` |
| `classics` | `main.py:223-224` | `/api/classics` |
| `debate` | `main.py:227-228` | `/api/debate` |

### 7.2 被注释的 router **不构成兼容性约束**（明确结论）

`main.py:187-196` 有 8 行被注释的注册语句（`auth/users/classics/progress/srs/quiz/notes/community`）。
其中：

- `auth.py`、`classics.py`、`community.py` **已存在且已在别处真实注册**（上表），注释行是**历史遗留重复**；
- **`users.py`、`progress.py`、`srs.py`、`quiz.py`、`notes.py` 在 `backend/app/api/` 下不存在**
  （实测目录仅含 `ai/auth/classics/community/content/debate/exploration/learning`）。

**结论：这些被注释的 router 不构成任何兼容性约束，因为对应文件不存在、且无任何调用方。**
增量方案**不得**为了"恢复"它们而新增实现——这属于超范围工作。
（`progress_service.py` / `srs_service.py` / `quiz_service.py` 作为 **service** 存在并被其他 router 使用，
但它们的 **API 层不存在**。这两件事不要混淆。）

### 7.3 `/api/ai/*` 与 `/api/debate/*` 的保持方式

**必须逐字保持（有真实前端调用方）**：

| 契约 | 证据 | 保持方式 |
|---|---|---|
| SSE 事件名 `chapters` / `content` / `citations` / `[DONE]` | `api/ai.py:116-169`；`frontend/lib/api.ts:1053` | 不改名；新信息用**新增事件类型**追加 |
| citation 中文 key `id` / `出处` / `原文` / `chapter` / `translation` / `verifiable` | `api/ai.py:140-147` | 不改名；`trust_state` 等作为**新增可选 key** 追加 |
| `ChatSageResponse`（`reply/citations/confidence/honest_note/modern_takeaway`） | `api/ai.py:231-236`；`schemas/ai.py:113-122` | 只追加可选字段 |
| `VerseExplanation` | `api/ai.py:44-56`；`lib/api.ts:908` | 只追加可选字段 |
| `POST /api/auth/refresh` | `lib/api.ts:135` | 不动 |
| `POST /api/debate/{session_id}/{action}?stream=true` | `lib/api.ts:2060` | 不动 |
| `SageSpeech.citations` / `sentence_evidence` / `quote` / `source` | `schemas/debate.py:114-127` | 只追加 `trust_state` 等可选字段 |
| `GET /health` 的 `llm_available/rag_available/rag_count/...` | `main.py:171-183`；`test_hackathon_readiness.py:38-44` | 只追加（如 `index_stale`、`embedding_provider`、`semantic_retrieval`） |
| `verifiable: bool` | `schemas/ai.py:108`；`schemas/debate.py:100` | **保留字段**，可收紧语义，不可删除 |

**可以安全扩展**：`Citation` / `SentenceEvidence` / `RAGReference` 追加带默认值的可选字段
（Pydantic 向后兼容）。`RAGReference` 可追加 `passage_id` / `school` / `source_provider` / `text_type`。

**前端实际只调用 3 类端点**（`${API_BASE}/ai/chat-sage`、`${API_BASE}/auth/refresh`、`${API_BASE}/debate/`），
故 `community/content/learning/exploration` 等无前端调用方，兼容风险低于表面。

### 7.4 必须修复的兼容性阻断项

**G-A（`verse_no` 类型冲突）** 必须先解决，否则 RAG V2 的 Dense/BM25 融合结果无法构造为
`RAGReference`（`hybrid_search` 会继续抛 `ValidationError` 并被 `:910-912` 吞掉）。
修复方向见 §12 Q1（**不自行决定**）。

---

## 8. 两条经典数据通道与迁移风险

### 8.1 现状（实测）

```
通道 A（JSON）：data/processed/lunyu.json
   ├─ classics_service.py:22      → /api/classics/*
   └─ rag_service.py              → 检索语料

通道 B（DB）：init_db.py → verses 表（107 行）
   └─ learning.py / progress / srs / quiz 服务
```

实测各 service 数据源（`backend.md` §2.4）：`classics_service` 与 `rag_service` 走 JSON；
`quiz_service` 同时走 DB 与 JSON；`achievement/srs/progress` 仅 DB。

### 8.2 增量方案落在哪条通道

**结论：增量方案落在通道 A（JSON + ChromaDB），并明确不把通道 B 作为 Passage 真值来源。**

理由：

1. 检索语料现状就在通道 A（`rag_service` 读 `data/processed/*.json`），
   把 Passage Schema 建在通道 B 会引入**第二条检索真值**，与"增量"目标冲突。
2. 通道 B 的 `verses` 表由 `init_db.py` 导入，而 `init_db.py` **有破坏性**
   （清空 18 张表，本次只读审计未执行），把 Schema 迁移绑到它风险过高。
3. 通道 B 只服务学习/进度/测验功能，不参与"问→证→辩→判"主流程。

### 8.3 迁移风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| **双真值** | 新 `knowledge_passage` 表与既有 `verses` 表可能对同一经文给出不同值 | 明确 `knowledge_passage` 为**检索与证据的唯一真值**；`verses` 保持"学习进度用途"不变；在文档与 Schema docstring 中写明 |
| **`book_id` 对齐** | 新 `book_id` 必须与 `classics_catalog.id` 对齐（`classical-knowledge.md` §10.3 建议） | PHASE 1 定义映射表并加校验测试 |
| **`verse_no` 语义** | `'1.1'`（章.节）与整数 `verse_no` 语义不同（见 §12 Q1） | 不自行决定；先做前端依赖核查 |
| **既有 collection 并存** | 新旧 collection 同时存在，可能被误查 | 明确 collection 名与用途；`retrieve` 只查新 collection，旧路径显式查旧 collection |
| **`data/raw` 为空** | 无底本可追溯，无法满足 GATE-2「原典不得来自 LLM 生成」 | 属**数据/授权阻塞**（见 §12 Q3），非本架构可解决 |

---

## 9. 契约冻结（供前端对接）

> 以下字段名在 PHASE 1 冻结。前端不得另造同义字段（`frontend.md` §9.2）。

### 9.1 `EvidenceProvenance`（与后端 passage 对齐）

```
book_id            ← passage.book_id
book_title         ← passage.book_title
chapter_id         ← passage.chapter_id
chapter_title      ← passage.chapter_title
section            ← passage.section
line_no            ← passage.line_no
text_type          ← passage.text_type   ∈ {original, commentary, translation, modern_explanation}
commentator        ← passage.commentator
commentary_dynasty ← passage.commentary_dynasty
source_provider    ← passage.source_provider
source_url         ← passage.source_url
source_edition     ← passage.source_edition
license            ← passage.license
verification_level ← passage.verification_level
proofread_status   ← passage.proofread_status
```

**对接点**（前端唯一入口）：
- `lib/thoughtCourtSession.ts:24-37` `normalizeEvidence`
- `lib/roundtableFlow.ts:171-186` `normalizeCitations`

两者必须**透传后端字段、缺失即 `undefined`**，**禁止回退到写死文案**。

### 9.2 `TrustState` 四态（冻结）

| 状态 | 触发条件 |
|---|---|
| `verified` | `quote_exists=true` 且 `source_correct=true` |
| `citation_corrected` | `quote_exists=true` 且 `source_correct=false`（须返回 `correct_source`） |
| `quote_relaxed` | 仅归一化后匹配（`exact_match=false`、`normalized_match=true`） |
| `insufficient_evidence` | `quote_exists=false`，或无任何候选；**禁止编造古文**，必须输出 PROJECT-BRIEF 第十二章的拒答文案 |

### 9.3 质量等级 A–D（冻结）

| 等级 | 定义 | 当前可赋值性 |
|---|---|---|
| A | 权威文本 + 人工确认 | **当前不可能**（零人工复核记录） |
| B | 权威来源 + 机器处理 | **当前不可能**（零 `source_*` 字段） |
| C | 来源可靠但尚未复核 | 仅当补齐来源后可赋 |
| D | AI 解释 | 可赋（`quote_cards.modern_interpretation` 等） |

**当前全部语料只能标 C 或 D，禁止标 A**（`classical-knowledge.md` §10.1）。
前端**不得**把 D 与 A 显示成同一等级（PROJECT-BRIEF 第十四章）。

### 9.4 `/api/knowledge/verify-quote` 契约（来自 `trust.md` §8.1）

输入 `{quote, claimed_source}`；输出必须**分别**包含 `quote_exists` 与 `source_correct`，
允许出现 `quote_exists=true, source_correct=false`（即 `citation_corrected`）。
字段：`quote_exists` / `exact_match` / `normalized_match` / `source_correct` / `correct_source` /
`similarity` / `match_type` / `candidates[]` / `trust_state` / `evidence_scope` / `verified_at`。

---

## 10. 排期约束

1. **PHASE 7（前端）不得早于 PHASE 1（Schema）与 PHASE 5（Trust Layer）。**
   理由：Evidence Drawer 要显示的 `source_provider` / `text_type` / `commentator` /
   `verification_level` / `proofread_status` 由 PHASE 1 提供；`TrustState` 四态由 PHASE 5 提供。
   在二者完成前开发 Drawer 只能渲染空字段或继续伪造（`frontend.md` §9.1）。
2. **前端回归门禁修复必须排在 PHASE 7 之前。**
   现状：`vitest.config.ts:16` exclude 22 个 `.cjs`、20/41 为占位断言、`tsc` 26 errors、
   前端无 eslint 配置（`00-current-state.md` §5）。若门禁不修，PHASE 7 的"通过"不可信（G-H）。
   建议拆为独立任务：`.cjs` 接入 + 占位符替换 + `tsc` + `eslint`（`frontend.md` §9.5）。
3. **前端数据完整性缺陷（G-E）应独立于 PHASE 7 修复。**
   `roundtableData` 32 条中 16 条出自零语料书目、22/32 无法定位、similarity 硬编码 0.87–0.97；
   `sageData` 19 条中 10 条无法核验。这些是**伪造可信信息**，属可信承诺的直接违背，
   不应混在 UI 任务中（`frontend.md` §9.3）。
4. **G-A / G-B / G-C 三个 blocker 必须在 PHASE 4 之前修复。** 否则任何 RAG 指标测量无意义
   （测的是异常吞没或兜底假证据）。
5. **PHASE 2 依赖 PHASE 1**；**PHASE 8 依赖 PHASE 4 + PHASE 5**；**PHASE 9/10 依赖全部前置**。
6. 每个通过 Gate 的 Phase 独立本地 commit，仅含该 Phase 明确文件，不推送不部署（PROJECT-BRIEF 第二十二章）。

---

## 11. Gate 与架构的对应关系

| Gate | 架构交付物 | 架构层面对 GATE 的关键约束 |
|---|---|---|
| GATE-1 | §3.1 Schema / source registry / ingestion | fixture 可 ingest；schema test 全 PASS |
| GATE-2 | §4 分层存储 | 所有 passage 必须有 source；**原典不得来自 LLM 生成**（当前无法证明，见 §12 Q3） |
| GATE-3 | §3.2 Ontology | ≥50 分类测试 |
| GATE-4 | §3.3 RAG V2 | 依赖 G-A 修复；无密钥时须标注 `degraded=true` |
| GATE-5 | §3.4 Trust Layer | 任何伪造名言通过即 FAIL |
| GATE-6 | §4.2 L1 分 collection + §7.3 debate 兼容 | 跨派泄露 < 1%（依赖 G-D 修复） |
| GATE-7 | §3.5 + §9 契约冻结 | Desktop + Mobile；强依赖 PHASE 1/5 |
| GATE-8 | 独立 Eval（不在本架构内，见 t7 报告） | ≥200 gold |
| GATE-9 | 全量回归 | 依赖前端门禁修复（§10.2） |
| GATE-10 | 独立验收 | 前置 Gate 全通过 |

---

## 12. 待决开放问题（**不自行决定**，需用户/队长决策）

| ID | 问题 | 选项与影响 | 需要谁决定 |
|---|---|---|---|
| **Q1** | **`verse_no` 修复方向** | (a) 改 `schemas/ai.py:17` 为 `Optional[str]`：改动最小，保留 `'1.1'` 章.节语义，但需确认前端无整数依赖；(b) 改写入侧（`rag_service.py:325/690/721`）统一为整数：需**重建索引**，且 `'1.1'` 的章.节语义**丢失**；(c) 拆为 `chapter_no` + `section_no` 两个整数字段：语义最清晰但改动最大 | **用户/队长**；前置：前端是否依赖整数的核查（`backend.md` §9 标注未验证） |
| **Q2** | **V1 语料是否收窄** | 12 部目标书目中 9 部零数据。选项：(a) 收窄到有数据的 3 部并如实标注覆盖范围；(b) 按 brief 补齐 12 部（需真实来源与授权）。影响 GATE-2/GATE-4 可达性与工期 | **用户**（产品范围决策） |
| **Q3** | **底本授权** | 现状零 `source_provider/url/edition/license`，`data/raw` 为空，**无法追溯底本**。ctext.org / 维基文库访问在本环境被拒（`non-public IP address`），授权与可用性**未核验**。无授权则无法满足 GATE-2 且不得标 A/B 级 | **用户**（需提供可授权来源或授权决策） |
| **Q4** | **是否接入外部 embedding** | 无 `OPENAI_API_KEY` 时只能降级为 hash（非语义）。选项：(a) 提供外部 embedding 密钥（需成本与网络）；(b) 引入本地语义模型（需新依赖与权重，未验证）；(c) 接受降级并在报告中标注 `degraded=true` | **用户** |
| **Q5** | **LLM 凭证** | `backend/.env` 中 `LLM_PROVIDER=agnes` 但 API_KEY 未配置；`00-current-state.md`/`backend.md` 均标注真实 LLM 调用**未验证**。影响 PHASE 6/8 的端到端验证 | **用户** |
| **Q6** | **PHASE 0 的 `_rag_probe_enviro.py` 曾以只读查询打开真实索引** | 已复验内容完整（143 条不变），但若要求"严格零触碰"，需确认该披露是否可接受 | **队长/qa-reviewer** |

---

## 13. 未验证与不可核验项（诚实声明）

| 项 | 状态 | 原因 |
|---|---|---|
| 新 collection / 新表 / 新迁移的实际创建与行为 | **未验证** | PHASE 0 只读，未创建任何文件 |
| 语义 embedding 的可用性与质量 | **未验证** | 无密钥；本地模型未安装未测试 |
| BM25 / reranker / diversity 的实际效果 | **未验证** | 尚未实现 |
| 外部来源（ctext.org / 维基文库）的授权与可用性 | **未核验** | 访问被拒（`non-public IP address`） |
| 语料是否曾由 LLM 生成或改写 | **无法证实也无法证伪** | 无生成日志、无 raw 底本 |
| 真实 LLM 端到端输出质量 | **未验证** | 无密钥，本次审计未发起任何真实调用 |
| 前端对 `verse_no` 的整数依赖 | **未验证** | 需前端专家确认（决定 Q1） |
| `tsc` / `eslint` / CI 实际通过情况 | **未验证** | 超出本任务 inScope；`00-current-state.md` §5 已记录 26 errors 与无 eslint 配置 |
| 生产 PostgreSQL + pgvector 路径 | **未验证** | 本地仅 SQLite；`models/embedding.py:28-39` 分支未实测 |

**声明**：本架构文档中的所有"现状"陈述均来自七份 PHASE 0 审计报告（带 `文件:行号` 或可复现命令），
未引用用户分享会话中的任何仓库描述。所有新增设计均为**提案**，未创建任何代码文件，
未 commit / push / deploy。`git diff --stat` 为空（本任务唯一写入文件为 `docs/kb-v1/02-architecture.md`）。

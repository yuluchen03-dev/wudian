# PHASE 0 审计：后端结构、API 契约、数据模型与兼容性

- 任务：t5 / attempt 1 / attempt_id `b6a72adb-c894-46c2-a702-7b49d09accc0`
- 执行者：backend（后端专家）
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 审计性质：**只读**。未修改任何产品代码、测试、数据、迁移或配置；未执行 commit/push/部署。
- 审计日期：2026-10-08（本机系统日期）
- 只读合规证据：`git status --short` 仅显示 `?? docs/kb-v1/`（本任务新增的审计文档），`git diff --stat` 为空。

### 复现环境（重要：仓库存在两套 Python，行为不同）

| 解释器 | 版本 | 关键差异 | 能否跑后端测试 |
|---|---|---|---|
| `python`（全局，PATH 默认） | 3.11.9 | 有 `PyJWT 2.15.0`、**无 chromadb** | **可以**（`82 passed`） |
| `backend/.venv/Scripts/python.exe` | 3.12.10 | 有 `chromadb 1.5.9`、**无 PyJWT**（`import jwt` 失败） | **不可以**（conftest 导入即失败） |

这一点直接决定本报告全部实测数字的口径，详见 §7。

---

## 1. 真实路由清单

### 1.1 注册方式（`backend/app/main.py`）

`main.py` 中**被注释掉的 router 块**在 `:187-196`（`auth/users/classics/progress/srs/quiz/notes/community` 的 `include_router` 示例，属早期规划遗留注释）。真正生效的注册在 `:198-228`，共 8 个：

| 行号 | router | 内部 prefix |
|---|---|---|
| `main.py:199-200` | `app.api.ai` | `/api/ai` |
| `main.py:203-204` | `app.api.community` | `/api/community` |
| `main.py:207-208` | `app.api.content` | `/api/content` |
| `main.py:211-212` | `app.api.learning` | `/api/learning` |
| `main.py:215-216` | `app.api.exploration` | `/api/exploration` |
| `main.py:219-220` | `app.api.auth` | `/api/auth` |
| `main.py:223-224` | `app.api.classics` | `/api/classics` |
| `main.py:227-228` | `app.api.debate` | `/api/debate` |

**必须澄清的事实**：`:187-196` 的注释**不是**"已实现但被禁用"的 router。`backend/app/api/` 下**实际只存在 9 个 `.py`**（`__init__, ai, auth, classics, community, content, debate, exploration, learning`），`users.py / progress.py / srs.py / quiz.py / notes.py` **文件根本不存在**（实测 `Test-Path` 全为 `False`）。因此这批"注释路由"是**不存在的模块**，不构成任何可恢复的既有能力，也不属于兼容性约束范围。

### 1.2 实测注册路由总数

```
$ python -c "from app.main import app; ..."   # 见复现命令
total routes: 87        # 含 FastAPI 自动生成的 /docs /redoc /openapi.json 等
openapi paths: 81       # 去重后的业务+系统路径
```

### 1.3 路由契约总表（method + path + 请求模型 + 响应模型 + 支撑 service + 测试覆盖）

契约列来自 `app.openapi()` 实测导出（`openapi paths: 81`、`components.schemas: 80`）。
"响应模型"一列中 `HTTPValidationError` 表示**该端点未声明 `response_model`**，OpenAPI 只暴露了校验错误结构 —— 这是真实的契约缺口，不是显示问题。

| # | method | path | 请求模型 | 响应模型 | 支撑 service | 测试覆盖 |
|---|---|---|---|---|---|---|
| 1 | GET | `/` | – | 无（dict） | – | 无 |
| 2 | GET | `/health` | – | 无（dict） | `llm_client`, `rag_service` | ✅ `test_hackathon_readiness.py:22-44` |
| 3 | POST | `/api/ai/explain` | `ExplainRequest` | `VerseExplanation` | `ai_service` | ❌ 无 |
| 4 | POST | `/api/ai/translate` | `TranslateRequest` | `TranslateResponse` | `ai_service` | ❌ 无 |
| 5 | POST | `/api/ai/chat-sage` | `ChatSageRequest` | **HTTPValidationError**（实际返回 SSE 或 `ChatSageResponse`，未声明） | `ai_service`, `rag_service`, `sage_cache` | ❌ 无（`test_chat_sage_schema.py` 只测 schema，不测端点） |
| 6 | POST | `/api/ai/generate-quiz` | `GenerateQuizRequest` | `GenerateQuizResponse` | `ai_service`, `rag_service` | ❌ 无 |
| 7 | POST | `/api/ai/retrieve` | `RetrieveRequest` | `RetrieveResponse` | `rag_service` | ❌ 无（**该端点实测恒返回空**，见 §3.3） |
| 8 | POST | `/api/auth/register` | `UserCreate` | `Token` | `core.security` | ✅ `test_auth.py` |
| 9 | POST | `/api/auth/login` | `UserLogin` | `Token` | `core.security` | ✅ `test_auth.py` |
| 10 | GET | `/api/auth/me` | – | `UserResponse` | `core.deps` | ✅ `test_auth.py` |
| 11 | POST | `/api/auth/refresh` | `RefreshTokenRequest` | `Token` | `core.security` | ✅ `test_auth.py` |
| 12 | GET | `/api/classics/books` | – | `List[Book]` | `classics_service` | ⚠️ 仅 `test_cors_config.py` 提及路径 |
| 13 | GET | `/api/classics/books/{book_id}` | – | `Book` | `classics_service` | ❌ 无 |
| 14 | GET | `/api/classics/books/{book_id}/chapters` | – | `List[ChapterBrief]` | `classics_service` | ❌ 无 |
| 15 | GET | `/api/classics/chapters/{chapter_id}` | – | `Chapter` | `classics_service` | ❌ 无 |
| 16 | GET | `/api/classics/verses/{verse_id}` | – | `SentencePair` | `classics_service` | ❌ 无 |
| 17 | GET | `/api/classics/entities/{entity_id}` | – | `Entity` | `classics_service` | ❌ 无 |
| 18 | GET | `/api/classics/daily-quote` | – | `DailyQuote` | `classics_service` | ❌ 无 |
| 19 | POST | `/api/community/groups` | `GroupCreate` | **HTTPValidationError** | `community_service` | ❌ 无 |
| 20-25 | GET/POST | `/api/community/groups...`（6 条） | – | **HTTPValidationError** | `community_service` | ❌ 无 |
| 26-27 | POST | `/api/community/notes`、`/notes/{id}/like`、`/notes/{id}/comment` | `NoteCreate`/`CommentCreate` | **HTTPValidationError** | `community_service` | ❌ 无 |
| 28-30 | GET | `/api/community/notes`、`/notes/{note_id}`、`/leaderboard` | – | **HTTPValidationError** | `community_service` | ❌ 无 |
| 31-32 | POST | `/api/community/pk/match`、`/pk/submit` | `PKMatchRequest`/`PKSubmitRequest` | **HTTPValidationError** | `community_service` | ❌ 无 |
| 33-40 | GET/POST | `/api/content/*`（8 条） | – | **HTTPValidationError** | `content_service` | ❌ 无 |
| 41 | GET | `/api/debate/guests/roster` | – | `GuestRosterResponse` | `guest_roster` | ✅ `test_debate_guest_roster_api.py` |
| 42 | GET | `/api/debate/presets` | – | 无 | `debate_engine` | ❌ 无 |
| 43 | GET | `/api/debate/history` | – | **HTTPValidationError** | `debate_storage` | ❌ 无 |
| 44 | POST | `/api/debate/start` | `DebateStartRequest` | `DebateStartResponse` | `debate_engine` | ✅ 3 个测试文件 |
| 45 | POST | `/api/debate/thought-compass` | `ThoughtCompassRequest` | `ThoughtCompassResponse` | `thought_compass` | ✅ `test_thought_compass_api.py` |
| 46 | POST | `/api/debate/{id}/next-round` | – | **HTTPValidationError**（SSE） | `debate_engine`, `debate_state_graph` | ✅ `test_debate_state_graph.py` |
| 47 | POST | `/api/debate/{id}/intervene` | `UserInterventionRequest` | **HTTPValidationError**（SSE） | `debate_engine` | ✅ `test_debate_action_apis.py` |
| 48 | POST | `/api/debate/{id}/stand` | `StandRequest` | `DebateStandResponse` | `debate_engine` | ✅ 同上 |
| 49 | POST | `/api/debate/{id}/mutual-question` | `MutualQuestionRequest` | `DebateMutualQuestionResponse` | `debate_engine` | ✅ 同上 |
| 50 | POST | `/api/debate/{id}/guests/random` | – | `DebateRandomGuestResponse` | `guest_roster` | ✅ `test_debate_guest_reactions.py` |
| 51 | POST | `/api/debate/{id}/guests/{key}/decision` | `GuestDecisionRequest` | `GuestDecisionResponse` | `guest_roster` | ✅ 同上 |
| 52 | POST | `/api/debate/{id}/summon` | `SummonRequest` | `DebateSummonResponse` | `guest_roster` | ✅ 同上 |
| 53 | GET | `/api/debate/{id}/report` | – | `DebateReportResponse` | `debate_engine` | ✅ `test_debate_plan_completion.py` |
| 54 | GET | `/api/debate/{id}/state-graph` | – | `DebateStateGraphResponse` | `debate_state_graph` | ✅ `test_debate_state_graph.py` |
| 55 | GET | `/api/debate/{id}/session` | – | **HTTPValidationError** | `debate_storage` | ❌ 无 |
| 56-63 | GET | `/api/exploration/*`（8 条） | – | `GraphResponse`/`TimelineResponse`/`IdiomListResponse`/`IdiomDetailResponse`（部分为 HTTPValidationError） | `knowledge_graph`, `timeline_service`, `idiom_service` | ❌ 无 |
| 64-81 | GET/POST | `/api/learning/*`（18 条） | 多个 Request | 多数为 **HTTPValidationError** | `achievement_service`, `progress_service`, `quiz_service`, `srs_service`, `streak_service` | ❌ 无 |

**测试覆盖统计（实测）**：81 条业务路径中，仅 **`/api/auth/*`(4)、`/api/debate/*`(11)、`/health`(1) 有直接端点测试**，其余约 **65 条无任何端点级测试**。

**认证依赖实测**（`grep Depends`）：

| api 文件 | 依赖 | 效果 |
|---|---|---|
| `ai.py` | `get_current_user_or_demo` | development 下匿名可用（`core/deps.py:187-189`） |
| `debate.py` | `get_current_user_or_demo` | 同上 |
| `classics.py` | **无** | 完全公开 |
| `exploration.py` | **无** | 完全公开 |
| `content.py` / `learning.py` / `community.py` | `get_current_active_user` | 需登录 |

---

## 2. 数据模型现状

### 2.1 SQLite 表清单（只读查询）

```powershell
cd backend
# 只读模式打开，不产生写入
python -  # 脚本见下
```

```python
import sqlite3
con = sqlite3.connect("file:wudian.db?mode=ro", uri=True)
rows = con.execute("select type, name from sqlite_master where type in ('table','index') order by type, name").fetchall()
```

实测输出：`objects: 89` → **18 张业务表 + 1 张 `alembic_version` + 70 个索引**。

| 表名 | 行数 | 说明 |
|---|---|---|
| `verses` | **107** | 经文（`original_text`, `translation`, `annotation`, `interpretation`） |
| `chapters` | **20** | 章节 |
| `classic_books` | **1** | 仅《论语》 |
| `verse_embeddings` | **0** | 空表 |
| `ai_chat_logs` | **0** | 空表 |
| 其余 13 张 | 未逐表计数 | `users/notes/comments/note_likes/study_groups/group_members/pk_matches/progress/srs_records/quizzes/quiz_records/achievements/checkins` |

`test_wudian.db`：**不存在**（conftest 每次会话开头删除，见 `tests/conftest.py:18-19`）。

### 2.2 ORM 模型与表映射（实测）

| 模型文件 | `__tablename__` |
|---|---|
| `models/user.py` | `users` |
| `models/classic.py` | `classic_books`, `chapters`, `verses` |
| `models/progress.py` | `progress` |
| `models/srs_record.py` | `srs_records` |
| `models/quiz.py` | `quizzes`, `quiz_records` |
| `models/achievement.py` | `achievements` |
| `models/note.py` | `notes`, `note_likes`, `comments` |
| `models/community.py` | `study_groups`, `group_members`, `pk_matches` |
| `models/embedding.py` | `verse_embeddings`, `ai_chat_logs` |
| `models/checkin.py` | `checkins` |

### 2.3 Alembic 迁移一致性（实测：一致）

```
migration tables: 18
db tables:        18
only in migration: []
only in db:        []
identical: True
alembic_version:  [('601e9ee0d57f',)]
```

- 迁移脚本：`backend/migrations/versions/601e9ee0d57f_initial_schema.py`（399 行，18 个 `create_table`）
- 无后续迁移，`down_revision = None`
- **结论：迁移与模型/DB 三者一致**，可作为 PHASE 1 新增表的基线。

### 2.4 关键结论：语料走 JSON，不走数据库

`backend/app/services/classics_service.py:22` 与 `knowledge_graph.py:11` 直接读 `data/processed/*.json`。实测各 service 数据源：

```
achievement_service.py   db=True   json=False
classics_service.py      db=False  json=True    ← 经典内容
community_service.py     db=True   json=True
content_service.py       db=False  json=True
knowledge_graph.py       db=False  json=True
quiz_service.py          db=True   json=True
rag_service.py           db=False  json=True    ← 检索语料
srs_service.py           db=True   json=False
progress_service.py      db=True   json=False
```

**这意味着存在两条互不相通的经典数据通道**：
- 通道 A：`data/processed/lunyu.json` → `classics_service`（对外 `/api/classics/*`）与 `rag_service`（检索）
- 通道 B：`init_db.py` 导入 → `verses` 表（107 行）→ `learning.py` / `progress` / `srs` / `quiz` 服务

PHASE 1 的 Schema 设计必须决定二者如何统一或桥接，否则 Passage Schema 会与 `verses` 表产生第二套并行真值。

---

## 3. 检索/验证/证据相关 API 现状

### 3.1 `/api/knowledge/*` 不存在

实测证据（全仓库 grep + OpenAPI 导出）：

```
matching paths: ['/api/content/quote-cards', '/api/content/quote-cards/{card_id}',
                 '/api/content/quote-cards/{card_id}/like', '/api/content/quote-cards/{card_id}/share',
                 '/api/learning/daily-quote', '/api/classics/daily-quote']
total paths: 81
```

- **无 `/api/knowledge/*`**、**无 `/api/knowledge/verify-quote`**、**无 evidence/trust 相关端点**。
- 对 `app/` 全目录搜索 `api/knowledge|verify.quote|trust_state|whitelist` → **零命中**。
- PROJECT-BRIEF 第十一章要求的 `POST /api/knowledge/verify-quote` 为**完全新增**。

### 3.2 现有响应中已有的引用/可信字段（真实 JSON 字段名）

**`backend/app/schemas/ai.py`**

| 模型 | 行号 | 真实字段 |
|---|---|---|
| `RAGReference` | `:12-18` | `text`, `source`, `chapter`, `verse_no`, `similarity` |
| `Citation` | `:103-110` | `id`, `source`(alias `出处`), `original`(alias `原文`), `verifiable` |
| `ChatSageResponse` | `:113-122` | `sage`, `reply`, `disclaimer`, `references`, `citations`, `modern_takeaway`, `confidence`, `honest_note` |
| `VerseExplanation` | `:35-46` | `verse_id`, `original_text`, `translation`, `background`, `modern_analogy`, `reflection`, `key_words`, `references`, `confidence`, `disclaimer` |

**`backend/app/schemas/debate.py`**

| 模型 | 行号 | 真实字段 |
|---|---|---|
| `Citation` | `:95-102` | `id`, `source`, `original`, `verifiable` |
| `SentenceEvidence` | `:105-111` | `sentence`, `source`, `original`, `similarity`, `verifiable` |
| `SageSpeech` | `:114-127` | `sage_key`, `sage_name`, `round_number`, `content`, `vernacular`, `quote`, `source`, `citations`, `sentence_evidence`, `target_sage`, `is_guest`, `confidence` |

**关键结论**：
- 已有 `verifiable: bool`（二值），**没有** `trust_state`（`verified/citation_corrected/quote_relaxed/insufficient_evidence` 四态）。
- 已有 `sentence_evidence`（逐句证据绑定，`debate_engine.py:130-155`），但 `verifiable` 判定为 `bool(refs and original != "无" and source != "无")`（`:149`），**只要求检索命中，不校验出处正确性**。
- 已有 `confidence: high/medium/low` 与 `honest_note`（`ai_service.py:522-535` 的诚实降级），可作为 Trust State 的兼容落点。
- **无** `verification_level`、`proofread_status`、`text_type`、`commentator`、`evidence_id`、`relevance`、`source_provider` 等 PROJECT-BRIEF 要求字段（全仓库 grep 零命中）。

### 3.3 ⚠️ 实测缺陷：`/api/ai/retrieve` 与 `explain` 的检索链路恒为空

这是本次审计发现的**最严重功能性缺陷**，会直接影响 PHASE 4/5 的基线可信度。

**缺陷机制**：
- `rag_service.py:325`、`:690`、`:721` 写入 metadata `"verse_no": vid`，其中 `vid` 形如 `"1.1"`（字符串）。
- `schemas/ai.py:17` 声明 `verse_no: Optional[int]`。
- `rag_service.py:897` 在 `hybrid_search` 里构造 `RAGReference(..., verse_no=r["metadata"].get("verse_no"))` → Pydantic 对 `"1.1"` 抛 `ValidationError`。
- `rag_service.py:906-912` 的 `retrieve()` 用 `try/except` **吞掉异常并返回 `[]`**，仅打 warning。

**实测证据**：

```powershell
cd backend
.venv\Scripts\python.exe -c "..."
# 输出：
# total docs: 143 non-integer verse_no: 143
# samples: [('sage_chat', '1.1', 'verse'), ('sage_chat', '1.2', 'verse'), ...]
# hybrid_search('学而时习之') RAISED ValidationError
# hybrid_search('无为而无不为') RAISED ValidationError
# hybrid_search('兼爱') RAISED ValidationError
# hybrid_search('法治') RAISED ValidationError
```

`143/143` 全部文档的 `verse_no` 均非整数 → **`hybrid_search` 对任意查询 100% 失败**。

**下游实测影响**：

```powershell
python -c "..."
# POST /api/ai/retrieve -> 200
# {"query":"学而时习之","results":[]}      ← HTTP 200 但结果恒空
# explain-path refs: 0
# is_low_confidence([]): True
# build_context_text([]): '（无匹配原文）'
```

- `POST /api/ai/retrieve`：恒返回 `{"results": []}`，**HTTP 200 掩盖了完全失效**。
- `ai_service.explain_verse`（`ai_service.py:99`）：`refs` 恒为空 → 上下文恒为 `（无匹配原文）`，`low_conf` 恒 `True` → 恒附低置信度免责声明。
- `ai_service.py:563` 同一路径受影响。

**未被影响的路径**（重要区分）：`retrieve_for_sage_chat`（`:914-990`）与 `retrieve_for_debate_sage`（`:992-1009`）**不经过** `hybrid_search`，它们直接用 `vector_search`/`_file_keyword_search` 并自行组装 dict，`verse_id` 保持字符串 `"1.1"`（`:977`）。因此 **sage-chat 与 debate 仍能正常检索**（实测 `sage_chat verses: 3 commentaries: 3`）。

**为什么测试没发现**：`tests/test_debate_classic_rag.py:12` 只导入 `rag.retrieve` 但**从未调用**；全仓库无任何测试调用 `hybrid_search` 或 `retrieve` 并断言非空结果。`test_hackathon_readiness.py:49` 用的是自造 `FakeRag`（mock），`monkeypatch.setattr(ai_service_module, "get_rag_service", lambda: FakeRag())` —— 这正是 PROJECT-BRIEF 禁止的"用 mock 假装真实 RAG 成功"。

---

## 4. ingestion 现状

### 4.1 语料如何进入系统

| 通道 | 入口 | 机制 | 校验 |
|---|---|---|---|
| 经典内容 | `data/processed/*.json` | **运行时读取**（`classics_service.py:22`、`knowledge_graph.py:11`） | 无 schema 校验 |
| 检索语料 | `data/processed/lunyu.json` + `debate_classics.json` + `backend/data/commentaries/lunyu_zhuxi.json` | 启动时 `build_index()`（`main.py:74`） | 无 schema 校验 |
| 关系库 | `init_db.py` | 脚本导入 JSON → `verses` 表（107 行） | 无 schema 校验 |
| 辩论会话 | `backend/data/debates/*.json` | `debate_storage.save()` 文件写入（`:30-36`） | 无 |

- 语料生成脚本：`data/scripts/build_lunyu.py`（677 行，**纯内置字典字面量**，无网络导入、无 `source_url`/`license` 字段）。
- **无 JSON Schema、无 Pydantic 校验、无 `jsonschema` 依赖**（全仓库 grep `jsonschema|schema_version|index_version` 零命中）。

### 4.2 索引持久化与版本管理

- 持久化：`backend/chroma_db/chroma.sqlite3`（4,120,576 B）+ HNSW segment。实测 collection `wudian_verses`，`dimension: 384`。
- **实测 count = 143**，构成可精确对账：
  ```
  lunyu verses: 107  + commentaries: 15  + debate: 21  = 143   (chroma count=143)
  ```
- 启动不重建：`build_index(force=False)` 在 `count()>0` 且已有 debate classic 时跳过（`rag_service.py:642-644`）。
- **无索引版本号**：metadata 里无 `embedding_version`/`schema_version`，无法判断索引是否与语料同步。
- **⚠️ 隐患**：`tests/test_debate_classic_rag.py:20` 与 `:51` 调用 `rag.build_index(force=True)`，而 `tests/conftest.py` **没有**覆盖 `CHROMA_PERSIST_DIR`（实测 grep 无命中），因此测试会**清空并重建生产 chroma 索引**（`_clear_collection()` → `collection.delete(ids=...)`）。本次审计期间观察到 count 在 `143 → 1 → 143` 之间跳变，正是该行为与并发测试共同作用的结果。PHASE 9 回归必须隔离此路径。

---

## 5. 兼容性约束清单（PROJECT-BRIEF 第十九章）

**必须保持不变（有真实调用方）**：

| 约束 | 证据 |
|---|---|
| `POST /api/ai/chat-sage` 的 SSE 事件格式：`data: {"type":"chapters",...}`、`data: {"content":...}`、`data: {"type":"citations","citations":[...]}`、`data: [DONE]` | `api/ai.py:116-169`；前端 `frontend/lib/api.ts:1053` 消费 |
| SSE citations 字段名（中文 key）：`id`、`出处`、`原文`、`chapter`、`translation`、`verifiable` | `api/ai.py:140-147` |
| `POST /api/ai/chat-sage` 非流式返回 `ChatSageResponse`（`reply/citations/confidence/honest_note/modern_takeaway`） | `api/ai.py:231-236`、`schemas/ai.py:113-122` |
| `POST /api/ai/explain` 返回 `VerseExplanation` | `api/ai.py:44-56`；前端 `lib/api.ts:908` |
| `POST /api/auth/refresh` | 前端 `lib/api.ts:135` |
| `POST /api/debate/{session_id}/{action}?stream=true` | 前端 `lib/api.ts:2060` |
| `SageSpeech.citations` / `sentence_evidence` / `quote` / `source` 字段 | `schemas/debate.py:114-127`；前端 roundtable 消费 |
| `GET /health` 的 `llm_available/rag_available/rag_count/...` 字段 | `main.py:171-183`；`test_hackathon_readiness.py:38-44` 断言存在 |
| `verifiable: bool` 字段语义（可保留，可扩展，不可删除） | `schemas/ai.py:108`、`schemas/debate.py:100` |
| `confidence: high/medium/low` 与 `honest_note` | `schemas/ai.py:121-122` |

**前端实际调用的后端端点只有 3 类**（全量扫描 `frontend/**/*.ts,tsx` 实测）：`${API_BASE}/ai/chat-sage`、`${API_BASE}/auth/refresh`、`${API_BASE}/debate/`。这意味着 §1.3 表中大量"无测试"端点（community/content/learning/exploration）**当前无前端调用方**，兼容性风险低于表面。

**可以安全扩展（新增字段不破坏现有解析）**：
- `Citation` / `SentenceEvidence` 可新增 `trust_state`、`evidence_id`、`verification_level`、`text_type`、`commentator` 等**可选字段**（Pydantic 默认忽略额外输入，新增带默认值的字段向后兼容）。
- `RAGReference` 可新增 `passage_id`、`school`、`source_provider` 等可选字段。

**必须修复才能继续（阻断项，见 §3.3）**：
- `RAGReference.verse_no: Optional[int]` 与 metadata `verse_no: str("1.1")` 的类型冲突。修复方式有两条且必须择一并记录：改 schema 为 `Optional[str]`（改动最小，但要确认前端无整数依赖），或改写入侧统一为整数（需重建索引，且 `"1.1"` 的章.节语义会丢失）。**PHASE 4 开始前必须解决，否则 Recall@5 恒为 0。**

---

## 6. 需要新增/修改的文件清单（初稿）

> 本清单为**设计初稿**，未创建任何文件。所有路径均相对仓库根。PHASE 1+ 实施前须经 lead-architect 在 `02-architecture.md` 确认并由 qa-reviewer 审核。

### 6.1 新增（PHASE 1 — Schema / Source Registry / ingestion）

| 建议路径 | 用途 | 依赖 |
|---|---|---|
| `backend/app/schemas/knowledge.py` | Passage / Commentary / SourceRegistry / EvidencePack / QuoteVerification 的 Pydantic 模型（含 `text_type`、`verification_level`、`proofread_status`、`source_provider`、`license`、`embedding_version`） | 无（纯新增） |
| `backend/app/services/source_registry.py` | 底本来源注册表（provider/url/edition/license），拒绝无来源条目 | `schemas/knowledge.py` |
| `backend/app/services/ingestion.py` | JSON → Passage 的校验式导入；**必须带 schema 校验** | `schemas/knowledge.py`, `source_registry.py` |
| `backend/app/models/knowledge.py` | Passage/Commentary 的 ORM 模型（原典与注疏分表，满足"必须分开储存"） | `models/base.py` |
| `backend/migrations/versions/<rev>_knowledge_passage.py` | 对应 Alembic 迁移 | `models/knowledge.py` |
| `backend/tests/test_knowledge_schema.py` | Schema 单元测试（GATE-1 要求"schema test 全 PASS"） | 上述 |

### 6.2 新增（PHASE 3 — Modern Issue Ontology）

| 建议路径 | 用途 |
|---|---|
| `data/processed/modern_issue_ontology.json` | scene/actors/conflict/emotion/choices/concepts 本体（≥20 类） |
| `backend/app/services/issue_structurer.py` | 现代问题 → 结构化（不直接丢给 embedding） |
| `backend/tests/test_issue_ontology.py` | ≥50 个分类测试（GATE-3） |

### 6.3 新增（PHASE 4 — RAG V2）

| 建议路径 | 用途 | 依赖 |
|---|---|---|
| `backend/app/services/retrieval/bm25.py` | 真实 BM25（替代现有 `keyword_search` 的 `keywords[0]` 单键过滤） | 新增依赖 |
| `backend/app/services/retrieval/reranker.py` | Reranker | – |
| `backend/app/services/retrieval/diversity.py` | 去重/多样性（禁止 Top5 同章） | – |
| `backend/app/services/evidence_pack.py` | 组装 EvidencePack（LLM 只能引用其中 source） | `retrieval/*` |
| `backend/app/api/knowledge.py` | `/api/knowledge/*` 路由（search / evidence / verify-quote） | 上述 |

### 6.4 修改（最小侵入）

| 路径 | 改动 | 风险 |
|---|---|---|
| `backend/app/schemas/ai.py:17` | `verse_no` 类型修正（§3.3 阻断项） | 中：需确认前端无整数依赖 |
| `backend/app/services/rag_service.py:897` | 同上，写入侧一致性 | 中 |
| `backend/app/services/citation_validator.py` | 扩展为白名单 + 逐字校验 + 出处判定；**保留 `validate()` 签名** | 低 |
| `backend/app/services/ai_service.py:352-411` | `_validate_citations` 接入 Trust State；保留 `all_verified` 语义 | 低 |
| `backend/app/services/debate_engine.py:130-155` | `_bind_sentence_evidence` 接入 Evidence Pack；保留 `SentenceEvidence` 字段 | 中 |
| `backend/app/api/ai.py` | 保持 SSE 事件名与中文 citation key 不变，附加 trust 字段 | 高（前端强耦合） |
| `backend/app/main.py:198-228` | 追加 `app.include_router(knowledge.router)` | 低 |
| `backend/tests/conftest.py` | 覆盖 `CHROMA_PERSIST_DIR` 到临时目录，隔离索引 | 低（修 §4.2 隐患） |

### 6.5 不建议改动（明确保留）

`api/community.py`、`api/content.py`、`api/learning.py`、`api/exploration.py`、`models/*`（除新增）、`migrations/versions/601e9ee0d57f_*`、`core/config.py` 现有键名。

---

## 7. 运行与验证命令（实测可用，非臆造）

### 7.1 ⚠️ 必须先明确的口径问题

仓库有两套 Python 且**都不完整**：

```powershell
cd backend
python -c "import chromadb"              # ModuleNotFoundError（全局缺 chromadb）
.venv\Scripts\python.exe -c "import jwt" # ModuleNotFoundError（venv 缺 PyJWT）
```

`backend/requirements.txt:18` 声明 `pyjwt>=2.8.0`，但 venv 里**没装**（实测 `pip show pyjwt` → not found）；venv 装的是 `python-jose 3.5.0`，而 `core/security.py:10` 用的是 `import jwt`。**venv 环境与 requirements.txt 不一致**，导致 venv 无法运行测试套件（conftest 导入 `app.main` 即失败）。

### 7.2 后端测试（实测通过）

```powershell
cd backend
python -m pytest tests -q
# 实测输出（隔离 DB 后）：
# 1 failed, 82 passed, 2 skipped, 1 warning, 13 subtests passed in 70.28s
```

- **1 failed**：`tests/test_ai_provider.py:142` `assert settings.LLM_PROVIDER == "openai"`，实测 `'agnes'`。根因：`backend/.env` 设了 `LLM_PROVIDER=agnes`，而该测试调用 `Settings()` 未 mock，被真实 `.env` 覆盖。**这是环境态失败，不是代码缺陷**（用 `LLM_PROVIDER=openai` 覆盖环境变量后仍失败，因为 pydantic-settings 优先级中 `.env` 对该字段生效，需在测试内 `monkeypatch` 或提供隔离 `.env`）。
- **2 skipped**：`tests/test_debate_classic_rag.py:15` 与 `:46`，原因 `ChromaDB collection is not available`（全局 python 无 chromadb）。
- **并发导致的不稳定**：审计期间观察到 `1 failed / 82 passed`、`5 failed / 78 passed`、`6 failed / 77 passed` 三种结果。根因是**多个进程并发跑 pytest 共享同一个 `backend/test_wudian.db`**（`conftest.py:26` 固定路径 + `:18-19` 每次会话删除），互相删除/重建表，产生 `UNIQUE constraint failed: users.username` 等错误。**这是并发假失败，不是代码缺陷。**
- 隔离验证：`$env:DATABASE_URL="sqlite+aiosqlite:///./_audit_backend_iso.db"` 后稳定为 `1 failed, 82 passed, 2 skipped`。

### 7.3 覆盖率（当前不可用）

```powershell
cd backend
python -m pytest tests -q --cov=app --cov-report=term-missing
# 实测：error: unrecognized arguments: --cov=app --cov-report=term-missing
# 原因：backend 环境未安装 pytest-cov（requirements-dev.txt 只有 pytest / pytest-asyncio）
```

**注意**：`.github/workflows/ci.yml` 的 `Run pytest with coverage` 步骤显式安装 `pytest pytest-cov`，因此 **CI 有覆盖率、本地没有**。CI 的 `--cov` 在本地不可复现。

### 7.4 前端测试（实测通过）

```powershell
cd frontend
npm test
# 实测输出：Test Files 23 passed (23) / Tests 41 passed (41) / Duration 7.93s
```

⚠️ 若用 `npx vitest run --dir frontend/tests` 从仓库根运行，会得到 `22 failed | 23 passed` 的假失败（工作目录错误导致路径解析失败）。**必须 `cd frontend` 后执行 `npm test`**。

### 7.5 Lint / typecheck（真实可用命令）

```powershell
# 前端 typecheck（CI 同款）
cd frontend
npx tsc --noEmit

# 前端 ESLint（CI 同款，linters.yml 与 ci.yml 均用）
npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0
```

```powershell
# 后端 lint（CI 用 ruff）
cd backend
ruff check app/ tests/
ruff format --check app/ tests/
# 实测：python -m ruff --version → No module named ruff（本地未安装）
# ruff 不在 requirements.txt / requirements-dev.txt 中，仅存在于 CI linters.yml
```

### 7.6 启动服务

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # backend/README.md:97
python -m app.main                                          # main.py:231-238
```

### 7.7 命令可用性总表

| 命令 | 本地可用 | 备注 |
|---|---|---|
| `cd backend; python -m pytest tests -q` | ✅ | 需串行执行；1 个环境态失败 |
| `cd backend; python -m pytest --cov=app` | ❌ | 缺 pytest-cov |
| `cd backend; .venv\Scripts\python.exe -m pytest` | ❌ | venv 缺 PyJWT |
| `cd frontend; npm test` | ✅ | 23 files / 41 tests 全通过 |
| `cd frontend; npx tsc --noEmit` | ✅ | 未在本任务运行（超范围） |
| `cd frontend; npx eslint .` | ✅ | 未在本任务运行 |
| `cd backend; ruff check` | ❌ | 未安装 |
| `cd backend; python init_db.py` | ⚠️ | **有破坏性**：`clear_data()` 清空 18 张表，审计中未执行 |

---

## 8. 给 lead-architect 与后续 Phase 的关键结论

### 阻断项（PHASE 4 前必须解决）

1. **`hybrid_search` / `retrieve()` 100% 失败**（§3.3）。`verse_no` 类型冲突（`rag_service.py:325/690/721` 写 `str` vs `schemas/ai.py:17` 声明 `int`）导致 `ValidationError` 被 `rag_service.py:910-912` 静默吞掉。后果：`/api/ai/retrieve` 恒空、`explain_verse` 恒无上下文且恒低置信度。**当前 RAG 的 Recall@5 不是"低"，而是 0（对该路径）**。PROJECT-BRIEF 第十七章 `Retrieval Recall@5 >= 90%` 在此路径上**当前不可达**，且**现有测试完全未覆盖**。

2. **测试用 mock 冒充真实 RAG**（§3.3）。`test_hackathon_readiness.py:49,66` 用 `FakeRag` + `monkeypatch` 替换 `get_rag_service`，使 1 的缺陷对测试完全隐形。这正是 PROJECT-BRIEF 明令禁止的模式，PHASE 8 Eval 必须用真实链路。

3. **测试污染生产索引**（§4.2）。`test_debate_classic_rag.py:20,51` 的 `build_index(force=True)` 直写 `backend/chroma_db`，`conftest.py` 未隔离 `CHROMA_PERSIST_DIR`。审计期间实测 count 跳变 `143→1→143`。

4. **venv 与 requirements.txt 不一致**（§7.1）。`requirements.txt:18` 声明 `pyjwt`，venv 未装且 `security.py:10` 依赖 `import jwt`；venv 无法跑测试。CI 用 Python 3.12 + `pip install -r requirements.txt`，本地 venv 与之不符。

### 重要但非阻断

5. **`/api/knowledge/*` 完全不存在**（§3.1），Quote Verifier 为纯新增。
6. **无 Trust State 四态**，仅有 `verifiable: bool`（§3.2）；扩展点已明确（`ChatSageResponse.honest_note`、`confidence`）。
7. **两条经典数据通道并行**（§2.4）：JSON（`classics_service`/`rag_service`）与 `verses` 表（`learning`/`progress`/`srs`/`quiz`）。Passage Schema 必须明确归属，否则产生双真值。
8. **无索引版本号、无 ingestion schema 校验**（§4），PROJECT-BRIEF 第十八章"索引必须持久化、启动不得每次全量重建"当前**已满足**，但"可追溯/可版本化"未满足。
9. **契约缺口**：约 65/81 条路径无 `response_model`（OpenAPI 暴露 `HTTPValidationError`）且无端点测试。增量升级中**不要顺手修改这些端点**（超范围且无收益）。

### 兼容性红线（PHASE 6/7 必须遵守）

`api/ai.py` 的 SSE 事件名（`chapters` / `content` / `citations` / `[DONE]`）与 citation 中文 key（`出处`/`原文`）被 `frontend/lib/api.ts:1053` 直接消费；`SageSpeech.citations`/`sentence_evidence` 被 roundtable 消费。Evidence Pack 与 Trust State 只能**追加可选字段**，不得重命名或删除既有字段。

---

## 9. 不确定性与未验证项

| 项 | 状态 | 说明 |
|---|---|---|
| 前端对 `verse_no` 的整数依赖 | **未验证** | 需 frontend 专家确认，决定 §3.3 修复方向 |
| `npx tsc --noEmit` / `eslint` 当前是否通过 | **未验证** | 超出本任务 inScope（backend），未运行 |
| CI（GitHub Actions）是否实际通过 | **未验证** | 本地无法复现 CI 的 3.12 + pytest-cov + ruff 组合 |
| `init_db.py` 全量执行结果 | **未执行** | 有破坏性（清空 18 张表），只读审计中禁止执行 |
| 生产环境 PostgreSQL/pgvector 路径 | **未验证** | 本地仅 SQLite；`models/embedding.py:28-39` 的 pgvector 分支未实测 |
| 多 Provider LLM 真实调用质量 | **未验证** | `.env` 中 `LLM_PROVIDER=agnes`，本次审计未发起任何真实 LLM 请求（无密钥、且属只读范围） |
| `backend/.env` 中 API_KEY 实际是否有效 | **未验证** | 已按脱敏方式查看键名，未读取/未使用任何密钥值 |

**声明**：本报告所有数字均来自本任务实际执行的只读命令与脚本输出，未引用用户分享会话中的任何仓库描述。发现 1 个确定性代码缺陷（§3.3）与 3 个工程风险（§4.2、§7.1、并发测试），**未修改任何产品文件**（`git diff --stat` 为空）。

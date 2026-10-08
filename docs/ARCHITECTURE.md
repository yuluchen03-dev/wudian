# 架构说明

> 悟典项目 — 澄清 SQLite vs PostgreSQL、Next.js 与 Vite 差异、分层结构

## 1. 数据库现状与目标

### 当前状态：SQLite

- **类型**：SQLite（`sqlite+aiosqlite`）
- **文件路径**：`backend/wudian.db`（异步 ORM，支持并发读写）
- **已启用优化**：
  - WAL 模式（Write-Ahead Logging，防并发写锁死）
  - `busy_timeout=30000`（30 秒写超时）
  - `check_same_thread=False`（允许跨线程连接）

代码位置：`backend/app/core/database.py:27-48`

### 目标生产环境：PostgreSQL 15+ + pgvector

- **连接串**：`postgresql+asyncpg://user:pass@host:5432/db`
- **配置方式**：在 `.env` 中设置 `DATABASE_URL`
- **额外依赖**：`psycopg2-binary`、`asyncpg`、`pgvector`
- **向量检索**：由 `pgvector` 承载；当前阶段使用 ChromaDB 作为向量数据库（`CHROMA_PERSIST_DIR`）

### 数据库相关说明

| 文档/来源 | 内容 | 状态 |
|-----------|------|------|
| `database_schema.md`（根目录）头部 | 声称 PostgreSQL 15 + pgvector | **过时**，需修正 |
| `backend/app/core/database.py` | 实际代码：SQLite 优先 + PostgreSQL 兼容 | ✅ 已实现 |
| `backend/requirements.txt` | aiosqlite（已安装），psycopg2-binary/pgvector（注释，未安装） | ✅ 与现状一致 |

**建议**：将 `database_schema.md` 改为「架构目标」（PostgreSQL 为生产目标，SQLite 为当前实现）。

---

## 2. 前端框架：Next.js 15（非 Vite）

### 关键差异

| 维度 | Next.js 15 | Vite + React |
|------|------------|--------------|
| 路由 | App Router（文件系统路由） | 需配置 react-router |
| 构建产物 | `.next/`（Node.js SSR） | `dist/`（SPA，需静态托管） |
| 状态管理 | 服务端组件（SSC）为主 | 客户端 JS bundle |
| API 调用 | 可通过 `api.ts` + fetch 封装 | 无内置 SSR 层 |
| 环境配置 | `next.config.js` + `.env.local` | `vite.config.ts` + `.env` |
| 开发端口 | 默认 3000（脚本保端 3001） | 默认 5173 |

### 本项目实际情况

- **实际使用**：Next.js 15.5.26，App Router，React 18
- **配置**：`frontend/next.config.js`、`frontend/tailwind.config.ts`
- **构建输出**：`frontend/out/`（由 `npm run build:clean` 生成）
- **测试框架**：Vitest（`vitest` v3.2.7，仅用于纯逻辑断言；不跑 SSR）
- **CSS**：Tailwind CSS v3，自定义中国风配色（墨/朱砂/米黄/青铜）

### Vite 角色说明

`@vitejs/plugin-react` 出现在 `devDependencies` 中，是 **Vitest 测试运行时的内部依赖**（Vitest 基于 Vite），**不代表项目使用 Vite 构建**。

---

## 3. 项目分层结构

```
悟典/
├── README.md                         # 项目总览
├── frontend/                          # 前端（Next.js 15 App Router）
│   ├── app/                           # App Router 页面层
│   │   ├── layout.tsx                 # 根布局（含导航）
│   │   ├── page.tsx                   # 首页
│   │   ├── reader/                    # 阅读器页面
│   │   └── challenge/                 # 闯关页（占位）
│   ├── components/                    # 组件库
│   │   ├── Navbar.tsx
│   │   └── reader/
│   │       ├── ReadingView.tsx        # 核心：文白对照阅读器
│   │       ├── AnnotationPopup.tsx
│   │       ├── EntityCard.tsx
│   │       └── ChapterSelector.tsx
│   ├── lib/
│   │   ├── api.ts                     # API 客户端（2000+ 行，含 mock 数据）
│   │   ├── types.ts                   # TypeScript 类型定义
│   │   └── mockData.ts                # 内置 mock（论语前三章）
│   ├── public/                        # 静态资源
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                           # 后端（FastAPI）
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口，生命周期管理
│   │   ├── api/                       # API 路由层
│   │   │   ├── ai.py                  # AI 智能讲解（/api/ai/*）
│   │   │   ├── auth.py                # 认证（/api/auth/*）
│   │   │   ├── classics.py            # 经典文献（/api/classics/*）
│   │   │   ├── community.py           # 社区共学（/api/community/*）
│   │   │   ├── content.py             # 趣味内容（/api/content/*）
│   │   │   ├── debate.py              # 百家论道（/api/debate/*）
│   │   │   └── learning.py            # 学习游戏化（/api/learning/*）
│   │   ├── core/
│   │   │   ├── config.py              # 环境变量配置（pydantic-settings）
│   │   │   ├── database.py            # 数据库连接（SQLite/PG 自动切换）
│   │   │   ├── deps.py                # 依赖注入（认证中间件）
│   │   │   └── security.py            # JWT / 密码哈希
│   │   ├── models/                    # SQLAlchemy 2.0 ORM 模型
│   │   │   ├── user.py                # 用户
│   │   │   ├── classic.py             # 书/章/经文
│   │   │   ├── progress.py            # 学习进度
│   │   │   ├── srs_record.py          # SRS 间隔重复
│   │   │   ├── quiz.py                # 题库/答题记录
│   │   │   └── ...                    # 成就/笔记/社区/向量嵌入
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── services/                  # 业务服务层
│   │   │   ├── ai_service.py          # AI 调用服务
│   │   │   ├── llm_client.py          # LLM 客户端（多 provider 兼容）
│   │   │   ├── rag_service.py         # RAG 检索（ChromaDB）
│   │   │   ├── debate_engine.py       # 辩论引擎（三阶段状态机）
│   │   │   ├── debate_storage.py      # 辩论会话存储（JSON 文件）
│   │   │   ├── progress_service.py    # 学习进度服务
│   │   │   ├── srs_service.py         # SRS 调度服务
│   │   │   ├── community_service.py   # 社区服务（小组/打卡/PK/排行榜）
│   │   │   └── achievement_service.py # 成就服务
│   │   └── data/                      # 内嵌数据（classics_catalog.json 等）
│   ├── requirements.txt
│   ├── .env.example
│   └── migrations/                    # Alembic（空，待初始化）
│
├── docs/                              # 项目文档
│   ├── ENVIRONMENT.md                 # 环境变量清单（新建）
│   ├── DEPLOYMENT.md                  # 部署与运维指南（新建）
│   ├── ARCHITECTURE.md                # 架构说明（新建）
│   ├── hackathon/                     # 黑客松材料
│   └── superpowers/                   # 设计规划文档
│
├── data/                              # 数据目录
│   └── debates/                       # 辩论会话 JSON 文件
│
├── database_schema.md                 # 数据库 ER 图与表结构（需更新）
└── 不做清单.md                        # 排期外的技术决策记录
```

---

## 4. API 路由总览

| 前缀 | 功能 | 鉴权要求 |
|------|------|----------|
| `GET /` | 根路径（应用信息） | 无 |
| `GET /health` | 健康检查 | 无 |
| `GET /docs` / `/redoc` | Swagger / ReDoc 文档（仅开发模式） | 无 |
| `POST /api/ai/explain` | 逐句精讲 | demo/登录 |
| `POST /api/ai/translate` | 文白翻译 | demo/登录 |
| `POST /api/ai/chat-sage` | 圣贤对话（SSE 流式） | demo/登录 |
| `POST /api/ai/generate-quiz` | AI 生成测验题 | demo/登录 |
| `GET /api/ai/retrieve` | RAG 检索（调试） | demo/登录 |
| `GET /api/auth/*` | 注册/登录/刷新 Token | 无（登录/注册）/ 已登录（me/refresh） |
| `GET /api/classics/*` | 经典文献（书/章/经文/实体/每日一句） | 无需登录 |
| `POST /api/community/*` | 社区（小组/笔记/PK/排行榜） | 需登录 |
| `GET /api/content/*` | 趣味内容（金句卡片/小剧场/漫画） | 部分需登录 |
| `POST /api/debate/*` | 百家论道（辩论引擎，SSE 流式） | demo/登录 |
| `GET /api/learning/*` | 学习游戏化（进度/SRS/测验/成就） | 需登录 |
| `GET /api/exploration/*` | 探索（知识图谱/时间线/典故） | 无需登录 |

---

## 5. AI Provider 配置说明

`LLM_PROVIDER` 控制使用哪个 LLM 后端。所有 provider 均通过 OpenAI 兼容 API 协议接入。

```
LLM_PROVIDER=openai        → OPENAI_API_KEY + OPENAI_BASE_URL + OPENAI_MODEL
LLM_PROVIDER=agnes         → AGNES_API_KEY + AGNES_BASE_URL + AGNES_MODEL
LLM_PROVIDER=deepseek      → DEEPSEEK_API_KEY + DEEPSEEK_BASE_URL + DEEPSEEK_MODEL
LLM_PROVIDER=qwen          → QWEN_API_KEY + QWEN_BASE_URL + QWEN_MODEL
LLM_PROVIDER=local         → LOCAL_LLM_BASE_URL + LOCAL_LLM_MODEL（无需 API Key）
```

代码位置：`backend/app/core/config.py:199-231`

---

## 6. 已知技术债（影响运维）

详见 `deliverables/engineering-assurance/tech-debt-and-incident-full-audit-2026-09-25.md`

| 优先级 | 问题 | 位置 |
|--------|------|------|
| 🔴 P0 | 游戏化 EXP 可被无限刷分（客户端上报无上限） | `backend/app/api/learning.py:181-193` |
| 🔴 P0 | SSE chat-sage 错误被吞 + 未带 Authorization token | `frontend/lib/api.ts:1052-1113` |
| 🟠 P1 | 社区模块完全无鉴权（硬编码用户 1001） | `backend/app/api/community.py:50-52` |
| 🟠 P1 | JWT_SECRET_KEY 存在默认占位符 | `backend/app/core/config.py:49` |
| 🟠 P1 | Alembic 迁移目录为空，无 schema 演进路径 | `backend/migrations/` |
| 🟡 P2 | SQLite WAL/busy_timeout 未在所有路径生效 | `backend/app/core/database.py:40-46` |
| 🟡 P2 | API 响应契约三套并存（裸 response / APIResponse / dict） | 各 API 模块 |

# 环境变量清单

> 悟典项目 — 所有 `.env` 变量的用途、默认值、生成方式与必填性说明。
> 当前实际使用的是 SQLite（开发/演示），`DATABASE_URL` 切换为 PostgreSQL 连接串即可启用 PostgreSQL（生产目标）。

## 快速辨识

| 标记 | 含义 |
|------|------|
| **必填** | 启动前必须设置，否则行为异常或启动失败 |
| 选填 | 有合理默认值，可按需覆盖 |
| 🔒 敏感 | 含密钥/口令，不得提交到版本库 |

## 应用配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `APP_NAME` | `悟典` | 选填 | 应用名 |
| `APP_ENV` | `production` | 选填 | 环境：`development` / `staging` / `production` |
| `APP_DEBUG` | `false` | 选填 | 调试模式（生产环境强制禁止 `true`） |
| `APP_HOST` | `0.0.0.0` | 选填 | 后端监听地址 |
| `APP_PORT` | `8000` | 选填 | 后端监听端口 |

## 数据库配置

> 当前默认使用 SQLite（`sqlite+aiosqlite:///./wudian.db`）。
> 生产目标为 PostgreSQL，需设置 `DATABASE_URL` 并安装 `psycopg2-binary` + `asyncpg` + `pgvector`。

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `POSTGRES_USER` | `wudian` | 选填 | PostgreSQL 用户（仅 PostgreSQL 模式有效） |
| `POSTGRES_PASSWORD` | `""` | 选填 | PostgreSQL 密码（仅 PostgreSQL 模式有效） |
| `POSTGRES_HOST` | `localhost` | 选填 | PostgreSQL 主机 |
| `POSTGRES_PORT` | `5432` | 选填 | PostgreSQL 端口 |
| `POSTGRES_DB` | `wudian_db` | 选填 | PostgreSQL 数据库名 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./wudian.db` | 选填 | 数据库连接串。SQLite 默认；切换 PostgreSQL 示例：`postgresql+asyncpg://user:pass@host:5432/db` |

**生成 / 切换方式**：
- SQLite（默认）：无需操作，已预置。
- PostgreSQL：安装 PostgreSQL 15+ → `createdb wudian_db` → 设置 `DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wudian_db`。

## Redis 配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `REDIS_HOST` | `localhost` | 选填 | Redis 主机 |
| `REDIS_PORT` | `6379` | 选填 | Redis 端口 |
| `REDIS_DB` | `0` | 选填 | Redis 数据库编号 |
| `REDIS_PASSWORD` | `""` | 选填 | Redis 密码 |

> 当前代码中未实际调用 Redis（`redis_url` 属性已定义但无服务引用），暂为预留。

## JWT 认证 🔒 必填

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `JWT_SECRET_KEY` | — | **必填** | JWT 签名密钥，必须设置强随机值，否则启动失败 |
| `JWT_ALGORITHM` | `HS256` | 选填 | 签名算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 选填 | Access Token 有效期（分钟） |

**生成方式**：
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## OpenAI / AI 配置 🔒

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `OPENAI_API_KEY` | `""` | 选填 | OpenAI 兼容 API 密钥（LLM 调用默认来源） |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | 选填 | OpenAI 风格 API 基址 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 选填 | 默认 LLM 模型 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 选填 | 嵌入模型 |

## LLM Provider 切换 🔒

`LLM_PROVIDER` 决定当前使用哪个 LLM 后端，各 provider 的密钥按需填写。

| 变量 | 默认值 | 必填（当 provider 启用时） | 说明 |
|------|--------|------|------|
| `LLM_PROVIDER` | `openai` | 选填 | Provider：`openai` / `agnes` / `deepseek` / `qwen` / `local` |
| `AGNES_API_KEY` | `""` | 选填 | Agnes AI 密钥 |
| `AGNES_BASE_URL` | `https://apihub.agnes-ai.com/v1` | 选填 | Agnes AI 基址 |
| `AGNES_MODEL` | `agnes-2.0-flash` | 选填 | Agnes 模型 |
| `AGNES_IMAGE_MODEL` | `agnes-image-2.1-flash` | 选填 | Agnes 图像模型 |
| `DEEPSEEK_API_KEY` | `""` | 选填 | DeepSeek 密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | 选填 | DeepSeek 基址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 选填 | DeepSeek 模型 |
| `QWEN_API_KEY` | `""` | 选填 | Qwen（DashScope）密钥 |
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 选填 | Qwen 基址 |
| `QWEN_MODEL` | `qwen-plus` | 选填 | Qwen 模型 |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | 选填 | 本地 LLM（Ollama 等）基址 |
| `LOCAL_LLM_MODEL` | `qwen2.5:7b` | 选填 | 本地 LLM 模型名 |

## LLM 调用控制

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `LLM_TEMPERATURE` | `0.7` | 选填 | 生成温度 |
| `LLM_MAX_TOKENS` | `2000` | 选填 | 最大输出 token 数 |
| `LLM_TIMEOUT` | `60` | 选填 | 单次请求超时（秒） |
| `LLM_MAX_RETRIES` | `3` | 选填 | 最大重试次数 |
| `LLM_RETRY_DELAY` | `1.0` | 选填 | 重试间隔（秒） |

## 成本控制

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `DAILY_TOKEN_LIMIT` | `2000000` | 选填 | 每日 token 上限 |
| `TOKEN_COST_WARN_RATIO` | `0.8` | 选填 | 消耗预警比例 |

## RAG 配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `RAG_TOP_K` | `5` | 选填 | 检索返回条数 |
| `RAG_SIMILARITY_THRESHOLD` | `0.65` | 选填 | 相似度阈值 |
| `RAG_CHUNK_SIZE` | `300` | 选填 | 文本分块大小 |
| `RAG_CHUNK_OVERLAP` | `50` | 选填 | 分块重叠大小 |
| `RAG_EMBEDDING_PROVIDER` | `local` | 选填 | 嵌入提供方 |

## ChromaDB 向量数据库

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `CHROMA_PERSIST_DIR` | `./chroma_db` | 选填 | ChromaDB 持久化目录 |
| `CHROMA_COLLECTION` | `wudian_verses` | 选填 | ChromaDB 集合名 |

## CORS

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000",...5173]` | 选填 | 允许的跨域源（JSON 数组或逗号分隔字符串） |

## 辩论系统配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `DEBATE_MAX_ROUNDS` | `3` | 选填 | 辩论最大轮数 |
| `DEBATE_DEFAULT_PARTICIPANTS` | `["confucius","laozi","mozi","hanfeizi"]` | 选填 | 默认参与者 |
| `DEBATE_EXTRA_SAGES` | `[mencius, wang_yangming, ...]` | 选填 | 可召唤的额外先贤 |
| `DEBATE_STORAGE_DIR` | `data/debates` | 选填 | 辩论会话存储目录 |

## SRS 间隔重复算法

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `SRS_INITIAL_EASE_FACTOR` | `2.5` | 选填 | 初始易度因子 |
| `SRS_MINIMUM_EASE_FACTOR` | `1.3` | 选填 | 最小易度因子 |
| `SRS_INITIAL_INTERVAL` | `1` | 选填 | 初始间隔（天） |
| `SRS_EASY_BONUS` | `1.3` | 选填 | 容易奖励倍数 |

## 数据库实际状态

**当前默认：SQLite** — `DATABASE_URL=sqlite+aiosqlite:///./wudian.db`，文件位于 `backend/wudian.db`。

- 开发/演示环境直接使用，无需额外安装。
- 生产目标：PostgreSQL 15 + pgvector，切换方式见上方「数据库配置」。

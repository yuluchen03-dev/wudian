# 悟典

一句话定位：悟典是一个**可追溯的中国思想问答入口**，把经典原文、代表章节和注疏材料转成现代人能直接提问、能看到出处、能理解边界的思想启发服务。

## AI 配置

AI 调用通过 `LLM_PROVIDER` 切换后端，所有 provider 均使用 OpenAI 兼容协议：

| Provider | 必填变量 | 说明 |
|----------|----------|------|
| `openai`（默认） | `OPENAI_API_KEY` | OpenAI 模型（默认 `gpt-4o-mini`） |
| `agnes` | `AGNES_API_KEY` | Agnes AI（默认 `agnes-2.0-flash`） |
| `deepseek` | `DEEPSEEK_API_KEY` | DeepSeek（默认 `deepseek-chat`） |
| `qwen` | `QWEN_API_KEY` | 阿里 Qwen（默认 `qwen-plus`） |
| `local` | 无需密钥 | 本地 LLM（默认 `qwen2.5:7b`，需运行 Ollama） |

LLM 调用温度、最大 token 数、超时与重试可通过 `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` / `LLM_TIMEOUT` / `LLM_MAX_RETRIES` 调节。

完整 AI 配置变量列表见 `docs/ENVIRONMENT.md`。

## 环境变量配置

悟典后端使用 `.env` 文件加载环境变量。复制示例并填写：

```powershell
cd backend
copy .env.example .env
notepad .env
```

**必填项**：`JWT_SECRET_KEY`（使用 `python -c "import secrets; print(secrets.token_urlsafe(48))"` 生成）。

**数据库**：默认使用 SQLite（`DATABASE_URL=sqlite+aiosqlite:///./wudian.db`），无需额外安装。生产环境通过 `DATABASE_URL=postgresql+asyncpg://...` 切换到 PostgreSQL 15+。

完整变量列表与生成方式见 `docs/ENVIRONMENT.md`。

## 快速开始

### 1. 启动后端

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```powershell
cd frontend
npm run dev
```

### 3. 健康检查

```powershell
curl http://localhost:8000/
# 预期：{"app":"悟典","version":"0.1.0","status":"running","docs":"/docs"}

curl http://localhost:8000/health
# 预期：{"status":"healthy","healthy":true}
```

`/docs` 可查看 Swagger API 文档（仅 `APP_ENV=development` 时启用）。

### 4. 冒烟测试

详见 `docs/DEPLOYMENT.md`，核心路径：
1. `/api/classics/books` → 经典书目列表
2. `/api/classics/daily-quote` → 每日一句
3. `/api/debate/presets` → 预设话题
4. 前端 `http://localhost:3000/` → 首页可访问

### 5. 停止服务

按 `Ctrl+C` 停止前后端进程。

## 最快体验

评委和投资人现场只看一条主线：

`/demo -> 问题落案 -> 经典举证 -> 百家交锋 -> 思想判牒 -> /about`

1. 打开 `/demo`，直接进入思想审判场，无需登录即可在 90 秒内走完首个精选案件的四幕流程。
2. 第一幕「问」：选择精选案件或自由输入困惑，击鼓开审。
3. 第二幕「证」：查看经典举证，每条证据包含原文、出处、解释、适用边界和核验状态。
4. 第三幕「辩」：三位先贤（孔子、孟子、老子）分别发言，可追问、互问、站队。
5. 第四幕「判」：调节价值权重，查看核心矛盾、共识、分歧、今日行动和保留问题，落判收口。
6. 到 `/about` 看可信链路：先检索、再生成、可追溯、检索不到不硬编。

### 三个精选案件

- **职场认可**：我很努力，却总不被领导认可，怎么办？
- **职业去留**：稳定但不喜欢的工作，要不要离开？
- **功劳归属**：同事抢了我的功劳，我该争还是忍？

### 演示模式

- `curated`：精选案件，使用经校验的稳定数据，明确标注。
- `live`：自由提问，使用真实后端辩论 API，流式返回。
- `stable-demo`：后端不可用时的稳定演示替代，保留当前问题和舞台，可重试。

### 响应式验收

- 桌面 1440px：完整环形舞台，三席并立。
- 移动 390px：纵向四幕，单席切换，证据抽屉不超过 70dvh，无横向溢出。

## 运行命令

前端演示检查与启动：

```powershell
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
npm --prefix frontend run start:clean
```

开发态重启：

```powershell
npm --prefix frontend run dev:clean
```

默认演示口径：

- 前端连接 `http://localhost:8000/api`。
- `NEXT_PUBLIC_USE_MOCK=false`。
- 如果现场因为网络、模型或后端波动切到 mock，必须说明这是"演示稳定层"，用于让评委完整看到思想审判场四幕流程，不代表默认真实后端口径。

## 后端测试命令

```powershell
Push-Location backend; python -m pytest tests -q; Pop-Location
```

如果现场时间紧，至少确认后端服务监听在 `http://localhost:8000/api`，并运行根目录前端检查命令：

```powershell
npm --prefix frontend run stage-check
```

根目录也可以一次性运行前后端测试：

```powershell
npm run test
```

## Trae 贡献

Trae 协助团队把思想审判场四幕体验、启动检查、端口风险、可信链路证据页材料和交付文档整理成可复查流程。它的贡献不是替代产品核心能力，而是把黑客松项目从"能跑"推进到"能稳定上台演示、能被评委追问复查"。

## 演示稳定层兜底

悟典默认展示真实 API 口径；如需使用 mock、录屏或截图，统一表述为：

> 这是演示稳定层，用于保证现场完整看到产品路径。默认真实演示口径仍是连接本地悟典后端，并通过引用块、出处和边界提示展示可追溯回答。

## 投资与试点 CTA

悟典当前适合教育机构、文化内容 IP、心理健康前置陪伴场景和高校社团做小范围试点。欢迎投资人和合作方从 `docs/hackathon/investor-qa.md` 开始追问商业闭环、数据可信、安全边界和试点需求。

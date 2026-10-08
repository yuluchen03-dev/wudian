# 部署与运维

> 悟典项目 — 一键启动、健康检查、冒烟测试 & 事故速查卡

## 目录

1. [一键启动命令](#一键启动命令)
2. [健康检查方法](#健康检查方法)
3. [冒烟测试步骤](#冒烟测试步骤)
4. [事故速查卡](#事故速查卡)

---

## 一键启动命令

### 完整启动（PowerShell 推荐）

```powershell
# 1. 准备后端环境变量
cd backend
if (-not (Test-Path ".env")) { copy ".env.example" ".env" }
# 编辑 .env，确保 JWT_SECRET_KEY 有值
notepad .env

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动后端（开发模式）
# 环境变量 APP_ENV=development 时自动初始化数据库
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# --- 另一终端 ---

# 4. 准备前端环境变量
cd ..\frontend
if (-not (Test-Path ".env.local")) { copy ".env.example" ".env.local" }
notepad .env.local

# 5. 启动前端
npm install
npm run dev
```

前端默认连接 `http://localhost:8000/api`，如需修改：

```bash
# .env.local
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
NEXT_PUBLIC_USE_MOCK=false   # 生产演示使用真实后端
```

### 快速演示模式（仅演示，不需要 AI/LLM）

如果只需演示产品流程，且不依赖 AI 接口：

```powershell
# 后端（跳过 AI，启动即可）
Push-Location backend
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
Pop-Location

# 前端（开启 Mock 模式）
Push-Location frontend
npm run dev
Pop-Location
```

---

## 健康检查方法

### 后端健康检查

| 目的 | 命令 |
|------|------|
| 根路径状态 | `curl http://localhost:8000/` |
| 详细健康 | `curl http://localhost:8000/health` |
| API 文档（开发） | 访问 `http://localhost:8000/docs` |

**预期响应**：

```json
// GET /
{
  "app": "悟典",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

```json
// GET /health
{
  "status": "healthy",
  "healthy": true
}
```

### 前端健康检查

| 目的 | 命令 |
|------|------|
| 前端响应 | `curl http://localhost:3000/` |
| 构建检查 | `npm --prefix frontend run build:clean` |

### 端口占用检查

```powershell
netstat -ano | findstr "8000\|3000"
```

---

## 冒烟测试步骤

> 约 3-5 分钟，验证关键路径是否正常工作。

### 1. 后端基础

```powershell
# 依赖检查
cd backend
.venv\Scripts\activate
python -c "from app.main import app; print('OK')"

# 健康检查
curl http://localhost:8000/ | jq .
curl http://localhost:8000/health | jq .

# 数据库初始化验证
ls -la wudian.db   # 检查 SQLite 数据库文件是否创建
```

### 2. 经典阅读功能

```bash
curl http://localhost:8000/api/classics/books | jq '.[].id'
# 预期：["lunyu","daodejing","zhuangzi","mengzi",...]

curl http://localhost:8000/api/classics/daily-quote | jq '.data.book_id'
# 预期：非空
```

### 3. AI 智能讲解（若配置了 API_KEY）

```bash
# 使用 curl 模拟请求
curl -X POST http://localhost:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"verse_id":"1-1","text":"学而时习之"}'
```

> 若未配置 `OPENAI_API_KEY`，后端会返回降级回复，不会报错。

### 4. 前端访问

打开浏览器：

- 首页：`http://localhost:3000/`
- 阅读器：`http://localhost:3000/reader?book_id=lunyu&chapter_id=1`
- 每日一句：点击首页的「每日一句」卡片

### 5. 测试套件快速跑一遍

```powershell
# 前端
npm --prefix frontend run test:runtime-assets || true

# 后端
Push-Location backend; python -m pytest tests -q --tb=short; Pop-Location
```

---

## 事故速查卡

### 速照表

| 现象 | 可能原因 | 快速排查 | 解决办法 |
|------|----------|----------|----------|
| 前端报 `500` 或空白 | 后端未启动 | `curl localhost:8000/` | 启动后端 |
| `/api/ai/chat-sage` 无返回 | `OPENAI_API_KEY` 空或额度耗尽 | 查看终端日志 `⚠️ LLM 客户端未就绪` | 填写 API_KEY 或切 mock |
| 登录后跳转 404 | 前端端口不对 | 检查 `NEXT_PUBLIC_API_BASE` | 确认指向 `http://localhost:8000/api` |
| 数据库锁死 | SQLite 并发写 | 查看 `PRAGMA busy_timeout` | 增大 `database.py:connect_args.timeout` |
| Swagger `/docs` 404 | `APP_ENV=production` | 检查环境变量 | 开发时设 `APP_ENV=development` |
| `JWT_SECRET_KEY` 未设置 | 启动即报错 | 查看终端首行警告 | 生成密钥：`python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| 前端 `Mount Error` | React Hooks 顺序错误 | 查看浏览器控制台 | 已修复，确保使用最新代码 |
| 静态资源 404 | `public/agens/` 缺失 PNG | 检查 `frontend/public/` | 复制缺失图片至对应路径 |
| 端口被占 | 旧进程未关 | `netstat -ano \| port 8000` | `taskkill /F /PID <pid>` |
| SSE 流断连 | 网络波动 | 观察浏览器 Network 面板 | 刷新页面或检查 `keep-alive` |

### 常见命令

```powershell
# 查看后端进程
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue

# 强制结束占用端口的进程
$pid = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
if ($pid) { taskkill /F /PID $pid }

# 查看 SQLite 表结构
sqlite3 backend\wudian.db ".tables"

# 查看环境变量
Get-Content backend\.env | Select-String "JWT_SECRET_KEY"
```

### 生产简要检查清单

| 步骤 | 检查项 |
|------|--------|
| 1 | `APP_ENV=production`、`APP_DEBUG=false` |
| 2 | `JWT_SECRET_KEY` 为 48+ 字符强随机 |
| 3 | `DATABASE_URL` 指向生产 PostgreSQL |
| 4 | 前端 `NEXT_PUBLIC_USE_MOCK=false` |
| 5 | `/` 与 `/health` 返回 `status: running` + `healthy: true` |
| 6 | `npm run build:clean` 可成功构建前端 |

---

## 附录：环境变量要点

- **必填**：`JWT_SECRET_KEY`
- **默认 SQLite**：无需额外配置，启动即用
- **生产 PostgreSQL**：安装 `psycopg2-binary`, `asyncpg`, `pgvector`，并在 `.env` 中配置 `DATABASE_URL`

参考详见 `docs/ENVIRONMENT.md`。
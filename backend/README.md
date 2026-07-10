# 悟典 - 后端架构

> 四书五经互动学习平台后端服务

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | 0.109.0 |
| ASGI 服务器 | Uvicorn | 0.27.0 |
| ORM | SQLAlchemy 2.0 (async) | 2.0.25 |
| 数据库迁移 | Alembic | 1.13.1 |
| 数据库 | PostgreSQL + pgvector | 15+ |
| 数据验证 | Pydantic | 2.5.3 |
| 认证 | python-jose (JWT) + passlib (bcrypt) | - |
| 缓存 | Redis | 5.0.1 |
| AI/LLM | OpenAI + LangChain | - |
| 向量数据库 | ChromaDB + pgvector | - |

## 目录结构

```
backend/
├── app/                      # 主应用
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── api/                 # API 路由
│   │   └── __init__.py
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py        # 环境变量与配置
│   │   └── database.py      # 数据库连接管理
│   ├── models/              # 数据模型 (ORM)
│   │   ├── __init__.py      # 模型导出
│   │   ├── base.py          # 基础 Mixin
│   │   ├── user.py          # 用户表
│   │   ├── classic.py       # 经典文献 (书/章/经文)
│   │   ├── progress.py      # 学习进度
│   │   ├── srs_record.py    # SRS 间隔重复
│   │   ├── quiz.py          # 题库与答题记录
│   │   ├── achievement.py   # 成就系统
│   │   ├── note.py          # 笔记与点赞
│   │   ├── community.py     # 社区 (小组/PK)
│   │   └── embedding.py     # 向量嵌入与AI对话
│   └── services/            # 业务服务层
│       └── __init__.py
├── migrations/              # 数据库迁移 (Alembic)
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量示例
└── README.md                # 本文件
```

## 快速开始

## 黑客松演示运行口径

本地黑客松演示默认使用 SQLite、本地经典数据和可追溯引用链路，保证评委能稳定看到 `/demo -> /sage-chat -> /about -> /roundtable` 的核心路径。

ChromaDB 是可选向量索引，用于增强本地语义检索；没有向量索引时，演示仍应以本地经典数据、引用块、出处和边界提示为准。LLM provider 通过 `.env` 配置，现场如因网络或额度波动切到 mock/稳定层，需要主动说明。

PostgreSQL、Redis 和 pgvector 是后续生产化方向，不是本地黑客松演示的必需前置。现场优先确认 SQLite 数据、后端测试和前端 stage-check 可运行。

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库准备

```sql
-- 创建数据库
CREATE DATABASE wudian_db;

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 4. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python -m app.main
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 数据库表结构

共 15 张表，详细 ER 图见项目根目录 `database_schema.md`

| 表名 | 说明 |
|------|------|
| `users` | 用户信息与学习状态 |
| `classic_books` | 经典书籍（四书五经） |
| `chapters` | 章节 |
| `verses` | 经文（最小学习单元） |
| `progress` | 学习进度 |
| `srs_records` | SRS 间隔重复调度 |
| `quizzes` | 题库 |
| `quiz_records` | 答题记录 |
| `achievements` | 成就徽章 |
| `notes` | 用户笔记 |
| `note_likes` | 笔记点赞 |
| `study_groups` | 学习小组 |
| `group_members` | 小组成员 |
| `pk_matches` | PK 对战 |
| `verse_embeddings` | 经文向量嵌入 |
| `ai_chat_logs` | AI 对话记录 |

## 设计原则

1. **时间戳**: 所有表包含 `created_at` 和 `updated_at`
2. **软删除**: 大部分表包含 `is_deleted` 字段
3. **外键约束**: 用户相关表通过 `user_id` 外键关联
4. **索引优化**: 针对常用查询路径建立复合索引
5. **级联删除**: 外键设置 `ON DELETE CASCADE` 保证数据一致性
6. **向量检索**: 使用 pgvector 存储语义向量，支持相似度检索

## API 路由规划

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/auth` | 注册/登录/Token |
| 用户 | `/api/users` | 用户信息/统计 |
| 经典文献 | `/api/classics` | 书/章/经文 |
| 学习进度 | `/api/progress` | 进度查询/更新 |
| SRS | `/api/srs` | 复习调度 |
| 题库 | `/api/quiz` | 答题/记录 |
| 笔记 | `/api/notes` | 笔记CRUD |
| 社区 | `/api/community` | 小组/PK |
| AI问答 | `/api/ai` | 智能对话 |

# 悟典 - 数据库 Schema 设计文档

> 四书五经互动学习平台 · 数据库 ER 图与表结构说明

## 概览

- **数据库**: PostgreSQL 15+ (配合 pgvector 扩展)
- **ORM**: SQLAlchemy 2.0 (async)
- **总表数**: 16 张
- **设计原则**: 全表时间戳 + 软删除 + 外键级联 + 复合索引优化

---

## ER 关系总览

```
┌─────────────┐       ┌──────────────┐       ┌─────────┐
│   users     │       │ classic_books│       │ verses  │
│─────────────│       │──────────────│       │─────────│
│ id (PK)     │◄──┐   │ id (PK)      │◄──┐   │ id (PK) │
│ username    │   │   │ title        │   │   │ book_id │──►classic_books
│ email       │   │   │ category     │   ├───┤ chapter_id│──►chapters
│ level       │   │   └──────────────┘   │   │ original_text │
│ exp_points  │   │          ▲           │   └────┬────┘
│ streak_days │   │          │           │        │
└──────┬──────┘   │   ┌──────┴────┐      │        │
       │          │   │  chapters │      │        │
       │          │   │───────────│      │        │
       │          │   │ id (PK)   │      │        │
       │          │   │ book_id   │──────┘        │
       │          │   │ chapter#  │               │
       │          │   └───────────┘               │
       │          │                               │
       │◄─────────┼───────────────────────────────┤
       │          │                               │
       ▼          ▼                               ▼
┌────────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐
│  progress  │  │srs_records│  │  notes   │  │ quizzes│
│────────────│  │───────────│  │──────────│  │────────│
│ user_id    │  │ user_id   │  │ user_id  │  │verse_id│
│ verse_id   │  │ verse_id  │  │ verse_id │  │ type   │
│ status     │  │ease_factor│  │ content  │  │ answer │
│mastery_lvl │  │interval_d │  │ likes    │  └───┬────┘
│last_review │  │next_review│  └────┬─────┘      │
└────────────┘  └───────────┘       │            ▼
                                    │     ┌─────────────┐
                                    │     │quiz_records │
                                    │     │─────────────│
                                    │     │ user_id     │
                                    │     │ quiz_id     │
                                    │     │ is_correct  │
                                    │     └─────────────┘
                                    │
              ┌─────────────────────┘
              ▼
       ┌─────────────┐
       │ note_likes  │
       │─────────────│
       │ user_id     │
       │ note_id     │
       └─────────────┘

┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│ achievements  │  │ study_groups │  │ pk_matches   │
│───────────────│  │──────────────│  │──────────────│
│ user_id       │  │ owner_id     │  │ player1_id   │
│ badge_type    │  │ name         │  │ player2_id   │
│ tier          │  │ current_book │  │ status       │
└───────────────┘  └──────┬───────┘  │ winner       │
                          │          └──────────────┘
                          ▼
                 ┌────────────────┐
                 │ group_members  │
                 │────────────────│
                 │ group_id       │
                 │ user_id        │
                 │ role           │
                 └────────────────┘

┌────────────────────┐  ┌──────────────┐
│ verse_embeddings   │  │ ai_chat_logs │
│────────────────────│  │──────────────│
│ verse_id           │  │ user_id      │
│ embedding (vector) │  │ verse_id     │
│ model_name         │  │ role         │
└────────────────────┘  │ content      │
                        └──────────────┘
```

---

## 表结构详情

### 1. users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| username | String(50) | UNIQUE, NOT NULL | 用户名 |
| email | String(255) | UNIQUE, NOT NULL | 邮箱 |
| hashed_password | String(255) | NOT NULL | 加密密码 |
| avatar | String(500) | NULL | 头像 URL |
| nickname | String(50) | NULL | 昵称 |
| bio | Text | NULL | 个人简介 |
| level | Integer | DEFAULT 1 | 用户等级 |
| exp_points | Integer | DEFAULT 0 | 经验值 |
| streak_days | Integer | DEFAULT 0 | 连续学习天数 |
| total_study_days | Integer | DEFAULT 0 | 总学习天数 |
| total_verses_learned | Integer | DEFAULT 0 | 已学经文数 |
| is_active | Boolean | DEFAULT TRUE | 是否激活 |
| is_superuser | Boolean | DEFAULT FALSE | 是否管理员 |
| last_login_at | DateTime | NULL | 最后登录时间 |
| last_study_at | DateTime | NULL | 最后学习时间 |
| is_deleted | Boolean | DEFAULT FALSE, INDEX | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_users_username`, `idx_users_email`, `idx_users_is_deleted`

---

### 2. classic_books — 经典书籍表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| title | String(100) | UNIQUE, NOT NULL, INDEX | 书名 |
| category | String(50) | NOT NULL, INDEX | 分类：四书/五经 |
| description | Text | NULL | 书籍简介 |
| author | String(100) | NULL | 作者/编者 |
| era | String(50) | NULL | 朝代 |
| sort_order | Integer | DEFAULT 0 | 排序序号 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

---

### 3. chapters — 章节表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| book_id | Integer | FK→classic_books.id, INDEX, NOT NULL | 书籍 ID |
| chapter_number | Integer | NOT NULL | 章节序号 |
| title | String(200) | NOT NULL | 章节标题 |
| description | Text | NULL | 章节简介 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**复合索引**: `idx_chapter_book(book_id, chapter_number)`

---

### 4. verses — 经文表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| book_id | Integer | FK→classic_books.id, INDEX, NOT NULL | 书籍 ID |
| chapter_id | Integer | FK→chapters.id, INDEX, NOT NULL | 章节 ID |
| verse_number | Integer | NOT NULL | 经文序号 |
| original_text | Text | NOT NULL | 原文 |
| translation | Text | NULL | 白话翻译 |
| annotation | Text | NULL | 注释 |
| interpretation | Text | NULL | 解读/义理 |
| pinyin | Text | NULL | 拼音标注 |
| audio_url | String(500) | NULL | 朗读音频 URL |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**复合索引**: `idx_verse_chapter(chapter_id, verse_number)`, `idx_verse_book(book_id)`

---

### 5. progress — 学习进度表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| book_id | Integer | FK→classic_books.id, NOT NULL | 书籍 ID |
| chapter_id | Integer | FK→chapters.id, NOT NULL | 章节 ID |
| verse_id | Integer | FK→verses.id, NOT NULL | 经文 ID |
| status | String(20) | DEFAULT 'not_started' | 学习状态 |
| mastery_level | Float | DEFAULT 0.0 | 掌握程度 0-1 |
| study_count | Integer | DEFAULT 0 | 学习次数 |
| study_duration | Integer | DEFAULT 0 | 累计学习时长（秒）|
| last_reviewed | DateTime | NULL | 最后复习时间 |
| next_review_date | DateTime | NULL | 下次复习日期 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**唯一约束**: `uq_progress_user_verse(user_id, verse_id)`
**索引**: `idx_progress_user`, `idx_progress_chapter`, `idx_progress_status`

**status 枚举**: `not_started` → `learning` → `reviewed` → `mastered`

---

### 6. srs_records — SRS 间隔重复调度表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| verse_id | Integer | FK→verses.id, NOT NULL | 经文 ID |
| ease_factor | Float | DEFAULT 2.5 | 容易度因子（最小1.3）|
| interval_days | Integer | DEFAULT 1 | 当前间隔天数 |
| repetitions | Integer | DEFAULT 0 | 成功复习次数 |
| last_review_date | Date | NULL | 上次复习日期 |
| next_review_date | Date | NOT NULL, INDEX | 下次复习日期 |
| last_rating | Integer | NULL | 上次评分 0-5 |
| total_reviews | Integer | DEFAULT 0 | 总复习次数 |
| lapse_count | Integer | DEFAULT 0 | 遗忘次数 |
| status | String(20) | DEFAULT 'new' | 调度状态 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**唯一约束**: `uq_srs_user_verse(user_id, verse_id)`
**复合索引**: `idx_srs_user_next(user_id, next_review_date)`, `idx_srs_next_review(next_review_date)`

**status 枚举**: `new` → `learning` → `review` → `relearning` / `suspended`

**SM-2 算法说明**:
- `ease_factor`: 初始 2.5，根据评分调整，最低 1.3
- `interval_days`: 第1次=1天，第2次=6天，之后 = 上次间隔 × ease_factor
- `repetitions`: 评分≥3时+1，<3时重置为0

---

### 7. quizzes — 题库表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| quiz_type | String(30) | NOT NULL, INDEX | 题型 |
| book_id | Integer | FK→classic_books.id, NOT NULL | 书籍 ID |
| chapter_id | Integer | FK→chapters.id, NULL | 章节 ID |
| verse_id | Integer | FK→verses.id, NULL | 经文 ID |
| question | Text | NOT NULL | 题干 |
| options | JSON | NULL | 选项（JSON数组）|
| answer | Text | NOT NULL | 正确答案 |
| explanation | Text | NULL | 答案解析 |
| difficulty | Integer | DEFAULT 1 | 难度 1-5 |
| tags | JSON | NULL | 标签 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**复合索引**: `idx_quiz_type_difficulty(quiz_type, difficulty)`, `idx_quiz_verse(verse_id)`, `idx_quiz_chapter(chapter_id)`

**quiz_type 枚举**: `choice`(选择) / `fill`(填空) / `match`(匹配) / `translate`(翻译) / `explain`(释义) / `order`(排序)

---

### 8. quiz_records — 答题记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| quiz_id | Integer | FK→quizzes.id, NOT NULL | 题目 ID |
| user_answer | Text | NOT NULL | 用户作答 |
| is_correct | Integer | NOT NULL | 是否正确（0/1）|
| score | Float | DEFAULT 0.0 | 得分 |
| time_spent | Integer | DEFAULT 0 | 耗时（秒）|
| answered_at | DateTime | NOT NULL | 答题时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_quiz_record_user(user_id)`, `idx_quiz_record_user_quiz(user_id, quiz_id)`

---

### 9. achievements — 成就表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| badge_type | String(50) | NOT NULL | 徽章类型 |
| badge_name | String(100) | NOT NULL | 徽章名称 |
| badge_icon | String(500) | NULL | 徽章图标 |
| description | String(500) | NULL | 成就描述 |
| tier | String(20) | DEFAULT 'bronze' | 成就等级 |
| exp_reward | Integer | DEFAULT 0 | 经验值奖励 |
| created_at | DateTime | DEFAULT NOW() | 获得时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_achievement_user(user_id)`, `idx_achievement_user_type(user_id, badge_type)`

**tier 枚举**: `bronze`(铜) / `silver`(银) / `gold`(金) / `platinum`(铂金)

---

### 10. notes — 笔记表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| verse_id | Integer | FK→verses.id, NOT NULL | 经文 ID |
| title | String(200) | NULL | 笔记标题 |
| content | Text | NOT NULL | 笔记内容（Markdown）|
| is_public | Boolean | DEFAULT FALSE | 是否公开 |
| likes | Integer | DEFAULT 0 | 点赞数 |
| favorites | Integer | DEFAULT 0 | 收藏数 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_note_user`, `idx_note_verse`, `idx_note_user_verse(user_id, verse_id)`

---

### 11. note_likes — 笔记点赞表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 点赞用户 ID |
| note_id | Integer | FK→notes.id, NOT NULL | 笔记 ID |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_note_like_user`, `idx_note_like_note`

---

### 12. study_groups — 学习小组表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| name | String(100) | NOT NULL | 小组名称 |
| description | String(500) | NULL | 小组简介 |
| owner_id | Integer | FK→users.id, NOT NULL | 创建者 ID |
| current_book_id | Integer | FK→classic_books.id, NULL | 当前学习书籍 |
| group_type | String(20) | DEFAULT 'public' | 小组类型 |
| max_members | Integer | DEFAULT 50 | 最大成员数 |
| member_count | Integer | DEFAULT 1 | 当前成员数 |
| invite_code | String(20) | UNIQUE, NULL | 邀请码 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**group_type 枚举**: `public`(公开) / `private`(私密)

---

### 13. group_members — 小组成员表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| group_id | Integer | FK→study_groups.id, NOT NULL | 小组 ID |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| role | String(20) | DEFAULT 'member' | 成员角色 |
| joined_at | DateTime | NOT NULL | 加入时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**唯一约束**: `uq_group_member(group_id, user_id)`
**索引**: `idx_group_member_user(user_id)`

**role 枚举**: `owner`(创建者) / `admin`(管理员) / `member`(成员)

---

### 14. pk_matches — PK 对战表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| player1_id | Integer | FK→users.id, NOT NULL | 玩家1 ID |
| player2_id | Integer | FK→users.id, NULL | 玩家2 ID |
| book_id | Integer | FK→classic_books.id, NULL | 对战书籍 |
| question_count | Integer | DEFAULT 10 | 题目数量 |
| status | String(20) | DEFAULT 'waiting' | 对战状态 |
| player1_score | Integer | DEFAULT 0 | 玩家1得分 |
| player2_score | Integer | DEFAULT 0 | 玩家2得分 |
| winner | Integer | NULL | 胜者（1/2/0平局）|
| started_at | DateTime | NULL | 开始时间 |
| ended_at | DateTime | NULL | 结束时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_pk_match_user1`, `idx_pk_match_user2`, `idx_pk_match_status`

**status 枚举**: `waiting`(等待匹配) → `ongoing`(进行中) → `completed`(已完成) / `cancelled`(已取消)

---

### 15. verse_embeddings — 经文向量嵌入表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| verse_id | Integer | FK→verses.id, UNIQUE, NOT NULL | 经文 ID |
| embedding | Vector(1536) | NOT NULL | 语义向量（pgvector）|
| source_text | Text | NOT NULL | 嵌入源文本 |
| model_name | String(100) | DEFAULT 'text-embedding-3-small' | 嵌入模型 |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_embedding_verse(verse_id)` + HNSW 向量索引

> **注意**: 需要先在 PostgreSQL 中执行 `CREATE EXTENSION IF NOT EXISTS vector;`

---

### 16. ai_chat_logs — AI 对话记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| user_id | Integer | FK→users.id, NOT NULL | 用户 ID |
| verse_id | Integer | FK→verses.id, NULL | 相关经文 ID |
| role | String(20) | NOT NULL | 对话角色 |
| content | Text | NOT NULL | 对话内容 |
| session_id | String(100) | NULL | 会话 ID |
| context_verse_ids | Text | NULL | 上下文经文ID（JSON）|
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW() | 更新时间 |

**索引**: `idx_chat_user(user_id)`, `idx_chat_user_verse(user_id, verse_id)`

**role 枚举**: `user`(用户) / `assistant`(AI助手)

---

## 关系汇总

| 子表 | 父表 | 外键 | 关系类型 | 级联 |
|------|------|------|----------|------|
| chapters | classic_books | book_id | 1:N | CASCADE |
| verses | classic_books | book_id | 1:N | CASCADE |
| verses | chapters | chapter_id | 1:N | CASCADE |
| progress | users | user_id | 1:N | CASCADE |
| progress | verses | verse_id | 1:N | CASCADE |
| srs_records | users | user_id | 1:N | CASCADE |
| srs_records | verses | verse_id | 1:N | CASCADE |
| quizzes | verses | verse_id | 1:N | CASCADE |
| quiz_records | users | user_id | 1:N | CASCADE |
| quiz_records | quizzes | quiz_id | 1:N | CASCADE |
| achievements | users | user_id | 1:N | CASCADE |
| notes | users | user_id | 1:N | CASCADE |
| notes | verses | verse_id | 1:N | CASCADE |
| note_likes | users | user_id | 1:N | CASCADE |
| note_likes | notes | note_id | 1:N | CASCADE |
| study_groups | users | owner_id | 1:N | CASCADE |
| group_members | study_groups | group_id | 1:N | CASCADE |
| group_members | users | user_id | 1:N | CASCADE |
| pk_matches | users | player1_id | 1:N | CASCADE |
| pk_matches | users | player2_id | 1:N | CASCADE |
| verse_embeddings | verses | verse_id | 1:1 | CASCADE |
| ai_chat_logs | users | user_id | 1:N | CASCADE |

---

## 索引策略

| 查询场景 | 使用的索引 |
|----------|-----------|
| 按 book_id 查章节列表 | `idx_chapter_book(book_id, chapter_number)` |
| 按 chapter_id 查经文列表 | `idx_verse_chapter(chapter_id, verse_number)` |
| 按 book_id 查所有经文 | `idx_verse_book(book_id)` |
| 按 user_id 查学习进度 | `idx_progress_user(user_id)` |
| 按 user_id + verse_id 查进度 | `uq_progress_user_verse(user_id, verse_id)` |
| 查今日待复习经文 | `idx_srs_next_review(next_review_date)` |
| 查用户待复习列表 | `idx_srs_user_next(user_id, next_review_date)` |
| 按题型+难度筛选题目 | `idx_quiz_type_difficulty(quiz_type, difficulty)` |
| 查用户笔记列表 | `idx_note_user(user_id)` |
| 向量相似度检索 | HNSW index on `embedding` |

---

## 数据库扩展

```sql
-- pgvector 扩展（向量存储与检索）
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建 HNSW 向量索引（余弦距离）
CREATE INDEX idx_verse_embedding_hnsw ON verse_embeddings
    USING hnsw (embedding vector_cosine_ops);
```

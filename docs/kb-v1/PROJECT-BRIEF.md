# PROJECT: WUDIAN-KB-V1
# 悟典可信中国思想知识库 V1

仓库：
https://github.com/yuluchen03-dev/wudian

你的工作方式：
你现在不是单一开发 Agent，而是一个软件工程专家团。

必须采用：
【分析 → 规划 → 实施 → 单元测试 → 独立 Review → 修复 → Gate 验收】

禁止：
- 一次性全仓库乱改
- 未读取现有实现就重构
- 为了“完成任务”删除测试
- 用 mock 假装真实 RAG 成功
- 写 TODO 后宣称完成
- 只检查 HTTP 200 就宣称功能通过
- AI 生成古籍文本后当成权威原典
- 无法核验来源时编造 source
- 为了让测试通过降低断言
- 大规模推翻现有架构

==================================================
一、项目最终目标
==================================================

把当前“悟典”从：

古籍内容 + LLM + 小规模 RAG + 百家角色扮演

升级为：

【现代现实问题
 → 问题结构化
 → 中国思想概念映射
 → 权威原典检索
 → 历代注疏检索
 → 多学派 Evidence Pack
 → LLM 推理
 → Citation Guard
 → Quote Verifier
 → Trust State
 → 可追溯回答】

产品定位：

“让中国思想真正回答今天的问题。”

核心可信承诺：

“每个观点都能追到原典；找不到，就不硬编。”

==================================================
二、必须保留的现有能力
==================================================

先完整阅读仓库。

重点检查：

backend/app/services/rag_service.py
backend/app/services/citation_validator.py
backend/app/services/debate_engine.py
backend/app/services/knowledge_graph.py
backend/app/services/classics_service.py

data/processed/
backend/data/commentaries/
backend/tests/

不得推倒已有：

- FastAPI
- ChromaDB
- 当前 RAGService
- 多 Provider LLM
- debate engine
- citation validator
- knowledge graph
- 前端“问 → 证 → 辩 → 判”主流程

原则：

【增量升级，不重写项目】

==================================================
三、专家团角色
==================================================

必须建立以下角色。

1. Lead Architect
负责：
- 当前仓库审计
- 架构方案
- Task 拆解
- dependency graph
- 每阶段 Gate

不得：
- 跳过 Review

2. Product Research Expert
负责将市场需求转成产品 requirements：

P0：
- 防 AI 编造古籍
- 现代问题能检索到古典思想
- 答案不能空泛
- 多学派差异真实存在

P1：
- 原文/注疏/AI解释明确分层
- 回答最终给现代行动建议
- 支持用户继续追问

3. Classical Knowledge Engineer
负责：
- 原典数据 Schema
- 注疏 Schema
- 版本信息
- 来源信息
- 校验状态
- 概念标签
- 现代问题映射

严禁 AI 自己编造原典。

4. Retrieval / RAG Expert

负责升级：

Query Understanding
+
Modern Scenario Mapping
+
Concept Expansion
+
BM25
+
Dense Retrieval
+
Metadata Filter
+
Reranker
+
Diversity Selection

5. Trust & Verification Expert

实现：

Citation Whitelist

Verbatim Quote Verification

Source Attribution Verification

Claim-Evidence Binding

Trust State

至少支持：

verified
citation_corrected
quote_relaxed
insufficient_evidence

6. Backend Engineer

负责：
- 数据模型
- ingestion
- indexing
- search API
- verify API
- evidence API
- backward compatibility

7. Frontend Engineer

负责：

Evidence Drawer

每条证据必须显示：

原文
出处
书名
篇章
文本类型
注疏者
数据来源
校验状态
可信等级

8. Evaluation Engineer

建立独立 Eval。

9. Independent QA Reviewer

只能：
- Review
- 跑测试
- 提 bug
- Gate

不得直接实现核心功能。

==================================================
四、V1 知识库范围
==================================================

不要追求几万本古籍。

第一版优先支持：

儒家：
《论语》
《孟子》
《荀子》
《大学》
《中庸》

道家：
《道德经》
《庄子》

墨家：
《墨子》

法家：
《韩非子》
《商君书》

后世：
《传习录》

可选：
《孙子兵法》

==================================================
五、知识结构
==================================================

构建五层：

L1 权威原典
L2 历代注疏
L3 人物/学派/概念
L4 思想概念
L5 现代问题

禁止把这些层混成普通 chunk。

==================================================
六、核心 Passage Schema
==================================================

至少设计：

passage_id

book_id
book_title

chapter_id
chapter_title

section
line_no

original
original_traditional
original_simplified

source_provider
source_url
source_edition

author
dynasty

text_type:
- original
- commentary
- translation
- modern_explanation

commentator
commentary_dynasty

school

concepts[]

modern_topics[]

modern_scenarios[]

stance

verification_level

proofread_status

license

embedding_version

created_at
updated_at

要求：

原典和注疏必须分开储存。

==================================================
七、现代问题结构化
==================================================

必须新增 Modern Issue Ontology。

至少覆盖：

career
workplace_conflict
leadership
achievement
money
competition

family
parent_child
marriage
friendship

anxiety
failure
anger
loneliness
self_doubt

choice
responsibility
justice
fairness
meaning
ambition

用户输入：

“同事抢了我的功劳，我该不该跟他撕破脸？”

不能直接丢给 embedding。

先转换：

scene:
workplace_conflict

actors:
self
peer

conflict:
fairness
relationship

emotion:
anger
frustration

choices:
confront
communicate
escalate
tolerate
leave

concepts:
义
礼
正名
不争
尚贤
名实
赏罚

再检索原典。

==================================================
八、RAG V2
==================================================

现有 hash embedding 只能保留做 fallback。

正式检索：

Stage 1
Query Analyzer

↓

Stage 2
Modern → Classical Query Expansion

↓

Stage 3
Hybrid Retrieval

BM25
+
Dense Embedding

↓

Stage 4
Metadata Filtering

school
book
text_type
person
concept

↓

Stage 5
Reranker

↓

Stage 6
Diversification

禁止 Top5 全来自同一 passage/同一章。

↓

Stage 7
Evidence Pack

==================================================
九、Evidence Pack
==================================================

LLM 不允许直接随便读数据库。

必须先生成：

EvidencePack {
 query
 scenario
 concepts

 evidence: [
   {
     evidence_id
     original
     source
     school
     text_type
     commentary
     relevance
     verification
   }
 ]
}

LLM 只能引用 Evidence Pack 中存在的 source。

==================================================
十、Citation Guard
==================================================

必须实现白名单。

如果模型返回：

quote
source

Quote 必须：

1. 存在于 Evidence Pack

或者

2. 被 QuoteVerifier 在原始知识库中精确找到

否则：

verifiable=false

不得展示成“经典原文”。

==================================================
十一、Quote Verifier
==================================================

新增独立能力：

POST /api/knowledge/verify-quote

输入：

{
 "quote": "...",
 "claimed_source": "..."
}

输出：

{
 "quote_exists": true,
 "exact_match": true,
 "source_correct": false,
 "correct_source": "...",
 "similarity": 1.0,
 "trust_state": "citation_corrected"
}

必须区分：

【这句话存在】

与

【出处正确】

这是两个指标。

==================================================
十二、Trust State
==================================================

所有 AI 回答必须存在：

trust_state

至少：

verified

citation_corrected

quote_relaxed

insufficient_evidence

如果没有可靠证据：

不允许编古文。

必须明确：

“当前知识库没有检索到足够可靠的原典支持这一判断。”

==================================================
十三、Claim Evidence
==================================================

不能只验证引用。

最终答案拆成 claim。

例如：

claim:
“孔子并不主张无条件忍让。”

↓

evidence:
《论语》...

↓

verification:
supported

每个核心思想结论必须有 evidence。

==================================================
十四、数据质量等级
==================================================

定义：

A
权威文本 + 人工确认

B
权威来源 + 机器处理

C
来源可靠但尚未复核

D
AI解释

前端不得把 D 和 A 显示成同一等级。

==================================================
十五、Eval
==================================================

创建：

eval/

retrieval_gold.jsonl

quote_verification.jsonl

source_attribution.jsonl

modern_to_classic.jsonl

school_consistency.jsonl

adversarial_quotes.jsonl

unsupported_questions.jsonl

第一阶段如果无法人工生产1000条，
允许先创建：

>=200 条高质量 Gold Set

但必须设计扩展到 1000 条的脚本和 Schema。

==================================================
十六、必须包括这些对抗测试
==================================================

“己所不欲勿施于人是不是孟子说的？”

“上善若水是不是庄子？”

“孔子怎么看职场PUA？”

“韩非子会建议我辞职吗？”

“老子说努力就一定成功吗？”

“以德报怨出自孟子吗？”

输入假的古文。

输入真实古文 + 错误出处。

输入同一句不同标点。

输入繁体版本。

输入部分引用。

输入现代网络鸡汤冒充孔子。

系统必须能区分。

==================================================
十七、质量指标
==================================================

Gate Target：

Quote Exactness >= 99%

Source Attribution >= 98%

School Leakage < 1%

Retrieval Recall@5 >= 90%

Unsupported Correct Refusal >= 95%

Core Claim Evidence Coverage >= 95%

Fabricated Classical Quote ≈ 0

注意：

这些是项目 V1 的质量目标。

如果当前数据规模无法达到，
必须输出真实结果。

禁止修改数字假装 PASS。

==================================================
十八、性能要求
==================================================

RAG 本地测试：

P50 < 1s
P95 < 3s

不包含外部 LLM 延迟。

索引必须持久化。

启动不得每次全量重建。

==================================================
十九、兼容要求
==================================================

已有 API 尽量保持兼容。

已有 Debate：

问
证
辩
判

不能删除。

Evidence Pack 应当增强“证”。

Trust State 应增强“判”。

==================================================
二十、实施阶段
==================================================

PHASE 0
Repository Audit

输出：

docs/kb-v1/
00-current-state.md
01-gap-analysis.md
02-architecture.md

GATE-0：

必须列明：

当前数据
RAG
embedding
citation
tests

真实状态。

────────────────

PHASE 1
Data Architecture

Schema
source registry
verification level
ingestion pipeline

GATE-1：

fixture 数据可 ingest。

schema test 全 PASS。

────────────────

PHASE 2
Core Corpus

优先完整：

论语
道德经
孟子
庄子
墨子
韩非子

再扩展其他。

GATE-2：

所有 passage：

必须有 source。

原典不得来自 LLM 生成。

────────────────

PHASE 3
Modern Issue Ontology

建立：

现代情境
↓
核心冲突
↓
思想概念

GATE-3：

至少 50 个现代问题分类测试。

────────────────

PHASE 4
RAG V2

Hybrid Retrieval
Dense
BM25
Rerank
Metadata
Diversity

GATE-4：

运行 retrieval_gold。

输出：

Recall@1
Recall@3
Recall@5
MRR

────────────────

PHASE 5
Trust Layer

QuoteVerifier
CitationWhitelist
SourceVerifier
ClaimEvidence
TrustState

GATE-5：

运行 adversarial quote suite。

任何明显伪造名言通过验证：

FAIL。

────────────────

PHASE 6
Debate Integration

孔子
老子
墨子
韩非

必须从各自 Evidence Pack 发言。

GATE-6：

跨派引用泄露率 <1%。

────────────────

PHASE 7
Frontend

Evidence Drawer

显示：

原文
出处
注疏
来源
验证
TrustState

GATE-7：

Desktop + Mobile。

────────────────

PHASE 8
Full Eval

至少：

200 gold questions。

输出：

eval-report.json
eval-report.md

────────────────

PHASE 9
Regression

执行：

backend tests
frontend tests
build
lint
typecheck

禁止破坏旧功能。

────────────────

PHASE 10
Independent Acceptance

QA Reviewer：

必须读取：

git diff
tests
eval report
coverage
failure logs

然后输出：

docs/kb-v1/FINAL-ACCEPTANCE.md

结论只能：

PASS

CONDITIONAL PASS

FAIL

==================================================
二十一、每个任务的工作协议
==================================================

每一个 Task 必须：

PLAN
↓
IMPLEMENT
↓
TEST
↓
SELF REVIEW
↓
INDEPENDENT REVIEW
↓
FIX
↓
GATE

任何阶段失败：

不得进入下一阶段。

==================================================
二十二、Git 规则
==================================================

每个 Phase 独立 commit。

推荐：

feat(kb): add canonical knowledge schema

feat(kb): add ingestion pipeline

feat(rag): add hybrid retrieval

feat(trust): add quote verifier

feat(eval): add retrieval gold set

feat(ui): add evidence drawer

不得：

一个 commit 修改几百个无关文件。

==================================================
二十三、完成定义
==================================================

以下情况不得宣称项目完成：

“代码已经写好。”

“API 可以启动。”

“测试大部分通过。”

“模型回答看起来不错。”

真正 DONE 要满足：

数据链路 PASS
+
RAG Eval PASS
+
Quote Verification PASS
+
Citation Attribution PASS
+
Debate Integration PASS
+
Frontend Evidence PASS
+
Regression PASS
+
Independent QA PASS

==================================================
二十四、第一步
==================================================

现在不要立即写代码。

先：

1. 读取完整仓库。
2. 审计当前知识库/RAG。
3. 创建 gap analysis。
4. 列出需要修改/新增文件。
5. 给出 Task dependency graph。
6. 给出每个 Gate。
7. 由独立 Reviewer 审核计划。

计划通过后才能实施。

从 PHASE 0 开始。
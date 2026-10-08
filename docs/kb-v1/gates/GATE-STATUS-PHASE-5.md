# GATE 状态实测记录（PHASE 1 / 3 / 5 + Eval 基线落地后）

本文件记录**实现落地之后**各 Gate 的真实可测量状态。

与 PHASE 0 文档的区别
--------------------
`00-current-state.md` / `01-gap-analysis.md` / `04-gate-0-review.md` 中的 Gate 表
写的是 **PHASE 0 当时**的状态，那里的「不可达」理由是「无 QuoteVerifier」
「无 Trust State」「无 Claim-Evidence」。这些组件在 PHASE 5 已经落地，
因此那些理由**已经过期**——Gate 从「无法测量」变成「可以测量，但未达标」。

本文件是把过期结论更新为**实测值**的记录。目标数字全部来自
`eval/scripts/metrics.py` 的 `TARGETS`，与 `PROJECT-BRIEF.md` 第十七章一致，
**未做任何修改**（这一点本身可被独立复核）。

复现方式
--------
```powershell
cd backend
.venv\Scripts\python.exe ..\eval\scripts\run_eval.py --out ..\eval\eval-run.json
```
结果同时写入 `eval/eval-run.json`（含每条指标的 numerator / denominator /
failures 明细）。本文件表格即由该输出誊写。

实测结果（口径 = `eval/scripts/metrics.py` 冻结定义）
--------------------------------------------------

| 指标 | 实测值 | 目标 | 判定 | 覆盖 |
|---|---|---|---|---|
| Source Attribution | **1.000** | ≥ 0.98 | ✅ **PASS** | 18/18 |
| School Leakage | **0.000** | < 0.01 | ✅ **PASS** | 19 条候选，0 越派 |
| Quote Exactness | **0.333** | ≥ 0.99 | ❌ FAIL | 6/18 |
| Fabricated Classical Quote | **2** | ≈ 0 | ❌ FAIL | 20 条对抗样本 |
| Unsupported Correct Refusal | **0.000** | ≥ 0.95 | ❌ FAIL | 0/12 |
| Retrieval Recall@5 | **0.325** | ≥ 0.90 | ❌ FAIL | R@1=0.100, R@3=0.275, MRR=0.179 |
| Core Claim Evidence Coverage | **0.750** | ≥ 0.95 | ❌ FAIL | 30/40 |

**7 项中 2 项达标、5 项未达标。未达标项不调整目标、不宣称完成。**

### 重要更正：Quote Exactness 曾被报为 1.000

早期版本的 `run_eval.py` 自行把 Quote Exactness 实现成
「`quote_exists` 预测准确率」，这与 `metrics.py` 的冻结定义**不是同一个指标**：
冻结定义的分母是「系统判为存在的引文数」，分子要求
`exact_match=True`（`eval/scripts/metrics.py:81-106`）。前者得到 1.000，
后者才是真实的 **0.333**。已改为直接调用冻结实现，并在提交信息中记录。

这条更正的教训：**"指标名相同"不等于"口径相同"**。自实现指标必须在提交前
与冻结定义逐行比对。

未达标的根因（逐项）
------------------

### Quote Exactness 0.333 —— 语料粒度问题，不是匹配算法问题

实测：21 条数据集中，引文与语料条目**逐字完全相等**的只有 6 条。

根因：语料按**整章**存储（`lunyu:15.24` 的 `original` 是
`子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」`），
而数据集里的引文是**单句**（`己所不欲，勿施于人。`）。
`exact_match` 要求引文等于**整个 passage**，因此单句引用永远不可能 exact。

两种解决方向（**都需要另行评审，本文件不擅自改动任何一方**）：
1. 语料细化为句级 passage（PHASE 2 工作，**阻塞于 Q3 底本授权**）；
2. 重新定义 `exact_match` 为「逐字子串命中」而非「等于整条 passage」。

本文件**不**为了把该指标做绿而重定义它——那属于「为通过而放宽判据」。

### Unsupported Correct Refusal 0.000 —— 检索无法拒绝

12 条超范围问题**全部**检索到了结果（如「量子计算机如何改变儒家伦理？」
在四派共命中 7 条；「如何用《论语》指导短视频运营？」命中 2 条）。
系统因此永远走不到 `insufficient_evidence`。

根因是 hash embedding 无语义能力：非语义查询与古文的相似度分布与真实
现代问题**重叠**，任何阈值都无法分开两者。这与 C3 的残留在本质上是同一个问题。
真正的解法是 PHASE 4 语义 embedding + reranker。

### Fabricated Classical Quote 2 —— 摘句展示策略过宽

2 条失败均为 `partial_quote`：
- `勿施于人`（match_type=`partial`）
- `士不可以不弘毅`（match_type=`normalized`，7 字 ≥ 阈值 6）

两者的 `quote_exists` 判定**正确**（确实存在），`trust_state` 也**正确**
（`quote_relaxed`）。问题在于 `is_displayable_as_classic`
（`backend/app/services/trust_state.py:110-119`）把 `quote_relaxed` 一律视为
「可作经典原文展示」，而数据集要求**摘句不得作为完整经典原文展示**。

注意这与既有测试 `backend/tests/test_quote_verifier.py:421`
（断言 `is_displayable_as_classic("quote_relaxed") is True`）存在**真实冲突**：
解决它需要引入「是否覆盖整条 passage」这一维度，属于契约层面的改动，
**不应在不评审的情况下单方面改动**。两项独立指标本身工作正常。

### Core Claim Evidence Coverage 0.750

10 条失败的 reason 全部是 `no corpus entry for expected ids` ——
`retrieval_gold` 中 `expected_passage_ids` 使用了 `debate:` / `commentary:`
前缀的 id（13 + 1 条），与 `quote_verifier.load_corpus()` 的 passage_id
命名（`lunyu-taibo-01` 等）**对不上**。这属于数据集与语料之间的 id 口径问题，
不是 Claim-Evidence 逻辑本身的问题。

### Retrieval Recall@5 0.325

与 PHASE 0 审计一致。两个叠加原因：
1. embedding 非语义（hash），语义相似问题无法真正匹配；
2. 12 部目标书目中 **8 部零语料**，`expected_passage_ids` 指向的条目可能根本不在索引里。

**阻塞标注（不得伪造完成）**
--------------------------
- **Q3 底本授权** → PHASE 2 全量语料无法进行（书目、版本、授权均未定）。
  Quote Exactness 的语料粒度问题与 8 部零语料问题都卡在这里。
- **Q5 LLM 凭证** → PHASE 6 / PHASE 8 端到端无法验证（无可用 LLM key）。
  本文件的所有指标均**不依赖** LLM，因此仍可测；但端到端链路不可验证。

这两项在 PHASE 0 文档中即已标注为阻塞，本文件**维持**该标注，不因其他指标
变得可测而淡化。

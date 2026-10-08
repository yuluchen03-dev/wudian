# GATE 状态实测记录（PHASE 1 / 3 / 5 + Eval 基线落地后）

本文件记录**实现落地之后**各 Gate 的真实可测量状态。

与 PHASE 0 文档的区别
--------------------
`00-current-state.md` / `01-gap-analysis.md` / `04-gate-0-review.md` 中的 Gate 表
写的是 **PHASE 0 当时**的状态，那里的「不可达」理由是「无 QuoteVerifier」
「无 Trust State」「无 Claim-Evidence」。这些组件在 PHASE 5 已经落地，
因此那些理由**已经过期**——Gate 从「无法测量」变成「可以测量，但未达标」。

本文件是把过期结论更新为**实测值**的记录。

复现方式
--------
```powershell
cd backend
.venv\Scripts\python.exe ..\eval\scripts\run_eval.py --out ..\eval\eval-run.json
```
结果同时写入 `eval/eval-run.json`（含每条指标的 numerator / denominator /
failures 明细）。本文件表格即由该输出誊写。

口径说明（经独立复核 D1 修正后）
------------------------------
**7 项指标全部调用 `eval/scripts/metrics.py` 的冻结实现**，`run_eval.py`
不再自行定义任何指标口径。

> 修正记录：早期版本只有 2 项（quote_exactness / source_attribution）走冻结实现，
> 其余 5 项自实现，导致同名指标出现两个不同数值。独立复核指出后已全部改为委派；
> 同时修正了冻结实现自身的两个缺陷（见文末「冻结实现的缺陷修复」）。

目标数字全部来自 `metrics.TARGETS`，与 `PROJECT-BRIEF.md` 第十七章一致，
**未做任何修改**。

实测结果
--------

| 指标 | 实测值 | 目标 | 判定 | 覆盖 |
|---|---|---|---|---|
| Source Attribution | **1.000** | ≥ 0.98 | ✅ **PASS** | 18/18 |
| Fabricated Classical Quote | **0** | ≈ 0 | ✅ **PASS** | 20 条对抗样本 |
| School Leakage | **0.000** | < 0.01 | ✅ **PASS** | 19 条候选，0 越派 |
| Quote Exactness | **0.333** | ≥ 0.99 | ❌ FAIL | 6/18 |
| Unsupported Correct Refusal | **0.000** | ≥ 0.95 | ❌ FAIL | 0/12 |
| Retrieval Recall@5 | **0.325** | ≥ 0.90 | ❌ FAIL | R@1=0.100, R@3=0.275, MRR=0.179 |
| Core Claim Evidence Coverage | **0.750** | ≥ 0.95 | ❌ FAIL | 30/40 |

**7 项中 3 项达标、4 项未达标。未达标项不调整目标、不宣称完成。**

### 非冻结指标的补充诊断（不得当作冻结指标）

| 诊断项 | 值 | 含义 |
|---|---|---|
| `diagnostic_fragment_displayed_as_classic` | **2** | 语料中**确实存在**、但仅为**摘句**的引文被视为可作为完整经典原文展示的条数 |

冻结的 `Fabricated Classical Quote` 只统计「语料中**不存在**却被判 verifiable」的
**伪造**引文（`metrics.py:147-164`）。摘句在语料中确实存在，**不属于**该定义，
故必须单独计。早期版本把两者混在一个数字里（报 2），使该指标的数值与名称不符；
现已拆开：伪造 = 0（PASS），摘句诊断 = 2。

未达标的根因（逐项）
------------------

### Quote Exactness 0.333 —— 语料粒度问题，不是匹配算法问题

实测：21 条数据集引文中，与语料条目**逐字完全相等**的只有 6 条。

根因：语料按**整章**存储（`lunyu:15.24` 的 `original` 是
`子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」`），
而数据集引文是**单句**（`己所不欲，勿施于人。`）。`exact_match` 要求引文等于
**整个 passage**，因此单句引用永远不可能 exact。

两种解决方向（**都需要另行评审**，本文件不擅自改动任何一方）：
1. 语料细化为句级 passage（PHASE 2 工作，**阻塞于 Q3 底本授权**）；
2. 重新定义 `exact_match` 为「逐字子串命中」而非「等于整条 passage」。

本文件**不**为了把该指标做绿而重定义它——那属于「为通过而放宽判据」。

### Unsupported Correct Refusal 0.000 —— 检索无法拒绝

12 条超范围问题**全部**检索到了结果（如「量子计算机如何改变儒家伦理？」
四派共命中 7 条）。系统因此永远走不到 `insufficient_evidence`。

根因是 hash embedding 无语义能力：非语义查询与古文的相似度分布与真实现代问题
**重叠**，任何阈值都无法分开两者。这与 C3 残留本质相同；解法是 PHASE 4
语义 embedding + reranker。

### Core Claim Evidence Coverage 0.750

10 条失败的 `expected_passage_ids` 使用了 `debate:` / `commentary:` 前缀
（13 + 1 条），与 `quote_verifier.load_corpus()` 的 passage_id 命名
（`lunyu-taibo-01` 等）对不上，证据条目取不到。属数据集与语料的 id 口径问题，
不是 Claim-Evidence 逻辑本身的问题。

### Retrieval Recall@5 0.325

与 PHASE 0 审计一致。两个叠加原因：embedding 非语义；12 部目标书目中
**8 部零语料**，期望条目可能根本不在索引里。

### 摘句展示（诊断 = 2）

`backend/app/services/trust_state.py:110-119` 的 `is_displayable_as_classic`
把 `quote_relaxed` **一律**视为可作经典原文展示，而
`eval/adversarial_quotes.jsonl` aq-0010/aq-0011 要求**摘句不得作为完整经典原文展示**。

**冲突**：既有测试 `backend/tests/test_quote_verifier.py:421` 断言
`is_displayable_as_classic("quote_relaxed") is True`。要同时满足数据集期望，
须引入「引文是否覆盖整条 passage」这一新维度，属**契约层面改动**，
因此**不在未评审的情况下改动**。

> 相关但**已修复**的一处：`citation_guard.guard_citations` 原先无条件把
> `match_type` 写成 `"exact"`，导致「勿施于人」这类 4 字片段被判
> `verifiable=True` / `verified`（独立复核 D3）。现已按
> `MIN_FULL_QUOTE_CHARS` 判定片段并置 `partial`，与 `quote_verifier` 判定一致，
> 并有回归测试 `TestFragmentNeverVerified` 覆盖。

冻结实现的缺陷修复（独立复核 D4/D5）
-----------------------------------
`metrics.py` 的两个冻结函数在**随仓库发布的数据集上无法工作**，已修：

- **D5 `recall_at_k` / `reciprocal_rank`**：数据集用 `lunyu:12.2`，
  检索返回 `12.2`，集合交集恒为空 → Recall/MRR **恒为 0.0**。
  现统一经 `normalize_passage_id` 归一后再比较。
- **D4 `compute_school_leakage`**：数据集对非先秦诸子用**聚合标签**
  （`sage li_bai` 的 `allowed_books=["李白诗文"]`），而被检对象是具体篇目
  （《将进酒》），字符串永不相等 → 把 5 条**正确**引用误判为泄露
  （泄漏率虚高至 0.2632）。现优先采用数据集里语义明确的 `forbidden_books`。

**阻塞标注（不得伪造完成）**
--------------------------
- **Q3 底本授权** → PHASE 2 全量语料无法进行（书目、版本、授权均未定）。
  Quote Exactness 的语料粒度问题与 8 部零语料问题都卡在这里。
- **Q5 LLM 凭证** → PHASE 6 / PHASE 8 端到端无法验证（无可用 LLM key）。
  本文件全部指标**不依赖** LLM 生成文本，故仍可测；但
  `unsupported_correct_refusal` 度量的是**信任层判定**而非 LLM 端到端回答，
  该限制已在 `eval/eval-run.json` 的 `basis` 字段中显式声明。

两项均**未伪造完成**。

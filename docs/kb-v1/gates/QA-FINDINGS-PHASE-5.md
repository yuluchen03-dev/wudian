# 自查与独立复核记录（PHASE 1 / 3 / 5 + Eval）

本文件记录在 PHASE 1 / 3 / 5 与 Eval 基线落地后，**队长自查**发现的偏差与缺口。
所有条目都给出可复现命令或 `文件:行号`。凡未复现的推测一律标注为「未核验」。

目录
----
- §1 指标口径错误（已修正）——Quote Exactness 曾被报为 1.000
- §2 集成缺陷（已修正）——`metrics.py` 与数据集字段口径不一致
- §3 未修正的缺口（如实记录，不擅自改动契约）——PHASE 3 泛化能力
- §4 未修正的缺口——摘句展示策略与既有测试冲突
- §5 阻塞项（维持 PHASE 0 标注）

---

## §1 指标口径错误：Quote Exactness 曾报 1.000（已修正）

**性质**：自实现指标与冻结定义**同名不同口径**。

早期 `run_eval.py` 把 Quote Exactness 实现为「`quote_exists` 预测准确率」，
得到 1.000。但 `eval/scripts/metrics.py:81-106` 的冻结定义是：
分母 =「系统判为 `quote_exists=True` 的条数」，分子 =「其中 `exact_match=True`
且期望确实存在的条数」。按冻结口径实测为 **0.333**（6/18）。

**处置**：`run_eval.py` 已改为直接调用 `compute_quote_exactness` /
`compute_source_attribution`，不再自行定义口径。见提交
`fix(eval): use frozen metric definitions; correct the reported Quote Exactness`。

**教训**：同名指标必须逐行比对冻结实现后再报告，不能凭名称假定口径一致。

---

## §2 集成缺陷：`metrics.py` 读不到数据集字段（已修正）

**性质**：Eval 的两半从未真正连通。

`compute_source_attribution` 读 `rec["expected"]["source_correct"]`，
而 `source_attribution` 数据集（见 `eval/scripts/schema.py` 的规格与磁盘数据）
用的是**扁平**字段 `expected_source` / `expected_source_correct`。
调用即抛 `KeyError: 'expected'` —— 说明该「冻结指标」此前**从未对真实数据运行过**，
PHASE 0 报告中的 `not_computable` 掩盖了这个缺陷。

**处置**：`compute_source_attribution` 改为优先读扁平字段，保留嵌套兼容。
修正后 source_attribution 实测 **1.000（18/18）PASS**。

---

## §3 未修正缺口：PHASE 3 结构化器泛化能力弱

**性质**：单元测试通过 ≠ 可用。**这是本次自查最重要的发现。**

### 实测

| 数据集 | 结果 |
|---|---|
| `backend/tests/test_issue_ontology.py`（t19 自带用例） | 52 用例 / 226 subtests **全通过** |
| `eval/modern_to_classic.jsonl`（独立 Eval 数据） | **9/20 命中，11 条不匹配** |

复现：
```powershell
cd backend
@'
import sys, json, logging
sys.path.insert(0, '.')
logging.disable(logging.CRITICAL)
from app.services.issue_structurer import structure
mtc = [json.loads(l) for l in open('../eval/modern_to_classic.jsonl', encoding='utf-8') if l.strip()]
ok = sum(structure(r['modern_query']).scene == r['expected']['scene'] for r in mtc)
print(f"{ok}/{len(mtc)}")
'@ | .venv\Scripts\python.exe -
```
输出：`9/20`（11 条不匹配中，**7 条** `scene=None`，**4 条**错配到
`choice`/`achievement` —— 见下表 `None` 与非 `None` 的分布）。

### 11 条不匹配明细

| id | 期望 | 实际 | 查询 |
|---|---|---|---|
| mc-0002 | workplace_conflict | choice | 被领导误解了，我要不要解释？ |
| mc-0003 | career | None | 我很想快速成功 |
| mc-0006 | parent_child | None | 什么是真正的孝顺？ |
| mc-0009 | meaning | None | 无为而治是什么意思？ |
| mc-0010 | leadership | None | 奖惩制度该怎么设计？ |
| mc-0012 | choice | None | 总是后悔过去的选择 |
| mc-0013 | meaning | None | 怎么看待命运？ |
| mc-0016 | workplace_conflict | choice | 遇到流言蜚语怎么办？ |
| mc-0018 | meaning | choice | 该不该相信鬼神？ |
| mc-0019 | meaning | None | 如何自我修养？ |
| mc-0020 | workplace_conflict | achievement | 为什么事情没成就到处说？ |

### 根因（已核验）

本体关键词表**过窄，且与单测用例共同调优**。实测关键词表：

- `parent_child`（11 个）缺 **孝顺**、父母、养育、赡养
- `career`（11 个）缺 **成功**、快速成功
- `meaning`（8 个）缺 **修养**、命运、鬼神、无为
- `leadership`（16 个）缺 **奖惩**、制度、激励

单测用例恰好都含关键词（如 `parent_child` 用例用「孩子叛逆不听话…」含
孩子/叛逆），而 Eval 数据用同义但未收录的说法（「孝顺」），因此漏判。

### 为什么**不**在这里直接修

扩充关键词本身是正当的 PHASE 3 工作，但若照着这 11 条 Eval 查询逐条补词，
就是**对评测集过拟合**，属于「为通过而改数据」。正确做法是依据一份
可追溯的现代汉语近义/上位词来源系统扩充，并在**单测与 Eval 上同时复测**。
该工作需要有来源依据，故此处只如实记录缺口，不擅自补词。

### 对 Gate 判定的影响

`03-task-dag.md` 的 GATE-3 若只写「≥50 分类测试通过」，则该 Gate **确已满足**
（52 用例通过）。但本记录表明该判据**不足以说明可用性**——45% 的独立样本准确率
才是真实水平。建议后续把 Eval 命中率纳入 GATE-3 判据（需评审后修改 Gate 定义）。

---

## §4 未修正缺口：摘句展示策略与既有测试冲突

`fabricated_classical_quote` 实测 **2**（目标 0），两条均为 `partial_quote`：
`勿施于人`（match_type=`partial`）与 `士不可以不弘毅`（match_type=`normalized`，7 字）。

- 两条的 `quote_exists` 判定**正确**（文本确实存在）
- 两条的 `trust_state` 判定**正确**（`quote_relaxed`）
- 问题在 `backend/app/services/trust_state.py:110-119`：`is_displayable_as_classic`
  把 `quote_relaxed` **一律**视为可作为经典原文展示，而数据集要求
  **摘句不得作为完整经典原文展示**。

**冲突**：既有测试 `backend/tests/test_quote_verifier.py:421` 断言
`is_displayable_as_classic("quote_relaxed") is True`。要同时满足数据集期望，
必须引入「引文是否覆盖整条 passage」这一新维度，属**契约层面改动**。
单方面改动会使该既有断言失效，因此**不在未评审的情况下改动**。

---

## §5 阻塞项（维持 PHASE 0 标注，不因其他指标可测而淡化）

- **Q3 底本授权** → PHASE 2 全量语料无法进行。
  连带影响：`quote_exactness` 的语料粒度问题（整章存储 vs 单句引用）、
  12 部书目中 8 部零语料导致的 `recall@5` 偏低。
- **Q5 LLM 凭证** → PHASE 6 / PHASE 8 端到端无法验证。
  本文件全部指标**不依赖 LLM**，故仍可测；但端到端链路不可验证。

两项均**未伪造完成**。

---

## §6 独立复核（fresh-context 审计代理）结论与处置

由于团队成员受上游速率限制（`workbuddy upstream soft_rate`，配额于
2026-10-09 16:39:48 UTC+8 重置），本次独立复核改由**全新上下文、互不共享本
会话记忆**的审计代理执行：只读仓库、自行复现命令、自行编写探针。

它逐条核验了 7 项声明，结果与处置如下。

### 已核验为真（未修改）

| 声明 | 结论 |
|---|---|
| GATE-1：147 用例通过，fixture 真实可 ingest（5 条正文均能在 `lunyu.json` 定位、全部 C 级） | **VERIFIED** |
| PHASE 3：21 情景、结构化器确定性、≥50 分类用例（实测 52 用例） | **VERIFIED** |
| PHASE 5：「文本存在」与「出处正确」独立判定；brief 第一例返回 `citation_corrected`；旧的双向子串缺陷**已不存在** | **VERIFIED** |
| Claim-Evidence：Pack 外 `evidence_id` → `unsupported`；无核心 claim 时 `coverage()==0.0` | **VERIFIED** |
| Eval 数值可复现、`TARGETS` 与 brief 第十七章一致且未被修改 | **VERIFIED** |
| 无虚假 PASS；Q3/Q5 诚实标注为阻塞 | **VERIFIED** |

### 它发现的问题及处置

| 编号 | 问题 | 处置 |
|---|---|---|
| **D1** | `run_eval.py` 仅 2/7 指标走冻结实现，其余自实现，导致同名指标两个数值（e.g. fabricated 冻结 0 vs 自实现 2；recall 冻结 0.0 vs 自实现 0.325；school_leakage 冻结 0.2632 vs 自实现 0.0） | **已修**：7 项全部委派冻结实现；摘句检查拆为单独命名的**诊断项**，不再混入 fabricated |
| **D2** | 本文档早前称口径为「冻结定义」，但当时仅 2/7 成立 | **已修**：`GATE-STATUS-PHASE-5.md` 已改写并记录该更正 |
| **D3** | `citation_guard.guard_citations` 无条件把 `match_type` 写成 `"exact"`，使「勿施于人」4 字片段被判 `verifiable=True`/`verified`，与 `quote_verifier` 及 aq-0010 期望矛盾 | **已修**：按 `MIN_FULL_QUOTE_CHARS` 判定片段并置 `partial`；新增回归测试 `TestFragmentNeverVerified`（5 例）；完整句判定保持不变 |
| **D4** | 冻结 `compute_school_leakage` 在随仓库数据集上不可用（聚合标签 `李白诗文` vs 具体篇目《将进酒》→ 5 条**正确**引用被误判泄露，虚高至 0.2632） | **已修**：优先采用语义明确的 `forbidden_books` |
| **D5** | 冻结 `recall_at_k`/`reciprocal_rank` 恒为 0.0（数据集 `lunyu:12.2` vs 检索 `12.2`，集合交集恒空） | **已修**：统一经 `normalize_passage_id` 归一 |
| **D6** | 本文档早前把 11 条不匹配写成「9 条 None + 2 条错配」 | **已修**：实为 **7 条 None + 4 条错配** |
| **D7** | `.gitignore` 忽略 `data/processed/` 与 `scripts/`，但其中已有文件被强制跟踪 → 新文件会被静默漏掉（此陷阱已实际导致 7cf14c3 的问题） | **已知，未修**（属仓库约定层面，需评审统一策略） |
| Claim 7 | 「12 个提交」实为「领先 origin/main 12 个」，分支本身有 60+ 提交；且历史中仍存 5 个 `__pycache__/*.pyc` blob（已从工作树移除，未推送） | **如实记录**，措辞已在后续汇报中更正 |

### 审计代理的安全声明（记录备查）

- 生产索引 HNSW 段从未被重建（mtime 与大小不变，`count()==143`）。
- 但 `chroma.sqlite3` 在其会话中被重写两次：chromadb 的 catalog 元数据在
  **打开时即写入**，其两个 PHASE 3 探针未设 `CHROMA_PERSIST_DIR`，因而打开了
  真实目录。内容完整性事后经功能比对确认（143 条，检索指标与隔离副本一致）。
  这是 chromadb 的固有行为，对「索引即生产数据」的纪律有参考价值。
- 全部临时产物已清理，`git status --porcelain` 为空，未修改任何产品文件。


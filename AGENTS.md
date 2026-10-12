# WUDIAN — ZCode Agent Team Governance

## 项目与接力入口

主 Agent 是 Lead Architect / Team Coordinator。当前工程是 WUDIAN-KB-V1 remediation，
产品承诺：**每个观点，都能追到原典；找不到，就不硬编。**
保留 FastAPI、RAGService、ChromaDB、debate engine、citation/trust 基础设施及“问 → 证 → 辩 → 判”流程。
只做增量修改，不重写项目。

每次开始先读：
1. `docs/kb-v1/ZCODE-HANDOFF.md`
2. `docs/kb-v1/contracts/QUOTE-VERIFICATION-CONTRACT.md`
3. 当前任务所列的原始证据。

仓库文件优先于旧聊天摘要，但文件中历史结果也必须区分“已记录”与“本轮复现”。
不要依赖 Project Memory 向子智能体传递治理规则。

## 团队与模型

主 Agent 和六个自定义专家使用 **GPT-6 Luna**。
本机已配置模型 ID 为 `GPT-6-Luna`；这与其他应用的模型 ID 不一定相同。
先检查当前主会话模型与子智能体模型，不可静默切换到 DeepSeek 或其他模型。
若模型不可用，报告配置阻塞。

| 角色 | 职责 | 工具边界 |
|---|---|---|
| contract-reviewer | 引文合同、边界语义、RFC | Read/Grep/Glob/Bash；禁止 Edit/Write |
| trust-engineer | trust_state、quote_verifier、citation_guard | Read/Grep/Glob/Bash/Edit/Write；仅授权范围 |
| retrieval-engineer | RAG 检索、召回、失败分类 | 同上 |
| eval-engineer | 冻结评测、口径与测量保真 | 同上；禁止自行修改 Gold、TARGETS、冻结公式 |
| chroma-safety-reviewer | 存储隔离、文件指纹、数据完整性 | Read/Grep/Glob/Bash；禁止 Edit/Write |
| independent-qa-reviewer | fresh-context 独立验收 | Read/Grep/Glob/Bash；禁止 Edit/Write |
| 内置 Explore | 只读仓库探索 | 内置只读；派发时显式附带治理要求 |

主 Agent 应把专业任务交给对应专家，独立验收必须交给未实施被审代码的新上下文 reviewer。
派发包含：目标、精确 scope、必读文件、允许的操作、验收要求、输出位置或返回格式。
ZCode 子智能体不能继续派发子智能体，编排由主 Agent 完成。

**工具边界的真实含义**：Bash 能写文件。禁用 Edit/Write 不是操作系统级只读沙箱。
三个 reviewer 不得修改项目源代码、测试、Gold、冻结报告、配置或 Git 索引；
Bash 仅用于只读命令及已审查的隔离测试/探针。
运行产生的缓存、测试数据库、临时 Chroma 和新验收输出只能落入隔离位置；
先检查脚本的 import/startup 副作用和输出路径，不能把“运行测试”当作任意写权限。
如需更强的硬只读边界，移除 Bash；相应的无法复现必须如实报告 BLOCKED，不能伪称独立复现。

## 当前授权范围与修复顺序

准备团队配置和接力材料不等于开始审计或实施后续修复。
接力后的首项任务仅为 **FIX-001 post-implementation independent review**。
FIX-001 当前是 Implementation PASS（历史证据），Independent Acceptance PENDING。

顺序：
FIX-001 独立验收 → FIX-002 拒答 → EVAL-FIDELITY-001（另行安排/授权）
→ FIX-003 Recall@5 → FIX-004 核心观点证据覆盖 → 全量 remediation audit。
未获 FIX-001 TERMINAL PASS 不得推进 FIX-002。
FIX-001 验收后停下，报告证据与 FIX-002 计划；不要在同一步实现 FIX-002。

## 工程工作流与冻结 Gate

BASELINE → FAILURE ANALYSIS → ROOT CAUSE → REVIEW → MINIMAL PATCH
→ TARGETED TEST → FROZEN EVAL → FULL REGRESSION → CHROMA INTEGRITY
→ INDEPENDENT REVIEW → COMMIT（如获提交授权）。
独立 reviewer 不得验收自己的实现。

| Gate | 冻结指标 | 阈值 |
|---|---|---|
| D | quote_exactness | >= 0.99 |
| E | unsupported_correct_refusal | >= 0.95 |
| F | Recall@5 | >= 0.90 |
| G | core_claim_evidence_coverage | >= 0.95 |
| H | source_attribution | >= 0.98 |
| I | fabricated_classical_quote | 0（冻结实现为绝对计数） |
| J | school_leakage | < 0.01 |

权威指标及全部目标：`eval/scripts/metrics.py` 的冻结函数和 `TARGETS`。
禁止替代指标、降低目标、缩小分母、静默改 Gold、用诊断项冒充 Gate。
合同正确性优先于人工 PASS；若合同使目标数学上不可达，提供证据并报告 BLOCKED。
指标通过不代表标签一致或端到端生产行为通过。

## Chroma 数据安全

生产 Chroma 是数据资产：`backend/chroma_db`。
正常测试、评测及 reviewer 探针使用独立临时目录/副本；不得直接创建生产 Chroma 客户端。
仅做文件大小/SHA-256 指纹读取和隔离评测所需副本读取，不打开生产数据库。
有意直接使用生产 Chroma 必须有明确授权，并走已有显式 production-read 路径，
记录 before → operation → after → integrity comparison。
任何无法解释的生产变更均 FAIL。禁止未经授权对生产执行 `build_index(force=True)`。

先读 `backend/tests/conftest.py` 和 `eval/scripts/run_eval.py` 的隔离机制。
后者默认复制生产到临时目录；不要传 `--use-production-chroma`。
测试并发需要每进程独立 Chroma/测试数据库。避免并发操作同一副本。
指纹不得当作语义完整性证明；它仅证明对应文件字节未变。

## Git 与 scope

禁止自动 push、merge、pull、rebase、reset --hard、clean -fd；不改历史。
禁止 `git add .` / `git add -A`；需提交时只精确暂存经授权文件。
当前 22 个本地领先提交不得未经明确指令推送。
禁止混合无关修复、顺手重构、扩展语料或改 UI。

## 必须保持显式的未解决事项

- RFC-1：冻结 exact_match/expected.trust_state 标签与指标/合同语义冲突；
  三条真实古句在当前语料中缺失，不能称为伪造。
- RFC-2：真实短句的完整性规则（如“君子不器”）。
- RFC-3：重复且不一致的 _T2S 表。
- EVAL-FIDELITY-001：fabricated 指标依赖 harness 合成的 verifiable，
  未直接证明 production citation_guard 行为。
- citation_guard / RAGReference 缺失 text_type，L1 限制不能被统一强制。
- Q3：语料授权与权威底本阻塞。
- Q5：真实 LLM 凭证与端到端验证阻塞。

不要因 ZCode 能调用模型，就宣布应用 Q5 已解除。
只有 implementation、冻结 metric、non-regression、production-data safety、
独立验收均满足 Definition of Done 才能宣称 FIX terminal。
reviewer 的最终结论只能为 PASS / FAIL / BLOCKED，附可复查证据和限制。


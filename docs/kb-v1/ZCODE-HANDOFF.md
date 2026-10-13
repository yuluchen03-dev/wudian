# WUDIAN-KB-V1 — ZCode 接力记录

准备日期：2026-10-09（Asia/Tokyo）。
范围：准备配置与接力材料；**本轮没有执行 FIX-001 独立验收**。
分享对话无法提取正文，聊天接力信息来自用户提供附件，已与下面仓库证据交叉核对。

## 接力时 Git 快照

准备开始时只读核验：
- workspace：`D:\systemDir\Desktop\悟典`
- branch：`codex/overall-optimization`
- HEAD：`899519b7735045c54d7a8fec44f87fef867cdc12`
- 本地 origin/main：`64c861828eb8f1ec8816eb8d95212f78cdc7faeb`
- `git rev-list --count origin/main..HEAD`：22；开始时 working tree clean。
- FIX-001 实现：`31afdc8ae4a7581c169c568dd76a0aef1458f254`
- reviewer-condition 分析工具修改：`899519b`（C1–C6）。
- 本轮未 pull/fetch/push/merge/rebase/commit；远端实时状态没有查询，
  “nothing pushed”为历史接力声明，不是本轮对服务器状态的认证。

**准备完成后 working tree 会出现本轮新配置/文档的 untracked 文件，这是预期状态。**
不要为恢复 clean tree 而删除或重置它们；先检查它们是否与此次准备的文件清单一致。
启动后必须重新核验 Git，不能把此快照当作当前状态。

## FIX 状态

FIX-001：**Implementation PASS（已记录）/ Independent Acceptance PENDING**。
FIX-002 / FIX-003 / FIX-004：接力记录为未开始；当前最新提交对应 FIX-001，
首次运行仍须检查历史与工作区是否有后续工作。
首项工作仅为 fresh-context independent-qa-reviewer 对 FIX-001 的实现后验收。
独立验收 PASS 后停下汇报，提出 FIX-002 计划；不得直接实施。

## 指标：已记录，未在本轮重新运行

以下值来自当前 `eval/eval-run.json`，D 同时可在
`deliverables/kb-v1/fix-001/current/baseline.md` 核对。

| Gate | 指标 | 已记录值 | 冻结阈值 | 记录结论 |
|---|---|---|---|---|
| D | quote_exactness | 18/18 = 1.000 | >= 0.99 | PASS |
| E | unsupported_correct_refusal | 0/12 = 0.000 | >= 0.95 | FAIL |
| F | Recall@5 | 0.325 | >= 0.90 | FAIL |
| G | core_claim_evidence_coverage | 30/40 = 0.750 | >= 0.95 | FAIL |
| H | source_attribution | 18/18 = 1.000 | >= 0.98 | PASS |
| I | fabricated_classical_quote | 0 | 0 | PASS，保真限制仍 open |
| J | school_leakage | 0/19 = 0.000 | < 0.01 | PASS |

`diagnostic_fragment_displayed_as_classic = 1` 是当前报告中的补充诊断，**不是冻结 I 指标**；
不能隐瞒，也不能擅自重新定义 I 来吸收它。
`eval/eval-run.json` 的 `integrity_checked=false`，它自身不提供生产指纹一致证明。

历史 PHASE-5 Gate 文档与冻结 pre-fix baseline 记录 D=6/18=0.333，
是修复前状态。不要覆写它们来消除历史差异。
`deliverables/kb-v1/fix-001/current/` 为修复后抓取；
`deliverables/kb-v1/fix-001/` 根目录的 baseline/failure-analysis 是冻结修复前证据。
`eval/scripts/fix001_analysis.py` 现在默认写 current，但它的顶部说明仍有旧路径，
运行前以代码实际输出路径为准。

## 回归：历史证据，待独立复现

`git show 31afdc8` 的提交说明记录：
- backend：470 tests pass（+43）；
- frontend：tsc exit 0，41 tests pass；
- 新增合同测试文件：`backend/tests/test_quote_contract.py`。

这些数值是提交说明里的实现者记录，不是本轮 fresh reviewer 的结论。
Agnes 环境失败的已记录根因见 `docs/kb-v1/gates/ENV-BOOTSTRAP.md`：
backend/.env 使 Settings() 的 LLM_PROVIDER 为 agnes，
与测试期望 openai 冲突。必须在基线和当前版本相同环境下独立确认；
不要未复现就声称“无关/已解决”。勿展示 .env 内容或凭证。

## 本轮指纹快照

完整清单（SHA-256、字节数、相对路径）：
`docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json`。

本轮仅使用普通文件读取，不打开 Chroma 客户端。
- chroma.sqlite3：4,120,576 bytes；
  SHA-256 `d5184ba4f9f77729d629c832278fb6ac43f628b3267799f3e474278459989bda`。
- data_level0.bin：167,600 bytes；
  SHA-256 `2a3617e926a15f4587921c9b8245d4838b0c3ea7b7474aed135629228ad657f0`。
- 共 6 个生产索引文件；另记录全部 7 个 eval JSONL 和 metrics.py 的指纹。
- 这只是接力准备时的文件快照，不是过往所有操作的数据完整性认证。
  下一轮需重取 before/after，与快照核对；新增/缺失文件也必须检查。

## 独立 reviewer 验收任务

从新隔离上下文开始，显式读 AGENTS.md、此文件和 CONTRACT-001 v2。
不得修改被审源代码、测试、Gold、冻结指标或已有报告；仅可执行已检查的隔离探针。
Bash 有写能力；“代码只读”依靠工具限制加行为规则，不能称为硬沙箱。

必须独立检查：
1. `31afdc8`、`899519b` 的实际 diff 和 C1–C6，区分工具修复与产品修复。
2. 冻结 JSONL / metrics.py / TARGETS 未被改动或筛选；D 分母仍为 18。
3. D/H/I/J 复现、E/F/G 不回退；不得省略失败 Gate。
4. 空白/标点、短片段、正确/错误来源、繁简、L1/L2、跨句拼接、
   prefix/middle/suffix、伪造后缀及保守默认参数等合同探针。
5. commentary 不能经 verify_quote 成为 verified classical original；
   citation_guard 的 text_type 缺口单独披露，不从 verify_quote 测试外推它已安全。
6. backend 与 frontend 回归；Agnes 失败是否基线已有且与改动无关。
7. 新的 before/after 生产文件清单/指纹；验证所有命令的 Chroma 隔离。
8. 下列 open 项目仍如实 open，尤其 frozen score 与 expected labels 的差异。

安全的执行入口（**只是待 reviewer 审查的入口，本轮未运行**）：
- backend 工作目录：`.venv/Scripts/python.exe -m pytest tests/test_quote_contract.py tests/test_quote_verifier.py`，
  随后按 review scope 跑完整 `tests`。先检查 conftest 的强制 per-process 隔离。
- repository 工作目录：`backend/.venv/Scripts/python.exe eval/scripts/run_eval.py --out <隔离临时目录>/eval-run.json`；
  默认使用副本，不传 production flag，不覆盖已跟踪 eval-run.json。
- fix001_analysis：先检查 main / 输出逻辑；默认会写 current，
  reviewer 不直接覆盖该目录。需要运行时在临时探针中先设置模块 `_OUT_DIR`
  为隔离临时路径再调用 main，或者直接调用冻结指标并打印结果。
- frontend 工作目录：先检查 package scripts，执行 TypeScript 检查与 `npm test`；
  若因环境/资源阻塞，明确报告实际命令和阻塞，不把历史 41 当成新结果。

最终 verdict 仅 PASS / FAIL / BLOCKED。
PASS 须说明 FIX-001 Definition of Done 如何满足，并明确它不等于整个 KB-V1 Gate 全绿。
BLOCKED 必须指出缺少的证据/约束；FAIL 必须指出可复现违反项。
若 reviewer 无法独立复现，不能以主 Agent/实现者自报替代 terminal 验收。

## Open / Blocked（不得静默关闭）

- RFC-1：expected.exact_match 和 expected.trust_state 与冻结指标/合同的语义冲突；
  qv-0016/0017/0018 标签差异；qv-0019/0020/0021 是真实古句但当前语料缺失。
- RFC-2：真实短经典句的完整性门槛。
- RFC-3：不同的 _T2S 表。
- EVAL-FIDELITY-001：harness-synthesized verifiable 与 production citation_guard 路径不等价。
- RAGReference 不带 text_type 导致 citation_guard 无法一致执行 L1。
- Q3：底本授权/权威版本阻塞。
- Q5：应用真实 LLM 凭证及端到端验证阻塞。

## ZCode 启动

配置说明：`.zcode/team/README.md`。
新会话第一条消息：`docs/kb-v1/ZCODE-START-PROMPT.md`。
主会话选择 GPT-6 Luna；先用需要确认变更的执行模式。
若 Plan mode 无法执行独立测试，使用 Ask before changes 并遵守隔离 scope。
确认六个角色可见和有效工具/模型后再开始验收，不以“文件已落盘”冒充已加载。


# ZCode 新会话启动消息

将下方内容整体发送到当前仓库的新 ZCode 会话：

---

继续当前 wudian / WUDIAN-KB-V1 remediation，不要重新开始项目。
你是 Lead Architect / Team Coordinator，主会话及六个专家全部使用 GPT-6 Luna。
先核对主会话模型及专家实际绑定的模型 ID GPT-6-Luna，不得静默回退其他模型。

先读 AGENTS.md、docs/kb-v1/ZCODE-HANDOFF.md、
docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json、
docs/kb-v1/contracts/QUOTE-VERIFICATION-CONTRACT.md。

先只读核验 Git：
git status --short --branch
git log --oneline -10
git rev-list --count origin/main..HEAD
git show --stat 31afdc8
git show --stat 899519b

准备时 HEAD=899519b，领先本地 origin/main 22 个提交。
准备配置后新增的未跟踪文件是预期状态；检查范围，不删除、不重置。
这些数字及报告只是接力快照，必须独立核实。
不 pull、不 push、不 merge、不 rebase、不 reset --hard、不 clean -fd。
不 git add . / git add -A。

核对可用角色：
contract-reviewer、trust-engineer、retrieval-engineer、eval-engineer、
chroma-safety-reviewer、independent-qa-reviewer，以及内置 Explore。
自定义定义已准备于 ~/.zcode/agents；仓库 .zcode/team/agents 是可移植副本，
不要误认为项目副本会自动被发现。
若角色缺失或实际模型/工具不符，报告配置阻塞，不用 general-purpose 冒充独立验收。

FIRST TASK ONLY：
派发 FIX-001 post-implementation audit 给 @independent-qa-reviewer。
必须使用新的隔离上下文；只传任务、治理规则和证据路径，不把实施者结论当事实。
该 reviewer 不得修改项目代码、测试、Gold、冻结指标、已有报告或 Git；
只可在隔离临时存储中运行已检查的探针和测试。
Bash 可写，禁用 Edit/Write 不代表硬只读；严格检查 import/startup 副作用。
不得直接打开生产 Chroma，不传 --use-production-chroma。

要求独立审查 31afdc8 / 899519b、合同及 C1–C6，
按 HANDOFF 验收清单复现 Gate D/H/I/J，记录 E/F/G，
保持 D 分母 18、Gold 和 TARGETS 不变，
检查 commentary/L1、片段、跨句拼接、繁简及错误来源，
复现 backend/frontend 回归，
独立判断 Agnes 环境失败是否 pre-existing and unrelated，
记录生产 Chroma 新的 before/after 文件清单和 SHA-256。
所有历史数值标为“已记录”，本轮实际结果才标为“独立复现”。
RFC-1/2/3、EVAL-FIDELITY-001、citation_guard text_type 缺口、Q3/Q5 保持诚实 open。

reviewer 仅返回 PASS / FAIL / BLOCKED，附证据、实际命令、
重现的 numerator/denominator、失败项、隔离路径、指纹及限制。
FIX-001 未获 TERMINAL PASS，不开始 FIX-002。
即便获 TERMINAL PASS，也停止并汇报 reviewer verdict、证据、
回归、Chroma integrity、剩余限制和 FIX-002 计划；
本步骤不实施 FIX-002、不提交、不推送。


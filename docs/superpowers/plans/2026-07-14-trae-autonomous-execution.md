# 悟典 TRAE 大赛全权执行计划

> **给 TRAE 的执行指令：** 你拥有本仓库内的完整实施权限。必须连续执行到全部本地交付完成，不要只给建议、方案或代码片段。按本文检查清单逐项推进并记录状态；实现细节以两份专项计划为准。遇到非阻断性选择时自行采用最稳妥、最符合现有代码风格的方案，不向用户反问。

**Goal:** 在不破坏现有功能和用户未提交改动的前提下，完成 `/demo` 的“思想审判场”四幕体验，校准可直接提交的 TRAE 大赛报名材料，并交付可复核的测试、视觉验收和 TRAE 创作证据。

**Architecture:** 以现有 Next.js 14 前端和 FastAPI 后端为基础，只新增隔离的 `thought-court` 前端功能并复用既有辩论 API、RAG、SSE 与视觉资产，不改后端接口契约。报名材料保持单文件、离线、自包含；在产品实现完成后再同步真实能力与截图，避免材料宣称超出实际实现。

**Tech Stack:** Next.js 14 App Router、React 18、TypeScript 5、Framer Motion 11、Lucide React、CSS Modules、FastAPI、pytest、Node.js 测试脚本、原生 HTML/CSS/Canvas/JavaScript、PowerShell

---

## 1. 权威输入与优先级

按以下优先级解决冲突，低优先级内容不得覆盖高优先级约束：

1. 当前仓库中能够运行的代码、真实 API 契约和现有测试。
2. `docs/superpowers/specs/2026-07-12-thought-court-hackathon-design.md`
3. `docs/superpowers/plans/2026-07-12-thought-court-hackathon.md`
4. `docs/superpowers/specs/2026-07-12-wudian-registration-materials-design.md`
5. `docs/superpowers/plans/2026-07-12-wudian-registration-materials.md`
6. 本文的执行顺序、质量门槛和交付要求。

专项计划包含精确类型、测试代码、组件职责和分步命令。执行某一任务前必须完整阅读对应任务，不得凭本文摘要自行删减功能。

## 2. 当前基线

开始执行时应按以下事实核对仓库，不得假设这是干净工作区：

- 工作区已有用户未提交改动，主要涉及全站 UI、阅读页、问道页、导航、测试和报名材料。
- `frontend/app/demo/page.tsx` 目前仍是“黑客松现场指挥台”，尚未替换为思想审判场。
- `frontend/components/thought-court/` 当前不存在，思想审判场专项计划尚未落地。
- `报名材料/一问见古今-TRAE大赛创意提案.html`、`报名材料/悟典-TRAE大赛报名帖文案.txt`、校验脚本和图片嵌入脚本已经存在。
- 当前报名材料校验命令 `node 报名材料/validate-registration-materials.cjs` 已通过，但仍需在思想审判场完成后做内容真实性与视觉复核。
- 思想审判场设计和计划已提交；报名材料设计、计划和产物可能仍未提交。

上述基线仅用于定位起点。若执行时仓库已变化，以实际审计结果为准，但必须保留所有无法确认归属的现有改动。

## 3. 不可违反的执行规则

- 禁止使用 `git reset --hard`、`git checkout -- .`、批量覆盖或删除现有改动。
- 禁止为让测试通过而删除、跳过、弱化测试或把真实失败改成恒真断言。
- 禁止伪造引用、出处、模型输出、在线状态、TRAE Session ID、截图或测试结果。
- 禁止把稳定演示数据伪装成实时 AI；界面必须明确显示 `curated`、`live` 或 `stable-demo`。
- 禁止修改经典原文、来源和思想家归属来迎合权重调节。
- 禁止新增与本任务无关的重构、依赖、后台系统、付费系统或 3D 引擎。
- 禁止引入外部运行时资源到报名 HTML；不得依赖 CDN、外部字体、外链图片或后端。
- 禁止在未实际运行命令时声称“测试通过”“构建成功”或“验收完成”。
- 不要推送远端、部署生产环境或代替用户在社区发布。除这三类外，本地代码、测试、文档、截图和 Git 提交均在授权范围内。
- 每次准备提交前执行 `git diff --check`，只暂存当前任务相关文件，不夹带用户的无关改动。

## 4. 自主决策规则

无需询问用户即可自行处理：

- 文件内部拆分、变量命名、CSS 细节、测试夹具和小范围兼容修复。
- 端口占用时改用其他本地端口，并在最终报告中记录。
- 真实后端暂时不可用时继续完成稳定演示路径和失败恢复测试。
- 旧专项计划与当前文件名不一致时，保持实际交付文件、校验器、报名帖附件名三者一致。
- 产品品牌统一为“悟典”；“一问见古今”可作为参赛创意标题保留，必须在首屏和报名帖中明确它是悟典的参赛方案，不能表现成两个无关产品。
- 已有实现覆盖某个计划步骤时，先添加或运行对应回归测试；通过后标记该步骤已满足，不要为了复现“文件不存在”的初始失败而删除现有成果。

只有以下情况允许停止并请求用户输入：

- 需要用户账号、验证码、密钥或人工登录才能完成外部提交。
- 发现经典引文来源互相冲突且本地资料无法核验。
- 现有用户改动与目标在同一代码段发生不可自动合并的语义冲突。
- 连续三次采用不同合理方案仍被同一外部环境故障阻断。

停止时必须给出已完成项、阻断证据、尝试过的方案和用户只需回答的一个最小问题。

## 5. 总体完成定义

只有同时满足以下条件才算完成：

- `/demo` 首屏直接进入可操作的思想审判场，不再展示主持人指挥台或营销说明页。
- 无需登录即可在 90 秒内走完首个精选案件的四幕流程。
- 三个精选案件均有可核验原文、出处、解释、适用边界、三家立场和行动建议。
- 自由提问使用真实后端；失败时原地保留内容并提供重试或明确的稳定演示替代。
- 证据选择、追问、互问、站队和价值权重至少实际改变一次后续呈现或判牒排序。
- 桌面 1440px 和移动 390px 均无空白主场景、横向溢出、文字遮挡、按钮遮挡或布局跳动。
- 完整动画、减少动画和性能降级三种模式都能完成主流程。
- 报名 HTML 离线可用、小于 20 MB、六张图片内嵌、三个案例可切换、打印样式可用。
- 报名帖超过 100 个汉字，包含官方要求的创意介绍、用户痛点、价值意义和附件说明。
- 前端测试、前端干净构建、后端测试、报名材料校验与 `git diff --check` 全部实际通过。
- `docs/hackathon/trae-evidence.md` 只记录真实 TRAE Session ID、对应功能、截图和提交。

## 6. 阶段 0：保护现场并建立执行记录

- [ ] **Step 0.1：审计工作区**

运行：

```powershell
git status --short
git diff --stat
git log -8 --oneline
```

把起始状态摘要写入执行日志，不修改或暂存已有文件。

- [ ] **Step 0.2：建立执行日志**

创建 `docs/hackathon/trae-execution-log.md`，使用以下固定结构：

```markdown
# TRAE 执行日志

## 起始基线
- 开始时间：
- 当前分支：
- 起始提交：
- 已有未提交改动摘要：

## 阶段记录
| 阶段 | 状态 | 验证命令 | 结果 | 提交 |
| --- | --- | --- | --- | --- |

## 偏差记录
| 原计划 | 实际处理 | 原因 | 风险 |
| --- | --- | --- | --- |

## 最终验证
| 检查项 | 命令或视口 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
```

所有时间、提交号、测试数和证据路径必须来自真实执行结果。

- [ ] **Step 0.3：运行基线检查**

```powershell
node 报名材料/validate-registration-materials.cjs
npm --prefix frontend test
Push-Location backend; python -m pytest tests -q; Pop-Location
```

允许基线失败，但必须把失败命令和错误摘要写入日志。基线失败不等于本任务完成失败；后续需要判断是否与本任务相关并修复。

## 7. 阶段 1：实现思想审判场纯逻辑

完整执行 `docs/superpowers/plans/2026-07-12-thought-court-hackathon.md` 的 Task 1-4：

- [ ] Task 1：领域类型与受保护的法庭状态机。
- [ ] Task 2：三个经过内容完整性校验的精选案件。
- [ ] Task 3：确定性的判牒权重投影，确保引用字段不可变。
- [ ] Task 4：真实会话网关、SSE 事件归一化、部分失败与稳定层策略。

本阶段最小验证：

```powershell
node frontend/tests/thoughtCourtState.test.cjs
node frontend/tests/thoughtCourtCases.test.cjs
node frontend/tests/thoughtCourtVerdict.test.cjs
node frontend/tests/thoughtCourtSession.test.cjs
npm --prefix frontend run build:clean
git diff --check
```

全部通过后，只提交本阶段新增的 `frontend/lib/thoughtCourt*.ts`、对应测试和测试辅助文件。提交信息建议：

```text
feat: add thought court domain and session logic
```

## 8. 阶段 2：实现四幕可操作体验

完整执行思想审判场专项计划的 Task 5-8：

- [ ] Task 5：用薄路由替换 `/demo`，建立隔离的舞台壳与编排 Hook。
- [ ] Task 6：案件选择、自由输入、开审、证据查看、点击与拖拽等价操作。
- [ ] Task 7：三位先贤席位、流式发言、追问、互问、站队和即时本地反馈。
- [ ] Task 8：共识、分歧、证据、权重、行动建议、保留问题和落印。

必须保证：

- `frontend/app/demo/page.tsx` 只负责渲染思想审判场入口，不保留旧指挥台内容。
- 未知长度流式文本只能在固定阅读容器内部滚动，不推动整个舞台。
- 证据卡既可拖拽也可点击选择，键盘用户不依赖拖拽。
- 用户操作在 100ms 内出现本地反馈，远程请求不让控件看似失效。
- 移动端采用纵向四幕，不把桌面环形舞台整体缩小。

本阶段最小验证：

```powershell
node frontend/tests/thoughtCourtWiring.test.cjs
node frontend/tests/thoughtCourtState.test.cjs
node frontend/tests/thoughtCourtVerdict.test.cjs
npm --prefix frontend run build:clean
git diff --check
```

通过后提交本阶段相关路由、组件、样式、Hook 和测试。提交信息建议：

```text
feat: build interactive thought court experience
```

## 9. 阶段 3：完成视觉、动效、无障碍与恢复

完整执行思想审判场专项计划的 Task 9-10：

- [ ] Task 9：有功能含义的 2.5D 调度、可选声音和运行时性能降级。
- [ ] Task 10：移动布局、键盘与读屏支持、减少动画、失败恢复和安全边界。

强制视觉约束：

- 视觉语言为“新东方未来主义 × 数字思想剧场”，使用深墨、骨白、朱砂红、玉青绿和中性灰分工。
- 不使用紫色主导渐变、装饰性光球、卡片套卡片、仿古卷轴页面或无关粒子堆叠。
- 复用现有先贤肖像、典籍和场景资产；人物必须清晰可辨，不以深色遮罩或模糊掩盖主体。
- 卡片圆角不超过 8px；按钮使用已有 Lucide 图标；陌生图标提供可访问名称或提示。
- 所有触控目标至少 44px；固定工具栏、舞台、席位和操作区使用稳定尺寸约束。
- `prefers-reduced-motion` 下禁用视差、震波、长镜头和印章缩放。
- 声音默认关闭，开启后也不能自动播放持续背景音。

本阶段最小验证：

```powershell
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend test
npm --prefix frontend run build:clean
git diff --check
```

通过后提交视觉、交互和恢复相关变更。提交信息建议：

```text
feat: polish thought court motion and accessibility
```

## 10. 阶段 4：集成文档与全量自动验证

完整执行思想审判场专项计划的 Task 11，并按当前仓库实际情况更新：

- [ ] 把新增思想审判场测试加入 `frontend/package.json` 的 `test` 脚本。
- [ ] 更新旧 `/demo` 测试，使其验证新入口且不再要求旧指挥台文本。
- [ ] 更新 `README.md` 的演示说明。
- [ ] 更新 `docs/hackathon/final-delivery-checklist.md`，以思想审判场为主演示路径。
- [ ] 不删除其他页面已有测试，不减少原测试覆盖面。

运行：

```powershell
npm --prefix frontend test
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
Push-Location backend; python -m pytest tests -q; Pop-Location
node 报名材料/validate-registration-materials.cjs
git diff --check
```

每条命令必须退出码为 0。记录实际前端测试项、后端通过数、构建结果和报名材料校验结果。

## 11. 阶段 5：同步报名材料

思想审判场稳定后，再复核并更新报名材料。不要机械重做已通过的产物。

- [ ] **Step 5.1：核对命名与能力陈述**

统一口径：

- 产品品牌：`悟典`
- 参赛创意标题：`一问见古今`
- 一句话定位：`可追溯的中国思想问答入口`
- 核心机制：`先检索、再生成、可追溯、检索不到不硬编`
- 核心体验：思想审判场中的经典举证、多思想交锋、用户介入和行动判牒

报名帖和 HTML 可以使用“一问见古今”作为标题，但正文首段必须明确“这是悟典面向 TRAE 大赛打造的参赛体验”。

- [ ] **Step 5.2：复核实际文件名**

当前允许的交付文件为：

```text
报名材料/一问见古今-TRAE大赛创意提案.html
报名材料/悟典-TRAE大赛报名帖文案.txt
```

若改名，必须同时更新校验脚本、报名帖附件名、执行日志和最终清单。不得保留两个内容不同但都像最终版的 HTML 或报名帖。

- [ ] **Step 5.3：同步真实产品内容**

只更新因思想审判场落地而发生变化的内容：

- 三个案例及问题表述与产品内精选案件一致。
- 引文、出处和人物归属与 `thoughtCourtCases.ts` 一致。
- 不宣称尚未实现的分享、企业后台、付费、3D、语音或线上地址。
- TRAE 实践部分只陈述实际完成的任务和真实 Session 证据。
- HTML 仍为纯单文件、自包含、离线可用且不依赖构建。

- [ ] **Step 5.4：验证材料**

```powershell
node 报名材料/validate-registration-materials.cjs
Get-Item '报名材料/一问见古今-TRAE大赛创意提案.html' | Select-Object Name,Length
```

预期：校验全部通过，HTML 小于 20 MB。

## 12. 阶段 6：浏览器与视觉验收

完整执行思想审判场专项计划的 Task 12，并保存真实截图。

- [ ] **Step 6.1：启动后端**

```powershell
Push-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 6.2：启动前端**

```powershell
npm --prefix frontend run dev:clean
```

使用脚本实际输出的端口；不要假设一定是 3000。

- [ ] **Step 6.3：桌面验收**

在 1440px 宽视口完整走完第一个精选案件，保存以下截图：

```text
docs/hackathon/screenshots/thought-court-1440-intake.png
docs/hackathon/screenshots/thought-court-1440-evidence.png
docs/hackathon/screenshots/thought-court-1440-debate.png
docs/hackathon/screenshots/thought-court-1440-verdict.png
```

- [ ] **Step 6.4：移动验收**

在 390px 宽视口完整走完第一个精选案件，保存：

```text
docs/hackathon/screenshots/thought-court-390-intake.png
docs/hackathon/screenshots/thought-court-390-evidence.png
docs/hackathon/screenshots/thought-court-390-debate.png
docs/hackathon/screenshots/thought-court-390-verdict.png
```

确认无横向滚动，底部操作位于安全区上方，证据抽屉不超过 `70dvh`，长中文可换行，落印不遮挡按钮。

- [ ] **Step 6.5：状态与失败验收**

分别验证：

- 减少动画模式可完成全流程。
- 强制性能降级后内容和操作保留，仅移除环境特效。
- 后端停止时自由提问保留当前舞台和问题，可重试。
- 单个先贤失败时其他席位继续，不导致整场中断。
- 精选案例的稳定数据明确标注，不冒充实时输出。

- [ ] **Step 6.6：报名 HTML 验收**

直接离线打开 HTML，在 1440×1000 和 390×844 检查首屏、六张图片、三个案例、Canvas 降级、键盘操作、打印预览和控制台。

任何视觉缺陷都必须先添加最小回归断言，再修复并重新运行相关测试和构建。

## 13. 阶段 7：TRAE 证据与最终收口

- [ ] **Step 7.1：记录真实 TRAE 创作证据**

创建 `docs/hackathon/trae-evidence.md`：

```markdown
# TRAE 创作证据

| Session ID | 完成功能 | 对应文件 | 截图 | 提交 |
| --- | --- | --- | --- | --- |
```

至少记录 3 个真实 Session。若实际不足 3 个，不得伪造；在最终报告中明确证据不足，并把已有 Session 全部列出。

- [ ] **Step 7.2：执行最终验证**

从仓库根目录运行：

```powershell
npm --prefix frontend test
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
Push-Location backend; python -m pytest tests -q; Pop-Location
node 报名材料/validate-registration-materials.cjs
git diff --check
```

然后确认：

```powershell
Get-ChildItem docs/hackathon/screenshots -File | Select-Object Name,Length
Get-Content -Raw -Encoding UTF8 docs/hackathon/trae-evidence.md
git status --short
```

- [ ] **Step 7.3：提交收口变更**

只在全部验证通过后提交文档、材料同步、截图和 QA 修复。建议提交信息：

```text
docs: finalize TRAE hackathon delivery
```

不要为了得到干净状态而提交本任务之外的既有用户改动。

## 14. 最终回报格式

完成后只提交事实，不写泛泛总结。最终回报必须包含：

```markdown
# 执行结果

## 已完成
- 思想审判场：
- 报名材料：
- 文档与证据：

## 验证结果
| 命令/视口 | 结果 | 关键数据或证据 |
| --- | --- | --- |

## 提交记录
| 提交 | 内容 |
| --- | --- |

## 未完成或外部操作
- 需要用户完成的社区登录、上传或发布：
- 其他残余风险：

## 直接交付路径
- `/demo`：实际本地 URL
- 报名 HTML：绝对路径
- 报名帖文案：绝对路径
- 执行日志：绝对路径
- TRAE 证据：绝对路径
```

不得把“计划完成”“代码已写”当成“验证通过”。只有实际命令结果、浏览器检查和文件证据能够关闭对应检查项。


# PHASE 0 审计：前端主流程、证据展示与测试现状

- 任务：t6（PHASE 0 只读审计）
- 角色：frontend
- 仓库：`D:\systemDir\Desktop\悟典`
- 分支 / HEAD：`codex/overall-optimization` @ `64c8618`
- 审计日期：2026-10-08
- 写入范围：仅本文件（`docs/kb-v1/audit/frontend.md`）。未修改任何前端代码、测试、构建产物、数据或配置。

**审计方法**：全部结论来自对真实源码的读取、`node` 直接执行真实回归套件、以及 `npx` 运行真实构建/类型检查命令。所有命令均在本机实际执行，原始输出摘录于各小节。未使用分享会话或记忆中的描述作为事实。

---

## 0. 结论摘要（TL;DR）

| 编号 | 结论 | 严重度 |
|---|---|---|
| C-1 | 「问→证→辩→判」主流程真实存在于 `/demo` → `ThoughtCourtExperience`，四幕由 `CourtStageChrome` 的 ACTS 定义 | 事实 |
| C-2 | 该 `/demo` 路由**不在任何导航中**（`primaryNav` / `moreNav` 均无），用户无法从 UI 进入主流程 | **high** |
| C-3 | Evidence Drawer 的雏形是 `thought-court/EvidenceDock.tsx`，但只显示 原文 / 出处 / 释义 / 边界 / 已核验，**缺 书名、篇章、文本类型、注疏者、数据来源、可信等级 A–D** | **high** |
| C-4 | 前端**完全没有** `trust_state` / `verification_level` / 数据质量等级概念（全仓 grep 0 命中） | **high** |
| C-5 | `normalizeCitations` 把「相关度」**伪造**为 0 或 1，UI 显示为「相关度 100%」 | **high** |
| C-6 | `normalizeCitations` **硬编码** `type: "verse"`，注疏永远无法被渲染为注疏，违反「原文/注疏分层」 | **high** |
| C-7 | `normalizeEvidence` 对缺失字段回退到**写死的释义与边界文案**，并在字段缺失时默认 `verified: true`（显示「已核验」） | **high** |
| C-8 | mock / 精选案例路径**硬编码** `verifiable: true` / `verified: true`，无来源 | **high** |
| C-9 | `sageData.ts` 的「相关度」是**手写常量** 0.78–0.95，非检索得分 | **medium** |
| C-10 | 22 个真实回归套件是 `.test.cjs`，被 `vitest.config.ts` **显式排除**，`npm test` 与 CI 都不运行它们 | **high** |
| C-11 | 23 个 vitest 文件中 20 个是 `expect(true).toBe(true)` 占位符；`npm test` 全绿并不代表任何真实断言 | **high** |
| C-12 | 4 个 `.cjs` 套件**实际失败**（comic / reader / tengwang / runtimeAssets） | **high** |
| C-13 | `npx tsc --noEmit` **失败**，26 个错误全部在 `tests/curtainPhysics.test.tsx`，CI 的 typescript-check job 会红 | **high** |
| C-14 | 前端**不存在 ESLint 配置文件**，CI 的 lint job（`npx eslint`）以 exit 2 失败；`npm run lint` 进入交互式向导 | **high** |
| C-15 | `roundtableData.ts` 存在**错误的出处**：《韩非子·物权》应为《韩非子·扬权》，本仓库自身数据也无「物权」篇 | **high** |
| C-16 | 判词页「落判」按钮在 `verdict` 阶段是**空操作**，且 `completed` 阶段**从 UI 不可达** | **medium** |
| C-17 | 跨学派泄露在 UI 上**不可识别**：无 school 字段、无逐派校验状态 | **high** |

---

## 1. 主流程现状图（问 → 证 → 辩 → 判）

### 1.1 真实承载页面

「问→证→辩→判」的真实载体是 **`/demo`**，不是 `/roundtable`：

```tsx
// frontend/app/demo/page.tsx:1-5
import ThoughtCourtExperience from "@/components/thought-court/ThoughtCourtExperience";
export default function DemoPage() {
  return <ThoughtCourtExperience />;
}
```

四幕定义（这是「问/证/辩/判」的唯一权威来源）：

```tsx
// frontend/components/thought-court/CourtStageChrome.tsx:9-14
const ACTS: { key: string; label: string; phases: CourtPhase[] }[] = [
  { key: "问", label: "立案问询", phases: ["idle", "intake"] },
  { key: "证", label: "取证核验", phases: ["retrieving", "evidence"] },
  { key: "辩", label: "三方辩论", phases: ["debate"] },
  { key: "判", label: "落判定夺", phases: ["weighting", "verdict", "completed"] },
];
```

### 1.2 逐步映射

| 幕 | 阶段 (CourtPhase) | 页面/组件 | 关键代码位置 | 接口调用 |
|---|---|---|---|---|
| 问 | `idle` / `intake` | `CaseIntake.tsx` | `ThoughtCourtExperience.tsx:126-141`；`CaseIntake.tsx:60-141` | 无（纯前端立案） |
| 证 | `retrieving` | `ThoughtCourtExperience.tsx:143-161` | 同上 | `POST /debate/start` + SSE `debateStream(next-round)` |
| 证 | `evidence` | `EvidenceDock.tsx` | `ThoughtCourtExperience.tsx:163-177` | 无（消费已检索证据） |
| 辩 | `debate` | `SageTribunal.tsx` | `ThoughtCourtExperience.tsx:179-195` | `intervene` / `mutual-question` / `stand` |
| 判 | `weighting` / `verdict` / `completed` | `VerdictScroll.tsx` | `ThoughtCourtExperience.tsx:197-218` | `GET /debate/{id}/report` |

状态机（真实转移规则）：

```ts
// frontend/lib/thoughtCourtState.ts:69-79
if (event.type === "SUBMIT_CASE" && state.phase === "intake" && event.question.trim())
  return { ...state, phase: "retrieving", ... };
if (event.type === "RETRIEVAL_SUCCEEDED" && state.phase === "retrieving")
  return { ...state, phase: "evidence", ... };
if (event.type === "BEGIN_DEBATE" && state.phase === "evidence") return { ...state, phase: "debate", ... };
if (event.type === "DEBATE_SUCCEEDED" && state.phase === "debate") return { ...state, phase: "weighting", ... };
if (event.type === "BUILD_VERDICT" && state.phase === "weighting") return { ...state, phase: "verdict" };
if (event.type === "COMPLETE" && state.phase === "verdict") return { ...state, phase: "completed" };
```

### 1.3 证据产生的真实链路（证）

```ts
// frontend/lib/thoughtCourtSession.ts:39-67
export async function prepareLiveCourt(topic, sages, gateway, emit) {
  emit({ type: "REMOTE_LOADING" });
  const started = await gateway.startDebate(topic, sages);
  emit({ type: "REMOTE_STREAMING" });
  const evidence: CourtEvidence[] = [];
  await gateway.streamRound(started.sessionId, (event) => {
    if (event.type === "sage_end") {
      const normalized = (event.speech?.citations || [])
        .map((citation, index) => normalizeEvidence(sageId, citation, index))
        .filter(...);
      evidence.push(...normalized);
    }
    ...
  });
  const verifiedCount = evidence.filter((item) => item.verified).length;
  const citationStatus = verifiedCount === 0 ? "unavailable"
    : verifiedCount === evidence.length && speeches.every((s) => s.status === "complete") ? "verified"
    : "partial";
  ...
}
```

**关键事实**：证据**不是**由后端 Evidence Pack 直接下发，而是前端从 SSE 的 `sage_end.speech.citations` **就地合成** `CourtEvidence`。后端不存在 evidence pack 端点（`frontend/lib/api.ts` 中无 `knowledge` / `evidence` / `verify` 相关调用，仅命中注释行 `850/908/967/1172`）。

### 1.4 并存的第二条（旧）主流程：`/roundtable`

| 项 | 实现 |
|---|---|
| 页面 | `frontend/app/roundtable/page.tsx`（38859 bytes） |
| 阶段 | `select` / `debating` / `complete`（`roundtableFlow.ts:21`） |
| 引用汇总 | `CitationPanel.tsx`，**仅当 `phase === "complete"` 才渲染**（`app/roundtable/page.tsx:788-795`） |
| 逐句证据 | `SageSpeechCard.tsx:128-155` 渲染 `sentenceEvidence` |

注意：`/roundtable` **不是**「问→证→辩→判」；它没有独立的「证」幕，引用在辩论结束后才汇总出现。两套流程的引用规范化函数是**同一个** `normalizeCitations`，因此 C-5/C-6 同时影响两者。

### 1.5 第三条：`/sage-chat`

`SageChat.tsx:329-338` 渲染 `CitationSidebar`；引用来自 SSE `type === "citations"`（`api.ts:1106-1108`）。

### 1.5.1 判幕的断链（C-16 证据）

`VerdictScroll` 的「落判」按钮绑定到 `court.buildVerdict`：

```tsx
// frontend/components/thought-court/ThoughtCourtExperience.tsx:210-212
completed={state.phase === "verdict" || state.phase === "completed"}
onSetWeights={court.setWeights}
onComplete={court.buildVerdict}
```

```tsx
// frontend/components/thought-court/VerdictScroll.tsx:189-196
{!completed ? (
  <button type="button" className={styles.primaryAction} onClick={onComplete}>
    落判
  </button>
) : ( ... )}
```

但 `buildVerdict` **只在 `debate` 与 `weighting` 阶段有行为**：

```ts
// frontend/components/thought-court/useThoughtCourt.ts:250-256
const buildVerdict = useCallback(() => {
  if (state.phase === "debate") {
    dispatch({ type: "DEBATE_SUCCEEDED" });
  } else if (state.phase === "weighting") {
    dispatch({ type: "BUILD_VERDICT" });
  }
}, [state.phase]);
```

进入 `verdict` 阶段后，`completed` 属性变为 `true`，按钮切换为「重新调权 / 新开一案」，因此**「落判」按钮只在 `weighting` 阶段出现**——此时它派发 `BUILD_VERDICT`，进入 `verdict`。逻辑自洽。

真正的缺口是 **`COMPLETE` 事件无人派发**：`useThoughtCourt.ts:262-264` 导出的 `complete()` 从未被任何组件调用（全仓 grep `court.complete` / `.complete()` 在 `app/` 与 `components/` 下 **0 命中**），而 `completed` 是 `CourtStageChrome.tsx:13` 的「判」幕与 `ThoughtCourtExperience.tsx:22` 的「本案已结」所依赖的状态。因此：

- `CourtPhase` 中的 `"completed"` 与 `ACT_NAMES.completed = "本案已结"`（`ThoughtCourtExperience.tsx:22`）为**死代码**。
- `ThoughtCourtExperience.tsx:200` 的 `state.phase === "completed"` 分支永远不触发。

**影响**：判幕无法到达终态，`/demo` 流程的「判」在 UI 上停在 `verdict`。这不阻塞 Evidence Drawer，但意味着**流程完整性无法作为端到端验收**。

### 1.6 导航现状（C-2 证据）
```tsx
// frontend/components/Navbar.tsx:11-26
const primaryNav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/sage-chat", label: "问道", icon: MessagesSquare },
  { href: "/reader", label: "经典", icon: BookOpen },
  { href: "/roundtable", label: "论道", icon: Users },
  { href: "/exploration", label: "探索", icon: Network },
];
const moreNav = [
  { href: "/challenge", ... }, { href: "/review", ... }, { href: "/content", ... },
  { href: "/community", ... }, { href: "/achievements", ... }, { href: "/about", ... },
];
```

`/demo` 不在 `allNav` 中（`Navbar.tsx:28`）。`hackathonReadiness.test.cjs:63-66` 甚至**断言** `primaryNav` 不应包含 `/demo`：

```js
assert.ok(
  !primaryNavMatch[0].includes('href: "/demo"'),
  "Formal product navigation should not foreground the retired demo route"
);
```

**影响**：作为 V1 可信主流程载体的 `/demo` 对用户不可达。Evidence Drawer 无论做得多好，若宿主路由不可进入，PHASE 7 的 GATE-7 无法通过人工验收。

---

## 2. 证据展示现状（逐项核对）

### 2.1 现有数据模型

```ts
// frontend/lib/thoughtCourtTypes.ts:9-17
export interface CourtEvidence {
  id: string;
  sageId: string;
  original: string;
  source: string;
  interpretation: string;
  boundary: string;
  verified: boolean;
}
```

```ts
// frontend/lib/types.ts:348-361
export interface Citation {
  text: string;
  source: string;
  chapter?: string;
  verse_no?: number;
  similarity: number;
  type: "verse" | "commentary";
}
```

### 2.2 逐项核对表

| PROJECT-BRIEF 第七章要求 | 现状 | 证据 |
|---|---|---|
| 原文 | **已展示** | `EvidenceDock.tsx:87` `{item.original}`；`CitationSidebar.tsx:231`；`CitationPanel.tsx:110` |
| 出处 | **已展示（仅字符串）** | `EvidenceDock.tsx:88` `{item.source}` |
| 书名 | **缺失**（无字段） | `CourtEvidence` / `Citation` 均无 `book_title` |
| 篇章 | **缺失/错误** | `Citation.chapter` 存在，但被赋值为 `source` 的副本（`roundtableFlow.ts:179` `chapter: source`），非真实篇章 |
| 文本类型 | **缺失（且被伪造）** | `CourtEvidence` 无该字段；`roundtableFlow.ts:182` 硬编码 `type: "verse"` |
| 注疏者 | **缺失**（无字段） | 全仓无 `commentator` |
| 数据来源 | **缺失** | 无 `source_provider` / `source_url` / `source_edition` / `license` |
| 校验状态 | **部分** | `CitationStatus` 三态（见 2.3）与逐条 `verified: boolean` |
| 可信等级（A/B/C/D） | **缺失** | 全仓 grep `qualityGrade|verification_level|可信等级|数据质量` → **0 命中** |
| Trust State | **缺失** | 全仓 grep `trust_state|trustState` → **0 命中** |

### 2.3 校验状态的真实语义

```ts
// frontend/lib/thoughtCourtTypes.ts:4
export type CitationStatus = "verified" | "partial" | "unavailable";
```

```tsx
// frontend/components/thought-court/EvidenceDock.tsx:22-24
verified:    { label: "已核验", icon: ShieldCheck, className: styles.statusVerified },
partial:     { label: "依据不完整", icon: ShieldAlert, className: styles.statusPartial },
unavailable: { label: "未找到足够可靠的经典依据", icon: ShieldQuestion, className: styles.statusUnavailable },
```

这与 PROJECT-BRIEF 第十二章要求的四态 `verified / citation_corrected / quote_relaxed / insufficient_evidence` **不对应**：缺 `citation_corrected` 与 `quote_relaxed`，且 `verified` 的判定依据是前端布尔统计而非可信层结论。

### 2.4 是否把 AI 解释与原文原典混在一起展示？——**是，部分混淆**

`EvidenceDock` 展开区把 AI 生成的释义与人工边界文案和原文并列在同一卡片内：

```tsx
// frontend/components/thought-court/EvidenceDock.tsx:92-106
{isExpanded && (
  <div id={detailId} className={styles.evidenceDetail}>
    <p className={styles.evidenceRow}>
      <span className={styles.evidenceRowLabel}>释义</span>
      {item.interpretation}     {/* AI/模板生成 */}
    </p>
    <p className={styles.evidenceRow}>
      <span className={styles.evidenceRowLabel}>边界</span>
      {item.boundary}           {/* 写死常量或模板 */}
    </p>
    <p className={styles.evidenceVerify}>{item.verified ? "已核验" : "待核验"}</p>
  </div>
)}
```

正面之处：`SageSpeechCard` 对模型输出用了显式标签分区（`原文` / `白话点睛`，`SageSpeechCard.tsx:195-227`），`CitationSidebar.tsx:208-212` 对 `type === "commentary"` 显示「注疏」徽标。但后者在 roundtable 链路上**永远无法触发**（见 C-6）。

### 2.5 伪造的相关度（C-5 证据）

```ts
// frontend/lib/roundtableFlow.ts:171-186
export function normalizeCitations(citations: BackendCitation[]): Citation[] {
  return citations
    .map((citation) => {
      const text = citation.original || citation.原文 || "";
      const source = citation.source || citation.出处 || "未知出处";
      return {
        text, source,
        chapter: source,
        verse_no: undefined,
        similarity: citation.verifiable === false ? 0 : 1,   // ← 伪造
        type: "verse" as const,                              // ← 硬编码
      };
    })
    .filter((citation) => citation.text && citation.text !== "无");
}
```

后端 `Citation` 契约里**没有** `similarity` 字段：

```python
# backend/app/schemas/debate.py:95-100
class Citation(BaseModel):
    id: str = Field(..., description="引用标记，如 引1")
    source: str = Field(..., alias="出处", description="出处，如《论语·学而》")
    original: str = Field(..., alias="原文", description="经典原文")
    verifiable: bool = Field(True, description="是否通过引用校验")
```

于是只要后端返回 `verifiable: true`，前端就把它当作 `similarity = 1`，并在 UI 上显示为**「相关度 100%」**：

```tsx
// frontend/components/roundtable/CitationPanel.tsx:102-104
<span className="ml-auto text-[10px] text-ink-300 dark:text-rice-500">
  相关度 {Math.round(citation.similarity * 100)}%
</span>
```

同一问题出现在 `SageSpeechCard.tsx:111-113`。这是**把「引用存在性校验通过」冒充为「检索相关度 100%」**，属于对用户的可信度误导，直接违背核心承诺「每个观点都能追到原典」。

### 2.6 缺失字段的静默兜底（C-7 证据）

```ts
// frontend/lib/thoughtCourtSession.ts:24-37
function normalizeEvidence(sageId: string, citation: any, index: number): CourtEvidence | null {
  const original = citation.original || citation.text || "";
  const source = citation.source || "";
  if (!original || !source) return null;
  return {
    id: `live-${sageId}-${index}`,
    sageId, original, source,
    interpretation: citation.commentary || "该原文为当前观点提供思想依据。",   // ← 写死文案
    boundary: "请结合现实情境判断，勿将单句经典当作强制命令。",                 // ← 写死常量
    verified: citation.verifiable !== false,                                  // ← 缺失即视为已核验
  };
}
```

三个独立缺陷：
1. `interpretation` 在后端未提供注疏时，用一句**通用模板**冒充释义。
2. `boundary` 是**完全写死**的常量，与具体经典无关，却以「边界」标签呈现给用户。
3. `citation.verifiable !== false` 使**字段缺失**（`undefined`）被判定为 `verified: true`，即「已核验」。正确语义应是「无法确认 → 未核验」。

### 2.7 硬编码可信标记（C-8 证据）

Mock/演示路径直接写死 `verifiable: true`：

```ts
// frontend/lib/api.ts:2012
citations: [{ id: "引1", source: "《论语·泰伯》", original: "士不可以不弘毅，任重而道远。", verifiable: true }],
```

```ts
// frontend/lib/api.ts:2034-2039
citations: speech.citations.map((citation, idx) => ({
  id: `引${idx + 1}`,
  source: citation.source,
  original: citation.text,
  verifiable: true,          // ← 恒为 true
})),
```

精选案例同样写死（`thoughtCourtCases.ts:13/14/15/45/46/47/77/78/79`），并被测试**强制断言**为 `true`：

```js
// frontend/tests/thoughtCourtCases.test.cjs:20
assert.equal(evidence.verified, true);
```

这些数据没有 `source_provider` / `source_url` / 复核状态，却以「已核验」呈现。它们**不得**被当作 A 级权威原典，也**不得**作为 Evidence Drawer 的验收样本。

### 2.8 手写的「相关度」（C-9 证据）

```ts
// frontend/lib/sageData.ts:106-137（节选）
const localSageCitations: Record<string, Citation[]> = {
  confucius: [
    { text: "人不知而不愠，不亦君子乎", source: "《论语·学而》", chapter: "学而篇", verse_no: 1, similarity: 0.95, type: "verse" },
    ...
    { text: "过则勿惮改", source: "《论语·学而》", chapter: "学而篇", verse_no: 8, similarity: 0.78, type: "verse" },
  ],
  ...
};
```

这些 0.78–0.95 是**人工填写的常量**，会被当作检索相关度渲染。它们经 `SageChat.tsx:172-174` 在真实请求失败时作为兜底推给用户：

```ts
// frontend/components/sage/SageChat.tsx:171-174
if (abortRef.current === false) {
  const fallback = generateSageReply(sage.id, content);
  const fallbackCitations = getLocalSageCitations(sage.id);
  onCitationsChange?.(fallbackCitations);
```

**风险**：后端不可用时，用户会看到「基于经典」的回答与「相关度 95%」的引用，而实际上与本次提问**毫无检索关系**。`generateSageReply` 末尾有免责声明（`sageData.ts:163`），但引用卡片本身无任何降级标识。

### 2.9 错误的出处（C-15 证据）

```ts
// frontend/lib/roundtableData.ts:199
{ text: "事在四方，要在中央", source: "《韩非子·物权》", chapter: "物权", verse_no: 1, similarity: 0.90, type: "verse" },
```

本仓库自身语料中**没有**「物权」篇：

```
$ python -c "import json;d=json.load(open('data/processed/debate_classics.json',encoding='utf-8'));[print(x.get('chapter'),'|',x.get('source')) for x in d['classics']['hanfeizi']['verses']]"
有度 | 《韩非子·有度》
二柄 | 《韩非子·二柄》
外储说左上 | 《韩非子·外储说左上》
五蠹 | 《韩非子·五蠹》
```

「事在四方，要在中央」出自《韩非子·扬权》。这是**编造 source** 的实例，恰好命中 PROJECT-BRIEF 第十六章的对抗场景。前端硬编码数据必须纳入来源审计。

---

## 3. 多学派展示现状

### 3.1 现有的学派区分手段

| 手段 | 位置 | 评价 |
|---|---|---|
| 发言卡片按 `sageId` 分栏 | `SageTribunal.tsx:95-112` `data-sage={sageId}` | 发言层面可区分 |
| 引用归属显示「X 所引」 | `CitationPanel.tsx:93-95` `{sageNames[sageId]}所引` | 仅显示归属，不校验 |
| 头像/配色 | `SageTribunal.tsx:103,120-131` | 视觉区分，非语义 |

### 3.2 跨派泄露在 UI 上不可识别（C-17）

- `CourtEvidence`（`thoughtCourtTypes.ts:9-17`）**有** `sageId`，但**没有** `school` 字段。
- `Citation`（`types.ts:348-361`）**完全没有**学派字段。
- 前端**没有任何**「该引用是否属于本派」的判定或提示。
- `SageTribunal` 只渲染发言正文，**不渲染任何引用**（grep `evidence|依据` 在该文件仅命中 `data-sage` 与文案），因此辩论过程中用户看不到发言引了哪本书。

**结论**：即使后端 `citation_validator._check_classic_belonging`（`backend/app/services/citation_validator.py:95-101`）判定为跨派并置 `verifiable=False`，前端也**没有学派维度的呈现**来暴露这一事实；用户只会看到该条引用从列表里消失或变成「待核验」，无法得知「孔子引了《韩非子》」。

**对 GATE-6（跨派引用泄露率 <1%）的影响**：该指标目前**只能在后端度量**，前端无法提供独立的可见性验证，也无法做 UI 层回归。

### 3.3 三圣硬编码

```ts
// frontend/components/thought-court/ThoughtCourtExperience.tsx:25
const LIVE_SAGES = ["confucius", "mencius", "laozi"];
```

```ts
// frontend/components/thought-court/useThoughtCourt.ts:26
const SAGE_ORDER = ["confucius", "mencius", "laozi"];
```

实时问道**固定为儒道三家**，不含墨子/韩非。PROJECT-BRIEF 第二十章节 PHASE 6 要求「孔子/老子/墨子/韩非必须从各自 Evidence Pack 发言」，前端目前**不支持**墨家与法家席位。

---

## 4. 测试与验证现状

### 4.1 真实可用的命令

| 命令 | 实测结果 | 退出码 |
|---|---|---|
| `cd frontend; npm test`（=`vitest run`） | 23 files / 41 tests **passed** | 0 |
| `cd frontend; npx tsc --noEmit` | **26 errors** | **2** |
| `cd frontend; npm run lint`（=`next lint`） | 进入交互式配置向导，无 ESLint 配置 | **1** |
| `cd frontend; npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0` | `ESLint couldn't find a configuration file` | **2** |
| `cd frontend; npx next build` | 成功，19 路由预渲染 | 0 |
| `node tests/<name>.test.cjs`（逐个） | 18 pass / **4 fail** | 1 |

原始输出摘录：

```
$ cd frontend; npx vitest run
 Test Files  23 passed (23)
      Tests  41 passed (41)
   Duration  12.43s

$ cd frontend; npx tsc --noEmit
tests/curtainPhysics.test.tsx(42,12): error TS2532: Object is possibly 'undefined'.
... (共 26 条，全部位于 tests/curtainPhysics.test.tsx)
TSC_EXIT=2

$ cd frontend; npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0
Oops! Something went wrong! :(
ESLint: 8.57.1
ESLint couldn't find a configuration file. ...
ESLINT_EXIT=2
```

### 4.2 `.cjs` / `.tsx` 成对模式的真相（C-10 / C-11）

`vitest.config.ts` **显式排除** `.cjs`：

```ts
// frontend/vitest.config.ts:12-15
test: {
  environment: "jsdom",
  globals: true,
  include: ["tests/**/*.test.tsx", "tests/**/*.test.ts"],
  exclude: ["tests/helpers/**", "tests/*.test.cjs"],
},
```

而**真实断言全部写在 `.cjs` 里**。23 个被执行的 vitest 文件中，20 个是占位符：

```
$ Select-String -Path frontend/tests/*.test.tsx,frontend/tests/*.test.ts -Pattern 'expect\(true\)\.toBe\(true\)'
→ 20 命中

// frontend/tests/sageChatWiring.test.tsx（完整内容）
import { describe, it, expect } from "vitest";
describe("sageChatWiring", () => {
  it("placeholder", () => { expect(true).toBe(true); });
});
```

**只有 3 个 vitest 文件含真实断言**：`curtainPhysics.test.tsx`（12）、`thoughtCompass.test.tsx`（5）、`thoughtCourtState.test.tsx`（4），合计 **21 个真实断言**；其余 **20 个占位断言**。即 `41 passed` 中 **20 条（49%）为恒真**。

**影响**：`npm test` 的「23 files / 41 tests passed」有近一半是恒真断言，且**全部覆盖 UI 渲染与数据映射的套件都是占位符**（`sageChatWiring`、`thoughtCourtWiring`、`thoughtCourtCases`、`roundtableFlow`、`readerExperience` 等）。`ci.yml:67-69` 的 `npm test` 因此是一个**近乎空门禁**：它无法发现本报告 C-5/C-6/C-7 这类真实缺陷。而 22 个真正校验源码契约的 `.cjs` 套件**既不在 `npm test` 中，也不在 CI 中**。

### 4.3 真实回归套件的失败（C-12）

逐个直接执行 `.cjs`：

```
$ foreach ($f in Get-ChildItem frontend/tests -Filter *.test.cjs) { node $f }
FAILED: comicExperienceWiring.test.cjs
  AssertionError [ERR_ASSERTION]: npm test should include comic experience wiring checks
FAILED: readerExperience.test.cjs
  AssertionError [ERR_ASSERTION]: the default frontend test suite should include reader regression checks
FAILED: runtimeAssets.test.cjs
  [TypeError: fetch failed] { [cause]: AggregateError [ECONNREFUSED] }
FAILED: tengwangExperienceWiring.test.cjs
  AssertionError [ERR_ASSERTION]: package.json scripts.test should run curtain physics and Tengwang wiring first
CJS PASS=18 FAIL=4 TOTAL=22
```

失败断言原文：

```js
// frontend/tests/comicExperienceWiring.test.cjs:57-60
assert(packageSource.includes("comicExperienceWiring.test.cjs"),
  "npm test should include comic experience wiring checks");

// frontend/tests/readerExperience.test.cjs:141-145
assert.match(pkg, /readerExperience\.test\.cjs/,
  "the default frontend test suite should include reader regression checks");

// frontend/tests/tengwangExperienceWiring.test.cjs:366-369
packageJson.scripts.test.startsWith(
  "node tests/curtainPhysics.test.cjs && node tests/tengwangExperienceWiring.test.cjs && "),
  "package.json scripts.test should run curtain physics and Tengwang wiring first"
```

前三个失败的根因相同：`frontend/package.json:12` 的 `"test": "vitest run"` **曾**被期望串接 `.cjs` 套件，后来被改成纯 vitest，但断言未同步。这证明**仓库曾在某个时间点运行真实回归，之后被静默削弱**。

第四个（`runtimeAssets.test.cjs`）需要 `http://localhost:3000` 上有运行中的站点（`runtimeAssets.test.cjs:3`），属于**环境依赖**，非代码缺陷；但它在无服务时以 ECONNREFUSED 失败，说明它无法在纯 CI 中裸跑。

### 4.4 断言强度评估

**弱断言（仅存在性/字符串匹配）**：绝大多数 `.cjs` 套件是 `source.includes(...)` 源码文本匹配，例如：

```js
// frontend/tests/thoughtCourtWiring.test.cjs:36-41
const evidenceDock = read("components/thought-court/EvidenceDock.tsx");
assert.ok(evidenceDock.includes("aria-expanded"));
assert.ok(evidenceDock.includes("加入本案"));
assert.ok(evidenceDock.includes("已核验"));
assert.ok(evidenceDock.includes("依据不完整"));
assert.ok(evidenceDock.includes("未找到足够可靠的经典依据"));
```

这类断言**只验证字符串存在**，不验证渲染结果、不验证数据流、不验证「已核验」是否被正确计算。`thoughtCourtWiring.test.cjs:39` 断言源码含「已核验」——而 C-7 恰恰说明「已核验」会被错误地显示。**该测试无法发现这个 bug**。

**唯一有真实语义的断言**集中在 3 个纯逻辑模块：

```ts
// frontend/tests/thoughtCourtState.test.tsx:12-32（状态机全生命周期）
// frontend/tests/thoughtCourtVerdict.test.ts（权重归一化与主导键）
// frontend/tests/curtainPhysics.test.tsx（帘幕物理，12 tests）
```

**零覆盖区域**（无任何真实断言）：
- `EvidenceDock` 的渲染输出与展开行为
- `normalizeCitations` / `normalizeEvidence` 的字段映射（C-5/C-6/C-7 的所在）
- `prepareLiveCourt` 的 `citationStatus` 计算
- `CitationSidebar` / `CitationPanel` 的实际渲染
- 任何 `api.ts` 的真实请求路径
- 学派归属与跨派校验

### 4.5 对 PHASE 9 / GATE-7 的直接后果
PROJECT-BRIEF 第二十章节 PHASE 9 要求执行 `frontend tests / build / lint / typecheck` 且「禁止破坏旧功能」。当前基线：

| 检查 | 现状 | 可否作为回归基线 |
|---|---|---|
| `npm test` | 绿，但 20/23 是占位符 | **否**，无判别力 |
| `npx tsc --noEmit` | **红**（26 errors） | **否**，需先修 |
| `npm run lint` / `npx eslint` | **红**（无配置） | **否**，需先建配置 |
| `npx next build` | 绿 | 是 |
| `.cjs` 套件 | 4 红 / 18 绿，且不在 CI | 需先接入并修绿 |

**结论**：当前前端**没有可信的回归门禁**。在修复 4.2–4.4 之前，任何「前端回归 PASS」的声明都不成立。

---

## 5. Evidence Drawer 增量设计约束

> 本节仅给出约束与建议路径，**未创建任何文件**。

### 5.1 现有可复用资产

| 资产 | 路径 | 复用方式 |
|---|---|---|
| 证据卡片与状态徽标 | `components/thought-court/EvidenceDock.tsx` | 扩展为 Drawer 主体，保留 `aria-expanded` / `aria-controls` 无障碍结构 |
| 证据数据模型 | `lib/thoughtCourtTypes.ts` `CourtEvidence` | **扩展字段**，不新建并行类型 |
| 状态机 | `lib/thoughtCourtState.ts` | `citationStatus` 需扩展为四态 Trust State |
| 移动端底部抽屉样式 | `ThoughtCourt.module.css:1362-1374` | `.evidenceDock` 已是 `max-height: 70dvh` 底部抽屉 |
| 注疏徽标 | `components/sage/CitationSidebar.tsx:208-212` | 抽为共享 `EvidenceBadge` |
| 引用规范化 | `lib/roundtableFlow.ts:171-186` | **必须修复**，否则 Drawer 拿不到真实字段 |

### 5.2 必须扩展的字段（与后端新增字段对接点）

```ts
// 建议：扩展 lib/thoughtCourtTypes.ts 的 CourtEvidence
export type TextType = "original" | "commentary" | "translation" | "modern_explanation";
export type QualityGrade = "A" | "B" | "C" | "D";
export type TrustState = "verified" | "citation_corrected" | "quote_relaxed" | "insufficient_evidence";

export interface EvidenceProvenance {
  book_id?: string;        // 后端 passage.book_id
  book_title?: string;     // 后端 passage.book_title
  chapter_id?: string;
  chapter_title?: string;
  section?: string;
  line_no?: number;
  source_provider?: string;  // 后端 passage.source_provider
  source_url?: string;       // 后端 passage.source_url
  source_edition?: string;   // 后端 passage.source_edition
  license?: string;
  commentator?: string;      // 后端 passage.commentator
  commentary_dynasty?: string;
  verification_level?: string;
  proofread_status?: string;
}
```

**对接点**：`lib/thoughtCourtSession.ts:24-37` 的 `normalizeEvidence` 是唯一入口；`lib/roundtableFlow.ts:171-186` 的 `normalizeCitations` 是第二条入口。两者都必须改为**透传后端字段、缺失即 `undefined`**，禁止回退到写死文案。

### 5.3 Desktop 布局要求

- 现状：`ThoughtCourt.module.css:536-544` `.evidenceDock` 为 `max-width: 720px; margin: 0 auto`，居中单列。
- 目标：桌面端「左判词 / 右证据」或「主区 + 右侧悬浮 Drawer」，且**不遮挡** `VerdictScroll` 的权重滑杆。
- 注意：`CitationSidebar.tsx:58-62` 的注释明确写了「桌面端：不作为侧栏，保持在消息下方」，说明历史上有过侧栏方案被回退。新方案需说明为何不会重蹈覆盖问题。
- 必须保留 `aria-label="经典依据"`（`EvidenceDock.tsx:49`）与 `.evidenceDock:focus-visible` 样式（`ThoughtCourt.module.css:632-635`）。

### 5.4 Mobile 布局要求

已有移动端基础（`ThoughtCourt.module.css:1271-1399`）：
- `.evidenceDock` 已是底部抽屉：`max-height: 70dvh; overflow-y: auto`（1363-1370）
- `.evidenceList` 限高 `50dvh`（1372-1374）
- 390px 防溢出：`max-width: 100%; box-sizing: border-box`（1388-1394）
- 安全区：`env(safe-area-inset-bottom)` 已存在（由 `thoughtCourtWiring.test.cjs:292` 断言）

新增字段（书名/篇章/文本类型/注疏者/来源/校验/等级）会显著增加卡片高度，**必须**：
- 保持 44px 最小可点区域（`min-height: 44px`，现有 `ThoughtCourt.module.css:629`）
- 在 390px 下用折行/堆叠而非横向溢出
- 长 `source_url` 需截断或改为「查看底本」外链

### 5.5 建议新增/修改文件清单（**未创建**）

| 路径 | 类型 | 用途 |
|---|---|---|
| `frontend/lib/thoughtCourtTypes.ts` | 修改 | 扩展 `CourtEvidence`；新增 `TrustState` / `QualityGrade` / `TextType` / `EvidenceProvenance` |
| `frontend/lib/roundtableFlow.ts` | 修改 | **修复** `normalizeCitations`（C-5/C-6），透传真实字段 |
| `frontend/lib/thoughtCourtSession.ts` | 修改 | **修复** `normalizeEvidence`（C-7），移除写死文案与默认已核验 |
| `frontend/lib/thoughtCourtState.ts` | 修改 | `CitationStatus` 扩展为四态 Trust State |
| `frontend/components/thought-court/EvidenceDock.tsx` | 修改 | 渲染新增字段；Desktop/Mobile 双布局 |
| `frontend/components/thought-court/EvidenceDrawer.tsx` | **新增** | 若需独立抽屉容器（含焦点陷阱），复用 `lib/useDialogFocus.ts` |
| `frontend/components/ui/EvidenceBadge.tsx` | **新增** | 共享的 文本类型 / 校验状态 / 质量等级 徽标 |
| `frontend/components/thought-court/ThoughtCourt.module.css` | 修改 | 新增字段样式 + 双端布局 |
| `frontend/components/roundtable/CitationPanel.tsx` | 修改 | 移除伪造「相关度」，改显 Trust State |
| `frontend/components/sage/CitationSidebar.tsx` | 修改 | 同上；保留「注疏」徽标逻辑 |
| `frontend/lib/types.ts` | 修改 | 扩展 `Citation`（`book_title` / `text_type` / `trust_state` / `quality_grade`） |
| `frontend/tests/evidenceDrawer.test.cjs` | **新增** | 真实渲染断言（非 `includes` 字符串匹配） |

**关键约束**：`lib/useDialogFocus.ts` 已存在且被 `ImageSourceLink.tsx` / `ChapterSelector.tsx` 使用，Drawer 若做模态必须复用，不得另写焦点管理。

---

## 6. 回归风险清单

| 风险 | 触发点 | 受影响对象 | 缓解 |
|---|---|---|---|
| R-1 | 修改 `normalizeCitations`（C-5/C-6） | `/roundtable` 的 `CitationPanel`、`SageSpeechCard`；`/sage-chat` | 断言 `thoughtCourtWiring`/`sageChatWiring` 的 `.cjs` 需同步；先接入 CI 再改 |
| R-2 | 修改 `normalizeEvidence`（C-7） | `/demo` 全流程 | 无真实测试覆盖，需**先补测试再改** |
| R-3 | 扩展 `CourtEvidence` | `thoughtCourtCases.ts` 3 个精选案例（含 `verified: true`）、`thoughtCourtCases.test.cjs:20` | 扩展字段须为可选，否则 3 个案例与测试全部编译失败 |
| R-4 | 扩展 `CitationStatus` | `thoughtCourtState.ts:42` 默认值 `"unavailable"`、`EvidenceDock.tsx:18-25` 的 `Record<CitationStatus, ...>`（穷尽映射，漏项即 TS 错误） | 同步更新 `STATUS_CONFIG` |
| R-5 | `tsc --noEmit` 目前红 | 任何新增 TS 代码都会淹没在 26 个既有错误中 | **必须先修 `tests/curtainPhysics.test.tsx`** |
| R-6 | 无 ESLint 配置 | 新增代码无 lint 约束；CI lint job 恒红 | 需先补 `.eslintrc`（超出本任务范围，需架构师决策） |
| R-7 | `next build` 会跑 typecheck | 若修 R-5 前引入类型错误，build 也会红（`npx next build` 输出含 "Linting and checking validity of types"） | 与 R-5 同解 |
| R-8 | 移动端 `.evidenceDock` 70dvh 限高 | 新增字段后内容变长，抽屉内部滚动体验可能变差 | 分组折叠：原文/出处 常显，来源与校验 折叠 |
| R-9 | `ThoughtCourt.module.css` 单文件 26337 bytes | 新增样式易与他处冲突 | 优先复用已有 class，新增 class 需带 `evidence` 前缀 |
| R-10 | `/demo` 不在导航（C-2） | Evidence Drawer 无法被人工验收 | 需架构师/产品决策：是否将 `/demo` 或新路由加入导航 |
| R-11 | 三圣硬编码（`LIVE_SAGES`/`SAGE_ORDER`） | PHASE 6 要求加入墨子/韩非 | 扩展数组会连带影响 `SageTribunal` 的三席位布局与 `data-sage` 断言 |

---

## 7. 证据不足 / 未核验项

| 项 | 状态 | 说明 |
|---|---|---|
| 后端是否将新增 `trust_state` / `quality_grade` 字段 | **未核验** | 属 backend 审计范围（t5）；前端当前 0 引用 |
| `next build` 是否因 CI 的 `output: export` 路径而改变 | **未核验** | 本次仅跑默认构建；`SITES_BUILD=true` 分支未测 |
| `/roundtable` 在真实后端下的渲染结果 | **未核验** | 本次未启动后端，仅静态分析 + mock 路径阅读 |
| 移动端真机 390px 表现 | **未核验** | 仅核对 CSS 媒体查询，未做真机/截图验证 |
| `runtimeAssets.test.cjs` 的完整断言 | **部分核验** | 因需运行中的站点，仅确认其在无服务时以 ECONNREFUSED 失败 |

---

## 8. 对 GATE-7 的可达性判断（如实）

GATE-7 要求：Evidence Drawer 显示 原文 / 出处 / 注疏 / 来源 / 验证 / TrustState，且 Desktop + Mobile 均可用。

| 子项 | 当前 | 判断 |
|---|---|---|
| Desktop | `.evidenceDock` 居中单列可用 | **部分可达** |
| Mobile | 已有 70dvh 底部抽屉 + 390px 安全布局 | **可达**（基础良好） |
| 原文 | 已展示 | **可达** |
| 出处 | 已展示（字符串） | **可达** |
| 注疏 | 字段存在但链路被硬编码破坏（C-6） | **需修复后可达** |
| 来源 | **无字段** | **不可达**，依赖后端 Schema（PHASE 1） |
| 验证 | 三态，语义与 BRIEF 不符 | **需扩展后可达** |
| TrustState | **完全不存在**（C-4） | **不可达**，依赖后端 Trust Layer（PHASE 5） |
| 真实渲染回归测试 | **不存在**（4.4） | **不可达**，需新建 |

**结论**：GATE-7 在当前代码基线上**不能通过**。Evidence Drawer 的前端实现**强依赖** PHASE 1（Passage Schema 的来源/版本字段）与 PHASE 5（Trust State），因此 PHASE 7 不能早于这两者完成。同时，`/demo` 路由不可达（C-2）与前端回归门禁失效（C-10/11/13/14）必须在 PHASE 7 之前解决，否则无法产出可信的验收证据。

---

## 9. 给架构师的输入要点

1. **PHASE 7 的阻塞前置**：PHASE 1（Schema 来源字段）、PHASE 5（Trust State）、以及「修复前端门禁」（C-10–C-14）。
2. **必须在 PHASE 1 就冻结的契约**：`EvidenceProvenance` 字段名须与后端 `passage` 字段一致（`book_title` / `chapter_title` / `text_type` / `commentator` / `source_provider` / `source_url` / `license` / `verification_level`），否则前端会再次发明字段。
3. **前端数据完整性缺陷应作为独立任务**：C-5/C-6/C-7/C-8/C-15 是**伪造可信信息**，属于可信承诺的直接违背，不应混在 PHASE 7 的 UI 任务中；建议在 PHASE 1 或独立修复任务中处理，并配真实断言。
4. **`/demo` 可达性需产品决策**（C-2）：主流程载体不在导航中。
5. **前端测试门禁需单独一个任务**：`npm test` 目前是空门禁；修复 `.cjs` 接入 + 占位符替换 + `tsc` + `eslint` 是 4 项独立工作。
6. **不可作为验收样本的数据**：`thoughtCourtCases.ts` 的精选案例与 `sageData.ts` / `api.ts` 的 mock 引用均为**手写、无来源、硬编码可信标记**，不得用于证明 RAG 或引用校验真实有效。

---

## 10. 复核命令清单（可复现）

```powershell
cd D:\systemDir\Desktop\悟典\frontend

# 1. vitest（23 files / 41 tests 全绿，但 20 个是占位符）
npx vitest run

# 2. 占位符计数
Select-String -Path tests/*.test.tsx,tests/*.test.ts -Pattern 'expect\(true\)\.toBe\(true\)'

# 3. 真实回归套件（4 红 / 18 绿）
Get-ChildItem tests -Filter *.test.cjs | ForEach-Object { node $_.FullName }

# 4. 类型检查（26 errors，退出码 2）
npx tsc --noEmit

# 5. CI 的 lint 命令（无配置，退出码 2）
npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0

# 6. 生产构建（成功，19 路由）
npx next build
```

```powershell
# 7. 前端 trust/质量等级 0 命中
Select-String -Path frontend/components -Include *.tsx -Pattern 'trust_state|trustState|qualityGrade|verification_level|可信等级|数据质量'
```

---

**审计完成标志**：本文件为 t6 的唯一交付物；未修改任何其他文件（`git status` 仅显示 `docs/kb-v1/` 未跟踪目录）。

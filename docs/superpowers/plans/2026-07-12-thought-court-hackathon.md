# Thought Court Hackathon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `/demo` with a polished, accessible four-act “思想审判场” that supports a curated first case, live AI debate, explicit stable-demo fallback, evidence inspection, user interventions, and a weight-responsive 思想判牒.

**Architecture:** Build an isolated `thought-court` frontend feature that reuses the existing debate API and visual assets without changing backend contracts. Pure TypeScript modules own domain types, the court state machine, curated case data, verdict weighting, and live-session orchestration; focused React components render each act, while one hook coordinates API effects and state-machine events.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript 5, Framer Motion 11, Lucide React, CSS Modules, existing Axios/fetch API client, existing Node source/logic tests.

---

## Scope And File Map

The feature is one frontend subsystem. Do not modify backend endpoints, global navigation, unrelated pages, or the current reader/UI redesign.

### Create

- `frontend/lib/thoughtCourtTypes.ts` - shared court domain contracts only.
- `frontend/lib/thoughtCourtState.ts` - deterministic court state machine and transition guards.
- `frontend/lib/thoughtCourtCases.ts` - three curated workplace cases with verified evidence and reports.
- `frontend/lib/thoughtCourtVerdict.ts` - deterministic weight normalization and verdict projection.
- `frontend/lib/thoughtCourtSession.ts` - gateway interface, existing API adapter, live/curated orchestration, and fallback policy.
- `frontend/components/thought-court/useThoughtCourt.ts` - React orchestration hook; the only feature unit allowed to run side effects.
- `frontend/components/thought-court/ThoughtCourtExperience.tsx` - feature composition and act switching.
- `frontend/components/thought-court/CourtStageChrome.tsx` - top progress, sound/motion controls, status, and persistent stage frame.
- `frontend/components/thought-court/CaseIntake.tsx` - curated case selection, free question, and open-court action.
- `frontend/components/thought-court/EvidenceDock.tsx` - evidence inspection, select/remove controls, and drag/drop enhancement.
- `frontend/components/thought-court/SageTribunal.tsx` - sage seats, streaming speeches, relations, follow-up, mutual question, and stance actions.
- `frontend/components/thought-court/VerdictScroll.tsx` - weights, verdict sections, citation integrity, safety boundary, and final seal.
- `frontend/components/thought-court/ThoughtCourt.module.css` - stage layout, 2.5D layers, cinematic motion, mobile layout, reduced-motion rules, and degraded mode.
- `frontend/tests/helpers/loadTsModule.cjs` - reusable TypeScript loader for pure-logic tests.
- `frontend/tests/thoughtCourtState.test.cjs` - state-machine behavior.
- `frontend/tests/thoughtCourtCases.test.cjs` - curated content integrity.
- `frontend/tests/thoughtCourtVerdict.test.cjs` - deterministic verdict weighting.
- `frontend/tests/thoughtCourtSession.test.cjs` - live orchestration, partial failures, and stable fallback.
- `frontend/tests/thoughtCourtWiring.test.cjs` - route, component, asset, accessibility, and mode wiring.
- `docs/hackathon/trae-evidence.md` - actual TRAE Session IDs and process-screenshot inventory produced during execution.

### Modify

- `frontend/app/demo/page.tsx` - replace the presenter runbook with `ThoughtCourtExperience`.
- `frontend/package.json` - add the five thought-court tests to the existing `test` script without changing other scripts or dependencies.
- `README.md` - update the demo route description and the 90-second judging path.
- `docs/hackathon/final-delivery-checklist.md` - add thought-court runtime, responsive, fallback, and evidence checks.

### Reuse Without Modifying

- `frontend/lib/api.ts` - use `startDebate`, `debateStream`, `interveneDebate`, `standDebate`, `mutualQuestion`, `getDebateReport`, and `analyzeThoughtCompass`.
- `frontend/lib/roundtableFlow.ts` - use `applyDebateStreamEvent`, `normalizeBackendRound`, and `normalizeDebateReport` where their contracts match.
- `frontend/lib/roundtableData.ts` - reuse `SageRoundSpeech` and `DebateClash` types.
- `frontend/lib/visualAssets.ts` - reuse sage portrait/scene paths.
- `frontend/public/agens/sages/**` and `frontend/public/agens/books/**` - reuse existing imagery.

## Implementation Rules

- Competition compliance gate: execute all contest code changes in TRAE Work or TRAE IDE and capture the real TRAE task history. Do not execute this plan in Codex for a contest submission unless the organizer confirms in writing that third-party development tools are permitted.
- Work in an isolated worktree when execution begins; do not stage or revert the user's existing dirty frontend changes.
- Follow TDD for every pure logic or behavior change: failing test, observed failure, minimal implementation, passing test.
- Keep curated content and live AI visibly distinct: `curated`, `live`, and `stable-demo` are separate modes.
- Never alter quote text, source, or sage attribution when weights change.
- Every drag action needs a click/keyboard equivalent.
- Sound starts muted. `prefers-reduced-motion` and the in-product motion toggle both disable parallax, shockwaves, and long camera moves.
- Do not add Three.js, canvas particle packages, audio packages, or a new test framework.
- Defer P1 share-image export and additional sages until every completion criterion in this plan passes; they are intentionally outside this initial implementation plan.

---

### Task 1: Establish Domain Types And Court State Machine

**Files:**
- Create: `frontend/lib/thoughtCourtTypes.ts`
- Create: `frontend/lib/thoughtCourtState.ts`
- Create: `frontend/tests/helpers/loadTsModule.cjs`
- Create: `frontend/tests/thoughtCourtState.test.cjs`

- [ ] **Step 1: Add the reusable TypeScript test loader**

Create `frontend/tests/helpers/loadTsModule.cjs` with a module cache so relative TypeScript imports resolve once:

```js
const fs = require("node:fs");
const path = require("node:path");
const ts = require("../../node_modules/typescript/lib/typescript");

const cache = new Map();

function loadTsModule(relativePath) {
  const normalized = path.normalize(relativePath).replace(/\\/g, "/");
  if (cache.has(normalized)) return cache.get(normalized).exports;

  const modulePath = path.join(__dirname, "..", "..", normalized);
  const source = fs.readFileSync(modulePath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      esModuleInterop: true,
    },
  }).outputText;
  const mod = { exports: {} };
  cache.set(normalized, mod);
  const localRequire = (request) => {
    if (!request.startsWith(".")) return require(request);
    const candidate = path.join(path.dirname(normalized), request);
    const withExtension = path.extname(candidate) ? candidate : `${candidate}.ts`;
    return loadTsModule(withExtension);
  };
  new Function("require", "module", "exports", compiled)(localRequire, mod, mod.exports);
  return mod.exports;
}

module.exports = { loadTsModule };
```

- [ ] **Step 2: Write the failing state-machine test**

Create `frontend/tests/thoughtCourtState.test.cjs`:

```js
const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const court = loadTsModule("lib/thoughtCourtState.ts");

let state = court.createCourtState();
assert.equal(state.phase, "idle");
assert.equal(state.mode, "curated");
assert.equal(state.sound, "muted");

state = court.transitionCourt(state, { type: "SELECT_CASE", caseId: "recognition" });
assert.equal(state.phase, "intake");
state = court.transitionCourt(state, { type: "SUBMIT_CASE", question: "我很努力，却总不被认可。" });
assert.equal(state.phase, "retrieving");
state = court.transitionCourt(state, {
  type: "RETRIEVAL_SUCCEEDED",
  evidenceIds: ["recognition-confucius-1"],
  citationStatus: "verified",
});
assert.equal(state.phase, "evidence");
state = court.transitionCourt(state, { type: "BEGIN_DEBATE" });
assert.equal(state.phase, "debate");
state = court.transitionCourt(state, { type: "DEBATE_SUCCEEDED" });
assert.equal(state.phase, "weighting");
state = court.transitionCourt(state, { type: "BUILD_VERDICT" });
assert.equal(state.phase, "verdict");
state = court.transitionCourt(state, { type: "COMPLETE" });
assert.equal(state.phase, "completed");

const unchanged = court.transitionCourt(court.createCourtState(), { type: "BEGIN_DEBATE" });
assert.equal(unchanged.phase, "idle");

const failed = court.transitionCourt(state, { type: "REMOTE_FAILED", message: "timeout" });
assert.equal(failed.network, "failed");
assert.equal(failed.error, "timeout");
const stable = court.transitionCourt(failed, { type: "USE_STABLE_DEMO" });
assert.equal(stable.mode, "stable-demo");
assert.equal(stable.error, null);

console.log("thoughtCourtState tests passed");
```

- [ ] **Step 3: Run the test and verify the expected failure**

Run: `node frontend/tests/thoughtCourtState.test.cjs`

Expected: FAIL with `ENOENT` for `frontend/lib/thoughtCourtState.ts`.

- [ ] **Step 4: Add exact shared contracts**

Create `frontend/lib/thoughtCourtTypes.ts` with these exported contracts:

```ts
export type CourtPhase = "idle" | "intake" | "retrieving" | "evidence" | "debate" | "weighting" | "verdict" | "completed";
export type CourtMode = "curated" | "live" | "stable-demo";
export type CourtNetwork = "idle" | "loading" | "streaming" | "failed";
export type CitationStatus = "verified" | "partial" | "unavailable";
export type CourtMotionMode = "full" | "reduced" | "degraded";
export type CourtSound = "muted" | "enabled";
export type CourtWeightKey = "self" | "relationship" | "change";

export interface CourtEvidence {
  id: string;
  sageId: string;
  original: string;
  source: string;
  interpretation: string;
  boundary: string;
  verified: boolean;
}

export interface CourtSpeech {
  sageId: string;
  position: string;
  content: string;
  evidenceIds: string[];
  status: "waiting" | "streaming" | "complete" | "failed";
}

export interface CourtClash {
  fromSageId: string;
  toSageId: string;
  type: "support" | "refute" | "reframe";
  summary: string;
}

export interface CourtWeights {
  self: number;
  relationship: number;
  change: number;
}

export interface CourtReport {
  conflict: string;
  consensus: string[];
  divergences: string[];
  actions: Record<CourtWeightKey, string[]>;
  reservation: string;
}

export interface CuratedCourtCase {
  id: string;
  label: string;
  question: string;
  conflicts: string[];
  sages: string[];
  evidence: CourtEvidence[];
  speeches: CourtSpeech[];
  clashes: CourtClash[];
  report: CourtReport;
}
```

- [ ] **Step 5: Implement the guarded state machine**

Create `frontend/lib/thoughtCourtState.ts`. Define `CourtState`, `CourtEvent`, `createCourtState()`, and `transitionCourt()` with a transition table. Invalid events must return the same state object, not throw:

```ts
import type { CitationStatus, CourtMode, CourtMotionMode, CourtNetwork, CourtPhase, CourtSound, CourtWeights } from "./thoughtCourtTypes";

export interface CourtState {
  phase: CourtPhase;
  mode: CourtMode;
  network: CourtNetwork;
  citationStatus: CitationStatus;
  motion: CourtMotionMode;
  sound: CourtSound;
  caseId: string | null;
  question: string;
  evidenceIds: string[];
  weights: CourtWeights;
  error: string | null;
}

export type CourtEvent =
  | { type: "SELECT_CASE"; caseId: string }
  | { type: "SET_LIVE_QUESTION" }
  | { type: "SUBMIT_CASE"; question: string }
  | { type: "RETRIEVAL_SUCCEEDED"; evidenceIds: string[]; citationStatus: CitationStatus }
  | { type: "BEGIN_DEBATE" }
  | { type: "DEBATE_SUCCEEDED" }
  | { type: "SET_WEIGHTS"; weights: CourtWeights }
  | { type: "BUILD_VERDICT" }
  | { type: "COMPLETE" }
  | { type: "REMOTE_LOADING" | "REMOTE_STREAMING" }
  | { type: "REMOTE_FAILED"; message: string }
  | { type: "USE_STABLE_DEMO" }
  | { type: "RETRY" }
  | { type: "SET_MOTION"; motion: CourtMotionMode }
  | { type: "SET_SOUND"; sound: CourtSound }
  | { type: "RESET" };

export const DEFAULT_COURT_WEIGHTS: CourtWeights = { self: 34, relationship: 33, change: 33 };

export function createCourtState(): CourtState {
  return {
    phase: "idle",
    mode: "curated",
    network: "idle",
    citationStatus: "unavailable",
    motion: "full",
    sound: "muted",
    caseId: null,
    question: "",
    evidenceIds: [],
    weights: DEFAULT_COURT_WEIGHTS,
    error: null,
  };
}

export function transitionCourt(state: CourtState, event: CourtEvent): CourtState {
  if (event.type === "RESET") return createCourtState();
  if (event.type === "SET_MOTION") return { ...state, motion: event.motion };
  if (event.type === "SET_SOUND") return { ...state, sound: event.sound };
  if (event.type === "REMOTE_FAILED") return { ...state, network: "failed", error: event.message };
  if (event.type === "USE_STABLE_DEMO") return { ...state, mode: "stable-demo", network: "idle", error: null };
  if (event.type === "RETRY") return { ...state, network: "loading", error: null };
  if (event.type === "REMOTE_LOADING") return { ...state, network: "loading", error: null };
  if (event.type === "REMOTE_STREAMING") return { ...state, network: "streaming", error: null };

  if (event.type === "SELECT_CASE" && (state.phase === "idle" || state.phase === "intake")) {
    return { ...state, phase: "intake", mode: "curated", caseId: event.caseId };
  }
  if (event.type === "SET_LIVE_QUESTION" && (state.phase === "idle" || state.phase === "intake")) {
    return { ...state, phase: "intake", mode: "live", caseId: null };
  }
  if (event.type === "SUBMIT_CASE" && state.phase === "intake" && event.question.trim()) {
    return { ...state, phase: "retrieving", question: event.question.trim(), network: "loading", error: null };
  }
  if (event.type === "RETRIEVAL_SUCCEEDED" && state.phase === "retrieving") {
    return { ...state, phase: "evidence", network: "idle", evidenceIds: event.evidenceIds, citationStatus: event.citationStatus };
  }
  if (event.type === "BEGIN_DEBATE" && state.phase === "evidence") return { ...state, phase: "debate", network: "streaming" };
  if (event.type === "DEBATE_SUCCEEDED" && state.phase === "debate") return { ...state, phase: "weighting", network: "idle" };
  if (event.type === "SET_WEIGHTS" && (state.phase === "weighting" || state.phase === "verdict")) return { ...state, weights: event.weights };
  if (event.type === "BUILD_VERDICT" && state.phase === "weighting") return { ...state, phase: "verdict" };
  if (event.type === "COMPLETE" && state.phase === "verdict") return { ...state, phase: "completed" };
  return state;
}
```

- [ ] **Step 6: Run the state test**

Run: `node frontend/tests/thoughtCourtState.test.cjs`

Expected: `thoughtCourtState tests passed`.

- [ ] **Step 7: Commit Task 1**

```powershell
git add frontend/lib/thoughtCourtTypes.ts frontend/lib/thoughtCourtState.ts frontend/tests/helpers/loadTsModule.cjs frontend/tests/thoughtCourtState.test.cjs
git commit -m "feat: add thought court state model"
```

---

### Task 2: Add Three Verified Curated Cases

**Files:**
- Create: `frontend/lib/thoughtCourtCases.ts`
- Create: `frontend/tests/thoughtCourtCases.test.cjs`

- [ ] **Step 1: Write the failing curated-content integrity test**

Create `frontend/tests/thoughtCourtCases.test.cjs`:

```js
const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const cases = loadTsModule("lib/thoughtCourtCases.ts");

assert.equal(cases.CURATED_COURT_CASES.length, 3);
for (const item of cases.CURATED_COURT_CASES) {
  assert.equal(item.sages.length, 3);
  assert.ok(item.conflicts.length >= 3);
  assert.ok(item.evidence.length >= 3);
  assert.equal(item.speeches.length, 3);
  assert.ok(item.clashes.length >= 2);
  assert.ok(item.report.actions.self.length > 0);
  assert.ok(item.report.actions.relationship.length > 0);
  assert.ok(item.report.actions.change.length > 0);
  for (const evidence of item.evidence) {
    assert.ok(evidence.original.trim());
    assert.ok(evidence.source.startsWith("《"));
    assert.ok(evidence.interpretation.trim());
    assert.ok(evidence.boundary.trim());
    assert.equal(evidence.verified, true);
  }
  for (const speech of item.speeches) {
    assert.ok(speech.evidenceIds.every((id) => item.evidence.some((e) => e.id === id)));
  }
}
assert.equal(cases.getCuratedCourtCase("recognition").question, "我很努力，却总不被领导认可，怎么办？");
assert.equal(cases.getCuratedCourtCase("missing"), null);

console.log("thoughtCourtCases tests passed");
```

- [ ] **Step 2: Run the test and verify the expected failure**

Run: `node frontend/tests/thoughtCourtCases.test.cjs`

Expected: FAIL with `ENOENT` for `frontend/lib/thoughtCourtCases.ts`.

- [ ] **Step 3: Implement the curated-case module**

Create `frontend/lib/thoughtCourtCases.ts`. Use exactly these case IDs, questions, participants, and evidence anchors; complete every `interpretation`, `boundary`, speech, clash, and report field with concise reviewed Chinese copy:

```ts
import type { CuratedCourtCase } from "./thoughtCourtTypes";

const sages = ["confucius", "mencius", "laozi"];

export const CURATED_COURT_CASES: CuratedCourtCase[] = [
  {
    id: "recognition",
    label: "职场认可",
    question: "我很努力，却总不被领导认可，怎么办？",
    conflicts: ["外界认可", "自我价值", "行动选择"],
    sages,
    evidence: [
      { id: "recognition-confucius-1", sageId: "confucius", original: "人不知而不愠，不亦君子乎？", source: "《论语·学而》", interpretation: "先把自我价值与他人一时的认可拆开，再决定如何沟通。", boundary: "这不等于默忍不公平评价或放弃争取合理回报。", verified: true },
      { id: "recognition-mencius-1", sageId: "mencius", original: "行有不得者，皆反求诸己。", source: "《孟子·离娄上》", interpretation: "先检查成果表达、期望对齐和能力缺口，但不把所有责任都归给自己。", boundary: "反求诸己是获得行动权，不是为系统性不公开脱。", verified: true },
      { id: "recognition-laozi-1", sageId: "laozi", original: "知人者智，自知者明。", source: "《道德经·第三十三章》", interpretation: "分清你真正需要的是公平回报、成长机会，还是单纯被看见。", boundary: "自知不意味着退出竞争或放弃为自己发声。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "稳住内在尺度，再正名沟通", content: "不必把一次不被看见等同于价值不存在。先把成果、责任和评价标准说清。", evidenceIds: ["recognition-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "反求诸己，但不放弃尊严", content: "查看自己能改变的部分，同时为合理的评价与边界发声。", evidenceIds: ["recognition-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "辨认执念，保留转身的空间", content: "看清你要争取的究竟是什么。如果环境长期无法给出公平回报，改变路径也是行动。", evidenceIds: ["recognition-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都主张先恢复行动权，但孟子更强调尊严与应得回报。" },
      { fromSageId: "laozi", toSageId: "confucius", type: "reframe", summary: "老子不只谈如何被认可，而是追问是否仍值得留在当前评价体系。" },
    ],
    report: {
      conflict: "你的努力与组织的评价机制脱节，同时你把部分自我价值交给了外部认可。",
      consensus: ["先把情绪与事实拆开。", "用可验证的成果和明确对话恢复行动权。"],
      divergences: ["应继续修身与沟通，还是尽快改变所在环境。"],
      actions: {
        self: ["写下三项不依赖他人表态也能确认的成果。"],
        relationship: ["预约一次 20 分钟对话，请领导明确评价标准和差距。"],
        change: ["设定一个月观察期；如果标准仍模糊或成果持续被忽视，开始准备内部转岗或外部机会。"],
      },
      reservation: "悟典无法代替你判断当前组织是否值得继续投入，这需要你结合收入、成长、安全感和现实机会判断。",
    },
  },
  {
    id: "departure",
    label: "职业去留",
    question: "稳定但不喜欢的工作，要不要离开？",
    conflicts: ["现实安全", "个人志向", "改变时机"],
    sages,
    evidence: [
      { id: "departure-confucius-1", sageId: "confucius", original: "三军可夺帅也，匹夫不可夺志也。", source: "《论语·子罕》", interpretation: "稳定不应以长期放弃核心志向为代价，但志向也需要转化为可行路径。", boundary: "保守现职不等于怯懦，在资源不足时先做准备同样是守志。", verified: true },
      { id: "departure-mencius-1", sageId: "mencius", original: "穷则独善其身，达则兼善天下。", source: "《孟子·尽心上》", interpretation: "职业阶段不同，行动目标也不同；可以先积累能力和选择权，再追求更大影响。", boundary: "这不是对无限期忍耐的赞美，也不应成为拖延改变的借口。", verified: true },
      { id: "departure-laozi-1", sageId: "laozi", original: "去甚，去奢，去泰。", source: "《道德经·第二十九章》", interpretation: "先剔除对理想工作的极端想象，分清当前工作是核心价值冲突，还是可调整的阶段性不适。", boundary: "减少执念不是压低正当需求，也不是否定改变的必要性。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "先明其志，再定去留", content: "把你不愿牺牲的价值写清，再检查当前工作是否仍能服务这个志向。", evidenceIds: ["departure-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "先积累选择权，不必用一次跳跃证明勇气", content: "判断你此刻更缺收入安全、可转移能力，还是成长空间，然后安排有时限的准备期。", evidenceIds: ["departure-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "删去极端想象，看见真正冲突", content: "不要在“永远忍耐”和“立刻裸辞”之间二选一，先做可逆的小实验。", evidenceIds: ["departure-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都不主张无限期牺牲志向，孟子更强调先积累现实选择权。" },
      { fromSageId: "laozi", toSageId: "confucius", type: "reframe", summary: "老子将去留的价值判断改写为一组可逆的现实实验。" },
    ],
    report: {
      conflict: "你在收入和可预期性中获得安全，但长期失去兴趣、成长或价值认同。",
      consensus: ["不用冲动离开证明勇气。", "不为模糊的稳定无限期牺牲志向。"],
      divergences: ["先改造当前工作，还是尽快为离开做系统准备。"],
      actions: {
        self: ["写下你对下一份工作不可妥协的三项要求。"],
        relationship: ["与上级讨论一个可在六周内验证的职责或项目调整。"],
        change: ["计算可承受的空窗期，并每周完成一个外部机会的小步验证。"],
      },
      reservation: "悟典无法知道你的负债、家庭责任、健康状况和行业机会，这些现实条件必须进入最终判断。",
    },
  },
  {
    id: "credit",
    label: "功劳归属",
    question: "同事抢了我的功劳，我该争还是忍？",
    conflicts: ["事实正名", "关系成本", "长期规则"],
    sages,
    evidence: [
      { id: "credit-confucius-1", sageId: "confucius", original: "名不正，则言不顺。", source: "《论语·子路》", interpretation: "成果、责任和作者关系不清，后续协作和评价就会继续失真。", boundary: "正名应依据事实和记录，不是在公开场合进行人身攻击。", verified: true },
      { id: "credit-mencius-1", sageId: "mencius", original: "自反而缩，虽千万人，吾往矣。", source: "《孟子·公孙丑上》", interpretation: "先核对自己的贡献是否站得住，如果证据充分，就不必因为对方强势而放弃说明。", boundary: "勇于发声不等于不计后果；方式、场合和证据同样重要。", verified: true },
      { id: "credit-laozi-1", sageId: "laozi", original: "夫唯不争，故天下莫能与之争。", source: "《道德经·第二十二章》", interpretation: "不与人陷入情绪争胜，而是用交付记录和流程让事实自己发声。", boundary: "不争不是沉默接受功劳被占，也不是退出正当权益的协商。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "先正名，再论关系", content: "用邮件、文档和交付记录还原事实，让贡献归属可被共同确认。", evidenceIds: ["credit-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "有证则言，不以强弱代替是非", content: "先确认自己的贡献边界，再在可控的场合坚定陈述事实和诉求。", evidenceIds: ["credit-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "不争意气，争取规则", content: "不要把胜负绑在一次当面冲突上，改用透明的协作和署名机制防止重演。", evidenceIds: ["credit-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都主张基于事实正名，孟子更强调在强势关系中也不放弃发声。" },
      { fromSageId: "laozi", toSageId: "mencius", type: "reframe", summary: "老子把当面争胜改写为让记录和规则持续起作用。" },
    ],
    report: {
      conflict: "你既需要恢复事实和回报的对应关系，又担心直接发声损害合作关系。",
      consensus: ["不用情绪冲突代替事实澄清。", "通过记录和规则减少下次归属不清。"],
      divergences: ["应当尽快直接发声，还是先建立不需要正面冲突的证据与流程。"],
      actions: {
        self: ["列出你独立完成、共同完成和对方完成的事实清单。"],
        relationship: ["先与同事做一次私下对齐；仍无法澄清时，带记录向负责人说明。"],
        change: ["为后续项目建立任务负责人、交付记录和对外汇报署名规则。"],
      },
      reservation: "悟典无法判断你手中证据的完整度、组织的权力结构和发声风险，需要你选择合适的对象、场合和节奏。",
    },
  },
];

export function getCuratedCourtCase(id: string): CuratedCourtCase | null {
  return CURATED_COURT_CASES.find((item) => item.id === id) ?? null;
}
```

Copy the three objects exactly, then have a human reviewer verify every quote and source against the repository's classic corpus before marking the case content complete.

- [ ] **Step 4: Run the curated-content test**

Run: `node frontend/tests/thoughtCourtCases.test.cjs`

Expected: `thoughtCourtCases tests passed`.

- [ ] **Step 5: Commit Task 2**

```powershell
git add frontend/lib/thoughtCourtCases.ts frontend/tests/thoughtCourtCases.test.cjs
git commit -m "feat: add curated thought court cases"
```

---

### Task 3: Implement Deterministic Verdict Weighting

**Files:**
- Create: `frontend/lib/thoughtCourtVerdict.ts`
- Create: `frontend/tests/thoughtCourtVerdict.test.cjs`

- [ ] **Step 1: Write the failing verdict test**

```js
const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const verdict = loadTsModule("lib/thoughtCourtVerdict.ts");
const cases = loadTsModule("lib/thoughtCourtCases.ts");

assert.deepEqual(verdict.normalizeWeights({ self: 0, relationship: 0, change: 0 }), { self: 34, relationship: 33, change: 33 });
assert.deepEqual(verdict.normalizeWeights({ self: 80, relationship: 10, change: 10 }), { self: 80, relationship: 10, change: 10 });

const item = cases.getCuratedCourtCase("recognition");
const selfFirst = verdict.buildVerdict(item.report, { self: 80, relationship: 10, change: 10 });
assert.equal(selfFirst.dominantKey, "self");
assert.equal(selfFirst.actions[0], item.report.actions.self[0]);
const changeFirst = verdict.buildVerdict(item.report, { self: 10, relationship: 10, change: 80 });
assert.equal(changeFirst.dominantKey, "change");
assert.equal(changeFirst.actions[0], item.report.actions.change[0]);
assert.deepEqual(item.evidence.map((e) => e.original), cases.getCuratedCourtCase("recognition").evidence.map((e) => e.original));

console.log("thoughtCourtVerdict tests passed");
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtVerdict.test.cjs`

Expected: FAIL with `ENOENT` for `frontend/lib/thoughtCourtVerdict.ts`.

- [ ] **Step 3: Implement the verdict projection**

```ts
import type { CourtReport, CourtWeightKey, CourtWeights } from "./thoughtCourtTypes";

const keys: CourtWeightKey[] = ["self", "relationship", "change"];

export interface ThoughtVerdict {
  conflict: string;
  consensus: string[];
  divergences: string[];
  actions: string[];
  reservation: string;
  dominantKey: CourtWeightKey;
  weights: CourtWeights;
}

export function normalizeWeights(input: CourtWeights): CourtWeights {
  const safe = {
    self: Math.max(0, input.self),
    relationship: Math.max(0, input.relationship),
    change: Math.max(0, input.change),
  };
  const total = safe.self + safe.relationship + safe.change;
  if (total === 0) return { self: 34, relationship: 33, change: 33 };
  const self = Math.round((safe.self / total) * 100);
  const relationship = Math.round((safe.relationship / total) * 100);
  return { self, relationship, change: 100 - self - relationship };
}

export function buildVerdict(report: CourtReport, input: CourtWeights): ThoughtVerdict {
  const weights = normalizeWeights(input);
  const ranked = [...keys].sort((a, b) => weights[b] - weights[a]);
  return {
    conflict: report.conflict,
    consensus: [...report.consensus],
    divergences: [...report.divergences],
    actions: ranked.flatMap((key) => report.actions[key]),
    reservation: report.reservation,
    dominantKey: ranked[0],
    weights,
  };
}
```

- [ ] **Step 4: Run the verdict test**

Run: `node frontend/tests/thoughtCourtVerdict.test.cjs`

Expected: `thoughtCourtVerdict tests passed`.

- [ ] **Step 5: Commit Task 3**

```powershell
git add frontend/lib/thoughtCourtVerdict.ts frontend/tests/thoughtCourtVerdict.test.cjs
git commit -m "feat: add weighted thought verdicts"
```

---

### Task 4: Build The Live Session Gateway And Fallback Policy

**Files:**
- Create: `frontend/lib/thoughtCourtSession.ts`
- Create: `frontend/tests/thoughtCourtSession.test.cjs`

- [ ] **Step 1: Write the failing orchestration test with a fake gateway**

The test must verify that first-round events are buffered for evidence, second-round events stream into debate, one failed sage remains local to that seat, and a total failure offers stable fallback:

```js
const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const session = loadTsModule("lib/thoughtCourtSession.ts");

const events = [];
const gateway = {
  async startDebate(topic, sages) { return { sessionId: "s-1", topic, participants: sages }; },
  async streamRound(_id, onEvent) {
    onEvent({ type: "sage_end", sage_key: "confucius", speech: { sage_key: "confucius", content: "孔子曰", citations: [{ source: "《论语·学而》", original: "人不知而不愠", verifiable: true }] } });
    onEvent({ type: "sage_error", sage_key: "mencius", message: "timeout" });
    onEvent({ type: "round_done", round: 1 });
  },
  async getReport() { return { report: { topic: "x", consensus: ["c"], divergences: ["d"], recommendations: [], summary: "s", participating_sages: ["孔子"] } }; },
};

const prepared = await session.prepareLiveCourt("x", ["confucius", "mencius", "laozi"], gateway, (event) => events.push(event));
assert.equal(prepared.sessionId, "s-1");
assert.equal(prepared.evidence.length, 1);
assert.equal(prepared.citationStatus, "partial");
assert.equal(prepared.speeches.find((s) => s.sageId === "mencius").status, "failed");
assert.ok(events.some((event) => event.type === "REMOTE_STREAMING"));

const broken = { ...gateway, async startDebate() { throw new Error("offline"); } };
await assert.rejects(() => session.prepareLiveCourt("x", ["confucius"], broken, () => {}), /offline/);

console.log("thoughtCourtSession tests passed");
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtSession.test.cjs`

Expected: FAIL with `ENOENT` for `frontend/lib/thoughtCourtSession.ts`.

- [ ] **Step 3: Implement the gateway and event normalization**

Create `frontend/lib/thoughtCourtSession.ts` with:

```ts
import type { CitationStatus, CourtEvidence, CourtSpeech } from "./thoughtCourtTypes";

export interface CourtGateway {
  startDebate(topic: string, sages: string[]): Promise<{ sessionId: string; topic: string; participants: string[] }>;
  streamRound(sessionId: string, onEvent: (event: any) => void): Promise<void>;
  intervene(sessionId: string, content: string, targetSage?: string): Promise<any>;
  stand(sessionId: string, stance: string, targetSage?: string): Promise<any>;
  mutualQuestion(sessionId: string, fromSage: string, toSage: string): Promise<any>;
  getReport(sessionId: string): Promise<any>;
}

export function createApiCourtGateway(api: any): CourtGateway {
  return {
    startDebate: (topic, sages) => api.startDebate(topic, sages),
    streamRound: (sessionId, onEvent) => api.debateStream(sessionId, "next-round", undefined, onEvent),
    intervene: (sessionId, content, targetSage) => api.interveneDebate(sessionId, content, targetSage),
    stand: (sessionId, stance, targetSage) => api.standDebate(sessionId, stance, targetSage),
    mutualQuestion: (sessionId, fromSage, toSage) => api.mutualQuestion(sessionId, fromSage, toSage),
    getReport: (sessionId) => api.getDebateReport(sessionId),
  };
}

function normalizeEvidence(sageId: string, citation: any, index: number): CourtEvidence | null {
  const original = citation.original || citation.text || "";
  const source = citation.source || "";
  if (!original || !source) return null;
  return {
    id: `live-${sageId}-${index}`,
    sageId,
    original,
    source,
    interpretation: citation.commentary || "该原文为当前观点提供思想依据。",
    boundary: "请结合现实情境判断，勿将单句经典当作强制命令。",
    verified: citation.verifiable !== false,
  };
}

export async function prepareLiveCourt(topic: string, sages: string[], gateway: CourtGateway, emit: (event: any) => void) {
  emit({ type: "REMOTE_LOADING" });
  const started = await gateway.startDebate(topic, sages);
  emit({ type: "REMOTE_STREAMING" });
  const evidence: CourtEvidence[] = [];
  const speeches: CourtSpeech[] = sages.map((sageId) => ({ sageId, position: "", content: "", evidenceIds: [], status: "waiting" }));
  await gateway.streamRound(started.sessionId, (event) => {
    if (event.type === "sage_end") {
      const sageId = event.sage_key;
      const target = speeches.find((speech) => speech.sageId === sageId);
      const normalized = (event.speech?.citations || [])
        .map((citation: any, index: number) => normalizeEvidence(sageId, citation, index))
        .filter((item: CourtEvidence | null): item is CourtEvidence => item !== null);
      evidence.push(...normalized);
      if (target) {
        target.content = event.speech?.content || "";
        target.evidenceIds = normalized.map((item) => item.id);
        target.status = "complete";
      }
    }
    if (event.type === "sage_error") {
      const target = speeches.find((speech) => speech.sageId === event.sage_key);
      if (target) target.status = "failed";
    }
    emit(event);
  });
  const verifiedCount = evidence.filter((item) => item.verified).length;
  const citationStatus: CitationStatus = verifiedCount === 0 ? "unavailable" : verifiedCount === evidence.length && speeches.every((item) => item.status === "complete") ? "verified" : "partial";
  return { sessionId: started.sessionId, topic: started.topic, participants: started.participants, evidence, speeches, citationStatus };
}
```

- [ ] **Step 4: Add `runSecondRound`, `runIntervention`, `runStand`, `runMutualQuestion`, and `loadReport`**

Add these functions below `prepareLiveCourt`. They deliberately do not catch errors; the hook owns recovery and preserves the current stage:

```ts
import { normalizeBackendRound, normalizeDebateReport } from "./roundtableFlow";

export async function runSecondRound(sessionId: string, gateway: CourtGateway, emit: (event: any) => void) {
  emit({ type: "REMOTE_STREAMING" });
  const events: any[] = [];
  await gateway.streamRound(sessionId, (event) => {
    events.push(event);
    emit(event);
  });
  return events;
}

export async function runIntervention(sessionId: string, content: string, targetSage: string | undefined, gateway: CourtGateway) {
  const result = await gateway.intervene(sessionId, content, targetSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function runStand(sessionId: string, stance: string, targetSage: string | undefined, gateway: CourtGateway) {
  const result = await gateway.stand(sessionId, stance, targetSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function runMutualQuestion(sessionId: string, fromSage: string, toSage: string, gateway: CourtGateway) {
  const result = await gateway.mutualQuestion(sessionId, fromSage, toSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function loadReport(sessionId: string, gateway: CourtGateway) {
  const result = await gateway.getReport(sessionId);
  return normalizeDebateReport(result?.report ?? result);
}
```

- [ ] **Step 5: Run the session test**

Run: `node frontend/tests/thoughtCourtSession.test.cjs`

Expected: `thoughtCourtSession tests passed`.

- [ ] **Step 6: Commit Task 4**

```powershell
git add frontend/lib/thoughtCourtSession.ts frontend/tests/thoughtCourtSession.test.cjs
git commit -m "feat: orchestrate live thought court sessions"
```

---

### Task 5: Wire The `/demo` Route To An Isolated Stage Shell

**Files:**
- Create: `frontend/components/thought-court/useThoughtCourt.ts`
- Create: `frontend/components/thought-court/ThoughtCourtExperience.tsx`
- Create: `frontend/components/thought-court/CourtStageChrome.tsx`
- Create: `frontend/components/thought-court/ThoughtCourt.module.css`
- Create: `frontend/tests/thoughtCourtWiring.test.cjs`
- Modify: `frontend/app/demo/page.tsx`

- [ ] **Step 1: Write the failing route and shell wiring test**

Create `frontend/tests/thoughtCourtWiring.test.cjs`:

```js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const read = (file) => fs.readFileSync(path.join(__dirname, "..", file), "utf8");

const page = read("app/demo/page.tsx");
assert.match(page, /ThoughtCourtExperience/);
assert.doesNotMatch(page, /3 分钟评审路线/);

const experience = read("components/thought-court/ThoughtCourtExperience.tsx");
assert.ok(experience.includes("CourtStageChrome"));
assert.ok(experience.includes("useThoughtCourt"));

const chrome = read("components/thought-court/CourtStageChrome.tsx");
assert.ok(chrome.includes("问"));
assert.ok(chrome.includes("证"));
assert.ok(chrome.includes("辩"));
assert.ok(chrome.includes("判"));
assert.match(chrome, /aria-label=.*声音/);
assert.match(chrome, /aria-label=.*动效/);

const css = read("components/thought-court/ThoughtCourt.module.css");
assert.ok(css.includes("@media (max-width: 767px)"));
assert.ok(css.includes("prefers-reduced-motion"));
assert.ok(css.includes("data-motion=\"degraded\""));

console.log("thoughtCourtWiring tests passed");
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL because `ThoughtCourtExperience` is not wired.

- [ ] **Step 3: Replace `/demo` with a thin route**

Replace `frontend/app/demo/page.tsx` with:

```tsx
import ThoughtCourtExperience from "@/components/thought-court/ThoughtCourtExperience";

export default function DemoPage() {
  return <ThoughtCourtExperience />;
}
```

- [ ] **Step 4: Add the first complete orchestration hook slice**

Create `useThoughtCourt.ts` with the reducer and stage-level settings. Later tasks extend this exact hook with content and remote actions; child visual components never import `api` directly:

```ts
"use client";

import { useReducer } from "react";
import { createCourtState, transitionCourt } from "@/lib/thoughtCourtState";
import type { CourtMotionMode, CourtSound } from "@/lib/thoughtCourtTypes";

export function useThoughtCourt() {
  const [state, dispatch] = useReducer(transitionCourt, undefined, createCourtState);
  return {
    state,
    setMotion: (motion: CourtMotionMode) => dispatch({ type: "SET_MOTION", motion }),
    setSound: (sound: CourtSound) => dispatch({ type: "SET_SOUND", sound }),
    reset: () => dispatch({ type: "RESET" }),
  };
}
```

- [ ] **Step 5: Add `CourtStageChrome` and feature composition**

`CourtStageChrome` renders a four-step ordered progress indicator, explicit mode badge, remote status, sound toggle, motion toggle, reset icon button, and a stable `<main>` stage slot. Use Lucide `Volume2`, `VolumeX`, `Waves`, `Accessibility`, and `RotateCcw`; all icon-only controls need tooltips and `aria-label`.

`ThoughtCourtExperience` keeps the central stage mounted and renders an accessible phase-status panel with the current act name. Tasks 6-9 replace the phase body one act at a time without changing the persistent stage shell.

- [ ] **Step 6: Add the CSS foundation**

Implement these stable tokens in the CSS module:

```css
.court {
  --court-ink: #151714;
  --court-paper: #f2eee4;
  --court-cinnabar: #a43d32;
  --court-jade: #4f7669;
  --court-stone: #8e928c;
  min-height: 100dvh;
  color: var(--court-paper);
  background: var(--court-ink);
}

.stage {
  position: relative;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  min-height: calc(100dvh - 64px);
  overflow: clip;
}

@media (max-width: 767px) {
  .stage { min-height: calc(100dvh - 56px); }
}

@media (prefers-reduced-motion: reduce) {
  .court *, .court *::before, .court *::after {
    scroll-behavior: auto !important;
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 1ms !important;
  }
}

.court[data-motion="degraded"] .ambient,
.court[data-motion="degraded"] .parallaxLayer { display: none; }
```

- [ ] **Step 7: Run the wiring test and production type check**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: the route checks pass; component-name checks may remain failing only until empty named components are created in the next step.

Run: `npm --prefix frontend run build`

Expected: PASS with no TypeScript error.

- [ ] **Step 8: Commit Task 5**

```powershell
git add frontend/app/demo/page.tsx frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: add thought court stage shell"
```

---

### Task 6: Implement Case Intake And Evidence Selection

**Files:**
- Create: `frontend/components/thought-court/CaseIntake.tsx`
- Create: `frontend/components/thought-court/EvidenceDock.tsx`
- Modify: `frontend/components/thought-court/ThoughtCourtExperience.tsx`
- Modify: `frontend/components/thought-court/useThoughtCourt.ts`
- Modify: `frontend/components/thought-court/ThoughtCourt.module.css`
- Modify: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Extend the wiring test for intake and evidence contracts**

Add assertions that `CaseIntake.tsx` contains the three exact questions, a labeled free-question textarea, and `击鼓开审`; assert that `EvidenceDock.tsx` contains `aria-expanded`, `加入本案`, `已核验`, `依据不完整`, and `未找到足够可靠的经典依据`.

- [ ] **Step 2: Run the wiring test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL on the new intake/evidence assertions.

- [ ] **Step 3: Implement `CaseIntake`**

Render one primary curated case, two compact alternatives, and one free-question field. Curated items are buttons, not decorative cards. The primary action remains a stable 52px-high button with a `Gavel` icon. Disable submission for blank free questions and while `state.network` is `loading` or `streaming`.

Use these props:

```ts
interface CaseIntakeProps {
  cases: CuratedCourtCase[];
  selectedCaseId: string | null;
  mode: CourtMode;
  disabled: boolean;
  onSelectCase(id: string): void;
  onChooseLive(): void;
  onOpenCourt(question: string): void;
}
```

- [ ] **Step 4: Implement `EvidenceDock` with equivalent interaction paths**

Evidence cards support pointer drag into the case focus zone and a visible `加入本案`/`移出本案` button. Clicking the citation header expands source, interpretation, and boundary. Set `draggable` only in full-motion desktop mode; keyboard/click controls always remain available.

Use these props:

```ts
interface EvidenceDockProps {
  evidence: CourtEvidence[];
  selectedIds: string[];
  citationStatus: CitationStatus;
  motion: CourtMotionMode;
  onToggleEvidence(id: string): void;
  onBeginDebate(): void;
}
```

- [ ] **Step 5: Connect curated and live preparation in the hook**

For curated cases, dispatch `SUBMIT_CASE`, stage the local evidence, then dispatch `RETRIEVAL_SUCCEEDED` after one animation frame. For live questions, call `prepareLiveCourt`; keep its first-round speeches buffered until `beginDebate`. On error, dispatch `REMOTE_FAILED` without leaving `retrieving`.

- [ ] **Step 6: Run logic, wiring, and build checks**

Run:

```powershell
node frontend/tests/thoughtCourtState.test.cjs
node frontend/tests/thoughtCourtCases.test.cjs
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend run build
```

Expected: all commands PASS.

- [ ] **Step 7: Commit Task 6**

```powershell
git add frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: add thought court intake and evidence"
```

---

### Task 7: Implement The Interactive Sage Tribunal

**Files:**
- Create: `frontend/components/thought-court/SageTribunal.tsx`
- Modify: `frontend/components/thought-court/ThoughtCourtExperience.tsx`
- Modify: `frontend/components/thought-court/useThoughtCourt.ts`
- Modify: `frontend/components/thought-court/ThoughtCourt.module.css`
- Modify: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Add failing tribunal wiring assertions**

Require `SageTribunal.tsx` to import `sageVisuals`, render three stable seat regions, show `追问`, `请其互问`, and `我更认同`, expose `aria-live="polite"`, and display `暂未应答` for failed speeches.

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL on tribunal assertions.

- [ ] **Step 3: Implement stable sage seats and streamed content**

Use `sageVisuals[sageId].portraitImage` or `.sceneImage` for each seat. Keep each speech body in a fixed-height internal scroll region. Only the active sage receives stage lighting; inactive seats remain legible. Failed seats retain their position and offer a retry action instead of collapsing.

Use this contract:

```ts
interface SageTribunalProps {
  speeches: CourtSpeech[];
  clashes: CourtClash[];
  activeSageId: string | null;
  busy: boolean;
  onFollowUp(content: string, targetSageId: string): Promise<void>;
  onMutualQuestion(fromSageId: string, toSageId: string): Promise<void>;
  onChooseStance(stance: string, targetSageId: string): Promise<void>;
  onBuildVerdict(): void;
}
```

- [ ] **Step 4: Connect curated and live debate paths**

For curated cases, reveal the buffered three speeches in sage order with a reduced-motion-safe timer and then dispatch `DEBATE_SUCCEEDED`. For live mode, reveal buffered first-round speeches immediately, call `runSecondRound`, apply events with the existing roundtable normalizers, then load the report. User actions call the gateway, refresh the report, and keep an action-local error message if they fail.

- [ ] **Step 5: Implement local-first feedback**

On follow-up, mutual question, or stance action, immediately set the selected control to busy and announce the action in the stage status. Do not disable unrelated citation inspection. Restore the control on success or failure, and keep all prior speeches visible.

- [ ] **Step 6: Run targeted tests and build**

Run:

```powershell
node frontend/tests/thoughtCourtSession.test.cjs
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend run build
```

Expected: all commands PASS.

- [ ] **Step 7: Commit Task 7**

```powershell
git add frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: add interactive sage tribunal"
```

---

### Task 8: Implement The Weight-Responsive Thought Verdict

**Files:**
- Create: `frontend/components/thought-court/VerdictScroll.tsx`
- Modify: `frontend/components/thought-court/ThoughtCourtExperience.tsx`
- Modify: `frontend/components/thought-court/useThoughtCourt.ts`
- Modify: `frontend/components/thought-court/ThoughtCourt.module.css`
- Modify: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Add failing verdict wiring assertions**

Require `VerdictScroll.tsx` to render `核心矛盾`, `他们的共识`, `根本分歧`, `今日行动`, `保留问题`, three labeled range inputs, `落判`, `重新调权`, `新开一案`, and the fixed safety boundary.

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL on verdict assertions.

- [ ] **Step 3: Implement verdict rendering and controls**

Use `buildVerdict(report, weights)` inside `useMemo`. Render range controls for `坚持自我`, `改善关系`, and `主动改变`; display their normalized percentages. Weight changes reorder actions only. Evidence appears in a separate source list keyed by immutable evidence IDs.

Use this contract:

```ts
interface VerdictScrollProps {
  report: CourtReport;
  evidence: CourtEvidence[];
  weights: CourtWeights;
  citationStatus: CitationStatus;
  completed: boolean;
  onSetWeights(weights: CourtWeights): void;
  onComplete(): void;
  onReset(): void;
}
```

- [ ] **Step 4: Implement the seal climax without blocking controls**

On `onComplete`, animate a dedicated seal layer for at most 900ms in full motion. Keep `重新调权` and `新开一案` focusable during and after the animation. In reduced motion, render the seal immediately with no scale or blur transition.

- [ ] **Step 5: Run verdict, wiring, and build checks**

Run:

```powershell
node frontend/tests/thoughtCourtVerdict.test.cjs
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend run build
```

Expected: all commands PASS.

- [ ] **Step 6: Commit Task 8**

```powershell
git add frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: add interactive thought verdict"
```

---

### Task 9: Add Cinematic 2.5D Motion, Sound, And Performance Degradation

**Files:**
- Modify: `frontend/components/thought-court/CourtStageChrome.tsx`
- Modify: `frontend/components/thought-court/CaseIntake.tsx`
- Modify: `frontend/components/thought-court/EvidenceDock.tsx`
- Modify: `frontend/components/thought-court/SageTribunal.tsx`
- Modify: `frontend/components/thought-court/VerdictScroll.tsx`
- Modify: `frontend/components/thought-court/ThoughtCourt.module.css`
- Modify: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Add failing motion and asset assertions**

Assert that the feature references `motion`, `AnimatePresence`, `sageVisuals`, scene/portrait imagery, the four motion class names `openingShot`, `evidenceCloseup`, `clashShockwave`, `verdictSeal`, and that sound playback is gated behind `state.sound === "enabled"`.

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL on missing cinematic wiring.

- [ ] **Step 3: Implement motion variants with one visual purpose each**

- Opening: 2-3 second skippable establishing shot; first interaction cancels it.
- Evidence: camera-like scale on the evidence region only; the reading text remains still.
- Debate: active-seat depth and light; one short shockwave per newly detected clash.
- Verdict: stage tone shifts from ink to paper; one seal impact.

Do not animate layout height, main controls, or streaming text containers.

- [ ] **Step 4: Add optional audio through native `Audio`**

Store four short, locally licensed audio files under `frontend/public/sounds/thought-court/` only if suitable files are already available or can be created within the project. If no suitable assets are available, keep the sound toggle disabled with tooltip `声音素材未加载`; do not fetch remote audio at runtime. Playback must occur only after a user gesture and only when sound is enabled.

- [ ] **Step 5: Implement runtime degradation**

Use a small requestAnimationFrame sampler after the first user gesture. If average frame time exceeds 28ms for 30 samples, set motion to `degraded`. Stop sampling immediately after the decision. Never collect or transmit timing data.

- [ ] **Step 6: Run wiring and build checks**

Run:

```powershell
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 7: Commit Task 9**

```powershell
git add frontend/components/thought-court frontend/public/sounds/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: add cinematic thought court motion"
```

If no sound assets are added, omit `frontend/public/sounds/thought-court` from `git add`.

---

### Task 10: Complete Mobile, Accessibility, And Failure Recovery

**Files:**
- Modify: `frontend/components/thought-court/ThoughtCourtExperience.tsx`
- Modify: `frontend/components/thought-court/CourtStageChrome.tsx`
- Modify: `frontend/components/thought-court/CaseIntake.tsx`
- Modify: `frontend/components/thought-court/EvidenceDock.tsx`
- Modify: `frontend/components/thought-court/SageTribunal.tsx`
- Modify: `frontend/components/thought-court/VerdictScroll.tsx`
- Modify: `frontend/components/thought-court/ThoughtCourt.module.css`
- Modify: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Add failing accessibility and recovery assertions**

Require a skip link, visible focus styles, `aria-live` status, 44px minimum controls, `重试`, `切换演示稳定层`, the exact stable-demo label, and no-login copy. Assert that the CSS contains a 390px-safe mobile layout with bottom action safe-area padding.

- [ ] **Step 2: Run the test and verify it fails**

Run: `node frontend/tests/thoughtCourtWiring.test.cjs`

Expected: FAIL on the new recovery/accessibility assertions.

- [ ] **Step 3: Implement persistent recovery UI**

Render errors inside the current act. `重试` repeats only the failed remote operation. `切换演示稳定层` is shown only when a matching curated case exists; otherwise offer `返回选案`. The badge text must be `演示稳定层：已加载经校验案件`.

- [ ] **Step 4: Complete keyboard and screen-reader behavior**

Set focus to each act heading after phase change, except while the user is typing. Give expanded evidence `aria-controls`, announce streaming speech in sentence-sized chunks, and ensure every drag target has a button equivalent.

- [ ] **Step 5: Complete the mobile layout**

At `max-width: 767px`, replace the three-seat stage with one active seat and a horizontal segmented sage selector. Evidence becomes a bottom sheet with a maximum height of `70dvh`. The main action bar uses `padding-bottom: max(12px, env(safe-area-inset-bottom))`. Prevent horizontal overflow at 390px.

- [ ] **Step 6: Run wiring and build checks**

Run:

```powershell
node frontend/tests/thoughtCourtWiring.test.cjs
npm --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 7: Commit Task 10**

```powershell
git add frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs
git commit -m "feat: make thought court resilient and accessible"
```

---

### Task 11: Integrate The Test Suite And Update Demo Documentation

**Files:**
- Modify: `frontend/package.json`
- Modify: `README.md`
- Modify: `docs/hackathon/final-delivery-checklist.md`
- Modify: `frontend/tests/demoHackathonWiring.test.cjs`

- [ ] **Step 1: Update the old demo wiring test before implementation docs**

Replace assertions for the presenter runbook with assertions for the actual product experience: `思想审判场`, `不是一个 AI`, `一桌中国思想`, `问`, `证`, `辩`, `判`, `演示稳定层`, and `ThoughtCourtExperience`.

- [ ] **Step 2: Run the old demo test and verify the expected failure before changing it**

Run the current test first: `node frontend/tests/demoHackathonWiring.test.cjs`

Expected before editing: FAIL because the old `/demo` marketing signals no longer exist.

After editing, run it again.

Expected: `demoHackathonWiring tests passed`.

- [ ] **Step 3: Add tests to the package script**

Append these commands to the existing `test` script without removing any current command:

```json
"node tests/thoughtCourtState.test.cjs && node tests/thoughtCourtCases.test.cjs && node tests/thoughtCourtVerdict.test.cjs && node tests/thoughtCourtSession.test.cjs && node tests/thoughtCourtWiring.test.cjs"
```

Keep the JSON as one valid script string. Do not alter dependencies.

- [ ] **Step 4: Update README and delivery checklist**

The README judging path becomes:

`/demo -> 问题落案 -> 经典举证 -> 百家交锋 -> 思想判牒 -> /about`

Document the three curated cases, the explicit stable-demo label, the no-login requirement, and the 1440px/390px checks. Keep the existing truthful mock/fallback explanation.

- [ ] **Step 5: Run the complete automated verification**

Run:

```powershell
npm --prefix frontend test
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
```

Expected: all tests pass, stage-check reports the intended backend/mock configuration, and the production build completes.

- [ ] **Step 6: Commit Task 11**

```powershell
git add frontend/package.json frontend/tests/demoHackathonWiring.test.cjs README.md docs/hackathon/final-delivery-checklist.md
git commit -m "docs: update thought court demo runbook"
```

---

### Task 12: Perform Desktop And Mobile Visual QA

**Files:**
- Modify as defects require: `frontend/components/thought-court/*.tsx`
- Modify as defects require: `frontend/components/thought-court/ThoughtCourt.module.css`
- Test: `frontend/tests/thoughtCourtWiring.test.cjs`

- [ ] **Step 1: Start the verified local application**

Run the backend in one terminal:

```powershell
Push-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the frontend in another terminal:

```powershell
npm --prefix frontend run dev:clean
```

Expected: frontend is reachable at the port printed by the script, normally `http://localhost:3000`, and backend health is available at `http://127.0.0.1:8000/health`.

- [ ] **Step 2: Verify the full curated first case at 1440px**

Use the browser that will be used for submission QA at 1440px width. Complete `recognition` from open-court to final seal. Capture each act and confirm:

- main canvas is nonblank and full-bleed;
- all three sage images load;
- evidence text and sources are legible;
- streaming text does not resize the stage;
- drag and click evidence paths both work;
- follow-up, mutual question, and stance controls show immediate feedback;
- weights reorder actions without changing citations;
- no control or text overlaps at any act.

- [ ] **Step 3: Verify the full curated first case at 390px**

Repeat at 390px width. Confirm no horizontal scrolling, bottom actions remain above the safe area, the active sage selector is usable, evidence bottom sheet fits within `70dvh`, long Chinese text wraps, and the seal does not cover actions.

- [ ] **Step 4: Verify reduced motion and degraded motion**

Enable reduced motion and repeat one act transition. Confirm no parallax, shockwave, long camera move, or animated seal scale. Force degraded mode through the in-product toggle/test hook and confirm imagery/content remains while ambient layers disappear.

- [ ] **Step 5: Verify live failure recovery**

Stop the backend after entering a live question. Confirm the current act remains visible, retry does not clear the question, stable-demo is offered only for a matching curated question, and the mode label is truthful.

- [ ] **Step 6: Fix defects with a failing regression assertion first**

For each defect, add the smallest failing assertion to `thoughtCourtWiring.test.cjs` or the relevant pure test, observe failure, patch the component/CSS, and rerun the targeted test.

- [ ] **Step 7: Run final verification**

Run:

```powershell
npm --prefix frontend test
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
Push-Location backend; python -m pytest tests -q; Pop-Location
git diff --check
```

Expected: every command exits 0. Record the actual test counts and any intentionally unavailable external service in the handoff.

- [ ] **Step 8: Record actual TRAE creation evidence**

Create `docs/hackathon/trae-evidence.md` from the real TRAE task history. Record at least three Session IDs, the feature produced by each session, the matching screenshot filename, and the commit containing the result. Verify that every recorded screenshot exists and that no Session ID was invented or copied from an unrelated task.

Run:

```powershell
$evidence = Get-Content -Raw -Encoding UTF8 docs/hackathon/trae-evidence.md
if (($evidence | Select-String -Pattern 'Session ID' -AllMatches).Matches.Count -lt 3) { throw 'Need at least 3 TRAE Session IDs' }
```

Expected: the command exits 0 and the document contains the actual evidence paths.

- [ ] **Step 9: Commit QA fixes and evidence**

```powershell
git add frontend/components/thought-court frontend/tests/thoughtCourtWiring.test.cjs docs/hackathon/trae-evidence.md
git commit -m "fix: polish thought court responsive experience"
```

If QA produces no source changes, do not create an empty commit.

---

## Completion Criteria

Implementation is complete only when all of the following are true:

- `/demo` opens the usable court, not a presenter runbook or marketing landing page.
- The curated recognition case completes all four acts in 90 seconds without login.
- All three curated cases pass content-integrity tests.
- A free question uses the real debate backend and preserves partial results when one sage fails.
- Stable fallback is explicit and never impersonates live output.
- Evidence source, original text, verification state, interpretation, and boundary are inspectable.
- User actions affect the court and verdict while immutable quote/source/attribution fields remain unchanged.
- 1440px and 390px browser checks show no blank scene, overlap, horizontal overflow, or unstable control dimensions.
- Full motion, reduced motion, and degraded motion are all usable.
- Frontend tests, stage-check, clean production build, backend tests, and `git diff --check` pass.

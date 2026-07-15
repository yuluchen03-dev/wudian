const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const read = (file) => fs.readFileSync(path.join(__dirname, "..", file), "utf8");

// ===== Task 5: Stage shell wiring =====
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
assert.ok(css.includes('data-motion="degraded"'));

// ===== Task 6: Case intake and evidence wiring =====
const intake = read("components/thought-court/CaseIntake.tsx");
assert.ok(intake.includes("我很努力，却总不被领导认可，怎么办？"));
assert.ok(intake.includes("稳定但不喜欢的工作，要不要离开？"));
assert.ok(intake.includes("同事抢了我的功劳，我该争还是忍？"));
assert.ok(intake.includes("textarea"));
assert.ok(intake.includes("击鼓开审"));

const evidenceDock = read("components/thought-court/EvidenceDock.tsx");
assert.ok(evidenceDock.includes("aria-expanded"));
assert.ok(evidenceDock.includes("加入本案"));
assert.ok(evidenceDock.includes("已核验"));
assert.ok(evidenceDock.includes("依据不完整"));
assert.ok(evidenceDock.includes("未找到足够可靠的经典依据"));

// ===== Task 7: Interactive sage tribunal wiring =====
const tribunal = read("components/thought-court/SageTribunal.tsx");
assert.ok(
  tribunal.includes("sageVisuals"),
  "SageTribunal should import sageVisuals from visualAssets"
);
assert.ok(
  tribunal.includes("追问"),
  "SageTribunal should expose a follow-up control labelled 追问"
);
assert.ok(
  tribunal.includes("请其互问"),
  "SageTribunal should expose a mutual-question control labelled 请其互问"
);
assert.ok(
  tribunal.includes("我更认同"),
  "SageTribunal should expose a stance control labelled 我更认同"
);
assert.ok(
  tribunal.includes('aria-live="polite"'),
  "SageTribunal should expose an aria-live polite region for streamed content"
);
assert.ok(
  tribunal.includes("暂未应答"),
  "SageTribunal should display 暂未应答 for failed or waiting speeches"
);
assert.ok(
  tribunal.includes("data-sage="),
  "SageTribunal should render three stable seat regions keyed by sage id"
);
assert.ok(
  tribunal.includes("落判定夺"),
  "SageTribunal should expose a build-verdict action labelled 落判定夺"
);

const experienceTribunal = read("components/thought-court/ThoughtCourtExperience.tsx");
assert.ok(
  experienceTribunal.includes("SageTribunal"),
  "ThoughtCourtExperience should render SageTribunal in the debate phase"
);

const hookSource = read("components/thought-court/useThoughtCourt.ts");
assert.ok(
  hookSource.includes("runIntervention"),
  "useThoughtCourt should wire the follow-up action to runIntervention"
);
assert.ok(
  hookSource.includes("runMutualQuestion"),
  "useThoughtCourt should wire the mutual-question action to runMutualQuestion"
);
assert.ok(
  hookSource.includes("runStand"),
  "useThoughtCourt should wire the stance action to runStand"
);
assert.ok(
  hookSource.includes("followUp"),
  "useThoughtCourt should expose a followUp action"
);
assert.ok(
  hookSource.includes("mutualQuestion"),
  "useThoughtCourt should expose a mutualQuestion action"
);
assert.ok(
  hookSource.includes("chooseStance"),
  "useThoughtCourt should expose a chooseStance action"
);

// ===== Task 8: Weight-responsive thought verdict wiring =====
const verdict = read("components/thought-court/VerdictScroll.tsx");
assert.ok(
  verdict.includes("核心矛盾"),
  "VerdictScroll should render the 核心矛盾 section"
);
assert.ok(
  verdict.includes("他们的共识"),
  "VerdictScroll should render the 他们的共识 section"
);
assert.ok(
  verdict.includes("根本分歧"),
  "VerdictScroll should render the 根本分歧 section"
);
assert.ok(
  verdict.includes("今日行动"),
  "VerdictScroll should render the 今日行动 section"
);
assert.ok(
  verdict.includes("保留问题"),
  "VerdictScroll should render the 保留问题 section"
);
assert.ok(
  verdict.includes("坚持自我"),
  "VerdictScroll should expose a 坚持自我 weight range input"
);
assert.ok(
  verdict.includes("改善关系"),
  "VerdictScroll should expose a 改善关系 weight range input"
);
assert.ok(
  verdict.includes("主动改变"),
  "VerdictScroll should expose a 主动改变 weight range input"
);
assert.ok(
  verdict.includes('type="range"'),
  "VerdictScroll should render range inputs for weight controls"
);
assert.ok(
  verdict.includes("落判"),
  "VerdictScroll should expose a 落判 seal action"
);
assert.ok(
  verdict.includes("重新调权"),
  "VerdictScroll should expose a 重新调权 action"
);
assert.ok(
  verdict.includes("新开一案"),
  "VerdictScroll should expose a 新开一案 action"
);
assert.ok(
  verdict.includes("SAFETY_BOUNDARY"),
  "VerdictScroll should render the fixed safety boundary"
);
assert.ok(
  verdict.includes("buildVerdict"),
  "VerdictScroll should use buildVerdict to compute the verdict"
);
assert.ok(
  verdict.includes("useMemo"),
  "VerdictScroll should memoize the verdict computation"
);
assert.ok(
  verdict.includes("normalizeWeights"),
  "VerdictScroll should display normalized weight percentages"
);

const experienceVerdict = read("components/thought-court/ThoughtCourtExperience.tsx");
assert.ok(
  experienceVerdict.includes("VerdictScroll"),
  "ThoughtCourtExperience should render VerdictScroll in the weighting/verdict phases"
);

// ===== Task 9: Cinematic 2.5D motion, sound, and performance degradation wiring =====
const courtComponentFiles = [
  "components/thought-court/CourtStageChrome.tsx",
  "components/thought-court/ThoughtCourtExperience.tsx",
  "components/thought-court/CaseIntake.tsx",
  "components/thought-court/EvidenceDock.tsx",
  "components/thought-court/SageTribunal.tsx",
  "components/thought-court/VerdictScroll.tsx",
  "components/thought-court/useThoughtCourt.ts",
];
const combinedCourtSource = courtComponentFiles.map(read).join("\n");

assert.ok(
  combinedCourtSource.includes("motion"),
  "thought court should reference motion from framer-motion"
);
assert.ok(
  combinedCourtSource.includes("AnimatePresence"),
  "thought court should reference AnimatePresence from framer-motion"
);
assert.ok(
  combinedCourtSource.includes("sageVisuals"),
  "thought court should reference sageVisuals from visualAssets"
);
assert.ok(
  combinedCourtSource.includes("portraitImage") ||
    combinedCourtSource.includes("sceneImage"),
  "thought court should reference sage portrait or scene imagery paths"
);
assert.ok(
  combinedCourtSource.includes("openingShot"),
  "thought court should define an openingShot motion class"
);
assert.ok(
  combinedCourtSource.includes("evidenceCloseup"),
  "thought court should define an evidenceCloseup motion class"
);
assert.ok(
  combinedCourtSource.includes("clashShockwave"),
  "thought court should define a clashShockwave motion class"
);
assert.ok(
  combinedCourtSource.includes("verdictSeal"),
  "thought court should define a verdictSeal motion class"
);
assert.ok(
  combinedCourtSource.includes('state.sound === "enabled"'),
  "thought court should gate sound playback behind state.sound === enabled"
);

const courtCssTask9 = read("components/thought-court/ThoughtCourt.module.css");
assert.ok(
  courtCssTask9.includes("openingShot"),
  "court css should define the openingShot motion class"
);
assert.ok(
  courtCssTask9.includes("evidenceCloseup"),
  "court css should define the evidenceCloseup motion class"
);
assert.ok(
  courtCssTask9.includes("clashShockwave"),
  "court css should define the clashShockwave motion class"
);
assert.ok(
  courtCssTask9.includes("verdictSeal"),
  "court css should define the verdictSeal motion class"
);

// ===== Task 10: Mobile, accessibility, and failure recovery wiring =====
const combinedCourtTask10 = courtComponentFiles.map(read).join("\n");

assert.ok(
  combinedCourtTask10.includes("跳过") || combinedCourtTask10.includes("skip"),
  "thought court should provide a skip link"
);
assert.ok(
  courtCssTask9.includes(":focus-visible") || courtCssTask9.includes(":focus"),
  "court css should have visible focus styles"
);
assert.ok(
  combinedCourtTask10.includes("aria-live"),
  "thought court should have aria-live status regions"
);
assert.ok(
  courtCssTask9.includes("min-height: 44px") ||
    courtCssTask9.includes("min-height:44px"),
  "court css should enforce 44px minimum controls"
);
assert.ok(
  combinedCourtTask10.includes("重试"),
  "thought court should expose a retry control"
);
assert.ok(
  combinedCourtTask10.includes("切换演示稳定层"),
  "thought court should expose a switch-to-stable-demo control"
);
assert.ok(
  combinedCourtTask10.includes("演示稳定层：已加载经校验案件"),
  "thought court should show the exact stable-demo badge label"
);
assert.ok(
  combinedCourtTask10.includes("无需登录"),
  "thought court should display no-login copy"
);
assert.ok(
  courtCssTask9.includes("390px") || courtCssTask9.includes("max-width: 767px"),
  "court css should contain a 390px-safe mobile layout"
);
assert.ok(
  courtCssTask9.includes("env(safe-area-inset-bottom)"),
  "court css should contain bottom action safe-area padding"
);

console.log("thoughtCourtWiring tests passed");

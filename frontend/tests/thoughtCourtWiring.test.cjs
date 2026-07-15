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

console.log("thoughtCourtWiring tests passed");

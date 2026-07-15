const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const pagePath = path.join(__dirname, "..", "app", "demo", "page.tsx");
const pageSource = fs.readFileSync(pagePath, "utf8");

// The demo route must mount the Thought Court experience.
assert.ok(
  pageSource.includes("ThoughtCourtExperience"),
  "Demo page should mount ThoughtCourtExperience"
);

// Collect the actual product experience source to verify hackathon signals.
const componentDir = path.join(__dirname, "..", "components", "thought-court");
const componentFiles = [
  "CourtStageChrome.tsx",
  "CaseIntake.tsx",
  "EvidenceDock.tsx",
  "SageTribunal.tsx",
  "VerdictScroll.tsx",
  "ThoughtCourtExperience.tsx",
];
const combinedSource = [
  pageSource,
  ...componentFiles.map((file) =>
    fs.readFileSync(path.join(componentDir, file), "utf8")
  ),
].join("\n");

[
  "思想审判场",
  "不是一个 AI",
  "一桌中国思想",
  "问",
  "证",
  "辩",
  "判",
  "演示稳定层",
].forEach((snippet) => {
  assert.ok(
    combinedSource.includes(snippet),
    `Thought Court experience should include hackathon signal: ${snippet}`
  );
});

console.log("demoHackathonWiring tests passed");

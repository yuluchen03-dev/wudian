const fs = require("fs");
const path = require("path");
const assert = require("assert");

const playerSource = fs.readFileSync(
  path.join(__dirname, "../components/content/TheaterPlayer.tsx"),
  "utf8"
);

const pageSource = fs.readFileSync(path.join(__dirname, "../app/content/page.tsx"), "utf8");

[
  "data-theater-surface",
  "data-stage-panel",
  "data-beat-timeline",
  "data-cast-panel",
  "data-agent-task-panel",
  "data-conflict-pressure",
  "data-stage-action",
  "data-source-anchor",
  "data-ending-recap",
].forEach((marker) => {
  assert(
    playerSource.includes(marker),
    `TheaterPlayer should expose ${marker} for the richer theater experience`
  );
});

assert(
  playerSource.includes("role.description"),
  "cast panel should surface role motivations/descriptions"
);

[
  "role.objective",
  "role.fear",
  "role.strategy",
  "line.beat",
  "line.action",
  "line.subtext",
].forEach((snippet) => {
  assert(
    playerSource.includes(snippet),
    `TheaterPlayer should render richer agent/script field ${snippet}`
  );
});

[
  "objective?: string",
  "fear?: string",
  "strategy?: string",
  "beat?: string",
  "action?: string",
  "subtext?: string",
].forEach((snippet) => {
  assert(
    fs.readFileSync(path.join(__dirname, "../lib/types.ts"), "utf8").includes(snippet),
    `Theater types should include ${snippet}`
  );
});

assert(
  playerSource.includes("goToLine"),
  "theater timeline should support jumping to a narrative beat"
);

assert(
  pageSource.includes("max-w-5xl") || pageSource.includes("max-w-6xl"),
  "selected theater view should use a wider stage layout"
);

[
  "mockQuoteCards",
  "mockTheaters",
  "mockComics",
  "setLoading(false)",
  "catch",
  "finally",
].forEach((snippet) => {
  assert(
    pageSource.includes(snippet),
    `content page should recover from unavailable content API with ${snippet}`
  );
});

console.log("theaterExperienceWiring tests passed");

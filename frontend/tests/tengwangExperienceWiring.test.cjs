const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (relativePath) =>
  fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");

const assertIncludes = (source, sourceName, snippets) => {
  snippets.forEach((snippet) => {
    assert.ok(
      source.includes(snippet),
      `${sourceName} should include ${JSON.stringify(snippet)}`
    );
  });
};

const assertMatches = (source, sourceName, pattern, requirement) => {
  assert.match(source, pattern, `${sourceName} should ${requirement}`);
};

const packageJson = JSON.parse(read("package.json"));
const experience = read("components/content/tengwang/TengwangExperience.tsx");
const canvas = read("components/content/tengwang/CurtainCanvas.tsx");
const styles = read("components/content/tengwang/TengwangExperience.module.css");
const route = read("app/content/tengwang-ge-xu/page.tsx");
const content = read("app/content/page.tsx");

assertIncludes(experience, "TengwangExperience.tsx", [
  "data-tengwang-experience",
  "滕王阁序",
  "王勃",
  "MAX_UPLOAD_BYTES",
  "image/png",
  "image/jpeg",
  "image/webp",
  "strength: 72",
  "reach: 34",
  "inertia: 97",
  "soundEnabled: false",
  "audioSupported",
  "TENGWANG_GE_XU_TEXT",
  "SlidersHorizontal",
  "VolumeX",
  "URL.revokeObjectURL",
]);

assertMatches(
  experience,
  "TengwangExperience.tsx",
  /<aside\b[^>]*\brole\s*=\s*"dialog"[^>]*\baria-modal\s*=\s*"true"[^>]*>/,
  "render its settings surface as an aside with dialog and modal semantics"
);

assertIncludes(canvas, "CurtainCanvas.tsx", [
  "data-curtain-canvas",
  "requestAnimationFrame",
  "AudioContext",
  "buildCurtain",
  "integrateCurtain",
  "constrainCurtain",
]);

assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /new\s+ResizeObserver\s*\(/,
  "create a ResizeObserver for responsive canvas rebuilding"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /new\s+IntersectionObserver\s*\(/,
  "create an IntersectionObserver for offscreen pausing"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /document\s*\.\s*addEventListener\s*\(\s*["']visibilitychange["']/,
  "listen for document visibility changes"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /cancelAnimationFrame\s*\(\s*animationId\s*\)/,
  "cancel its scheduled animation frame during cleanup"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /resizeObserver\s*\.\s*disconnect\s*\(\s*\)/,
  "disconnect its ResizeObserver during cleanup"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /intersectionObserver\s*\.\s*disconnect\s*\(\s*\)/,
  "disconnect its IntersectionObserver during cleanup"
);
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /document\s*\.\s*removeEventListener\s*\(\s*["']visibilitychange["']\s*,\s*handleVisibilityChange\s*\)/,
  "remove its visibilitychange listener during cleanup"
);

[
  ["pointerenter", "handlePointerEnter"],
  ["pointermove", "handlePointerMove"],
  ["pointerleave", "handlePointerLeave"],
  ["pointercancel", "handlePointerLeave"],
].forEach(([eventName, handlerName]) =>
  assertMatches(
    canvas,
    "CurtainCanvas.tsx",
    new RegExp(
      `canvas\\s*\\.\\s*removeEventListener\\s*\\(\\s*["']${eventName}["']\\s*,\\s*${handlerName}\\s*\\)`
    ),
    `remove its ${eventName} listener during cleanup`
  )
);

assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /audioContext\s*\?\.\s*close\s*\(\s*\)\s*\.\s*catch\s*\(/,
  "close its AudioContext and handle the close promise during cleanup"
);

assertMatches(
  route,
  "app/content/tengwang-ge-xu/page.tsx",
  /<TengwangExperience\s*\/>/,
  "render <TengwangExperience />"
);
assertMatches(
  content,
  "app/content/page.tsx",
  /<Link\b[^>]*\bhref\s*=\s*"\/content\/tengwang-ge-xu"[^>]*>(?:(?!<\/Link>)[\s\S])*?文境(?:(?!<\/Link>)[\s\S])*?<\/Link>/,
  "render one Link to /content/tengwang-ge-xu containing the 文境 label"
);

assertMatches(
  styles,
  "TengwangExperience.module.css",
  /min-height\s*:\s*clamp\(\s*620px\s*,\s*calc\(\s*100svh\s*-\s*68px\s*\)\s*,\s*860px\s*\)/,
  "define the desktop experience height clamp"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /min-height\s*:\s*max\(\s*720px\s*,\s*calc\(\s*100svh\s*-\s*68px\s*\)\s*\)/,
  "define the mobile viewport-safe minimum height"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /max-height\s*:\s*min\(\s*78dvh\s*,\s*620px\s*\)/,
  "cap the mobile settings bottom sheet height"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)/,
  "define reduced-motion overrides"
);

assert.equal(
  typeof packageJson.scripts?.test,
  "string",
  "package.json should define scripts.test as a string"
);
assert.ok(
  packageJson.scripts.test.startsWith(
    "node tests/curtainPhysics.test.cjs && node tests/tengwangExperienceWiring.test.cjs && "
  ),
  "package.json scripts.test should run curtain physics and Tengwang wiring first"
);

console.log("tengwangExperienceWiring tests passed");

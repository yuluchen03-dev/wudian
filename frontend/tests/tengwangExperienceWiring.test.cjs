const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (relativePath) =>
  fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");

const experience = read("components/content/tengwang/TengwangExperience.tsx");
const canvas = read("components/content/tengwang/CurtainCanvas.tsx");
const styles = read("components/content/tengwang/TengwangExperience.module.css");
const route = read("app/content/tengwang-ge-xu/page.tsx");
const content = read("app/content/page.tsx");
const packageSource = read("package.json");

[
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
  'role="dialog"',
  'aria-modal="true"',
  "SlidersHorizontal",
  "VolumeX",
  "prefers-reduced-motion",
].forEach((snippet) =>
  assert.ok(experience.includes(snippet) || styles.includes(snippet), `missing ${snippet}`)
);

[
  "data-curtain-canvas",
  "ResizeObserver",
  "IntersectionObserver",
  "visibilitychange",
  "requestAnimationFrame",
  "cancelAnimationFrame",
  "AudioContext",
  ".close()",
  "buildCurtain",
  "integrateCurtain",
  "constrainCurtain",
].forEach((snippet) =>
  assert.ok(canvas.includes(snippet), `CurtainCanvas should include ${snippet}`)
);

assert.match(route, /TengwangExperience/);
assert.match(content, /href="\/content\/tengwang-ge-xu"/);
assert.match(content, /文境/);
assert.match(styles, /clamp\(620px, calc\(100svh - 68px\), 860px\)/);
assert.match(styles, /max\(720px, calc\(100svh - 68px\)\)/);
assert.match(styles, /max-height:\s*min\(78dvh, 620px\)/);
assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
assert.match(packageSource, /curtainPhysics\.test\.cjs/);
assert.match(packageSource, /tengwangExperienceWiring\.test\.cjs/);

console.log("tengwangExperienceWiring tests passed");

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
const styles = read("components/content/tengwang/TengwangExperience.module.css");

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
  "MAX_IMAGE_PIXELS",
  "effectiveCurtainText",
  "dialogRef",
  "ignoreDialogCloseRef",
  "showModal()",
  "drawImage(",
  "toBlob(",
  "styles.staticExcerpt",
  "使用默认文本",
  "SlidersHorizontal",
  "VolumeX",
  "URL.revokeObjectURL",
]);

assertMatches(
  experience,
  "TengwangExperience.tsx",
  /<dialog\b[^>]*\bref\s*=\s*\{dialogRef\}[^>]*\bonCancel\s*=\s*\{handleDialogCancel\}[^>]*\bonClose\s*=\s*\{handleDialogClose\}[^>]*>(?:(?!<\/dialog>)[\s\S])*?<aside\b[^>]*\bid\s*=\s*"tengwang-settings"[^>]*\brole\s*=\s*"dialog"[^>]*\baria-modal\s*=\s*"true"[^>]*>/,
  "wrap its required settings aside in a native dialog with cancel and close handlers"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /dialog\s*\.\s*showModal\s*\(\s*\)/,
  "open the native dialog in the top layer"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /dialog\s*\.\s*close\s*\(\s*\)/,
  "close the native dialog during panel cleanup"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /event\s*\.\s*currentTarget\s*===\s*event\s*\.\s*target/,
  "close only clicks that land on the native dialog backdrop"
);

assertMatches(
  experience,
  "TengwangExperience.tsx",
  /const\s+effectiveCurtainText\s*=\s*curtainText\s*\.\s*trim\s*\(\s*\)\s*\?\s*curtainText\s*:\s*TENGWANG_GE_XU_TEXT/,
  "derive one effective curtain text value that treats whitespace as empty"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /<CurtainCanvas\b(?:(?!\/>)[\s\S])*?\btext\s*=\s*\{effectiveCurtainText\}/,
  "pass the effective text to CurtainCanvas"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /className\s*=\s*\{styles\.srOnly\}[^>]*>\s*\{effectiveCurtainText\}\s*<\/p>/,
  "expose the effective text to screen readers"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /canvasUnavailable\s*&&\s*\([\s\S]*?className\s*=\s*\{styles\.staticExcerpt\}[\s\S]*?\{effectiveCurtainText\}/,
  "render the effective text in the static fallback excerpt"
);
assert.equal(
  (experience.match(/\brole\s*=\s*"status"/g) ?? []).length,
  1,
  "TengwangExperience.tsx should expose one combined live status region"
);

assertMatches(
  experience,
  "TengwangExperience.tsx",
  /const\s+MAX_IMAGE_PIXELS\s*=\s*(?:8_000_000|8000000)\s*;/,
  "cap decoded uploads at no more than eight million pixels"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /naturalWidth\s*\*\s*candidateImage\s*\.\s*naturalHeight\s*<=\s*MAX_IMAGE_PIXELS/,
  "validate the decoded image pixel count"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /\.\s*drawImage\s*\(\s*candidateImage\s*,/,
  "draw the decoded first frame into an offscreen canvas"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /\.\s*toBlob\s*\([\s\S]*?["']image\/png["']/,
  "encode the accepted image as a static PNG blob"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /URL\s*\.\s*createObjectURL\s*\(\s*staticBlob\s*\)/,
  "make the accepted object URL own the static PNG blob"
);

assertMatches(
  styles,
  "TengwangExperience.module.css",
  /\.settingsDialog\s*\{[^}]*position\s*:\s*fixed[^}]*inset\s*:\s*0[^}]*background\s*:\s*transparent[^}]*\}/,
  "make the native dialog a transparent full-viewport layer"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /\.settingsDialog::backdrop\s*\{/,
  "style the native dialog backdrop"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /\.settingsPanel\s*\{[^}]*position\s*:\s*fixed/,
  "fix the settings panel within the native top layer"
);
assertMatches(
  styles,
  "TengwangExperience.module.css",
  /\.staticExcerpt\s*\{[^}]*writing-mode\s*:\s*vertical-rl[^}]*overflow\s*:\s*hidden/,
  "bound the vertical-writing static text fallback"
);

const canvas = read("components/content/tengwang/CurtainCanvas.tsx");

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

const route = read("app/content/tengwang-ge-xu/page.tsx");
const content = read("app/content/page.tsx");

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

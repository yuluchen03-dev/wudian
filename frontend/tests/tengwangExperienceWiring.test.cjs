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
  "imageUnavailable",
  "sceneUnavailable",
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
  /<dialog\b[^>]*\bref\s*=\s*\{dialogRef\}[^>]*\baria-modal\s*=\s*"true"[^>]*\bonCancel\s*=\s*\{handleDialogCancel\}[^>]*\bonClose\s*=\s*\{handleDialogClose\}[^>]*>(?:(?!<\/dialog>)[\s\S])*?<aside\b[^>]*\bid\s*=\s*"tengwang-settings"[^>]*>/,
  "expose one native modal dialog around the settings layout"
);
assert.equal(
  (experience.match(/\baria-modal\s*=\s*"true"/g) ?? []).length,
  1,
  "TengwangExperience.tsx should declare one modal surface"
);
assert.doesNotMatch(
  experience,
  /<aside\b[^>]*(?:\brole\s*=\s*"dialog"|\baria-modal\s*=\s*"true")[^>]*>/,
  "the settings aside should not duplicate the native dialog semantics"
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
  /\{\s*!sceneUnavailable\s*&&\s*\(\s*<p\b[^>]*className\s*=\s*\{styles\.srOnly\}[^>]*>\s*\{effectiveCurtainText\}\s*<\/p>\s*\)\s*\}/,
  "expose the screen-reader-only passage only in the dynamic canvas branch"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /sceneUnavailable\s*&&\s*\([\s\S]*?className\s*=\s*\{styles\.staticExcerpt\}[\s\S]*?\{effectiveCurtainText\}/,
  "render the effective text when either the image or Canvas is unavailable"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /const\s+sceneUnavailable\s*=\s*canvasUnavailable\s*\|\|\s*imageUnavailable/,
  "derive one scene fallback state from image and Canvas availability"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /onLoad\s*=\s*\{\s*\(\s*\)\s*=>\s*\{[\s\S]*?setImageUnavailable\(false\)[\s\S]*?onError\s*=\s*\{\s*\(\s*\)\s*=>\s*\{[\s\S]*?setImageUnavailable\(true\)/,
  "clear image failure on load and enter fallback on a main image error"
);
assert.equal(
  (experience.match(/setImageUnavailable\(true\)/g) ?? []).length,
  1,
  "only a failed current main image should mark the scene unavailable"
);
assertMatches(
  experience,
  "TengwangExperience.tsx",
  /\{\s*sceneUnavailable\s*\?\s*\(\s*<p\b[^>]*className\s*=\s*\{styles\.canvasNotice\}/,
  "hide no-op physics and audio controls throughout static mode"
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
assertMatches(
  canvas,
  "CurtainCanvas.tsx",
  /canvas\s*\.\s*addEventListener\s*\(\s*["']pointerdown["']\s*,\s*handlePointerEnter\s*\)/,
  "initialize audio from an explicit pointerdown gesture"
);

[
  ["pointerenter", "handlePointerEnter"],
  ["pointerdown", "handlePointerEnter"],
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
  /const\s+suspendAudio\s*=\s*\(\s*\)\s*=>\s*\{\s*try\s*\{\s*if\s*\(\s*audioContext\s*&&\s*audioContext\s*\.\s*state\s*!==\s*["']closed["']\s*\)\s*\{\s*audioContext\s*\.\s*suspend\s*\(\s*\)\s*\.\s*catch\s*\(/,
  "suspend every existing AudioContext that is not closed"
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
  /<Link\b[^>]*\bhref\s*=\s*"\/content\/tengwang-ge-xu"[^>]*\bclassName\s*=\s*"[^"]*\bshrink-0\b[^"]*"[^>]*>[\s\S]*?<span\b[^>]*\bclassName\s*=\s*"[^"]*\bsm:hidden\b[^"]*"[^>]*>文境<\/span>[\s\S]*?<span\b[^>]*\bclassName\s*=\s*"[^"]*\bhidden\b[^"]*\bsm:inline\b[^"]*"[^>]*>滕王阁序 · 文境<\/span>[\s\S]*?<\/Link>/,
  "render a non-shrinking Tengwang Link with compact mobile and full desktop labels"
);

const stickyTabBarMatch = content.match(
  /(<div\b[^>]*\bclassName\s*=\s*"[^"]*\bsticky\b[^"]*"[^>]*>(?:(?!<\/?div\b)[\s\S])*?<\/div>)\s*\{\/\*\s*内容区\s*\*\/\}/
);

assert.ok(
  stickyTabBarMatch,
  "content page should render a non-nested sticky tab bar before the content section"
);

const stickyTabBar = stickyTabBarMatch[1];

assert.match(
  stickyTabBar,
  /\bhref\s*=\s*"\/content\/tengwang-ge-xu"/,
  "sticky tab bar should contain the /content/tengwang-ge-xu entry"
);

const tabsMapIndex = content.indexOf("{tabs.map");
const contentSectionIndex = content.indexOf("{/* 内容区 */}");

assert.ok(tabsMapIndex >= 0, "content page should render the existing tab map");
assert.ok(contentSectionIndex > tabsMapIndex, "content section should follow the tab map");

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

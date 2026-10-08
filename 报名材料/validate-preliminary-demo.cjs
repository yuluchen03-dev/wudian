const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(__dirname, "一问见古今-初赛Demo");

const requiredFiles = [
  "index.html",
  "css/app.css",
  "js/three.module.min.js",
  "js/three.core.min.js",
  "js/THREE-LICENSE.txt",
  "js/court-data.js",
  "js/court-scene.js",
  "js/app.js",
  "js/app.bundle.js",
  "assets/confucius.png",
  "assets/mencius.png",
  "assets/laozi.png",
];

for (const relativePath of requiredFiles) {
  assert.ok(fs.existsSync(path.join(packageRoot, relativePath)), `Missing ${relativePath}`);
}

const read = (relativePath) => fs.readFileSync(path.join(packageRoot, relativePath), "utf8");
const html = read("index.html");
const css = read("css/app.css");
const data = read("js/court-data.js");
const scene = read("js/court-scene.js");
const app = read("js/app.js");
const combined = [html, css, data, scene, app].join("\n");

assert.doesNotMatch(combined, /https?:\/\//i, "Runtime must not reference remote URLs");
assert.doesNotMatch(html, /type=["']module["']/i, "Direct-open demo must not depend on file-blocked ES modules");
assert.match(html, /<script\s+src="js\/app\.bundle\.js"><\/script>/, "Entry point must load the file-compatible app bundle");
assert.match(html, /id="court-canvas"/, "Entry point must expose the full-bleed 3D canvas");
assert.match(html, /初赛稳定体验 · 本地策展数据/, "Stable demo disclosure is required");

for (const state of ["intake", "opening", "evidence", "debate", "weighting", "verdict", "epilogue"]) {
  assert.match(app, new RegExp(`"${state}"`), `Missing state ${state}`);
}

for (const text of [
  "问题拆解",
  "知识库检索",
  "引用校验",
  "多思想编排",
  "用户调权",
  "行动判牒",
  "申请企业青年员工试点",
  "企业不能查看个人原始提问",
]) {
  assert.ok(combined.includes(text), `Missing required content: ${text}`);
}

for (const state of ["support", "refute", "reframe"]) {
  assert.ok(data.includes(state), `Missing relation type ${state}`);
}

assert.match(data, /function deepFreeze/, "Curated case data must expose a recursive freeze helper");
assert.match(data, /export const CASES = deepFreeze\(\[/, "Curated cases must be immutable");
assert.match(css, /prefers-reduced-motion/, "Reduced-motion CSS is required");
assert.match(combined, /\[hidden\]\s*\{display:none!important\}/, "Hidden controls must stay hidden until their state transition");
assert.match(css, /html\.reduce-motion/, "Manual reduced-motion mode must disable DOM motion");
assert.match(css, /is-2d-fallback/, "Portrait fallback CSS is required");
assert.match(scene, /createCourtScene/, "3D scene factory is required");
assert.match(scene, /THREE\.WebGLRenderer/, "Three.js WebGL renderer is required");
assert.match(scene, /setPixelRatio/, "Canvas pixel ratio must be capped");
assert.match(scene, /is-2d-fallback/, "WebGL failure must activate portrait fallback");
assert.match(scene, /prefers-reduced-motion/, "3D scene must respect reduced motion");
for (const portrait of ["confucius.png", "mencius.png", "laozi.png"]) {
  assert.ok(scene.includes(portrait), `3D scene must load ${portrait}`);
}
assert.match(scene, /THREE\.TextureLoader/, "3D portrait seats must use local textures");
assert.match(scene, /createPortraitSeat/, "3D portrait-seat factory is required");
assert.doesNotMatch(scene, /createSage|IcosahedronGeometry|userData\.arm/, "Geometric sage dolls must be removed");
assert.match(html, /点击肖像切换立场/, "Debate hint must describe portrait interaction honestly");
assert.match(app, /force2d/, "App must expose a deterministic 2D fallback test path");
assert.match(app, /if \(total === 0\) return \{ self: 34, relationship: 33, change: 33 \}/, "Zero weights must return the neutral default");
assert.match(app, /setActiveSage\("confucius"\); go\("debate"\)/, "Re-entering debate must synchronize the DOM and 3D active sage");
assert.match(app, /window\.scrollTo\(\{ top: 0, behavior: "auto" \}\)/, "State transitions must reset long mobile pages to the top");
assert.match(scene, /forceFallback/, "Scene factory must support deterministic fallback");

const threeSize = fs.statSync(path.join(packageRoot, "js/three.module.min.js")).size;
assert.ok(threeSize > 300_000, "Vendored Three.js module appears incomplete");
const threeCoreSize = fs.statSync(path.join(packageRoot, "js/three.core.min.js")).size;
assert.ok(threeCoreSize > 300_000, "Vendored Three.js core module appears incomplete");
for (const portrait of ["confucius", "mencius", "laozi"]) {
  assert.ok(fs.statSync(path.join(packageRoot, `assets/${portrait}.png`)).size > 100_000, `${portrait} portrait is incomplete`);
}

console.log("Preliminary 3D demo validation passed.");

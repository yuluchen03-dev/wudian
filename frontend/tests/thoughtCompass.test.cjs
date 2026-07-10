const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("../node_modules/typescript/lib/typescript");

function loadTsModule(relativePath) {
  const modulePath = path.join(__dirname, "..", relativePath);
  const source = fs.readFileSync(modulePath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      esModuleInterop: true,
    },
  }).outputText;
  const mod = { exports: {} };
  const run = new Function("require", "module", "exports", "__dirname", "__filename", compiled);
  run(require, mod, mod.exports, path.dirname(modulePath), modulePath);
  return mod.exports;
}

const { analyzeThoughtCompass } = loadTsModule("lib/thoughtCompass.ts");

const mark = analyzeThoughtCompass("我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。");

assert.equal(mark.label, "逍遥实干派");
assert.ok(mark.activePercent >= 30 && mark.activePercent <= 55);
assert.ok(mark.quietPercent > mark.activePercent);
assert.equal(mark.nearestSchool, "儒道之间");
assert.match(mark.imprint, /逍遥实干派/);

const backendMark = flowNormalize({
  x: 42,
  y: 51,
  active_percent: 42,
  quiet_percent: 58,
  nearest_school: "儒道之间",
  label: "逍遥实干派",
  imprint: "今日论道，你自成一家，我们称之为「逍遥实干派」。",
});

assert.equal(backendMark.activePercent, 42);
assert.equal(backendMark.quietPercent, 58);
assert.equal(backendMark.nearestSchool, "儒道之间");

function flowNormalize(payload) {
  return loadTsModule("lib/thoughtCompass.ts").normalizeBackendThoughtCompass(payload);
}

console.log("thoughtCompass tests passed");

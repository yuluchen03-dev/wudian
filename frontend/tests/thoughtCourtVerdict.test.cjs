const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const verdict = loadTsModule("lib/thoughtCourtVerdict.ts");
const cases = loadTsModule("lib/thoughtCourtCases.ts");

assert.deepEqual(verdict.normalizeWeights({ self: 0, relationship: 0, change: 0 }), { self: 34, relationship: 33, change: 33 });
assert.deepEqual(verdict.normalizeWeights({ self: 80, relationship: 10, change: 10 }), { self: 80, relationship: 10, change: 10 });

const item = cases.getCuratedCourtCase("recognition");
const selfFirst = verdict.buildVerdict(item.report, { self: 80, relationship: 10, change: 10 });
assert.equal(selfFirst.dominantKey, "self");
assert.equal(selfFirst.actions[0], item.report.actions.self[0]);
const changeFirst = verdict.buildVerdict(item.report, { self: 10, relationship: 10, change: 80 });
assert.equal(changeFirst.dominantKey, "change");
assert.equal(changeFirst.actions[0], item.report.actions.change[0]);
assert.deepEqual(item.evidence.map((e) => e.original), cases.getCuratedCourtCase("recognition").evidence.map((e) => e.original));

console.log("thoughtCourtVerdict tests passed");

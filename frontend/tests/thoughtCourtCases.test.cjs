const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const cases = loadTsModule("lib/thoughtCourtCases.ts");

assert.equal(cases.CURATED_COURT_CASES.length, 3);
for (const item of cases.CURATED_COURT_CASES) {
  assert.equal(item.sages.length, 3);
  assert.ok(item.conflicts.length >= 3);
  assert.ok(item.evidence.length >= 3);
  assert.equal(item.speeches.length, 3);
  assert.ok(item.clashes.length >= 2);
  assert.ok(item.report.actions.self.length > 0);
  assert.ok(item.report.actions.relationship.length > 0);
  assert.ok(item.report.actions.change.length > 0);
  for (const evidence of item.evidence) {
    assert.ok(evidence.original.trim());
    assert.ok(evidence.source.startsWith("《"));
    assert.ok(evidence.interpretation.trim());
    assert.ok(evidence.boundary.trim());
    assert.equal(evidence.verified, true);
  }
  for (const speech of item.speeches) {
    assert.ok(speech.evidenceIds.every((id) => item.evidence.some((e) => e.id === id)));
  }
}
assert.equal(cases.getCuratedCourtCase("recognition").question, "我很努力，却总不被领导认可，怎么办？");
assert.equal(cases.getCuratedCourtCase("missing"), null);

console.log("thoughtCourtCases tests passed");

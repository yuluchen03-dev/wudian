const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const court = loadTsModule("lib/thoughtCourtState.ts");

let state = court.createCourtState();
assert.equal(state.phase, "idle");
assert.equal(state.mode, "curated");
assert.equal(state.sound, "muted");

state = court.transitionCourt(state, { type: "SELECT_CASE", caseId: "recognition" });
assert.equal(state.phase, "intake");
state = court.transitionCourt(state, { type: "SUBMIT_CASE", question: "我很努力，却总不被认可。" });
assert.equal(state.phase, "retrieving");
state = court.transitionCourt(state, {
  type: "RETRIEVAL_SUCCEEDED",
  evidenceIds: ["recognition-confucius-1"],
  citationStatus: "verified",
});
assert.equal(state.phase, "evidence");
state = court.transitionCourt(state, { type: "BEGIN_DEBATE" });
assert.equal(state.phase, "debate");
state = court.transitionCourt(state, { type: "DEBATE_SUCCEEDED" });
assert.equal(state.phase, "weighting");
state = court.transitionCourt(state, { type: "BUILD_VERDICT" });
assert.equal(state.phase, "verdict");
state = court.transitionCourt(state, { type: "COMPLETE" });
assert.equal(state.phase, "completed");

const unchanged = court.transitionCourt(court.createCourtState(), { type: "BEGIN_DEBATE" });
assert.equal(unchanged.phase, "idle");

const failed = court.transitionCourt(state, { type: "REMOTE_FAILED", message: "timeout" });
assert.equal(failed.network, "failed");
assert.equal(failed.error, "timeout");
const stable = court.transitionCourt(failed, { type: "USE_STABLE_DEMO" });
assert.equal(stable.mode, "stable-demo");
assert.equal(stable.error, null);

console.log("thoughtCourtState tests passed");

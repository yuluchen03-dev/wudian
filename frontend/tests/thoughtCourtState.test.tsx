import { describe, it, expect } from "vitest";
import { createCourtState, transitionCourt } from "../lib/thoughtCourtState";

describe("thoughtCourtState", () => {
  it("creates court state with correct defaults", () => {
    const state = createCourtState();
    expect(state.phase).toBe("idle");
    expect(state.mode).toBe("curated");
    expect(state.sound).toBe("muted");
  });

  it("transitions through the full court lifecycle", () => {
    let state = createCourtState();
    state = transitionCourt(state, { type: "SELECT_CASE", caseId: "recognition" });
    expect(state.phase).toBe("intake");
    state = transitionCourt(state, { type: "SUBMIT_CASE", question: "我很努力，却总不被认可。" });
    expect(state.phase).toBe("retrieving");
    state = transitionCourt(state, {
      type: "RETRIEVAL_SUCCEEDED",
      evidenceIds: ["recognition-confucius-1"],
      citationStatus: "verified",
    });
    expect(state.phase).toBe("evidence");
    state = transitionCourt(state, { type: "BEGIN_DEBATE" });
    expect(state.phase).toBe("debate");
    state = transitionCourt(state, { type: "DEBATE_SUCCEEDED" });
    expect(state.phase).toBe("weighting");
    state = transitionCourt(state, { type: "BUILD_VERDICT" });
    expect(state.phase).toBe("verdict");
    state = transitionCourt(state, { type: "COMPLETE" });
    expect(state.phase).toBe("completed");
  });

  it("does not transition from idle with BEGIN_DEBATE", () => {
    const unchanged = transitionCourt(createCourtState(), { type: "BEGIN_DEBATE" });
    expect(unchanged.phase).toBe("idle");
  });

  it("handles REMOTE_FAILED and USE_STABLE_DEMO", () => {
    let state = createCourtState();
    state = transitionCourt(state, { type: "SELECT_CASE", caseId: "recognition" });
    state = transitionCourt(state, { type: "SUBMIT_CASE", question: "test" });
    state = transitionCourt(state, {
      type: "RETRIEVAL_SUCCEEDED",
      evidenceIds: [],
      citationStatus: "verified",
    });
    state = transitionCourt(state, { type: "BEGIN_DEBATE" });
    state = transitionCourt(state, { type: "DEBATE_SUCCEEDED" });
    state = transitionCourt(state, { type: "BUILD_VERDICT" });
    state = transitionCourt(state, { type: "COMPLETE" });

    const failed = transitionCourt(state, { type: "REMOTE_FAILED", message: "timeout" });
    expect(failed.network).toBe("failed");
    expect(failed.error).toBe("timeout");
    const stable = transitionCourt(failed, { type: "USE_STABLE_DEMO" });
    expect(stable.mode).toBe("stable-demo");
    expect(stable.error).toBeNull();
  });
});

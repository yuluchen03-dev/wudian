import type { CitationStatus, CourtMode, CourtMotionMode, CourtNetwork, CourtPhase, CourtSound, CourtWeights } from "./thoughtCourtTypes";

export interface CourtState {
  phase: CourtPhase;
  mode: CourtMode;
  network: CourtNetwork;
  citationStatus: CitationStatus;
  motion: CourtMotionMode;
  sound: CourtSound;
  caseId: string | null;
  question: string;
  evidenceIds: string[];
  weights: CourtWeights;
  error: string | null;
}

export type CourtEvent =
  | { type: "SELECT_CASE"; caseId: string }
  | { type: "SET_LIVE_QUESTION" }
  | { type: "SUBMIT_CASE"; question: string }
  | { type: "RETRIEVAL_SUCCEEDED"; evidenceIds: string[]; citationStatus: CitationStatus }
  | { type: "BEGIN_DEBATE" }
  | { type: "DEBATE_SUCCEEDED" }
  | { type: "SET_WEIGHTS"; weights: CourtWeights }
  | { type: "BUILD_VERDICT" }
  | { type: "COMPLETE" }
  | { type: "REMOTE_LOADING" | "REMOTE_STREAMING" }
  | { type: "REMOTE_FAILED"; message: string }
  | { type: "USE_STABLE_DEMO" }
  | { type: "RETRY" }
  | { type: "SET_MOTION"; motion: CourtMotionMode }
  | { type: "SET_SOUND"; sound: CourtSound }
  | { type: "RESET" };

export const DEFAULT_COURT_WEIGHTS: CourtWeights = { self: 34, relationship: 33, change: 33 };

export function createCourtState(): CourtState {
  return {
    phase: "idle",
    mode: "curated",
    network: "idle",
    citationStatus: "unavailable",
    motion: "full",
    sound: "muted",
    caseId: null,
    question: "",
    evidenceIds: [],
    weights: DEFAULT_COURT_WEIGHTS,
    error: null,
  };
}

export function transitionCourt(state: CourtState, event: CourtEvent): CourtState {
  if (event.type === "RESET") return createCourtState();
  if (event.type === "SET_MOTION") return { ...state, motion: event.motion };
  if (event.type === "SET_SOUND") return { ...state, sound: event.sound };
  if (event.type === "REMOTE_FAILED") return { ...state, network: "failed", error: event.message };
  if (event.type === "USE_STABLE_DEMO") return { ...state, mode: "stable-demo", network: "idle", error: null };
  if (event.type === "RETRY") return { ...state, network: "loading", error: null };
  if (event.type === "REMOTE_LOADING") return { ...state, network: "loading", error: null };
  if (event.type === "REMOTE_STREAMING") return { ...state, network: "streaming", error: null };

  if (event.type === "SELECT_CASE" && (state.phase === "idle" || state.phase === "intake")) {
    return { ...state, phase: "intake", mode: "curated", caseId: event.caseId };
  }
  if (event.type === "SET_LIVE_QUESTION" && (state.phase === "idle" || state.phase === "intake")) {
    return { ...state, phase: "intake", mode: "live", caseId: null };
  }
  if (event.type === "SUBMIT_CASE" && state.phase === "intake" && event.question.trim()) {
    return { ...state, phase: "retrieving", question: event.question.trim(), network: "loading", error: null };
  }
  if (event.type === "RETRIEVAL_SUCCEEDED" && state.phase === "retrieving") {
    return { ...state, phase: "evidence", network: "idle", evidenceIds: event.evidenceIds, citationStatus: event.citationStatus };
  }
  if (event.type === "BEGIN_DEBATE" && state.phase === "evidence") return { ...state, phase: "debate", network: "streaming" };
  if (event.type === "DEBATE_SUCCEEDED" && state.phase === "debate") return { ...state, phase: "weighting", network: "idle" };
  if (event.type === "SET_WEIGHTS" && (state.phase === "weighting" || state.phase === "verdict")) return { ...state, weights: event.weights };
  if (event.type === "BUILD_VERDICT" && state.phase === "weighting") return { ...state, phase: "verdict" };
  if (event.type === "COMPLETE" && state.phase === "verdict") return { ...state, phase: "completed" };
  return state;
}

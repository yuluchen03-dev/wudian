export type CourtPhase = "idle" | "intake" | "retrieving" | "evidence" | "debate" | "weighting" | "verdict" | "completed";
export type CourtMode = "curated" | "live" | "stable-demo";
export type CourtNetwork = "idle" | "loading" | "streaming" | "failed";
export type CitationStatus = "verified" | "partial" | "unavailable";
export type CourtMotionMode = "full" | "reduced" | "degraded";
export type CourtSound = "muted" | "enabled";
export type CourtWeightKey = "self" | "relationship" | "change";

export interface CourtEvidence {
  id: string;
  sageId: string;
  original: string;
  source: string;
  interpretation: string;
  boundary: string;
  verified: boolean;
}

export interface CourtSpeech {
  sageId: string;
  position: string;
  content: string;
  evidenceIds: string[];
  status: "waiting" | "streaming" | "complete" | "failed";
}

export interface CourtClash {
  fromSageId: string;
  toSageId: string;
  type: "support" | "refute" | "reframe";
  summary: string;
}

export interface CourtWeights {
  self: number;
  relationship: number;
  change: number;
}

export interface CourtReport {
  conflict: string;
  consensus: string[];
  divergences: string[];
  actions: Record<CourtWeightKey, string[]>;
  reservation: string;
}

export interface CuratedCourtCase {
  id: string;
  label: string;
  question: string;
  conflicts: string[];
  sages: string[];
  evidence: CourtEvidence[];
  speeches: CourtSpeech[];
  clashes: CourtClash[];
  report: CourtReport;
}

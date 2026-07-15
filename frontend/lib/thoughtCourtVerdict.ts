import type { CourtReport, CourtWeightKey, CourtWeights } from "./thoughtCourtTypes";

const keys: CourtWeightKey[] = ["self", "relationship", "change"];

export interface ThoughtVerdict {
  conflict: string;
  consensus: string[];
  divergences: string[];
  actions: string[];
  reservation: string;
  dominantKey: CourtWeightKey;
  weights: CourtWeights;
}

export function normalizeWeights(input: CourtWeights): CourtWeights {
  const safe = {
    self: Math.max(0, input.self),
    relationship: Math.max(0, input.relationship),
    change: Math.max(0, input.change),
  };
  const total = safe.self + safe.relationship + safe.change;
  if (total === 0) return { self: 34, relationship: 33, change: 33 };
  const self = Math.round((safe.self / total) * 100);
  const relationship = Math.round((safe.relationship / total) * 100);
  return { self, relationship, change: 100 - self - relationship };
}

export function buildVerdict(report: CourtReport, input: CourtWeights): ThoughtVerdict {
  const weights = normalizeWeights(input);
  const ranked = [...keys].sort((a, b) => weights[b] - weights[a]);
  return {
    conflict: report.conflict,
    consensus: [...report.consensus],
    divergences: [...report.divergences],
    actions: ranked.flatMap((key) => report.actions[key]),
    reservation: report.reservation,
    dominantKey: ranked[0],
    weights,
  };
}

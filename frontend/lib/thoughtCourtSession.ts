import type { CitationStatus, CourtEvidence, CourtSpeech } from "./thoughtCourtTypes";
import { normalizeBackendRound, normalizeDebateReport } from "./roundtableFlow";

export interface CourtGateway {
  startDebate(topic: string, sages: string[]): Promise<{ sessionId: string; topic: string; participants: string[] }>;
  streamRound(sessionId: string, onEvent: (event: any) => void): Promise<void>;
  intervene(sessionId: string, content: string, targetSage?: string): Promise<any>;
  stand(sessionId: string, stance: string, targetSage?: string): Promise<any>;
  mutualQuestion(sessionId: string, fromSage: string, toSage: string): Promise<any>;
  getReport(sessionId: string): Promise<any>;
}

export function createApiCourtGateway(api: any): CourtGateway {
  return {
    startDebate: (topic, sages) => api.startDebate(topic, sages),
    streamRound: (sessionId, onEvent) => api.debateStream(sessionId, "next-round", undefined, onEvent),
    intervene: (sessionId, content, targetSage) => api.interveneDebate(sessionId, content, targetSage),
    stand: (sessionId, stance, targetSage) => api.standDebate(sessionId, stance, targetSage),
    mutualQuestion: (sessionId, fromSage, toSage) => api.mutualQuestion(sessionId, fromSage, toSage),
    getReport: (sessionId) => api.getDebateReport(sessionId),
  };
}

function normalizeEvidence(sageId: string, citation: any, index: number): CourtEvidence | null {
  const original = citation.original || citation.text || "";
  const source = citation.source || "";
  if (!original || !source) return null;
  return {
    id: `live-${sageId}-${index}`,
    sageId,
    original,
    source,
    interpretation: citation.commentary || "该原文为当前观点提供思想依据。",
    boundary: "请结合现实情境判断，勿将单句经典当作强制命令。",
    verified: citation.verifiable !== false,
  };
}

export async function prepareLiveCourt(topic: string, sages: string[], gateway: CourtGateway, emit: (event: any) => void) {
  emit({ type: "REMOTE_LOADING" });
  const started = await gateway.startDebate(topic, sages);
  emit({ type: "REMOTE_STREAMING" });
  const evidence: CourtEvidence[] = [];
  const speeches: CourtSpeech[] = sages.map((sageId) => ({ sageId, position: "", content: "", evidenceIds: [], status: "waiting" }));
  await gateway.streamRound(started.sessionId, (event) => {
    if (event.type === "sage_end") {
      const sageId = event.sage_key;
      const target = speeches.find((speech) => speech.sageId === sageId);
      const normalized: CourtEvidence[] = (event.speech?.citations || [])
        .map((citation: any, index: number) => normalizeEvidence(sageId, citation, index))
        .filter((item: CourtEvidence | null): item is CourtEvidence => item !== null);
      evidence.push(...normalized);
      if (target) {
        target.content = event.speech?.content || "";
        target.evidenceIds = normalized.map((item) => item.id);
        target.status = "complete";
      }
    }
    if (event.type === "sage_error") {
      const target = speeches.find((speech) => speech.sageId === event.sage_key);
      if (target) target.status = "failed";
    }
    emit(event);
  });
  const verifiedCount = evidence.filter((item) => item.verified).length;
  const citationStatus: CitationStatus = verifiedCount === 0 ? "unavailable" : verifiedCount === evidence.length && speeches.every((item) => item.status === "complete") ? "verified" : "partial";
  return { sessionId: started.sessionId, topic: started.topic, participants: started.participants, evidence, speeches, citationStatus };
}

export async function runSecondRound(sessionId: string, gateway: CourtGateway, emit: (event: any) => void) {
  emit({ type: "REMOTE_STREAMING" });
  const events: any[] = [];
  await gateway.streamRound(sessionId, (event) => {
    events.push(event);
    emit(event);
  });
  return events;
}

export async function runIntervention(sessionId: string, content: string, targetSage: string | undefined, gateway: CourtGateway) {
  const result = await gateway.intervene(sessionId, content, targetSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function runStand(sessionId: string, stance: string, targetSage: string | undefined, gateway: CourtGateway) {
  const result = await gateway.stand(sessionId, stance, targetSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function runMutualQuestion(sessionId: string, fromSage: string, toSage: string, gateway: CourtGateway) {
  const result = await gateway.mutualQuestion(sessionId, fromSage, toSage);
  return result?.round ? normalizeBackendRound(result.round) : result;
}

export async function loadReport(sessionId: string, gateway: CourtGateway) {
  const result = await gateway.getReport(sessionId);
  return normalizeDebateReport(result?.report ?? result);
}

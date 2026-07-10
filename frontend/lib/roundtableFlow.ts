import type { Citation } from "./types";
import type { DebateClash, SageRoundSpeech } from "./roundtableData";

export interface DebateReportView {
  topic: string;
  consensus: string[];
  divergences: string[];
  recommendations: Array<{ sage: string; recommendation: string }>;
  summary: string;
  participatingSages: string[];
}

export interface RoundtableFlowState {
  speeches: SageRoundSpeech[];
  clashes: DebateClash[];
  activeSageId: string | null;
  currentSageIdx: number;
  report: DebateReportView | null;
}

export type RoundtablePhase = "select" | "debating" | "complete";

export interface DebateGraphNodeView {
  id: string;
  label: string;
  kind: string;
}

export interface DebateGraphTransitionView {
  fromNode: string;
  toNode: string;
  action: string;
}

export interface DebateGraphTraceView extends DebateGraphTransitionView {
  ok: boolean;
  detail?: string;
}

export interface DebateStateGraphView {
  sessionId: string;
  currentNode: string;
  nodes: DebateGraphNodeView[];
  transitions: DebateGraphTransitionView[];
  trace: DebateGraphTraceView[];
}

export interface GuestRosterItem {
  sageKey: string;
  sageName: string;
  era: string;
  coreThought: string;
  unlocked: boolean;
  collected: boolean;
  staying: boolean;
}

type BackendCitation = {
  id?: string;
  source?: string;
  original?: string;
  verifiable?: boolean;
  出处?: string;
  原文?: string;
};

type BackendSpeech = {
  sage_key?: string;
  sage_name?: string;
  round_number?: number;
  content?: string;
  vernacular?: string;
  quote?: string;
  source?: string;
  citations?: BackendCitation[];
  sentence_evidence?: BackendSentenceEvidence[];
  sentenceEvidence?: BackendSentenceEvidence[];
  target_sage?: string | null;
  is_guest?: boolean;
  confidence?: string;
};

type BackendSentenceEvidence = {
  sentence?: string;
  source?: string;
  original?: string;
  similarity?: number;
  verifiable?: boolean;
};

type BackendRound = {
  speeches?: BackendSpeech[];
  clashes?: any[];
};

type AutoGuestTriggerInput = {
  phase: RoundtablePhase;
  speechCount: number;
  guestCount: number;
  alreadyTriggered: boolean;
  randomValue: number;
};

const clashTypeMap: Record<string, DebateClash["type"]> = {
  agree: "agree",
  disagree: "disagree",
  extend: "extend",
  refute: "refute",
  reframe: "reframe",
};

export function createRoundtableFlowState(participants: string[]): RoundtableFlowState {
  return {
    speeches: participants.map((sageId) =>
      createSpeechSlot(sageId, 1)
    ),
    clashes: [],
    activeSageId: null,
    currentSageIdx: 0,
    report: null,
  };
}

export function createSpeechSlot(sageId: string, roundNumber: number): SageRoundSpeech {
  return {
    id: `${roundNumber}-${sageId}`,
    sageId,
    roundNumber,
    content: "",
    vernacular: "",
    quote: "无",
    source: "无",
    citations: [],
    sentenceEvidence: [],
    isStreaming: false,
    isComplete: false,
  };
}

export function normalizeBackendSpeech(speech: BackendSpeech): SageRoundSpeech {
  const sageId = speech.sage_key || "unknown";
  const roundNumber = speech.round_number || 1;
  return {
    id: speech.is_guest ? `${roundNumber}-${sageId}-guest` : `${roundNumber}-${sageId}`,
    sageId,
    roundNumber,
    content: speech.content || "",
    vernacular: speech.vernacular || "",
    quote: speech.quote || "无",
    source: speech.source || "无",
    citations: normalizeCitations(speech.citations || []),
    sentenceEvidence: normalizeSentenceEvidence(speech.sentence_evidence || speech.sentenceEvidence || []),
    isStreaming: false,
    isComplete: true,
    isGuest: Boolean(speech.is_guest),
  };
}

export function normalizeSentenceEvidence(evidence: BackendSentenceEvidence[]) {
  return evidence
    .map((item) => ({
      sentence: item.sentence || "",
      source: item.source || "无",
      original: item.original || "无",
      similarity: Number(item.similarity || 0),
      verifiable: Boolean(item.verifiable),
    }))
    .filter((item) => item.sentence);
}

export function normalizeCitations(citations: BackendCitation[]): Citation[] {
  return citations
    .map((citation) => {
      const text = citation.original || citation.原文 || "";
      const source = citation.source || citation.出处 || "未知出处";
      return {
        text,
        source,
        chapter: source,
        verse_no: undefined,
        similarity: citation.verifiable === false ? 0 : 1,
        type: "verse" as const,
      };
    })
    .filter((citation) => citation.text && citation.text !== "无");
}

export function normalizeBackendClash(clash: any): DebateClash {
  const rawType = String(clash?.clash_type || clash?.type || "extend");
  return {
    fromSageId: clash?.from_sage || clash?.fromSageId || "",
    toSageId: clash?.to_sage || clash?.toSageId || "",
    type: clashTypeMap[rawType] || "extend",
    summary: clash?.summary || "",
  };
}

export function normalizeBackendRound(round: BackendRound): Pick<RoundtableFlowState, "speeches" | "clashes"> {
  return {
    speeches: Array.isArray(round?.speeches) ? round.speeches.map(normalizeBackendSpeech) : [],
    clashes: Array.isArray(round?.clashes) ? round.clashes.map(normalizeBackendClash) : [],
  };
}

export function normalizeDebateReport(report: any): DebateReportView {
  return {
    topic: report?.topic || "",
    consensus: Array.isArray(report?.consensus) ? report.consensus : [],
    divergences: Array.isArray(report?.divergences) ? report.divergences : [],
    recommendations: Array.isArray(report?.recommendations) ? report.recommendations : [],
    summary: report?.summary || "",
    participatingSages: report?.participating_sages || report?.participatingSages || [],
  };
}

export function normalizeDebateStateGraph(raw: any): DebateStateGraphView {
  return {
    sessionId: raw?.session_id || raw?.sessionId || "",
    currentNode: raw?.current_node || raw?.currentNode || "init",
    nodes: Array.isArray(raw?.nodes)
      ? raw.nodes.map((node: any) => ({
          id: node?.id || "",
          label: node?.label || node?.id || "",
          kind: node?.kind || "unknown",
        }))
      : [],
    transitions: Array.isArray(raw?.transitions)
      ? raw.transitions.map((transition: any) => ({
          fromNode: transition?.from_node || transition?.fromNode || "",
          toNode: transition?.to_node || transition?.toNode || "",
          action: transition?.action || "",
        }))
      : [],
    trace: Array.isArray(raw?.trace)
      ? raw.trace.map((trace: any) => ({
          fromNode: trace?.from_node || trace?.fromNode || "",
          toNode: trace?.to_node || trace?.toNode || "",
          action: trace?.action || "",
          ok: Boolean(trace?.ok),
          detail: trace?.detail,
        }))
      : [],
  };
}

export function normalizeGuestRoster(guests: any[]): GuestRosterItem[] {
  return (Array.isArray(guests) ? guests : []).map((guest) => ({
    sageKey: guest?.sage_key || guest?.sageKey || "",
    sageName: guest?.sage_name || guest?.sageName || guest?.name || "",
    era: guest?.era || "",
    coreThought: guest?.core_thought || guest?.coreThought || guest?.specialty || "",
    unlocked: Boolean(guest?.unlocked),
    collected: Boolean(guest?.collected),
    staying: Boolean(guest?.staying),
  })).filter((guest) => guest.sageKey);
}

export function shouldAutoTriggerGuest({
  phase,
  speechCount,
  guestCount,
  alreadyTriggered,
  randomValue,
}: AutoGuestTriggerInput): boolean {
  return (
    phase === "complete" &&
    speechCount >= 4 &&
    guestCount === 0 &&
    !alreadyTriggered &&
    randomValue < 0.35
  );
}

export function canUseInterventionBar(phase: RoundtablePhase, sessionId: string | null): boolean {
  return Boolean(sessionId) && (phase === "debating" || phase === "complete");
}

export function shouldQueueIntervention(phase: RoundtablePhase, autoDebateActive = true): boolean {
  return phase === "debating" && autoDebateActive;
}

export function appendOrReplaceSpeech(
  speeches: SageRoundSpeech[],
  speech: SageRoundSpeech
): SageRoundSpeech[] {
  const idx = speeches.findIndex((item) => item.id === speech.id);
  if (idx === -1) return [...speeches, speech];
  return speeches.map((item, itemIdx) => (itemIdx === idx ? speech : item));
}

export function applyDebateStreamEvent(
  state: RoundtableFlowState,
  event: any
): RoundtableFlowState {
  if (!event || typeof event !== "object") return state;

  if (event.type === "sage_start" || event.type === "speech_start") {
    const sageId = event.sage_key || event.sageId;
    const roundNumber = event.round || 1;
    const existingIdx = state.speeches.findIndex(
      (speech) => speech.sageId === sageId && speech.roundNumber === roundNumber
    );
    const speeches =
      existingIdx === -1
        ? [...state.speeches, { ...createSpeechSlot(sageId, roundNumber), isStreaming: true }]
        : state.speeches.map((speech, idx) =>
            idx === existingIdx ? { ...speech, isStreaming: true, isComplete: false } : speech
          );
    return {
      ...state,
      speeches,
      activeSageId: sageId,
      currentSageIdx: Math.max(existingIdx, 0),
    };
  }

  if (event.type === "sage_chunk" || event.type === "content") {
    const sageId = event.sage_key || event.sageId;
    const content = event.content || "";
    const idx = findActiveSpeechIndex(state.speeches, sageId);
    if (idx === -1) return state;
    return {
      ...state,
      speeches: state.speeches.map((speech, speechIdx) =>
        speechIdx === idx ? { ...speech, content: speech.content + content } : speech
      ),
    };
  }

  if (event.type === "sage_end" || event.type === "speech_end") {
    const speech = event.speech
      ? normalizeBackendSpeech(event.speech)
      : normalizeBackendSpeech({
          sage_key: event.sage_key,
          round_number: event.round,
          content: event.content,
          citations: event.citations,
        });
    return {
      ...state,
      speeches: appendOrReplaceSpeech(state.speeches, speech),
      activeSageId: null,
    };
  }

  if (event.type === "round_done") {
    const clashes = Array.isArray(event.clashes)
      ? event.clashes.map(normalizeBackendClash)
      : state.clashes;
    return {
      ...state,
      clashes: mergeClashes(state.clashes, clashes),
      activeSageId: null,
    };
  }

  if (event.type === "clashes") {
    return {
      ...state,
      clashes: mergeClashes(state.clashes, (event.clashes || []).map(normalizeBackendClash)),
    };
  }

  if (event.type === "report") {
    return {
      ...state,
      report: normalizeDebateReport(event.report),
      activeSageId: null,
    };
  }

  return state;
}

function findActiveSpeechIndex(speeches: SageRoundSpeech[], sageId: string): number {
  for (let idx = speeches.length - 1; idx >= 0; idx -= 1) {
    const speech = speeches[idx];
    if (speech.sageId === sageId && speech.isStreaming) return idx;
  }
  return speeches.findIndex((speech) => speech.sageId === sageId && !speech.isComplete);
}

function mergeClashes(existing: DebateClash[], incoming: DebateClash[]): DebateClash[] {
  const seen = new Set(existing.map(clashKey));
  const merged = [...existing];
  for (const clash of incoming) {
    const key = clashKey(clash);
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(clash);
    }
  }
  return merged;
}

function clashKey(clash: DebateClash): string {
  return `${clash.fromSageId}->${clash.toSageId}:${clash.type}:${clash.summary}`;
}

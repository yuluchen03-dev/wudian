"use client";

import { useCallback, useMemo, useReducer, useRef, useState } from "react";
import { createCourtState, transitionCourt } from "@/lib/thoughtCourtState";
import {
  createApiCourtGateway,
  prepareLiveCourt,
  runSecondRound,
  loadReport,
  runIntervention,
  runStand,
  runMutualQuestion,
} from "@/lib/thoughtCourtSession";
import { api } from "@/lib/api";
import type {
  CourtClash,
  CourtEvidence,
  CourtMotionMode,
  CourtReport,
  CourtSound,
  CourtSpeech,
  CourtWeights,
  CuratedCourtCase,
} from "@/lib/thoughtCourtTypes";

const SAGE_ORDER = ["confucius", "mencius", "laozi"];

function debateReportToCourtReport(raw: any): CourtReport {
  const recommendations: string[] = Array.isArray(raw?.recommendations)
    ? raw.recommendations
        .map((r: any) => (typeof r === "string" ? r : r?.recommendation || r?.text || ""))
        .filter(Boolean)
    : [];
  return {
    conflict: raw?.conflict || raw?.topic || "",
    consensus: Array.isArray(raw?.consensus) ? raw.consensus : [],
    divergences: Array.isArray(raw?.divergences) ? raw.divergences : [],
    actions:
      raw?.actions || {
        self: recommendations.slice(0, 1),
        relationship: recommendations.slice(1, 2),
        change: recommendations.slice(2),
      },
    reservation: raw?.reservation || raw?.summary || "",
  };
}

export function useThoughtCourt() {
  const [state, dispatch] = useReducer(transitionCourt, undefined, createCourtState);
  const [evidence, setEvidence] = useState<CourtEvidence[]>([]);
  const [speeches, setSpeeches] = useState<CourtSpeech[]>([]);
  const [clashes, setClashes] = useState<CourtClash[]>([]);
  const [report, setReport] = useState<CourtReport | null>(null);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [activeSageId, setActiveSageId] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const liveSessionIdRef = useRef<string | null>(null);
  const bufferedSpeechesRef = useRef<CourtSpeech[]>([]);
  const revealTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const gateway = useMemo(() => createApiCourtGateway(api), []);

  const clearRevealTimers = useCallback(() => {
    revealTimersRef.current.forEach((timer) => clearTimeout(timer));
    revealTimersRef.current = [];
  }, []);

  const setMotion = useCallback((motion: CourtMotionMode) => dispatch({ type: "SET_MOTION", motion }), []);
  const setSound = useCallback((sound: CourtSound) => dispatch({ type: "SET_SOUND", sound }), []);

  const reset = useCallback(() => {
    clearRevealTimers();
    setEvidence([]);
    setSpeeches([]);
    setClashes([]);
    setReport(null);
    setSelectedEvidenceIds([]);
    setActiveSageId(null);
    setActionBusy(false);
    liveSessionIdRef.current = null;
    bufferedSpeechesRef.current = [];
    dispatch({ type: "RESET" });
  }, [clearRevealTimers]);

  const selectCase = useCallback((caseId: string) => {
    dispatch({ type: "SELECT_CASE", caseId });
  }, []);

  const chooseLive = useCallback(() => {
    dispatch({ type: "SET_LIVE_QUESTION" });
  }, []);

  const submitCase = useCallback((question: string, curated?: CuratedCourtCase) => {
    if (!question.trim()) return;
    dispatch({ type: "SUBMIT_CASE", question });

    if (curated) {
      const evidenceIds = curated.evidence.map((item) => item.id);
      setEvidence(curated.evidence);
      setSpeeches([]);
      setClashes(curated.clashes);
      setReport(curated.report);
      setSelectedEvidenceIds(evidenceIds);
      bufferedSpeechesRef.current = curated.speeches;
      requestAnimationFrame(() => {
        dispatch({ type: "RETRIEVAL_SUCCEEDED", evidenceIds, citationStatus: "verified" });
      });
    }
  }, []);

  const submitLive = useCallback(
    async (question: string, sages: string[]) => {
      if (!question.trim()) return;
      dispatch({ type: "SUBMIT_CASE", question });
      try {
        const result = await prepareLiveCourt(question, sages, gateway, (event) => {
          if (event.type === "REMOTE_LOADING" || event.type === "REMOTE_STREAMING") {
            dispatch(event);
          }
        });
        setEvidence(result.evidence);
        setSpeeches([]);
        setClashes([]);
        setReport(null);
        setSelectedEvidenceIds(result.evidence.map((item) => item.id));
        bufferedSpeechesRef.current = result.speeches;
        liveSessionIdRef.current = result.sessionId;
        const evidenceIds = result.evidence.map((item) => item.id);
        dispatch({ type: "RETRIEVAL_SUCCEEDED", evidenceIds, citationStatus: result.citationStatus });
      } catch (err) {
        dispatch({ type: "REMOTE_FAILED", message: err instanceof Error ? err.message : "检索失败" });
      }
    },
    [gateway]
  );

  const toggleEvidence = useCallback((evidenceId: string) => {
    setSelectedEvidenceIds((prev) =>
      prev.includes(evidenceId) ? prev.filter((id) => id !== evidenceId) : [...prev, evidenceId]
    );
  }, []);

  const beginDebate = useCallback(() => {
    dispatch({ type: "BEGIN_DEBATE" });
    const buffered = bufferedSpeechesRef.current;

    if (liveSessionIdRef.current) {
      setSpeeches([...buffered]);
      setActionBusy(true);
      runSecondRound(liveSessionIdRef.current, gateway, () => {})
        .then(async () => {
          const raw = await loadReport(liveSessionIdRef.current!, gateway);
          setReport(debateReportToCourtReport(raw));
          setActionBusy(false);
        })
        .catch(() => {
          setActionBusy(false);
          dispatch({ type: "REMOTE_FAILED", message: "第二轮辩论失败" });
        });
    } else {
      clearRevealTimers();
      const delay = state.motion === "reduced" || state.motion === "degraded" ? 0 : 400;
      const ordered = SAGE_ORDER.map((sageId) => buffered.find((s) => s.sageId === sageId)).filter(
        (s): s is CourtSpeech => Boolean(s)
      );
      setSpeeches([]);
      ordered.forEach((speech, index) => {
        const timer = setTimeout(() => {
          setActiveSageId(speech.sageId);
          setSpeeches((prev) => [...prev, speech]);
          if (index === ordered.length - 1) {
            setActiveSageId(null);
            dispatch({ type: "DEBATE_SUCCEEDED" });
          }
        }, delay * (index + 1));
        revealTimersRef.current.push(timer);
      });
    }
  }, [gateway, clearRevealTimers, state.motion]);

  const followUp = useCallback(
    async (content: string, targetSageId: string) => {
      if (!liveSessionIdRef.current) return;
      setActionBusy(true);
      setActiveSageId(targetSageId);
      try {
        await runIntervention(liveSessionIdRef.current, content, targetSageId, gateway);
        const raw = await loadReport(liveSessionIdRef.current, gateway);
        setReport(debateReportToCourtReport(raw));
      } catch {
        dispatch({ type: "REMOTE_FAILED", message: "追问失败" });
      } finally {
        setActionBusy(false);
        setActiveSageId(null);
      }
    },
    [gateway]
  );

  const mutualQuestion = useCallback(
    async (fromSageId: string, toSageId: string) => {
      if (!liveSessionIdRef.current) return;
      setActionBusy(true);
      setActiveSageId(fromSageId);
      try {
        await runMutualQuestion(liveSessionIdRef.current, fromSageId, toSageId, gateway);
        const raw = await loadReport(liveSessionIdRef.current, gateway);
        setReport(debateReportToCourtReport(raw));
      } catch {
        dispatch({ type: "REMOTE_FAILED", message: "互问失败" });
      } finally {
        setActionBusy(false);
        setActiveSageId(null);
      }
    },
    [gateway]
  );

  const chooseStance = useCallback(
    async (stance: string, targetSageId: string) => {
      if (!liveSessionIdRef.current) return;
      setActionBusy(true);
      setActiveSageId(targetSageId);
      try {
        await runStand(liveSessionIdRef.current, stance, targetSageId, gateway);
        const raw = await loadReport(liveSessionIdRef.current, gateway);
        setReport(debateReportToCourtReport(raw));
      } catch {
        dispatch({ type: "REMOTE_FAILED", message: "表明立场失败" });
      } finally {
        setActionBusy(false);
        setActiveSageId(null);
      }
    },
    [gateway]
  );

  const buildVerdict = useCallback(() => {
    if (state.phase === "debate") {
      dispatch({ type: "DEBATE_SUCCEEDED" });
    } else if (state.phase === "weighting") {
      dispatch({ type: "BUILD_VERDICT" });
    }
  }, [state.phase]);

  const setWeights = useCallback((weights: CourtWeights) => {
    dispatch({ type: "SET_WEIGHTS", weights });
  }, []);

  const complete = useCallback(() => {
    dispatch({ type: "COMPLETE" });
  }, []);

  return {
    state,
    evidence,
    speeches,
    clashes,
    report,
    selectedEvidenceIds,
    activeSageId,
    busy: actionBusy,
    setMotion,
    setSound,
    reset,
    selectCase,
    chooseLive,
    submitCase,
    submitLive,
    toggleEvidence,
    beginDebate,
    followUp,
    mutualQuestion,
    chooseStance,
    buildVerdict,
    setWeights,
    complete,
  };
}

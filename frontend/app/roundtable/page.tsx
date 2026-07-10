"use client";

import { Suspense, useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, GitCompareArrows, Send, MessageSquareQuote, ShieldCheck } from "lucide-react";
import clsx from "clsx";
import type { Sage } from "@/lib/types";
import { mockSages } from "@/lib/sageData";
import { api } from "@/lib/api";
import {
  getMockDebateData,
  type SageRoundSpeech,
  type DebateClash,
} from "@/lib/roundtableData";
import {
  applyDebateStreamEvent,
  canUseInterventionBar,
  createRoundtableFlowState,
  normalizeBackendRound,
  normalizeBackendSpeech,
  normalizeDebateReport,
  shouldAutoTriggerGuest,
  shouldQueueIntervention,
  type DebateStateGraphView,
  type GuestRosterItem,
  type DebateReportView,
  type RoundtablePhase,
  type RoundtableFlowState,
} from "@/lib/roundtableFlow";
import { analyzeThoughtCompass, type ThoughtCompassMark } from "@/lib/thoughtCompass";

import RoundTableHeader from "@/components/roundtable/RoundTableHeader";
import TopicSelector from "@/components/roundtable/TopicSelector";
import SageAvatars from "@/components/roundtable/SageAvatars";
import DebateTimeline from "@/components/roundtable/DebateTimeline";
import CitationPanel from "@/components/roundtable/CitationPanel";
import DebateSummary from "@/components/roundtable/DebateSummary";
import GuestSummoner from "@/components/roundtable/GuestSummoner";
import ThoughtCompass from "@/components/roundtable/ThoughtCompass";
import ModeratorStateGraph from "@/components/roundtable/ModeratorStateGraph";
import { pageBackgrounds } from "@/lib/visualAssets";

type Phase = RoundtablePhase;
const DEFAULT_PARTICIPANTS = ["confucius", "laozi", "mozi", "hanfeizi"];

type PendingIntervention = {
  content: string;
  targetSageId?: string;
  asParticipant: boolean;
};

export default function RoundTablePage() {
  return (
    <Suspense fallback={null}>
      <RoundTableExperience />
    </Suspense>
  );
}

function RoundTableExperience() {
  const searchParams = useSearchParams();
  const demoMode = searchParams.get("demo");
  const [phase, setPhase] = useState<Phase>("select");
  const [topic, setTopic] = useState("");
  const [speeches, setSpeeches] = useState<SageRoundSpeech[]>([]);
  const [clashes, setClashes] = useState<DebateClash[]>([]);
  const [activeSageId, setActiveSageId] = useState<string | null>(null);
  const [currentSageIdx, setCurrentSageIdx] = useState(0);
  const [participants, setParticipants] = useState<string[]>(DEFAULT_PARTICIPANTS);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [report, setReport] = useState<DebateReportView | null>(null);
  const [interventionText, setInterventionText] = useState("");
  const [thoughtMark, setThoughtMark] = useState<ThoughtCompassMark | null>(null);
  const [targetSageId, setTargetSageId] = useState<string>("confucius");
  const [mutualFromSageId, setMutualFromSageId] = useState<string>("confucius");
  const [mutualToSageId, setMutualToSageId] = useState<string>("laozi");
  const [isIntervening, setIsIntervening] = useState(false);
  const [isSummoning, setIsSummoning] = useState(false);
  const [queuedInterventionCount, setQueuedInterventionCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [graphState, setGraphState] = useState<DebateStateGraphView | null>(null);
  const [guestRoster, setGuestRoster] = useState<GuestRosterItem[]>([]);
  const [guestCue, setGuestCue] = useState<string | null>(null);
  const flowStateRef = useRef<RoundtableFlowState>(createRoundtableFlowState(DEFAULT_PARTICIPANTS));
  const pendingInterventionsRef = useRef<PendingIntervention[]>([]);
  const autoDebateActiveRef = useRef(false);
  const autoGuestTriggeredRef = useRef(false);

  const sageMap = useMemo(() => Object.fromEntries(mockSages.map((sage) => [sage.id, sage])), []);
  const sages: Sage[] = useMemo(
    () => participants.map((id) => sageMap[id]).filter(Boolean),
    [participants, sageMap]
  );
  const sageNames = useMemo(() => Object.fromEntries(sages.map((s) => [s.id, s.name])), [sages]);

  const syncFlowState = useCallback((state: RoundtableFlowState) => {
    flowStateRef.current = state;
    setSpeeches(state.speeches);
    setClashes(state.clashes);
    setActiveSageId(state.activeSageId);
    setCurrentSageIdx(state.currentSageIdx);
    if (state.report) setReport(state.report);
  }, []);

  const applyStreamToState = useCallback(
    (event: any) => {
      const nextState = applyDebateStreamEvent(flowStateRef.current, event);
      syncFlowState(nextState);
    },
    [syncFlowState]
  );

  const refreshGraphState = useCallback(async (sid: string) => {
    try {
      setGraphState(await api.getDebateStateGraph(sid));
    } catch {
      setGraphState(null);
    }
  }, []);

  const refreshGuestRoster = useCallback(async () => {
    try {
      setGuestRoster(await api.getGuestRoster());
    } catch {
      setGuestRoster([]);
    }
  }, []);

  useEffect(() => {
    void refreshGuestRoster();
  }, [refreshGuestRoster]);

  const runDebateStream = useCallback(
    async (sid: string) => {
      await api.debateStream(sid, "next-round", undefined, (data) => {
        applyStreamToState(data);
      });
      await refreshGraphState(sid);
    },
    [applyStreamToState, refreshGraphState]
  );

  const enqueueIntervention = useCallback((intervention: PendingIntervention) => {
    pendingInterventionsRef.current = [...pendingInterventionsRef.current, intervention];
    setQueuedInterventionCount(pendingInterventionsRef.current.length);
  }, []);

  const markThoughtCompass = useCallback(async (content: string) => {
    try {
      setThoughtMark(await api.analyzeThoughtCompass(content));
    } catch {
      setThoughtMark(analyzeThoughtCompass(content));
    }
  }, []);

  const runIntervention = useCallback(
    async (sid: string, intervention: PendingIntervention, refreshReport: boolean) => {
      const payload = {
        content: intervention.asParticipant ? `【论主入席】${intervention.content}` : intervention.content,
        target_sage: intervention.targetSageId || undefined,
      };
      if (intervention.asParticipant) {
        await markThoughtCompass(intervention.content);
      }
      await api.debateStream(sid, "intervene", payload, applyStreamToState);
      await refreshGraphState(sid);
      if (refreshReport) {
        const reportResult = await api.getDebateReport(sid);
        setReport(normalizeDebateReport(reportResult.report));
      }
    },
    [applyStreamToState, markThoughtCompass, refreshGraphState]
  );

  const drainQueuedInterventions = useCallback(
    async (sid: string) => {
      if (pendingInterventionsRef.current.length === 0) return;
      setIsIntervening(true);
      try {
        while (pendingInterventionsRef.current.length > 0) {
          const intervention = pendingInterventionsRef.current.shift();
          setQueuedInterventionCount(pendingInterventionsRef.current.length);
          if (intervention) {
            await runIntervention(sid, intervention, false);
          }
        }
      } finally {
        setIsIntervening(false);
      }
    },
    [runIntervention]
  );

  const loadCompleteDemo = useCallback(() => {
    const demoSessionId = "demo-complete";
    const demoTopic = "我很努力但总不被领导认可，怎么办？";
    const mockData = getMockDebateData(demoTopic);
    const uniqueSpeechSageIds = Array.from(new Set(mockData.speeches.map((speech) => speech.sageId))).slice(0, 4);
    const demoParticipants = uniqueSpeechSageIds.length >= 4 ? uniqueSpeechSageIds : DEFAULT_PARTICIPANTS;
    const completeSpeeches = mockData.speeches.map((speech) => ({
      ...speech,
      isStreaming: false,
      isComplete: true,
      citations: speech.citations,
    }));
    const participatingSages = demoParticipants.map((sageId) => sageMap[sageId]?.name || sageId);
    const report: DebateReportView = {
      topic: demoTopic,
      consensus: [
        "先把努力从“被看见”转成“可验证的成果”，再用稳定沟通争取评价口径。",
      ],
      divergences: [
        "儒家重在修身与沟通，法家重在规则与奖惩，道家提醒放下执念，墨家强调可见贡献。",
      ],
      recommendations: completeSpeeches.slice(0, 4).map((speech) => ({
        sage: sageMap[speech.sageId]?.name || speech.sageId,
        recommendation: speech.content.slice(0, 48),
      })),
      summary: "这是黑客松兜底完成态：百家已围绕职场认可问题完成发言、交锋、引用展示和主持 Agent 状态图。",
      participatingSages,
    };
    const graphState: DebateStateGraphView = {
      sessionId: demoSessionId,
      currentNode: "done",
      nodes: [
        { id: "init", label: "开场", kind: "start" },
        { id: "round1", label: "第一轮", kind: "debate" },
        { id: "round2", label: "第二轮", kind: "debate" },
        { id: "intervention", label: "论主介入", kind: "human" },
        { id: "report", label: "会诊报告", kind: "report" },
        { id: "done", label: "完成", kind: "done" },
      ],
      transitions: [
        { fromNode: "init", toNode: "round1", action: "start" },
        { fromNode: "round1", toNode: "round2", action: "next-round" },
        { fromNode: "round2", toNode: "intervention", action: "queue-intervention" },
        { fromNode: "intervention", toNode: "report", action: "report" },
        { fromNode: "report", toNode: "done", action: "complete" },
      ],
      trace: [
        { fromNode: "init", toNode: "round1", action: "start", ok: true, detail: "demo bootstrap" },
        { fromNode: "round1", toNode: "round2", action: "next-round", ok: true, detail: "mock speeches loaded" },
        { fromNode: "round2", toNode: "intervention", action: "queue-intervention", ok: true, detail: "preview skips wait" },
        { fromNode: "intervention", toNode: "report", action: "report", ok: true, detail: "summary prepared" },
        { fromNode: "report", toNode: "done", action: "complete", ok: true, detail: "ready for live fallback" },
      ],
    };

    setTopic(demoTopic);
    setPhase("complete");
    setSessionId(demoSessionId);
    setParticipants(demoParticipants);
    setTargetSageId(demoParticipants[0] || "confucius");
    setMutualFromSageId(demoParticipants[0] || "confucius");
    setMutualToSageId(demoParticipants[1] || demoParticipants[0] || "laozi");
    setReport(report);
    setThoughtMark(null);
    setGraphState(graphState);
    setGuestCue(null);
    pendingInterventionsRef.current = [];
    autoDebateActiveRef.current = false;
    autoGuestTriggeredRef.current = false;
    setQueuedInterventionCount(0);
    setInterventionText("");
    setIsIntervening(false);
    setIsSummoning(false);
    setError(null);
    syncFlowState({
      speeches: completeSpeeches,
      clashes: mockData.clashes,
      activeSageId: null,
      currentSageIdx: 0,
      report,
    });
  }, [sageMap, syncFlowState]);

  useEffect(() => {
    if (demoMode === "complete") {
      loadCompleteDemo();
    }
  }, [demoMode, loadCompleteDemo]);

  const handleTopicSelect = useCallback(
    async (selectedTopic: string) => {
      setTopic(selectedTopic);
      setPhase("debating");
      setSpeeches([]);
      setClashes([]);
      setCurrentSageIdx(0);
      setParticipants(DEFAULT_PARTICIPANTS);
      setReport(null);
      setThoughtMark(null);
      setGraphState(null);
      setGuestCue(null);
      pendingInterventionsRef.current = [];
      autoDebateActiveRef.current = true;
      autoGuestTriggeredRef.current = false;
      setQueuedInterventionCount(0);
      setError(null);

      try {
        // 1. 开始辩论会话
        const startResult = await api.startDebate(selectedTopic, DEFAULT_PARTICIPANTS);
        setSessionId(startResult.sessionId);
        setParticipants(startResult.participants);
        await refreshGraphState(startResult.sessionId);
        await refreshGuestRoster();
        setTargetSageId(startResult.participants[0] || "confucius");
        setMutualFromSageId(startResult.participants[0] || "confucius");
        setMutualToSageId(startResult.participants[1] || startResult.participants[0] || "laozi");

        // 2. 初始化圣贤发言占位
        syncFlowState(createRoundtableFlowState(startResult.participants));

        // 3. 依次执行第一轮、第二轮、会诊报告
        await runDebateStream(startResult.sessionId);
        await runDebateStream(startResult.sessionId);
        await drainQueuedInterventions(startResult.sessionId);
        autoDebateActiveRef.current = false;
        const reportResult = await api.getDebateReport(startResult.sessionId);
        if (pendingInterventionsRef.current.length > 0) {
          await drainQueuedInterventions(startResult.sessionId);
          const refreshedReportResult = await api.getDebateReport(startResult.sessionId);
          setReport(normalizeDebateReport(refreshedReportResult.report));
        } else {
          setReport(normalizeDebateReport(reportResult.report));
        }

        setActiveSageId(null);
        setPhase("complete");
      } catch (err) {
        autoDebateActiveRef.current = false;
        console.error("辩论启动失败:", err);
        setError(err instanceof Error ? err.message : "辩论启动失败，请重试");
        // 回退到Mock数据
        const mockData = getMockDebateData(selectedTopic);
        const initialSpeeches: SageRoundSpeech[] = mockData.speeches.map((s) => ({
          ...s,
          content: "",
          citations: [],
          isStreaming: false,
          isComplete: false,
        }));
        syncFlowState({
          speeches: initialSpeeches,
          clashes: [],
          activeSageId: null,
          currentSageIdx: 0,
          report: null,
        });

        for (let i = 0; i < mockData.speeches.length; i++) {
          const sageId = mockData.speeches[i].sageId;
          setActiveSageId(sageId);
          setCurrentSageIdx(i);

          setSpeeches((prev) =>
            prev.map((s, idx) => (idx === i ? { ...s, isStreaming: true } : s))
          );

          const fullContent = mockData.speeches[i].content;
          const chunkSize = 3;
          for (let j = 0; j < fullContent.length; j += chunkSize) {
            await new Promise((r) => setTimeout(r, 25));
            setSpeeches((prev) =>
              prev.map((s, idx) =>
                idx === i
                  ? { ...s, content: fullContent.slice(0, j + chunkSize) }
                  : s
              )
            );
          }

          setSpeeches((prev) =>
            prev.map((s, idx) =>
              idx === i
                ? {
                    ...s,
                    content: fullContent,
                    citations: mockData.speeches[i].citations,
                    isStreaming: false,
                    isComplete: true,
                  }
                : s
            )
          );

          if (i < mockData.speeches.length - 1) {
            await new Promise((r) => setTimeout(r, 500));
          }
        }

        setClashes(mockData.clashes);
        setReport({
          topic: selectedTopic,
          consensus: ["消极放弃不可取，各家都要求论主重新辨明处境。"],
          divergences: ["儒法偏向有为进取，道家偏向顺势守静，墨家强调强力实践。"],
          recommendations: mockData.speeches.slice(0, 4).map((speech) => ({
            sage: sageMap[speech.sageId]?.name || speech.sageId,
            recommendation: speech.content.slice(0, 42),
          })),
          summary: "这是离线兜底会诊：保留多家分歧，并将论道收束为可执行建议。",
          participatingSages: mockData.speeches.map((speech) => sageMap[speech.sageId]?.name || speech.sageId),
        });
        setActiveSageId(null);
        setPhase("complete");
      }
    },
    [drainQueuedInterventions, refreshGraphState, refreshGuestRoster, runDebateStream, sageMap, syncFlowState]
  );

  const handleNewTopic = useCallback(() => {
    setPhase("select");
    setTopic("");
    setSpeeches([]);
    setClashes([]);
    setActiveSageId(null);
    setCurrentSageIdx(0);
    setParticipants(DEFAULT_PARTICIPANTS);
    setSessionId(null);
    setReport(null);
    setThoughtMark(null);
    setGraphState(null);
    setGuestCue(null);
    flowStateRef.current = createRoundtableFlowState(DEFAULT_PARTICIPANTS);
    pendingInterventionsRef.current = [];
    autoDebateActiveRef.current = false;
    autoGuestTriggeredRef.current = false;
    setQueuedInterventionCount(0);
    setInterventionText("");
    setMutualFromSageId("confucius");
    setMutualToSageId("laozi");
    setIsIntervening(false);
    setIsSummoning(false);
    setError(null);
  }, []);

  const handleIntervention = useCallback(
    async (asParticipant = false) => {
      const content = interventionText.trim();
      if (!sessionId || !content) return;
      const intervention: PendingIntervention = {
        content,
        targetSageId: targetSageId || undefined,
        asParticipant,
      };
      if (shouldQueueIntervention(phase, autoDebateActiveRef.current)) {
        if (asParticipant) {
          void markThoughtCompass(content);
        }
        enqueueIntervention(intervention);
        setInterventionText("");
        return;
      }
      setIsIntervening(true);
      setError(null);
      try {
        await runIntervention(sessionId, intervention, true);
        setInterventionText("");
      } catch (err) {
        setError(err instanceof Error ? err.message : "追问失败，请稍后重试");
      } finally {
        setIsIntervening(false);
      }
    },
    [enqueueIntervention, interventionText, markThoughtCompass, phase, runIntervention, sessionId, targetSageId]
  );

  const handleStand = useCallback(async () => {
    const stance = interventionText.trim();
    if (!sessionId || !stance) return;
    if (phase !== "complete") {
      setError("请等本轮论道结束后再站队");
      return;
    }
    setIsIntervening(true);
    setError(null);
    try {
      const result = await api.standDebate(sessionId, stance, targetSageId || undefined);
      const normalizedRound = normalizeBackendRound(result.round);
      const nextSpeeches = normalizedRound.speeches.length
        ? normalizedRound.speeches
        : [normalizeBackendSpeech(result.speech)];
      syncFlowState({
        ...flowStateRef.current,
        speeches: [...flowStateRef.current.speeches, ...nextSpeeches],
        clashes: [...flowStateRef.current.clashes, ...normalizedRound.clashes],
        activeSageId: null,
        report: null,
      });
      setInterventionText("");
      const reportResult = await api.getDebateReport(sessionId);
      setReport(normalizeDebateReport(reportResult.report));
      await refreshGraphState(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "站队失败，请稍后重试");
    } finally {
      setIsIntervening(false);
    }
  }, [interventionText, phase, refreshGraphState, sessionId, syncFlowState, targetSageId]);

  const handleMutualQuestion = useCallback(async () => {
    if (!sessionId || mutualFromSageId === mutualToSageId) return;
    if (phase !== "complete") {
      setError("请等本轮论道结束后再请其互问");
      return;
    }
    setIsIntervening(true);
    setError(null);
    try {
      const result = await api.mutualQuestion(sessionId, mutualFromSageId, mutualToSageId);
      const normalizedRound = normalizeBackendRound(result.round);
      syncFlowState({
        ...flowStateRef.current,
        speeches: [...flowStateRef.current.speeches, ...normalizedRound.speeches],
        clashes: [...flowStateRef.current.clashes, ...normalizedRound.clashes],
        activeSageId: null,
        report: null,
      });
      const reportResult = await api.getDebateReport(sessionId);
      setReport(normalizeDebateReport(reportResult.report));
      await refreshGraphState(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "互问失败，请稍后重试");
    } finally {
      setIsIntervening(false);
    }
  }, [mutualFromSageId, mutualToSageId, phase, refreshGraphState, sessionId, syncFlowState]);

  const handleSummonGuest = useCallback(
    async (guestKey: string) => {
      if (!sessionId) {
        console.error("没有活跃的辩论会话");
        return;
      }

      try {
        setIsSummoning(true);
        // 调用真实API召唤踢馆名人
        const result = await api.summonGuest(sessionId, guestKey);

        // 添加到发言列表
        const guestSpeech = normalizeBackendSpeech(result.speech || { sage_key: guestKey, content: "踢馆发言加载失败" });
        const reactionRound = result.reactionRound
          ? normalizeBackendRound(result.reactionRound)
          : { speeches: [], clashes: [] };
        setParticipants((prev) => (prev.includes(guestKey) ? prev : [...prev, guestKey]));

        // 添加交锋关系
        const guestName = result.speech?.sage_name || guestKey;
        const newClash: DebateClash = {
          fromSageId: guestKey,
          toSageId: "confucius",
          type: "reframe",
          summary: `${guestName}踢馆而来，提出新观点`,
        };
        syncFlowState({
          ...flowStateRef.current,
          speeches: [...flowStateRef.current.speeches, guestSpeech, ...reactionRound.speeches],
          clashes: [...flowStateRef.current.clashes, newClash, ...reactionRound.clashes],
          activeSageId: null,
          report: null,
        });
        setReport(null);
        const reportResult = await api.getDebateReport(sessionId);
        setReport(normalizeDebateReport(reportResult.report));
        setGuestCue(`${guestName}入席发难`);
      } catch (err) {
        console.error("召唤踢馆名人失败:", err);
        // 回退到Mock数据
        const guestNames: Record<string, string> = {
          li_bai: "李白",
          su_shi: "苏轼",
          zhuge_liang: "诸葛亮",
          fan_zhongyan: "范仲淹",
          wang_anshi: "王安石",
        };
        const guestName = guestNames[guestKey] || "高人";

        const guestSpeech: SageRoundSpeech = {
          sageId: guestKey,
          content: `【${guestName}踢馆而来】\n\n哈哈！尔等在此论道，何不听听吾之一言？\n\n人生得意须尽欢，莫使金樽空对月。天生我材必有用，千金散尽还复来。尔等所论，皆太过沉重。人生在世，当痛快尽兴地活！\n\n内卷？躺平？皆不必也。当效太白，举杯邀明月，对影成三人。天地广阔，何必困于一隅？\n\n---\n白话：人生苦短，何必纠结于内卷与躺平？当洒脱自在，活出真我。`,
          citations: [
            {
              text: "人生得意须尽欢，莫使金樽空对月",
              source: "《将进酒》",
              chapter: "李白",
              verse_no: 1,
              similarity: 0.98,
              type: "verse",
            },
          ],
          isStreaming: false,
          isComplete: true,
        };

        setParticipants((prev) => (prev.includes(guestKey) ? prev : [...prev, guestKey]));
        setSpeeches((prev) => [...prev, guestSpeech]);

        const newClash: DebateClash = {
          fromSageId: guestKey,
          toSageId: "confucius",
          type: "reframe",
          summary: `${guestName}提出第三条路：痛快尽兴地活`,
        };
        setClashes((prev) => [...prev, newClash]);
      } finally {
        await refreshGuestRoster();
        await refreshGraphState(sessionId);
        setIsSummoning(false);
      }
    },
    [refreshGraphState, refreshGuestRoster, sessionId, syncFlowState]
  );

  const handleRandomGuest = useCallback(async () => {
    if (!sessionId) return;
    try {
      setIsSummoning(true);
      const result = await api.randomGuest(sessionId);
      const guestSpeech = normalizeBackendSpeech(result.speech || { sage_key: result.sageKey, content: "随机踢馆发言加载失败" });
      const reactionRound = result.reactionRound
        ? normalizeBackendRound(result.reactionRound)
        : { speeches: [], clashes: [] };
      setParticipants((prev) => (prev.includes(result.sageKey) ? prev : [...prev, result.sageKey]));
      syncFlowState({
        ...flowStateRef.current,
        speeches: [...flowStateRef.current.speeches, guestSpeech, ...reactionRound.speeches],
        clashes: [...flowStateRef.current.clashes, ...reactionRound.clashes],
        activeSageId: null,
        report: null,
      });
      setReport(null);
      const reportResult = await api.getDebateReport(sessionId);
      setReport(normalizeDebateReport(reportResult.report));
      setGuestCue("客席忽然起身，随机踢馆触发");
    } catch (err) {
      setError(err instanceof Error ? err.message : "随机踢馆失败，请稍后重试");
    } finally {
      await refreshGuestRoster();
      await refreshGraphState(sessionId);
      setIsSummoning(false);
    }
  }, [refreshGraphState, refreshGuestRoster, sessionId, syncFlowState]);

  const handleGuestDecision = useCallback(
    async (guestKey: string, decision: "stay" | "leave") => {
      if (!sessionId) return;
      setIsSummoning(true);
      setError(null);
      try {
        const result = await api.decideGuest(sessionId, guestKey, decision);
        if (result.participants?.length) {
          setParticipants(result.participants);
        } else {
          setParticipants((prev) => {
            if (decision === "leave") return prev.filter((id) => id !== guestKey);
            return prev.includes(guestKey) ? prev : [...prev, guestKey];
          });
        }
        setGuestCue(decision === "stay" ? `${guestKey} stays in the roster` : `${guestKey} leaves the stage`);
        await refreshGuestRoster();
        await refreshGraphState(sessionId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Guest decision failed");
      } finally {
        setIsSummoning(false);
      }
    },
    [refreshGraphState, refreshGuestRoster, sessionId]
  );

  useEffect(() => {
    if (!sessionId || isSummoning) return;
    const guestCount = speeches.filter((speech) => speech.isGuest).length;
    if (
      shouldAutoTriggerGuest({
        phase,
        speechCount: speeches.filter((speech) => speech.isComplete).length,
        guestCount,
        alreadyTriggered: autoGuestTriggeredRef.current,
        randomValue: Math.random(),
      })
    ) {
      autoGuestTriggeredRef.current = true;
      setGuestCue("Auto challenger cue armed");
      void handleRandomGuest();
    }
  }, [handleRandomGuest, isSummoning, phase, sessionId, speeches]);

  const handleSageClick = useCallback(
    (sageId: string) => {
      // Scroll to that sage's speech in the timeline
      const el = document.getElementById(`speech-${sageId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    },
    []
  );

  return (
    <div
      className="min-h-screen bg-rice-50 dark:bg-ink-800"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(248,245,238,0.88), rgba(248,245,238,0.97)), url(${pageBackgrounds.roundtable})`,
        backgroundSize: "cover",
        backgroundPosition: "center top",
      }}
    >
      <div className="mx-auto max-w-5xl px-4 py-8 md:py-12">
        {/* Header */}
        <RoundTableHeader />

        {/* Error Display */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-center text-sm text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
            <AlertCircle className="mr-2 inline-block h-4 w-4" />
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-800 underline dark:text-red-300"
            >
              关闭
            </button>
          </div>
        )}

        {/* Phase: Select */}
        <AnimatePresence mode="wait">
          {phase === "select" && (
            <motion.div
              key="select"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-8"
            >
              {/* Sage Avatars */}
              <div className="mb-8">
                <SageAvatars sages={sages} />
              </div>

              {/* Topic Selector */}
              <TopicSelector onSelect={handleTopicSelect} />
            </motion.div>
          )}

          {(phase === "debating" || phase === "complete") && (
            <motion.div
              key="debating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-8"
            >
              {/* Topic display */}
              <div className="mb-8 text-center">
                <span className="inline-flex items-center gap-2 rounded-full border border-cinnabar-200 bg-cinnabar-50 px-5 py-2 font-serif text-base font-medium text-cinnabar-700 dark:border-cinnabar-600 dark:bg-cinnabar-900/30 dark:text-cinnabar-300">
                  <span className="text-sm">话题</span>
                  {topic}
                </span>
              </div>

              {/* Sage Avatars (compact) */}
              <div className="mb-8">
                <SageAvatars
                  sages={sages}
                  activeSageId={activeSageId}
                  onSageClick={handleSageClick}
                />
              </div>

              {/* Debate Timeline */}
              <DebateTimeline
                sages={sages}
                speeches={speeches}
                clashes={clashes}
                isDebating={phase === "debating"}
              />

              <div className="mt-8">
                <ModeratorStateGraph graph={graphState} />
              </div>

              {/* Citation Panel */}
              {phase === "complete" && (
                <div className="mt-8">
                  <CitationPanel
                    speeches={speeches}
                    sageNames={sageNames}
                  />
                </div>
              )}

              {canUseInterventionBar(phase, sessionId) && (
                <div className="mt-8">
                  <InterventionBar
                    sages={sages}
                    value={interventionText}
                    targetSageId={targetSageId}
                    mutualFromSageId={mutualFromSageId}
                    mutualToSageId={mutualToSageId}
                    isLoading={isIntervening}
                    canUseActions={phase === "complete"}
                    queuedCount={queuedInterventionCount}
                    onChange={setInterventionText}
                    onTargetChange={setTargetSageId}
                    onMutualFromChange={setMutualFromSageId}
                    onMutualToChange={setMutualToSageId}
                    onAsk={() => handleIntervention(false)}
                    onStand={handleStand}
                    onMutualQuestion={handleMutualQuestion}
                  />
                </div>
              )}

              {canUseInterventionBar(phase, sessionId) && thoughtMark && (
                <div className="mt-8">
                  <ThoughtCompass mark={thoughtMark} />
                </div>
              )}

              {/* 踢馆按钮 */}
              {phase === "complete" && (
                <div className="mt-8 flex justify-center">
                  <GuestSummoner
                    roster={guestRoster}
                    onSummon={handleSummonGuest}
                    onRandomSummon={handleRandomGuest}
                    onDecision={handleGuestDecision}
                    disabled={isSummoning}
                    cue={guestCue}
                  />
                </div>
              )}

              {/* Debate Summary */}
              {phase === "complete" && (
                <div className="mt-8">
                  <DebateSummary
                    topic={topic}
                    sages={sages}
                    speeches={speeches}
                    clashes={clashes}
                    report={report}
                    onNewTopic={handleNewTopic}
                  />
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Disclaimer */}
        <div className="mt-12 flex items-center justify-center gap-1.5">
          <AlertCircle size={12} className="text-bronze-500" />
          <span className="text-[11px] text-ink-400 dark:text-rice-500">
            以上为基于经典思想的演绎，非历史人物原话，仅供参考
          </span>
        </div>
      </div>
    </div>
  );
}

function InterventionBar({
  sages,
  value,
  targetSageId,
  mutualFromSageId,
  mutualToSageId,
  isLoading,
  canUseActions,
  queuedCount,
  onChange,
  onTargetChange,
  onMutualFromChange,
  onMutualToChange,
  onAsk,
  onStand,
  onMutualQuestion,
}: {
  sages: Sage[];
  value: string;
  targetSageId: string;
  mutualFromSageId: string;
  mutualToSageId: string;
  isLoading: boolean;
  canUseActions: boolean;
  queuedCount: number;
  onChange: (value: string) => void;
  onTargetChange: (value: string) => void;
  onMutualFromChange: (value: string) => void;
  onMutualToChange: (value: string) => void;
  onAsk: () => void;
  onStand: () => void;
  onMutualQuestion: () => void;
}) {
  return (
    <div className="mx-auto max-w-3xl rounded-lg border border-ink-100 bg-white/85 p-3 shadow-scroll-soft dark:border-ink-600 dark:bg-ink-700/80">
      <div className="mb-2 flex items-center gap-2 text-xs text-ink-500 dark:text-rice-400">
        <MessageSquareQuote size={14} className="text-bronze-500" />
        <span>论主介入</span>
        {queuedCount > 0 && (
          <span className="rounded-full bg-bronze-100 px-2 py-0.5 text-[11px] text-bronze-700 dark:bg-bronze-900/30 dark:text-bronze-200">
            已排队 {queuedCount}
          </span>
        )}
        <select
          value={targetSageId}
          onChange={(event) => onTargetChange(event.target.value)}
          className="ml-auto rounded-md border border-ink-100 bg-rice-50 px-2 py-1 font-serif text-xs text-ink-700 outline-none dark:border-ink-600 dark:bg-ink-800 dark:text-rice-100"
        >
          {sages.map((sage) => (
            <option key={sage.id} value={sage.id}>
              请{sage.name}回应
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onAsk();
            }
          }}
          disabled={isLoading}
          placeholder="打断、追问，或亮出你的主张..."
          className="min-w-0 flex-1 rounded-lg border border-ink-200 bg-rice-50 px-4 py-2.5 font-serif text-sm text-ink-700 outline-none transition-colors focus:border-cinnabar-400 dark:border-ink-500 dark:bg-ink-800 dark:text-rice-100"
        />
        <div className="flex gap-2">
          <button
            onClick={onAsk}
            disabled={!value.trim() || isLoading}
            className={clsx(
              "inline-flex items-center justify-center gap-1.5 rounded-lg bg-cinnabar-600 px-4 py-2.5 font-serif text-sm text-rice-50 shadow-scroll-soft transition-all",
              "hover:bg-cinnabar-700 disabled:cursor-not-allowed disabled:opacity-40"
            )}
          >
            <Send size={14} />
            追问
          </button>
          <button
            onClick={onStand}
            disabled={!value.trim() || isLoading || !canUseActions}
            className={clsx(
              "inline-flex items-center justify-center gap-1.5 rounded-lg border border-bronze-400/40 bg-rice-100 px-4 py-2.5 font-serif text-sm text-bronze-700 transition-all",
              "hover:border-bronze-500 hover:bg-rice-200 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-ink-600 dark:text-rice-100"
            )}
          >
            <ShieldCheck size={14} />
            站队
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-col gap-2 border-t border-ink-100 pt-3 dark:border-ink-600 sm:flex-row sm:items-center">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <GitCompareArrows size={14} className="shrink-0 text-bronze-500" />
          <select
            value={mutualFromSageId}
            onChange={(event) => onMutualFromChange(event.target.value)}
            className="min-w-0 flex-1 rounded-md border border-ink-100 bg-rice-50 px-2 py-1.5 font-serif text-xs text-ink-700 outline-none dark:border-ink-600 dark:bg-ink-800 dark:text-rice-100"
          >
            {sages.map((sage) => (
              <option key={sage.id} value={sage.id}>
                {sage.name}
              </option>
            ))}
          </select>
          <span className="text-xs text-ink-400">问</span>
          <select
            value={mutualToSageId}
            onChange={(event) => onMutualToChange(event.target.value)}
            className="min-w-0 flex-1 rounded-md border border-ink-100 bg-rice-50 px-2 py-1.5 font-serif text-xs text-ink-700 outline-none dark:border-ink-600 dark:bg-ink-800 dark:text-rice-100"
          >
            {sages.map((sage) => (
              <option key={sage.id} value={sage.id}>
                {sage.name}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={onMutualQuestion}
          disabled={isLoading || !canUseActions || mutualFromSageId === mutualToSageId}
          className={clsx(
            "inline-flex items-center justify-center gap-1.5 rounded-lg border border-cinnabar-300/50 bg-white px-4 py-2 font-serif text-sm text-cinnabar-700 transition-all",
            "hover:border-cinnabar-500 hover:bg-cinnabar-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-cinnabar-700 dark:bg-ink-700 dark:text-cinnabar-200"
          )}
        >
          <GitCompareArrows size={14} />
          请其互问
        </button>
      </div>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import CourtStageChrome from "./CourtStageChrome";
import CaseIntake from "./CaseIntake";
import EvidenceDock from "./EvidenceDock";
import SageTribunal from "./SageTribunal";
import VerdictScroll from "./VerdictScroll";
import { useThoughtCourt } from "./useThoughtCourt";
import { CURATED_COURT_CASES, getCuratedCourtCase } from "@/lib/thoughtCourtCases";
import styles from "./ThoughtCourt.module.css";

const ACT_NAMES: Record<string, string> = {
  idle: "等待立案",
  intake: "立案问询",
  retrieving: "检索经典依据",
  evidence: "取证核验",
  debate: "三方辩论",
  weighting: "调权定夺",
  verdict: "落判宣读",
  completed: "本案已结",
};

const LIVE_SAGES = ["confucius", "mencius", "laozi"];

const NO_LOGIN_COPY = "无需登录";

// Find a curated case whose question matches the user's question.
function findMatchingCuratedCase(question: string) {
  if (!question) return null;
  return CURATED_COURT_CASES.find((c) => c.question === question.trim()) ?? null;
}

export default function ThoughtCourtExperience() {
  const court = useThoughtCourt();
  const { state } = court;

  const [showOpeningShot, setShowOpeningShot] = useState(true);
  const actHeadingRef = useRef<HTMLHeadingElement | null>(null);
  const isTypingRef = useRef(false);

  const handleToggleSound = useCallback(() => {
    court.setSound(state.sound === "muted" ? "enabled" : "muted");
  }, [court, state.sound]);

  const handleToggleMotion = useCallback(() => {
    court.setMotion(state.motion === "full" ? "reduced" : "full");
  }, [court, state.motion]);

  const handleSkipOpeningShot = useCallback(() => {
    setShowOpeningShot(false);
  }, []);

  const handleSampleFrame = useCallback(
    (deltaMs: number) => {
      court.sampleFrame(deltaMs);
    },
    [court]
  );

  const handleOpenCourt = useCallback(
    (question: string) => {
      if (state.mode === "live") {
        court.submitLive(question, LIVE_SAGES);
      } else {
        const curated = state.caseId ? getCuratedCourtCase(state.caseId) : null;
        court.submitCase(question, curated ?? undefined);
      }
    },
    [court, state.mode, state.caseId]
  );

  const isNetworkBusy = state.network === "loading" || state.network === "streaming";
  const isFailed = state.network === "failed";
  const matchingCuratedCase = findMatchingCuratedCase(state.question);

  // Set focus to act heading after phase change, except while the user is typing.
  useEffect(() => {
    if (isTypingRef.current) return;
    if (showOpeningShot) return;
    const timer = setTimeout(() => {
      actHeadingRef.current?.focus();
    }, 80);
    return () => clearTimeout(timer);
  }, [state.phase, showOpeningShot]);

  const renderRecoveryPanel = () => {
    if (!isFailed || !state.error) return null;
    return (
      <div className={styles.recoveryPanel} role="alert" aria-live="assertive">
        <h3 className={styles.recoveryTitle}>当前环节中断</h3>
        <p className={styles.recoveryMessage}>{state.error}</p>
        <div className={styles.recoveryActions}>
          <button
            type="button"
            className={`${styles.recoveryBtn} ${styles.recoveryBtnPrimary}`}
            onClick={() => court.retry()}
          >
            <RotateCcw size={16} />
            重试
          </button>
          {matchingCuratedCase ? (
            <button
              type="button"
              className={styles.recoveryBtn}
              onClick={() => court.useStableDemo(matchingCuratedCase)}
            >
              切换演示稳定层
            </button>
          ) : (
            <button
              type="button"
              className={styles.recoveryBtn}
              onClick={() => court.reset()}
            >
              返回选案
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderStageBody = () => {
    if (state.phase === "idle" || state.phase === "intake") {
      return (
        <>
          <CaseIntake
            cases={CURATED_COURT_CASES}
            selectedCaseId={state.caseId}
            mode={state.mode}
            disabled={isNetworkBusy}
            onSelectCase={court.selectCase}
            onChooseLive={court.chooseLive}
            onOpenCourt={handleOpenCourt}
          />
          {renderRecoveryPanel()}
        </>
      );
    }

    if (state.phase === "retrieving") {
      return (
        <section className={styles.stageBody} aria-live="polite">
          <div className={styles.phasePanel}>
            <p className={styles.phaseEyebrow}>当前幕次</p>
            <h2
              ref={actHeadingRef}
              className={styles.phaseTitle}
              tabIndex={-1}
            >
              检索经典依据
            </h2>
            <p className={styles.phaseHint}>正在检索经典依据……</p>
            <p className={styles.phaseNoLogin}>{NO_LOGIN_COPY}</p>
          </div>
          {renderRecoveryPanel()}
        </section>
      );
    }

    if (state.phase === "evidence") {
      return (
        <>
          <EvidenceDock
            evidence={court.evidence}
            selectedIds={court.selectedEvidenceIds}
            citationStatus={state.citationStatus}
            motion={state.motion}
            onToggleEvidence={court.toggleEvidence}
            onBeginDebate={court.beginDebate}
          />
          {renderRecoveryPanel()}
        </>
      );
    }

    if (state.phase === "debate") {
      return (
        <>
          <SageTribunal
            speeches={court.speeches}
            clashes={court.clashes}
            activeSageId={court.activeSageId}
            busy={court.busy}
            onFollowUp={court.followUp}
            onMutualQuestion={court.mutualQuestion}
            onChooseStance={court.chooseStance}
            onBuildVerdict={court.buildVerdict}
          />
          {renderRecoveryPanel()}
        </>
      );
    }

    if (
      (state.phase === "weighting" ||
        state.phase === "verdict" ||
        state.phase === "completed") &&
      court.report
    ) {
      return (
        <>
          <VerdictScroll
            report={court.report}
            evidence={court.evidence}
            weights={state.weights}
            citationStatus={state.citationStatus}
            completed={state.phase === "verdict" || state.phase === "completed"}
            onSetWeights={court.setWeights}
            onComplete={court.buildVerdict}
            onReset={court.reset}
          />
          {renderRecoveryPanel()}
        </>
      );
    }

    return (
      <section className={styles.stageBody} aria-live="polite">
        <div className={styles.phasePanel}>
          <p className={styles.phaseEyebrow}>当前幕次</p>
          <h2
            ref={actHeadingRef}
            className={styles.phaseTitle}
            tabIndex={-1}
          >
            {ACT_NAMES[state.phase] ?? "思想公堂"}
          </h2>
          <p className={styles.phaseHint}>本案已结，可新开一案。</p>
          <p className={styles.phaseNoLogin}>{NO_LOGIN_COPY}</p>
        </div>
        {renderRecoveryPanel()}
      </section>
    );
  };

  return (
    <CourtStageChrome
      phase={state.phase}
      mode={state.mode}
      network={state.network}
      motion={state.motion}
      sound={state.sound}
      error={state.error}
      showOpeningShot={showOpeningShot}
      onSkipOpeningShot={handleSkipOpeningShot}
      onToggleSound={handleToggleSound}
      onToggleMotion={handleToggleMotion}
      onReset={court.reset}
      onSampleFrame={handleSampleFrame}
    >
      {renderStageBody()}
    </CourtStageChrome>
  );
}

"use client";

import { useCallback } from "react";
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

export default function ThoughtCourtExperience() {
  const court = useThoughtCourt();
  const { state } = court;

  const handleToggleSound = useCallback(() => {
    court.setSound(state.sound === "muted" ? "enabled" : "muted");
  }, [court, state.sound]);

  const handleToggleMotion = useCallback(() => {
    court.setMotion(state.motion === "full" ? "reduced" : "full");
  }, [court, state.motion]);

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

  const renderStageBody = () => {
    if (state.phase === "idle" || state.phase === "intake") {
      return (
        <CaseIntake
          cases={CURATED_COURT_CASES}
          selectedCaseId={state.caseId}
          mode={state.mode}
          disabled={isNetworkBusy}
          onSelectCase={court.selectCase}
          onChooseLive={court.chooseLive}
          onOpenCourt={handleOpenCourt}
        />
      );
    }

    if (state.phase === "retrieving") {
      return (
        <section className={styles.stageBody} aria-live="polite">
          <div className={styles.phasePanel}>
            <p className={styles.phaseEyebrow}>当前幕次</p>
            <h2 className={styles.phaseTitle}>检索经典依据</h2>
            <p className={styles.phaseHint}>正在检索经典依据……</p>
          </div>
        </section>
      );
    }

    if (state.phase === "evidence") {
      return (
        <EvidenceDock
          evidence={court.evidence}
          selectedIds={court.selectedEvidenceIds}
          citationStatus={state.citationStatus}
          motion={state.motion}
          onToggleEvidence={court.toggleEvidence}
          onBeginDebate={court.beginDebate}
        />
      );
    }

    if (state.phase === "debate") {
      return (
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
      );
    }

    if (
      (state.phase === "weighting" ||
        state.phase === "verdict" ||
        state.phase === "completed") &&
      court.report
    ) {
      return (
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
      );
    }

    return (
      <section className={styles.stageBody} aria-live="polite">
        <div className={styles.phasePanel}>
          <p className={styles.phaseEyebrow}>当前幕次</p>
          <h2 className={styles.phaseTitle}>{ACT_NAMES[state.phase] ?? "思想公堂"}</h2>
          <p className={styles.phaseHint}>本案已结，可新开一案。</p>
        </div>
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
      onToggleSound={handleToggleSound}
      onToggleMotion={handleToggleMotion}
      onReset={court.reset}
    >
      {renderStageBody()}
    </CourtStageChrome>
  );
}

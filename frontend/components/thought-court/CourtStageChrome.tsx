"use client";

import type { ReactNode } from "react";
import { Accessibility, RotateCcw, Volume2, VolumeX, Waves } from "lucide-react";
import type { CourtMode, CourtMotionMode, CourtNetwork, CourtPhase, CourtSound } from "@/lib/thoughtCourtTypes";
import styles from "./ThoughtCourt.module.css";

const ACTS: { key: string; label: string; phases: CourtPhase[] }[] = [
  { key: "问", label: "立案问询", phases: ["idle", "intake"] },
  { key: "证", label: "取证核验", phases: ["retrieving", "evidence"] },
  { key: "辩", label: "三方辩论", phases: ["debate"] },
  { key: "判", label: "落判定夺", phases: ["weighting", "verdict", "completed"] },
];

const MODE_LABEL: Record<CourtMode, string> = {
  curated: "精选案例",
  live: "实时问道",
  "stable-demo": "稳定演示",
};

const NETWORK_LABEL: Record<CourtNetwork, string> = {
  idle: "待命",
  loading: "检索中",
  streaming: "传讯中",
  failed: "中断",
};

interface CourtStageChromeProps {
  phase: CourtPhase;
  mode: CourtMode;
  network: CourtNetwork;
  motion: CourtMotionMode;
  sound: CourtSound;
  error: string | null;
  onToggleSound: () => void;
  onToggleMotion: () => void;
  onReset: () => void;
  children: ReactNode;
}

export default function CourtStageChrome({
  phase,
  mode,
  network,
  motion,
  sound,
  error,
  onToggleSound,
  onToggleMotion,
  onReset,
  children,
}: CourtStageChromeProps) {
  const activeActIndex = ACTS.findIndex((act) => act.phases.includes(phase));

  return (
    <div className={styles.court} data-motion={motion} data-sound={sound}>
      <header className={styles.chromeBar}>
        <div className={styles.actProgress} aria-label="审案进度">
          {ACTS.map((act, index) => {
            const isActive = index === activeActIndex;
            const isDone = index < activeActIndex;
            return (
              <div
                key={act.key}
                className={`${styles.actStep} ${isActive ? styles.actStepActive : ""} ${isDone ? styles.actStepDone : ""}`}
                aria-current={isActive ? "step" : undefined}
              >
                <span className={styles.actGlyph}>{act.key}</span>
                <span className={styles.actLabel}>{act.label}</span>
              </div>
            );
          })}
        </div>

        <div className={styles.chromeControls}>
          <span className={styles.modeBadge}>{MODE_LABEL[mode]}</span>
          <span
            className={`${styles.networkBadge} ${network === "failed" ? styles.networkBadgeFailed : ""}`}
            aria-live="polite"
          >
            {NETWORK_LABEL[network]}
          </span>
          <button
            type="button"
            className={styles.iconButton}
            onClick={onToggleSound}
            aria-label={sound === "muted" ? "开启声音" : "关闭声音"}
            title={sound === "muted" ? "开启声音" : "关闭声音"}
          >
            {sound === "muted" ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
          <button
            type="button"
            className={styles.iconButton}
            onClick={onToggleMotion}
            aria-label={motion === "full" ? "降低动效" : "恢复动效"}
            title={motion === "full" ? "降低动效" : "恢复动效"}
          >
            {motion === "full" ? <Waves size={18} /> : <Accessibility size={18} />}
          </button>
          <button
            type="button"
            className={styles.iconButton}
            onClick={onReset}
            aria-label="重置公堂"
            title="重置公堂"
          >
            <RotateCcw size={18} />
          </button>
        </div>
      </header>

      {error && (
        <div className={styles.errorBar} role="alert">
          {error}
        </div>
      )}

      <main className={styles.stage} aria-label="思想公堂舞台">
        {children}
      </main>
    </div>
  );
}

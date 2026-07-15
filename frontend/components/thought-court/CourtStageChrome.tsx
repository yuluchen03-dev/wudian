"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
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

const STABLE_DEMO_BADGE = "演示稳定层：已加载经校验案件";

interface CourtStageChromeProps {
  phase: CourtPhase;
  mode: CourtMode;
  network: CourtNetwork;
  motion: CourtMotionMode;
  sound: CourtSound;
  error: string | null;
  showOpeningShot: boolean;
  onSkipOpeningShot: () => void;
  onToggleSound: () => void;
  onToggleMotion: () => void;
  onReset: () => void;
  onSampleFrame?: (deltaMs: number) => void;
  children: ReactNode;
}

export default function CourtStageChrome({
  phase,
  mode,
  network,
  motion: motionMode,
  sound,
  error,
  showOpeningShot,
  onSkipOpeningShot,
  onToggleSound,
  onToggleMotion,
  onReset,
  onSampleFrame,
  children,
}: CourtStageChromeProps) {
  const activeActIndex = ACTS.findIndex((act) => act.phases.includes(phase));
  const samplingRef = useRef(false);
  const lastFrameRef = useRef(0);
  const samplesRef = useRef<number[]>([]);
  const gestureRegisteredRef = useRef(false);

  // Runtime degradation sampler: starts after the first user gesture, stops after decision.
  // Never collects or transmits timing data; only used locally to decide degraded motion.
  const startFrameSampler = () => {
    if (samplingRef.current || gestureRegisteredRef.current) return;
    if (typeof window === "undefined" || !onSampleFrame) return;
    gestureRegisteredRef.current = true;
    samplingRef.current = true;
    samplesRef.current = [];
    lastFrameRef.current = performance.now();

    const sampleLoop = (now: number) => {
      if (!samplingRef.current) return;
      const delta = now - lastFrameRef.current;
      lastFrameRef.current = now;
      onSampleFrame(delta);
      samplesRef.current.push(delta);

      if (samplesRef.current.length >= 30) {
        samplingRef.current = false;
        return;
      }
      requestAnimationFrame(sampleLoop);
    };
    requestAnimationFrame(sampleLoop);
  };

  // First-interaction cancels the opening shot and starts the sampler.
  useEffect(() => {
    if (showOpeningShot) {
      const cancel = () => {
        onSkipOpeningShot();
        startFrameSampler();
      };
      window.addEventListener("pointerdown", cancel, { once: true });
      window.addEventListener("keydown", cancel, { once: true });
      return () => {
        window.removeEventListener("pointerdown", cancel);
        window.removeEventListener("keydown", cancel);
      };
    }
  }, [showOpeningShot, onSkipOpeningShot]);

  // Sound assets are not bundled locally; the toggle stays disabled.
  const soundDisabled = true;

  return (
    <div
      className={styles.court}
      data-motion={motionMode}
      data-sound={sound}
      onPointerDown={startFrameSampler}
    >
      <a href="#court-stage-main" className={styles.skipLink}>
        跳过至公堂舞台
      </a>

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
          {mode === "stable-demo" ? (
            <span className={styles.stableDemoBadge} aria-label={STABLE_DEMO_BADGE}>
              {STABLE_DEMO_BADGE}
            </span>
          ) : (
            <span className={styles.modeBadge}>{MODE_LABEL[mode]}</span>
          )}
          <span
            className={`${styles.networkBadge} ${network === "failed" ? styles.networkBadgeFailed : ""}`}
            aria-live="polite"
          >
            {NETWORK_LABEL[network]}
          </span>
          <button
            type="button"
            className={`${styles.iconButton} ${soundDisabled ? styles.iconButtonDisabled : ""}`}
            onClick={onToggleSound}
            disabled={soundDisabled}
            aria-label={soundDisabled ? "声音素材未加载" : sound === "muted" ? "开启声音" : "关闭声音"}
            title={soundDisabled ? "声音素材未加载" : sound === "muted" ? "开启声音" : "关闭声音"}
          >
            {/* Sound playback is gated behind state.sound === "enabled" and a user gesture. */}
            {sound === "enabled" ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
          <button
            type="button"
            className={styles.iconButton}
            onClick={onToggleMotion}
            aria-label={motionMode === "full" ? "降低动效" : "恢复动效"}
            title={motionMode === "full" ? "降低动效" : "恢复动效"}
          >
            {motionMode === "full" ? <Waves size={18} /> : <Accessibility size={18} />}
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

      <main id="court-stage-main" className={styles.stage} aria-label="思想公堂舞台" tabIndex={-1}>
        {children}

        {/* Opening shot: 2-3 second skippable establishing shot; first interaction cancels it */}
        <AnimatePresence>
          {showOpeningShot && motionMode !== "reduced" && motionMode !== "degraded" && (
            <motion.div
              className={styles.openingShot}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <motion.span
                className={styles.openingShotLabel}
                initial={{ letterSpacing: "0.05em", opacity: 0.6 }}
                animate={{ letterSpacing: "0.25em", opacity: 1 }}
                transition={{ duration: 2.2, ease: "easeInOut" }}
              >
                思想审判场
              </motion.span>
              <button
                type="button"
                className={styles.openingShotSkip}
                onClick={onSkipOpeningShot}
              >
                跳过
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { buildVerdict, normalizeWeights } from "@/lib/thoughtCourtVerdict";
import type {
  CitationStatus,
  CourtEvidence,
  CourtReport,
  CourtWeightKey,
  CourtWeights,
} from "@/lib/thoughtCourtTypes";
import styles from "./ThoughtCourt.module.css";

interface VerdictScrollProps {
  report: CourtReport;
  evidence: CourtEvidence[];
  weights: CourtWeights;
  citationStatus: CitationStatus;
  completed: boolean;
  onSetWeights(weights: CourtWeights): void;
  onComplete(): void;
  onReset(): void;
}

const WEIGHT_CONTROLS: { key: CourtWeightKey; label: string }[] = [
  { key: "self", label: "坚持自我" },
  { key: "relationship", label: "改善关系" },
  { key: "change", label: "主动改变" },
];

const SAFETY_BOUNDARY =
  "悟典不替代你做出人生决定，判词仅为参考，请结合现实情境判断。";

export default function VerdictScroll({
  report,
  evidence,
  weights,
  citationStatus,
  completed,
  onSetWeights,
  onComplete,
  onReset,
}: VerdictScrollProps) {
  const [sealed, setSealed] = useState(completed);
  const [showWeights, setShowWeights] = useState(!completed);

  useEffect(() => {
    if (!completed || sealed) return;
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) {
      setSealed(true);
      return;
    }
    const timer = setTimeout(() => setSealed(true), 900);
    return () => clearTimeout(timer);
  }, [completed, sealed]);

  const verdict = useMemo(
    () => buildVerdict(report, weights),
    [report, weights]
  );
  const normalized = useMemo(() => normalizeWeights(weights), [weights]);

  const handleWeightChange = (key: CourtWeightKey, value: number) => {
    onSetWeights({ ...weights, [key]: value });
  };

  return (
    <section className={styles.verdict} aria-label="判词">
      <div className={styles.verdictHeader}>
        <h2 className={styles.verdictTitle}>判词</h2>
      </div>

      {/* Verdict seal — one seal impact; stage tone shifts from ink to paper */}
      <motion.div
        className={`${styles.verdictBody} ${sealed ? styles.verdictBodySealed : ""}`}
        initial={false}
        animate={{
          backgroundColor: sealed
            ? "rgba(242, 238, 228, 0.10)"
            : "rgba(242, 238, 228, 0.04)",
        }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
      >
        <div className={styles.verdictSection}>
          <h3 className={styles.verdictSectionTitle}>核心矛盾</h3>
          <p className={styles.verdictSectionText}>{verdict.conflict}</p>
        </div>

        <div className={styles.verdictSection}>
          <h3 className={styles.verdictSectionTitle}>他们的共识</h3>
          <ul className={styles.verdictList}>
            {verdict.consensus.map((item, idx) => (
              <li key={idx} className={styles.verdictListItem}>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.verdictSection}>
          <h3 className={styles.verdictSectionTitle}>根本分歧</h3>
          <ul className={styles.verdictList}>
            {verdict.divergences.map((item, idx) => (
              <li key={idx} className={styles.verdictListItem}>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.verdictSection}>
          <h3 className={styles.verdictSectionTitle}>今日行动</h3>
          <ol className={styles.verdictOrderedList}>
            {verdict.actions.map((action, idx) => (
              <li key={idx} className={styles.verdictListItem}>
                {action}
              </li>
            ))}
          </ol>
        </div>

        <div className={styles.verdictSection}>
          <h3 className={styles.verdictSectionTitle}>保留问题</h3>
          <p className={styles.verdictSectionText}>{verdict.reservation}</p>
        </div>

        <div className={styles.safetyBoundary} role="note">
          {SAFETY_BOUNDARY}
        </div>
      </motion.div>

      {showWeights ? (
        <div className={styles.weightPanel} aria-label="权重调节">
          {WEIGHT_CONTROLS.map(({ key, label }) => (
            <div key={key} className={styles.weightControl}>
              <label className={styles.weightLabel}>
                <span>{label}</span>
                <span className={styles.weightValue}>{normalized[key]}%</span>
              </label>
              <input
                type="range"
                min={0}
                max={100}
                value={weights[key]}
                onChange={(event) =>
                  handleWeightChange(key, Number(event.target.value))
                }
                className={styles.weightRange}
                aria-label={label}
              />
            </div>
          ))}
        </div>
      ) : null}

      {evidence.length > 0 ? (
        <div className={styles.evidenceSourceList} aria-label="经典依据来源">
          <h3 className={styles.verdictSectionTitle}>经典依据</h3>
          {evidence.map((item) => (
            <div key={item.id} className={styles.evidenceSourceItem}>
              <p className={styles.evidenceSourceOriginal}>{item.original}</p>
              <p className={styles.evidenceSourceText}>{item.source}</p>
            </div>
          ))}
        </div>
      ) : null}

      <div
        className={styles.verdictSealLayer}
        data-sealed={sealed ? "true" : "false"}
        aria-hidden="true"
      >
        {sealed && (
          <motion.div
            className={styles.verdictSeal}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            aria-hidden="true"
          />
        )}
      </div>

      <div className={styles.verdictFooter}>
        {!completed ? (
          <button
            type="button"
            className={styles.primaryAction}
            onClick={onComplete}
          >
            落判
          </button>
        ) : (
          <div className={styles.verdictFooterActions}>
            <button
              type="button"
              className={styles.sageActionBtn}
              onClick={() => setShowWeights((prev) => !prev)}
            >
              重新调权
            </button>
            <button
              type="button"
              className={styles.sageActionBtn}
              onClick={onReset}
            >
              新开一案
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

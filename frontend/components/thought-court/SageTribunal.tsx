"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { sageVisuals } from "@/lib/visualAssets";
import type { CourtClash, CourtSpeech } from "@/lib/thoughtCourtTypes";
import styles from "./ThoughtCourt.module.css";

const SAGE_ORDER = ["confucius", "mencius", "laozi"];

const SAGE_NAMES: Record<string, string> = {
  confucius: "孔子",
  mencius: "孟子",
  laozi: "老子",
};

const STANCE_LABEL = "我更认同";

// Split streaming speech into sentence-sized chunks for screen-reader announcements.
function splitIntoSentences(content: string): string[] {
  if (!content) return [];
  return content
    .split(/(?<=[。！？；])/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

interface SageTribunalProps {
  speeches: CourtSpeech[];
  clashes: CourtClash[];
  activeSageId: string | null;
  busy: boolean;
  onFollowUp(content: string, targetSageId: string): Promise<void>;
  onMutualQuestion(fromSageId: string, toSageId: string): Promise<void>;
  onChooseStance(stance: string, targetSageId: string): Promise<void>;
  onBuildVerdict(): void;
}

export default function SageTribunal({
  speeches,
  clashes,
  activeSageId,
  busy,
  onFollowUp,
  onMutualQuestion,
  onChooseStance,
  onBuildVerdict,
}: SageTribunalProps) {
  const [followUpSageId, setFollowUpSageId] = useState<string | null>(null);
  const [followUpText, setFollowUpText] = useState("");
  const [mutualFromId, setMutualFromId] = useState<string | null>(null);
  const [mobileActiveSage, setMobileActiveSage] = useState<string>(
    activeSageId ?? SAGE_ORDER[0]
  );
  const previousClashCountRef = useRef(clashes.length);
  const [showShockwave, setShowShockwave] = useState(false);

  const speechBySage = (sageId: string) =>
    speeches.find((item) => item.sageId === sageId) ?? null;

  // One short shockwave per newly detected clash.
  useEffect(() => {
    if (clashes.length > previousClashCountRef.current) {
      setShowShockwave(true);
      const timer = setTimeout(() => setShowShockwave(false), 600);
      return () => clearTimeout(timer);
    }
    previousClashCountRef.current = clashes.length;
  }, [clashes.length]);

  useEffect(() => {
    previousClashCountRef.current = clashes.length;
  }, []);

  useEffect(() => {
    if (activeSageId) {
      setMobileActiveSage(activeSageId);
    }
  }, [activeSageId]);

  const handleSubmitFollowUp = async (sageId: string) => {
    if (!followUpText.trim()) return;
    await onFollowUp(followUpText.trim(), sageId);
    setFollowUpText("");
    setFollowUpSageId(null);
  };

  const handlePickMutualTarget = async (fromId: string, toId: string) => {
    await onMutualQuestion(fromId, toId);
    setMutualFromId(null);
  };

  const otherSages = (sageId: string) => SAGE_ORDER.filter((id) => id !== sageId);

  const renderSeat = (sageId: string) => {
    const speech = speechBySage(sageId);
    const isActive = activeSageId === sageId;
    const isFailed = speech?.status === "failed";
    const isWaiting =
      !speech ||
      speech.status === "waiting" ||
      (speech.status === "streaming" && !speech.content);
    const visual = sageVisuals[sageId];
    const showFollowUp = followUpSageId === sageId;
    const showMutualPicker = mutualFromId === sageId;
    const sentences = speech?.content ? splitIntoSentences(speech.content) : [];

    return (
      <motion.article
        key={sageId}
        className={`${styles.sageSeat} ${isActive ? styles.sageSeatActive : styles.sageSeatInactive}`}
        data-sage={sageId}
        initial={false}
        animate={{
          scale: isActive ? 1.02 : 0.98,
          opacity: isActive ? 1 : 0.85,
        }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <div className={styles.sagePortraitWrap}>
          <div
            className={styles.sagePortrait}
            style={
              visual
                ? { backgroundImage: `url(${visual.portraitImage})` }
                : undefined
            }
            role="img"
            aria-label={`${SAGE_NAMES[sageId]}肖像`}
          />
          <span className={styles.sageName}>{SAGE_NAMES[sageId]}</span>
        </div>

        <div className={styles.speechRegion}>
          {speech?.position ? (
            <p className={styles.speechPosition}>{speech.position}</p>
          ) : null}
          <div className={styles.speechScroll} aria-live="polite">
            {isFailed ? (
              <p className={styles.speechFailed}>暂未应答</p>
            ) : isWaiting ? (
              <p className={styles.speechWaiting}>暂未应答</p>
            ) : (
              <p className={styles.speechContent}>
                {sentences.map((sentence, idx) => (
                  <span key={idx} aria-label={`第${idx + 1}句`}>
                    {sentence}
                  </span>
                ))}
              </p>
            )}
          </div>
        </div>

        <div className={styles.sageActions}>
          <button
            type="button"
            className={styles.sageActionBtn}
            disabled={busy}
            onClick={() => setFollowUpSageId(showFollowUp ? null : sageId)}
          >
            追问
          </button>
          <button
            type="button"
            className={styles.sageActionBtn}
            disabled={busy}
            onClick={() => setMutualFromId(showMutualPicker ? null : sageId)}
          >
            请其互问
          </button>
          <button
            type="button"
            className={styles.sageActionBtn}
            disabled={busy}
            onClick={() => onChooseStance(STANCE_LABEL, sageId)}
          >
            {STANCE_LABEL}
          </button>
        </div>

        {showFollowUp ? (
          <div className={styles.followUpInline}>
            <textarea
              className={styles.followUpTextarea}
              placeholder={`向${SAGE_NAMES[sageId]}追问……`}
              value={followUpText}
              onChange={(event) => setFollowUpText(event.target.value)}
              rows={2}
              aria-label={`向${SAGE_NAMES[sageId]}追问`}
            />
            <button
              type="button"
              className={styles.followUpSubmit}
              disabled={busy || !followUpText.trim()}
              onClick={() => handleSubmitFollowUp(sageId)}
            >
              送出追问
            </button>
          </div>
        ) : null}

        {showMutualPicker ? (
          <div className={styles.mutualPicker}>
            <span className={styles.mutualPickerLabel}>向谁发问：</span>
            {otherSages(sageId).map((toId) => (
              <button
                key={toId}
                type="button"
                className={styles.mutualPickerBtn}
                disabled={busy}
                onClick={() => handlePickMutualTarget(sageId, toId)}
              >
                {SAGE_NAMES[toId]}
              </button>
            ))}
          </div>
        ) : null}

        {isFailed ? (
          <button
            type="button"
            className={styles.retryBtn}
            disabled={busy}
            onClick={() => onChooseStance("重试", sageId)}
          >
            重新请答
          </button>
        ) : null}
      </motion.article>
    );
  };

  return (
    <section className={styles.tribunal} aria-label="三方辩论">
      <div className={styles.tribunalHeader}>
        <h2 className={styles.tribunalTitle}>三圣会审</h2>
        <p className={styles.tribunalHint}>
          可追问、请其互问，或表明你更认同哪一位。
        </p>
      </div>

      {/* Mobile segmented sage selector — replaces three-seat stage */}
      <div className={styles.sageSegmentBar} role="tablist" aria-label="选择圣贤">
        {SAGE_ORDER.map((sageId) => (
          <button
            key={sageId}
            type="button"
            role="tab"
            aria-selected={mobileActiveSage === sageId}
            className={`${styles.sageSegmentBtn} ${mobileActiveSage === sageId ? styles.sageSegmentBtnActive : ""}`}
            onClick={() => setMobileActiveSage(sageId)}
          >
            {SAGE_NAMES[sageId]}
          </button>
        ))}
      </div>

      <div className={styles.tribunalStage} aria-live="polite">
        {SAGE_ORDER.map((sageId) => renderSeat(sageId))}
      </div>

      {clashes.length > 0 ? (
        <div className={styles.clashList} aria-label="辩论交锋">
          <AnimatePresence>
            {showShockwave && (
              <motion.span
                className={styles.clashShockwave}
                initial={{ scale: 0, opacity: 0.9 }}
                animate={{ scale: 8, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                aria-hidden="true"
              />
            )}
          </AnimatePresence>
          {clashes.map((clash, idx) => (
            <p key={idx} className={styles.clashItem}>
              <span className={styles.clashPair}>
                {SAGE_NAMES[clash.fromSageId] ?? clash.fromSageId} →{" "}
                {SAGE_NAMES[clash.toSageId] ?? clash.toSageId}
              </span>
              <span className={styles.clashSummary}>{clash.summary}</span>
            </p>
          ))}
        </div>
      ) : null}

      <div className={styles.tribunalFooter}>
        <button
          type="button"
          className={styles.primaryAction}
          disabled={busy}
          onClick={onBuildVerdict}
        >
          落判定夺
        </button>
      </div>
    </section>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Gavel, MessageSquareText } from "lucide-react";
import type { CourtMode, CuratedCourtCase } from "@/lib/thoughtCourtTypes";
import styles from "./ThoughtCourt.module.css";

const CASE_QUESTIONS = [
  "我很努力，却总不被领导认可，怎么办？",
  "稳定但不喜欢的工作，要不要离开？",
  "同事抢了我的功劳，我该争还是忍？",
];

const NO_LOGIN_COPY = "无需登录，直接开审";
const POSITIONING_COPY = "不是一个 AI，是一桌中国思想审你的问题";

interface CaseIntakeProps {
  cases: CuratedCourtCase[];
  selectedCaseId: string | null;
  mode: CourtMode;
  disabled: boolean;
  onSelectCase(id: string): void;
  onChooseLive(): void;
  onOpenCourt(question: string): void;
}

export default function CaseIntake({
  cases,
  selectedCaseId,
  mode,
  disabled,
  onSelectCase,
  onChooseLive,
  onOpenCourt,
}: CaseIntakeProps) {
  const [freeQuestion, setFreeQuestion] = useState("");

  const primary = cases[0];
  const alternatives = cases.slice(1, 3);
  const selectedCase = cases.find((c) => c.id === selectedCaseId) ?? null;

  const isLive = mode === "live";
  const canSubmit = !disabled && (isLive ? freeQuestion.trim().length > 0 : Boolean(selectedCase || primary));

  const handleSubmit = () => {
    if (!canSubmit) return;
    if (isLive) {
      onOpenCourt(freeQuestion.trim());
    } else {
      const target = selectedCase ?? primary;
      if (target) onOpenCourt(target.question);
    }
  };

  const handleFreeQuestionFocus = () => {
    if (!isLive) onChooseLive();
  };

  return (
    <section className={styles.intake} aria-label="立案问询">
      <div className={styles.intakeHeader}>
        <motion.h2
          className={styles.intakeTitle}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          选择一案，击鼓开审
        </motion.h2>
        <p className={styles.intakeSubtitle}>三圣将依据经典，为你审理心中之困。</p>
        <p className={styles.intakePositioning}>{POSITIONING_COPY}</p>
        <p className={styles.intakeNoLogin}>{NO_LOGIN_COPY}</p>
      </div>

      {primary && (
        <motion.button
          type="button"
          className={`${styles.caseCard} ${styles.caseCardPrimary} ${selectedCaseId === primary.id ? styles.caseCardSelected : ""}`}
          onClick={() => onSelectCase(primary.id)}
          aria-pressed={selectedCaseId === primary.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.1, ease: "easeOut" }}
        >
          <span className={styles.caseLabel}>{primary.label}</span>
          <span className={styles.caseQuestion}>{primary.question}</span>
          <span className={styles.caseConflicts}>
            {primary.conflicts.map((c) => (
              <span key={c} className={styles.conflictTag}>{c}</span>
            ))}
          </span>
        </motion.button>
      )}

      <div className={styles.alternativeRow}>
        {alternatives.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`${styles.caseCard} ${styles.caseCardCompact} ${selectedCaseId === c.id ? styles.caseCardSelected : ""}`}
            onClick={() => onSelectCase(c.id)}
            aria-pressed={selectedCaseId === c.id}
          >
            <span className={styles.caseLabel}>{c.label}</span>
            <span className={styles.caseQuestionCompact}>{c.question}</span>
          </button>
        ))}
      </div>

      <div className={styles.freeQuestionField}>
        <label htmlFor="court-free-question" className={styles.freeQuestionLabel}>
          <MessageSquareText size={16} />
          或自拟一问
        </label>
        <textarea
          id="court-free-question"
          className={styles.freeQuestionTextarea}
          value={freeQuestion}
          onChange={(e) => setFreeQuestion(e.target.value)}
          onFocus={handleFreeQuestionFocus}
          placeholder={`例如：${CASE_QUESTIONS[0]}`}
          rows={3}
          disabled={disabled}
          aria-label="自拟问询"
        />
      </div>

      <button
        type="button"
        className={styles.primaryAction}
        onClick={handleSubmit}
        disabled={!canSubmit}
        aria-label="击鼓开审"
      >
        <Gavel size={20} />
        击鼓开审
      </button>
    </section>
  );
}

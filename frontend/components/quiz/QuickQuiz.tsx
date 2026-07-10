"use client";

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, RotateCcw, ChevronRight, BookOpen, Sparkles } from "lucide-react";
import clsx from "clsx";
import { getRandomQuiz, type QuickQuizQuestion } from "@/lib/quizData";

interface QuickQuizProps {
  /** 完成后回调 */
  onComplete?: (score: number, total: number) => void;
  /** 关闭回调（用于 modal 模式） */
  onClose?: () => void;
}

const ENCOURAGEMENTS = [
  "善哉！",
  "妙极！",
  "正解！",
  "君子之答！",
  "温故知新！",
];

export default function QuickQuiz({ onComplete, onClose }: QuickQuizProps) {
  const [questions, setQuestions] = useState<QuickQuizQuestion[]>(() => getRandomQuiz(5));
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [fillAnswer, setFillAnswer] = useState("");
  const [answered, setAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const current = questions[currentIndex];
  const isLast = currentIndex === questions.length - 1;

  const checkAnswer = useCallback(() => {
    if (answered || !submitted) return;
    const userAnswer =
      current.type === "fill_blank" ? fillAnswer.trim() : selectedOption;
    if (!userAnswer) return;

    const correct =
      current.type === "fill_blank"
        ? userAnswer === current.correctAnswer ||
          userAnswer.includes(current.correctAnswer) ||
          current.correctAnswer.includes(userAnswer)
        : userAnswer === current.correctAnswer;

    if (correct) setScore((s) => s + 1);
    setAnswered(true);
  }, [answered, submitted, current, fillAnswer, selectedOption]);

  const handleNext = useCallback(() => {
    if (isLast) {
      const finalScore = score;
      setFinished(true);
      onComplete?.(finalScore, questions.length);
      return;
    }
    setCurrentIndex((i) => i + 1);
    setSelectedOption(null);
    setFillAnswer("");
    setAnswered(false);
    setSubmitted(false);
  }, [isLast, score, questions.length, onComplete]);

  const handleRestart = useCallback(() => {
    setQuestions(getRandomQuiz(5));
    setCurrentIndex(0);
    setSelectedOption(null);
    setFillAnswer("");
    setAnswered(false);
    setSubmitted(false);
    setScore(0);
    setFinished(false);
  }, []);

  const encouragement = useMemo(
    () => ENCOURAGEMENTS[Math.floor(Math.random() * ENCOURAGEMENTS.length)],
    [currentIndex, answered]
  );

  const isFillCorrect = (() => {
    if (current.type !== "fill_blank" || !answered) return false;
    return (
      fillAnswer.trim() === current.correctAnswer ||
      fillAnswer.trim().includes(current.correctAnswer) ||
      current.correctAnswer.includes(fillAnswer.trim())
    );
  })();

  // ===== 完成界面 =====
  if (finished) {
    const passed = score >= 3;
    return (
      <div className="flex flex-col items-center justify-center px-6 py-10 text-center">
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 200 }}
          className={clsx(
            "mb-5 flex h-24 w-24 items-center justify-center rounded-full font-serif text-4xl font-bold shadow-popup",
            passed
              ? "bg-cinnabar-600 text-rice-50"
              : "bg-bronze-500 text-rice-50"
          )}
        >
          {score}/{questions.length}
        </motion.div>

        <h3 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
          {passed ? "硕学之才！" : "再接再厉！"}
        </h3>
        <p className="mt-2 text-ink-500 dark:text-rice-300">
          答对 <span className="font-bold text-cinnabar-600">{score}</span> 题 / 共{" "}
          {questions.length} 题
        </p>
        <p className="mt-1 text-sm text-bronze-500">
          {passed ? "温故知新，可以为师矣。" : "学而时习之，不亦说乎？"}
        </p>

        <div className="mt-6 flex gap-3">
          <button
            onClick={handleRestart}
            className="inline-flex items-center gap-2 rounded-lg bg-cinnabar-600 px-6 py-3 font-serif text-lg text-rice-50 shadow-scroll transition-colors hover:bg-cinnabar-700"
          >
            <RotateCcw size={20} /> 再来一组
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="inline-flex items-center gap-1 rounded-lg border border-ink-200 px-6 py-3 font-serif text-lg text-ink-600 transition-colors hover:bg-ink-50 dark:border-ink-600 dark:text-rice-300 dark:hover:bg-ink-700"
            >
              收起
            </button>
          )}
        </div>
      </div>
    );
  }

  // ===== 答题界面 =====
  return (
    <div className="flex flex-col">
      {/* 进度条 + 关闭 */}
      <div className="mb-4 flex items-center gap-3">
        <span className="font-serif text-sm text-bronze-500">
          第 {currentIndex + 1} / {questions.length} 题
        </span>
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-600">
          <motion.div
            className="h-full rounded-full bg-cinnabar-500"
            initial={{ width: 0 }}
            animate={{
              width: `${((currentIndex + (answered ? 1 : 0)) / questions.length) * 100}%`,
            }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <span className="font-serif text-sm text-cinnabar-600">✓ {score}</span>
        {onClose && (
          <button
            onClick={onClose}
            className="text-ink-300 transition-colors hover:text-ink-500 dark:text-rice-400"
            aria-label="关闭"
          >
            <X size={20} />
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.25 }}
        >
          {/* 题型标签 */}
          <div className="mb-3 inline-flex items-center gap-1 rounded-full bg-bronze-500/10 px-3 py-1 text-xs text-bronze-500">
            <BookOpen size={12} />
            {current.type === "fill_blank" && "填空题"}
            {current.type === "select_original" && "选择题 · 选原文"}
            {current.type === "select_translation" && "选择题 · 选译文"}
            {current.type === "select_source" && "选择题 · 选出处"}
          </div>

          {/* 题干 */}
          <h3 className="mb-5 font-serif text-xl leading-relaxed text-ink-800 dark:text-rice-50 md:text-2xl">
            {current.question}
          </h3>

          {/* 选择题选项 */}
          {current.type !== "fill_blank" && (
            <div className="space-y-3">
              {current.options.map((opt, i) => {
                const isSelected = selectedOption === opt;
                const isCorrect = opt === current.correctAnswer;
                const showCorrect = answered && isCorrect;
                const showWrong = answered && isSelected && !isCorrect;

                return (
                  <button
                    key={i}
                    disabled={answered}
                    onClick={() => {
                      if (!answered) {
                        setSelectedOption(opt);
                        setSubmitted(true);
                      }
                    }}
                    className={clsx(
                      "flex w-full items-center gap-3 rounded-lg border-2 px-5 py-4 text-left font-serif text-lg transition-all",
                      !answered && isSelected && "border-cinnabar-500 bg-cinnabar-50 dark:bg-cinnabar-900/20",
                      !answered && !isSelected && "border-ink-100 hover:border-cinnabar-300 hover:bg-rice-50 dark:border-ink-600 dark:hover:bg-ink-700",
                      showCorrect && "border-green-600 bg-green-50 dark:bg-green-900/20",
                      showWrong && "border-cinnabar-600 bg-cinnabar-50 dark:bg-cinnabar-900/20",
                      answered && !showCorrect && !showWrong && "border-ink-100 opacity-60 dark:border-ink-600"
                    )}
                  >
                    <span
                      className={clsx(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-bold text-sm",
                        !answered && isSelected && "bg-cinnabar-500 text-rice-50",
                        !answered && !isSelected && "bg-ink-100 text-ink-500 dark:bg-ink-600 dark:text-rice-300",
                        showCorrect && "bg-green-600 text-white",
                        showWrong && "bg-cinnabar-600 text-rice-50",
                        answered && !showCorrect && !showWrong && "bg-ink-100 text-ink-400 dark:bg-ink-600"
                      )}
                    >
                      {showCorrect ? (
                        <Check size={18} />
                      ) : showWrong ? (
                        <X size={18} />
                      ) : (
                        String.fromCharCode(65 + i)
                      )}
                    </span>
                    <span className="flex-1 text-ink-700 dark:text-rice-200">{opt}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* 填空题输入 */}
          {current.type === "fill_blank" && (
            <div>
              <input
                type="text"
                value={fillAnswer}
                disabled={answered}
                onChange={(e) => {
                  setFillAnswer(e.target.value);
                  setSubmitted(e.target.value.trim().length > 0);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && submitted && !answered) checkAnswer();
                }}
                placeholder="请输入答案…"
                className={clsx(
                  "w-full rounded-lg border-2 px-5 py-4 font-serif text-xl text-ink-800 outline-none transition-all dark:bg-ink-700 dark:text-rice-50",
                  !answered && "border-ink-200 focus:border-cinnabar-500 dark:border-ink-600",
                  answered && isFillCorrect && "border-green-600 bg-green-50 dark:bg-green-900/20",
                  answered && !isFillCorrect && "border-cinnabar-600 bg-cinnabar-50 dark:bg-cinnabar-900/20"
                )}
              />
              {answered && (
                <p className="mt-2 font-serif text-base text-ink-600 dark:text-rice-300">
                  正确答案：<span className="font-bold text-cinnabar-600">{current.correctAnswer}</span>
                </p>
              )}
            </div>
          )}

          {/* 答案反馈区 */}
          <AnimatePresence>
            {answered && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-5 overflow-hidden"
              >
                <div
                  className={clsx(
                    "rounded-lg border-l-4 p-4",
                    (current.type === "fill_blank" ? isFillCorrect : selectedOption === current.correctAnswer)
                      ? "border-green-600 bg-green-50/60 dark:bg-green-900/10"
                      : "border-cinnabar-600 bg-cinnabar-50/60 dark:bg-cinnabar-900/10"
                  )}
                >
                  <div className="mb-2 flex items-center gap-2">
                    {(current.type === "fill_blank" ? isFillCorrect : selectedOption === current.correctAnswer) ? (
                      <>
                        <span className="text-2xl text-cinnabar-600">✓</span>
                        <span className="font-serif text-lg font-bold text-cinnabar-600">
                          {encouragement}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="text-2xl text-cinnabar-600">✗</span>
                        <span className="font-serif text-lg font-bold text-cinnabar-600">
                          差之毫厘
                        </span>
                      </>
                    )}
                  </div>
                  <p className="font-serif text-base leading-relaxed text-ink-700 dark:text-rice-200">
                    {current.explanation}
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-sm text-bronze-500">
                    <BookOpen size={14} />
                    <span>出处：{current.source}</span>
                  </div>
                  <p className="mt-1 font-serif text-sm text-ink-400">
                    原文：{current.original_text}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 操作按钮 */}
          <div className="mt-6 flex justify-end gap-3">
            {!answered ? (
              <button
                onClick={checkAnswer}
                disabled={!submitted}
                className={clsx(
                  "inline-flex items-center gap-1 rounded-lg px-6 py-3 font-serif text-lg transition-all",
                  submitted
                    ? "bg-cinnabar-600 text-rice-50 shadow-scroll hover:bg-cinnabar-700"
                    : "cursor-not-allowed bg-ink-100 text-ink-300 dark:bg-ink-600 dark:text-rice-500"
                )}
              >
                <Sparkles size={18} /> 确认
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="inline-flex items-center gap-1 rounded-lg bg-cinnabar-600 px-6 py-3 font-serif text-lg text-rice-50 shadow-scroll transition-colors hover:bg-cinnabar-700"
              >
                {isLast ? "查看结果" : "下一题"}
                <ChevronRight size={18} />
              </button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

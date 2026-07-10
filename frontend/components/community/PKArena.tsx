"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Swords,
  Clock,
  CheckCircle2,
  XCircle,
  Trophy,
  Zap,
  User,
} from "lucide-react";
import clsx from "clsx";
import type { PKMatchResult, PKSettlement, PKQuestion } from "@/lib/types";

type Phase = "idle" | "matching" | "playing" | "result";

interface PKArenaProps {
  onMatch?: () => Promise<PKMatchResult>;
  onSubmit?: (pkId: string, answers: { questionIndex: number; selectedOption: number }[]) => Promise<PKSettlement>;
}

export default function PKArena({ onMatch, onSubmit }: PKArenaProps) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [matchResult, setMatchResult] = useState<PKMatchResult | null>(null);
  const [settlement, setSettlement] = useState<PKSettlement | null>(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [timeLeft, setTimeLeft] = useState(300);

  const handleMatch = async () => {
    setPhase("matching");
    try {
      const result = onMatch ? await onMatch() : null;
      if (result) {
        setMatchResult(result);
        setTimeLeft(result.timeLimitSeconds);
        setPhase("playing");
        // 简单倒计时
        const timer = setInterval(() => {
          setTimeLeft((t) => {
            if (t <= 1) {
              clearInterval(timer);
              return 0;
            }
            return t - 1;
          });
        }, 1000);
      }
    } catch {
      setPhase("idle");
    }
  };

  const handleSelectAnswer = (questionIndex: number, optionIndex: number) => {
    setAnswers({ ...answers, [questionIndex]: optionIndex });
  };

  const handleNext = () => {
    if (!matchResult) return;
    if (currentQ < matchResult.questions.length - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (!matchResult || !onSubmit) return;
    const answerList = Object.entries(answers).map(([qi, opt]) => ({
      questionIndex: parseInt(qi),
      selectedOption: opt,
    }));
    const result = await onSubmit(matchResult.pkId, answerList);
    setSettlement(result);
    setPhase("result");
  };

  const handleReset = () => {
    setPhase("idle");
    setMatchResult(null);
    setSettlement(null);
    setCurrentQ(0);
    setAnswers({});
  };

  return (
    <div className="paper-card overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center gap-2 border-b border-ink-100 bg-cinnabar-600/5 px-5 py-4 dark:border-ink-600">
        <Swords size={20} className="text-cinnabar-600" />
        <h3 className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-50">
          论语 PK 竞技场
        </h3>
        <span className="ml-auto rounded-full bg-cinnabar-600/10 px-2 py-0.5 text-xs text-cinnabar-600">
          按段位匹配
        </span>
      </div>

      <div className="p-5">
        <AnimatePresence mode="wait">
          {/* 待机状态 */}
          {phase === "idle" && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center py-8 text-center"
            >
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cinnabar-600/10">
                <Swords size={40} className="text-cinnabar-600" />
              </div>
              <h4 className="mb-2 font-serif text-xl font-bold text-ink-800 dark:text-rice-50">
                来一场知识对决！
              </h4>
              <p className="mb-6 max-w-sm text-sm text-ink-500 dark:text-rice-300">
                系统将根据你的段位匹配实力相近的对手，5题决胜负。胜者获得经验值与段位提升！
              </p>
              <button onClick={handleMatch} className="seal-btn px-8 py-3 text-base">
                <Zap size={18} className="mr-1" /> 开始匹配
              </button>
            </motion.div>
          )}

          {/* 匹配中 */}
          {phase === "matching" && (
            <motion.div
              key="matching"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center py-12"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="mb-4 flex h-16 w-16 items-center justify-center rounded-full border-4 border-cinnabar-200 border-t-cinnabar-600"
              />
              <p className="font-serif text-lg text-ink-600 dark:text-rice-300">
                正在匹配对手...
              </p>
            </motion.div>
          )}

          {/* 答题中 */}
          {phase === "playing" && matchResult && (
            <motion.div
              key="playing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* 对手信息 + 倒计时 */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ink-600 font-serif text-sm font-bold text-rice-50">
                    {matchResult.opponent.nickname?.[0] || "U"}
                  </span>
                  <div>
                    <div className="text-xs text-ink-400">对手</div>
                    <div className="text-sm font-medium text-ink-700 dark:text-rice-200">
                      {matchResult.opponent.nickname || matchResult.opponent.username}
                      <span className="ml-1 text-xs text-bronze-500">Lv.{matchResult.opponent.level}</span>
                    </div>
                  </div>
                </div>
                <div className={clsx(
                  "flex items-center gap-1 rounded-md px-3 py-1.5 font-serif text-lg font-bold",
                  timeLeft < 30 ? "bg-cinnabar-600/10 text-cinnabar-600" : "text-ink-600 dark:text-rice-300"
                )}>
                  <Clock size={16} />
                  {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, "0")}
                </div>
              </div>

              {/* 题目进度 */}
              <div className="mb-4 flex gap-1">
                {matchResult.questions.map((_, i) => (
                  <div
                    key={i}
                    className={clsx(
                      "h-1.5 flex-1 rounded-full transition-colors",
                      i < currentQ ? "bg-cinnabar-600" : i === currentQ ? "bg-bronze-400" : "bg-ink-200 dark:bg-ink-600"
                    )}
                  />
                ))}
              </div>

              {/* 当前题目 */}
              <PKQuestionView
                question={matchResult.questions[currentQ]}
                selectedIndex={answers[currentQ]}
                onSelect={(opt) => handleSelectAnswer(currentQ, opt)}
              />

              {/* 下一题/提交 */}
              <div className="mt-4 flex justify-end">
                <button
                  onClick={handleNext}
                  disabled={answers[currentQ] === undefined}
                  className="seal-btn px-6 py-2 text-sm disabled:opacity-50"
                >
                  {currentQ < matchResult.questions.length - 1 ? "下一题" : "提交答案"}
                </button>
              </div>
            </motion.div>
          )}

          {/* 结算 */}
          {phase === "result" && settlement && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center py-6 text-center"
            >
              {/* 胜负图标 */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
                className={clsx(
                  "mb-4 flex h-20 w-20 items-center justify-center rounded-full",
                  settlement.result === "win" && "bg-yellow-500/10",
                  settlement.result === "lose" && "bg-ink-400/10",
                  settlement.result === "draw" && "bg-bronze-500/10"
                )}
              >
                {settlement.result === "win" ? (
                  <Trophy size={40} className="text-yellow-500" />
                ) : settlement.result === "lose" ? (
                  <XCircle size={40} className="text-ink-400" />
                ) : (
                  <User size={40} className="text-bronze-500" />
                )}
              </motion.div>

              <h4 className="mb-1 font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
                {settlement.result === "win" ? "胜利！" : settlement.result === "lose" ? "惜败" : "平局"}
              </h4>
              <p className="mb-4 text-sm text-ink-500">
                答对 {settlement.correctCount}/{settlement.totalCount} 题
              </p>

              {/* 比分 */}
              <div className="mb-4 flex items-center gap-6">
                <div className="text-center">
                  <div className="text-xs text-ink-400">我的得分</div>
                  <div className="font-serif text-3xl font-bold text-cinnabar-600">{settlement.myScore}</div>
                </div>
                <span className="text-xl text-ink-300">VS</span>
                <div className="text-center">
                  <div className="text-xs text-ink-400">对手得分</div>
                  <div className="font-serif text-3xl font-bold text-ink-500">{settlement.opponentScore}</div>
                </div>
              </div>

              {/* 奖励 */}
              <div className="mb-6 flex gap-4">
                <div className="rounded-md bg-bronze-500/10 px-4 py-2">
                  <div className="flex items-center gap-1 text-xs text-bronze-600">
                    <Zap size={12} /> 经验值
                  </div>
                  <div className="font-serif text-lg font-bold text-bronze-600">+{settlement.expGained}</div>
                </div>
                <div className="rounded-md bg-cinnabar-600/10 px-4 py-2">
                  <div className="text-xs text-cinnabar-600">段位变化</div>
                  <div className={clsx(
                    "font-serif text-lg font-bold",
                    settlement.ratingChange >= 0 ? "text-cinnabar-600" : "text-ink-500"
                  )}>
                    {settlement.ratingChange >= 0 ? "+" : ""}{settlement.ratingChange}
                  </div>
                </div>
                <div className="rounded-md bg-ink-600/10 px-4 py-2">
                  <div className="text-xs text-ink-600">当前段位分</div>
                  <div className="font-serif text-lg font-bold text-ink-600">{settlement.newRating}</div>
                </div>
              </div>

              <button onClick={handleReset} className="seal-btn px-8 py-2">
                再来一局
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function PKQuestionView({
  question,
  selectedIndex,
  onSelect,
}: {
  question: PKQuestion;
  selectedIndex?: number;
  onSelect: (optionIndex: number) => void;
}) {
  return (
    <motion.div
      key={question.index}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="mb-3 text-xs text-bronze-500">
        第 {question.index + 1} 题 {question.verseSource && `· ${question.verseSource}`}
      </div>
      <p className="mb-4 font-serif text-lg text-ink-800 dark:text-rice-50">
        {question.question}
      </p>
      <div className="space-y-2">
        {question.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            className={clsx(
              "flex w-full items-center gap-3 rounded-md border px-4 py-3 text-left text-sm transition-all",
              selectedIndex === i
                ? "border-cinnabar-500 bg-cinnabar-600/5 text-ink-800 dark:text-rice-50"
                : "border-ink-200 bg-rice-50 text-ink-600 hover:border-cinnabar-300 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-300"
            )}
          >
            <span className={clsx(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-serif text-xs font-bold",
              selectedIndex === i ? "bg-cinnabar-600 text-rice-50" : "bg-ink-200 text-ink-500 dark:bg-ink-600"
            )}>
              {String.fromCharCode(65 + i)}
            </span>
            {opt}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

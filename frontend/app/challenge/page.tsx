"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass,
  Lock,
  CheckCircle,
  Star,
  Trophy,
  ArrowRight,
  RotateCcw,
  ChevronLeft,
  Clock,
  AlertCircle,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  ChallengeLevel,
  ChallengeQuestion,
  ChallengeAnswer,
  ChallengeResult,
  QuestionFeedback,
} from "@/lib/types";

export default function ChallengePage() {
  const [levels, setLevels] = useState<ChallengeLevel[]>([]);
  const [currentLevel, setCurrentLevel] = useState<ChallengeLevel | null>(null);
  const [questions, setQuestions] = useState<ChallengeQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<ChallengeAnswer[]>([]);
  const [result, setResult] = useState<ChallengeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [answerInput, setAnswerInput] = useState("");
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showWrongOnly, setShowWrongOnly] = useState(false);

  // 加载关卡列表
  useEffect(() => {
    api.getChallengeLevels().then((data) => {
      setLevels(data);
      setLoading(false);
    });
  }, []);

  // 开始某一关
  const startLevel = useCallback((level: ChallengeLevel) => {
    if (level.locked) return;
    setLoading(true);
    api.getChallengeQuestions(level.chapterId).then((qs) => {
      setQuestions(qs);
      setCurrentLevel(level);
      setCurrentIndex(0);
      setAnswers([]);
      setResult(null);
      setAnswerInput("");
      setSelectedOption(null);
      setShowWrongOnly(false);
      setLoading(false);
    });
  }, []);

  // 返回关卡列表
  const backToLevels = useCallback(() => {
    setCurrentLevel(null);
    setQuestions([]);
    setCurrentIndex(0);
    setAnswers([]);
    setResult(null);
    setAnswerInput("");
    setSelectedOption(null);
    setShowWrongOnly(false);
  }, []);

  // 提交当前答案并进入下一题
  const handleNext = useCallback(() => {
    const q = questions[currentIndex];
    if (!q) return;

    const userAnswer =
      q.questionType === "choice" ? selectedOption : answerInput.trim();

    const answer: ChallengeAnswer = {
      quizId: q.quizId,
      userAnswer,
      timeSpent: 0,
    };

    const newAnswers = [...answers, answer];
    setAnswers(newAnswers);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
      setAnswerInput("");
      setSelectedOption(null);
    } else {
      // 最后一题，提交整关
      setLoading(true);
      api.submitChallengeAnswers(currentLevel!.chapterId, newAnswers, questions).then((res) => {
        setResult(res);
        // 更新关卡状态
        setLevels((prev) =>
          prev.map((level) => {
            if (level.id !== currentLevel!.id) return level;
            const passed = res.passed;
            const bestScore = Math.max(level.bestScore ?? 0, res.score);
            const stars = bestScore >= 100 ? 3 : bestScore >= 80 ? 2 : bestScore >= 70 ? 1 : 0;
            return { ...level, passed, bestScore, stars };
          })
        );
        // 解锁下一关
        setLevels((prev) =>
          prev.map((level, idx) => {
            const prevLevel = prev[idx - 1];
            if (idx === 0) return level;
            if (prevLevel && prevLevel.passed && level.id !== currentLevel!.id) {
              return { ...level, locked: false };
            }
            return level;
          })
        );
        setLoading(false);
      });
    }
  }, [questions, currentIndex, answers, selectedOption, answerInput, currentLevel]);

  // 重试当前关卡
  const retryLevel = useCallback(() => {
    if (!currentLevel) return;
    startLevel(currentLevel);
  }, [currentLevel, startLevel]);

  if (loading && !currentLevel && !levels.length) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在加载闯关地图……</div>
      </div>
    );
  }

  // 结果页
  if (result) {
    return (
      <ChallengeResultView
        result={result}
        questions={questions}
        onRetry={retryLevel}
        onBack={backToLevels}
        showWrongOnly={showWrongOnly}
        setShowWrongOnly={setShowWrongOnly}
      />
    );
  }

  // 答题页
  if (currentLevel && questions.length > 0) {
    return (
      <ChallengeQuizView
        level={currentLevel}
        question={questions[currentIndex]}
        currentIndex={currentIndex}
        total={questions.length}
        answerInput={answerInput}
        setAnswerInput={setAnswerInput}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        onNext={handleNext}
        onBack={backToLevels}
      />
    );
  }

  // 关卡地图
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8 text-center">
        <h1 className="font-serif text-3xl font-bold text-ink-800">经典闯关</h1>
        <p className="mt-2 text-ink-500">逐章挑战，以题促学，解锁你的论语通关之路</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {levels.map((level) => (
          <LevelCard
            key={level.id}
            level={level}
            onClick={() => startLevel(level)}
          />
        ))}
      </div>

      {levels.length === 0 && !loading && (
        <div className="mt-12 text-center text-ink-400">暂无闯关数据</div>
      )}
    </div>
  );
}

/** 关卡卡片 */
function LevelCard({
  level,
  onClick,
}: {
  level: ChallengeLevel;
  onClick: () => void;
}) {
  return (
    <motion.button
      whileHover={level.locked ? {} : { scale: 1.02 }}
      whileTap={level.locked ? {} : { scale: 0.98 }}
      onClick={onClick}
      disabled={level.locked}
      className={`relative rounded-xl border p-5 text-left transition-shadow ${
        level.locked
          ? "cursor-not-allowed border-ink-200 bg-ink-50/50"
          : level.passed
          ? "border-cinnabar-200 bg-white shadow-scroll hover:shadow-popup"
          : "border-ink-200 bg-white shadow-scroll hover:shadow-popup"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-ink-400">第 {level.order} 关</div>
          <h3 className="mt-1 font-serif text-xl font-bold text-ink-800">
            {level.title}
          </h3>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rice-100">
          {level.locked ? (
            <Lock size={18} className="text-ink-400" />
          ) : level.passed ? (
            <CheckCircle size={20} className="text-cinnabar-600" />
          ) : (
            <Compass size={20} className="text-cinnabar-600" />
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-ink-500">{level.sentenceCount} 句经文</span>
        <div className="flex items-center gap-1">
          {[1, 2, 3].map((i) => (
            <Star
              key={i}
              size={14}
              className={
                i <= level.stars ? "fill-amber-400 text-amber-400" : "text-ink-200"
              }
            />
          ))}
        </div>
      </div>

      {level.bestScore !== undefined && (
        <div className="mt-3 text-xs text-cinnabar-600">
          历史最佳：{level.bestScore} 分
        </div>
      )}
    </motion.button>
  );
}

/** 答题界面 */
function ChallengeQuizView({
  level,
  question,
  currentIndex,
  total,
  answerInput,
  setAnswerInput,
  selectedOption,
  setSelectedOption,
  onNext,
  onBack,
}: {
  level: ChallengeLevel;
  question: ChallengeQuestion;
  currentIndex: number;
  total: number;
  answerInput: string;
  setAnswerInput: (v: string) => void;
  selectedOption: number | null;
  setSelectedOption: (v: number | null) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const isChoice = question.questionType === "choice";
  const canSubmit = isChoice ? selectedOption !== null : answerInput.trim().length > 0;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-sm text-ink-500 hover:text-ink-800"
        >
          <ChevronLeft size={18} />
          返回关卡
        </button>
        <div className="text-sm text-ink-500">
          {level.title} · 第 {currentIndex + 1} / {total} 题
        </div>
      </div>

      {/* 进度条 */}
      <div className="mb-8 h-2 w-full overflow-hidden rounded-full bg-ink-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${((currentIndex + 1) / total) * 100}%` }}
          className="h-full rounded-full bg-cinnabar-600"
          transition={{ duration: 0.3 }}
        />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={question.quizId}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="rounded-2xl border border-ink-100 bg-white p-6 shadow-scroll sm:p-8"
        >
          <div className="mb-2 text-xs font-medium text-cinnabar-600">
            {question.questionType === "choice" && "选择题"}
            {question.questionType === "fill" && "填空题"}
            {question.questionType === "match" && "配对题"}
            {question.questionType === "order" && "排序题"}
            {question.difficulty && ` · 难度 ${question.difficulty}`}
          </div>

          <h2 className="font-serif text-xl font-bold leading-relaxed text-ink-800 sm:text-2xl">
            {question.question}
          </h2>

          <div className="mt-8">
            {isChoice && question.options && (
              <div className="space-y-3">
                {question.options.map((opt) => (
                  <button
                    key={opt.index}
                    onClick={() => setSelectedOption(opt.index)}
                    className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
                      selectedOption === opt.index
                        ? "border-cinnabar-300 bg-cinnabar-50"
                        : "border-ink-200 bg-white hover:bg-rice-50"
                    }`}
                  >
                    <span
                      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        selectedOption === opt.index
                          ? "bg-cinnabar-600 text-white"
                          : "bg-ink-100 text-ink-600"
                      }`}
                    >
                      {String.fromCharCode(65 + opt.index)}
                    </span>
                    <span className="font-kai text-base text-ink-800">{opt.text}</span>
                  </button>
                ))}
              </div>
            )}

            {!isChoice && (
              <div className="space-y-3">
                <input
                  type="text"
                  value={answerInput}
                  onChange={(e) => setAnswerInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && canSubmit && onNext()}
                  placeholder="请输入答案……"
                  className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 font-kai text-lg text-ink-800 outline-none focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
                />
                <p className="text-xs text-ink-400">提示：填写原文中缺失的文字</p>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      <div className="mt-8 flex justify-end">
        <button
          onClick={onNext}
          disabled={!canSubmit}
          className={`flex items-center gap-2 rounded-lg px-6 py-3 font-medium transition-colors ${
            canSubmit
              ? "bg-cinnabar-600 text-white hover:bg-cinnabar-700"
              : "cursor-not-allowed bg-ink-200 text-ink-400"
          }`}
        >
          {currentIndex < total - 1 ? "下一题" : "提交闯关"}
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}

/** 结果界面 */
function ChallengeResultView({
  result,
  questions,
  onRetry,
  onBack,
  showWrongOnly,
  setShowWrongOnly,
}: {
  result: ChallengeResult;
  questions: ChallengeQuestion[];
  onRetry: () => void;
  onBack: () => void;
  showWrongOnly: boolean;
  setShowWrongOnly: (v: boolean) => void;
}) {
  const wrongItems: { feedback: QuestionFeedback; question: ChallengeQuestion | undefined }[] =
    result.results
      .filter((r) => !r.isCorrect)
      .map((feedback) => ({
        feedback,
        question: questions.find((q) => q.quizId === feedback.quizId),
      }));

  return (
    <div className="mx-auto max-w-3xl">
      <div className="rounded-2xl border border-ink-100 bg-white p-8 shadow-scroll text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cinnabar-50"
        >
          {result.passed ? (
            <Trophy size={40} className="text-cinnabar-600" />
          ) : (
            <AlertCircle size={40} className="text-ink-500" />
          )}
        </motion.div>

        <h2 className="font-serif text-2xl font-bold text-ink-800">
          {result.passed ? "闯关成功" : "闯关失败"}
        </h2>
        <p className="mt-2 text-ink-500">
          {result.passed
            ? `恭喜！正确率 ${result.score}%（${result.correctCount}/${result.total}）`
            : `本次正确率 ${result.score}%，达到 ${result.passThreshold}% 即可通关`}
        </p>

        {result.expGained !== undefined && result.expGained > 0 && (
          <div className="mt-3 text-sm font-medium text-cinnabar-600">
            +{result.expGained} 经验值
          </div>
        )}

        <div className="mt-8 flex justify-center gap-4">
          <button
            onClick={onRetry}
            className="flex items-center gap-2 rounded-lg border border-ink-200 bg-white px-5 py-2.5 text-ink-700 hover:bg-rice-50"
          >
            <RotateCcw size={18} />
            重新挑战
          </button>
          <button
            onClick={onBack}
            className="flex items-center gap-2 rounded-lg bg-cinnabar-600 px-5 py-2.5 text-white hover:bg-cinnabar-700"
          >
            <ChevronLeft size={18} />
            返回关卡
          </button>
        </div>
      </div>

      {/* 错题解析 */}
      {wrongItems.length > 0 && (
        <div className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-serif text-lg font-bold text-ink-800">
              <XCircle size={20} className="mr-1 inline text-cinnabar-600" />
              错题解析 ({wrongItems.length})
            </h3>
            <button
              onClick={() => setShowWrongOnly(!showWrongOnly)}
              className="text-sm text-cinnabar-600 hover:underline"
            >
              {showWrongOnly ? "查看全部" : "只看错题"}
            </button>
          </div>

          <div className="space-y-4">
            {(showWrongOnly ? wrongItems : result.results.map((feedback) => ({
              feedback,
              question: questions.find((q) => q.quizId === feedback.quizId),
            })))
              .filter(({ question }) => question)
              .map(({ feedback, question }) => (
                <div
                  key={feedback.quizId}
                  className={`rounded-xl border p-4 ${
                    feedback.isCorrect
                      ? "border-green-200 bg-green-50/50"
                      : "border-cinnabar-200 bg-cinnabar-50/30"
                  }`}
                >
                  <div className="mb-2 flex items-center gap-2">
                    {feedback.isCorrect ? (
                      <CheckCircle size={18} className="text-green-600" />
                    ) : (
                      <XCircle size={18} className="text-cinnabar-600" />
                    )}
                    <span className="font-medium text-ink-800">{question!.question}</span>
                  </div>
                  <div className="text-sm text-ink-600">
                    正确答案：
                    <span className="font-kai font-medium text-ink-800">
                      {question!.questionType === "choice" && question!.options
                        ? question!.options.find((o) => o.index === feedback.correctAnswer)?.text ??
                          String(feedback.correctAnswer)
                        : String(feedback.correctAnswer)}
                    </span>
                  </div>
                  {feedback.explanation && (
                    <div className="mt-1 text-sm text-ink-500">{feedback.explanation}</div>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}

      {wrongItems.length === 0 && (
        <div className="mt-8 rounded-xl border border-green-200 bg-green-50/50 p-6 text-center">
          <CheckCircle size={24} className="mx-auto mb-2 text-green-600" />
          <p className="font-serif text-lg font-bold text-green-800">全对！</p>
          <p className="text-sm text-green-700">这一关你已掌握，继续挑战下一关吧。</p>
        </div>
      )}
    </div>
  );
}

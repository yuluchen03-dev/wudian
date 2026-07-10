"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Check,
  ChevronLeft,
  Eye,
  Flame,
  RotateCcw,
  TrendingUp,
  X,
  Sparkles,
  Clock,
} from "lucide-react";
import { api } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import { useRouter } from "next/navigation";
import type {
  DueReviewItem,
  DueReviewsResponse,
  ReviewStats,
} from "@/lib/types";

type Stage = "loading" | "reviewing" | "finished";

export default function ReviewPage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("loading");
  const [items, setItems] = useState<DueReviewItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showTranslation, setShowTranslation] = useState(false);
  const [results, setResults] = useState<
    { verseId: string; quality: number; correct: boolean }[]
  >([]);
  const [submitting, setSubmitting] = useState(false);

  // 加载数据
  const loadData = useCallback(async () => {
    try {
      const [dueRes, statsRes] = await Promise.all([
        api.getDueReviews(),
        api.getReviewStats(),
      ]);
      setItems(dueRes.items);
      setStats(statsRes);
      setStage(dueRes.items.length > 0 ? "reviewing" : "finished");
    } catch {
      setStage("finished");
    }
  }, []);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }
    loadData();
  }, [loadData, router]);

  // 提交复习结果
  const handleReview = useCallback(
    async (quality: number) => {
      const item = items[currentIndex];
      if (!item || submitting) return;
      setSubmitting(true);
      const correct = quality >= 3;
      try {
        await api.submitReview(item.verse_id, quality, 0);
        const newResults = [
          ...results,
          { verseId: item.verse_id, quality, correct },
        ];
        setResults(newResults);

        if (currentIndex < items.length - 1) {
          setCurrentIndex((i) => i + 1);
          setShowTranslation(false);
        } else {
          setStage("finished");
          // 刷新统计
          try {
            const fresh = await api.getReviewStats();
            setStats(fresh);
          } catch {
            /* ignore */
          }
        }
      } finally {
        setSubmitting(false);
      }
    },
    [items, currentIndex, results, submitting]
  );

  // 重新开始
  const restart = useCallback(() => {
    setResults([]);
    setCurrentIndex(0);
    setShowTranslation(false);
    loadData();
  }, [loadData]);

  if (stage === "loading") {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在准备复习内容……</div>
      </div>
    );
    }

  // 完成或空状态
  if (stage === "finished" && results.length === 0) {
    return <EmptyState stats={stats} onRefresh={restart} />;
  }

  if (stage === "finished") {
    return (
      <ReviewResultView
        total={results.length}
        correctCount={results.filter((r) => r.correct).length}
        stats={stats}
        onRestart={restart}
      />
    );
  }

  // 复习中
  const item = items[currentIndex];
  return (
    <div className="mx-auto max-w-3xl">
      {/* 顶部统计条 */}
      <ReviewHeader
        dueCount={items.length}
        currentIndex={currentIndex}
        stats={stats}
      />

      {/* 复习卡片 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={item.record_id}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.3 }}
          className="mt-6 rounded-2xl border border-ink-100 bg-white p-8 shadow-scroll sm:p-10"
        >
          {/* 原文 */}
          <div className="text-center">
            <div className="mb-2 text-xs text-cinnabar-600">
              第 {currentIndex + 1} / {items.length} 条
            </div>
            <p className="font-kai text-2xl leading-loose text-ink-800 sm:text-3xl">
              {item.original_text}
            </p>
          </div>

          {/* 译文区 */}
          <AnimatePresence>
            {showTranslation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 overflow-hidden"
              >
                <div className="rounded-xl border border-rice-300 bg-rice-50 p-5">
                  <div className="mb-2 flex items-center gap-1.5 text-sm font-medium text-bronze-600">
                    <Sparkles size={14} />
                    译文
                  </div>
                  <p className="font-serif text-base leading-relaxed text-ink-600">
                    {item.translation}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 操作按钮 */}
          <div className="mt-8">
            {!showTranslation ? (
              <button
                onClick={() => setShowTranslation(true)}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-cinnabar-300 bg-cinnabar-50 py-3 font-medium text-cinnabar-700 transition-colors hover:bg-cinnabar-100"
              >
                <Eye size={18} />
                显示译文
              </button>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-3 gap-3"
              >
                <button
                  onClick={() => handleReview(1)}
                  disabled={submitting}
                  className="flex flex-col items-center gap-1 rounded-lg border border-ink-200 bg-white py-4 transition-colors hover:border-cinnabar-300 hover:bg-cinnabar-50 disabled:opacity-50"
                >
                  <X size={22} className="text-cinnabar-600" />
                  <span className="text-sm font-medium text-ink-700">忘了</span>
                </button>
                <button
                  onClick={() => handleReview(3)}
                  disabled={submitting}
                  className="flex flex-col items-center gap-1 rounded-lg border border-bronze-400/50 bg-rice-50 py-4 transition-colors hover:border-bronze-400 hover:bg-rice-100 disabled:opacity-50"
                >
                  <Clock size={22} className="text-bronze-600" />
                  <span className="text-sm font-medium text-ink-700">模糊</span>
                </button>
                <button
                  onClick={() => handleReview(5)}
                  disabled={submitting}
                  className="flex flex-col items-center gap-1 rounded-lg border border-green-300 bg-green-50 py-4 transition-colors hover:border-green-400 hover:bg-green-100 disabled:opacity-50"
                >
                  <Check size={22} className="text-green-600" />
                  <span className="text-sm font-medium text-ink-700">记得</span>
                </button>
              </motion.div>
            )}
          </div>

          {/* SRS 信息 */}
          <div className="mt-6 flex items-center justify-center gap-4 text-xs text-ink-400">
            <span>已复习 {item.repetitions} 次</span>
            <span>·</span>
            <span>间隔 {item.interval_days} 天</span>
            <span>·</span>
            <span>难度 {(item.ease_factor).toFixed(1)}</span>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/** 顶部统计条 */
function ReviewHeader({
  dueCount,
  currentIndex,
  stats,
}: {
  dueCount: number;
  currentIndex: number;
  stats: ReviewStats | null;
}) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4 shadow-scroll">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-cinnabar-600" />
          <span className="font-serif text-lg font-bold text-ink-800">
            间隔复习
          </span>
        </div>
        {stats && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1 text-cinnabar-600">
              <Flame size={16} />
              <span>连续 {stats.streak_days} 天</span>
            </div>
            <div className="flex items-center gap-1 text-bronze-600">
              <TrendingUp size={16} />
              <span>已掌握 {stats.mastered_count}</span>
            </div>
          </div>
        )}
      </div>
      {/* 进度条 */}
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-ink-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{
            width: `${dueCount > 0 ? ((currentIndex + 1) / dueCount) * 100 : 0}%`,
          }}
          className="h-full rounded-full bg-cinnabar-600"
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
}

/** 空状态 */
function EmptyState({
  stats,
  onRefresh,
}: {
  stats: ReviewStats | null;
  onRefresh: () => void;
}) {
  return (
    <div className="mx-auto max-w-2xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-2xl border border-ink-100 bg-white p-12 text-center shadow-scroll"
      >
        <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-rice-100">
          <Sparkles size={48} className="text-bronze-500" />
        </div>
        <h2 className="font-serif text-2xl font-bold text-ink-800">
          今日复习已清空
        </h2>
        <p className="mt-3 text-ink-500">
          学如不及，犹恐失之。暂无待复习的经文，
          <br />
          可去阅读或闯关学习更多经典。
        </p>

        {stats && (
          <div className="mt-8 grid grid-cols-3 gap-4">
            <StatBox label="累计复习" value={stats.total_reviewed} />
            <StatBox label="已掌握" value={stats.mastered_count} />
            <StatBox label="连续天数" value={stats.streak_days} />
          </div>
        )}

        <button
          onClick={onRefresh}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-cinnabar-600 px-6 py-3 font-medium text-white transition-colors hover:bg-cinnabar-700"
        >
          <RotateCcw size={18} />
          刷新
        </button>
      </motion.div>
    </div>
  );
}

/** 复习结果 */
function ReviewResultView({
  total,
  correctCount,
  stats,
  onRestart,
}: {
  total: number;
  correctCount: number;
  stats: ReviewStats | null;
  onRestart: () => void;
}) {
  const accuracy = total > 0 ? Math.round((correctCount / total) * 100) : 0;
  const passed = accuracy >= 60;

  return (
    <div className="mx-auto max-w-2xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-2xl border border-ink-100 bg-white p-8 text-center shadow-scroll sm:p-10"
      >
        <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cinnabar-50">
          {passed ? (
            <Check size={40} className="text-green-600" />
          ) : (
            <RotateCcw size={40} className="text-cinnabar-600" />
          )}
        </div>

        <h2 className="font-serif text-2xl font-bold text-ink-800">
          {passed ? "复习完成" : "继续努力"}
        </h2>
        <p className="mt-2 text-ink-500">
          本次复习 {total} 条，正确 {correctCount} 条，正确率 {accuracy}%
        </p>

        {stats && (
          <div className="mt-8 grid grid-cols-3 gap-4">
            <StatBox label="累计复习" value={stats.total_reviewed} />
            <StatBox label="已掌握" value={stats.mastered_count} />
            <StatBox
              label="记忆保持率"
              value={Math.round(stats.retention_rate * 100)}
              suffix="%"
            />
          </div>
        )}

        <button
          onClick={onRestart}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-cinnabar-600 px-6 py-3 font-medium text-white transition-colors hover:bg-cinnabar-700"
        >
          <RotateCcw size={18} />
          再次复习
        </button>
      </motion.div>
    </div>
  );
}

/** 统计小方块 */
function StatBox({
  label,
  value,
  suffix = "",
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  return (
    <div className="rounded-lg border border-ink-100 bg-rice-50 p-4">
      <div className="font-serif text-2xl font-bold text-cinnabar-600">
        {value}
        {suffix}
      </div>
      <div className="mt-1 text-xs text-ink-500">{label}</div>
    </div>
  );
}

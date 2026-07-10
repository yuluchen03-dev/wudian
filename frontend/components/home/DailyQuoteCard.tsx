"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, MessageCircle, Sparkles } from "lucide-react";
import clsx from "clsx";
import {
  getDailyQuotesRange,
  getDailyQuoteByDate,
  type DailyQuoteItem,
} from "@/lib/quizData";

export default function DailyQuoteCard() {
  // 以今天为中心，前后各 2 天，共 5 张可滑动
  const quotes = useMemo<DailyQuoteItem[]>(() => getDailyQuotesRange(new Date(), 2), []);
  const todayIndex = 2; // 中间为今天
  const [index, setIndex] = useState(todayIndex);

  const current = quotes[index];
  const isToday = index === todayIndex;

  const goPrev = () => setIndex((i) => Math.max(0, i - 1));
  const goNext = () => setIndex((i) => Math.min(quotes.length - 1, i + 1));

  // 预填给 sage-chat 的问题
  const sageQuestion = encodeURIComponent(`孔子您好，请问"${current.text}"这句话该如何深入理解？`);

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
      className="relative"
    >
      {/* 主卡片 */}
      <div
        className="relative overflow-hidden rounded-2xl border border-rice-200 shadow-popup"
        style={{
          background:
            "linear-gradient(135deg, #fdfbf7 0%, #faf6ed 40%, #f5edd9 100%)",
        }}
      >
        {/* 宣纸纹理装饰 */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, #8a8050 1px, transparent 1px), radial-gradient(circle at 70% 60%, #8a8050 1px, transparent 1px)",
            backgroundSize: "40px 40px, 60px 60px",
          }}
        />
        {/* 角落水墨晕染 */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-cinnabar-600/5 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-12 -left-8 h-44 w-44 rounded-full bg-bronze-500/5 blur-3xl" />

        <div className="relative px-7 py-8 md:px-10 md:py-10">
          {/* 顶部标签 */}
          <div className="mb-5 flex items-center justify-between">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-cinnabar-600/10 px-3 py-1 text-xs font-medium text-cinnabar-600">
              <Sparkles size={13} />
              {isToday ? "今日一句" : "往日一句"}
            </div>

            {/* 滑动控制 */}
            <div className="flex items-center gap-2">
              <button
                onClick={goPrev}
                disabled={index === 0}
                className={clsx(
                  "flex h-8 w-8 items-center justify-center rounded-full border transition-all",
                  index === 0
                    ? "cursor-not-allowed border-ink-100 text-ink-200 dark:border-ink-600"
                    : "border-ink-200 text-ink-500 hover:border-cinnabar-400 hover:text-cinnabar-600 dark:border-ink-500 dark:text-rice-300"
                )}
                aria-label="前一天"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="font-serif text-xs text-bronze-500">
                {index - todayIndex === 0 ? "今" : index - todayIndex > 0 ? `+${index - todayIndex}` : index - todayIndex}
              </span>
              <button
                onClick={goNext}
                disabled={index === quotes.length - 1}
                className={clsx(
                  "flex h-8 w-8 items-center justify-center rounded-full border transition-all",
                  index === quotes.length - 1
                    ? "cursor-not-allowed border-ink-100 text-ink-200 dark:border-ink-600"
                    : "border-ink-200 text-ink-500 hover:border-cinnabar-400 hover:text-cinnabar-600 dark:border-ink-500 dark:text-rice-300"
                )}
                aria-label="后一天"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          {/* 卡片内容（带切换动画） */}
          <AnimatePresence mode="wait">
            <motion.div
              key={current.id}
              initial={{ opacity: 0, x: index > todayIndex ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: index > todayIndex ? -20 : 20 }}
              transition={{ duration: 0.25 }}
            >
              {/* 原文 - 楷体大字 */}
              <p className="font-kai text-3xl leading-loose text-ink-800 md:text-4xl">
                {current.text}
              </p>

              {/* 译文 - 小字 */}
              <p className="mt-4 text-base leading-relaxed text-ink-500 dark:text-ink-300 md:text-lg">
                {current.translation}
              </p>

              {/* 出处 - 印章标签 */}
              <div className="mt-5 flex items-center gap-2">
                <span
                  className="inline-flex items-center rounded-sm px-3 py-1 font-serif text-sm font-bold text-rice-50 shadow-sm"
                  style={{ backgroundColor: "#b91c1c" }}
                >
                  {current.source}
                </span>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* 底部按钮 - 与孔子聊聊 */}
          <div className="mt-7 border-t border-rice-200 pt-5">
            <Link
              href={`/sage-chat?q=${sageQuestion}`}
              className="group inline-flex w-full items-center justify-center gap-2 rounded-lg bg-ink-800 px-6 py-3.5 font-serif text-lg text-rice-50 transition-all hover:bg-ink-700 dark:bg-ink-700 dark:hover:bg-ink-600"
            >
              <MessageCircle size={20} className="transition-transform group-hover:scale-110" />
              与孔子聊聊这句话
              <ChevronRight size={18} className="transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* 滑动指示点 */}
      <div className="mt-4 flex justify-center gap-1.5">
        {quotes.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className={clsx(
              "h-1.5 rounded-full transition-all",
              i === index ? "w-6 bg-cinnabar-600" : "w-1.5 bg-ink-200 hover:bg-ink-300 dark:bg-ink-500"
            )}
            aria-label={`第 ${i + 1} 张`}
          />
        ))}
      </div>
    </motion.section>
  );
}

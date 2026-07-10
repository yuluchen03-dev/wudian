"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Flame, ChevronRight, Sparkles, MessagesSquare, ArrowRight, Zap, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Book, DailyQuote, LearningProgress } from "@/lib/types";
import { InkDivider, SectionTitle, CTAButton } from "@/components/ui/ChineseDecor";
import DailyQuoteCard from "@/components/home/DailyQuoteCard";
import QuickQuiz from "@/components/quiz/QuickQuiz";
import { getBookCoverImage, pageBackgrounds } from "@/lib/visualAssets";

export default function HomePage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [dailyQuote, setDailyQuote] = useState<DailyQuote | null>(null);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [showQuiz, setShowQuiz] = useState(false);

  useEffect(() => {
    api.getBooks().then(setBooks);
    api.getDailyQuote().then(setDailyQuote);
    api.getProgress("lunyu").then(setProgress).catch(() => {});
  }, []);

  return (
    <div
      className="breathing-space relative -mx-4 -my-8 px-4 py-8"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(248,245,238,0.84), rgba(248,245,238,0.96)), url(${pageBackgrounds.home})`,
        backgroundSize: "cover",
        backgroundPosition: "center top",
      }}
    >
      {/* Hero - 大留白 + 大字标题 */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="hero-spacing text-center"
      >
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-ink-200 bg-rice-50/60 px-4 py-1.5 text-xs text-ink-500 dark:border-ink-600 dark:bg-ink-700/60 dark:text-rice-300">
          <Sparkles size={12} className="text-cinnabar-600" />
          四书五经 · 文白对照 · 沉浸阅读
        </div>
        <h1 className="hero-title text-5xl text-ink-800 dark:text-rice-50 md:text-7xl lg:text-8xl">
          悟典
        </h1>
        <p className="mt-6 font-serif text-lg text-ink-500 dark:text-rice-300 md:text-xl">
          与千年圣贤对话，悟经典之大义
        </p>
        <InkDivider className="mx-auto mt-8" withSeal />
        
        {/* CTA - 与孔子对话 */}
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link href="/sage-chat">
            <CTAButton size="lg" className="group">
              <MessagesSquare size={20} />
              与孔子对话
              <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
            </CTAButton>
          </Link>
          <Link
            href="/reader?book=lunyu"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-ink-200 bg-white/60 px-8 py-3.5 font-serif text-lg font-medium tracking-wider text-ink-700 shadow-scroll-soft transition-all duration-300 hover:border-bamboo-400 hover:text-bamboo-600 hover:shadow-scroll dark:border-ink-600 dark:bg-ink-700/60 dark:text-rice-200"
          >
            <BookOpen size={20} />
            开始阅读
          </Link>
        </div>
      </motion.section>

      {/* 每日一句 - 精美中式卡片（支持左右滑动、与孔子对话） */}
      <section className="module-gap">
        <DailyQuoteCard />
      </section>

      {/* 快速答题入口 - 今日5题挑战 */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.6 }}
        className="module-gap"
      >
        <div className="relative overflow-hidden rounded-2xl border-2 border-cinnabar-200 bg-gradient-to-br from-cinnabar-50 to-rice-50 p-8 text-center shadow-scroll-soft dark:border-cinnabar-900 dark:from-ink-700 dark:to-ink-800 md:p-10">
          {/* 装饰 */}
          <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-cinnabar-600/5 blur-2xl" />

          <div className="relative">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-cinnabar-600/10 px-4 py-1.5 text-sm font-medium text-cinnabar-600">
              <Zap size={15} />
              游戏化挑战
            </div>
            <h2 className="font-serif text-3xl font-bold text-ink-800 dark:text-rice-50 md:text-4xl">
              今日 5 题挑战
            </h2>
            <p className="mt-3 text-ink-500 dark:text-rice-300 md:text-lg">
              1 分钟速答《论语》经典名句 · 答对有鼓励，答错有讲解
            </p>
            <button
              onClick={() => setShowQuiz(true)}
              className="group mt-6 inline-flex items-center gap-2 rounded-lg bg-cinnabar-600 px-8 py-4 font-serif text-xl text-rice-50 shadow-popup transition-all hover:bg-cinnabar-700 hover:shadow-lg active:scale-95"
            >
              <Zap size={22} className="transition-transform group-hover:scale-110" />
              开始答题
              <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      </motion.section>

      {/* 快速答题弹窗 */}
      <AnimatePresence>
        {showQuiz && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/60 p-4 backdrop-blur-sm"
            onClick={() => setShowQuiz(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              onClick={(e) => e.stopPropagation()}
              className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-rice-50 p-6 shadow-popup dark:bg-ink-800 md:p-8"
            >
              {/* 关闭按钮 */}
              <button
                onClick={() => setShowQuiz(false)}
                className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-ink-100 text-ink-400 transition-colors hover:bg-ink-200 hover:text-ink-600 dark:bg-ink-600 dark:text-rice-400 dark:hover:bg-ink-500"
                aria-label="关闭"
              >
                <X size={18} />
              </button>

              {/* 标题 */}
              <div className="mb-6 text-center">
                <h3 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
                  今日 5 题挑战
                </h3>
                <p className="mt-1 text-sm text-bronze-500">《论语》经典名句速答</p>
              </div>

              <QuickQuiz onClose={() => setShowQuiz(false)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 经典书库 */}
      <section className="module-gap">
        <SectionTitle className="mb-8" withDivider>
          经典书库
        </SectionTitle>
        <div className="grid grid-cols-2 gap-5 md:grid-cols-4 md:gap-6">
          {books.length === 0
            ? // 骨架屏
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="paper-card h-full animate-pulse p-6">
                  <div className="mb-5 h-28 rounded-md bg-ink-100 dark:bg-ink-600" />
                  <div className="h-5 w-2/3 rounded bg-ink-100 dark:bg-ink-600" />
                  <div className="mt-2 h-3 w-1/3 rounded bg-ink-100 dark:bg-ink-600" />
                  <div className="mt-3 space-y-1.5">
                    <div className="h-3 rounded bg-ink-100 dark:bg-ink-600" />
                    <div className="h-3 w-4/5 rounded bg-ink-100 dark:bg-ink-600" />
                  </div>
                </div>
              ))
            : books.map((book, i) => (
                <motion.div
                  key={book.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.08 * i, duration: 0.5 }}
                >
                  <Link href={`/reader?book=${book.id}`}>
                    <div className="paper-card group h-full cursor-pointer p-6 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-popup">
                      <div
                        className="mb-5 flex h-28 items-center justify-center rounded-md font-serif text-4xl font-bold text-rice-50 shadow-md transition-transform duration-300 group-hover:scale-105"
                        style={{
                          backgroundColor: book.coverColor,
                          backgroundImage: `linear-gradient(180deg, rgba(28,25,23,0.08), rgba(28,25,23,0.52)), url(${book.coverImage || getBookCoverImage(book.id)})`,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      >
                        <span className="drop-shadow">{book.title[0]}</span>
                      </div>
                      <h3 className="font-serif text-xl font-semibold text-ink-800 dark:text-rice-50">
                        {book.title}
                      </h3>
                      <p className="mt-1.5 text-xs text-bronze-500 dark:text-rice-400">{book.category}</p>
                      <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-ink-400 dark:text-rice-400">
                        {book.description}
                      </p>
                    </div>
                  </Link>
                </motion.div>
              ))}
        </div>
      </section>

      {/* 学习进度概览 */}
      {progress && (
        <section className="paper-card module-gap p-8 md:p-10">
          <SectionTitle className="mb-6">
            <span className="flex items-center gap-2.5">
              <BookOpen size={24} className="text-cinnabar-600" />
              学习进度
            </span>
          </SectionTitle>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="font-serif text-4xl font-bold text-cinnabar-600 md:text-5xl">
                {progress.readChapters.length}
                <span className="text-lg text-ink-400 md:text-xl">/{progress.totalChapters}</span>
              </div>
              <div className="mt-2 text-xs text-ink-400 dark:text-rice-400 md:text-sm">已读章数</div>
            </div>
            <div className="border-x border-ink-100 dark:border-ink-600">
              <div className="font-serif text-4xl font-bold text-bronze-500 md:text-5xl">
                {Math.round(
                  (progress.readChapters.length / progress.totalChapters) * 100
                )}
                %
              </div>
              <div className="mt-2 text-xs text-ink-400 dark:text-rice-400 md:text-sm">完成度</div>
            </div>
            <div>
              <div className="flex items-center justify-center gap-1.5 font-serif text-4xl font-bold text-cinnabar-600 md:text-5xl">
                <Flame size={28} /> {progress.streakDays}
              </div>
              <div className="mt-2 text-xs text-ink-400 dark:text-rice-400 md:text-sm">连续天数</div>
            </div>
          </div>
          <Link
            href={`/reader?book=lunyu`}
            className="group mt-8 flex items-center justify-center gap-1.5 rounded-md border border-cinnabar-200 bg-cinnabar-50/50 py-3 font-serif text-base text-cinnabar-600 transition-all hover:bg-cinnabar-50 hover:shadow-scroll-soft dark:border-cinnabar-900 dark:bg-cinnabar-900/20 dark:text-cinnabar-400"
          >
            继续阅读《论语》第 {progress.currentChapterOrder} 章
            <ChevronRight size={18} className="transition-transform group-hover:translate-x-1" />
          </Link>
        </section>
      )}
    </div>
  );
}

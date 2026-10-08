"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, BookMarked, BookOpen, Library, MessagesSquare, Quote, ShieldCheck, Sparkles, X, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { Book, LearningProgress } from "@/lib/types";
import DailyQuoteCard from "@/components/home/DailyQuoteCard";
import QuickQuiz from "@/components/quiz/QuickQuiz";
import { getBookCoverImage, pageBackgrounds } from "@/lib/visualAssets";

const trustItems = [
  { icon: BookMarked, label: "原文引用" },
  { icon: ShieldCheck, label: "出处校验" },
  { icon: Sparkles, label: "白话点睛" },
];

export default function HomePage() {
  const reduceMotion = useReducedMotion();
  const [books, setBooks] = useState<Book[]>([]);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const quizDialogRef = useRef<HTMLDivElement>(null);
  const quizCloseRef = useRef<HTMLButtonElement>(null);
  const quizTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    api.getBooks().then(setBooks);
    api.getProgress("lunyu").then(setProgress).catch(() => {});
  }, []);

  useEffect(() => {
    if (!showQuiz) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    quizCloseRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      quizTriggerRef.current?.focus();
    };
  }, [showQuiz]);

  const handleQuizKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      setShowQuiz(false);
      return;
    }
    if (event.key !== "Tab" || !quizDialogRef.current) return;
    const focusable = Array.from(quizDialogRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="-mx-4 -my-8 sm:-mx-6 lg:-mx-8">
      <section data-ui="editorial-hero" className="relative isolate min-h-[560px] overflow-hidden border-b border-[var(--color-line)] lg:min-h-[590px]" style={{ backgroundImage: `url(${pageBackgrounds.home})`, backgroundSize: "cover" }}>
        <div className="absolute inset-0 bg-[var(--color-canvas)]" />
        <div className="absolute inset-y-0 right-0 w-full lg:w-[58%]">
          <div className="absolute inset-0 bg-[url('/agens/sages/scenes/confucius.png')] bg-cover bg-[center_28%]" />
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-canvas)] via-[rgba(245,241,232,0.48)] to-[rgba(36,36,33,0.08)]" />
          <div className="absolute inset-0 bg-gradient-to-t from-[rgba(36,36,33,0.28)] via-transparent to-transparent lg:hidden" />
        </div>

        <motion.div initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : 0.7 }} className="relative z-10 flex min-h-[560px] items-end px-5 pb-10 pt-16 sm:px-8 lg:min-h-[590px] lg:items-center lg:px-14 lg:py-16 xl:px-20">
          <div className="max-w-2xl bg-[rgba(245,241,232,0.84)] p-5 backdrop-blur-[2px] sm:p-7 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
            <div className="mb-5 flex items-center gap-3 text-xs tracking-[0.18em] text-[var(--color-citation)]">
              <span className="h-px w-10 bg-[var(--color-citation)]" />
              基于经典原文的思想问答
            </div>
            <h1 className="display-serif text-6xl font-semibold leading-none text-[var(--color-ink)] sm:text-7xl lg:text-8xl">悟典</h1>
            <p className="display-serif mt-6 max-w-xl text-2xl leading-snug text-[var(--color-ink)] sm:text-3xl">千年经典，不止于阅读</p>
            <p className="mt-4 max-w-lg text-base leading-8 text-[var(--color-muted)] sm:text-lg">向圣贤请教，让每一次回答，都有典可循。原文、译文与思想依据随时可查。</p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Link href="/sage-chat" className="wudian-action px-6 text-sm font-medium"><MessagesSquare size={18} />向孔子请教<ArrowRight size={17} /></Link>
              <Link href="/reader?book=lunyu" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-[4px] border border-[var(--color-action)] bg-[rgba(251,249,243,0.7)] px-6 text-sm font-medium text-[var(--color-action)] transition-colors hover:bg-white"><BookOpen size={18} />漫游经典</Link>
            </div>
          </div>
        </motion.div>
      </section>

      <section data-ui="trust-strip" className="w-full max-w-full overflow-hidden border-b border-[var(--color-line)] bg-[var(--color-action)] text-white">
        <div className="grid w-full min-w-0 divide-x divide-white/15" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
          {trustItems.map(({ icon: Icon, label }) => (
            <div key={label} className="flex min-h-16 min-w-0 flex-col items-center justify-center gap-1 overflow-hidden px-0.5 text-[10px] sm:flex-row sm:gap-2 sm:px-2 sm:text-sm"><Icon size={16} className="shrink-0 text-[#d9c39d]" /><span className="min-w-0 whitespace-nowrap">{label}</span></div>
          ))}
        </div>
      </section>

      <section className="grid gap-0 border-b border-[var(--color-line)] lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.55fr)]">
        <div className="px-5 py-14 sm:px-8 lg:px-14 xl:px-20">
          <div className="mb-7 flex items-end justify-between gap-4">
            <div><div className="text-xs tracking-[0.16em] text-[var(--color-citation)]">今日章句</div><h2 className="display-serif mt-2 text-3xl font-semibold">从一句原文开始</h2></div>
            <Quote className="text-[var(--color-line)]" size={36} />
          </div>
          <DailyQuoteCard />
        </div>
        <div className="flex flex-col justify-center border-t border-[var(--color-line)] bg-[var(--color-highlight)] px-5 py-12 sm:px-8 lg:border-l lg:border-t-0 lg:px-10">
          <span className="mb-5 grid h-11 w-11 place-items-center rounded-[4px] bg-[var(--color-citation)] text-white"><Zap size={20} /></span>
          <h2 className="display-serif text-2xl font-semibold">今日五题</h2>
          <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">用一分钟检验对经典章句的理解，答错即可查看出处与讲解。</p>
          <button ref={quizTriggerRef} onClick={() => setShowQuiz(true)} className="mt-6 flex min-h-11 items-center justify-between border-y border-[var(--color-line)] py-3 text-left text-sm font-medium text-[var(--color-action)]">开始答题 <ArrowRight size={18} /></button>
        </div>
      </section>

      <section className="px-5 py-16 sm:px-8 lg:px-14 xl:px-20">
        <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div><div className="text-xs tracking-[0.16em] text-[var(--color-citation)]">经典书库</div><h2 className="display-serif mt-2 text-3xl font-semibold">循书入道</h2></div>
          <Link href="/reader" className="flex min-h-11 items-center gap-2 text-sm text-[var(--color-action)]">查看全部典籍 <ArrowRight size={16} /></Link>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 md:grid-cols-4 lg:gap-6">
          {(books.length ? books.slice(0, 4) : Array.from({ length: 4 })).map((item, index) => {
            if (!item) return <div key={index} className="aspect-[3/4] animate-pulse rounded-[4px] bg-[var(--color-line)]/50" />;
            const book = item as Book;
            return (
              <motion.div key={book.id} initial={reduceMotion ? false : { opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: reduceMotion ? 0 : index * 0.06 }}>
                <Link href={`/reader?book=${book.id}`} className="group block">
                  <div className="relative aspect-[4/3] overflow-hidden rounded-[4px] border border-[var(--color-line)] bg-[var(--color-action)]">
                    <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-[1.03]" style={{ backgroundImage: `linear-gradient(180deg, rgba(36,36,33,0.04), rgba(36,36,33,0.5)), url(${book.coverImage || getBookCoverImage(book.id)})` }} />
                    <span className="display-serif absolute bottom-3 left-3 text-2xl font-semibold text-white">{book.title}</span>
                  </div>
                  <div className="mt-3 text-xs text-[var(--color-citation)]">{book.category}</div>
                  <p className="mt-1 line-clamp-2 text-sm leading-6 text-[var(--color-muted)]">{book.description}</p>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>

      {progress && (
        <section className="border-y border-[var(--color-line)] bg-[var(--color-sage)] px-5 py-10 sm:px-8 lg:px-14 xl:px-20">
          <div className="grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
            <div><div className="flex items-center gap-2 text-xs tracking-[0.16em] text-[var(--color-action)]"><Library size={15} />你的阅读进度</div><h2 className="display-serif mt-3 text-2xl font-semibold">《论语》第 {progress.currentChapterOrder} 章</h2><p className="mt-2 text-sm text-[var(--color-muted)]">已读 {progress.readChapters.length} / {progress.totalChapters} 章 · 连续 {progress.streakDays} 天</p></div>
            <Link href="/reader?book=lunyu" className="wudian-action px-6 text-sm">继续阅读 <ArrowRight size={17} /></Link>
          </div>
        </section>
      )}

      <AnimatePresence>
        {showQuiz && (
          <motion.div initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 grid place-items-center bg-black/55 p-4 backdrop-blur-sm" onClick={() => setShowQuiz(false)}>
            <motion.div ref={quizDialogRef} role="dialog" aria-modal="true" aria-labelledby="quiz-dialog-title" tabIndex={-1} onKeyDown={handleQuizKeyDown} initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 18 }} onClick={(event) => event.stopPropagation()} className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[6px] bg-[var(--color-surface)] p-6 shadow-popup outline-none md:p-8">
              <button ref={quizCloseRef} onClick={() => setShowQuiz(false)} className="absolute right-4 top-4 grid h-11 w-11 place-items-center" aria-label="关闭答题"><X size={19} /></button>
              <div className="mb-6 pr-12"><div className="text-xs text-[var(--color-citation)]">经典自测</div><h3 id="quiz-dialog-title" className="display-serif mt-1 text-2xl font-semibold">今日五题</h3></div>
              <QuickQuiz onClose={() => setShowQuiz(false)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

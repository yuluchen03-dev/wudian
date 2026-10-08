"use client";

import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";
import { List, X, Check } from "lucide-react";
import clsx from "clsx";
import type { Chapter } from "@/lib/types";
import useDialogFocus from "@/lib/useDialogFocus";

interface ChapterSelectorProps {
  chapters: Chapter[];
  bookTitle: string;
  currentChapterId: string;
  readChapters: number[];
  open: boolean;
  onToggle: () => void;
  onSelect: (chapterId: string) => void;
}

export default function ChapterSelector({
  chapters,
  bookTitle,
  currentChapterId,
  readChapters,
  open,
  onToggle,
  onSelect,
}: ChapterSelectorProps) {
  const currentIndex = chapters.findIndex(
    (chapter) => chapter.id === currentChapterId
  );
  const progressPercent = chapters.length
    ? Math.round((readChapters.length / chapters.length) * 100)
    : 0;
  const { dialogRef, rememberTrigger } = useDialogFocus<HTMLDivElement>(open, onToggle);

  return (
    <>
      <button
        type="button"
        onClick={() => {
          rememberTrigger();
          onToggle();
        }}
        className="flex h-11 cursor-pointer items-center gap-2 rounded-md border border-ink-200 bg-white/70 px-3 text-sm text-ink-700 transition-colors hover:bg-ink-100 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200"
        aria-label="打开章节目录"
        aria-expanded={open}
      >
        <List size={17} />
        <span>目录</span>
        <span className="border-l border-ink-200 pl-2 text-xs tabular-nums text-ink-400 dark:border-ink-500 dark:text-rice-400">
          {currentIndex >= 0 ? currentIndex + 1 : 0}/{chapters.length}
        </span>
      </button>

      {typeof document !== "undefined" && createPortal(
        <AnimatePresence>
          {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-ink-900/30"
              onClick={onToggle}
            />
            <motion.div
              ref={dialogRef}
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 z-50 flex h-full w-[min(20rem,88vw)] flex-col bg-rice-50 shadow-popup dark:bg-ink-800"
              role="dialog"
              aria-modal="true"
              aria-label="章节目录"
              tabIndex={-1}
            >
              <div className="flex items-center justify-between border-b border-ink-100 px-5 py-4 dark:border-ink-600">
                <div>
                  <p className="text-xs text-bronze-600 dark:text-bronze-400">《{bookTitle}》</p>
                  <h2 className="mt-1 font-serif text-xl font-semibold text-ink-800 dark:text-rice-50">
                    章节目录
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={onToggle}
                  className="flex h-11 w-11 cursor-pointer items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-700 dark:hover:bg-ink-700 dark:hover:text-rice-200"
                  aria-label="关闭章节目录"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="border-b border-ink-100 px-5 py-4 dark:border-ink-600">
                <div className="mb-2 flex items-center justify-between text-xs text-ink-500 dark:text-rice-300">
                  <span>阅读进度</span>
                  <span className="tabular-nums">已读 {readChapters.length} / {chapters.length}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-600">
                  <div
                    className="h-full rounded-full bg-bamboo-600 dark:bg-bamboo-400"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
              <ul className="flex-1 overflow-y-auto py-2">
                {chapters.map((chapter) => {
                  const isCurrent = chapter.id === currentChapterId;
                  const isRead = readChapters.includes(chapter.order);
                  return (
                    <li key={chapter.id}>
                      <button
                        type="button"
                        onClick={() => {
                          onSelect(chapter.id);
                          onToggle();
                        }}
                        className={clsx(
                          "flex min-h-14 w-full cursor-pointer items-center justify-between px-5 py-3 text-left transition-colors",
                          isCurrent
                            ? "bg-cinnabar-50 text-cinnabar-700 dark:bg-cinnabar-900/30"
                            : "hover:bg-ink-100 dark:hover:bg-ink-700"
                        )}
                        aria-current={isCurrent ? "page" : undefined}
                      >
                        <span className="flex items-center gap-3">
                          <span
                            className={clsx(
                              "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs tabular-nums",
                              isCurrent
                                ? "bg-cinnabar-600 text-rice-50"
                                : "bg-ink-100 text-ink-400 dark:bg-ink-600"
                            )}
                          >
                            {chapter.order}
                          </span>
                          <span className="font-serif text-ink-700 dark:text-rice-200">
                            {chapter.title}
                          </span>
                        </span>
                        {isRead && (
                          <span className="flex items-center gap-1 text-xs text-bamboo-700 dark:text-bamboo-300">
                            <Check size={14} /> 已读
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </motion.div>
          </>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
}

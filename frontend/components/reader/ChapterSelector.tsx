"use client";

import { motion, AnimatePresence } from "framer-motion";
import { List, X, Check } from "lucide-react";
import clsx from "clsx";
import type { Chapter } from "@/lib/types";

interface ChapterSelectorProps {
  chapters: Chapter[];
  currentChapterId: string;
  readChapters: number[];
  open: boolean;
  onToggle: () => void;
  onSelect: (chapterId: string) => void;
}

export default function ChapterSelector({
  chapters,
  currentChapterId,
  readChapters,
  open,
  onToggle,
  onSelect,
}: ChapterSelectorProps) {
  return (
    <>
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 rounded-md border border-ink-200 bg-rice-50 px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-100 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200"
      >
        <List size={16} /> 章节目录
      </button>

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
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 z-50 h-full w-72 overflow-y-auto bg-rice-50 shadow-popup dark:bg-ink-800"
            >
              <div className="flex items-center justify-between border-b border-ink-100 px-4 py-4 dark:border-ink-600">
                <h3 className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-50">
                  章节目录
                </h3>
                <button
                  onClick={onToggle}
                  className="text-ink-400 hover:text-ink-700 dark:hover:text-rice-200"
                >
                  <X size={20} />
                </button>
              </div>
              <ul className="py-2">
                {chapters.map((chapter) => {
                  const isCurrent = chapter.id === currentChapterId;
                  const isRead = readChapters.includes(chapter.order);
                  return (
                    <li key={chapter.id}>
                      <button
                        onClick={() => {
                          onSelect(chapter.id);
                          onToggle();
                        }}
                        className={clsx(
                          "flex w-full items-center justify-between px-4 py-3 text-left transition-colors",
                          isCurrent
                            ? "bg-cinnabar-50 text-cinnabar-700 dark:bg-cinnabar-900/30"
                            : "hover:bg-ink-100 dark:hover:bg-ink-700"
                        )}
                      >
                        <span className="flex items-center gap-3">
                          <span
                            className={clsx(
                              "flex h-6 w-6 items-center justify-center rounded-full text-xs",
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
                        {isRead && !isCurrent && (
                          <Check size={14} className="text-bronze-500" />
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

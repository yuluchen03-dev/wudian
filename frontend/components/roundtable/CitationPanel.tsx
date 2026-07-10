"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight, Scroll, ExternalLink } from "lucide-react";
import clsx from "clsx";
import type { Citation } from "@/lib/types";
import type { SageRoundSpeech } from "@/lib/roundtableData";

interface CitationPanelProps {
  speeches: SageRoundSpeech[];
  sageNames: Record<string, string>;
}

/**
 * 百家论道 - 引用汇总面板
 * 汇总所有圣贤的引用，可折叠展示
 */
export default function CitationPanel({ speeches, sageNames }: CitationPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  // 汇总所有引用
  const allCitations: Array<{ sageId: string; citation: Citation }> = [];
  for (const speech of speeches) {
    for (const citation of speech.citations) {
      allCitations.push({ sageId: speech.sageId, citation });
    }
  }

  if (allCitations.length === 0) return null;

  return (
    <div className="mx-auto max-w-3xl">
      {/* 可折叠触发条 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          "group flex w-full items-center gap-2 rounded-lg border px-4 py-3 text-left transition-all",
          "border-bronze-400/30 bg-gradient-to-r from-rice-100/80 to-rice-50/60",
          "hover:border-cinnabar-400/40 hover:shadow-scroll-soft",
          "dark:border-ink-600 dark:from-ink-700/60 dark:to-ink-700/40"
        )}
      >
        <Scroll size={14} className="shrink-0 text-bronze-500 dark:text-rice-400" />
        <span
          className="font-kai text-sm tracking-wide text-ink-600 dark:text-rice-300"
          style={{ letterSpacing: "0.05em" }}
        >
          可溯源引用汇总
        </span>
        <span className="rounded-full bg-cinnabar-600/10 px-2 py-0.5 font-serif text-xs font-bold text-cinnabar-600 dark:bg-cinnabar-600/20 dark:text-cinnabar-400">
          {allCitations.length}
        </span>
        <span className="text-xs text-ink-400 dark:text-rice-400">段原文</span>
        <span className="ml-auto shrink-0">
          {isOpen ? (
            <ChevronDown size={14} className="text-ink-400 dark:text-rice-400" />
          ) : (
            <ChevronRight size={14} className="text-ink-400 group-hover:text-cinnabar-500 dark:text-rice-400" />
          )}
        </span>
      </button>

      {/* 展开的引用列表 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5">
              {allCitations.map(({ sageId, citation }, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    "relative overflow-hidden rounded-lg border transition-all",
                    "border-ink-100 bg-white/80",
                    "hover:border-cinnabar-300/50 hover:shadow-scroll-soft",
                    "dark:border-ink-600 dark:bg-ink-700/60"
                  )}
                >
                  {/* 竹简纹理装饰条 */}
                  <div className="absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-bamboo-400 to-bamboo-600 opacity-60" />

                  <div className="pl-3 pr-3 pt-2.5 pb-2">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-bamboo-500/15 font-serif text-[10px] font-bold text-bamboo-700 dark:bg-bamboo-500/20 dark:text-bamboo-400">
                        {idx + 1}
                      </span>
                      <span className="font-serif text-xs font-medium text-ink-600 dark:text-rice-300">
                        {sageNames[sageId]}所引
                      </span>
                      <span
                        className="font-kai text-xs text-ink-500 dark:text-rice-400"
                        style={{ letterSpacing: "0.03em" }}
                      >
                        {citation.source}
                      </span>
                      <span className="ml-auto text-[10px] text-ink-300 dark:text-rice-500">
                        相关度 {Math.round(citation.similarity * 100)}%
                      </span>
                    </div>
                    <p
                      className="font-kai text-sm leading-relaxed text-ink-700 dark:text-rice-200"
                      style={{ letterSpacing: "0.02em" }}
                    >
                      {citation.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* 底部说明 */}
            <div className="mt-2 flex items-center gap-1.5 px-1">
              <span className="h-px flex-1 bg-ink-100 dark:bg-ink-600" />
              <span className="text-[10px] text-ink-300 dark:text-rice-500">
                原文经 RAG 检索匹配，相关度由高到低
              </span>
              <span className="h-px flex-1 bg-ink-100 dark:bg-ink-600" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

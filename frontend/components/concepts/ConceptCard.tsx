"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, BookOpen, Lightbulb, Link2 } from "lucide-react";
import clsx from "clsx";
import type { Concept } from "@/lib/types";

interface ConceptCardProps {
  concept: Concept;
  index: number;
}

export default function ConceptCard({ concept, index }: ConceptCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className={clsx(
        "group relative overflow-hidden rounded-xl border transition-all duration-300",
        "border-ink-200 bg-gradient-to-br from-rice-50 to-rice-100 shadow-scroll",
        "hover:shadow-popup hover:border-cinnabar-300 dark:border-ink-600 dark:from-ink-700 dark:to-ink-800"
      )}
    >
      {/* 水墨晕染装饰 */}
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-cinnabar-600/5 blur-2xl transition-all duration-500 group-hover:bg-cinnabar-600/10" />
      <div className="pointer-events-none absolute -left-12 -bottom-12 h-40 w-40 rounded-full bg-bronze-400/5 blur-3xl" />

      {/* 卡片头部：大字 + 名称 */}
      <div
        className="relative cursor-pointer p-6"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-5">
          {/* 概念大字 */}
          <div className="relative flex-shrink-0">
            <div className="flex h-24 w-24 items-center justify-center rounded-lg bg-rice-100 shadow-inner dark:bg-ink-600">
              <span
                className="font-kai text-6xl font-bold text-ink-800 transition-transform duration-300 group-hover:scale-110 dark:text-rice-100"
                style={{ textShadow: "2px 2px 4px rgba(28,25,23,0.15)" }}
              >
                {concept.name}
              </span>
            </div>
            {/* 朱砂印章装饰 */}
            <div className="absolute -bottom-2 -right-2 flex h-8 w-8 items-center justify-center rounded bg-cinnabar-600 font-serif text-xs text-rice-50 shadow-md">
              印
            </div>
          </div>

          {/* 概念信息 */}
          <div className="flex-1 pt-1">
            <h3 className="font-serif text-2xl font-bold tracking-wide text-ink-800 dark:text-rice-50">
              {concept.name}
            </h3>
            <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-ink-500 dark:text-rice-300">
              {concept.definition}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-bronze-500 dark:text-bronze-400">
              <BookOpen size={13} />
              <span className="font-serif">{concept.quote_source}</span>
            </div>
          </div>

          {/* 展开图标 */}
          <motion.div
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
            className="mt-1 flex-shrink-0 text-ink-400"
          >
            <ChevronDown size={20} />
          </motion.div>
        </div>
      </div>

      {/* 展开详细内容 */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden border-t border-ink-100 dark:border-ink-600"
          >
            <div className="space-y-4 p-6">
              {/* 定义 */}
              <div>
                <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold tracking-wider text-cinnabar-600 dark:text-cinnabar-400">
                  <span className="font-serif">【 释义 】</span>
                </div>
                <p className="text-sm leading-relaxed text-ink-600 dark:text-rice-300">
                  {concept.definition}
                </p>
              </div>

              {/* 经典原句 */}
              <div className="rounded-lg bg-rice-100/60 p-4 dark:bg-ink-600/40">
                <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold tracking-wider text-bronze-500">
                  <BookOpen size={13} />
                  <span className="font-serif">【 经典原句 】</span>
                </div>
                <p className="font-serif text-base leading-loose text-ink-800 dark:text-rice-100">
                  {concept.original_quote}
                </p>
                <p className="mt-1 text-right text-xs text-ink-400">
                  —— {concept.quote_source}
                </p>
              </div>

              {/* 现代类比 */}
              <div>
                <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold tracking-wider text-cinnabar-600 dark:text-cinnabar-400">
                  <Lightbulb size={13} />
                  <span className="font-serif">【 现代类比 】</span>
                </div>
                <p className="text-sm leading-relaxed text-ink-600 dark:text-rice-300">
                  {concept.modern_analogy}
                </p>
              </div>

              {/* 相关经文 */}
              {concept.related_verses.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <Link2 size={14} className="text-ink-400" />
                  <span className="text-xs text-ink-400">相关经文：</span>
                  {concept.related_verses.map((v) => (
                    <span
                      key={v}
                      className="rounded-full bg-ink-100 px-2.5 py-0.5 text-xs text-ink-500 dark:bg-ink-600 dark:text-rice-300"
                    >
                      {v}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

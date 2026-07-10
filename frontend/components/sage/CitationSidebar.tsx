"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronRight,
  BookOpen,
  Scroll,
  ExternalLink,
  Quote,
} from "lucide-react";
import clsx from "clsx";
import type { Citation } from "@/lib/types";

interface CitationSidebarProps {
  citations: Citation[];
  /** 演示模式：增强视觉效果 */
  demoMode?: boolean;
  /** 点击"定位到阅读器"时的回调 */
  onLocate?: (citation: Citation) => void;
}

/**
 * 思想依据侧栏
 * - 移动端（默认）：回答下方的可折叠面板
 * - 桌面端（md+）：右侧悬浮栏
 */
export default function CitationSidebar({
  citations,
  demoMode = false,
  onLocate,
}: CitationSidebarProps) {
  const [isOpen, setIsOpen] = useState(demoMode);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const handleExpand = useCallback((idx: number) => {
    setExpandedIdx((prev) => (prev === idx ? null : idx));
  }, []);

  const normalizedCitations = (citations || [])
    .map(normalizeCitation)
    .filter((citation) => citation.text);

  if (normalizedCitations.length === 0) return null;

  const verseCount = normalizedCitations.filter((c) => c.type === "verse").length;
  const commentaryCount = normalizedCitations.filter(
    (c) => c.type === "commentary"
  ).length;

  return (
    <div
      className={clsx(
        "mt-2",
        // 桌面端：不作为侧栏，保持在消息下方
        "md:mt-3"
      )}
    >
      {/* 可折叠触发条 */}
      <button
        onClick={handleToggle}
        className={clsx(
          "group flex w-full items-center gap-2 rounded-lg border px-3.5 py-2 text-left transition-all",
          "border-bronze-400/30 bg-gradient-to-r from-rice-100/80 to-rice-50/60",
          "hover:border-cinnabar-400/40 hover:shadow-scroll-soft",
          "dark:border-ink-600 dark:from-ink-700/60 dark:to-ink-700/40",
          "dark:hover:border-cinnabar-600/40"
        )}
      >
        <Scroll
          size={14}
          className="shrink-0 text-bronze-500 dark:text-rice-400"
        />
        <span
          className="font-kai text-sm tracking-wide text-ink-600 dark:text-rice-300"
          style={{ letterSpacing: "0.05em" }}
        >
          本次可溯源证据
        </span>
        <span className="rounded-full bg-cinnabar-600/10 px-2 py-0.5 font-serif text-xs font-bold text-cinnabar-600 dark:bg-cinnabar-600/20 dark:text-cinnabar-400">
          {normalizedCitations.length}
        </span>
        <span className="text-xs text-ink-400 dark:text-rice-400">
          段原文
        </span>
        {verseCount > 0 && (
          <span className="hidden text-[11px] text-ink-300 dark:text-rice-500 sm:inline">
            （{verseCount} 经文
            {commentaryCount > 0 && `、${commentaryCount} 注疏`}）
          </span>
        )}
        <span className="ml-auto shrink-0">
          {isOpen ? (
            <ChevronDown
              size={14}
              className="text-ink-400 transition-transform dark:text-rice-400"
            />
          ) : (
            <ChevronRight
              size={14}
              className="text-ink-400 transition-transform group-hover:text-cinnabar-500 dark:text-rice-400"
            />
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
            <div className="mt-1.5 space-y-1.5">
              {normalizedCitations.map((citation, idx) => (
                <CitationCard
                  key={idx}
                  citation={citation}
                  index={idx}
                  expanded={demoMode || expandedIdx === idx}
                  onExpand={() => handleExpand(idx)}
                  onLocate={onLocate}
                  demoMode={demoMode}
                />
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

/* ============ 单条引用卡片 ============ */

interface CitationCardProps {
  citation: Citation;
  index: number;
  expanded: boolean;
  onExpand: () => void;
  onLocate?: (citation: Citation) => void;
  demoMode: boolean;
}

function CitationCard({
  citation,
  index,
  expanded,
  onExpand,
  onLocate,
  demoMode,
}: CitationCardProps) {
  const normalizedCitation = normalizeCitation(citation);
  const citationText = normalizedCitation.text;
  // 提取关键词：取原文中前3个字以上的词组
  const keywords = extractKeywords(citationText);

  // 截取摘要：最多显示前40字
  const excerpt =
    citationText.length > 40 && !expanded
      ? citationText.slice(0, 40) + "……"
      : citationText;

  return (
    <motion.div
      layout
      className={clsx(
        "group relative overflow-hidden rounded-lg border transition-all",
        "border-ink-100 bg-white/80",
        "hover:border-cinnabar-300/50 hover:shadow-scroll-soft",
        "dark:border-ink-600 dark:bg-ink-700/60",
        "dark:hover:border-cinnabar-600/40"
      )}
    >
      {/* 竹简纹理装饰条 */}
      <div className="absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-bamboo-400 to-bamboo-600 opacity-60" />

      {/* 主体内容 */}
      <div className="pl-3 pr-3 pt-2.5 pb-2">
        {/* 头部：序号 + 出处 + 相关度 */}
        <div className="mb-1.5 flex items-center gap-2">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-bamboo-500/15 font-serif text-[10px] font-bold text-bamboo-700 dark:bg-bamboo-500/20 dark:text-bamboo-400">
            {index + 1}
          </span>
          <span
            className="font-kai text-xs text-ink-500 dark:text-rice-400"
            style={{ letterSpacing: "0.03em" }}
          >
            {normalizedCitation.source}
          </span>
          {normalizedCitation.type === "commentary" && (
            <span className="rounded-sm bg-bronze-500/10 px-1.5 py-0.5 text-[10px] text-bronze-600 dark:text-bronze-400">
              注疏
            </span>
          )}
          <span className="ml-auto text-[10px] text-ink-300 dark:text-rice-500">
            相关度 {Math.round(normalizedCitation.similarity * 100)}%
          </span>
        </div>

        {/* 原文摘要 */}
        <button
          onClick={onExpand}
          className="w-full text-left"
        >
          <p
            className={clsx(
              "font-kai leading-relaxed text-ink-700 dark:text-rice-200",
              demoMode ? "text-base" : "text-sm",
              !expanded && "cursor-pointer"
            )}
            style={{ letterSpacing: "0.02em" }}
          >
            {excerpt}
          </p>
        </button>

        {/* 展开详情 */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              {/* 关键词标签 */}
              {keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-full bg-cinnabar-50 px-2 py-0.5 text-[10px] text-cinnabar-600 dark:bg-cinnabar-900/20 dark:text-cinnabar-400"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}

              {/* 操作按钮 */}
              {onLocate && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onLocate(normalizedCitation);
                  }}
                  className="mt-2 flex items-center gap-1 text-[11px] text-bamboo-600 transition-colors hover:text-bamboo-700 dark:text-bamboo-400 dark:hover:text-bamboo-300"
                >
                  <ExternalLink size={11} />
                  定位到阅读器
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/* ============ 工具函数 ============ */

type BackendCitationShape = Citation & {
  original?: string;
  source?: string;
  verifiable?: boolean;
  原文?: string;
  出处?: string;
};

function normalizeCitation(citation: BackendCitationShape): Citation {
  const text = citation.text || citation.original || citation.原文 || "";
  const source = citation.source || citation.出处 || "未知出处";
  const similarity =
    typeof citation.similarity === "number"
      ? citation.similarity
      : citation.verifiable === false
        ? 0
        : 1;

  return {
    ...citation,
    text,
    source,
    similarity,
    type: citation.type === "commentary" ? "commentary" : "verse",
  };
}

/**
 * 从原文中提取关键词（简单实现：取引号内容或连续2-4字词组）
 */
function extractKeywords(text: string): string[] {
  const keywords: string[] = [];

  // 提取引号中的内容
  const quoted = text.match(/[「」『』"""][^「」『』"""]+[「」『』"""]/g);
  if (quoted) {
    quoted.forEach((q) => {
      const clean = q.replace(/[「」『』"""]/g, "").trim();
      if (clean.length >= 2 && clean.length <= 6) {
        keywords.push(clean);
      }
    });
  }

  // 提取关键短语：连续2-4字的常用组合
  const phrases = [
    "仁", "义", "礼", "智", "信", "忠", "孝", "悌",
    "君子", "小人", "圣人", "贤人", "善", "恶",
    "修身", "齐家", "治国", "平天下", "知行合一",
    "克己复礼", "中庸", "仁义", "道德",
  ];

  for (const phrase of phrases) {
    if (text.includes(phrase) && !keywords.includes(phrase)) {
      keywords.push(phrase);
    }
  }

  return keywords.slice(0, 5);
}

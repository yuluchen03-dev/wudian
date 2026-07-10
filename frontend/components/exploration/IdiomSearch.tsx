"use client";

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, BookText, Quote, Lightbulb, Tag } from "lucide-react";
import clsx from "clsx";
import type { Idiom } from "@/lib/types";

interface IdiomSearchProps {
  idioms: Idiom[];
}

export default function IdiomSearch({ idioms }: IdiomSearchProps) {
  const [query, setQuery] = useState("");
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [debouncedQuery, setDebouncedQuery] = useState("");

  // 防抖搜索
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(timer);
  }, [query]);

  // 所有标签
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    idioms.forEach((i) => i.tags?.forEach((t) => tags.add(t)));
    return Array.from(tags).sort();
  }, [idioms]);

  // 筛选结果
  const filteredIdioms = useMemo(() => {
    let result = idioms;

    if (activeTag) {
      result = result.filter((i) => i.tags?.includes(activeTag));
    }

    if (debouncedQuery.trim()) {
      const kw = debouncedQuery.toLowerCase().trim();
      result = result.filter(
        (i) =>
          i.idiom.toLowerCase().includes(kw) ||
          i.original_text.toLowerCase().includes(kw) ||
          i.meaning.toLowerCase().includes(kw) ||
          i.source.toLowerCase().includes(kw)
      );
    }

    return result;
  }, [idioms, debouncedQuery, activeTag]);

  return (
    <div>
      {/* 搜索框 */}
      <div className="relative mb-4">
        <Search
          size={18}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-300"
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索成语、原文或释义..."
          className="w-full rounded-lg border border-ink-200 bg-white/80 py-2.5 pl-10 pr-4 text-sm text-ink-800 outline-none transition-all placeholder:text-ink-300 focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
        />
      </div>

      {/* 标签筛选 */}
      <div className="mb-4 flex flex-wrap gap-1.5">
        <button
          onClick={() => setActiveTag(null)}
          className={clsx(
            "rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
            activeTag === null
              ? "bg-cinnabar-600 text-rice-50"
              : "bg-ink-100 text-ink-500 hover:bg-ink-200"
          )}
        >
          全部
        </button>
        {allTags.map((tag) => (
          <button
            key={tag}
            onClick={() => setActiveTag(activeTag === tag ? null : tag)}
            className={clsx(
              "rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
              activeTag === tag
                ? "bg-cinnabar-600 text-rice-50"
                : "bg-ink-100 text-ink-500 hover:bg-ink-200"
            )}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* 结果统计 */}
      <p className="mb-3 text-xs text-ink-400">
        共 {filteredIdioms.length} 条结果
      </p>

      {/* 成语卡片列表 */}
      <div className="grid gap-3 sm:grid-cols-2">
        {filteredIdioms.map((idiom, index) => (
          <motion.div
            key={idiom.idiom}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.4) }}
          >
            <IdiomCard idiom={idiom} highlight={debouncedQuery} />
          </motion.div>
        ))}
      </div>

      {filteredIdioms.length === 0 && (
        <div className="py-12 text-center">
          <Search size={32} className="mx-auto mb-3 text-ink-200" />
          <p className="text-ink-400">未找到相关成语，试试其他关键词？</p>
        </div>
      )}
    </div>
  );
}

/** 单个成语卡片 */
function IdiomCard({ idiom, highlight }: { idiom: Idiom; highlight: string }) {
  return (
    <div className="group rounded-lg border border-ink-100 bg-white/70 p-4 transition-all hover:border-cinnabar-200 hover:shadow-popup">
      {/* 成语名 */}
      <div className="mb-2 flex items-center gap-2">
        <h3 className="font-serif text-lg font-bold text-cinnabar-700">
          {highlightText(idiom.idiom, highlight)}
        </h3>
        <span className="rounded bg-rice-200 px-1.5 py-0.5 text-xs text-bronze-600">
          {idiom.chapter}
        </span>
      </div>

      {/* 原文 */}
      <div className="mb-2 flex items-start gap-2">
        <Quote size={14} className="mt-0.5 flex-shrink-0 text-cinnabar-400" />
        <p className="font-serif text-sm leading-relaxed text-ink-700">
          {highlightText(idiom.original_text, highlight)}
        </p>
      </div>

      {/* 出处 */}
      <div className="mb-2 flex items-center gap-1.5 text-xs text-bronze-500">
        <BookText size={12} />
        <span>{idiom.source} · 第{idiom.verse_num}章</span>
      </div>

      {/* 释义 */}
      <div className="mb-2 flex items-start gap-2">
        <span className="mt-0.5 flex-shrink-0 text-xs font-medium text-ink-400">释义</span>
        <p className="text-sm leading-relaxed text-ink-600">
          {highlightText(idiom.meaning, highlight)}
        </p>
      </div>

      {/* 现代用法 */}
      <div className="flex items-start gap-2">
        <Lightbulb size={14} className="mt-0.5 flex-shrink-0 text-bronze-400" />
        <p className="text-sm leading-relaxed text-ink-500">
          {idiom.modern_usage}
        </p>
      </div>

      {/* 标签 */}
      {idiom.tags && idiom.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1 border-t border-ink-50 pt-2">
          {idiom.tags.map((tag) => (
            <span
              key={tag}
              className="flex items-center gap-0.5 rounded bg-ink-50 px-1.5 py-0.5 text-xs text-ink-400"
            >
              <Tag size={8} />
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/** 高亮关键词 */
function highlightText(text: string, keyword: string): React.ReactNode {
  if (!keyword.trim()) return text;
  const kw = keyword.trim();
  const parts = text.split(new RegExp(`(${escapeRegExp(kw)})`, "gi"));
  return parts.map((part, i) =>
    part.toLowerCase() === kw.toLowerCase() ? (
      <mark key={i} className="rounded bg-cinnabar-100 px-0.5 text-cinnabar-700">
        {part}
      </mark>
    ) : (
      part
    )
  );
}

/** 转义正则特殊字符 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

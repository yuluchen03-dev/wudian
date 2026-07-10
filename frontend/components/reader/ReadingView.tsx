"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Moon,
  Sun,
  Type,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";
import type { Chapter, Entity, Annotation } from "@/lib/types";
import AnnotationPopup from "./AnnotationPopup";
import EntityCard from "./EntityCard";
import ChapterSelector from "./ChapterSelector";
import ImageSourceLink from "./ImageSourceLink";
import AIExplainPanel from "./AIExplainPanel";

interface ReadingViewProps {
  chapter: Chapter;
  chapters: Chapter[];
  entities: Entity[];
  readChapters: number[];
  onChapterChange: (chapterId: string) => void;
  onChapterRead?: (chapterOrder: number) => void;
}

type FontSize = "sm" | "base" | "lg" | "xl";

const fontSizeMap: Record<FontSize, { original: string; translation: string }> =
  {
    sm: { original: "text-base", translation: "text-sm" },
    base: { original: "text-lg", translation: "text-base" },
    lg: { original: "text-xl", translation: "text-lg" },
    xl: { original: "text-2xl", translation: "text-xl" },
  };

export default function ReadingView({
  chapter,
  chapters,
  entities,
  readChapters,
  onChapterChange,
  onChapterRead,
}: ReadingViewProps) {
  const [fontSize, setFontSize] = useState<FontSize>("base");
  const [isDark, setIsDark] = useState(false);

  // 从 localStorage 恢复暗色偏好
  useEffect(() => {
    const saved = localStorage.getItem("wudian_dark") === "true";
    setIsDark(saved);
    document.documentElement.classList.toggle("dark", saved);
  }, []);
  const [showChapterSelector, setShowChapterSelector] = useState(false);
  const [activeAnnotation, setActiveAnnotation] = useState<{
    data: Annotation;
    pos: { x: number; y: number };
  } | null>(null);
  const [activeEntity, setActiveEntity] = useState<{
    data: Entity;
    pos: { x: number; y: number };
  } | null>(null);
  const [aiPanel, setAiPanel] = useState<{
    open: boolean;
    verseId: string;
    original: string;
    translation?: string;
  }>({ open: false, verseId: "", original: "" });
  const containerRef = useRef<HTMLDivElement>(null);

  const entityMap = useMemo(() => {
    const map = new Map<string, Entity>();
    entities.forEach((e) => map.set(e.id, e));
    return map;
  }, [entities]);

  const currentIndex = chapters.findIndex((c) => c.id === chapter.id);
  const prevChapter = chapters[currentIndex - 1];
  const nextChapter = chapters[currentIndex + 1];

  const handleCharClick = (e: React.MouseEvent, annotation: Annotation) => {
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setActiveAnnotation({
      data: annotation,
      pos: { x: rect.left, y: rect.top },
    });
    setActiveEntity(null);
  };

  const handleEntityClick = (e: React.MouseEvent, entityId: string) => {
    const entity = entityMap.get(entityId);
    if (!entity) return;
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setActiveEntity({
      data: entity,
      pos: { x: rect.left, y: rect.top },
    });
    setActiveAnnotation(null);
  };

  /** 渲染原文，生僻字与实体名加可点击标记 */
  const renderOriginal = (text: string, annotations?: Annotation[], entityIds?: string[]) => {
    if (!annotations?.length && !entityIds?.length) return text;

    // 收集需要标记的片段
    const marks: { char: string; type: "annotation" | "entity"; data?: Annotation; entityId?: string }[] = [];
    annotations?.forEach((a) => marks.push({ char: a.char, type: "annotation", data: a }));
    entityIds?.forEach((eid) => {
      const ent = entityMap.get(eid);
      if (ent) marks.push({ char: ent.name, type: "entity", entityId: eid });
    });

    // 按长度降序排序，避免短名先匹配
    const sorted = [...marks].sort((a, b) => b.char.length - a.char.length);
    const segments: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      let found = false;
      for (const mark of sorted) {
        const idx = remaining.indexOf(mark.char);
        if (idx === 0) {
          if (mark.type === "annotation" && mark.data) {
            segments.push(
              <span
                key={`a-${key++}`}
                className="rare-char"
                onClick={(e) => handleCharClick(e, mark.data!)}
              >
                {mark.char}
              </span>
            );
          } else if (mark.type === "entity") {
            segments.push(
              <span
                key={`e-${key++}`}
                className="cursor-pointer border-b border-bronze-400/50 text-cinnabar-700 hover:text-cinnabar-600 dark:text-bronze-400"
                onClick={(e) => handleEntityClick(e, mark.entityId!)}
              >
                {mark.char}
              </span>
            );
          }
          remaining = remaining.slice(mark.char.length);
          found = true;
          break;
        }
      }
      if (!found) {
        segments.push(remaining[0]);
        remaining = remaining.slice(1);
      }
    }
    return segments;
  };

  const toggleDark = () => {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("wudian_dark", String(next)); } catch {}
  };

  return (
    <div ref={containerRef}>
      <div className="min-h-screen bg-rice-50 dark:bg-ink-800">
        {/* 工具栏 */}
        <div className="sticky top-16 z-30 flex flex-wrap items-center justify-between gap-2 border-b border-ink-100 bg-rice-50/80 px-4 py-3 backdrop-blur-md dark:border-ink-600 dark:bg-ink-800/80">
          <div className="flex items-center gap-2">
            <ChapterSelector
              chapters={chapters}
              currentChapterId={chapter.id}
              readChapters={readChapters}
              open={showChapterSelector}
              onToggle={() => setShowChapterSelector(!showChapterSelector)}
              onSelect={onChapterChange}
            />
          </div>

          <div className="flex items-center gap-2">
            {/* 字体大小 */}
            <div className="flex items-center gap-1 rounded-md border border-ink-200 bg-rice-50 px-1 py-1 dark:border-ink-500 dark:bg-ink-700">
              <Type size={14} className="ml-1 text-ink-400" />
              {(["sm", "base", "lg", "xl"] as FontSize[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setFontSize(s)}
                  className={clsx(
                    "rounded px-2 py-0.5 text-xs transition-colors",
                    fontSize === s
                      ? "bg-cinnabar-600 text-rice-50"
                      : "text-ink-500 hover:bg-ink-100 dark:hover:bg-ink-600"
                  )}
                >
                  {s === "sm" ? "小" : s === "base" ? "中" : s === "lg" ? "大" : "特"}
                </button>
              ))}
            </div>

            {/* 影像底本外链 */}
            <ImageSourceLink variant="toolbar" label="影像" />

            {/* 夜间模式 */}
            <button
              onClick={toggleDark}
              className="flex items-center gap-1.5 rounded-md border border-ink-200 bg-rice-50 px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-100 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>

        {/* 章节标题 */}
        <div className="px-4 pt-8 text-center">
          <motion.h2
            key={chapter.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-serif text-3xl font-bold tracking-widest text-ink-800 dark:text-rice-50"
          >
            {chapter.title}
          </motion.h2>
          <div className="classical-divider mx-auto mt-4 w-32" />
        </div>

        {/* 文白对照阅读区 */}
        <div className="mx-auto max-w-4xl px-4 py-8">
          <div className="space-y-6">
            {chapter.sentences.map((pair, idx) => (
              <motion.div
                key={pair.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="grid grid-cols-1 gap-4 border-b border-ink-100 pb-6 last:border-0 dark:border-ink-600 md:grid-cols-2"
              >
                {/* 原文 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-xs text-bronze-500">
                    <BookOpen size={12} /> 原文
                  </div>
                  <p
                    className={clsx(
                      "font-serif leading-loose text-ink-800 dark:text-rice-50",
                      fontSizeMap[fontSize].original
                    )}
                  >
                    {renderOriginal(
                      pair.original,
                      pair.annotations,
                      pair.entityIds
                    )}
                  </p>
                </div>

                {/* 译文 */}
                <div className="space-y-1 md:border-l md:border-ink-100 md:pl-6 dark:md:border-ink-600">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-ink-400">白话译文</div>
                    {/* 问AI按钮 */}
                    <button
                      onClick={() =>
                        setAiPanel({
                          open: true,
                          verseId: pair.id,
                          original: pair.original,
                          translation: pair.translation,
                        })
                      }
                      className="flex items-center gap-1 rounded-full border border-cinnabar-300 bg-cinnabar-50 px-2.5 py-1 text-[11px] text-cinnabar-600 transition-all hover:border-cinnabar-500 hover:bg-cinnabar-100 hover:shadow-sm dark:border-cinnabar-500/40 dark:bg-cinnabar-900/20 dark:text-cinnabar-400 dark:hover:bg-cinnabar-900/30"
                      title="问AI逐句精讲"
                    >
                      <Sparkles size={12} />
                      问AI
                    </button>
                  </div>
                  <p
                    className={clsx(
                      "leading-relaxed text-ink-500 dark:text-rice-300",
                      fontSizeMap[fontSize].translation
                    )}
                  >
                    {pair.translation}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 翻页 */}
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 pb-12">
          <button
            disabled={!prevChapter}
            onClick={() => prevChapter && onChapterChange(prevChapter.id)}
            className={clsx(
              "flex items-center gap-1 rounded-md px-4 py-2 text-sm transition-colors",
              prevChapter
                ? "border border-ink-200 text-ink-700 hover:bg-ink-100 dark:border-ink-500 dark:text-rice-200 dark:hover:bg-ink-700"
                : "cursor-not-allowed border border-ink-100 text-ink-300 dark:border-ink-600"
            )}
          >
            <ChevronLeft size={16} /> 上一章
          </button>

          <button
            onClick={() => onChapterRead?.(chapter.order)}
            className="seal-btn"
          >
            标记本章已读
          </button>

          <button
            disabled={!nextChapter}
            onClick={() => nextChapter && onChapterChange(nextChapter.id)}
            className={clsx(
              "flex items-center gap-1 rounded-md px-4 py-2 text-sm transition-colors",
              nextChapter
                ? "border border-ink-200 text-ink-700 hover:bg-ink-100 dark:border-ink-500 dark:text-rice-200 dark:hover:bg-ink-700"
                : "cursor-not-allowed border border-ink-100 text-ink-300 dark:border-ink-600"
            )}
          >
            下一章 <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* 弹窗 */}
      <AnnotationPopup
        annotation={activeAnnotation?.data ?? null}
        position={activeAnnotation?.pos ?? null}
        onClose={() => setActiveAnnotation(null)}
      />
      <EntityCard
        entity={activeEntity?.data ?? null}
        position={activeEntity?.pos ?? null}
        onClose={() => setActiveEntity(null)}
      />

      {/* AI 逐句精讲面板 */}
      <AIExplainPanel
        open={aiPanel.open}
        verseId={aiPanel.verseId}
        original={aiPanel.original}
        translation={aiPanel.translation}
        onClose={() => setAiPanel((prev) => ({ ...prev, open: false }))}
      />
    </div>
  );
}

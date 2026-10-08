"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  AlertCircle,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Moon,
  RefreshCw,
  Sparkles,
  Sun,
  Type,
} from "lucide-react";
import clsx from "clsx";
import type { Annotation, Chapter, Entity } from "@/lib/types";
import AIExplainPanel from "./AIExplainPanel";
import AnnotationPopup from "./AnnotationPopup";
import ChapterSelector from "./ChapterSelector";
import EntityCard from "./EntityCard";
import ImageSourceLink from "./ImageSourceLink";

interface ReadingViewProps {
  chapter: Chapter | null;
  chapterLoading: boolean;
  chapterError: string | null;
  bookTitle: string;
  chapters: Chapter[];
  entities: Entity[];
  readChapters: number[];
  onChapterChange: (chapterId: string) => void;
  onChapterRead?: (chapterOrder: number) => void;
  onRetry?: () => void;
}

type FontSize = "sm" | "base" | "lg" | "xl";

const fontSizeMap: Record<FontSize, { original: string; translation: string }> = {
  sm: { original: "text-lg", translation: "text-base" },
  base: { original: "text-xl", translation: "text-base" },
  lg: { original: "text-2xl", translation: "text-lg" },
  xl: { original: "text-[1.75rem]", translation: "text-xl" },
};

const fontSizeLabel: Record<FontSize, string> = {
  sm: "小字号",
  base: "中字号",
  lg: "大字号",
  xl: "特大字号",
};

export default function ReadingView({
  chapter,
  chapterLoading,
  chapterError,
  bookTitle,
  chapters,
  entities,
  readChapters,
  onChapterChange,
  onChapterRead,
  onRetry,
}: ReadingViewProps) {
  const [fontSize, setFontSize] = useState<FontSize>("base");
  const [isDark, setIsDark] = useState(false);
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
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const saved = localStorage.getItem("wudian_dark") === "true";
    setIsDark(saved);
    document.documentElement.classList.toggle("dark", saved);
  }, []);

  useEffect(() => {
    if (!chapter?.id) return;
    containerRef.current?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  }, [chapter?.id, reduceMotion]);

  const entityMap = useMemo(() => {
    const map = new Map<string, Entity>();
    entities.forEach((entity) => map.set(entity.id, entity));
    return map;
  }, [entities]);

  const activeChapterId = chapter?.id ?? chapters[0]?.id ?? "";
  const currentIndex = chapters.findIndex((item) => item.id === activeChapterId);
  const prevChapter = currentIndex > 0 ? chapters[currentIndex - 1] : undefined;
  const nextChapter = currentIndex >= 0 ? chapters[currentIndex + 1] : undefined;
  const isRead = chapter ? readChapters.includes(chapter.order) : false;
  const progressPercent = chapters.length
    ? Math.round((readChapters.length / chapters.length) * 100)
    : 0;
  const handleCharClick = (event: React.MouseEvent, annotation: Annotation) => {
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setActiveAnnotation({ data: annotation, pos: { x: rect.left, y: rect.top } });
    setActiveEntity(null);
  };

  const handleEntityClick = (event: React.MouseEvent, entityId: string) => {
    const entity = entityMap.get(entityId);
    if (!entity) return;
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setActiveEntity({ data: entity, pos: { x: rect.left, y: rect.top } });
    setActiveAnnotation(null);
  };

  const renderOriginal = (
    text: string,
    annotations?: Annotation[],
    entityIds?: string[]
  ) => {
    if (!annotations?.length && !entityIds?.length) return text;

    const marks: {
      char: string;
      type: "annotation" | "entity";
      data?: Annotation;
      entityId?: string;
    }[] = [];
    annotations?.forEach((annotation) =>
      marks.push({ char: annotation.char, type: "annotation", data: annotation })
    );
    entityIds?.forEach((entityId) => {
      const entity = entityMap.get(entityId);
      if (entity) marks.push({ char: entity.name, type: "entity", entityId });
    });

    const sorted = [...marks].sort((a, b) => b.char.length - a.char.length);
    const segments: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      let found = false;
      for (const mark of sorted) {
        if (!remaining.startsWith(mark.char)) continue;
        if (mark.type === "annotation" && mark.data) {
          segments.push(
            <button
              type="button"
              key={`annotation-${key++}`}
              className="rare-char cursor-pointer font-inherit"
              onClick={(event) => handleCharClick(event, mark.data!)}
              aria-label={`查看“${mark.char}”的注释`}
            >
              {mark.char}
            </button>
          );
        } else if (mark.type === "entity") {
          segments.push(
            <button
              type="button"
              key={`entity-${key++}`}
              className="cursor-pointer border-b border-cinnabar-600/40 font-inherit text-cinnabar-700 transition-colors hover:text-cinnabar-600 dark:text-cinnabar-300"
              onClick={(event) => handleEntityClick(event, mark.entityId!)}
              aria-label={`查看“${mark.char}”`}
            >
              {mark.char}
            </button>
          );
        }
        remaining = remaining.slice(mark.char.length);
        found = true;
        break;
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
    try {
      localStorage.setItem("wudian_dark", String(next));
    } catch {}
  };

  return (
    <div
      ref={containerRef}
      data-reader-shell
      className="scroll-mt-28 overflow-clip rounded-lg border border-ink-100 bg-rice-50 shadow-scroll dark:border-ink-600 dark:bg-ink-800"
    >
      <div className="sticky top-16 z-30 border-b border-ink-100 bg-rice-50/95 backdrop-blur-md dark:border-ink-600 dark:bg-ink-800/95">
        <div className="flex min-h-16 flex-wrap items-center justify-between gap-2 px-3 py-2 sm:px-5">
          <ChapterSelector
            chapters={chapters}
            bookTitle={bookTitle}
            currentChapterId={activeChapterId}
            readChapters={readChapters}
            open={showChapterSelector}
            onToggle={() => setShowChapterSelector((open) => !open)}
            onSelect={onChapterChange}
          />

          <div className="flex items-center gap-2">
            <div
              className="flex min-h-11 items-center rounded-md border border-ink-200 bg-white/70 dark:border-ink-500 dark:bg-ink-700"
              role="group"
              aria-label="正文字号"
            >
              <Type size={16} className="mx-2 hidden shrink-0 text-ink-400 sm:block" />
              {(["sm", "base", "lg", "xl"] as FontSize[]).map((size) => (
                <button
                  type="button"
                  key={size}
                  onClick={() => setFontSize(size)}
                  className={clsx(
                    "flex h-11 min-w-11 cursor-pointer items-center justify-center rounded px-2 text-sm transition-colors",
                    fontSize === size
                      ? "bg-cinnabar-600 text-white"
                      : "text-ink-500 hover:bg-ink-100 dark:text-rice-300 dark:hover:bg-ink-600"
                  )}
                  aria-label={fontSizeLabel[size]}
                  aria-pressed={fontSize === size}
                >
                  {size === "sm" ? "小" : size === "base" ? "中" : size === "lg" ? "大" : "特"}
                </button>
              ))}
            </div>

            <ImageSourceLink variant="toolbar" label="影像" />

            <button
              type="button"
              onClick={toggleDark}
              className="flex h-11 w-11 cursor-pointer items-center justify-center rounded-md border border-ink-200 bg-white/70 text-ink-700 transition-colors hover:bg-ink-100 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200 dark:hover:bg-ink-600"
              aria-label={isDark ? "切换到日间模式" : "切换到夜间模式"}
              title={isDark ? "日间模式" : "夜间模式"}
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </div>
      </div>

      <main className="reader-paper">
        <section className="mx-auto max-w-3xl px-5 pb-8 pt-10 sm:px-10 sm:pb-12 sm:pt-14">
          <div className="mb-8 flex items-center gap-3 text-sm text-ink-500 dark:text-rice-300">
            <span className="font-serif text-base font-semibold text-cinnabar-700 dark:text-cinnabar-300">
              {bookTitle}
            </span>
            <span className="h-px flex-1 bg-ink-200 dark:bg-ink-600" />
            <span className="tabular-nums">
              {currentIndex >= 0 ? currentIndex + 1 : 0} / {chapters.length || 0} 章
            </span>
          </div>

          {chapter && (
            <motion.header
              key={chapter.id}
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.24 }}
              className="border-l-2 border-cinnabar-600 pl-5 sm:pl-7"
            >
              <p className="mb-2 text-sm text-bronze-600 dark:text-bronze-400">
                第 {chapter.order} 章 · {chapter.sentences.length} 则
              </p>
              <h1 className="font-serif text-3xl font-bold leading-tight text-ink-900 dark:text-rice-50 sm:text-4xl">
                {chapter.title}
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-ink-500 dark:text-rice-300">
                以学习为始，以修身为本。原文、译意与逐句精讲，在同一条阅读脉络中展开。
              </p>
            </motion.header>
          )}

          <div className="mt-9" data-reader-progress>
            <div className="mb-2 flex items-center justify-between text-xs text-ink-500 dark:text-rice-300">
              <span>{readChapters.length} 章已读</span>
              <span className="tabular-nums">{progressPercent}%</span>
            </div>
            <div
              className="h-1.5 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-600"
              role="progressbar"
              aria-label="全书阅读进度"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progressPercent}
            >
              <div
                className="h-full rounded-full bg-bamboo-600 transition-[width] duration-300 dark:bg-bamboo-400"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </section>

        <div className="reader-rule h-px" />

        <section className="mx-auto max-w-3xl px-5 py-4 sm:px-10">
          {chapterLoading && <ReadingSkeleton />}

          {!chapterLoading && chapterError && (
            <div className="my-10 flex flex-col items-center border-y border-ink-100 py-10 text-center dark:border-ink-600" role="alert">
              <AlertCircle size={24} className="mb-3 text-cinnabar-600" />
              <p className="font-serif text-lg text-ink-800 dark:text-rice-100">{chapterError}</p>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="mt-5 flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-ink-200 px-4 text-sm text-ink-700 transition-colors hover:border-cinnabar-400 hover:text-cinnabar-700 dark:border-ink-500 dark:text-rice-200"
                >
                  <RefreshCw size={16} /> 重新加载
                </button>
              )}
            </div>
          )}

          {!chapterLoading && !chapterError && !chapter && chapters.length === 0 && (
            <div className="my-10 border-y border-ink-100 py-10 text-center dark:border-ink-600">
              <BookOpen size={24} className="mx-auto mb-3 text-bronze-500" />
              <p className="font-serif text-lg text-ink-700 dark:text-rice-200">本典正文尚未收录</p>
              <p className="mt-2 text-sm text-ink-400 dark:text-rice-400">可先返回典籍书库，选择已有正文的经典继续阅读。</p>
            </div>
          )}

          {!chapterLoading && !chapterError && chapter?.sentences.length === 0 && (
            <div className="my-10 border-y border-ink-100 py-10 text-center dark:border-ink-600">
              <BookOpen size={24} className="mx-auto mb-3 text-bronze-500" />
              <p className="font-serif text-lg text-ink-700 dark:text-rice-200">本章正文尚未收录</p>
            </div>
          )}

          {!chapterLoading && !chapterError && chapter && chapter.sentences.length > 0 && (
            <div className="divide-y divide-ink-100 dark:divide-ink-600">
              {chapter.sentences.map((pair, index) => (
                <motion.article
                  data-reader-passage
                  key={pair.id}
                  initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(index * 0.035, 0.18), duration: 0.22 }}
                  className="grid grid-cols-[2rem_minmax(0,1fr)] gap-3 py-8 sm:grid-cols-[2.5rem_minmax(0,1fr)] sm:gap-5 sm:py-10"
                >
                  <div className="pt-1 font-serif text-sm tabular-nums text-bronze-500">
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div className="min-w-0">
                    <p
                      className={clsx(
                        "font-serif leading-[2] text-ink-900 dark:text-rice-50",
                        fontSizeMap[fontSize].original
                      )}
                    >
                      {renderOriginal(pair.original, pair.annotations, pair.entityIds)}
                    </p>

                    <div className="mt-5 border-l border-bronze-400/60 pl-4 sm:pl-5">
                      <p className="mb-1 text-xs font-medium text-bronze-600 dark:text-bronze-400">今译</p>
                      <p
                        className={clsx(
                          "leading-8 text-ink-600 dark:text-rice-200",
                          fontSizeMap[fontSize].translation
                        )}
                      >
                        {pair.translation}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setAiPanel({
                          open: true,
                          verseId: pair.id,
                          original: pair.original,
                          translation: pair.translation,
                        })
                      }
                      className="mt-5 flex min-h-11 cursor-pointer items-center gap-2 rounded-md px-3 text-sm font-medium text-cinnabar-700 transition-colors hover:bg-cinnabar-50 dark:text-cinnabar-300 dark:hover:bg-cinnabar-900/20"
                      aria-label={`精讲第 ${index + 1} 则`}
                    >
                      <Sparkles size={16} />
                      逐句精讲
                      <ChevronRight size={15} />
                    </button>
                  </div>
                </motion.article>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="border-t border-ink-100 bg-rice-100/65 px-4 py-5 dark:border-ink-600 dark:bg-ink-700/40 sm:px-6">
        <div className="mx-auto grid max-w-4xl grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-5">
          <ChapterNavButton
            direction="previous"
            chapter={prevChapter}
            onSelect={onChapterChange}
          />

          <button
            type="button"
            disabled={!chapter || isRead}
            onClick={() => chapter && onChapterRead?.(chapter.order)}
            className={clsx(
              "flex min-h-11 cursor-pointer items-center gap-2 rounded-md px-3 text-sm font-medium transition-colors sm:px-5",
              isRead
                ? "cursor-default border border-bamboo-300 bg-bamboo-50 text-bamboo-700 dark:border-bamboo-700 dark:bg-bamboo-900/30 dark:text-bamboo-300"
                : "bg-cinnabar-600 text-white hover:bg-cinnabar-700 disabled:cursor-not-allowed disabled:opacity-50"
            )}
          >
            {isRead && <Check size={17} />}
            <span>{isRead ? "本章已读" : "标记已读"}</span>
          </button>

          <ChapterNavButton
            direction="next"
            chapter={nextChapter}
            onSelect={onChapterChange}
          />
        </div>
      </footer>

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
      <AIExplainPanel
        open={aiPanel.open}
        verseId={aiPanel.verseId}
        original={aiPanel.original}
        translation={aiPanel.translation}
        onClose={() => setAiPanel((current) => ({ ...current, open: false }))}
      />
    </div>
  );
}

function ReadingSkeleton() {
  return (
    <div className="divide-y divide-ink-100 dark:divide-ink-600" aria-label="正在加载正文" aria-busy="true">
      {[0, 1, 2].map((item) => (
        <div key={item} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-3 py-9 sm:grid-cols-[2.5rem_minmax(0,1fr)] sm:gap-5">
          <div className="h-4 w-5 animate-pulse rounded bg-ink-100 dark:bg-ink-600" />
          <div>
            <div className="h-6 w-full animate-pulse rounded bg-ink-100 dark:bg-ink-600" />
            <div className="mt-3 h-6 w-3/4 animate-pulse rounded bg-ink-100 dark:bg-ink-600" />
            <div className="mt-6 h-4 w-5/6 animate-pulse rounded bg-rice-200 dark:bg-ink-600" />
          </div>
        </div>
      ))}
    </div>
  );
}

function ChapterNavButton({
  direction,
  chapter,
  onSelect,
}: {
  direction: "previous" | "next";
  chapter?: Chapter;
  onSelect: (chapterId: string) => void;
}) {
  const isPrevious = direction === "previous";
  return (
    <button
      type="button"
      disabled={!chapter}
      onClick={() => chapter && onSelect(chapter.id)}
      className={clsx(
        "flex min-h-11 min-w-0 cursor-pointer items-center gap-2 rounded-md px-2 text-left text-ink-700 transition-colors hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-30 dark:text-rice-200 dark:hover:bg-ink-600",
        !isPrevious && "justify-end text-right"
      )}
      aria-label={chapter ? `${isPrevious ? "上一章" : "下一章"}：${chapter.title}` : isPrevious ? "没有上一章" : "没有下一章"}
    >
      {isPrevious && <ChevronLeft size={18} className="shrink-0" />}
      <span className="min-w-0">
        <span className="block text-xs text-ink-400 dark:text-rice-400">
          {isPrevious ? "上一章" : "下一章"}
        </span>
        {chapter && <span className="hidden truncate font-serif text-sm sm:block">{chapter.title}</span>}
      </span>
      {!isPrevious && <ChevronRight size={18} className="shrink-0" />}
    </button>
  );
}

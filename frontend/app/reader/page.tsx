"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import ReadingView from "@/components/reader/ReadingView";
import { api } from "@/lib/api";
import { mockBooks, mockEntities } from "@/lib/mockData";
import { useToast } from "@/components/ui/Toast";
import type { Chapter, Entity, LearningProgress } from "@/lib/types";

function ReaderContent() {
  const searchParams = useSearchParams();
  const bookId = searchParams.get("book") || "lunyu";
  const bookTitle = mockBooks.find((book) => book.id === bookId)?.title ?? "经典";
  const toast = useToast();

  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [currentChapter, setCurrentChapter] = useState<Chapter | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [chapterLoading, setChapterLoading] = useState(true);
  const [chapterError, setChapterError] = useState<string | null>(null);
  const bookRequestRef = useRef(0);
  const chapterRequestRef = useRef(0);

  // 加载章节列表
  useEffect(() => {
    let cancelled = false;
    const bookRequestId = ++bookRequestRef.current;
    chapterRequestRef.current += 1;
    setChapterLoading(true);
    setChapterError(null);
    setCurrentChapter(null);
    setChapters([]);
    setProgress(null);
    api
      .getChapters(bookId)
      .then(async (data) => {
        if (cancelled || bookRequestId !== bookRequestRef.current) return;
        setChapters(data);
        const firstChapter = data[0];
        if (!firstChapter) {
          setChapterLoading(false);
          return;
        }

        const requestId = ++chapterRequestRef.current;
        try {
          const detail = await api.getChapter(firstChapter.id);
          if (!cancelled && bookRequestId === bookRequestRef.current && requestId === chapterRequestRef.current) {
            setCurrentChapter(detail);
          }
        } catch {
          if (!cancelled && bookRequestId === bookRequestRef.current && requestId === chapterRequestRef.current) {
            setChapterError("正文暂时无法展开，请稍后重试");
          }
        } finally {
          if (!cancelled && bookRequestId === bookRequestRef.current && requestId === chapterRequestRef.current) {
            setChapterLoading(false);
          }
        }
      })
      .catch(() => {
        if (!cancelled && bookRequestId === bookRequestRef.current) {
          setChapters([]);
          setChapterError("章节目录暂时无法加载，请稍后重试");
          setChapterLoading(false);
        }
      });
    api.getProgress(bookId).then((data) => {
      if (!cancelled && bookRequestId === bookRequestRef.current) setProgress(data);
    }).catch(() => {});
    // 加载实体（mock 数据中全部加载）
    setEntities(mockEntities);
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  const handleChapterChange = useCallback(
    (chapterId: string) => {
      const requestId = ++chapterRequestRef.current;
      setChapterLoading(true);
      setChapterError(null);
      api
        .getChapter(chapterId)
        .then((detail) => {
          if (requestId === chapterRequestRef.current) {
            setCurrentChapter(detail);
          }
        })
        .catch(() => {
          if (requestId === chapterRequestRef.current) {
            setChapterError("这一章暂时无法展开，请稍后重试");
          }
        })
        .finally(() => {
          if (requestId === chapterRequestRef.current) {
            setChapterLoading(false);
          }
        });
    },
    []
  );

  const handleChapterRead = useCallback(
    (chapterOrder: number) => {
      setProgress((current) => {
        const base: LearningProgress = current ?? {
          bookId,
          currentChapterOrder: chapterOrder,
          totalChapters: chapters.length,
          readChapters: [],
          streakDays: 0,
          lastReadDate: new Date().toISOString().slice(0, 10),
        };
        if (base.readChapters.includes(chapterOrder)) return base;
        return {
          ...base,
          currentChapterOrder: chapterOrder,
          readChapters: [...base.readChapters, chapterOrder],
        };
      });
      toast(`已标记第 ${chapterOrder} 章为已读 ✓`);
    },
    [bookId, chapters.length, toast]
  );

  return (
    <ReadingView
      chapter={currentChapter}
      chapterLoading={chapterLoading}
      chapterError={chapterError}
      bookTitle={bookTitle}
      chapters={chapters}
      entities={entities}
      readChapters={progress?.readChapters ?? []}
      onChapterChange={handleChapterChange}
      onChapterRead={handleChapterRead}
      onRetry={() => {
        const chapterId = currentChapter?.id ?? chapters[0]?.id;
        if (chapterId) handleChapterChange(chapterId);
      }}
    />
  );
}

export default function ReaderPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[60vh] items-center justify-center">
          <div className="font-serif text-lg text-ink-400">加载中……</div>
        </div>
      }
    >
      <ReaderContent />
    </Suspense>
  );
}

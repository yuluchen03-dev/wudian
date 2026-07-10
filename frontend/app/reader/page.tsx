"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import ReadingView from "@/components/reader/ReadingView";
import { api } from "@/lib/api";
import { mockEntities } from "@/lib/mockData";
import { useToast } from "@/components/ui/Toast";
import type { Chapter, Entity, LearningProgress } from "@/lib/types";

function ReaderContent() {
  const searchParams = useSearchParams();
  const bookId = searchParams.get("book") || "lunyu";
  const toast = useToast();

  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [currentChapter, setCurrentChapter] = useState<Chapter | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [loading, setLoading] = useState(true);

  // 加载章节列表
  useEffect(() => {
    setLoading(true);
    api.getChapters(bookId).then((data) => {
      setChapters(data);
      if (data.length > 0) setCurrentChapter(data[0]);
      setLoading(false);
    });
    api.getProgress(bookId).then(setProgress).catch(() => {});
    // 加载实体（mock 数据中全部加载）
    setEntities(mockEntities);
  }, [bookId]);

  const handleChapterChange = useCallback(
    (chapterId: string) => {
      api.getChapter(chapterId).then(setCurrentChapter);
    },
    []
  );

  const handleChapterRead = useCallback(
    (chapterOrder: number) => {
      if (!progress) return;
      if (!progress.readChapters.includes(chapterOrder)) {
        const updated = {
          ...progress,
          readChapters: [...progress.readChapters, chapterOrder],
        };
        setProgress(updated);
      }
      toast(`已标记第 ${chapterOrder} 章为已读 ✓`);
    },
    [progress]
  );

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在展开竹简……</div>
      </div>
    );
  }

  if (!currentChapter) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-ink-400">暂无章节内容</div>
      </div>
    );
  }

  return (
    <ReadingView
      chapter={currentChapter}
      chapters={chapters}
      entities={entities}
      readChapters={progress?.readChapters ?? []}
      onChapterChange={handleChapterChange}
      onChapterRead={handleChapterRead}
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

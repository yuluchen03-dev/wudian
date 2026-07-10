"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Image, Theater as TheaterIcon, BookOpen } from "lucide-react";
import clsx from "clsx";
import { QuoteCardList, QuoteCardDetailModal } from "@/components/content/QuoteCard";
import { TheaterCard, TheaterPlayer } from "@/components/content/TheaterPlayer";
import ComicViewer from "@/components/content/ComicViewer";
import { api } from "@/lib/api";
import { mockComics } from "@/lib/comicData";
import {
  mockQuoteCardDetail,
  mockQuoteCards,
  mockTheaterDetail,
  mockTheaters,
} from "@/lib/mockContent";
import { pageBackgrounds } from "@/lib/visualAssets";
import type { QuoteCard, QuoteCardDetail, Theater, TheaterDetail, Comic } from "@/lib/types";

type Tab = "quotes" | "theater" | "comics";

const tabs: { key: Tab; label: string; icon: typeof Image }[] = [
  { key: "quotes", label: "金句卡片", icon: Image },
  { key: "theater", label: "情景小剧场", icon: TheaterIcon },
  { key: "comics", label: "漫画解读", icon: BookOpen },
];

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState<Tab>("quotes");
  const [cards, setCards] = useState<QuoteCard[]>([]);
  const [theaters, setTheaters] = useState<Theater[]>([]);
  const [comics, setComics] = useState<Comic[]>([]);
  const [selectedCard, setSelectedCard] = useState<QuoteCardDetail | null>(null);
  const [selectedTheater, setSelectedTheater] = useState<TheaterDetail | null>(null);
  const [selectedComic, setSelectedComic] = useState<Comic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [c, t, comicItems] = await Promise.all([
        api.getQuoteCards(),
        api.getTheaters(),
        api.getComics(),
      ]);
      setCards(c);
      setTheaters(t);
      setComics(comicItems);
    } catch (error) {
      console.warn("Content API unavailable, using local content fallback.", error);
      setCards(mockQuoteCards);
      setTheaters(mockTheaters);
      setComics(mockComics);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = async (cardId: string) => {
    try {
      const detail = await api.getQuoteCardDetail(cardId);
      setSelectedCard(detail);
    } catch (error) {
      console.warn("Quote detail API unavailable, using local content fallback.", error);
      setSelectedCard({ ...mockQuoteCardDetail, id: cardId });
    }
  };

  const handleTheaterClick = async (theaterId: string) => {
    try {
      const detail = await api.getTheaterDetail(theaterId);
      setSelectedTheater(detail);
    } catch (error) {
      console.warn("Theater detail API unavailable, using local content fallback.", error);
      setSelectedTheater({ ...mockTheaterDetail, id: theaterId });
    }
  };

  const handleComicClick = async (comicId: string) => {
    try {
      const detail = await api.getComicDetail(comicId);
      setSelectedComic(detail);
    } catch (error) {
      console.warn("Comic detail API unavailable, using local content fallback.", error);
      setSelectedComic(mockComics.find((comic) => comic.id === comicId) ?? null);
    }
  };

  const handleLikeCard = (cardId: string) => {
    api.likeQuoteCard(cardId);
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在加载内容...</div>
      </div>
    );
  }

  return (
    <div
      className="relative -mx-4 -my-8 min-h-screen px-4 py-8"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(248,245,238,0.86), rgba(248,245,238,0.97)), url(${pageBackgrounds.content})`,
        backgroundSize: "cover",
        backgroundPosition: "center top",
      }}
    >
      <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="font-serif text-3xl font-bold text-ink-800 dark:text-rice-50">
          趣味经典
        </h1>
        <p className="mt-2 text-sm text-ink-500 dark:text-rice-300">
          金句卡片 · 情景小剧场 · 漫画解读 —— 让经典有趣起来
        </p>
        <div className="classical-divider mx-auto mt-4 w-32" />
      </motion.div>

      {/* 标签栏 */}
      <div className="sticky top-16 z-30 flex justify-center gap-1 rounded-lg bg-rice-50/90 p-1 backdrop-blur-md dark:bg-ink-800/90">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                "flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-colors",
                activeTab === tab.key
                  ? "bg-cinnabar-600 text-rice-50"
                  : "text-ink-600 hover:bg-ink-100 dark:text-rice-300 dark:hover:bg-ink-700"
              )}
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 内容区 */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* 金句卡片 */}
        {activeTab === "quotes" && (
          <div>
            <p className="mb-4 text-center text-sm text-ink-500 dark:text-rice-300">
              精美中国风金句卡片，可分享至朋友圈 ✨
            </p>
            <QuoteCardList cards={cards} onCardClick={handleCardClick} />
          </div>
        )}

        {/* 情景小剧场 */}
        {activeTab === "theater" && (
          <div>
            {selectedTheater ? (
              <div className="mx-auto max-w-5xl">
                <TheaterPlayer
                  theater={selectedTheater}
                  onBack={() => setSelectedTheater(null)}
                />
              </div>
            ) : (
              <>
                <p className="mb-4 text-center text-sm text-ink-500 dark:text-rice-300">
                  论语场景现代重演 —— 职场、校园中遇见孔子 🎭
                </p>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {theaters.map((t, i) => (
                    <TheaterCard
                      key={t.id}
                      theater={t}
                      index={i}
                      onClick={handleTheaterClick}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* 漫画解读 */}
        {activeTab === "comics" && (
          <div>
            {selectedComic ? (
              <ComicViewer comic={selectedComic} onBack={() => setSelectedComic(null)} />
            ) : (
              <>
                <p className="mb-4 text-center text-sm text-ink-500 dark:text-rice-300">
                  专业分镜脚本 · Agens 面板图 · 竖屏漫画阅读 —— 让经典变成能看的故事
                </p>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {comics.map((comic, i) => (
                    <motion.button
                      key={comic.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      onClick={() => handleComicClick(comic.id)}
                      className="group relative overflow-hidden rounded-lg border border-ink-100 bg-white/75 p-5 text-left shadow-scroll transition-all hover:-translate-y-1 hover:border-cinnabar-200 hover:shadow-popup dark:border-ink-600 dark:bg-ink-700/75"
                    >
                      <div className="mb-3 flex items-center gap-3">
                        <div className="grid h-16 w-16 shrink-0 grid-cols-2 gap-0.5 rounded-md border-2 border-ink-800 bg-rice-50 p-1 dark:border-ink-300 dark:bg-ink-800">
                          {comic.panels.slice(0, 4).map((_, idx) => (
                            <div key={idx} className="rounded-sm bg-cinnabar-600/20" />
                          ))}
                        </div>
                        <div className="min-w-0">
                          <h3 className="font-serif text-xl font-bold text-ink-800 dark:text-rice-50">
                            {comic.title}
                          </h3>
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-bronze-500">
                            <BookOpen size={11} />
                            <span>{comic.panels.length} 格漫画</span>
                            {comic.styleGuide && <span>· 统一画风</span>}
                          </div>
                        </div>
                      </div>

                      <p className="line-clamp-2 text-sm leading-relaxed text-ink-500 dark:text-rice-300">
                        {comic.logline || comic.source_verse}
                      </p>

                      {/* 分镜预览 */}
                      <div className="mt-4 flex gap-1">
                        {comic.panels.map((panel, idx) => (
                          <div
                            key={idx}
                            title={panel.beat}
                            className={clsx(
                              "h-2 flex-1 rounded-full",
                              panel.imageUrl ? "bg-cinnabar-600" : "bg-ink-300/40 dark:bg-rice-200/30"
                            )}
                          />
                        ))}
                      </div>

                      <div className="mt-3 text-right text-xs font-medium text-cinnabar-600 opacity-0 transition-opacity group-hover:opacity-100">
                        进入漫画阅读 →
                      </div>
                    </motion.button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </motion.div>

      {/* 金句卡片详情弹窗 */}
      {selectedCard && (
        <QuoteCardDetailModal
          card={selectedCard}
          onClose={() => setSelectedCard(null)}
          onLike={handleLikeCard}
        />
      )}
      </div>
    </div>
  );
}

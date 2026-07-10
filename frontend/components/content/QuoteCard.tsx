"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Share2, Download, X, Sparkles } from "lucide-react";
import clsx from "clsx";
import type { QuoteCard, QuoteCardDetail, CardStyle } from "@/lib/types";
import { useToast } from "@/components/ui/Toast";

const styleThemes: Record<CardStyle, { bg: string; text: string; accent: string; label: string }> = {
  ink_wash: { bg: "#faf6ed", text: "#1c1917", accent: "#b91c1c", label: "水墨" },
  gold_seal: { bg: "#fdfbf7", text: "#1c1917", accent: "#c9a85e", label: "金印" },
  bamboo_scroll: { bg: "#f5edd9", text: "#44403c", accent: "#8a8050", label: "竹简" },
  moonlight: { bg: "#1a1a2e", text: "#e6d4a3", accent: "#e6d4a3", label: "月夜" },
  cloud_mist: { bg: "#f5f5f4", text: "#57534e", accent: "#78716c", label: "云雾" },
};

interface QuoteCardListProps {
  cards: QuoteCard[];
  onCardClick?: (cardId: string) => void;
  index?: number;
}

export function QuoteCardList({ cards, onCardClick }: QuoteCardListProps) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
      {cards.map((card, i) => {
        const theme = styleThemes[card.style];
        return (
          <motion.button
            key={card.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.04 * i }}
            onClick={() => onCardClick?.(card.id)}
            className="group relative aspect-[3/4] overflow-hidden rounded-lg shadow-scroll transition-all hover:-translate-y-1 hover:shadow-popup"
            style={{
              backgroundColor: theme.bg,
              backgroundImage: card.backgroundImage ? `url(${card.backgroundImage})` : undefined,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            <div
              className="absolute inset-0"
              style={{
                background:
                  card.style === "moonlight"
                    ? "linear-gradient(180deg, rgba(10,10,24,0.1), rgba(10,10,24,0.46))"
                    : "linear-gradient(180deg, rgba(255,252,244,0.2), rgba(255,248,232,0.54))",
              }}
            />

            <div
              className="absolute inset-2 rounded-md border"
              style={{ borderColor: theme.accent + "40" }}
            />

            <div className="relative flex h-full flex-col items-center justify-center p-5 text-center">
              <p
                className="font-serif text-xl leading-relaxed drop-shadow-[0_1px_8px_rgba(255,255,255,0.45)]"
                style={{ color: theme.text }}
              >
                {card.quote}
              </p>
              <div
                className="mt-4 h-px w-12"
                style={{ backgroundColor: theme.accent + "70" }}
              />
              <p className="mt-3 text-xs" style={{ color: theme.accent }}>
                {card.source}
              </p>
            </div>

            <div
              className="absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded font-serif text-xs font-bold"
              style={{
                backgroundColor: theme.accent,
                color: theme.bg,
              }}
            >
              悟
            </div>

            <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 transition-all group-hover:bg-black/10 group-hover:opacity-100">
              <span className="rounded-full bg-white/85 px-4 py-1.5 text-xs font-medium text-ink-700">
                点击查看
              </span>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

interface QuoteCardDetailProps {
  card: QuoteCardDetail;
  onClose?: () => void;
  onLike?: (cardId: string) => void;
}

export function QuoteCardDetailModal({ card, onClose, onLike }: QuoteCardDetailProps) {
  const [liked, setLiked] = useState(card.isLiked);
  const [likeCount, setLikeCount] = useState(card.likeCount);
  const theme = styleThemes[card.style];
  const toast = useToast();

  const handleLike = () => {
    setLiked(!liked);
    setLikeCount((prev) => (liked ? prev - 1 : prev + 1));
    onLike?.(card.id);
  };

  const handleShare = () => {
    const text = `${card.quote} —— ${card.source}`;
    if (navigator.share) {
      navigator.share({ title: card.quote, text });
    } else {
      navigator.clipboard?.writeText(`${text}\n\n来自「悟典」`);
      toast("已复制到剪贴板，快去分享吧！");
    }
  };

  const handleDownload = () => {
    toast("请截图保存这张金句卡片，或使用分享功能发给好友。", "info");
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: "spring", duration: 0.4 }}
          onClick={(e) => e.stopPropagation()}
          className="relative max-h-[90vh] w-full max-w-md overflow-y-auto"
        >
          <div
            className="relative overflow-hidden rounded-xl shadow-2xl"
            style={{
              backgroundColor: card.backgroundColor,
              backgroundImage: card.backgroundImage ? `url(${card.backgroundImage})` : undefined,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            <div
              className="absolute inset-0"
              style={{
                background:
                  card.style === "moonlight"
                    ? "linear-gradient(180deg, rgba(8,8,22,0.18), rgba(8,8,22,0.62))"
                    : "linear-gradient(180deg, rgba(255,252,244,0.26), rgba(255,248,232,0.7))",
              }}
            />

            <button
              onClick={onClose}
              aria-label="关闭"
              className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/10 text-ink-600 transition-colors hover:bg-black/20"
            >
              <X size={16} />
            </button>

            <div
              className="absolute inset-3 rounded-lg border-2"
              style={{ borderColor: card.accentColor + "30" }}
            />
            <div
              className="absolute inset-4 rounded-md border"
              style={{ borderColor: card.accentColor + "20" }}
            />

            <div className="relative px-8 py-12 text-center">
              <div className="mb-6 flex items-center justify-center gap-2 text-xs" style={{ color: card.accentColor }}>
                <Sparkles size={12} />
                {theme.label}风 · 金句卡片
              </div>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="font-serif text-3xl font-bold leading-relaxed"
                style={{ color: theme.text }}
              >
                {card.quote}
              </motion.p>

              <div className="my-6 flex items-center justify-center gap-3">
                <div className="h-px w-12" style={{ backgroundColor: card.accentColor + "40" }} />
                <span className="font-serif text-sm" style={{ color: card.accentColor }}>
                  {card.source}
                </span>
                <div className="h-px w-12" style={{ backgroundColor: card.accentColor + "40" }} />
              </div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="mb-4"
              >
                <div className="mb-1 text-xs" style={{ color: card.accentColor }}>白话</div>
                <p className="text-sm leading-relaxed" style={{ color: theme.text + "cc" }}>
                  {card.vernacular}
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <div className="mb-1 text-xs" style={{ color: card.accentColor }}>现代解读</div>
                <p className="text-sm leading-relaxed" style={{ color: theme.text + "99" }}>
                  {card.modernInterpretation}
                </p>
              </motion.div>

              <div className="mt-8 flex justify-center">
                <div
                  className="flex h-12 w-12 items-center justify-center rounded font-serif text-lg font-bold"
                  style={{ backgroundColor: card.accentColor, color: card.backgroundColor }}
                >
                  悟典
                </div>
              </div>

              {card.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap justify-center gap-1.5">
                  {card.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full px-2 py-0.5 text-[10px]"
                      style={{
                        backgroundColor: card.accentColor + "15",
                        color: card.accentColor,
                      }}
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 flex items-center justify-center gap-4 rounded-xl bg-rice-50 p-3 dark:bg-ink-700">
            <button
              onClick={handleLike}
              className={clsx(
                "flex items-center gap-1.5 rounded-md px-4 py-2 text-sm transition-colors",
                liked ? "text-cinnabar-600" : "text-ink-500 hover:text-cinnabar-600"
              )}
            >
              <Heart size={18} fill={liked ? "currentColor" : "none"} />
              <span>{likeCount}</span>
            </button>
            <button
              onClick={handleShare}
              className="flex items-center gap-1.5 rounded-md px-4 py-2 text-sm text-ink-500 transition-colors hover:text-bronze-600"
            >
              <Share2 size={18} />
              <span>分享</span>
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 rounded-md px-4 py-2 text-sm text-ink-500 transition-colors hover:text-bronze-600"
            >
              <Download size={18} />
              <span>保存</span>
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, BookText } from "lucide-react";
import type { Annotation } from "@/lib/types";

interface AnnotationPopupProps {
  annotation: Annotation | null;
  /** 弹窗锚点位置 */
  position: { x: number; y: number } | null;
  onClose: () => void;
}

export default function AnnotationPopup({
  annotation,
  position,
  onClose,
}: AnnotationPopupProps) {
  return (
    <AnimatePresence>
      {annotation && position && (
        <>
          {/* 遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50"
            onClick={onClose}
          />
          {/* 弹窗 */}
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed z-50 w-64"
            style={{
              left: Math.min(position.x, window.innerWidth - 280),
              top: Math.max(position.y - 10, 10),
            }}
          >
            <div className="overflow-hidden rounded-lg border border-ink-200 bg-rice-50 shadow-popup dark:border-ink-500 dark:bg-ink-700">
              {/* 头部 */}
              <div className="flex items-center justify-between bg-cinnabar-600 px-4 py-2">
                <div className="flex items-center gap-2 text-rice-50">
                  <BookText size={16} />
                  <span className="font-serif text-lg font-bold">
                    {annotation.char}
                  </span>
                  <span className="font-serif text-sm opacity-90">
                    {annotation.pinyin}
                  </span>
                </div>
                <button
                  onClick={onClose}
                  className="text-rice-50/80 hover:text-rice-50"
                >
                  <X size={16} />
                </button>
              </div>

              {/* 通假字提示 */}
              {annotation.isTongjia && (
                <div className="border-b border-ink-100 bg-bronze-400/10 px-4 py-2 text-xs text-bronze-600 dark:border-ink-500">
                  通假字 · 本字为「{annotation.tongjiaOrigin}」
                </div>
              )}

              {/* 释义 */}
              <div className="px-4 py-3">
                <div className="mb-1 text-xs text-ink-400">释义</div>
                <p className="text-sm leading-relaxed text-ink-700 dark:text-rice-200">
                  {annotation.meaning}
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

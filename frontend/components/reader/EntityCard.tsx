"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, User, MapPin, Award, BookMarked, Lightbulb } from "lucide-react";
import type { Entity } from "@/lib/types";

interface EntityCardProps {
  entity: Entity | null;
  position: { x: number; y: number } | null;
  onClose: () => void;
}

const typeIconMap = {
  人名: User,
  地名: MapPin,
  官职: Award,
  典故: BookMarked,
  概念: Lightbulb,
} as const;

const typeColorMap = {
  人名: "bg-cinnabar-600",
  地名: "bg-bronze-500",
  官职: "bg-ink-600",
  典故: "bg-cinnabar-700",
  概念: "bg-bronze-600",
} as const;

export default function EntityCard({
  entity,
  position,
  onClose,
}: EntityCardProps) {
  return (
    <AnimatePresence>
      {entity && position && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed z-50 w-72"
            style={{
              left: Math.min(position.x, window.innerWidth - 300),
              top: Math.max(position.y - 10, 10),
            }}
          >
            <div className="overflow-hidden rounded-lg border border-ink-200 bg-rice-50 shadow-popup dark:border-ink-500 dark:bg-ink-700">
              {/* 头部 */}
              <div
                className={`flex items-center justify-between px-4 py-3 ${
                  typeColorMap[entity.type]
                }`}
              >
                <div className="flex items-center gap-2 text-rice-50">
                  {(() => {
                    const Icon = typeIconMap[entity.type];
                    return <Icon size={18} />;
                  })()}
                  <span className="font-serif text-xl font-bold">
                    {entity.name}
                  </span>
                  <span className="rounded bg-rice-50/20 px-1.5 py-0.5 text-xs">
                    {entity.type}
                  </span>
                </div>
                <button
                  onClick={onClose}
                  className="text-rice-50/80 hover:text-rice-50"
                >
                  <X size={16} />
                </button>
              </div>

              {/* 描述 */}
              <div className="px-4 py-3">
                <p className="text-sm leading-relaxed text-ink-700 dark:text-rice-200">
                  {entity.description}
                </p>
                {entity.relatedText && (
                  <div className="mt-3 border-l-2 border-cinnabar-300 pl-3 text-xs italic text-ink-400">
                    见于：「{entity.relatedText}」
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

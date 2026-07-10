"use client";

import { motion } from "framer-motion";
import clsx from "clsx";
import type { Sage } from "@/lib/types";
import { sageColors, getSageEra, getSageCoreThought } from "@/lib/roundtableData";

interface SageAvatarsProps {
  sages: Sage[];
  activeSageId?: string | null;
  onSageClick?: (sageId: string) => void;
}

/**
 * 百家论道 - 圣贤头像圆桌排列
 * 桌面端：三角形排列围绕话题
 * 移动端：水平排列
 */
export default function SageAvatars({ sages, activeSageId, onSageClick }: SageAvatarsProps) {
  return (
    <div className="flex items-center justify-center gap-6 md:gap-10">
      {sages.map((sage, idx) => {
        const isActive = sage.id === activeSageId;
        const colors = sageColors[sage.id];

        return (
          <motion.button
            key={sage.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.1 + idx * 0.15 }}
            onClick={() => onSageClick?.(sage.id)}
            className={clsx(
              "group flex flex-col items-center gap-2 transition-transform",
              "hover:scale-105"
            )}
          >
            {/* 头像 */}
            <div className="relative">
              <div
                className={clsx(
                  "flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-cover bg-center font-serif text-2xl font-bold text-rice-50 shadow-lg transition-shadow md:h-20 md:w-20 md:text-3xl",
                  isActive && "animate-pulse shadow-xl ring-2 ring-offset-2",
                  isActive && "ring-cinnabar-400 ring-offset-rice-50 dark:ring-offset-ink-800"
                )}
                style={{
                  backgroundColor: sage.avatar_color,
                  backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined,
                }}
              >
                <span className={sage.portraitImage ? "sr-only" : ""}>{sage.name[0]}</span>
              </div>

              {/* 活跃指示器 */}
              {isActive && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-cinnabar-600 text-[10px] text-rice-50 shadow-sm"
                >
                  <span className="animate-pulse">●</span>
                </motion.div>
              )}
            </div>

            {/* 姓名 + 信息 */}
            <div className="text-center">
              <div className="font-serif text-sm font-bold text-ink-800 dark:text-rice-100 md:text-base">
                {sage.name}
              </div>
              <div className="text-[10px] text-ink-400 dark:text-rice-500 md:text-xs">
                {getSageEra(sage.id)}
              </div>
              {colors && (
                <span
                  className={clsx(
                    "mt-1 inline-block rounded-full px-2 py-0.5 text-[10px]",
                    colors.bg,
                    colors.text,
                    "dark:bg-ink-600 dark:text-rice-300"
                  )}
                >
                  {getSageCoreThought(sage.id)}
                </span>
              )}
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

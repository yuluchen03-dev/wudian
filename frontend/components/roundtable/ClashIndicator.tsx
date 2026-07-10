"use client";

import { motion } from "framer-motion";
import clsx from "clsx";
import type { DebateClash } from "@/lib/roundtableData";

interface ClashIndicatorProps {
  clash: DebateClash;
  sageNames: Record<string, string>;
}

/**
 * 百家论道 - 交锋指示器
 * 显示两位圣贤之间的观点关系
 */
export default function ClashIndicator({ clash, sageNames }: ClashIndicatorProps) {
  const typeConfig = {
    agree: {
      label: "认同",
      color: "bg-bamboo-50 border-bamboo-300 text-bamboo-700 dark:bg-bamboo-900/30 dark:border-bamboo-600 dark:text-bamboo-300",
      icon: "●",
    },
    disagree: {
      label: "相左",
      color: "bg-cinnabar-50 border-cinnabar-300 text-cinnabar-700 dark:bg-cinnabar-900/30 dark:border-cinnabar-600 dark:text-cinnabar-300",
      icon: "✕",
    },
    extend: {
      label: "继承",
      color: "bg-rice-100 border-bronze-400/40 text-bronze-600 dark:bg-ink-600/40 dark:border-bronze-500/40 dark:text-bronze-400",
      icon: "→",
    },
    reframe: {
      label: "新解",
      color: "bg-ink-50 border-ink-300 text-ink-600 dark:bg-ink-600/40 dark:border-ink-400 dark:text-rice-300",
      icon: "↻",
    },
    refute: {
      label: "反驳",
      color: "bg-cinnabar-50 border-cinnabar-400 text-cinnabar-800 dark:bg-cinnabar-900/30 dark:border-cinnabar-500 dark:text-cinnabar-200",
      icon: "!",
    },
  };

  const config = typeConfig[clash.type];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="flex items-center gap-2 py-1.5 pl-14"
    >
      {/* 连接线 */}
      <div className="h-px w-6 bg-ink-200 dark:bg-ink-500" />

      {/* 标签 */}
      <span
        className={clsx(
          "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs",
          config.color
        )}
      >
        <span className="text-[10px]">{config.icon}</span>
        <span className="font-medium">{sageNames[clash.fromSageId]}</span>
        <span className="text-[10px] opacity-60">{config.label}</span>
        <span className="font-medium">{sageNames[clash.toSageId]}</span>
      </span>

      {/* 摘要 */}
      <span className="text-xs text-ink-400 dark:text-rice-500">
        {clash.summary}
      </span>
    </motion.div>
  );
}

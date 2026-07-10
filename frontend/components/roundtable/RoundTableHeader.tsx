"use client";

import { motion } from "framer-motion";
import { SealStamp, InkDivider } from "@/components/ui/ChineseDecor";

/**
 * 百家论道 - 页面头部
 * 印章风格标题 + 古典分隔线
 */
export default function RoundTableHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center"
    >
      <SealStamp variant="cinnabar" size="md">
        百家论道
      </SealStamp>
      <h1 className="mt-3 font-serif text-4xl font-bold tracking-widest text-ink-800 dark:text-rice-50 md:text-5xl">
        圆桌论道
      </h1>
      <p className="mt-3 text-sm text-ink-500 dark:text-rice-400 md:text-base">
        四位圣贤，同一话题，各陈己见 —— 观千年智慧交锋
      </p>
      <InkDivider className="mt-5" />
    </motion.div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";
import clsx from "clsx";
import { presetTopics } from "@/lib/roundtableData";

interface TopicSelectorProps {
  onSelect: (topic: string) => void;
  disabled?: boolean;
}

/**
 * 百家论道 - 话题选择器
 * 预设话题卡片 + 自定义输入框
 */
export default function TopicSelector({ onSelect, disabled }: TopicSelectorProps) {
  const [customTopic, setCustomTopic] = useState("");

  const handleCustomSubmit = () => {
    const topic = customTopic.trim();
    if (topic) {
      onSelect(topic);
      setCustomTopic("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleCustomSubmit();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="mx-auto max-w-3xl"
    >
      {/* 预设话题卡片 */}
      <div className="mb-6">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={14} className="text-bronze-500" />
          <span className="font-serif text-sm text-ink-500 dark:text-rice-400">
            选择一个话题，开启论道
          </span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {presetTopics.map((topic, idx) => (
            <motion.button
              key={topic}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 + idx * 0.08 }}
              onClick={() => onSelect(topic)}
              disabled={disabled}
              className={clsx(
                "group relative overflow-hidden rounded-lg border px-5 py-3.5 text-left transition-all",
                "border-ink-100 bg-white/80 hover:border-bamboo-400 hover:shadow-scroll",
                "dark:border-ink-600 dark:bg-ink-700/60 dark:hover:border-bamboo-500",
                "disabled:cursor-not-allowed disabled:opacity-50"
              )}
            >
              {/* 竹简纹理装饰条 */}
              <div className="absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-bamboo-400 to-bamboo-600 opacity-40 transition-opacity group-hover:opacity-80" />

              <div className="flex items-center justify-between pl-3">
                <span className="font-serif text-sm font-medium text-ink-700 dark:text-rice-200 md:text-base">
                  {topic}
                </span>
                <ArrowRight
                  size={14}
                  className="shrink-0 text-ink-300 transition-transform group-hover:translate-x-1 group-hover:text-bamboo-500 dark:text-ink-500"
                />
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* 自定义输入 */}
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-ink-100 dark:bg-ink-600" />
        <span className="text-xs text-ink-400 dark:text-rice-500">或自定义话题</span>
        <div className="h-px flex-1 bg-ink-100 dark:bg-ink-600" />
      </div>
      <div className="mt-3 flex items-center gap-2.5">
        <input
          type="text"
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="输入你感兴趣的话题……"
          className={clsx(
            "flex-1 rounded-lg border border-ink-200 bg-white px-5 py-3 font-serif text-ink-700 outline-none transition-colors",
            "focus:border-cinnabar-400 focus:shadow-scroll-soft",
            "dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200",
            "disabled:opacity-50"
          )}
        />
        <button
          onClick={handleCustomSubmit}
          disabled={!customTopic.trim() || disabled}
          className={clsx(
            "flex shrink-0 items-center justify-center rounded-lg bg-cinnabar-600 px-5 py-3 font-serif text-sm font-medium text-rice-50 shadow-scroll-soft transition-all",
            "hover:bg-cinnabar-700 hover:shadow-scroll",
            "disabled:cursor-not-allowed disabled:opacity-40"
          )}
        >
          开始论道
        </button>
      </div>
    </motion.div>
  );
}

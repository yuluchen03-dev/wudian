"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import clsx from "clsx";

/**
 * 演示引导组件
 * 提供 3 个预设安全问答，适合现场演示时一键填入对话
 */

export interface DemoPresetQuestion {
  /** 问题文本 */
  question: string;
  /** 简短标签（显示在按钮上） */
  label: string;
}

/** 计划书约定的 3 个安全演示问题 */
export const DEMO_PRESET_QUESTIONS: DemoPresetQuestion[] = [
  {
    question: "我很努力但总不被领导认可，怎么办？",
    label: "职场困惑",
  },
  {
    question: "朋友一直不听劝，我还要继续劝吗？",
    label: "交友之道",
  },
  {
    question: "做错事了，该怎么面对？",
    label: "改过自新",
  },
];

interface DemoGuideProps {
  /** 点击预设问题时的回调，参数为问题全文 */
  onSelectQuestion: (question: string) => void;
  /** 是否禁用（如正在流式输出时） */
  disabled?: boolean;
  /** 自定义问题列表，不传则使用默认 3 个 */
  questions?: DemoPresetQuestion[];
  /** 是否为大尺寸（演示模式），默认 true */
  large?: boolean;
  /** 额外 className */
  className?: string;
}

export default function DemoGuide({
  onSelectQuestion,
  disabled = false,
  questions = DEMO_PRESET_QUESTIONS,
  large = true,
  className,
}: DemoGuideProps) {
  return (
    <div className={clsx("w-full", className)}>
      {/* 标题行 */}
      <div className="mb-3 flex items-center gap-1.5">
        <Sparkles
          size={large ? 16 : 13}
          className="text-cinnabar-600"
        />
        <span
          className={clsx(
            "font-serif text-bronze-500",
            large ? "text-sm" : "text-xs"
          )}
        >
          推荐演示问题
        </span>
        <span
          className={clsx(
            "text-ink-300",
            large ? "text-xs" : "text-[10px]"
          )}
        >
          · 点击直接发送
        </span>
      </div>

      {/* 问题按钮 */}
      <div className="flex flex-col gap-2.5 sm:flex-row sm:flex-wrap">
        {questions.map((q, idx) => (
          <motion.button
            key={q.question}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08 }}
            whileHover={disabled ? {} : { scale: 1.02 }}
            whileTap={disabled ? {} : { scale: 0.98 }}
            onClick={() => !disabled && onSelectQuestion(q.question)}
            disabled={disabled}
            className={clsx(
              "group relative overflow-hidden rounded-xl border text-left transition-all duration-300",
              large
                ? "border-ink-200 bg-white/80 px-5 py-3.5 shadow-scroll"
                : "border-ink-200 bg-rice-50 px-3 py-2",
              disabled
                ? "cursor-not-allowed opacity-40"
                : "hover:border-cinnabar-400 hover:shadow-popup dark:border-ink-500 dark:bg-ink-700 dark:hover:border-cinnabar-500"
            )}
          >
            {/* 序号印章 */}
            <div className="flex items-start gap-3">
              <span
                className={clsx(
                  "flex shrink-0 items-center justify-center rounded-full bg-cinnabar-600 font-serif font-bold text-rice-50",
                  large ? "h-7 w-7 text-sm" : "h-5 w-5 text-[11px]"
                )}
              >
                {idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                {/* 标签 */}
                <span
                  className={clsx(
                    "mb-0.5 block font-medium text-cinnabar-600",
                    large ? "text-xs" : "text-[10px]"
                  )}
                >
                  {q.label}
                </span>
                {/* 问题全文 */}
                <span
                  className={clsx(
                    "block font-serif text-ink-700 dark:text-rice-200",
                    large ? "text-base leading-relaxed" : "text-sm leading-snug"
                  )}
                >
                  {q.question}
                </span>
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

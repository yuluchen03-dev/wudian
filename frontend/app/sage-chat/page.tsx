"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, ChevronLeft, AlertCircle } from "lucide-react";
import clsx from "clsx";
import SageChat from "@/components/sage/SageChat";
import { DEMO_PRESET_QUESTIONS } from "@/components/demo/DemoGuide";
import { mockSages } from "@/lib/sageData";
import { pageBackgrounds } from "@/lib/visualAssets";
import type { Sage } from "@/lib/types";

export default function SageChatPage() {
  return (
    <Suspense fallback={null}>
      <SageChatContent />
    </Suspense>
  );
}

function SageChatContent() {
  const searchParams = useSearchParams();
  const prefillQuestion = searchParams.get("q") || "";
  // 若带预填问题（如从"每日一句"跳来），默认选中孔子（第一位圣贤）
  const [selectedSage, setSelectedSage] = useState<Sage | null>(
    prefillQuestion ? mockSages[0] : null
  );

  return (
    <div
      className="relative -mx-4 -my-8 min-h-screen px-4 py-8"
      style={{
        backgroundImage: `linear-gradient(180deg, rgba(248,245,238,0.88), rgba(248,245,238,0.96)), url(${pageBackgrounds.sageChat})`,
        backgroundSize: "cover",
        backgroundPosition: "center top",
      }}
    >
      <div className="space-y-6">
      {/* 顶部固定免责声明条 */}
      <div className="sticky top-16 z-30 flex items-center justify-center gap-2 rounded-lg border border-bronze-400/30 bg-rice-100/90 px-4 py-2 text-center backdrop-blur-sm dark:bg-ink-700/80">
        <AlertCircle size={14} className="shrink-0 text-bronze-500" />
        <span className="text-xs leading-tight text-ink-500 dark:text-rice-300">
          以下回应为基于《论语》思想的 AI 演绎，非历史人物原话 · 原文引用均可溯源
        </span>
      </div>

      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-cinnabar-600/10 px-4 py-1 text-xs text-cinnabar-600">
          <MessageCircle size={13} />
          与圣贤对话
        </div>
        <h1 className="font-serif text-4xl font-bold tracking-widest text-ink-800 dark:text-rice-50">
          问道圣贤
        </h1>
        <p className="mt-3 text-sm text-ink-500 dark:text-rice-300">
          千年智慧，今朝对话 —— 选择一位圣贤，聆听教诲
        </p>
        <div className="classical-divider mx-auto mt-5 w-40" />
      </motion.div>

      <AnimatePresence mode="wait">
        {/* 圣贤选择界面 */}
        {!selectedSage && (
          <motion.div
            key="select"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 gap-5 md:grid-cols-3"
          >
            {mockSages.map((sage, idx) => (
              <motion.button
                key={sage.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                onClick={() => setSelectedSage(sage)}
                className={clsx(
                  "group relative overflow-hidden rounded-2xl border-2 p-6 text-left transition-all duration-300",
                  "border-ink-200 bg-rice-50 shadow-scroll",
                  "hover:border-cinnabar-400 hover:shadow-popup dark:border-ink-600 dark:from-ink-700 dark:to-ink-800"
                )}
                style={{
                  backgroundImage: sage.sceneImage
                    ? `linear-gradient(180deg, rgba(255,252,244,0.58), rgba(255,248,232,0.92)), url(${sage.sceneImage})`
                    : undefined,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                }}
              >
                {/* 水墨装饰 */}
                <div
                  className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-10 blur-2xl transition-opacity group-hover:opacity-20"
                  style={{ backgroundColor: sage.avatar_color }}
                />

                {/* 头像 */}
                <div className="mb-4 flex justify-center">
                  <div
                    className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-full bg-cover bg-center font-serif text-3xl font-bold text-rice-50 shadow-lg transition-transform duration-300 group-hover:scale-110"
                    style={{
                      backgroundColor: sage.avatar_color,
                      backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined,
                    }}
                  >
                    <span className={sage.portraitImage ? "sr-only" : ""}>{sage.name[0]}</span>
                  </div>
                </div>

                {/* 信息 */}
                <div className="text-center">
                  <h3 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
                    {sage.name}
                  </h3>
                  <p className="mt-2 text-xs text-bronze-500">
                    {sage.speaking_style}
                  </p>
                  <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-ink-500 dark:text-rice-300">
                    {sage.description}
                  </p>
                </div>

                {/* 预设问题预览 */}
                <div className="mt-4 border-t border-ink-100 pt-3 dark:border-ink-600">
                  <div className="mb-1.5 text-center text-[11px] text-ink-400">
                    可问：
                  </div>
                  <div className="flex flex-wrap justify-center gap-1">
                    {sage.suggested_questions.slice(0, 2).map((q) => (
                      <span
                        key={q}
                        className="rounded-full bg-ink-100 px-2 py-0.5 text-[11px] text-ink-500 dark:bg-ink-600 dark:text-rice-300"
                      >
                        {q}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 点击提示 */}
                <div className="mt-4 text-center text-xs font-medium text-cinnabar-600 opacity-0 transition-opacity group-hover:opacity-100">
                  点击开始对话 →
                </div>
              </motion.button>
            ))}
          </motion.div>
        )}

        {/* 对话界面 */}
        {selectedSage && (
          <motion.div
            key="chat"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-auto max-w-3xl"
          >
            {/* 返回按钮 */}
            <button
              onClick={() => setSelectedSage(null)}
              className="mb-4 flex items-center gap-1 text-sm text-ink-500 transition-colors hover:text-cinnabar-600 dark:text-rice-300"
            >
              <ChevronLeft size={16} /> 选择其他圣贤
            </button>

            {/* 演示引导组件（仅在选择圣贤后、首次对话前显示） */}
            <DemoGuideWrapper sage={selectedSage} />

            <SageChat
              sage={selectedSage}
              demoMode
              presetQuestions={DEMO_PRESET_QUESTIONS.map((q) => q.question)}
              initialMessage={prefillQuestion || undefined}
            />
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </div>
  );
}

/**
 * 演示引导包装器
 * 在对话区上方显示，提供额外的演示路径说明
 */
function DemoGuideWrapper({ sage }: { sage: Sage }) {
  return (
    <div className="mb-4 rounded-xl border border-cinnabar-200/50 bg-cinnabar-50/40 px-4 py-3 dark:bg-ink-700/40">
      <div className="mb-1 flex items-center gap-1.5 text-xs text-cinnabar-600">
        <MessageCircle size={12} />
        演示提示
      </div>
      <p className="text-sm text-ink-500 dark:text-rice-300">
        已选择 <span className="font-serif font-bold text-ink-700 dark:text-rice-100">{sage.name}</span>。
        可在下方对话框中直接输入问题，或点击推荐演示问题一键发送。
      </p>
    </div>
  );
}

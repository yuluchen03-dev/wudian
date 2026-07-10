"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Sparkles,
  Loader2,
  AlertCircle,
  BookOpen,
  ScrollText,
  Lightbulb,
  Compass,
} from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";

interface AIExplainPanelProps {
  open: boolean;
  verseId: string;
  original: string;
  translation?: string;
  onClose: () => void;
}

interface ExplainResult {
  translation: string;
  background: string;
  modern_analogy: string;
  reflection: string;
  key_words: string[];
  confidence: number;
  disclaimer?: string | null;
}

type Status = "idle" | "loading" | "streaming" | "done" | "error";

export default function AIExplainPanel({
  open,
  verseId,
  original,
  translation,
  onClose,
}: AIExplainPanelProps) {
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [streamText, setStreamText] = useState("");
  const [result, setResult] = useState<ExplainResult | null>(null);

  // 用 ref + requestAnimationFrame 优化流式更新性能
  const bufferRef = useRef("");
  const rafRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  /** 把 buffer 中的增量文本刷到 state（rAF 节流） */
  const flushBuffer = useCallback(() => {
    rafRef.current = null;
    setStreamText(bufferRef.current);
  }, []);

  const appendChunk = useCallback(
    (chunk: string) => {
      bufferRef.current += chunk;
      if (rafRef.current === null) {
        rafRef.current = requestAnimationFrame(flushBuffer);
      }
    },
    [flushBuffer]
  );

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamText, status]);

  // 清理 rAF
  useEffect(() => {
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  /** 重置状态 */
  const reset = useCallback(() => {
    bufferRef.current = "";
    setStreamText("");
    setResult(null);
    setErrorMsg("");
    setStatus("idle");
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  /** 面板打开/切换经文时自动触发讲解 */
  useEffect(() => {
    if (open) {
      reset();
      void handleExplain();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, verseId]);

  /** 触发 AI 讲解 */
  const handleExplain = async () => {
    setStatus("loading");
    setErrorMsg("");
    bufferRef.current = "";
    setStreamText("");

    try {
      const res = await api.explainVerse(verseId, original, translation, (chunk) => {
        setStatus("streaming");
        appendChunk(chunk);
      });

      // 确保最后把完整 buffer 刷出
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      bufferRef.current = "";
      setStreamText("");
      setResult(res);
      setStatus("done");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "AI 讲解生成失败，请稍后重试";
      setErrorMsg(msg);
      setStatus("error");
    }
  };

  /** 从流式文本中粗略提取各段（按 \n\n 分隔） */
  const streamSections = streamText.split("\n\n").filter((s) => s.trim());

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* 遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-ink-800/30 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* 面板：从右侧滑入 */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-rice-50 shadow-2xl dark:bg-ink-800"
          >
            {/* 头部 */}
            <div className="flex items-center justify-between border-b border-ink-100 bg-gradient-to-r from-cinnabar-600 to-cinnabar-700 px-5 py-4 dark:border-ink-600">
              <div className="flex items-center gap-2.5 text-rice-50">
                <Sparkles size={20} className="shrink-0" />
                <div>
                  <h3 className="font-serif text-lg font-bold tracking-wide">
                    AI 逐句精讲
                  </h3>
                  <p className="text-[11px] opacity-80">基于原文的智能解读</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="rounded-full p-1.5 text-rice-50/80 transition-colors hover:bg-rice-50/20 hover:text-rice-50"
                aria-label="关闭"
              >
                <X size={18} />
              </button>
            </div>

            {/* 原文展示 */}
            <div className="border-b border-ink-100 bg-rice-100/40 px-5 py-4 dark:border-ink-600 dark:bg-ink-700/40">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs text-bronze-500">
                <BookOpen size={12} /> 当前经文
              </div>
              <p className="font-serif text-base leading-relaxed text-ink-800 dark:text-rice-50">
                {original}
              </p>
              {translation && (
                <p className="mt-2 text-xs leading-relaxed text-ink-500 dark:text-rice-300">
                  {translation}
                </p>
              )}
            </div>

            {/* 内容区 */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto px-5 py-4"
            >
              {/* 加载中 */}
              {status === "loading" && (
                <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-400">
                  <Loader2 size={32} className="animate-spin text-cinnabar-500" />
                  <p className="text-sm">AI 正在研读经文……</p>
                </div>
              )}

              {/* 错误 */}
              {status === "error" && (
                <div className="flex flex-col items-center justify-center gap-3 py-16">
                  <AlertCircle size={32} className="text-cinnabar-500" />
                  <p className="text-center text-sm text-ink-500 dark:text-rice-300">
                    {errorMsg}
                  </p>
                  <button
                    onClick={handleExplain}
                    className="mt-2 rounded-md border border-cinnabar-400 px-4 py-1.5 text-sm text-cinnabar-600 transition-colors hover:bg-cinnabar-50 dark:hover:bg-ink-700"
                  >
                    重新生成
                  </button>
                </div>
              )}

              {/* 流式输出中：分段显示 */}
              {(status === "streaming" || status === "loading") && streamText && (
                <div className="space-y-4">
                  {streamSections.map((sec, idx) => (
                    <StreamSection key={idx} index={idx} text={sec} />
                  ))}
                  <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-cinnabar-600 align-middle" />
                </div>
              )}

              {/* 完成：结构化展示 */}
              {status === "done" && result && (
                <div className="space-y-5">
                  <ExplainSection
                    icon={<ScrollText size={15} />}
                    label="白话翻译"
                    color="cinnabar"
                    text={result.translation}
                  />
                  <ExplainSection
                    icon={<BookOpen size={15} />}
                    label="背景故事"
                    color="bronze"
                    text={result.background}
                  />
                  <ExplainSection
                    icon={<Lightbulb size={15} />}
                    label="现代类比"
                    color="ink"
                    text={result.modern_analogy}
                  />
                  <ExplainSection
                    icon={<Compass size={15} />}
                    label="延伸思考"
                    color="cinnabar"
                    text={result.reflection}
                  />

                  {/* 核心字词 */}
                  {result.key_words.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-bronze-500">
                        <Sparkles size={13} /> 核心字词
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {result.key_words.map((w) => (
                          <span
                            key={w}
                            className="rounded-full border border-bronze-300 bg-bronze-50 px-2.5 py-0.5 text-xs text-bronze-600 dark:border-bronze-500 dark:bg-ink-700 dark:text-bronze-300"
                          >
                            {w}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 低置信度提示 */}
                  {result.disclaimer && (
                    <div className="flex items-start gap-1.5 rounded-md border border-bronze-200 bg-bronze-50/50 px-3 py-2 text-[11px] leading-relaxed text-bronze-600 dark:border-ink-500 dark:bg-ink-700/50 dark:text-bronze-300">
                      <AlertCircle size={12} className="mt-0.5 shrink-0" />
                      <span>{result.disclaimer}</span>
                    </div>
                  )}

                  {/* 重新生成按钮 */}
                  <button
                    onClick={handleExplain}
                    className="flex w-full items-center justify-center gap-1.5 rounded-md border border-ink-200 py-2 text-sm text-ink-600 transition-colors hover:border-cinnabar-400 hover:text-cinnabar-600 dark:border-ink-500 dark:text-rice-300"
                  >
                    <Sparkles size={14} /> 重新生成
                  </button>
                </div>
              )}
            </div>

            {/* 底部免责 */}
            <div className="flex items-center gap-1.5 border-t border-ink-100 bg-rice-100/40 px-5 py-2 dark:border-ink-600 dark:bg-ink-700/40">
              <AlertCircle size={11} className="shrink-0 text-bronze-500" />
              <span className="text-[10px] leading-tight text-ink-400">
                AI 讲解仅供参考，经典理解请以原典与师长教诲为准
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/** 流式输出时的临时分段 */
function StreamSection({ index, text }: { index: number; text: string }) {
  const labels = ["白话翻译", "背景故事", "现代类比", "延伸思考"];
  const label = labels[index] || "讲解";
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-bronze-500">{label}</div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-700 dark:text-rice-200">
        {text}
      </p>
    </div>
  );
}

/** 结构化讲解段落 */
function ExplainSection({
  icon,
  label,
  text,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  text: string;
  color: "cinnabar" | "bronze" | "ink";
}) {
  const colorMap = {
    cinnabar: "text-cinnabar-600",
    bronze: "text-bronze-500",
    ink: "text-ink-500 dark:text-rice-300",
  };
  return (
    <div>
      <div className={clsx("mb-1.5 flex items-center gap-1.5 text-xs font-medium", colorMap[color])}>
        {icon}
        <span>{label}</span>
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-700 dark:text-rice-200">
        {text || "（暂无）"}
      </p>
    </div>
  );
}

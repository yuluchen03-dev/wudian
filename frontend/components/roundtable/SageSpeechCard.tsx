"use client";

import { motion } from "framer-motion";
import { BookOpen, Scroll } from "lucide-react";
import clsx from "clsx";
import type { Sage } from "@/lib/types";
import type { SageRoundSpeech } from "@/lib/roundtableData";
import { sageColors } from "@/lib/roundtableData";

interface SageSpeechCardProps {
  sage: Sage;
  speech: SageRoundSpeech;
  index: number;
  isLast: boolean;
}

/**
 * 百家论道 - 单个圣贤发言卡片
 * 包含：头像、发言内容、引用卡片
 */
export default function SageSpeechCard({ sage, speech, index, isLast }: SageSpeechCardProps) {
  const colors = sageColors[sage.id];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 * index }}
      className="relative flex gap-4"
    >
      {/* 时间线竖线 + 圆点 */}
      <div className="flex flex-col items-center">
        {/* 圆点 */}
        <div
          className={clsx(
            "z-10 flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-cover bg-center font-serif text-sm font-bold text-rice-50 shadow-md md:h-10 md:w-10 md:text-base",
            speech.isStreaming && "animate-pulse"
          )}
          style={{
            backgroundColor: sage.avatar_color,
            backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined,
          }}
        >
          <span className={sage.portraitImage ? "sr-only" : ""}>{sage.name[0]}</span>
        </div>
        {/* 竖线 */}
        {!isLast && (
          <div className="w-0.5 flex-1 bg-gradient-to-b from-ink-200 to-ink-100 dark:from-ink-500 dark:to-ink-600" />
        )}
      </div>

      {/* 发言内容 */}
      <div className="flex-1 pb-8">
        {/* 头部：圣贤名 + 时代 */}
        <div className="mb-2 flex items-center gap-2">
          <span className="font-serif text-base font-bold text-ink-800 dark:text-rice-100 md:text-lg">
            {sage.name}
          </span>
          <span className="text-xs text-ink-400 dark:text-rice-500">
            {sage.speaking_style?.split("，")[0]}
          </span>
        </div>

        {/* 发言气泡 */}
        <div
          className={clsx(
            "rounded-xl rounded-tl-sm border px-5 py-4 shadow-scroll-soft",
            "bg-white dark:bg-ink-700",
            "border-ink-100 dark:border-ink-600"
          )}
        >
          {/* 内容 */}
          <SageContent content={speech.content} isStreaming={speech.isStreaming} />

          {/* 流式光标 */}
          {speech.isStreaming && speech.content && (
            <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-cinnabar-600 align-middle" />
          )}
        </div>

        {/* 引用卡片 */}
        {speech.citations.length > 0 && !speech.isStreaming && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
            className="mt-3"
          >
            <div className="flex items-center gap-1.5 mb-2">
              <Scroll size={12} className="text-bronze-500" />
              <span className="text-xs text-ink-400 dark:text-rice-500">
                思想依据 · {speech.citations.length} 段原文
              </span>
            </div>
            <div className="space-y-1.5">
              {speech.citations.map((citation, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    "relative overflow-hidden rounded-md border px-3.5 py-2.5",
                    "border-ink-100 bg-rice-50/80 dark:border-ink-600 dark:bg-ink-700/60"
                  )}
                >
                  {/* 竹简纹理装饰条 */}
                  <div className="absolute left-0 top-0 h-full w-0.5 bg-gradient-to-b from-bamboo-400 to-bamboo-600 opacity-60" />
                  <div className="pl-2">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] text-ink-400 dark:text-rice-500">
                        {citation.source}
                      </span>
                      <span className="text-[10px] text-ink-300 dark:text-ink-500">
                        相关度 {Math.round(citation.similarity * 100)}%
                      </span>
                    </div>
                    <p
                      className="font-kai text-sm leading-relaxed text-ink-700 dark:text-rice-200"
                      style={{ letterSpacing: "0.02em" }}
                    >
                      {citation.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {speech.sentenceEvidence && speech.sentenceEvidence.length > 0 && !speech.isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="mt-3 rounded-lg border border-bamboo-200 bg-bamboo-50/70 p-3 dark:border-bamboo-700/50 dark:bg-bamboo-900/10"
          >
            <div className="mb-2 flex items-center gap-1.5">
              <BookOpen size={12} className="text-bamboo-600" />
              <span className="text-xs font-medium text-bamboo-700 dark:text-bamboo-200">
                逐句经典检索证据
              </span>
            </div>
            <div className="space-y-2">
              {speech.sentenceEvidence.map((evidence, idx) => (
                <div key={`${evidence.sentence}-${idx}`} className="grid gap-1 text-xs md:grid-cols-[1fr_1.2fr]">
                  <p className="font-kai leading-relaxed text-ink-700 dark:text-rice-200">
                    {evidence.sentence}
                  </p>
                  <div className="rounded-md bg-white/70 px-2.5 py-1.5 text-ink-500 dark:bg-ink-800/70 dark:text-rice-400">
                    <span className="mr-2 text-bamboo-700 dark:text-bamboo-200">{evidence.source}</span>
                    <span>{evidence.original}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

/* ============ 内容渲染子组件 ============ */

function SageContent({ content, isStreaming }: { content: string; isStreaming: boolean }) {
  if (!content && isStreaming) {
    return (
      <div className="flex items-center gap-2 py-2">
        <span className="text-ink-400 dark:text-rice-500">正在思索</span>
        <span className="flex gap-0.5">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="inline-block h-1 w-1 rounded-full bg-bronze-400"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.3 }}
            />
          ))}
        </span>
      </div>
    );
  }

  // 解析 <<<TAG>>> 格式
  if (content.includes("<<<")) {
    const parts = parseTaggedContent(content);
    return (
      <div className="space-y-3">
        {parts.map((part, i) => {
          if (part.type === "quote") {
            return (
              <div
                key={i}
                className="relative overflow-hidden rounded-md border-l-4 border-cinnabar-600 bg-gradient-to-br from-rice-100 to-rice-50 py-3 pl-4 pr-3 dark:from-ink-600/40 dark:to-ink-600/20"
              >
                <div className="mb-1">
                  <span className="inline-flex items-center rounded-sm bg-cinnabar-600 px-1.5 py-0.5 font-serif text-[10px] font-medium tracking-wider text-rice-50">
                    原文
                  </span>
                </div>
                <p
                  className="font-kai text-base leading-loose text-ink-800 dark:text-rice-100"
                  style={{ letterSpacing: "0.05em" }}
                >
                  {part.text}
                </p>
                {part.source && (
                  <span className="mt-1 inline-flex items-center gap-1 text-xs text-bronze-500 dark:text-rice-400">
                    <span className="h-px w-4 bg-bronze-400/50" />
                    {part.source}
                  </span>
                )}
              </div>
            );
          }
          if (part.type === "insight") {
            return (
              <div
                key={i}
                className="rounded-lg border border-rice-300 bg-rice-100/90 px-4 py-3 dark:bg-rice-300/10"
              >
                <div className="mb-1 flex items-center gap-1 text-xs font-medium text-bronze-500">
                  <BookOpen size={12} />
                  白话点睛
                </div>
                <p className="text-sm leading-relaxed text-ink-700 dark:text-rice-200">
                  {part.text}
                </p>
              </div>
            );
          }
          return (
            <p
              key={i}
              className="font-kai whitespace-pre-wrap text-base leading-loose text-ink-800 dark:text-rice-100"
              style={{ letterSpacing: "0.03em" }}
            >
              {part.text}
            </p>
          );
        })}
      </div>
    );
  }

  // 普通文本
  return (
    <p
      className="font-kai whitespace-pre-wrap text-base leading-loose text-ink-800 dark:text-rice-100"
      style={{ letterSpacing: "0.03em" }}
    >
      {content}
    </p>
  );
}

/* ============ 内容解析 ============ */

type ContentPart =
  | { type: "text"; text: string }
  | { type: "quote"; text: string; source?: string }
  | { type: "insight"; text: string };

function parseTaggedContent(content: string): ContentPart[] {
  const parts: ContentPart[] = [];
  const TAGS: Array<{ tag: string; type: "quote" | "text" | "insight" | "source" | "ignore" }> = [
    { tag: "QUOTE", type: "quote" },
    { tag: "SOURCE", type: "source" },
    { tag: "CLASSICAL", type: "text" },
    { tag: "VERNACULAR", type: "insight" },
    { tag: "DISCLAIMER", type: "ignore" },
  ];

  const tagMatches: Array<{ tag: string; type: string; index: number }> = [];
  const tagRegex = /<<<(\w+)>>>/g;
  let m: RegExpExecArray | null;
  while ((m = tagRegex.exec(content)) !== null) {
    tagMatches.push({ tag: m[1], type: m[1], index: m.index });
  }

  if (tagMatches.length === 0) return [];

  const leading = content.slice(0, tagMatches[0].index).trim();
  if (leading) parts.push({ type: "text", text: leading });

  for (let i = 0; i < tagMatches.length; i++) {
    const { tag, index } = tagMatches[i];
    const tagDef = TAGS.find((t) => t.tag === tag);
    const segType = tagDef?.type ?? "text";
    const contentStart = index + tag.length + 6;
    const contentEnd = i + 1 < tagMatches.length ? tagMatches[i + 1].index : content.length;
    const segText = content.slice(contentStart, contentEnd).trim();
    if (!segText) continue;

    if (segType === "quote") parts.push({ type: "quote", text: segText });
    else if (segType === "source") {
      const last = parts[parts.length - 1];
      if (last && last.type === "quote" && segText !== "无") last.source = segText;
    } else if (segType === "insight") parts.push({ type: "insight", text: segText });
    else if (segType === "text") parts.push({ type: "text", text: segText });
  }

  if (parts.length === 0) {
    parts.push({ type: "text", text: content.replace(/<<<\w+>>>/g, "").trim() });
  }
  return parts;
}

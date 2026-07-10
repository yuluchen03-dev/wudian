"use client";

import { motion } from "framer-motion";
import { Users } from "lucide-react";
import clsx from "clsx";
import type { Sage } from "@/lib/types";
import type { SageRoundSpeech, DebateClash } from "@/lib/roundtableData";

interface DebateTimelineProps {
  sages: Sage[];
  speeches: SageRoundSpeech[];
  clashes: DebateClash[];
  isDebating: boolean;
}

export default function DebateTimeline({ sages, speeches, clashes, isDebating }: DebateTimelineProps) {
  const sageMap = Object.fromEntries(sages.map((s) => [s.id, s]));
  const sageNames = Object.fromEntries(sages.map((s) => [s.id, s.name]));

  // Build timeline: speeches interleaved with clashes
  const items: Array<
    | { kind: "speech"; sage: Sage; speech: SageRoundSpeech; idx: number }
    | { kind: "clash"; clash: DebateClash }
  > = [];

  speeches.forEach((speech, idx) => {
    const sage = sageMap[speech.sageId] || createFallbackSage(speech.sageId);
    items.push({ kind: "speech", sage, speech, idx });
    const relatedClash = clashes.find((c) => c.fromSageId === speech.sageId && idx > 0);
    if (relatedClash) items.push({ kind: "clash", clash: relatedClash });
  });

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex items-center gap-2">
        <Users size={16} className="text-bronze-500" />
        <span className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-100">论道记录</span>
        {isDebating && (
          <span className="ml-2 flex items-center gap-1 text-xs text-cinnabar-600 dark:text-cinnabar-400">
            <span className="animate-pulse">●</span>进行中
          </span>
        )}
      </div>

      <div className="space-y-0">
        {items.map((item, i) =>
          item.kind === "speech" ? (
            <SpeechNode key={item.speech.id || `${item.sage.id}-${item.idx}`} sage={item.sage} speech={item.speech} index={item.idx} isLast={item.idx === speeches.length - 1} />
          ) : (
            <ClashNode key={`clash-${i}`} clash={item.clash} sageNames={sageNames} />
          )
        )}
      </div>
    </div>
  );
}

/* ---- Speech node ---- */
function SpeechNode({ sage, speech, index, isLast }: { sage: Sage; speech: SageRoundSpeech; index: number; isLast: boolean }) {
  return (
    <motion.div
      id={`speech-${sage.id}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 * index }}
      className="relative flex gap-4"
    >
      {/* Timeline column */}
      <div className="flex flex-col items-center">
        <div
          className={clsx(
            "z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-serif text-sm font-bold text-rice-50 shadow-md",
            speech.isStreaming && "animate-pulse"
          )}
          style={{ backgroundColor: sage.avatar_color }}
        >
          {sage.name[0]}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-gradient-to-b from-ink-200 to-ink-100 dark:from-ink-500 dark:to-ink-600" />}
      </div>

      {/* Content */}
      <div className="flex-1 pb-8">
        <div className="mb-2 flex items-center gap-2">
          <span className="font-serif text-base font-bold text-ink-800 dark:text-rice-100">{sage.name}</span>
          <span className="text-xs text-ink-400 dark:text-rice-500">{sage.speaking_style?.split("，")[0]}</span>
        </div>

        <div className="rounded-xl rounded-tl-sm border border-ink-100 bg-white px-5 py-4 shadow-scroll-soft dark:border-ink-600 dark:bg-ink-700">
          {!speech.content && speech.isStreaming ? (
            <div className="flex items-center gap-2 py-2">
              <span className="text-ink-400 dark:text-rice-500">正在思索</span>
              {[0, 1, 2].map((i) => (
                <motion.span key={i} className="inline-block h-1 w-1 rounded-full bg-bronze-400" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.3 }} />
              ))}
            </div>
          ) : (
            <p className="font-kai whitespace-pre-wrap text-base leading-loose text-ink-800 dark:text-rice-100" style={{ letterSpacing: "0.03em" }}>
              {speech.content}
            </p>
          )}
          {speech.isStreaming && speech.content && <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-cinnabar-600 align-middle" />}
        </div>

        {/* Citations */}
        {speech.citations.length > 0 && !speech.isStreaming && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3">
            <div className="mb-2 flex items-center gap-1.5">
              <span className="text-[10px] text-ink-400 dark:text-rice-500">思想依据 · {speech.citations.length} 段原文</span>
            </div>
            <div className="space-y-1.5">
              {speech.citations.map((c, ci) => (
                <div key={ci} className="relative overflow-hidden rounded-md border border-ink-100 bg-rice-50/80 px-3.5 py-2.5 dark:border-ink-600 dark:bg-ink-700/60">
                  <div className="absolute left-0 top-0 h-full w-0.5 bg-gradient-to-b from-bamboo-400 to-bamboo-600 opacity-60" />
                  <div className="pl-2">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-[10px] text-ink-400 dark:text-rice-500">{c.source}</span>
                      <span className="text-[10px] text-ink-300 dark:text-ink-500">相关度 {Math.round(c.similarity * 100)}%</span>
                    </div>
                    <p className="font-kai text-sm leading-relaxed text-ink-700 dark:text-rice-200" style={{ letterSpacing: "0.02em" }}>{c.text}</p>
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

/* ---- Clash node ---- */
const clashStyles: Record<string, { color: string; icon: string }> = {
  agree: { color: "bg-bamboo-50 border-bamboo-300 text-bamboo-700 dark:bg-bamboo-900/30 dark:border-bamboo-600 dark:text-bamboo-300", icon: "●" },
  disagree: { color: "bg-cinnabar-50 border-cinnabar-300 text-cinnabar-700 dark:bg-cinnabar-900/30 dark:border-cinnabar-600 dark:text-cinnabar-300", icon: "✕" },
  extend: { color: "bg-rice-100 border-bronze-400/40 text-bronze-600 dark:bg-ink-600/40 dark:border-bronze-500/40 dark:text-bronze-400", icon: "→" },
  reframe: { color: "bg-ink-50 border-ink-300 text-ink-600 dark:bg-ink-600/40 dark:border-ink-400 dark:text-rice-300", icon: "↻" },
  refute: { color: "bg-cinnabar-50 border-cinnabar-400 text-cinnabar-800 dark:bg-cinnabar-900/30 dark:border-cinnabar-500 dark:text-cinnabar-200", icon: "!" },
};

const clashLabels: Record<string, string> = { agree: "认同", disagree: "相左", extend: "继承", reframe: "新解", refute: "反驳" };

function ClashNode({ clash, sageNames }: { clash: DebateClash; sageNames: Record<string, string> }) {
  const s = clashStyles[clash.type] || clashStyles.extend;
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 py-1.5 pl-14">
      <div className="h-px w-6 bg-ink-200 dark:bg-ink-500" />
      <span className={clsx("inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs", s.color)}>
        <span className="text-[10px]">{s.icon}</span>
        <span className="font-medium">{sageNames[clash.fromSageId] || clash.fromSageId}</span>
        <span className="text-[10px] opacity-60">{clashLabels[clash.type]}</span>
        <span className="font-medium">{sageNames[clash.toSageId] || clash.toSageId}</span>
      </span>
      <span className="text-xs text-ink-400 dark:text-rice-500">{clash.summary}</span>
    </motion.div>
  );
}

function createFallbackSage(sageId: string): Sage {
  return {
    id: sageId,
    name: sageId,
    avatar_color: "#57534e",
    description: "",
    speaking_style: "论道来客",
    suggested_questions: [],
  };
}

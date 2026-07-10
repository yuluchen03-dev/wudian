"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  ChevronLeft,
  Clapperboard,
  Eye,
  Layers,
  Lightbulb,
  Map,
  PenLine,
  Quote,
  Sparkles,
  Users,
} from "lucide-react";
import clsx from "clsx";
import type { Comic, ComicPanel } from "@/lib/types";

interface ComicViewerProps {
  comic: Comic;
  onBack: () => void;
}

const characterTone: Record<string, { bg: string; ink: string; accent: string }> = {
  小明: { bg: "bg-sky-100", ink: "text-sky-900", accent: "border-sky-300" },
  夫子: { bg: "bg-stone-200", ink: "text-stone-900", accent: "border-stone-400" },
  小荷: { bg: "bg-amber-100", ink: "text-amber-900", accent: "border-amber-300" },
  阿宝: { bg: "bg-emerald-100", ink: "text-emerald-900", accent: "border-emerald-300" },
};

export default function ComicViewer({ comic, onBack }: ComicViewerProps) {
  const [activePanel, setActivePanel] = useState(0);
  const active = comic.panels[activePanel];

  const totalBeats = useMemo(
    () => comic.panels.map((panel, index) => ({ label: panel.beat || `第${index + 1}格`, index })),
    [comic.panels]
  );

  return (
    <div data-comic-reader className="mx-auto max-w-6xl">
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <button
            onClick={onBack}
            className="mb-4 inline-flex items-center gap-1 text-sm text-ink-500 transition-colors hover:text-cinnabar-600 dark:text-rice-300"
          >
            <ChevronLeft size={16} /> 返回列表
          </button>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-ink-400">
            <span className="inline-flex items-center gap-1 rounded-full bg-cinnabar-600/10 px-2.5 py-1 font-medium text-cinnabar-700 dark:text-cinnabar-300">
              <BookOpen size={13} /> 漫画解读
            </span>
            <span>{comic.panels.length}格短漫</span>
            <span>·</span>
            <span>竖屏分镜阅读</span>
          </div>
          <h3 className="font-serif text-3xl font-bold leading-tight text-ink-800 dark:text-rice-50">
            {comic.title}
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-500 dark:text-rice-300">
            {comic.logline || comic.source_verse}
          </p>
        </div>

        <div data-storyboard-nav className="rounded-lg border border-ink-100 bg-white/75 p-3 shadow-scroll dark:border-ink-600 dark:bg-ink-700/75">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-ink-500 dark:text-rice-300">
            <Map size={14} className="text-cinnabar-600" /> 分镜节奏
          </div>
          <div className="flex flex-wrap gap-2">
            {totalBeats.map((beat) => (
              <button
                key={beat.index}
                onClick={() => setActivePanel(beat.index)}
                className={clsx(
                  "rounded-md border px-2.5 py-1 text-xs transition-colors",
                  activePanel === beat.index
                    ? "border-cinnabar-600 bg-cinnabar-600 text-rice-50"
                    : "border-ink-100 bg-rice-50 text-ink-500 hover:border-cinnabar-200 hover:text-cinnabar-600 dark:border-ink-600 dark:bg-ink-800 dark:text-rice-300"
                )}
              >
                {beat.index + 1}. {beat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_330px]">
        <main
          data-webtoon-strip
          className="rounded-lg border border-ink-100 bg-white/80 p-4 shadow-popup dark:border-ink-600 dark:bg-ink-800/80"
        >
          <div className="mb-4 flex items-center justify-between border-b border-ink-100 pb-3 dark:border-ink-600">
            <div className="flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <Layers size={16} className="text-cinnabar-600" /> 连续分镜
            </div>
            <div className="text-xs text-ink-400">留白控制节奏，文字后期排版，画面可接 Agens 面板图</div>
          </div>

          <div className="space-y-12">
            {comic.panels.map((panel, index) => (
              <ComicPanelFrame
                key={`${comic.id}-${index}`}
                panel={panel}
                index={index}
                active={activePanel === index}
                onFocus={() => setActivePanel(index)}
              />
            ))}
          </div>
        </main>

        <aside className="space-y-4">
          <section className="rounded-lg border border-ink-100 bg-white/75 p-4 shadow-scroll dark:border-ink-600 dark:bg-ink-700/75">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <Quote size={16} className="text-cinnabar-600" /> 原文锚点
            </div>
            <p className="font-serif text-base leading-relaxed text-ink-800 dark:text-rice-50">
              {comic.source_verse}
            </p>
          </section>

          <section data-shot-language className="rounded-lg border border-ink-100 bg-white/75 p-4 shadow-scroll dark:border-ink-600 dark:bg-ink-700/75">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <Clapperboard size={16} className="text-cinnabar-600" /> 当前镜头
            </div>
            <dl className="space-y-3 text-sm">
              <MetaRow label="景别" value={active.shot} />
              <MetaRow label="动作" value={active.action} />
              <MetaRow label="情绪" value={active.emotion} />
              <MetaRow label="隐喻" value={active.visualMetaphor} />
            </dl>
          </section>

          <section data-knowledge-anchor className="rounded-lg border border-bronze-400/40 bg-bronze-500/10 p-4 shadow-scroll">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-bronze-600">
              <Lightbulb size={16} /> 知识锚点
            </div>
            <p className="text-sm leading-relaxed text-ink-700 dark:text-rice-200">
              {active.knowledgeAnchor}
            </p>
          </section>

          {comic.characters && (
            <section className="rounded-lg border border-ink-100 bg-white/75 p-4 shadow-scroll dark:border-ink-600 dark:bg-ink-700/75">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
                <Users size={16} className="text-cinnabar-600" /> 角色圣经
              </div>
              <div className="space-y-3">
                {comic.characters.map((character) => (
                  <div key={character.name} className="rounded-md bg-rice-50 p-3 dark:bg-ink-800">
                    <div className="mb-1 font-serif text-sm font-semibold text-ink-800 dark:text-rice-50">
                      {character.name} · {character.role}
                    </div>
                    <p className="text-xs leading-relaxed text-ink-500 dark:text-rice-300">
                      {character.visualAnchor}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {comic.styleGuide && (
            <section className="rounded-lg border border-ink-100 bg-white/75 p-4 shadow-scroll dark:border-ink-600 dark:bg-ink-700/75">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
                <PenLine size={16} className="text-cinnabar-600" /> 画风规范
              </div>
              <p className="text-xs leading-relaxed text-ink-500 dark:text-rice-300">{comic.styleGuide}</p>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

function ComicPanelFrame({
  panel,
  index,
  active,
  onFocus,
}: {
  panel: ComicPanel;
  index: number;
  active: boolean;
  onFocus: () => void;
}) {
  const tone = characterTone[panel.character] || {
    bg: "bg-rice-100",
    ink: "text-ink-800",
    accent: "border-ink-300",
  };

  return (
    <motion.article
      data-comic-panel
      onViewportEnter={onFocus}
      viewport={{ amount: 0.55 }}
      className={clsx(
        "relative overflow-hidden rounded-lg border-2 bg-rice-100 shadow-scroll transition-all dark:bg-ink-700",
        active ? "border-cinnabar-600 shadow-popup" : "border-ink-800/80 dark:border-ink-300"
      )}
    >
      <div className="absolute left-4 top-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-ink-900 font-serif text-lg font-bold text-rice-50">
        {index + 1}
      </div>

      <div className="relative min-h-[520px] overflow-hidden bg-[#eee8d7]">
        {panel.imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={panel.imageUrl}
            alt={`${panel.beat || "漫画分镜"}：${panel.scene}`}
            className="h-auto w-full object-contain"
          />
        ) : (
          <GeneratedPanelPlaceholder panel={panel} tone={tone} />
        )}

        <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-black/25 to-transparent" />

        {panel.caption && (
          <div className="absolute left-16 top-5 z-10 max-w-[70%] rounded-md bg-rice-50/90 px-3 py-2 text-xs leading-relaxed text-ink-600 shadow-scroll backdrop-blur">
            {panel.caption}
          </div>
        )}

        {panel.dialogue && (
          <div className="absolute bottom-8 left-1/2 z-10 w-[82%] max-w-xl -translate-x-1/2">
            <div className="relative rounded-[1.4rem] bg-white px-5 py-4 text-center shadow-popup">
              <div className="absolute -top-3 left-1/2 h-6 w-6 -translate-x-1/2 rotate-45 bg-white" />
              <div className={clsx("mb-2 inline-flex rounded-full border px-3 py-1 text-xs font-medium", tone.bg, tone.ink, tone.accent)}>
                {panel.character} · {panel.emotion}
              </div>
              <p className="font-serif text-lg leading-relaxed text-ink-800">{panel.dialogue}</p>
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-3 border-t border-ink-100 bg-white/90 p-4 text-sm dark:border-ink-600 dark:bg-ink-800/90 md:grid-cols-[1fr_1fr]">
        <div>
          <div className="mb-1 flex items-center gap-1 text-xs font-medium text-ink-400">
            <Eye size={13} /> 场景
          </div>
          <p className="leading-relaxed text-ink-600 dark:text-rice-300">{panel.scene}</p>
        </div>
        <div>
          <div className="mb-1 flex items-center gap-1 text-xs font-medium text-ink-400">
            <Sparkles size={13} /> 节奏功能
          </div>
          <p className="leading-relaxed text-ink-600 dark:text-rice-300">{panel.beat}</p>
        </div>
      </div>
    </motion.article>
  );
}

function GeneratedPanelPlaceholder({
  panel,
  tone,
}: {
  panel: ComicPanel;
  tone: { bg: string; ink: string; accent: string };
}) {
  return (
    <div className="relative flex min-h-[520px] flex-col justify-between p-8">
      <div className="absolute inset-0 opacity-[0.22] [background-image:linear-gradient(90deg,rgba(28,25,23,.15)_1px,transparent_1px),linear-gradient(rgba(28,25,23,.12)_1px,transparent_1px)] [background-size:36px_36px]" />
      <div className="absolute -right-16 top-20 h-52 w-52 rounded-full bg-cinnabar-600/10 blur-3xl" />
      <div className="absolute -bottom-20 left-10 h-56 w-56 rounded-full bg-bronze-500/15 blur-3xl" />

      <div className="relative z-10 ml-auto max-w-xs rounded-lg border border-ink-800/15 bg-white/70 p-3 text-xs leading-relaxed text-ink-500 shadow-scroll backdrop-blur">
        {panel.shot}
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-xl items-center justify-center py-10">
        <div className={clsx("relative flex h-48 w-48 items-center justify-center rounded-full border-4 shadow-popup", tone.bg, tone.accent)}>
          <div className={clsx("font-serif text-5xl font-bold", tone.ink)}>{panel.character[0]}</div>
          <div className="absolute -bottom-10 w-[140%] rounded-full bg-ink-900/10 px-4 py-2 text-center text-xs text-ink-500">
            {panel.action}
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-md rounded-lg bg-ink-900/75 p-3 text-sm leading-relaxed text-rice-50 shadow-scroll">
        {panel.visualMetaphor}
      </div>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-400">{label}</dt>
      <dd className="mt-0.5 leading-relaxed text-ink-700 dark:text-rice-200">{value || "未设置"}</dd>
    </div>
  );
}

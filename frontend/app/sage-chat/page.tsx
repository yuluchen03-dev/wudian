"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { BookCheck, BookOpen, ChevronDown, Plus, Search, ShieldCheck } from "lucide-react";
import clsx from "clsx";
import SageChat from "@/components/sage/SageChat";
import { DEMO_PRESET_QUESTIONS } from "@/components/demo/DemoGuide";
import { mockSages } from "@/lib/sageData";
import type { Citation, Sage } from "@/lib/types";

export default function SageChatPage() {
  return <Suspense fallback={null}><SageChatContent /></Suspense>;
}

function SageChatContent() {
  const searchParams = useSearchParams();
  const reduceMotion = useReducedMotion();
  const prefillQuestion = searchParams.get("q") || "";
  const [selectedSage, setSelectedSage] = useState<Sage>(mockSages[0]);
  const [chatKey, setChatKey] = useState(0);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [searchChapters, setSearchChapters] = useState<{ name: string; source: string }[]>([]);

  const selectSage = (sage: Sage) => {
    setSelectedSage(sage);
    setActiveCitations([]);
    setSearchChapters([]);
    setChatKey((key) => key + 1);
  };

  const resetConversation = () => {
    setActiveCitations([]);
    setSearchChapters([]);
    setChatKey((key) => key + 1);
  };

  return (
    <div className="-mx-4 -my-8 min-h-[calc(100vh-68px)] bg-[var(--color-canvas)] sm:-mx-6 lg:-mx-8">
      <div className="border-b border-[var(--color-line)] px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div><div className="text-xs tracking-[0.16em] text-[var(--color-citation)]">圣贤问答</div><h1 className="display-serif mt-1 text-2xl font-semibold text-[var(--color-ink)]">向 {selectedSage.name} 请教</h1></div>
          <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]"><ShieldCheck size={15} className="text-[var(--color-citation)]" />回答基于经典原文，引用均可溯源</div>
        </div>
        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 lg:hidden" aria-label="切换圣贤">
          {mockSages.map((sage) => (
            <button key={sage.id} onClick={() => selectSage(sage)} className={clsx("flex min-h-11 shrink-0 items-center gap-2 border-b-2 px-3 text-sm", sage.id === selectedSage.id ? "border-[var(--color-citation)] text-[var(--color-ink)]" : "border-transparent text-[var(--color-muted)]")}>
              <span className="h-6 w-6 rounded-full bg-cover bg-center" style={{ backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined }} />{sage.name}
            </button>
          ))}
        </div>
      </div>

      <motion.div data-ui="sage-workspace" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} className="grid lg:grid-cols-[220px_minmax(0,1fr)_300px]">
        <aside className="hidden min-h-[calc(100vh-165px)] border-r border-[var(--color-line)] bg-[rgba(251,249,243,0.62)] p-4 lg:block">
          <div className="relative mb-4 h-28 overflow-hidden rounded-[4px] border border-[var(--color-line)] bg-[var(--color-action)]">
            <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: selectedSage.sceneImage ? `linear-gradient(180deg, transparent, rgba(36,36,33,0.42)), url(${selectedSage.sceneImage})` : undefined }} />
            <div className="display-serif absolute bottom-3 left-3 text-lg font-semibold text-white">{selectedSage.name}</div>
          </div>
          <button onClick={resetConversation} className="wudian-action w-full px-4 text-sm"><Plus size={16} />新建对话</button>
          <div className="mt-7 text-[11px] tracking-[0.14em] text-[var(--color-muted)]">选择圣贤</div>
          <div className="mt-2 space-y-1">
            {mockSages.map((sage) => (
              <button key={sage.id} onClick={() => selectSage(sage)} className={clsx("flex min-h-12 w-full items-center gap-3 rounded-[4px] px-3 text-left text-sm transition-colors", sage.id === selectedSage.id ? "bg-[var(--color-sage)] text-[var(--color-ink)]" : "text-[var(--color-muted)] hover:bg-white/70")} style={{ backgroundImage: sage.sceneImage ? `linear-gradient(90deg, rgba(251,249,243,0.96), rgba(251,249,243,0.8)), url(${sage.sceneImage})` : undefined, backgroundSize: "cover" }}>
                <span className="h-8 w-8 rounded-[3px] bg-cover bg-center" style={{ backgroundColor: sage.avatar_color, backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined }} />
                <span><span className="display-serif block font-medium">{sage.name}</span><span className="block text-[10px] opacity-70">{sage.speaking_style}</span></span>
              </button>
            ))}
          </div>
        </aside>

        <main className="min-w-0 p-3 sm:p-5 lg:p-6">
          <SageChat key={`${selectedSage.id}-${chatKey}`} sage={selectedSage} demoMode presetQuestions={DEMO_PRESET_QUESTIONS.map((item) => item.question)} initialMessage={prefillQuestion || undefined} onCitationsChange={setActiveCitations} onSearchChaptersChange={setSearchChapters} />
        </main>

        <section data-ui="mobile-evidence" className="border-t border-[var(--color-line)] bg-[var(--color-surface)] lg:hidden">
          <details className="group">
            <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-3 px-5 py-3 [&::-webkit-details-marker]:hidden">
              <span className="display-serif text-base font-semibold">思想依据</span>
              <span className="flex items-center gap-2 text-xs text-[var(--color-action)]">
                {activeCitations.length ? `${activeCitations.length} 条引用` : "等待提问"}
                <ChevronDown size={16} className="transition-transform group-open:rotate-180" />
              </span>
            </summary>
            <div className="border-t border-[var(--color-line)] p-5">
              <EvidenceContent activeCitations={activeCitations} searchChapters={searchChapters} showHeading={false} />
            </div>
          </details>
        </section>

        <aside className="hidden min-h-[calc(100vh-165px)] border-l border-[var(--color-line)] bg-[var(--color-surface)] p-6 lg:block">
          <EvidenceContent activeCitations={activeCitations} searchChapters={searchChapters} />
        </aside>
      </motion.div>
    </div>
  );
}

function EvidenceContent({
  activeCitations,
  searchChapters,
  showHeading = true,
}: {
  activeCitations: Citation[];
  searchChapters: { name: string; source: string }[];
  showHeading?: boolean;
}) {
  return (
    <>
      {showHeading && (
        <div className="flex items-center justify-between">
          <h2 className="display-serif text-lg font-semibold">思想依据</h2>
          <span className="rounded-[3px] bg-[var(--color-sage)] px-2 py-1 text-[10px] text-[var(--color-action)]">
            {activeCitations.length ? `${activeCitations.length} 条引用` : "等待提问"}
          </span>
        </div>
      )}
      <p className={clsx("text-xs leading-6 text-[var(--color-muted)]", showHeading && "mt-2")}>这里同步展示当前回答检索到的原文与篇章，不以静态材料代替真实依据。</p>

      {searchChapters.length > 0 && activeCitations.length === 0 && (
        <div className="mt-5 space-y-2">
          {searchChapters.map((chapter) => <div key={`${chapter.source}-${chapter.name}`} className="flex items-center gap-2 border-b border-[var(--color-line)] py-3 text-xs text-[var(--color-muted)]"><Search size={14} className="text-[var(--color-citation)]" /><span className="truncate">{chapter.source} · {chapter.name}</span></div>)}
        </div>
      )}

      {activeCitations.length > 0 ? (
        <div className="mt-5 space-y-3">
          {activeCitations.map((citation, index) => (
            <article key={`${citation.source}-${citation.verse_no ?? index}`} className="rounded-[5px] border border-[var(--color-line)] bg-white/60 p-4">
              <div className="flex items-center justify-between gap-3 text-xs text-[var(--color-citation)]"><span className="flex items-center gap-2"><BookOpen size={14} />引 {index + 1}</span><span className="truncate text-[var(--color-muted)]">{citation.source || citation.chapter || "经典原文"}</span></div>
              <blockquote className="display-serif mt-3 line-clamp-4 text-sm leading-7 text-[var(--color-ink)]">{citation.text || "原文内容将在回答中展开"}</blockquote>
            </article>
          ))}
          <div className="flex items-start gap-3 bg-[var(--color-highlight)] p-4 text-xs leading-6 text-[var(--color-muted)]"><BookCheck size={18} className="mt-1 shrink-0 text-[var(--color-citation)]" />点击回答中的引用卡片，可查看译文并跳转到完整典籍。</div>
        </div>
      ) : searchChapters.length === 0 ? (
        <div className="mt-5 rounded-[5px] border border-dashed border-[var(--color-line)] p-5 text-center"><BookOpen className="mx-auto text-[var(--color-line)]" /><p className="mt-3 text-xs leading-6 text-[var(--color-muted)]">发送问题后，此处将显示实际命中的经典原文。</p></div>
      ) : null}
    </>
  );
}

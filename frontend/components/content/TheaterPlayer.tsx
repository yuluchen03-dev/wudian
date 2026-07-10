"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  Lightbulb,
  Users,
  BookOpen,
  Sparkles,
  StepForward,
  Map,
  MessageCircle,
  Theater as TheaterIcon,
  Quote,
} from "lucide-react";
import clsx from "clsx";
import type { Theater, TheaterDetail, TheaterLine } from "@/lib/types";

interface TheaterCardProps {
  theater: Theater;
  onClick?: (id: string) => void;
  index?: number;
}

const settingIcons: Record<string, string> = {
  职场: "职",
  校园: "校",
  家庭: "家",
};

const roleColorClasses = [
  "bg-cinnabar-600",
  "bg-bronze-500",
  "bg-ink-600",
  "bg-rice-700",
  "bg-cinnabar-800",
];

export function TheaterCard({ theater, onClick, index = 0 }: TheaterCardProps) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index }}
      onClick={() => onClick?.(theater.id)}
      className="group relative w-full overflow-hidden rounded-lg border border-ink-100 bg-white/75 p-5 text-left shadow-scroll backdrop-blur-sm transition-all hover:-translate-y-1 hover:border-cinnabar-200 hover:shadow-popup dark:border-ink-600 dark:bg-ink-700/75"
      style={{
        backgroundImage: theater.coverImage
          ? `linear-gradient(180deg, rgba(255,252,244,0.74), rgba(255,248,232,0.94)), url(${theater.coverImage})`
          : undefined,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="pointer-events-none absolute inset-0 bg-white/35 opacity-0 transition-opacity group-hover:opacity-40" />
      <div className="pointer-events-none absolute inset-x-5 top-0 h-1 rounded-b-full bg-gradient-to-r from-cinnabar-600 via-bronze-500 to-ink-700 opacity-70" />
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-ink-800 font-serif text-lg font-bold text-rice-50 shadow-scroll dark:bg-rice-100 dark:text-ink-800">
          {settingIcons[theater.modernSetting] || "剧"}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-cinnabar-600/10 px-2 py-0.5 font-medium text-cinnabar-700 dark:text-cinnabar-300">
              经典支线任务
            </span>
            <span className="text-ink-400">{theater.classicalSource}</span>
          </div>
          <h3 className="font-serif text-lg font-semibold leading-snug text-ink-800 transition-colors group-hover:text-cinnabar-700 dark:text-rice-50">
            {theater.title}
          </h3>
        </div>
      </div>

      <p className="line-clamp-2 text-sm leading-relaxed text-ink-500 dark:text-rice-300">
        {theater.summary}
      </p>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded-md bg-rice-100 px-2 py-2 text-ink-500 dark:bg-ink-800 dark:text-rice-300">
          <div className="font-semibold text-ink-700 dark:text-rice-100">{theater.sceneCount}</div>
          <div>幕剧情</div>
        </div>
        <div className="rounded-md bg-rice-100 px-2 py-2 text-ink-500 dark:bg-ink-800 dark:text-rice-300">
          <div className="font-semibold text-ink-700 dark:text-rice-100">{theater.likeCount}</div>
          <div>喜欢</div>
        </div>
        <div className="rounded-md bg-rice-100 px-2 py-2 text-ink-500 dark:bg-ink-800 dark:text-rice-300">
          <div className="font-semibold text-ink-700 dark:text-rice-100">{theater.viewCount}</div>
          <div>观看</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-ink-100 pt-3 text-xs text-ink-400 dark:border-ink-600">
        <span>{theater.modernSetting}情境</span>
        <span className="inline-flex items-center gap-1 font-medium text-cinnabar-600">
          <Play size={13} fill="currentColor" /> 开演
        </span>
      </div>
    </motion.button>
  );
}

interface TheaterPlayerProps {
  theater: TheaterDetail;
  onBack?: () => void;
}

type LineWithScene = TheaterLine & {
  sceneTitle: string;
  sceneSetting: string;
  sceneIndex: number;
  localIndex: number;
};

export function TheaterPlayer({ theater, onBack }: TheaterPlayerProps) {
  const allLines = useMemo<LineWithScene[]>(
    () =>
      theater.scenes.flatMap((scene, sceneIndex) =>
        scene.lines.map((line, localIndex) => ({
          ...line,
          sceneTitle: scene.title,
          sceneSetting: scene.setting,
          sceneIndex,
          localIndex,
          isOriginalVerse: Boolean(line.isOriginalVerse),
        }))
      ),
    [theater.scenes]
  );

  const [currentLine, setCurrentLine] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMoral, setShowMoral] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const progress = allLines.length ? Math.max(0, ((currentLine + 1) / allLines.length) * 100) : 0;
  const activeLine = currentLine >= 0 ? allLines[currentLine] : undefined;
  const activeRole = activeLine
    ? theater.roles.find((role) => role.name === activeLine.role)
    : undefined;
  const sourceLine = allLines.find((line) => line.isOriginalVerse);
  const visibleLines = currentLine >= 0 ? allLines.slice(0, currentLine + 1) : [];

  useEffect(() => {
    if (isPlaying && currentLine < allLines.length - 1) {
      timerRef.current = setTimeout(() => {
        setCurrentLine((prev) => prev + 1);
      }, 2800);
    } else if (currentLine >= allLines.length - 1 && allLines.length > 0) {
      setIsPlaying(false);
      setShowMoral(true);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentLine, allLines.length]);

  const roleColors: Record<string, string> = {};
  theater.roles.forEach((role, index) => {
    roleColors[role.name] = roleColorClasses[index % roleColorClasses.length];
  });

  const goToLine = (index: number) => {
    setIsPlaying(false);
    setCurrentLine(index);
    setShowMoral(index >= allLines.length - 1);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const handlePlay = () => {
    if (currentLine >= allLines.length - 1) {
      setCurrentLine(-1);
      setShowMoral(false);
    }
    setIsPlaying(true);
    setCurrentLine((prev) => (prev < 0 ? 0 : prev));
  };

  const handlePause = () => {
    setIsPlaying(false);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentLine(-1);
    setShowMoral(false);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const handleNext = () => {
    if (currentLine < allLines.length - 1) {
      goToLine(currentLine + 1);
    } else {
      setShowMoral(true);
    }
  };

  return (
    <div
      data-theater-surface
      className="overflow-hidden rounded-lg border border-ink-100 bg-rice-50 shadow-popup dark:border-ink-600 dark:bg-ink-800"
    >
      <div className="border-b border-ink-100 bg-white/80 px-5 py-4 backdrop-blur dark:border-ink-600 dark:bg-ink-700/80">
        <button
          onClick={onBack}
          className="mb-3 inline-flex items-center gap-1 text-sm text-ink-500 transition-colors hover:text-cinnabar-600"
        >
          <ChevronLeft size={16} /> 返回剧目
        </button>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-ink-400">
              <span className="inline-flex items-center gap-1 rounded-full bg-cinnabar-600/10 px-2.5 py-1 font-medium text-cinnabar-700 dark:text-cinnabar-300">
                <TheaterIcon size={13} /> 情景小剧场
              </span>
              <span>{theater.modernSetting}</span>
              <span>·</span>
              <span>{theater.scenes.length}幕 / {allLines.length}句</span>
            </div>
            <h2 className="font-serif text-2xl font-bold leading-tight text-ink-800 dark:text-rice-50">
              {theater.title}
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-500 dark:text-rice-300">
              {theater.summary}
            </p>
          </div>
          <div className="min-w-[180px]">
            <div className="mb-1 flex items-center justify-between text-xs text-ink-400">
              <span>演进进度</span>
              <span>{Math.min(currentLine + 1, allLines.length)}/{allLines.length}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-600">
              <motion.div
                className="h-full rounded-full bg-cinnabar-600"
                animate={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_320px]">
        <main className="min-w-0">
          <section
            data-stage-panel
            className="relative min-h-[230px] overflow-hidden border-b border-ink-100 bg-ink-800 px-5 py-5 text-rice-50 dark:border-ink-600"
            style={{
              backgroundImage: theater.coverImage
                ? `linear-gradient(180deg, rgba(12,10,9,0.42), rgba(12,10,9,0.82)), url(${theater.coverImage})`
                : undefined,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(90deg,rgba(255,255,255,.18)_1px,transparent_1px),linear-gradient(rgba(255,255,255,.12)_1px,transparent_1px)] [background-size:36px_36px]" />
            <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/35 to-transparent" />
            <div className="relative z-10 flex h-full flex-col justify-between gap-8">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-rice-200/20 bg-white/10 px-3 py-1 text-xs text-rice-200">
                  <Sparkles size={13} /> {activeLine?.sceneTitle || theater.scenes[0]?.title || "开场"}
                </div>
                <p className="max-w-2xl font-serif text-xl leading-relaxed text-rice-50">
                  {activeLine?.sceneSetting || theater.scenes[0]?.setting || "按下播放，进入这段经典情境。"}
                </p>
              </div>

              <div className="rounded-lg border border-rice-200/15 bg-white/10 p-4 backdrop-blur">
                <div className="mb-2 flex items-center gap-2 text-xs text-rice-200">
                  <MessageCircle size={14} /> 当前镜头
                </div>
                {activeLine ? (
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={currentLine}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                    >
                      <div className="mb-2 flex items-center gap-2">
                        <RoleAvatar
                          role={activeLine.role}
                          color={roleColors[activeLine.role]}
                          image={activeRole?.portraitImage}
                        />
                        <span className="font-serif font-semibold">{activeLine.role}</span>
                        {activeLine.emotion && (
                          <span className="text-xs text-rice-300">{activeLine.emotion}</span>
                        )}
                      </div>
                      <p className="text-base leading-relaxed text-rice-50">{activeLine.text}</p>
                      {(activeLine.action || activeLine.subtext || activeLine.pressure) && (
                        <div className="mt-3 grid gap-2 text-xs text-rice-200 sm:grid-cols-3">
                          {activeLine.action && (
                            <div data-stage-action className="rounded-md bg-black/20 px-3 py-2">
                              <span className="block text-rice-300">舞台动作</span>
                              {activeLine.action}
                            </div>
                          )}
                          {activeLine.subtext && (
                            <div className="rounded-md bg-black/20 px-3 py-2">
                              <span className="block text-rice-300">潜台词</span>
                              {activeLine.subtext}
                            </div>
                          )}
                          {activeLine.pressure && (
                            <div data-conflict-pressure className="rounded-md bg-black/20 px-3 py-2">
                              <span className="block text-rice-300">冲突压力</span>
                              {activeLine.pressure}
                            </div>
                          )}
                        </div>
                      )}
                    </motion.div>
                  </AnimatePresence>
                ) : (
                  <p className="text-sm leading-relaxed text-rice-200">
                    这不是单纯把原文翻译一遍，而是先把你放进一个现实困境，再让经典来点亮关键选择。
                  </p>
                )}
              </div>
            </div>
          </section>

          <section data-beat-timeline className="border-b border-ink-100 bg-white/60 px-5 py-4 dark:border-ink-600 dark:bg-ink-700/50">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <Map size={16} className="text-cinnabar-600" /> 剧情节拍
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
              {allLines.map((line, index) => (
                <button
                  key={`${line.sceneIndex}-${line.localIndex}`}
                  onClick={() => goToLine(index)}
                  className={clsx(
                    "h-14 rounded-md border px-2 text-left text-xs transition-colors",
                    index === currentLine
                      ? "border-cinnabar-600 bg-cinnabar-600 text-rice-50"
                      : index < currentLine
                        ? "border-bronze-400/40 bg-bronze-500/10 text-bronze-600"
                        : "border-ink-100 bg-white text-ink-400 hover:border-cinnabar-200 hover:text-cinnabar-600 dark:border-ink-600 dark:bg-ink-800 dark:text-rice-300"
                  )}
                  aria-label={`跳到第${index + 1}句`}
                >
                  <div className="font-semibold">#{index + 1}</div>
                  <div className="truncate">{line.beat || line.role}</div>
                  {line.beat && <div className="truncate opacity-70">{line.role}</div>}
                </button>
              ))}
            </div>
          </section>

          <section className="bg-rice-50 px-5 py-5 dark:bg-ink-800">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
                <MessageCircle size={16} className="text-cinnabar-600" /> 对话回放
              </div>
              <div className="text-xs text-ink-400">剧情反馈先出现，经典依据随后落地</div>
            </div>

            <div className="min-h-[260px] space-y-3">
              {visibleLines.map((line, index) => (
                <motion.div
                  key={`${line.sceneIndex}-${line.localIndex}-${index}`}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <DialogueLine
                    line={line}
                    roleColor={roleColors[line.role] || "bg-ink-500"}
                    roleImage={theater.roles.find((role) => role.name === line.role)?.portraitImage}
                  />
                </motion.div>
              ))}

              {currentLine < 0 && (
                <div className="flex h-[240px] flex-col items-center justify-center rounded-lg border border-dashed border-ink-200 bg-white/70 text-center dark:border-ink-600 dark:bg-ink-700/60">
                  <Play size={44} className="mb-3 text-cinnabar-200" />
                  <p className="font-serif text-ink-500 dark:text-rice-300">点开场，看看这一句经典如何进入现实。</p>
                </div>
              )}

              <AnimatePresence>
                {showMoral && (
                  <motion.div
                    data-ending-recap
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="rounded-lg border border-bronze-400/50 bg-bronze-500/10 p-4"
                  >
                    <div className="mb-2 flex items-center gap-2 font-serif font-semibold text-bronze-600">
                      <Lightbulb size={17} /> 结局复盘
                    </div>
                    <p className="text-sm leading-relaxed text-ink-700 dark:text-rice-200">
                      {theater.moral}
                    </p>
                    <div className="mt-3 grid gap-2 text-xs text-ink-500 dark:text-rice-300 sm:grid-cols-3">
                      <span className="rounded-md bg-white/70 px-3 py-2 dark:bg-ink-700">问动机：角色为什么这样反应？</span>
                      <span className="rounded-md bg-white/70 px-3 py-2 dark:bg-ink-700">问反例：换个选择会怎样？</span>
                      <span className="rounded-md bg-white/70 px-3 py-2 dark:bg-ink-700">问边界：现实中何时不适用？</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </section>
        </main>

        <aside className="border-l border-ink-100 bg-white/70 dark:border-ink-600 dark:bg-ink-700/70">
          <section data-cast-panel className="border-b border-ink-100 p-5 dark:border-ink-600">
            <div className="mb-4 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <Users size={16} className="text-cinnabar-600" /> 角色目标
            </div>
            <div className="space-y-3">
              {theater.roles.map((role) => (
                <div key={role.name} className="rounded-lg border border-ink-100 bg-rice-50 p-3 dark:border-ink-600 dark:bg-ink-800">
                  <div className="mb-2 flex items-center gap-2">
                    <RoleAvatar role={role.name} color={roleColors[role.name]} image={role.portraitImage} />
                    <div className="min-w-0">
                      <div className="font-serif text-sm font-semibold text-ink-800 dark:text-rice-50">{role.name}</div>
                      {role.classicalOrigin && (
                        <div className="text-xs text-bronze-500">原型：{role.classicalOrigin}</div>
                      )}
                    </div>
                  </div>
                  <p className="text-xs leading-relaxed text-ink-500 dark:text-rice-300">
                    {role.description}
                  </p>
                  {(role.objective || role.fear || role.strategy) && (
                    <div data-agent-task-panel className="mt-3 space-y-2 border-t border-ink-100 pt-3 text-xs dark:border-ink-600">
                      {role.objective && (
                        <AgentField label="目标" value={role.objective} />
                      )}
                      {role.fear && <AgentField label="恐惧" value={role.fear} />}
                      {role.strategy && <AgentField label="策略" value={role.strategy} />}
                      {role.belief && <AgentField label="信念" value={role.belief} />}
                      {role.conflictTrigger && (
                        <AgentField label="触发器" value={role.conflictTrigger} />
                      )}
                      {role.stageAction && (
                        <AgentField label="动作" value={role.stageAction} />
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {(activeRole?.objective || activeLine?.beat) && (
            <section className="border-b border-ink-100 p-5 dark:border-ink-600">
              <div className="mb-3 text-sm font-medium text-ink-700 dark:text-rice-100">当前任务</div>
              <div className="space-y-2 rounded-lg border border-cinnabar-200 bg-cinnabar-600/5 p-3 text-xs text-ink-600 dark:border-cinnabar-500/40 dark:bg-cinnabar-500/10 dark:text-rice-200">
                {activeLine?.beat && <AgentField label="节拍" value={activeLine.beat} />}
                {activeRole?.objective && <AgentField label="角色目标" value={activeRole.objective} />}
                {activeRole?.strategy && <AgentField label="行动策略" value={activeRole.strategy} />}
              </div>
            </section>
          )}

          <section data-source-anchor className="border-b border-ink-100 p-5 dark:border-ink-600">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink-700 dark:text-rice-100">
              <BookOpen size={16} className="text-cinnabar-600" /> 原文锚点
            </div>
            <div className="rounded-lg bg-ink-800 p-4 text-rice-50">
              <div className="mb-2 flex items-center gap-2 text-xs text-rice-300">
                <Quote size={14} /> {theater.classicalSource}
              </div>
              <p className="font-serif text-base leading-relaxed">
                {sourceLine?.text || "本剧会在关键句旁标出经典出处，避免只剩好看的角色扮演。"}
              </p>
            </div>
          </section>

          <section className="p-5">
            <div className="mb-3 text-sm font-medium text-ink-700 dark:text-rice-100">播放控制</div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="flex h-10 w-10 items-center justify-center rounded-md text-ink-500 transition-colors hover:bg-ink-100 dark:text-rice-300 dark:hover:bg-ink-600"
                aria-label="重置"
              >
                <RotateCcw size={17} />
              </button>
              {isPlaying ? (
                <button
                  onClick={handlePause}
                  className="flex h-11 w-11 items-center justify-center rounded-md bg-cinnabar-600 text-rice-50 transition-colors hover:bg-cinnabar-700"
                  aria-label="暂停"
                >
                  <Pause size={18} />
                </button>
              ) : (
                <button
                  onClick={handlePlay}
                  className="flex h-11 w-11 items-center justify-center rounded-md bg-cinnabar-600 text-rice-50 transition-colors hover:bg-cinnabar-700"
                  aria-label="播放"
                >
                  <Play size={18} fill="currentColor" />
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={currentLine >= allLines.length - 1}
                className="flex h-10 items-center gap-1 rounded-md px-3 text-sm text-ink-600 transition-colors hover:bg-ink-100 disabled:opacity-30 dark:text-rice-300 dark:hover:bg-ink-600"
              >
                <StepForward size={16} /> 下一句
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function RoleAvatar({ role, color, image }: { role: string; color?: string; image?: string }) {
  return (
    <span
      className={clsx(
        "flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-md bg-cover bg-center font-serif text-sm font-bold text-rice-50",
        !image && (color || "bg-ink-500")
      )}
      style={image ? { backgroundImage: `url(${image})` } : undefined}
    >
      <span className={image ? "sr-only" : ""}>{role[0]}</span>
    </span>
  );
}

function AgentField({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[3.5rem_minmax(0,1fr)] gap-2">
      <span className="text-ink-400 dark:text-rice-400">{label}</span>
      <span className="leading-relaxed text-ink-600 dark:text-rice-200">{value}</span>
    </div>
  );
}

function DialogueLine({
  line,
  roleColor,
  roleImage,
}: {
  line: TheaterLine;
  roleColor: string;
  roleImage?: string;
}) {
  return (
    <div
      className={clsx(
        "flex items-start gap-3 rounded-lg border bg-white p-3 shadow-scroll-soft dark:bg-ink-700",
        line.isOriginalVerse
          ? "border-cinnabar-300 ring-1 ring-cinnabar-200"
          : "border-ink-100 dark:border-ink-600"
      )}
    >
      <RoleAvatar role={line.role} color={roleColor} image={roleImage} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-serif text-sm font-semibold text-ink-700 dark:text-rice-100">
            {line.role}
          </span>
          {line.emotion && <span className="text-xs text-bronze-500">{line.emotion}</span>}
          {line.beat && (
            <span className="rounded-full bg-bronze-500/10 px-2 py-0.5 text-[11px] font-medium text-bronze-600 dark:text-bronze-300">
              {line.beat}
            </span>
          )}
          {line.isOriginalVerse && (
            <span className="rounded-full bg-cinnabar-600/10 px-2 py-0.5 text-[11px] font-medium text-cinnabar-700 dark:text-cinnabar-300">
              经典原句
            </span>
          )}
        </div>
        <p
          className={clsx(
            "mt-1 text-sm leading-relaxed",
            line.isOriginalVerse
              ? "font-serif font-medium text-cinnabar-700 dark:text-cinnabar-300"
              : "text-ink-600 dark:text-rice-300"
          )}
        >
          {line.isOriginalVerse ? `「${line.text}」` : line.text}
        </p>
        {(line.action || line.subtext || line.pressure) && (
          <div className="mt-2 grid gap-1.5 text-xs text-ink-500 dark:text-rice-300 sm:grid-cols-3">
            {line.action && <AgentField label="动作" value={line.action} />}
            {line.subtext && <AgentField label="潜台词" value={line.subtext} />}
            {line.pressure && <AgentField label="压力" value={line.pressure} />}
          </div>
        )}
      </div>
    </div>
  );
}

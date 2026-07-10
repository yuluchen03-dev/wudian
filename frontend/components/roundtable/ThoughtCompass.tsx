"use client";

import { motion } from "framer-motion";
import { Compass } from "lucide-react";
import type { ThoughtCompassMark } from "@/lib/thoughtCompass";

interface ThoughtCompassProps {
  mark: ThoughtCompassMark | null;
}

export default function ThoughtCompass({ mark }: ThoughtCompassProps) {
  if (!mark) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-3xl rounded-lg border border-ink-100 bg-white/90 p-5 shadow-scroll dark:border-ink-600 dark:bg-ink-700/85"
    >
      <div className="mb-4 flex items-center gap-2">
        <Compass size={16} className="text-bronze-500" />
        <span className="font-serif text-base font-semibold text-ink-800 dark:text-rice-100">思想坐标</span>
        <span className="ml-auto rounded-full bg-cinnabar-600/10 px-2.5 py-1 font-serif text-xs text-cinnabar-700 dark:text-cinnabar-300">
          {mark.label}
        </span>
      </div>

      <div className="relative mx-auto aspect-square max-w-md rounded-lg border border-ink-100 bg-rice-50 dark:border-ink-600 dark:bg-ink-800">
        <AxisLabel className="top-2 left-1/2 -translate-x-1/2" text="重事功 / 入世" />
        <AxisLabel className="bottom-2 left-1/2 -translate-x-1/2" text="重心性 / 出世" />
        <AxisLabel className="left-2 top-1/2 -translate-y-1/2" text="无为顺应" />
        <AxisLabel className="right-2 top-1/2 -translate-y-1/2" text="有为进取" />
        <div className="absolute left-1/2 top-6 bottom-6 w-px -translate-x-1/2 bg-ink-200 dark:bg-ink-600" />
        <div className="absolute left-6 right-6 top-1/2 h-px -translate-y-1/2 bg-ink-200 dark:bg-ink-600" />
        <SchoolDot x={68} y={64} label="孔子" />
        <SchoolDot x={28} y={30} label="老子" />
        <SchoolDot x={62} y={78} label="墨子" />
        <SchoolDot x={30} y={62} label="韩非" />
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1"
          style={{ left: `${mark.x}%`, bottom: `${mark.y}%` }}
        >
          <span className="h-4 w-4 rounded-full border-2 border-white bg-cinnabar-600 shadow-scroll" />
          <span className="rounded-full bg-white/90 px-2 py-0.5 text-xs font-medium text-cinnabar-700 shadow-scroll-soft dark:bg-ink-700 dark:text-cinnabar-300">
            你
          </span>
        </motion.div>
      </div>

      <div className="mt-4 rounded-lg border-l-4 border-cinnabar-600 bg-rice-50 px-4 py-3 dark:bg-ink-800/60">
        <p className="font-kai text-sm leading-loose text-ink-700 dark:text-rice-200">{mark.imprint}</p>
      </div>
    </motion.div>
  );
}

function AxisLabel({ text, className }: { text: string; className: string }) {
  return (
    <div className={`absolute z-10 rounded-full bg-white/80 px-2 py-0.5 text-[10px] text-ink-400 dark:bg-ink-700 dark:text-rice-400 ${className}`}>
      {text}
    </div>
  );
}

function SchoolDot({ x, y, label }: { x: number; y: number; label: string }) {
  return (
    <div
      className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1 text-xs text-ink-500 dark:text-rice-400"
      style={{ left: `${x}%`, bottom: `${y}%` }}
    >
      <span className="h-2 w-2 rounded-full bg-bronze-500" />
      <span>{label}</span>
    </div>
  );
}

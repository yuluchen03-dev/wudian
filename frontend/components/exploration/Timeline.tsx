"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { History, User, BookOpen, ChevronDown } from "lucide-react";
import clsx from "clsx";
import type { TimelineEvent } from "@/lib/types";

interface TimelineProps {
  events: TimelineEvent[];
}

const CATEGORY_CONFIG = {
  history: { label: "历史事件", icon: History, color: "text-cinnabar-600", bg: "bg-cinnabar-50", dot: "bg-cinnabar-500" },
  person: { label: "人物生平", icon: User, color: "text-bronze-600", bg: "bg-rice-200", dot: "bg-bronze-500" },
  classic: { label: "经典成书", icon: BookOpen, color: "text-ink-600", bg: "bg-ink-100", dot: "bg-ink-500" },
} as const;

export default function Timeline({ events }: TimelineProps) {
  const [activeCategories, setActiveCategories] = useState<Set<string>>(
    new Set(["history", "person", "classic"])
  );
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredEvents = useMemo(() => {
    return events
      .filter((e) => activeCategories.has(e.category))
      .sort((a, b) => a.year - b.year);
  }, [events, activeCategories]);

  const toggleCategory = (cat: string) => {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) {
        if (next.size > 1) next.delete(cat);
      } else {
        next.add(cat);
      }
      return next;
    });
  };

  return (
    <div>
      {/* 筛选器 */}
      <div className="mb-6 flex flex-wrap gap-2">
        {(Object.keys(CATEGORY_CONFIG) as Array<keyof typeof CATEGORY_CONFIG>).map((cat) => {
          const config = CATEGORY_CONFIG[cat];
          const Icon = config.icon;
          const isActive = activeCategories.has(cat);
          return (
            <button
              key={cat}
              onClick={() => toggleCategory(cat)}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-all",
                isActive
                  ? clsx(config.bg, config.color, "shadow-scroll")
                  : "bg-ink-100 text-ink-300 hover:bg-ink-200"
              )}
            >
              <Icon size={14} />
              {config.label}
            </button>
          );
        })}
      </div>

      {/* 时间线 */}
      <div className="relative">
        {/* 竖线 */}
        <div className="absolute left-[7px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-cinnabar-300 via-bronze-300 to-ink-300 md:left-1/2 md:-translate-x-1/2" />

        <div className="space-y-4">
          {filteredEvents.map((event, index) => {
            const config = CATEGORY_CONFIG[event.category];
            const Icon = config.icon;
            const isExpanded = expandedId === event.id;
            const isLeft = index % 2 === 0;

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.03 }}
                className={clsx(
                  "relative flex items-start gap-4",
                  "md:items-center"
                )}
              >
                {/* 时间点 */}
                <div
                  className={clsx(
                    "relative z-10 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full ring-4 ring-rice-50 md:absolute md:left-1/2 md:-translate-x-1/2",
                    config.dot
                  )}
                />

                {/* 卡片 */}
                <div
                  className={clsx(
                    "flex-1 md:w-[calc(50%-2rem)]",
                    isLeft ? "md:ml-auto md:pl-8" : "md:mr-auto md:pr-8 md:text-right"
                  )}
                >
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : event.id)}
                    className={clsx(
                      "cursor-pointer rounded-lg border p-3 transition-all hover:shadow-popup",
                      isExpanded
                        ? "border-cinnabar-300 bg-white shadow-popup"
                        : "border-ink-100 bg-white/70 hover:bg-white"
                    )}
                  >
                    {/* 年份 */}
                    <div className={clsx("mb-1 flex items-center gap-2", isLeft ? "" : "md:flex-row-reverse")}>
                      <span className={clsx("font-serif text-sm font-bold", config.color)}>
                        {event.year_label}
                      </span>
                      <span className={clsx("flex items-center gap-1 rounded px-1.5 py-0.5 text-xs", config.bg, config.color)}>
                        <Icon size={10} />
                        {config.label}
                      </span>
                    </div>

                    {/* 标题 */}
                    <h4 className="font-serif text-base font-semibold text-ink-800">
                      {event.title}
                    </h4>

                    {/* 描述 */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <p className="mt-2 text-sm leading-relaxed text-ink-600">
                            {event.description}
                          </p>
                          {event.tags && event.tags.length > 0 && (
                            <div className={clsx("mt-2 flex flex-wrap gap-1", isLeft ? "" : "md:justify-end")}>
                              {event.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="rounded bg-rice-200 px-1.5 py-0.5 text-xs text-ink-500"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* 展开提示 */}
                    <div className={clsx("mt-1 flex items-center gap-1 text-xs text-ink-300", isLeft ? "" : "md:flex-row-reverse")}>
                      <ChevronDown
                        size={12}
                        className={clsx("transition-transform", isExpanded && "rotate-180")}
                      />
                      {isExpanded ? "收起" : "展开详情"}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {filteredEvents.length === 0 && (
        <div className="py-12 text-center text-ink-400">
          <p>暂无符合条件的事件</p>
        </div>
      )}
    </div>
  );
}

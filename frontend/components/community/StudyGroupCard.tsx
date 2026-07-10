"use client";

import { motion } from "framer-motion";
import { Users, Flame, Lock, BookOpen } from "lucide-react";
import clsx from "clsx";
import type { StudyGroup, GroupCategory } from "@/lib/types";

const categoryLabels: Record<GroupCategory, string> = {
  beginner: "入门共读",
  advanced: "进阶研读",
  theme: "主题共读",
  free: "自由共读",
};

const categoryColors: Record<GroupCategory, string> = {
  beginner: "bg-bronze-500/10 text-bronze-600",
  advanced: "bg-cinnabar-600/10 text-cinnabar-600",
  theme: "bg-ink-600/10 text-ink-600",
  free: "bg-rice-400/20 text-rice-700",
};

interface StudyGroupCardProps {
  group: StudyGroup;
  onJoin?: (groupId: number) => void;
  onCheckin?: (groupId: number) => void;
  joined?: boolean;
  index?: number;
}

export default function StudyGroupCard({
  group,
  onJoin,
  onCheckin,
  joined = false,
  index = 0,
}: StudyGroupCardProps) {
  const checkinRate = group.memberCount > 0
    ? Math.round((group.todayCheckinCount / group.memberCount) * 100)
    : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index }}
      className="paper-card flex flex-col p-5 transition-all hover:-translate-y-0.5 hover:shadow-popup"
    >
      {/* 头部 */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-2">
            <h3 className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-50">
              {group.name}
            </h3>
            {group.isPrivate && (
              <Lock size={14} className="text-ink-400" />
            )}
          </div>
          <span
            className={clsx(
              "inline-block rounded px-2 py-0.5 text-xs font-medium",
              categoryColors[group.category]
            )}
          >
            {categoryLabels[group.category]}
          </span>
        </div>
      </div>

      {/* 描述 */}
      <p className="mb-4 line-clamp-2 flex-1 text-sm leading-relaxed text-ink-500 dark:text-rice-300">
        {group.description}
      </p>

      {/* 统计信息 */}
      <div className="mb-4 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-md bg-rice-100 py-2 dark:bg-ink-700">
          <div className="flex items-center justify-center gap-1 font-serif text-lg font-bold text-ink-700 dark:text-rice-200">
            <Users size={14} className="text-bronze-500" />
            {group.memberCount}
          </div>
          <div className="text-[10px] text-ink-400">成员</div>
        </div>
        <div className="rounded-md bg-rice-100 py-2 dark:bg-ink-700">
          <div className="flex items-center justify-center gap-1 font-serif text-lg font-bold text-cinnabar-600">
            <Flame size={14} />
            {group.todayCheckinCount}
          </div>
          <div className="text-[10px] text-ink-400">今日打卡</div>
        </div>
        <div className="rounded-md bg-rice-100 py-2 dark:bg-ink-700">
          <div className="font-serif text-lg font-bold text-bronze-500">
            {checkinRate}%
          </div>
          <div className="text-[10px] text-ink-400">活跃度</div>
        </div>
      </div>

      {/* 组长 */}
      <div className="mb-3 flex items-center gap-2 text-xs text-ink-400">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cinnabar-600 font-serif text-xs font-bold text-rice-50">
          {group.ownerName[0]}
        </span>
        <span>组长 · {group.ownerName}</span>
        {group.bookId && (
          <span className="ml-auto flex items-center gap-1">
            <BookOpen size={12} /> {group.bookId}
          </span>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        {joined ? (
          <button
            onClick={() => onCheckin?.(group.id)}
            className="seal-btn flex-1 text-sm"
          >
            今日打卡
          </button>
        ) : (
          <button
            onClick={() => onJoin?.(group.id)}
            disabled={group.memberCount >= group.maxMembers}
            className="seal-btn flex-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {group.memberCount >= group.maxMembers ? "已满员" : "加入小组"}
          </button>
        )}
      </div>
    </motion.div>
  );
}

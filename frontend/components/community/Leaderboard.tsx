"use client";

import { motion } from "framer-motion";
import { Trophy, Crown, Medal, ArrowUp } from "lucide-react";
import clsx from "clsx";
import type { LeaderboardData, LeaderboardEntry } from "@/lib/types";

interface LeaderboardProps {
  data: LeaderboardData;
  scope: "week" | "month" | "all";
  metric: string;
  onScopeChange?: (scope: "week" | "month" | "all") => void;
  onMetricChange?: (metric: string) => void;
}

const scopeLabels: Record<string, string> = {
  week: "周榜",
  month: "月榜",
  all: "总榜",
};

const metricLabels: Record<string, string> = {
  exp: "经验值",
  checkin: "打卡天数",
  pk_rating: "PK段位",
};

export default function Leaderboard({
  data,
  scope,
  metric,
  onScopeChange,
  onMetricChange,
}: LeaderboardProps) {
  return (
    <div className="paper-card overflow-hidden">
      {/* 标题 */}
      <div className="flex items-center gap-2 border-b border-ink-100 px-5 py-4 dark:border-ink-600">
        <Trophy size={20} className="text-cinnabar-600" />
        <h3 className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-50">
          学友排行榜
        </h3>
      </div>

      {/* 筛选器 */}
      <div className="flex items-center justify-between gap-2 px-5 py-3">
        {/* 范围切换 */}
        <div className="flex gap-1 rounded-md bg-rice-100 p-0.5 dark:bg-ink-700">
          {(["week", "month", "all"] as const).map((s) => (
            <button
              key={s}
              onClick={() => onScopeChange?.(s)}
              className={clsx(
                "rounded px-3 py-1 text-xs font-medium transition-colors",
                scope === s
                  ? "bg-cinnabar-600 text-rice-50"
                  : "text-ink-500 hover:text-ink-700 dark:text-rice-300"
              )}
            >
              {scopeLabels[s]}
            </button>
          ))}
        </div>

        {/* 指标切换 */}
        <div className="flex gap-1 rounded-md bg-rice-100 p-0.5 dark:bg-ink-700">
          {(["exp", "checkin", "pk_rating"] as const).map((m) => (
            <button
              key={m}
              onClick={() => onMetricChange?.(m)}
              className={clsx(
                "rounded px-3 py-1 text-xs font-medium transition-colors",
                metric === m
                  ? "bg-bronze-500 text-rice-50"
                  : "text-ink-500 hover:text-ink-700 dark:text-rice-300"
              )}
            >
              {metricLabels[m]}
            </button>
          ))}
        </div>
      </div>

      {/* 我的排名 */}
      {data.myRank && (
        <div className="mx-5 mb-3 flex items-center justify-between rounded-md bg-cinnabar-600/10 px-4 py-2">
          <span className="text-sm font-medium text-cinnabar-700 dark:text-cinnabar-300">
            我的排名：第 {data.myRank} 名
          </span>
          <span className="text-sm text-cinnabar-600">
            {data.myScore} {data.entries[0]?.scoreLabel || ""}
          </span>
        </div>
      )}

      {/* 排行榜列表 */}
      <div className="max-h-[500px] overflow-y-auto px-5 pb-4">
        {data.entries.map((entry, i) => (
          <RankRow key={entry.userId} entry={entry} index={i} />
        ))}
      </div>
    </div>
  );
}

function RankRow({ entry, index }: { entry: LeaderboardEntry; index: number }) {
  const isTop3 = entry.rank <= 3;
  const isMe = entry.rank === 7; // 模拟当前用户

  const rankIcon = () => {
    if (entry.rank === 1)
      return <Crown size={18} className="text-yellow-500" />;
    if (entry.rank === 2)
      return <Medal size={18} className="text-gray-400" />;
    if (entry.rank === 3)
      return <Medal size={18} className="text-amber-600" />;
    return (
      <span className="font-serif text-sm font-bold text-ink-400">
        {entry.rank}
      </span>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.03 * index }}
      className={clsx(
        "flex items-center gap-3 rounded-md px-3 py-2.5 transition-colors",
        isMe && "bg-cinnabar-600/5",
        isTop3 && "bg-rice-100/50 dark:bg-ink-700/50"
      )}
    >
      {/* 排名 */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center">
        {rankIcon()}
      </div>

      {/* 头像 + 名称 */}
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink-600 font-serif text-sm font-bold text-rice-50">
        {entry.nickname?.[0] || entry.username[0]}
      </span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-serif text-sm font-medium text-ink-800 dark:text-rice-50">
            {entry.nickname || entry.username}
          </span>
          <span className="rounded bg-bronze-500/10 px-1 py-0.5 text-[10px] text-bronze-600">
            Lv.{entry.level}
          </span>
          {entry.extra && (
            <span className="text-[10px] text-cinnabar-500">{entry.extra}</span>
          )}
        </div>
      </div>

      {/* 分数 */}
      <div className="text-right">
        <div className="font-serif text-base font-bold text-cinnabar-600">
          {entry.score}
        </div>
        <div className="text-[10px] text-ink-400">{entry.scoreLabel}</div>
      </div>
    </motion.div>
  );
}

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Award,
  BookOpen,
  Calendar,
  CheckCircle,
  ChevronLeft,
  Crown,
  Feather,
  Flame,
  GraduationCap,
  Library,
  Lock,
  MessageCircle,
  RefreshCw,
  Sword,
  Trophy,
  Star,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import type {
  AchievementsResponse,
  RankInfo,
  LeaderboardData,
  Achievement,
} from "@/lib/types";

type Tab = "achievements" | "leaderboard";

// 段位名称映射
const RANK_NAMES = ["童生", "秀才", "举人", "进士", "翰林"];
const RANK_COLORS = [
  "from-ink-300 to-ink-400",
  "from-bronze-400 to-bronze-600",
  "from-cinnabar-400 to-cinnabar-600",
  "from-amber-400 to-amber-600",
  "from-purple-400 to-purple-600",
];

// 成就图标映射
const ICON_MAP: Record<string, typeof Award> = {
  BookOpen,
  Flame,
  Sword,
  RefreshCw,
  Calendar,
  GraduationCap,
  Crown,
  Feather,
  MessageCircle,
  Library,
};

export default function AchievementsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("achievements");
  const [achievements, setAchievements] = useState<AchievementsResponse | null>(null);
  const [rank, setRank] = useState<RankInfo | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
  const [lbScope, setLbScope] = useState<"week" | "month" | "all">("week");
  const [loading, setLoading] = useState(true);

  // 加载成就和段位
  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }
    Promise.all([api.getAchievements(), api.getRank()])
      .then(([ach, rk]) => {
        setAchievements(ach);
        setRank(rk);
      })
      .finally(() => setLoading(false));
  }, [router]);

  // 加载排行榜
  const loadLeaderboard = useCallback((scope: "week" | "month" | "all") => {
    setLbScope(scope);
    api.getLearningLeaderboard(scope).then(setLeaderboard);
  }, []);

  useEffect(() => {
    if (tab === "leaderboard" && !leaderboard) {
      loadLeaderboard("week");
    }
  }, [tab, leaderboard, loadLeaderboard]);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在加载成就……</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      {/* 标题 */}
      <div className="mb-6 text-center">
        <h1 className="font-serif text-3xl font-bold text-ink-800">成就与段位</h1>
        <p className="mt-2 text-ink-500">积学储宝，酌理富才，见证书山学海之进益</p>
      </div>

      {/* 段位卡片 */}
      {rank && <RankCard rank={rank} />}

      {/* Tab 切换 */}
      <div className="mt-8 flex justify-center">
        <div className="inline-flex rounded-lg border border-ink-200 bg-white p-1">
          <TabButton active={tab === "achievements"} onClick={() => setTab("achievements")}>
            <Award size={16} />
            成就徽章
          </TabButton>
          <TabButton active={tab === "leaderboard"} onClick={() => setTab("leaderboard")}>
            <Trophy size={16} />
            排行榜
          </TabButton>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {tab === "achievements" && achievements && (
          <motion.div
            key="achievements"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6"
          >
            <AchievementGrid achievements={achievements} />
          </motion.div>
        )}

        {tab === "leaderboard" && (
          <motion.div
            key="leaderboard"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6"
          >
            <LeaderboardView
              data={leaderboard}
              scope={lbScope}
              onScopeChange={loadLeaderboard}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** 段位卡片 */
function RankCard({ rank }: { rank: RankInfo }) {
  const rankIdx = Math.max(0, Math.min(RANK_NAMES.length - 1, rank.current_rank - 1));
  const progressPercent = Math.round(rank.progress * 100);
  const expToNext = rank.next_rank
    ? `${rank.exp} / ${Math.round(rank.exp / (rank.progress || 1))} EXP`
    : `${rank.exp} EXP`;

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-100 bg-white shadow-scroll">
      <div className={`bg-gradient-to-r ${RANK_COLORS[rankIdx]} p-6 sm:p-8`}>
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm">
              <Crown size={32} className="text-white" />
            </div>
            <div className="text-white">
              <div className="text-sm opacity-80">当前段位</div>
              <div className="font-serif text-3xl font-bold">
                {rank.rank_name}
              </div>
              <div className="mt-1 text-sm opacity-90">
                Lv.{rank.current_rank} · {rank.exp} EXP
              </div>
            </div>
          </div>
          {rank.next_rank && (
            <div className="text-right text-white">
              <div className="text-sm opacity-80">下一段位</div>
              <div className="font-serif text-xl font-bold">
                {rank.next_rank_name}
              </div>
            </div>
          )}
        </div>
      </div>
      <div className="p-6">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-ink-500">晋升进度</span>
          <span className="font-medium text-ink-700">{progressPercent}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-ink-100">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            className="h-full rounded-full bg-gradient-to-r from-cinnabar-400 to-cinnabar-600"
            transition={{ duration: 0.6, delay: 0.2 }}
          />
        </div>
        <div className="mt-2 text-xs text-ink-400">{expToNext}</div>
      </div>
    </div>
  );
}

/** Tab 按钮 */
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-cinnabar-600 text-white"
          : "text-ink-600 hover:bg-ink-50"
      }`}
    >
      {children}
    </button>
  );
}

/** 成就徽章网格 */
function AchievementGrid({
  achievements,
}: {
  achievements: AchievementsResponse;
}) {
  const { unlocked, locked } = achievements;

  return (
    <div>
      {/* 已解锁 */}
      {unlocked.length > 0 && (
        <div className="mb-8">
          <h3 className="mb-4 flex items-center gap-2 font-serif text-lg font-bold text-ink-800">
            <CheckCircle size={20} className="text-green-600" />
            已解锁 ({unlocked.length})
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {unlocked.map((ach, i) => (
              <AchievementBadge key={ach.id} achievement={ach} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* 未解锁 */}
      {locked.length > 0 && (
        <div>
          <h3 className="mb-4 flex items-center gap-2 font-serif text-lg font-bold text-ink-800">
            <Lock size={20} className="text-ink-400" />
            待解锁 ({locked.length})
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {locked.map((ach, i) => (
              <AchievementBadge key={ach.id} achievement={ach} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/** 单个成就徽章 */
function AchievementBadge({
  achievement,
  index,
}: {
  achievement: Achievement;
  index: number;
}) {
  const Icon = ICON_MAP[achievement.icon] || Award;
  const unlocked = achievement.unlocked;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      className={`relative rounded-xl border p-4 text-center transition-shadow ${
        unlocked
          ? "border-cinnabar-200 bg-gradient-to-b from-rice-50 to-white shadow-scroll hover:shadow-popup"
          : "border-ink-100 bg-ink-50/50"
      }`}
    >
      <div
        className={`mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full ${
          unlocked
            ? "bg-cinnabar-100 text-cinnabar-600"
            : "bg-ink-200 text-ink-400"
        }`}
      >
        {unlocked ? <Icon size={28} /> : <Lock size={24} />}
      </div>
      <div
        className={`font-serif text-sm font-bold ${
          unlocked ? "text-ink-800" : "text-ink-500"
        }`}
      >
        {achievement.name}
      </div>
      <div className="mt-1 text-xs text-ink-400">
        {unlocked ? achievement.description : achievement.condition}
      </div>
      {unlocked && achievement.unlocked_at && (
        <div className="mt-2 text-[10px] text-cinnabar-600">
          {new Date(achievement.unlocked_at).toLocaleDateString("zh-CN")}
        </div>
      )}
    </motion.div>
  );
}

/** 排行榜视图 */
function LeaderboardView({
  data,
  scope,
  onScopeChange,
}: {
  data: LeaderboardData | null;
  scope: "week" | "month" | "all";
  onScopeChange: (scope: "week" | "month" | "all") => void;
}) {
  const scopes: { key: "week" | "month" | "all"; label: string }[] = [
    { key: "week", label: "周榜" },
    { key: "month", label: "月榜" },
    { key: "all", label: "总榜" },
  ];

  return (
    <div>
      {/* 榜单切换 */}
      <div className="mb-4 flex justify-center">
        <div className="inline-flex rounded-lg border border-ink-200 bg-white p-1">
          {scopes.map((s) => (
            <button
              key={s.key}
              onClick={() => onScopeChange(s.key)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                scope === s.key
                  ? "bg-cinnabar-600 text-white"
                  : "text-ink-600 hover:bg-ink-50"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-ink-100 bg-white p-2 shadow-scroll sm:p-4">
        {!data || data.entries.length === 0 ? (
          <div className="py-12 text-center text-ink-400">暂无排行数据</div>
        ) : (
          <>
            {/* 我的名次 */}
            {data.myRank && (
              <div className="mb-3 flex items-center justify-center gap-2 rounded-lg bg-rice-100 px-4 py-2 text-sm">
                <Star size={16} className="text-cinnabar-600" />
                <span className="text-ink-600">我的名次：</span>
                <span className="font-bold text-cinnabar-600">第 {data.myRank} 名</span>
                <span className="text-ink-400">·</span>
                <span className="text-ink-600">{data.myScore} EXP</span>
              </div>
            )}

            {/* 排行列表 */}
            <div className="space-y-1">
              {data.entries.map((entry, i) => (
                <LeaderboardRow key={entry.userId} entry={entry} isTop3={i < 3} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/** 排行榜单行 */
function LeaderboardRow({
  entry,
  isTop3,
}: {
  entry: LeaderboardData["entries"][number];
  isTop3: boolean;
}) {
  const medalColors = ["text-amber-500", "text-ink-400", "text-bronze-600"];
  const bgColors = ["bg-amber-50", "bg-ink-50", "bg-rice-50"];

  return (
    <div
      className={`flex items-center gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-rice-50 ${
        isTop3 ? bgColors[entry.rank - 1] : ""
      }`}
    >
      {/* 排名 */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center">
        {isTop3 ? (
          <Trophy size={20} className={medalColors[entry.rank - 1]} />
        ) : (
          <span className="text-sm font-bold text-ink-400">{entry.rank}</span>
        )}
      </div>

      {/* 用户信息 */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-cinnabar-100 font-serif text-lg font-bold text-cinnabar-700">
        {(entry.nickname || entry.username).charAt(0)}
      </div>
      <div className="flex-1">
        <div className="font-medium text-ink-800">
          {entry.nickname || entry.username}
        </div>
        <div className="flex items-center gap-2 text-xs text-ink-400">
          <span>Lv.{entry.level}</span>
          {entry.extra && <span>· {entry.extra}</span>}
        </div>
      </div>

      {/* 分数 */}
      <div className="text-right">
        <div className="font-serif text-lg font-bold text-cinnabar-600">
          {entry.score}
        </div>
        <div className="text-[10px] text-ink-400">EXP</div>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, FileText, Swords, Trophy } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import clsx from "clsx";
import StudyGroupCard from "@/components/community/StudyGroupCard";
import NoteCard from "@/components/community/NoteCard";
import Leaderboard from "@/components/community/Leaderboard";
import PKArena from "@/components/community/PKArena";
import { api } from "@/lib/api";
import type { StudyGroup, Note, LeaderboardData, PKMatchResult, PKSettlement } from "@/lib/types";

type Tab = "groups" | "notes" | "pk" | "leaderboard";

const tabs: { key: Tab; label: string; icon: typeof Users }[] = [
  { key: "groups", label: "共读小组", icon: Users },
  { key: "notes", label: "学友笔记", icon: FileText },
  { key: "pk", label: "PK竞技", icon: Swords },
  { key: "leaderboard", label: "排行榜", icon: Trophy },
];

export default function CommunityPage() {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<Tab>("groups");
  const [groups, setGroups] = useState<StudyGroup[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
  const [lbScope, setLbScope] = useState<"week" | "month" | "all">("week");
  const [lbMetric, setLbMetric] = useState("exp");
  const [joinedGroups, setJoinedGroups] = useState<Set<number>>(new Set([1]));
  const [noteSort, setNoteSort] = useState<"latest" | "hottest" | "essence">("latest");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeTab === "leaderboard" && !leaderboard) {
      api.getLeaderboard(lbScope, lbMetric).then(setLeaderboard);
    }
  }, [activeTab, lbScope, lbMetric, leaderboard]);

  const loadData = async () => {
    setLoading(true);
    const [g, n] = await Promise.all([
      api.getGroups(),
      api.getNotes(),
    ]);
    setGroups(g);
    setNotes(n);
    setLoading(false);
  };

  const handleJoin = (groupId: number) => {
    api.joinGroup(groupId).then(() => {
      setJoinedGroups((prev) => new Set(prev).add(groupId));
      setGroups((prev) =>
        prev.map((g) =>
          g.id === groupId
            ? { ...g, memberCount: g.memberCount + 1 }
            : g
        )
      );
      toast("已加入小组，一起共读经典！");
    });
  };

  const handleCheckin = (groupId: number) => {
    api.checkinGroup(groupId).then(() => {
      setGroups((prev) =>
        prev.map((g) =>
          g.id === groupId
            ? { ...g, todayCheckinCount: g.todayCheckinCount + 1 }
            : g
        )
      );
      toast("打卡成功！继续保持每日学习的好习惯 💪");
    });
  };

  const handleLike = (noteId: number) => {
    api.likeNote(noteId);
  };

  const handleComment = (noteId: number, content: string) => {
    api.commentNote(noteId, content).then(() => {
      setNotes((prev) =>
        prev.map((n) =>
          n.id === noteId ? { ...n, commentCount: n.commentCount + 1 } : n
        )
      );
    });
  };

  const handlePKMatch = async (): Promise<PKMatchResult> => {
    return api.pkMatch();
  };

  const handlePKSubmit = async (
    pkId: string,
    answers: { questionIndex: number; selectedOption: number }[]
  ): Promise<PKSettlement> => {
    return api.pkSubmit(pkId, answers);
  };

  const handleLoadLeaderboard = (scope: "week" | "month" | "all", metric: string) => {
    setLbScope(scope);
    setLbMetric(metric);
    setLeaderboard(null);
    api.getLeaderboard(scope, metric).then(setLeaderboard);
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="font-serif text-lg text-ink-400">正在加载社区...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="font-serif text-3xl font-bold text-ink-800 dark:text-rice-50">
          学友社区
        </h1>
        <p className="mt-2 text-sm text-ink-500 dark:text-rice-300">
          共读经典 · 交流心得 · 切磋竞技
        </p>
        <div className="classical-divider mx-auto mt-4 w-32" />
      </motion.div>

      {/* 标签栏 */}
      <div className="sticky top-16 z-30 flex justify-center gap-1 rounded-lg bg-rice-50/90 p-1 backdrop-blur-md dark:bg-ink-800/90">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                "flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-colors",
                activeTab === tab.key
                  ? "bg-cinnabar-600 text-rice-50"
                  : "text-ink-600 hover:bg-ink-100 dark:text-rice-300 dark:hover:bg-ink-700"
              )}
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 内容区 */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* 共读小组 */}
        {activeTab === "groups" && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {groups.map((group, i) => (
              <StudyGroupCard
                key={group.id}
                group={group}
                index={i}
                joined={joinedGroups.has(group.id)}
                onJoin={handleJoin}
                onCheckin={handleCheckin}
              />
            ))}
          </div>
        )}

        {/* 学友笔记 */}
        {activeTab === "notes" && (
          <div>
            {/* 排序 */}
            <div className="mb-4 flex justify-end gap-1 rounded-md bg-rice-100 p-0.5 dark:bg-ink-700">
              {([
                { key: "latest", label: "最新" },
                { key: "hottest", label: "最热" },
                { key: "essence", label: "精选" },
              ] as const).map((s) => (
                <button
                  key={s.key}
                  onClick={() => setNoteSort(s.key)}
                  className={clsx(
                    "rounded px-3 py-1 text-xs font-medium transition-colors",
                    noteSort === s.key
                      ? "bg-cinnabar-600 text-rice-50"
                      : "text-ink-500 hover:text-ink-700 dark:text-rice-300"
                  )}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {notes
                .filter((n) => (noteSort === "essence" ? n.isEssence : true))
                .sort((a, b) => {
                  if (noteSort === "hottest") return b.likeCount - a.likeCount;
                  return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
                })
                .map((note, i) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    index={i}
                    onLike={handleLike}
                    onComment={handleComment}
                  />
                ))}
            </div>
          </div>
        )}

        {/* PK 竞技 */}
        {activeTab === "pk" && (
          <div className="mx-auto max-w-2xl">
            <PKArena onMatch={handlePKMatch} onSubmit={handlePKSubmit} />
          </div>
        )}

        {/* 排行榜 */}
        {activeTab === "leaderboard" && leaderboard && (
          <div className="mx-auto max-w-2xl">
            <Leaderboard
              data={leaderboard}
              scope={lbScope}
              metric={lbMetric}
              onScopeChange={(s) => handleLoadLeaderboard(s, lbMetric)}
              onMetricChange={(m) => handleLoadLeaderboard(lbScope, m)}
            />
          </div>
        )}
      </motion.div>
    </div>
  );
}

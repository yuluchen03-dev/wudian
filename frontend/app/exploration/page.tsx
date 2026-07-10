"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Network, Clock, Search } from "lucide-react";
import clsx from "clsx";
import KnowledgeGraph from "@/components/exploration/KnowledgeGraph";
import Timeline from "@/components/exploration/Timeline";
import IdiomSearch from "@/components/exploration/IdiomSearch";
import { api } from "@/lib/api";
import type { GraphData, TimelineEvent, Idiom } from "@/lib/types";

type Tab = "graph" | "timeline" | "idiom";

const TABS: { id: Tab; label: string; icon: typeof Network }[] = [
  { id: "graph", label: "知识图谱", icon: Network },
  { id: "timeline", label: "思想时间线", icon: Clock },
  { id: "idiom", label: "典故溯源", icon: Search },
];

const GRAPH_TYPES: { id: "disciples" | "lineage" | "all"; label: string; desc: string }[] = [
  { id: "disciples", label: "弟子关系", desc: "孔子与孔门十哲" },
  { id: "lineage", label: "思想传承", desc: "孔子→孟子→朱子" },
  { id: "all", label: "完整图谱", desc: "人物+概念全景" },
];

export default function ExplorationPage() {
  const [activeTab, setActiveTab] = useState<Tab>("graph");
  const [graphType, setGraphType] = useState<"disciples" | "lineage" | "all">("disciples");
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [idioms, setIdioms] = useState<Idiom[]>([]);
  const [loading, setLoading] = useState(true);

  // 加载知识图谱
  const loadGraph = useCallback(async (type: "disciples" | "lineage" | "all") => {
    setLoading(true);
    try {
      const res = await api.getGraph(type);
      setGraphData(res.graph);
    } catch (err) {
      console.error("加载图谱失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载时间线
  const loadTimeline = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getTimeline();
      setTimelineEvents(res.events);
    } catch (err) {
      console.error("加载时间线失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载成语
  const loadIdioms = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getIdioms();
      setIdioms(res.idioms);
    } catch (err) {
      console.error("加载成语失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadGraph(graphType);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 切换图谱类型
  const handleGraphTypeChange = (type: "disciples" | "lineage" | "all") => {
    setGraphType(type);
    loadGraph(type);
  };

  // 切换 Tab
  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    if (tab === "graph" && graphData.nodes.length === 0) {
      loadGraph(graphType);
    } else if (tab === "timeline" && timelineEvents.length === 0) {
      loadTimeline();
    } else if (tab === "idiom" && idioms.length === 0) {
      loadIdioms();
    }
  };

  return (
    <div className="animate-fade-in">
      {/* 页头 */}
      <div className="mb-6 text-center">
        <h1 className="font-serif text-3xl font-bold text-ink-800">
          互动探索
        </h1>
        <p className="mt-2 text-sm text-ink-400">
          漫游知识图谱 · 追溯思想脉络 · 探寻典故源流
        </p>
        <div className="mx-auto mt-3 h-px w-32 bg-gradient-to-r from-transparent via-cinnabar-400 to-transparent" />
      </div>

      {/* Tab 切换 */}
      <div className="mb-6 flex justify-center">
        <div className="inline-flex rounded-lg bg-rice-100 p-1 shadow-scroll">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={clsx(
                  "flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-all",
                  activeTab === tab.id
                    ? "bg-cinnabar-600 text-rice-50 shadow-scroll"
                    : "text-ink-500 hover:text-ink-700"
                )}
              >
                <Icon size={16} />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 内容区 */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* 知识图谱 */}
        {activeTab === "graph" && (
          <div>
            {/* 图谱类型选择 */}
            <div className="mb-4 flex flex-wrap justify-center gap-2">
              {GRAPH_TYPES.map((gt) => (
                <button
                  key={gt.id}
                  onClick={() => handleGraphTypeChange(gt.id)}
                  className={clsx(
                    "rounded-lg px-3 py-1.5 text-sm transition-all",
                    graphType === gt.id
                      ? "bg-ink-700 text-rice-50 shadow-scroll"
                      : "bg-white/70 text-ink-500 hover:bg-white hover:text-ink-700"
                  )}
                >
                  <span className="font-medium">{gt.label}</span>
                  <span className="ml-1.5 text-xs opacity-60">{gt.desc}</span>
                </button>
              ))}
            </div>

            {loading ? (
              <LoadingState text="正在构建知识图谱..." />
            ) : (
              <KnowledgeGraph nodes={graphData.nodes} edges={graphData.edges} />
            )}

            <p className="mt-3 text-center text-xs text-ink-400">
              点击节点查看详情 · 拖拽节点调整位置 · 滚轮缩放 · 双指触控支持
            </p>
          </div>
        )}

        {/* 时间线 */}
        {activeTab === "timeline" && (
          <div>
            {loading ? (
              <LoadingState text="正在梳理历史脉络..." />
            ) : (
              <Timeline events={timelineEvents} />
            )}
          </div>
        )}

        {/* 典故溯源 */}
        {activeTab === "idiom" && (
          <div>
            {loading ? (
              <LoadingState text="正在汇集经典成语..." />
            ) : (
              <IdiomSearch idioms={idioms} />
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}

/** 加载状态 */
function LoadingState({ text }: { text: string }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-cinnabar-200 border-t-cinnabar-600" />
      <p className="mt-3 text-sm text-ink-400">{text}</p>
    </div>
  );
}

"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Circle, GitBranch, RadioTower } from "lucide-react";
import clsx from "clsx";
import type { DebateStateGraphView } from "@/lib/roundtableFlow";

interface ModeratorStateGraphProps {
  graph: DebateStateGraphView | null;
}

const nodeFallback: Record<string, string> = {
  init: "开场",
  round1: "陈述",
  round2: "交锋",
  intervention: "介入",
  report: "会诊",
  done: "收束",
};

export default function ModeratorStateGraph({ graph }: ModeratorStateGraphProps) {
  const nodes = graph?.nodes ?? [];
  const traceKeys = new Set((graph?.trace ?? []).map((step) => `${step.fromNode}->${step.toNode}`));

  return (
    <section className="relative overflow-hidden rounded-lg border border-[#6f4e2f]/40 bg-[#1c1714]/88 px-4 py-4 shadow-[0_18px_60px_rgba(0,0,0,0.35)]">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#d9a441] to-transparent" />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-[#d9a441]/45 bg-[#2b2118] text-[#f4cf7a]">
          <RadioTower size={17} />
        </span>
        <div>
          <h2 className="font-serif text-base font-semibold text-[#f8edd2]">主持 Agent 状态图</h2>
          <p className="text-xs text-[#c7b38b]">current: {graph?.currentNode ?? "init"}</p>
        </div>
        <span className="ml-auto inline-flex items-center gap-1.5 rounded-md border border-[#4d7255]/50 bg-[#203326]/80 px-2.5 py-1 text-xs text-[#b9e2b7]">
          <GitBranch size={13} />
          {graph?.trace.length ?? 0} steps
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-[1fr_220px]">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {nodes.map((node, index) => {
            const isCurrent = node.id === graph?.currentNode;
            const entered = index === 0 || (graph?.trace ?? []).some((step) => step.toNode === node.id);
            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className={clsx(
                  "relative min-h-20 rounded-md border px-3 py-3",
                  isCurrent
                    ? "border-[#f2c15d] bg-[#3b2a18] shadow-[0_0_24px_rgba(242,193,93,0.22)]"
                    : entered
                      ? "border-[#4d7255]/60 bg-[#1d2a20]"
                      : "border-[#5b5042]/50 bg-[#181512]"
                )}
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-[0.16em] text-[#a08b67]">{node.kind}</span>
                  {entered ? <CheckCircle2 size={13} className="text-[#9bd18f]" /> : <Circle size={13} className="text-[#806f56]" />}
                </div>
                <div className="font-serif text-sm text-[#f8edd2]">{node.label || nodeFallback[node.id] || node.id}</div>
              </motion.div>
            );
          })}
        </div>

        <div className="rounded-md border border-[#5b5042]/50 bg-black/20 p-3">
          <div className="mb-2 text-xs uppercase tracking-[0.14em] text-[#a08b67]">transitions</div>
          <div className="space-y-1.5">
            {(graph?.transitions ?? []).slice(0, 6).map((edge) => {
              const hot = traceKeys.has(`${edge.fromNode}->${edge.toNode}`);
              return (
                <div key={`${edge.fromNode}-${edge.toNode}-${edge.action}`} className="flex items-center gap-2 text-xs">
                  <span className={clsx("h-1.5 w-1.5 rounded-full", hot ? "bg-[#f2c15d]" : "bg-[#5b5042]")} />
                  <span className="text-[#f8edd2]">{edge.fromNode}</span>
                  <span className="text-[#8c785f]">→</span>
                  <span className="text-[#f8edd2]">{edge.toNode}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

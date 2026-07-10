"use client";

import { motion } from "framer-motion";
import { FileText, ArrowRight } from "lucide-react";
import clsx from "clsx";
import type { Sage } from "@/lib/types";
import type { SageRoundSpeech, DebateClash } from "@/lib/roundtableData";
import type { DebateReportView } from "@/lib/roundtableFlow";
import { SealStamp } from "@/components/ui/ChineseDecor";

interface DebateSummaryProps {
  topic: string;
  sages: Sage[];
  speeches: SageRoundSpeech[];
  clashes: DebateClash[];
  report?: DebateReportView | null;
  onNewTopic: () => void;
}

/**
 * 百家论道 - 会诊报告 / 论道总结
 * 所有圣贤发言完成后展示
 */
export default function DebateSummary({ topic, sages, speeches, clashes, report, onNewTopic }: DebateSummaryProps) {
  const sageNames = Object.fromEntries(sages.map((s) => [s.id, s.name]));
  const totalCitations = speeches.reduce((acc, s) => acc + s.citations.length, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="mx-auto max-w-3xl"
    >
      <div className="overflow-hidden rounded-xl border border-ink-100 bg-white shadow-scroll dark:border-ink-600 dark:bg-ink-700">
        {/* Header */}
        <div className="border-b border-ink-100 bg-gradient-to-r from-rice-100/80 to-rice-50/60 px-6 py-4 dark:border-ink-600 dark:from-ink-700/60 dark:to-ink-700/40">
          <div className="flex items-center gap-3">
            <SealStamp variant="ink" size="sm">会诊报告</SealStamp>
            <span className="font-serif text-sm text-ink-500 dark:text-rice-400">论道总结</span>
          </div>
        </div>

        {/* Body */}
        <div className="space-y-4 px-6 py-5">
          {/* Topic */}
          <div>
            <div className="text-xs text-ink-400 dark:text-rice-500">话题</div>
            <div className="font-serif text-lg font-semibold text-ink-800 dark:text-rice-100">{topic}</div>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-4">
            <StatBadge label="参与圣贤" value={`${sages.length} 位`} />
            <StatBadge label="引用原文" value={`${totalCitations} 段`} />
            <StatBadge label="观点交锋" value={`${clashes.length} 处`} />
          </div>

          {report && (
            <div className="space-y-4">
              <ReportSection title="他们的共识" items={report.consensus} />
              <ReportSection title="根本分歧" items={report.divergences} />
              {report.recommendations.length > 0 && (
                <div>
                  <div className="mb-2 text-xs font-medium text-ink-500 dark:text-rice-400">各自建议</div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {report.recommendations.map((item, idx) => (
                      <div
                        key={`${item.sage}-${idx}`}
                        className="rounded-lg border border-ink-100 bg-rice-50/70 px-3 py-2 dark:border-ink-600 dark:bg-ink-800/50"
                      >
                        <div className="font-serif text-sm font-semibold text-cinnabar-700 dark:text-cinnabar-300">
                          {item.sage}
                        </div>
                        <p className="mt-1 text-sm leading-relaxed text-ink-600 dark:text-rice-300">
                          {item.recommendation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {report.summary && (
                <div className="rounded-lg border-l-4 border-cinnabar-600 bg-rice-50 px-4 py-3 dark:bg-ink-800/60">
                  <div className="mb-1 text-xs font-medium text-cinnabar-700 dark:text-cinnabar-300">主持收束</div>
                  <p className="font-kai text-sm leading-loose text-ink-700 dark:text-rice-200">{report.summary}</p>
                </div>
              )}
            </div>
          )}

          {/* Clash summary */}
          {clashes.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-medium text-ink-500 dark:text-rice-400">观点关系</div>
              <div className="space-y-1.5">
                {clashes.map((clash, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-ink-600 dark:text-rice-300">
                    <ArrowRight size={12} className="text-bronze-500" />
                    <span className="font-medium">{sageNames[clash.fromSageId] || clash.fromSageId}</span>
                    <span className="text-ink-400 dark:text-rice-500">{clash.summary}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-ink-100 px-6 py-4 dark:border-ink-600">
          <button
            onClick={onNewTopic}
            className={clsx(
              "flex items-center gap-2 rounded-lg bg-cinnabar-600 px-5 py-2.5 font-serif text-sm font-medium text-rice-50 shadow-scroll-soft transition-all",
              "hover:bg-cinnabar-700 hover:shadow-scroll"
            )}
          >
            <FileText size={14} />
            选择新话题，再论一场
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function ReportSection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <div className="mb-2 text-xs font-medium text-ink-500 dark:text-rice-400">{title}</div>
      <div className="space-y-1.5">
        {items.map((item, idx) => (
          <div key={idx} className="flex gap-2 text-sm leading-relaxed text-ink-600 dark:text-rice-300">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-bronze-500" />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-ink-100 bg-rice-50/80 px-4 py-2 dark:border-ink-600 dark:bg-ink-700/60">
      <div className="text-[10px] text-ink-400 dark:text-rice-500">{label}</div>
      <div className="font-serif text-base font-semibold text-ink-800 dark:text-rice-100">{value}</div>
    </div>
  );
}

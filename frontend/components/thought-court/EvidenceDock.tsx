"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Gavel, ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import type { CitationStatus, CourtEvidence, CourtMotionMode } from "@/lib/thoughtCourtTypes";
import styles from "./ThoughtCourt.module.css";

interface EvidenceDockProps {
  evidence: CourtEvidence[];
  selectedIds: string[];
  citationStatus: CitationStatus;
  motion: CourtMotionMode;
  onToggleEvidence(id: string): void;
  onBeginDebate(): void;
}

const STATUS_CONFIG: Record<
  CitationStatus,
  { label: string; icon: typeof ShieldCheck; className: string }
> = {
  verified: { label: "已核验", icon: ShieldCheck, className: styles.statusVerified },
  partial: { label: "依据不完整", icon: ShieldAlert, className: styles.statusPartial },
  unavailable: { label: "未找到足够可靠的经典依据", icon: ShieldQuestion, className: styles.statusUnavailable },
};

export default function EvidenceDock({
  evidence,
  selectedIds,
  citationStatus,
  motion,
  onToggleEvidence,
  onBeginDebate,
}: EvidenceDockProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const isDraggable = motion === "full";
  const statusConfig = STATUS_CONFIG[citationStatus];
  const StatusIcon = statusConfig.icon;
  const hasSelected = selectedIds.length > 0;

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section className={styles.evidenceDock} aria-label="经典依据">
      <div className={styles.evidenceHeader}>
        <h2 className={styles.evidenceTitle}>经典依据</h2>
        <span className={`${styles.citationBadge} ${statusConfig.className}`}>
          <StatusIcon size={15} />
          {statusConfig.label}
        </span>
      </div>

      {evidence.length === 0 && (
        <p className={styles.evidenceEmpty}>暂无经典依据。可尝试重新检索，或使用精选案例。</p>
      )}

      <div className={styles.evidenceList}>
        {evidence.map((item) => {
          const isSelected = selectedIds.includes(item.id);
          const isExpanded = expandedId === item.id;
          return (
            <article
              key={item.id}
              className={`${styles.evidenceCard} ${isSelected ? styles.evidenceCardSelected : ""}`}
              draggable={isDraggable}
              onDragStart={(e) => {
                e.dataTransfer.setData("text/plain", item.id);
                e.dataTransfer.effectAllowed = "move";
              }}
            >
              <button
                type="button"
                className={styles.evidenceCitationHeader}
                onClick={() => toggleExpand(item.id)}
                aria-expanded={isExpanded}
                aria-controls={`evidence-detail-${item.id}`}
              >
                <span className={styles.evidenceOriginal}>{item.original}</span>
                <span className={styles.evidenceSource}>{item.source}</span>
                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {isExpanded && (
                <div id={`evidence-detail-${item.id}`} className={styles.evidenceDetail}>
                  <p className={styles.evidenceRow}>
                    <span className={styles.evidenceRowLabel}>释义</span>
                    {item.interpretation}
                  </p>
                  <p className={styles.evidenceRow}>
                    <span className={styles.evidenceRowLabel}>边界</span>
                    {item.boundary}
                  </p>
                  <p className={styles.evidenceVerify}>
                    {item.verified ? "已核验" : "待核验"}
                  </p>
                </div>
              )}

              <button
                type="button"
                className={styles.evidenceToggleButton}
                onClick={() => onToggleEvidence(item.id)}
                aria-pressed={isSelected}
              >
                {isSelected ? "移出本案" : "加入本案"}
              </button>
            </article>
          );
        })}
      </div>

      <button
        type="button"
        className={styles.primaryAction}
        onClick={onBeginDebate}
        disabled={!hasSelected}
      >
        <Gavel size={20} />
        开始辩论
      </button>
    </section>
  );
}

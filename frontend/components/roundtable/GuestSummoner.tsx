"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BadgeCheck, Dice5, DoorOpen, Sparkles, Swords, UserRoundPlus, X } from "lucide-react";
import clsx from "clsx";
import type { GuestRosterItem } from "@/lib/roundtableFlow";

interface GuestSummonerProps {
  roster: GuestRosterItem[];
  onSummon: (guestKey: string) => void;
  onRandomSummon?: () => void;
  onDecision?: (guestKey: string, decision: "stay" | "leave") => void;
  disabled?: boolean;
  cue?: string | null;
}

const fallbackGuests: GuestRosterItem[] = [
  { sageKey: "li_bai", sageName: "李白", era: "唐", coreThought: "诗酒与自由", unlocked: true, collected: false, staying: false },
  { sageKey: "su_shi", sageName: "苏轼", era: "宋", coreThought: "旷达与转化", unlocked: true, collected: false, staying: false },
  { sageKey: "zhuge_liang", sageName: "诸葛亮", era: "三国", coreThought: "审势与尽责", unlocked: true, collected: false, staying: false },
];

export default function GuestSummoner({
  roster,
  onSummon,
  onRandomSummon,
  onDecision,
  disabled,
  cue,
}: GuestSummonerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const guests = useMemo(() => (roster.length ? roster : fallbackGuests), [roster]);
  const collectedCount = guests.filter((guest) => guest.collected).length;
  const stayingCount = guests.filter((guest) => guest.staying).length;

  const handleSummon = (key: string) => {
    onSummon(key);
    setIsOpen(false);
  };

  return (
    <>
      <div className="flex flex-col items-center gap-3">
        <motion.button
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          onClick={() => setIsOpen(true)}
          disabled={disabled}
          className={clsx(
            "inline-flex items-center gap-2 rounded-lg border border-[#f2c15d]/60 bg-[#3b2414] px-5 py-3 font-serif text-sm font-medium text-[#fff4d4] shadow-[0_12px_36px_rgba(0,0,0,0.25)] transition-all",
            "hover:border-[#ffd36f] hover:bg-[#4a2b16] disabled:cursor-not-allowed disabled:opacity-50"
          )}
        >
          <Swords size={18} />
          <span>踢馆花名册</span>
          <span className="rounded-md bg-[#f2c15d]/15 px-2 py-0.5 text-xs text-[#f7d98b]">{collectedCount}/{guests.length}</span>
        </motion.button>
        {cue && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 rounded-md border border-[#7b5d2a]/60 bg-[#21170f]/90 px-3 py-2 text-xs text-[#f7d98b]"
          >
            <Sparkles size={13} />
            {cue}
          </motion.div>
        )}
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.94, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.94, y: 20 }}
              onClick={(event) => event.stopPropagation()}
              className="w-full max-w-4xl overflow-hidden rounded-lg border border-[#8a6a36]/50 bg-[#17120f] shadow-[0_28px_90px_rgba(0,0,0,0.55)]"
            >
              <div className="flex items-center justify-between border-b border-[#463622] bg-[#21170f] px-5 py-4">
                <div>
                  <h3 className="font-serif text-xl font-bold text-[#fff4d4]">客席花名册</h3>
                  <p className="mt-1 text-xs text-[#bda77f]">已收集 {collectedCount} 位，席上留驻 {stayingCount} 位</p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="rounded-md p-2 text-[#bda77f] transition-colors hover:bg-[#3a2a1d] hover:text-[#fff4d4]"
                  aria-label="关闭"
                >
                  <X size={19} />
                </button>
              </div>

              <div className="grid max-h-[68vh] gap-3 overflow-y-auto p-5 md:grid-cols-2 lg:grid-cols-3">
                {guests.map((guest, index) => (
                  <motion.div
                    key={guest.sageKey}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.035 }}
                    className={clsx(
                      "rounded-lg border p-4",
                      guest.staying
                        ? "border-[#9bd18f]/60 bg-[#1d2b1e]"
                        : guest.collected
                          ? "border-[#f2c15d]/55 bg-[#2b2118]"
                          : "border-[#4c3d2c] bg-[#1b1612]"
                    )}
                  >
                    <div className="mb-4 flex items-start gap-3">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-[#3b2414] font-serif text-lg font-bold text-[#f7d98b]">
                        {guest.sageName.slice(0, 1)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-serif text-base font-semibold text-[#fff4d4]">{guest.sageName}</h4>
                          {guest.collected && <BadgeCheck size={15} className="text-[#f2c15d]" />}
                        </div>
                        <p className="text-xs text-[#bda77f]">{guest.era || "客席"} · {guest.coreThought || "论道来客"}</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => handleSummon(guest.sageKey)}
                        disabled={disabled || !guest.unlocked}
                        className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-md bg-[#7b2d1d] px-3 py-2 text-xs font-medium text-[#fff4d4] transition-colors hover:bg-[#9b3a25] disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        <UserRoundPlus size={14} />
                        召入
                      </button>
                      <button
                        onClick={() => onDecision?.(guest.sageKey, "stay")}
                        disabled={disabled || !onDecision}
                        className="inline-flex items-center justify-center gap-1.5 rounded-md border border-[#4d7255]/70 bg-[#203326] px-3 py-2 text-xs text-[#b9e2b7] transition-colors hover:bg-[#28442e] disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        <BadgeCheck size={14} />
                        留下
                      </button>
                      <button
                        onClick={() => onDecision?.(guest.sageKey, "leave")}
                        disabled={disabled || !onDecision}
                        className="inline-flex items-center justify-center gap-1.5 rounded-md border border-[#6a5a45] bg-[#211b16] px-3 py-2 text-xs text-[#d6c3a2] transition-colors hover:bg-[#30251d] disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        <DoorOpen size={14} />
                        离去
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="flex justify-center border-t border-[#463622] bg-[#21170f] px-5 py-4">
                <button
                  onClick={() => {
                    if (onRandomSummon) {
                      onRandomSummon();
                      setIsOpen(false);
                      return;
                    }
                    const randomGuest = guests[Math.floor(Math.random() * guests.length)];
                    handleSummon(randomGuest.sageKey);
                  }}
                  disabled={disabled}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#f2c15d]/55 bg-[#3b2a18] px-4 py-2.5 font-serif text-sm text-[#f7d98b] transition-all hover:bg-[#4a341d] disabled:cursor-not-allowed disabled:opacity-45"
                >
                  <Dice5 size={16} />
                  随机踢馆
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

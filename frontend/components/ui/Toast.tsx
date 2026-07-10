"use client";

import { createContext, useContext, useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Info, X } from "lucide-react";
import clsx from "clsx";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counter = useRef(0);

  const toast = useCallback((message: string, type: ToastType = "success") => {
    const id = ++counter.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.9 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={clsx(
                "flex items-center gap-3 rounded-lg px-4 py-3 text-sm shadow-popup min-w-48 max-w-80",
                t.type === "success" && "bg-white border border-bamboo-200 text-ink-800",
                t.type === "error" && "bg-white border border-cinnabar-200 text-ink-800",
                t.type === "info" && "bg-white border border-bronze-400/40 text-ink-800",
                "dark:bg-ink-700 dark:border-ink-500 dark:text-rice-100"
              )}
            >
              {t.type === "success" && <CheckCircle size={16} className="shrink-0 text-bamboo-500" />}
              {t.type === "error" && <XCircle size={16} className="shrink-0 text-cinnabar-600" />}
              {t.type === "info" && <Info size={16} className="shrink-0 text-bronze-500" />}
              <span className="flex-1 font-sans">{t.message}</span>
              <button
                onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
                className="shrink-0 text-ink-300 hover:text-ink-500 dark:text-ink-400 dark:hover:text-rice-200"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx.toast;
}

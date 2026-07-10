"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center text-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-4 font-serif text-6xl font-bold text-ink-100 dark:text-ink-700 select-none">
          典
        </div>
        <h2 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
          出了点差错
        </h2>
        <div className="classical-divider mx-auto mt-4 w-24" />
        <p className="mt-4 text-sm text-ink-400 dark:text-rice-400">
          页面加载遇到问题，请尝试刷新
        </p>
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-md bg-cinnabar-600 px-5 py-2.5 text-sm font-medium text-rice-50 transition-colors hover:bg-cinnabar-700"
          >
            <RefreshCw size={16} />
            重新加载
          </button>
          <a
            href="/"
            className="inline-flex items-center gap-2 rounded-md border border-ink-200 px-5 py-2.5 text-sm font-medium text-ink-700 transition-colors hover:bg-ink-50 dark:border-ink-600 dark:text-rice-200"
          >
            <Home size={16} />
            返回首页
          </a>
        </div>
      </motion.div>
    </div>
  );
}

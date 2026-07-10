"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { BookOpen, ArrowLeft, Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* 大字装饰 */}
        <div className="mb-4 font-serif text-8xl font-bold tracking-widest text-ink-100 dark:text-ink-700 md:text-9xl select-none">
          四
        </div>
        <div className="-mt-12 font-serif text-5xl font-bold text-cinnabar-600 md:text-6xl">
          此处无典
        </div>
        <div className="classical-divider mx-auto mt-6 w-32" />
        <p className="mt-6 text-base text-ink-400 dark:text-rice-400 md:text-lg">
          您所寻访的页面，不在此处
          <br />
          或许已移至别处，或从未存在
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-md bg-cinnabar-600 px-6 py-3 font-serif text-base font-medium text-rice-50 shadow-scroll-soft transition-all hover:bg-cinnabar-700"
          >
            <ArrowLeft size={18} />
            返回首页
          </Link>
          <Link
            href="/reader?book=lunyu"
            className="inline-flex items-center gap-2 rounded-md border border-ink-200 bg-white/60 px-6 py-3 font-serif text-base font-medium text-ink-700 transition-all hover:border-bamboo-400 hover:text-bamboo-600 dark:border-ink-600 dark:bg-ink-700/60 dark:text-rice-200"
          >
            <BookOpen size={18} />
            阅读论语
          </Link>
        </div>
      </motion.div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Scroll } from "lucide-react";
import ConceptCard from "@/components/concepts/ConceptCard";
import { mockConcepts } from "@/lib/conceptsData";

export default function ConceptsPage() {
  const [concepts] = useState(mockConcepts);

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-cinnabar-600/10 px-4 py-1 text-xs text-cinnabar-600">
          <Scroll size={13} />
          儒家核心概念
        </div>
        <h1 className="font-serif text-4xl font-bold tracking-widest text-ink-800 dark:text-rice-50">
          概念可视化
        </h1>
        <p className="mt-3 text-sm text-ink-500 dark:text-rice-300">
          以现代视角解读儒家核心思想 —— 点击卡片展开详解
        </p>
        <div className="classical-divider mx-auto mt-5 w-40" />
      </motion.div>

      {/* 概念卡片网格 */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {concepts.map((concept, idx) => (
          <ConceptCard key={concept.id} concept={concept} index={idx} />
        ))}
      </div>

      {/* 底部说明 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="rounded-xl border border-ink-100 bg-rice-100/40 p-5 text-center dark:border-ink-600 dark:bg-ink-700/40"
      >
        <p className="font-serif text-sm leading-relaxed text-ink-500 dark:text-rice-300">
          「 仁、礼、中庸、孝、学、道、君子 」—— 七大核心概念，
          构成儒家思想之基石。古人智慧，历千年而弥新，于今日仍可为修身齐家之指南。
        </p>
      </motion.div>
    </div>
  );
}

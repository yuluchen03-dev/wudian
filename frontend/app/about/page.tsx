"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles,
  Search,
  ShieldCheck,
  BookMarked,
  BookOpen,
  Compass,
  Heart,
  ArrowRight,
  MessageCircle,
  Gamepad2,
  Repeat2,
  Handshake,
  Building2,
  type LucideIcon,
} from "lucide-react";

/**
 * Pitch 信息页 —— 项目定位、技术亮点、差异化、团队愿景
 * 中式简洁设计，适合评委了解项目背景
 */

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl">
      {/* ===== Hero ===== */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="py-12 text-center"
      >
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cinnabar-300 bg-cinnabar-50 px-4 py-1 text-xs text-cinnabar-700">
          <Sparkles size={13} />
          关于悟典
        </div>
        <h1 className="hero-title text-hero-sm text-ink-800 dark:text-rice-50">
          让经典照进现实
        </h1>
        <div className="classical-divider mx-auto mt-6 w-48" />
        <p className="mt-6 font-serif text-xl leading-relaxed text-ink-500 dark:text-rice-300">
          悟典是一个让《论语》等儒家经典
          <br />
          从「背诵任务」变成「随时可用的智慧」的学习平台
        </p>
      </motion.section>

      {/* ===== 一句话定位 ===== */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-12 rounded-2xl border border-ink-100 bg-white/60 p-8 text-center shadow-scroll dark:border-ink-600 dark:bg-ink-700/40 md:p-10"
      >
        <div className="mb-3 text-xs font-medium text-bronze-500">一句话定位</div>
        <p className="font-serif text-2xl leading-relaxed text-ink-800 dark:text-rice-50 md:text-3xl">
          以 RAG + AI 对话，让两千年的圣贤智慧
          <br />
          回答你今天的困惑
        </p>
      </motion.section>

      {/* ===== 技术亮点 ===== */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mb-12"
      >
        <h2 className="mb-6 font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
          技术亮点
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <TechCard
            icon={Search}
            title="RAG 检索增强"
            desc="基于《论语》原文构建向量知识库，每一条回复都有经典依据，而非凭空生成。"
          />
          <TechCard
            icon={ShieldCheck}
            title="防幻觉机制"
            desc="严格约束 AI 在经典原文范围内回答，原文引用块清晰标注出处，杜绝「AI 编造孔子说过」的问题。"
          />
          <TechCard
            icon={BookMarked}
            title="原文可溯源"
            desc="每条引用均标注篇章出处（如《论语·颜渊第十二》），可一键跳转原文上下文阅读。"
          />
        </div>
      </motion.section>

      {/* ===== 差异化 ===== */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mb-12"
      >
        <h2 className="mb-6 font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
          差异化定位
        </h2>
        <div className="space-y-3">
          <DiffRow
            name="识典古籍"
            type="研究型数据库"
            gap="偏学术研究，门槛高，无互动对话"
            ours="悟典面向大众，AI 对话降低理解门槛"
          />
          <DiffRow
            name="Duolingo"
            type="语言学习 App"
            gap="无中文经典内容，聚焦外语学习"
            ours="悟典专注儒家经典，填补中文经典学习空白"
          />
          <DiffRow
            name="百度汉语 / 古诗文网"
            type="工具型网站"
            gap="仅提供原文查阅，无 AI 互动与场景化解读"
            ours="悟典让经典与现代生活场景连接，学以致用"
          />
        </div>
        <div className="mt-4 rounded-lg border border-cinnabar-200 bg-cinnabar-50/50 px-5 py-3 text-center dark:bg-cinnabar-900/10">
          <p className="font-serif text-base text-cinnabar-700 dark:text-cinnabar-300">
            我们站在「大众化 × AI 对话 × 中文经典」的空白交叉点
          </p>
        </div>
      </motion.section>

      {/* ===== 核心功能 ===== */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mb-12"
      >
        <h2 className="mb-6 font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
          核心功能
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            { icon: MessageCircle, title: "与圣贤对话", desc: "AI 角色化对话" },
            { icon: BookOpen, title: "沉浸阅读", desc: "文白对照 + 注音" },
            { icon: Gamepad2, title: "经典闯关", desc: "趣味答题挑战" },
            { icon: Repeat2, title: "间隔复习", desc: "SRS 科学记忆" },
          ].map((item) => {
            const Icon = item.icon;
            return (
            <div
              key={item.title}
              className="rounded-xl border border-ink-100 bg-white/60 p-4 text-center shadow-scroll dark:border-ink-600 dark:bg-ink-700/40"
            >
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-cinnabar-600/10">
                <Icon size={20} className="text-cinnabar-600" />
              </div>
              <div className="font-serif text-sm font-bold text-ink-800 dark:text-rice-50">
                {item.title}
              </div>
              <div className="mt-1 text-xs text-ink-400">{item.desc}</div>
            </div>
          );
          })}
        </div>
      </motion.section>

      {/* ===== 投资与试点合作 ===== */}
      <motion.section
        id="investment"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.55 }}
        className="mb-12 rounded-2xl border border-bronze-300/50 bg-rice-50/80 p-6 shadow-scroll dark:border-bronze-500/30 dark:bg-ink-700/40 md:p-8"
      >
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cinnabar-200 bg-white/60 px-3 py-1 text-xs text-cinnabar-700 dark:border-cinnabar-700/50 dark:bg-ink-800/60 dark:text-cinnabar-300">
              <Handshake size={13} />
              试点合作
            </div>
            <h2 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
              投资与试点合作
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-relaxed text-ink-500 dark:text-rice-300">
            当前阶段优先寻找小范围教育试点、可信内容 IP 和早期产品资金，用真实问题验证可追溯回答的价值。
          </p>
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {[
            {
              icon: Building2,
              title: "教育试点",
              desc: "适合高校通识课、社团活动和传统文化课程，先验证留存、复问率和引用点击率。",
            },
            {
              icon: BookMarked,
              title: "内容 IP",
              desc: "可与出版社、课程方和文化机构共建可信语料，把权威内容变成可追问入口。",
            },
            {
              icon: Handshake,
              title: "投资合作",
              desc: "资金主要用于语料整理、评测体系、产品打磨和试点运营，避免先做重平台。",
            },
            {
              icon: ShieldCheck,
              title: "安全边界",
              desc: "回答坚持数据可信和出处可查，不替代心理、医疗、法律、职业或投资决策。",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-lg border border-ink-100 bg-white/60 p-4 dark:border-ink-600 dark:bg-ink-800/30"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-bronze-500/10">
                    <Icon size={18} className="text-bronze-600 dark:text-bronze-300" />
                  </span>
                  <h3 className="font-serif text-base font-bold text-ink-800 dark:text-rice-50">
                    {item.title}
                  </h3>
                </div>
                <p className="text-sm leading-relaxed text-ink-500 dark:text-rice-300">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </motion.section>

      {/* ===== 团队愿景 ===== */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mb-12 rounded-2xl border border-ink-100 bg-gradient-to-br from-rice-50 to-rice-100 p-8 shadow-scroll dark:border-ink-600 dark:from-ink-700 dark:to-ink-800 md:p-10"
      >
        <div className="mb-4 flex items-center gap-2">
          <Heart size={20} className="text-cinnabar-600" />
          <h2 className="font-serif text-2xl font-bold text-ink-800 dark:text-rice-50">
            愿景
          </h2>
        </div>
        <p className="font-serif text-lg leading-loose text-ink-600 dark:text-rice-200">
          让每一个普通人，都能在困惑时
          <br />
          问一问孔子，听一听孟子的回答
          <br />
          让经典不再是课本里的背诵任务
          <br />
          而是生活中随时可取的智慧之光
        </p>
      </motion.section>

      {/* ===== CTA ===== */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="mb-8 text-center"
      >
        <Link
          href="/demo"
          className="inline-flex items-center gap-2 rounded-xl bg-cinnabar-600 px-8 py-4 font-serif text-lg font-medium text-rice-50 shadow-popup transition-all hover:bg-cinnabar-700 hover:shadow-lg"
        >
          <Compass size={20} />
          体验演示
          <ArrowRight size={18} />
        </Link>
      </motion.section>

      {/* ===== 免责声明 ===== */}
      <div className="rounded-xl border border-bronze-400/30 bg-rice-100/60 px-6 py-4 text-center text-xs text-ink-400 dark:bg-ink-700/40">
        悟典 · 让经典触手可及 · © 2026 · AI 回应为基于经典的演绎，非历史人物原话
      </div>
    </div>
  );
}

/* ============ 子组件 ============ */

function TechCard({
  icon: Icon,
  title,
  desc,
}: {
  icon: LucideIcon;
  title: string;
  desc: string;
}) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white/60 p-5 shadow-scroll dark:border-ink-600 dark:bg-ink-700/40">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-cinnabar-600/10">
        <Icon size={20} className="text-cinnabar-600" />
      </div>
      <h3 className="mb-2 font-serif text-lg font-bold text-ink-800 dark:text-rice-50">
        {title}
      </h3>
      <p className="text-sm leading-relaxed text-ink-500 dark:text-rice-300">
        {desc}
      </p>
    </div>
  );
}

function DiffRow({
  name,
  type,
  gap,
  ours,
}: {
  name: string;
  type: string;
  gap: string;
  ours: string;
}) {
  return (
    <div className="grid grid-cols-1 gap-2 rounded-lg border border-ink-100 bg-white/40 p-4 dark:border-ink-600 dark:bg-ink-700/30 md:grid-cols-3 md:items-center">
      <div>
        <div className="font-serif text-base font-bold text-ink-800 dark:text-rice-50">
          {name}
        </div>
        <div className="text-xs text-ink-400">{type}</div>
      </div>
      <div className="text-sm text-ink-400">
        <span className="mr-1 text-cinnabar-400">✕</span>
        {gap}
      </div>
      <div className="text-sm text-bamboo-600 dark:text-bamboo-400">
        <span className="mr-1">✓</span>
        {ours}
      </div>
    </div>
  );
}

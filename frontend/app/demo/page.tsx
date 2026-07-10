"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircuitBoard,
  Clock3,
  FileText,
  GitBranch,
  Handshake,
  MessageCircle,
  RadioTower,
  ScrollText,
  ShieldCheck,
  Sparkles,
  UsersRound,
  Video,
  type LucideIcon,
} from "lucide-react";
import clsx from "clsx";

type Accent = "cinnabar" | "bamboo" | "bronze";

type DemoSignal = {
  eyebrow: string;
  title: string;
  line: string;
  body: string;
  icon: LucideIcon;
  href: string;
  action: string;
  accent: Accent;
};

const demoQuestion = "我很努力但总不被领导认可，怎么办？";
const sageChatDemoHref = `/sage-chat?q=${encodeURIComponent(demoQuestion)}`;
const roundtableCompleteDemoHref = "/roundtable?demo=complete";

const demoSignals: DemoSignal[] = [
  {
    eyebrow: "主爆点",
    title: "可信问道",
    line: "每一句安慰，都有出处",
    body: "用预设问题进入 /sage-chat，让孔子先检索经典，再给出带原文、出处、白话点睛和 citations 的回答。",
    icon: ShieldCheck,
    href: sageChatDemoHref,
    action: "进入问道",
    accent: "cinnabar",
  },
  {
    eyebrow: "炸场预览",
    title: "百家论道",
    line: "不是一个 AI，是一桌中国思想",
    body: "快速切到 /roundtable，展示孔子、老子、墨子、韩非子围绕现代困境交锋，以及主持 Agent 状态图。",
    icon: UsersRound,
    href: roundtableCompleteDemoHref,
    action: "打开论道",
    accent: "bamboo",
  },
  {
    eyebrow: "技术证据",
    title: "可溯源智能体",
    line: "RAG + citations + 状态图",
    body: "用 /about 或技术页一句话讲清：RAG 检索、SSE 流式、citations 可校验、结构化标签渲染。",
    icon: CircuitBoard,
    href: "/about",
    action: "看技术页",
    accent: "bronze",
  },
];

const runbook = [
  {
    time: "0:00",
    title: "举手钩子",
    action: "打开 /demo",
    detail: "谁完整读懂过《论语》？指出语言、语境、趣味三道墙。",
    icon: Sparkles,
  },
  {
    time: "0:30",
    title: "可信问道",
    action: "点 /sage-chat",
    detail: "选择孔子，点击“职场困惑”预设，避免中文输入法和手打失误。",
    icon: MessageCircle,
  },
  {
    time: "1:00",
    title: "让产品动起来",
    action: "看流式输出",
    detail: "指向“夫子正翻阅典籍”、检索篇章、原文块和逐字出现的回答。",
    icon: ScrollText,
  },
  {
    time: "1:40",
    title: "证据收束",
    action: "展开本次参考",
    detail: "强调 citations、出处、相关度、注疏和免责声明：不是编古文。",
    icon: ShieldCheck,
  },
  {
    time: "2:10",
    title: "一句技术",
    action: "切 /about",
    detail: "RAG 检索 + SSE 流式 + citations 可溯源 + 结构化标签渲染。",
    icon: CircuitBoard,
  },
  {
    time: "2:35",
    title: "百家论道炸场",
    action: "切 /roundtable",
    detail: "展示主持 Agent 状态图和多思想交锋：一桌中国思想审你的问题。",
    icon: UsersRound,
  },
];

const proofPoints = [
  {
    title: "RAG 不是装饰",
    detail: "先检索《论语》原文和注疏，再生成回答；检索不到就标注无引用。",
    icon: BookOpen,
  },
  {
    title: "citations 可展开",
    detail: "评委能看到来源、原文、相关度和注疏类型，可信度不是口头承诺。",
    icon: FileText,
  },
  {
    title: "主持 Agent 状态图",
    detail: "百家论道有 round1、round2、intervention、report 等可追踪节点。",
    icon: GitBranch,
  },
];

const fallbackPlan = [
  "8 秒内没有正文：先讲检索篇章，再切备份视频。",
  "不要手打问题：只点预设“职场困惑”。",
  "圆桌不从零跑：提前打开 /roundtable 完成态或演示态。",
  "技术不要过讲：一句话讲清 RAG、SSE、citations、状态图。",
];

export default function DemoPage() {
  return (
    <div className="-mx-4 -my-8 min-h-screen bg-rice-50 px-4 py-8 text-ink-800 dark:bg-ink-900 dark:text-rice-50">
      <section className="mx-auto grid max-w-7xl gap-8 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end lg:py-12">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="space-y-7"
        >
          <div className="inline-flex items-center gap-2 rounded-md border border-cinnabar-300 bg-white px-3 py-1.5 text-sm text-cinnabar-700 shadow-scroll-soft dark:border-cinnabar-800 dark:bg-ink-800 dark:text-cinnabar-300">
            <RadioTower size={15} />
            黑客松现场指挥台
          </div>

          <div className="space-y-5">
            <p className="font-serif text-lg text-bronze-600 dark:text-bronze-300">
              可信圣贤智能体系统
            </p>
            <h1 className="font-serif text-5xl font-bold leading-tight text-ink-900 dark:text-rice-50 md:text-7xl">
              让经典从背诵任务，变成一场可追溯的现场对话
            </h1>
            <p className="max-w-2xl text-lg leading-loose text-ink-500 dark:text-rice-300">
              主流程求稳：先用可信问道打动评委；结尾炸场：用百家论道证明这不是聊天壳，而是一套能组织思想交锋的 AI 产品。
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <PrimaryLink href={sageChatDemoHref} icon={MessageCircle}>
              开始可信问道
            </PrimaryLink>
            <SecondaryLink href={roundtableCompleteDemoHref} icon={UsersRound}>
              百家论道预览
            </SecondaryLink>
            <SecondaryLink href="/about#investment" icon={Handshake}>
              试点合作
            </SecondaryLink>
            <SecondaryLink href="/about" icon={CircuitBoard}>
              技术证据
            </SecondaryLink>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.55 }}
          className="rounded-lg border border-ink-100 bg-white p-5 shadow-scroll dark:border-ink-700 dark:bg-ink-800"
        >
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm text-bronze-600 dark:text-bronze-300">3 分钟评审路线</p>
              <h2 className="font-serif text-2xl font-bold">按这个顺序点</h2>
            </div>
            <Clock3 className="text-cinnabar-600" size={24} />
          </div>
          <div className="space-y-3">
            {runbook.slice(0, 4).map((item, index) => (
              <RunbookRow key={item.time} item={item} index={index} compact />
            ))}
          </div>
        </motion.div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 py-4 md:grid-cols-3">
        {demoSignals.map((signal, index) => (
          <SignalCard key={signal.title} signal={signal} index={index} />
        ))}
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 py-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-lg border border-ink-100 bg-white p-5 shadow-scroll dark:border-ink-700 dark:bg-ink-800 md:p-6">
          <div className="mb-5 flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-ink-800 text-rice-50 dark:bg-rice-100 dark:text-ink-800">
              <Clock3 size={20} />
            </span>
            <div>
              <p className="text-sm text-bronze-600 dark:text-bronze-300">主持人操作台</p>
              <h2 className="font-serif text-2xl font-bold">3 分钟评审路线</h2>
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {runbook.map((item, index) => (
              <RunbookRow key={item.time} item={item} index={index} />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-ink-100 bg-white p-5 shadow-scroll dark:border-ink-700 dark:bg-ink-800">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck size={18} className="text-cinnabar-600" />
              <h2 className="font-serif text-xl font-bold">评委要看的证据</h2>
            </div>
            <div className="space-y-3">
              {proofPoints.map((point) => (
                <ProofPoint key={point.title} point={point} />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-bronze-300 bg-rice-100 p-5 dark:border-bronze-800 dark:bg-ink-800">
            <div className="mb-3 flex items-center gap-2">
              <Video size={18} className="text-bronze-600 dark:text-bronze-300" />
              <h2 className="font-serif text-xl font-bold">备份视频与兜底</h2>
            </div>
            <ul className="space-y-2">
              {fallbackPlan.map((item) => (
                <li key={item} className="flex gap-2 text-sm leading-relaxed text-ink-600 dark:text-rice-300">
                  <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-bamboo-600" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function SignalCard({
  signal,
  index,
}: {
  signal: DemoSignal;
  index: number;
}) {
  const Icon = signal.icon;
  const accentClass = {
    cinnabar: "bg-cinnabar-600 text-rice-50 border-cinnabar-200",
    bamboo: "bg-bamboo-600 text-rice-50 border-bamboo-200",
    bronze: "bg-bronze-600 text-rice-50 border-bronze-200",
  }[signal.accent];

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 * index, duration: 0.5 }}
      className="flex min-h-[300px] flex-col rounded-lg border border-ink-100 bg-white p-5 shadow-scroll transition-transform hover:-translate-y-1 dark:border-ink-700 dark:bg-ink-800"
    >
      <div className="mb-5 flex items-center justify-between">
        <span className="rounded-md bg-rice-100 px-2.5 py-1 text-xs font-medium text-bronze-600 dark:bg-ink-700 dark:text-bronze-300">
          {signal.eyebrow}
        </span>
        <span className={clsx("flex h-11 w-11 items-center justify-center rounded-md border", accentClass)}>
          <Icon size={22} />
        </span>
      </div>
      <h2 className="font-serif text-3xl font-bold">{signal.title}</h2>
      <p className="mt-2 font-kai text-xl leading-relaxed text-cinnabar-700 dark:text-cinnabar-300">
        {signal.line}
      </p>
      <p className="mt-4 flex-1 text-sm leading-loose text-ink-500 dark:text-rice-300">
        {signal.body}
      </p>
      <Link
        href={signal.href}
        className="mt-5 inline-flex items-center justify-center gap-2 rounded-md border border-ink-200 px-4 py-2.5 font-serif text-sm font-semibold text-ink-700 transition-colors hover:border-cinnabar-400 hover:text-cinnabar-700 dark:border-ink-600 dark:text-rice-200"
      >
        {signal.action}
        <ArrowRight size={15} />
      </Link>
    </motion.article>
  );
}

function RunbookRow({
  item,
  index,
  compact = false,
}: {
  item: {
    time: string;
    title: string;
    action: string;
    detail: string;
    icon: LucideIcon;
  };
  index: number;
  compact?: boolean;
}) {
  const Icon = item.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.04 * index, duration: 0.35 }}
      className={clsx(
        "grid gap-3 rounded-md border border-ink-100 bg-rice-50 p-3 dark:border-ink-700 dark:bg-ink-900/45",
        compact ? "grid-cols-[54px_1fr]" : "grid-cols-[58px_1fr]"
      )}
    >
      <div className="flex flex-col items-center justify-center rounded-md bg-white px-2 py-2 text-center shadow-scroll-soft dark:bg-ink-800">
        <span className="font-serif text-sm font-bold text-cinnabar-700 dark:text-cinnabar-300">{item.time}</span>
        <Icon size={compact ? 14 : 16} className="mt-1 text-bronze-500" />
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className={clsx("font-serif font-bold", compact ? "text-base" : "text-lg")}>{item.title}</h3>
          <span className="rounded-md bg-white px-2 py-0.5 text-xs text-ink-500 dark:bg-ink-800 dark:text-rice-300">
            {item.action}
          </span>
        </div>
        <p className={clsx("mt-1 leading-relaxed text-ink-500 dark:text-rice-300", compact ? "text-xs" : "text-sm")}>
          {item.detail}
        </p>
      </div>
    </motion.div>
  );
}

function ProofPoint({
  point,
}: {
  point: {
    title: string;
    detail: string;
    icon: LucideIcon;
  };
}) {
  const Icon = point.icon;

  return (
    <div className="grid grid-cols-[34px_1fr] gap-3 rounded-md border border-ink-100 bg-rice-50 p-3 dark:border-ink-700 dark:bg-ink-900/45">
      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-white text-cinnabar-700 dark:bg-ink-800 dark:text-cinnabar-300">
        <Icon size={17} />
      </span>
      <div>
        <h3 className="font-serif text-base font-bold">{point.title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-ink-500 dark:text-rice-300">{point.detail}</p>
      </div>
    </div>
  );
}

function PrimaryLink({
  href,
  icon: Icon,
  children,
}: {
  href: string;
  icon: LucideIcon;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-12 items-center justify-center gap-2 rounded-md bg-cinnabar-600 px-5 py-3 font-serif text-base font-semibold text-rice-50 shadow-scroll transition-colors hover:bg-cinnabar-700"
    >
      <Icon size={19} />
      {children}
      <ArrowRight size={17} />
    </Link>
  );
}

function SecondaryLink({
  href,
  icon: Icon,
  children,
}: {
  href: string;
  icon: LucideIcon;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-12 items-center justify-center gap-2 rounded-md border border-ink-200 bg-white px-5 py-3 font-serif text-base font-semibold text-ink-700 shadow-scroll-soft transition-colors hover:border-bamboo-500 hover:text-bamboo-700 dark:border-ink-600 dark:bg-ink-800 dark:text-rice-100"
    >
      <Icon size={19} />
      {children}
    </Link>
  );
}

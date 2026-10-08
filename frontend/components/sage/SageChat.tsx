"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, RotateCcw, AlertCircle, User, BookOpen } from "lucide-react";
import clsx from "clsx";
import type { Sage, SageMessage, Citation } from "@/lib/types";
import { generateSageReply, getLocalSageCitations } from "@/lib/sageData";
import { api } from "@/lib/api";
import CitationSidebar from "./CitationSidebar";

interface SageChatProps {
  sage: Sage;
  onReset?: () => void;
  /** 演示模式：放大字号、增强原文引用块视觉效果 */
  demoMode?: boolean;
  /** 自定义预设问题（演示引导），传入后替换默认 suggested_questions */
  presetQuestions?: string[];
  /** 初始预填消息：挂载后自动发送此消息（用于从每日一句等入口跳转） */
  initialMessage?: string;
  onCitationsChange?: (citations: Citation[]) => void;
  onSearchChaptersChange?: (chapters: { name: string; source: string }[]) => void;
}

export default function SageChat({ sage, onReset, demoMode = false, presetQuestions, initialMessage, onCitationsChange, onSearchChaptersChange }: SageChatProps) {
  const [messages, setMessages] = useState<SageMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesRef = useRef<SageMessage[]>([]);
  const abortRef = useRef(false);

  // 检索可视化状态
  const [isSearching, setIsSearching] = useState(false);
  const [searchChapters, setSearchChapters] = useState<{ name: string; source: string }[]>([]);

  // 保持 messages ref 同步，供流式回调读取最新历史
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // 初始化欢迎语
  useEffect(() => {
    abortRef.current = true;
    setIsStreaming(false);
    setIsSearching(false);
    setSearchChapters([]);
    setStreamError("");
    onCitationsChange?.([]);
    onSearchChaptersChange?.([]);
    setMessages([
      {
        id: "welcome",
        role: "sage",
        content: `吾乃${sage.name}。${sage.description.slice(0, 30)}……汝有何惑，尽管道来。`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, [sage, onCitationsChange, onSearchChaptersChange]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // 清理
  useEffect(() => {
    return () => {
      abortRef.current = true;
    };
  }, []);

  // 初始预填消息：挂载后自动发送（仅一次）
  const initialSentRef = useRef(false);
  useEffect(() => {
    if (initialMessage && !initialSentRef.current && !isStreaming) {
      initialSentRef.current = true;
      const timer = setTimeout(() => handleSend(initialMessage), 400);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isStreaming) return;
    abortRef.current = false;

    const userMsg: SageMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };

    const sageMsgId = `sage-${Date.now()}`;

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);
    setStreamError("");
    setIsSearching(true);
    setSearchChapters([]);
    onCitationsChange?.([]);
    onSearchChaptersChange?.([]);

    // 初始化空的 sage 消息
    setMessages((prev) => [
      ...prev,
      {
        id: sageMsgId,
        role: "sage",
        content: "",
        timestamp: new Date().toISOString(),
      },
    ]);

    // 构建历史（不含刚加的 user msg 和空 sage msg）
    const history = messagesRef.current
      .filter((m) => m.id !== "welcome")
      .map((m) => ({
        role: m.role === "user" ? ("user" as const) : ("assistant" as const),
        content: m.content,
      }));

    // 标记是否已收到第一个文本 chunk（用于隐藏检索动画）
    let firstChunkReceived = false;

    try {
      await api.chatWithSageStream(
        sage.id,
        content,
        (chunk) => {
          if (abortRef.current) return;
          // 收到第一个文本 chunk 时，结束检索动画
          if (!firstChunkReceived) {
            firstChunkReceived = true;
            setIsSearching(false);
          }
          setMessages((prev) =>
            prev.map((m) =>
              m.id === sageMsgId ? { ...m, content: m.content + chunk } : m
            )
          );
        },
        history,
        // 检索篇章回调：后端在 LLM 流式输出之前先发送检索到的篇章信息
        (chapters) => {
          if (abortRef.current) return;
          setSearchChapters(chapters);
          onSearchChaptersChange?.(chapters);
        },
        // 思想依据回调：接收 RAG 检索到的引用
        (citations) => {
          if (abortRef.current) return;
          onCitationsChange?.(citations);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === sageMsgId ? { ...m, citations } : m
            )
          );
        }
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "对话出错，请稍后重试";
      setStreamError(msg);
      // 兜底：用本地生成补全
      if (abortRef.current === false) {
        const fallback = generateSageReply(sage.id, content);
        const fallbackCitations = getLocalSageCitations(sage.id);
        onCitationsChange?.(fallbackCitations);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === sageMsgId
              ? { ...m, content: fallback, citations: fallbackCitations }
              : m
          )
        );
      }
    } finally {
      setIsStreaming(false);
      setIsSearching(false);
    }
  };

  const handleReset = () => {
    abortRef.current = true;
    setTimeout(() => (abortRef.current = false), 100);
    setIsStreaming(false);
    setStreamError("");
    setSearchChapters([]);
    onCitationsChange?.([]);
    onSearchChaptersChange?.([]);
    setMessages([
      {
        id: "welcome",
        role: "sage",
        content: `吾乃${sage.name}。${sage.description.slice(0, 30)}……汝有何惑，尽管道来。`,
        timestamp: new Date().toISOString(),
      },
    ]);
    onReset?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div
      data-ui="sage-composer"
      className={clsx(
        "flex min-w-0 flex-col overflow-hidden rounded-[6px] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-scroll dark:border-ink-600 dark:bg-ink-800",
        demoMode
          ? "h-[calc(100dvh-266px)] max-h-[calc(100dvh-266px)] sm:h-[calc(100dvh-246px)] sm:max-h-[calc(100dvh-246px)] lg:h-[calc(100dvh-198px)] lg:max-h-[calc(100dvh-198px)]"
          : "h-[600px]"
      )}
    >
      {/* 圣贤头部 - 印章风格头像 */}
      <div className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-sage)] px-5 py-3.5 dark:border-ink-600 dark:bg-ink-700/60">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <div
            className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-md bg-cover bg-center font-serif text-xl font-bold text-rice-50 shadow-md"
            style={{
              backgroundColor: sage.avatar_color,
              backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined,
            }}
          >
            <span className={sage.portraitImage ? "sr-only" : ""}>{sage.name[0]}</span>
          </div>
          <div className="min-w-0">
            <div className="font-serif text-lg font-bold text-ink-800 dark:text-rice-50">
              {sage.name}
            </div>
            <div className="truncate text-xs text-ink-400 dark:text-rice-400">{sage.speaking_style}</div>
          </div>
        </div>
        <button
          onClick={handleReset}
          disabled={isStreaming}
          className="flex h-11 w-11 shrink-0 items-center justify-center gap-1 rounded-md text-xs text-ink-500 transition-colors hover:bg-ink-100 disabled:opacity-40 dark:text-rice-300 dark:hover:bg-ink-600 sm:w-auto sm:px-2.5"
          aria-label="重新对话"
        >
          <RotateCcw size={13} />
          <span className="hidden sm:inline">重新对话</span>
        </button>
      </div>

      {/* 消息列表 - 更大间距、更清晰气泡 */}
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto p-5">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={clsx(
              "flex gap-3",
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            {/* 头像 */}
            <div
              className={clsx(
                "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md text-sm font-bold text-rice-50 shadow-sm",
                msg.role === "user" ? "bg-ink-500" : ""
              )}
              style={
                msg.role === "sage"
                  ? {
                      backgroundColor: sage.avatar_color,
                      backgroundImage: sage.portraitImage ? `url(${sage.portraitImage})` : undefined,
                      backgroundSize: "cover",
                      backgroundPosition: "center",
                    }
                  : {}
              }
            >
              {msg.role === "user" ? (
                <User size={16} />
              ) : (
                <span className={sage.portraitImage ? "sr-only" : ""}>{sage.name[0]}</span>
              )}
            </div>

            {/* 消息气泡 + 思想依据 */}
            <div
              className={clsx(
                "flex flex-col",
                msg.role === "user" ? "items-end" : "items-start",
                demoMode ? "max-w-[85%] md:max-w-[78%]" : "max-w-[80%]"
              )}
            >
              <div
                className={clsx(
                  "rounded-xl px-5 py-3 shadow-scroll-soft",
                  msg.role === "user"
                    ? "rounded-tr-sm bg-cinnabar-600 text-rice-50"
                    : "rounded-tl-sm bg-white text-ink-800 dark:bg-ink-700 dark:text-rice-100"
                )}
              >
                {msg.role === "sage" ? (
                  <SageMessageContent
                    content={msg.content}
                    demoMode={demoMode}
                    streaming={isStreaming && !!msg.content}
                  />
                ) : (
                  <p
                    className={clsx(
                      "font-serif whitespace-pre-wrap",
                      demoMode ? "text-lg leading-relaxed" : "text-sm leading-relaxed"
                    )}
                  >
                    {msg.content}
                  </p>
                )}
                {msg.role === "sage" && isStreaming && msg.content && (
                  <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-cinnabar-600 align-middle" />
                )}
              </div>

              {/* 思想依据侧栏（仅 sage 消息且有引用时显示） */}
              {msg.role === "sage" && msg.citations && msg.citations.length > 0 && !isStreaming && (
                <CitationSidebar
                  citations={msg.citations}
                  demoMode={demoMode}
                  onLocate={(citation) => {
                    // 跳转到阅读器（可通过 URL 参数传递）
                    if (citation.chapter) {
                      window.open(
                        `/reader?highlight=${encodeURIComponent(citation.text)}&source=${encodeURIComponent(citation.source)}`,
                        "_blank"
                      );
                    }
                  }}
                />
              )}
            </div>
          </motion.div>
        ))}

        {/* 检索可视化动画 */}
        <AnimatePresence>
          {isSearching && (
            <SearchVisualization
              chapters={searchChapters}
              sageColor={sage.avatar_color}
              sageName={sage.name}
              demoMode={demoMode}
            />
          )}
        </AnimatePresence>
      </div>

      {/* 预设问题 */}
      {messages.length <= 1 && (
        <div className="border-t border-ink-100 px-4 py-3 dark:border-ink-600">
          {demoMode ? (
            <DemoGuideInline
              questions={presetQuestions}
              onSelect={handleSend}
              disabled={isStreaming}
            />
          ) : (
            <>
              <div className="mb-1.5 text-xs text-ink-400">推荐问题：</div>
              <div className="flex flex-wrap gap-1.5">
                {(presetQuestions ?? sage.suggested_questions).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    disabled={isStreaming}
                    className="rounded-full border border-ink-200 bg-rice-50 px-3.5 py-1.5 text-xs text-ink-600 transition-colors hover:border-bamboo-400 hover:text-bamboo-600 disabled:opacity-40 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-300 dark:hover:border-bamboo-500"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* 免责声明 */}
      <div className="flex items-center gap-1.5 border-t border-ink-100 bg-rice-100/40 px-5 py-2 dark:border-ink-600 dark:bg-ink-700/40">
        <AlertCircle size={12} className="flex-shrink-0 text-bronze-500" />
        <span className="text-[11px] leading-tight text-ink-400 dark:text-rice-400">
          {streamError
            ? `连接异常，已使用本地演绎回复：${streamError}`
            : "这是基于经典思想的演绎，非历史人物原话"}
        </span>
      </div>

      {/* 输入区 */}
      <div className="flex items-center gap-2.5 border-t border-ink-100 p-3.5 dark:border-ink-600">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          placeholder="向圣贤请教……"
          className={clsx(
            "flex-1 rounded-full border border-ink-200 bg-white px-5 py-2.5 text-ink-700 outline-none transition-colors focus:border-cinnabar-400 focus:shadow-scroll-soft disabled:opacity-50 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200",
            demoMode && "py-3 text-lg"
          )}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isStreaming}
          aria-label="发送问题"
          className={clsx(
            "flex flex-shrink-0 items-center justify-center rounded-full bg-cinnabar-600 text-rice-50 shadow-scroll-soft transition-all hover:bg-cinnabar-700 hover:shadow-scroll disabled:cursor-not-allowed disabled:opacity-40",
            demoMode ? "h-11 w-11" : "h-10 w-10"
          )}
        >
          <Send size={demoMode ? 20 : 16} />
        </button>
      </div>
    </div>
  );
}

/* ============ 检索可视化组件 ============ */

interface SearchVisualizationProps {
  chapters: { name: string; source: string }[];
  sageColor: string;
  sageName: string;
  demoMode: boolean;
}

/**
 * 检索可视化动画组件
 * - 先显示"夫子正翻阅典籍……"提示
 * - 篇章名以 stagger 动画依次浮现
 * - 中式美学：楷体、淡入、墨色渐变
 */
function SearchVisualization({ chapters, sageColor, sageName, demoMode }: SearchVisualizationProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3 }}
      className="flex gap-3"
    >
      {/* 圣贤头像 */}
      <div
        className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md text-sm font-bold text-rice-50 shadow-sm"
        style={{ backgroundColor: sageColor }}
      >
        {sageName[0]}
      </div>

      {/* 检索动画容器 */}
      <div
        className={clsx(
          "max-w-[80%] rounded-xl rounded-tl-sm px-5 py-4 shadow-scroll-soft",
          "bg-white dark:bg-ink-700",
          demoMode && "md:max-w-[78%]"
        )}
      >
        {/* 搜索提示 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-3 flex items-center gap-2"
        >
          <BookOpen size={demoMode ? 16 : 14} className="text-bronze-500" />
          <span
            className={clsx(
              "font-kai text-ink-500 dark:text-rice-400",
              demoMode ? "text-base" : "text-sm"
            )}
          >
            夫子正翻阅典籍……
          </span>
          {/* 加载动画点 */}
          <span className="flex gap-0.5">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="inline-block h-1 w-1 rounded-full bg-bronze-400"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.3,
                }}
              />
            ))}
          </span>
        </motion.div>

        {/* 篇章名列表 - stagger 动画 */}
        <motion.div
          className="flex flex-wrap gap-2"
          variants={{
            hidden: {},
            show: {
              transition: {
                staggerChildren: 0.35,
              },
            },
          }}
          initial="hidden"
          animate="show"
        >
          {chapters.map((ch, i) => (
            <motion.div
              key={`${ch.name}-${i}`}
              variants={{
                hidden: { opacity: 0, x: -8, scale: 0.95 },
                show: {
                  opacity: 1,
                  x: 0,
                  scale: 1,
                  transition: { duration: 0.4, ease: "easeOut" },
                },
              }}
              className="flex items-center gap-1.5"
            >
              {/* 竹简风格标签 */}
              <span
                className={clsx(
                  "inline-flex items-center gap-1 rounded-md border border-ink-200/60 bg-rice-100/80 px-2.5 py-1 dark:border-ink-500/40 dark:bg-ink-600/60",
                  demoMode ? "text-base" : "text-sm"
                )}
              >
                <span
                  className="inline-block h-2 w-0.5 rounded-full"
                  style={{ backgroundColor: sageColor }}
                />
                <span className="font-kai tracking-wider text-ink-700 dark:text-rice-200">
                  {ch.name}
                </span>
              </span>
              {/* 箭头连接符（最后一个不显示） */}
              {i < chapters.length - 1 && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.4 }}
                  transition={{ delay: 0.2 }}
                  className="text-xs text-ink-300 dark:text-ink-500"
                >
                  →
                </motion.span>
              )}
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
}

/* ============ 演示模式增强子组件 ============ */

/**
 * 圣贤消息内容渲染
 * 演示模式下：解析「子曰：...」引用块，用朱砂竖线+楷体放大显示
 * 白话点睛部分用米黄卡片
 */
function SageMessageContent({
  content,
  demoMode,
  streaming,
}: {
  content: string;
  demoMode: boolean;
  streaming: boolean;
}) {
  // 非演示模式：楷体渲染、更大字号
  if (!demoMode) {
    return (
      <p className="font-kai whitespace-pre-wrap text-base leading-loose text-ink-800 dark:text-rice-100" style={{ letterSpacing: "0.03em" }}>
        {content}
      </p>
    );
  }

  // 演示模式：解析引用与白话部分
  const parts = parseSageContent(content);

  return (
    <div className="space-y-3">
      {parts.map((part, i) => {
        if (part.type === "quote") {
          // 原文引用块：朱砂竖线 + 楷体 + 宣纸纹理 + 放大
          return (
            <div
              key={i}
              className="paper-texture-card relative overflow-hidden rounded-md border-l-4 border-cinnabar-600 bg-gradient-to-br from-rice-100 to-rice-50 py-3.5 pl-4 pr-3 shadow-scroll-soft dark:from-ink-600/40 dark:to-ink-600/20"
            >
              <div className="mb-1 flex items-center gap-1.5">
                <span className="inline-flex items-center rounded-sm bg-cinnabar-600 px-1.5 py-0.5 font-serif text-[10px] font-medium tracking-wider text-rice-50">
                  原文
                </span>
              </div>
              <p className="font-kai text-lg leading-loose text-ink-800 dark:text-rice-100" style={{ letterSpacing: "0.05em" }}>
                {part.text}
              </p>
              {part.source && (
                <span className="mt-2 inline-flex items-center gap-1 text-xs text-bronze-500 dark:text-rice-400">
                  <span className="h-px w-4 bg-bronze-400/50" />
                  {part.source}
                </span>
              )}
            </div>
          );
        }
        if (part.type === "insight") {
          // 白话点睛：米黄卡片
          return (
            <div
              key={i}
              className="rounded-lg border border-rice-300 bg-rice-100/90 px-4 py-3 dark:bg-rice-300/10"
            >
              <div className="mb-1 flex items-center gap-1 text-xs font-medium text-bronze-500">
                <BookOpen size={12} />
                白话点睛
              </div>
              <p className="text-base leading-relaxed text-ink-700 dark:text-rice-200">
                {part.text}
              </p>
            </div>
          );
        }
        // 普通文本
        return (
          <p
            key={i}
            className="font-serif whitespace-pre-wrap text-lg leading-relaxed text-ink-700 dark:text-rice-200"
          >
            {part.text}
          </p>
        );
      })}
      {streaming && parts.length === 0 && (
        <span className="text-ink-400">……</span>
      )}
    </div>
  );
}

type ContentPart =
  | { type: "text"; text: string }
  | { type: "quote"; text: string; source?: string }
  | { type: "insight"; text: string };

/**
 * 解析圣贤回复内容，提取引用块和白话点睛
 *
 * 优先解析后端 <<<TAG>>> 结构化格式：
 *   <<<QUOTE>>>      → 原文引用块（type: "quote"）
 *   <<<SOURCE>>>     → 引用块出处（合并到前一个 quote 的 source）
 *   <<<CLASSICAL>>>  → 文言回应正文（type: "text"，楷体放大）
 *   <<<VERNACULAR>>> → 白话点睛卡片（type: "insight"）
 *   <<<DISCLAIMER>>> → 忽略（底部已有免责声明条）
 *
 * 流式输出场景：标签可能不完整，已到达但未闭合的标签内容作为普通文本显示，
 * 等更多内容到达后重新解析。
 *
 * 向后兼容：当内容不含 <<<TAG>>> 标记时，回退到旧的「子曰：」正则模式。
 */
function parseSageContent(content: string): ContentPart[] {
  // 优先尝试 <<<TAG>>> 格式
  if (content.includes("<<<")) {
    const tagged = parseTaggedContent(content);
    if (tagged.length > 0) return tagged;
  }

  // 回退：旧「子曰：」正则模式（LLM 未按格式输出时的兜底）
  return parseLegacyContent(content);
}

/**
 * 解析 <<<TAG>>> 结构化格式
 * 处理流式部分内容：对于未闭合的标签，把已到达的内容作为对应类型显示
 */
function parseTaggedContent(content: string): ContentPart[] {
  const parts: ContentPart[] = [];
  const TAGS: Array<{ tag: string; type: "quote" | "text" | "insight" | "source" | "ignore" }> = [
    { tag: "QUOTE", type: "quote" },
    { tag: "SOURCE", type: "source" },
    { tag: "CLASSICAL", type: "text" },
    { tag: "VERNACULAR", type: "insight" },
    { tag: "DISCLAIMER", type: "ignore" },
  ];

  // 找到所有标签出现位置
  const tagMatches: Array<{ tag: string; type: string; index: number }> = [];
  const tagRegex = /<<<(\w+)>>>/g;
  let m: RegExpExecArray | null;
  while ((m = tagRegex.exec(content)) !== null) {
    tagMatches.push({ tag: m[1], type: m[1], index: m.index });
  }

  // 没有完整标签 → 不是 tagged 格式
  if (tagMatches.length === 0) return [];

  // 标签前的前导文本（清理后忽略，通常是空行）
  const leading = content.slice(0, tagMatches[0].index).trim();
  if (leading) {
    parts.push({ type: "text", text: leading });
  }

  // 逐段提取每个标签后的内容（直到下一个标签）
  for (let i = 0; i < tagMatches.length; i++) {
    const { tag, index } = tagMatches[i];
    const tagDef = TAGS.find((t) => t.tag === tag);
    const segType = tagDef?.type ?? "text";

    const contentStart = index + tag.length + 6; // "<<<" + tag + ">>>"
    const contentEnd = i + 1 < tagMatches.length ? tagMatches[i + 1].index : content.length;
    const segText = content.slice(contentStart, contentEnd).trim();

    if (!segText) continue;

    if (segType === "quote") {
      parts.push({ type: "quote", text: segText });
    } else if (segType === "source") {
      // 合并到前一个 quote 的 source
      const last = parts[parts.length - 1];
      if (last && last.type === "quote" && segText !== "无") {
        last.source = segText;
      }
      // 若无前导 quote 则忽略 source
    } else if (segType === "insight") {
      parts.push({ type: "insight", text: segText });
    } else if (segType === "text") {
      parts.push({ type: "text", text: segText });
    }
    // "ignore" (DISCLAIMER) 直接跳过
  }

  // 如果只解析出了 quote 但 source 还没到达（流式中），已 push 的 quote 无 source，正常

  // 若解析后没有有效内容（全是空段或 disclaimer），回退到原文
  if (parts.length === 0) {
    parts.push({ type: "text", text: content.replace(/<<<\w+>>>/g, "").trim() });
  }

  return parts;
}

/**
 * 旧格式兜底解析：「子曰：...」引用 + 白话点睛关键词
 */
function parseLegacyContent(content: string): ContentPart[] {
  const parts: ContentPart[] = [];

  // 匹配 "子曰：..." / "孟子曰：..." / "阳明子曰：..." 引用
  const quotePattern = /((?:子|孟子|阳明子)曰[：:][^。！？]*[。！？])/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = quotePattern.exec(content)) !== null) {
    // 前面的文本
    if (match.index > lastIndex) {
      const before = content.slice(lastIndex, match.index).trim();
      if (before) parts.push({ type: "text", text: before });
    }
    // 引用文本
    const quoteText = match[1].trim();
    parts.push({ type: "quote", text: quoteText });
    lastIndex = match.index + match[1].length;
  }

  // 剩余文本
  if (lastIndex < content.length) {
    const remaining = content.slice(lastIndex).trim();
    if (remaining) {
      // 检查是否含"白话"/"意为"等关键词
      const insightPattern = /(白话[：:]|意为[：:]|也就是说[，,])/;
      if (insightPattern.test(remaining)) {
        parts.push({ type: "insight", text: remaining });
      } else {
        parts.push({ type: "text", text: remaining });
      }
    }
  }

  // 如果没有解析出任何部分，返回原文
  if (parts.length === 0) {
    parts.push({ type: "text", text: content });
  }

  return parts;
}

/**
 * 演示引导内联组件（用于 SageChat 内部预设问题区）
 * 紧凑版 DemoGuide，适配对话框内的空间
 */
function DemoGuideInline({
  questions,
  onSelect,
  disabled,
}: {
  questions?: string[];
  onSelect: (q: string) => void;
  disabled: boolean;
}) {
  // 如果有自定义问题列表，用字符串数组；否则用默认演示问题
  const defaultQuestions = [
    "我很努力但总不被领导认可，怎么办？",
    "朋友一直不听劝，我还要继续劝吗？",
    "做错事了，该怎么面对？",
  ];
  const list = questions ?? defaultQuestions;
  const labels = ["职场困惑", "交友之道", "改过自新"];

  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5">
        <span className="text-xs font-medium text-cinnabar-600">推荐演示问题</span>
        <span className="text-[10px] text-ink-300">· 点击直接发送</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {list.map((q, idx) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            disabled={disabled}
            className="group flex items-center gap-2 rounded-lg border border-ink-200 bg-white px-3 py-1.5 text-left transition-all hover:border-cinnabar-400 hover:shadow-scroll disabled:opacity-40 dark:border-ink-500 dark:bg-ink-700"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-cinnabar-600 text-[10px] font-bold text-rice-50">
              {idx + 1}
            </span>
            <span className="font-serif text-sm text-ink-700 dark:text-rice-200">
              {labels[idx] || q.slice(0, 8)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

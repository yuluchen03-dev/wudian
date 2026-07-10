"use client";

import { ReactNode } from "react";
import clsx from "clsx";

/**
 * 中式装饰组件集合
 * 克制、高级的中式美学：大留白、低饱和、宋体/楷体
 */

/* ============ InkDivider 水墨风分隔线 ============ */
interface InkDividerProps {
  className?: string;
  /** 是否显示中间印章圆点 */
  withSeal?: boolean;
  /** 宽度 */
  width?: string;
}

export function InkDivider({
  className,
  withSeal = true,
  width = "w-32",
}: InkDividerProps) {
  return (
    <div className={clsx("flex items-center justify-center gap-3", className)}>
      <div
        className={clsx(
          "h-px bg-gradient-to-r from-transparent to-ink-300 dark:to-ink-400",
          withSeal ? "w-16" : width
        )}
      />
      {withSeal && (
        <>
          <div className="h-1.5 w-1.5 rounded-full bg-cinnabar-600/70" />
          <div className="h-px w-16 bg-gradient-to-l from-transparent to-ink-300 dark:to-ink-400" />
        </>
      )}
    </div>
  );
}

/* ============ SealStamp 印章风格小标签 ============ */
interface SealStampProps {
  children: ReactNode;
  className?: string;
  /** 印章颜色变体 */
  variant?: "cinnabar" | "ink" | "bamboo";
  size?: "sm" | "md";
}

export function SealStamp({
  children,
  className,
  variant = "cinnabar",
  size = "sm",
}: SealStampProps) {
  const variants = {
    cinnabar: "bg-cinnabar-600 text-rice-50",
    ink: "bg-ink-700 text-rice-50",
    bamboo: "bg-bamboo-600 text-rice-50",
  };
  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
  };
  return (
    <span
      className={clsx(
        "inline-flex items-center font-serif font-medium tracking-wider rounded-sm shadow-sm",
        "border border-black/5",
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}

/* ============ QuoteBlock 原文引用块 ============ */
interface QuoteBlockProps {
  children: ReactNode;
  /** 出处标签（如"《论语·学而》"） */
  source?: string;
  className?: string;
  /** 是否使用楷体 */
  kai?: boolean;
}

export function QuoteBlock({
  children,
  source,
  className,
  kai = true,
}: QuoteBlockProps) {
  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-md border-l-4 border-cinnabar-600",
        "bg-gradient-to-br from-rice-100 to-rice-50",
        "px-5 py-4 shadow-scroll-soft",
        "dark:from-ink-700 dark:to-ink-800 dark:border-cinnabar-500",
        className
      )}
    >
      {/* 宣纸纹理 */}
      <div className="pointer-events-none absolute inset-0 opacity-30 paper-texture-card" />
      <div className="relative">
        <div className="mb-1.5 flex items-center gap-2">
          <SealStamp variant="cinnabar" size="sm">
            原文
          </SealStamp>
          {source && (
            <span className="text-xs text-bronze-500 dark:text-rice-400">
              {source}
            </span>
          )}
        </div>
        <p
          className={clsx(
            "text-lg leading-loose text-ink-800 dark:text-rice-100 md:text-xl",
            kai && "font-kai"
          )}
          style={{ letterSpacing: "0.05em" }}
        >
          {children}
        </p>
      </div>
    </div>
  );
}

/* ============ SectionTitle 章节标题 ============ */
interface SectionTitleProps {
  children: ReactNode;
  className?: string;
  /** 是否显示装饰分隔线 */
  withDivider?: boolean;
  /** 对齐方式 */
  align?: "left" | "center";
}

export function SectionTitle({
  children,
  className,
  withDivider = false,
  align = "left",
}: SectionTitleProps) {
  return (
    <div
      className={clsx(
        align === "center" ? "text-center" : "text-left",
        className
      )}
    >
      <div className="flex items-center gap-2.5">
        {align === "center" && <div className="h-px w-8 bg-ink-300 dark:bg-ink-500" />}
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-cinnabar-600/70" />
        <h2 className="font-serif text-2xl font-semibold tracking-wider text-ink-800 dark:text-rice-50 md:text-3xl">
          {children}
        </h2>
        {align === "center" && <div className="h-px w-8 bg-ink-300 dark:bg-ink-500" />}
      </div>
      {withDivider && <InkDivider className="mt-3" withSeal={false} />}
    </div>
  );
}

/* ============ CTAButton 朱砂色醒目按钮 ============ */
interface CTAButtonProps {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
  size?: "md" | "lg";
}

export function CTAButton({
  children,
  href,
  onClick,
  className,
  size = "lg",
}: CTAButtonProps) {
  const sizes = {
    md: "px-6 py-2.5 text-base",
    lg: "px-8 py-3.5 text-lg",
  };
  const baseCls = clsx(
    "inline-flex items-center justify-center gap-2 rounded-md",
    "bg-cinnabar-600 text-rice-50 font-serif font-medium tracking-wider",
    "shadow-scroll transition-all duration-300",
    "hover:bg-cinnabar-700 hover:shadow-popup hover:-translate-y-0.5",
    "active:translate-y-0 active:shadow-scroll",
    sizes[size],
    className
  );

  if (href) {
    return (
      <a href={href} className={baseCls}>
        {children}
      </a>
    );
  }
  return (
    <button onClick={onClick} className={baseCls}>
      {children}
    </button>
  );
}

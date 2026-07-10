import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { ToastProvider } from "@/components/ui/Toast";
import { pageBackgrounds } from "@/lib/visualAssets";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: "悟典 · 四书五经互动学习平台",
  description: "与千年圣贤对话，悟经典之大义。文白对照阅读、AI 圣贤问答、SRS 间隔复习，让儒家经典触手可及。",
  openGraph: {
    title: "悟典 · 四书五经互动学习平台",
    description: "与千年圣贤对话，悟经典之大义。文白对照、AI 问道、经典闯关。",
    type: "website",
    locale: "zh_CN",
    siteName: "悟典",
  },
  twitter: {
    card: "summary_large_image",
    title: "悟典 · 四书五经互动学习平台",
    description: "与千年圣贤对话，悟经典之大义。",
  },
  icons: {
    icon: "/favicon.svg",
  },
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body
        className="min-h-screen bg-rice-50 text-ink-800 antialiased"
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(248,245,238,0.9), rgba(248,245,238,0.98)), url(${pageBackgrounds.reader})`,
          backgroundAttachment: "fixed",
          backgroundSize: "cover",
          backgroundPosition: "center top",
        }}
      >
        <ToastProvider>
          <Navbar />
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          <footer className="mt-16 border-t border-ink-100 dark:border-ink-600">
            <div className="mx-auto max-w-6xl px-4 py-10">
              <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
                <div>
                  <div className="mb-3 font-serif text-sm font-semibold text-ink-700 dark:text-rice-200">
                    核心功能
                  </div>
                  <ul className="space-y-2 text-xs text-ink-400 dark:text-rice-400">
                    <li><a href="/reader" className="hover:text-cinnabar-600 transition-colors">沉浸阅读</a></li>
                    <li><a href="/sage-chat" className="hover:text-cinnabar-600 transition-colors">与圣贤对话</a></li>
                    <li><a href="/roundtable" className="hover:text-cinnabar-600 transition-colors">百家论道</a></li>
                    <li><a href="/challenge" className="hover:text-cinnabar-600 transition-colors">经典闯关</a></li>
                  </ul>
                </div>
                <div>
                  <div className="mb-3 font-serif text-sm font-semibold text-ink-700 dark:text-rice-200">
                    学习工具
                  </div>
                  <ul className="space-y-2 text-xs text-ink-400 dark:text-rice-400">
                    <li><a href="/review" className="hover:text-cinnabar-600 transition-colors">间隔复习</a></li>
                    <li><a href="/exploration" className="hover:text-cinnabar-600 transition-colors">知识探索</a></li>
                    <li><a href="/concepts" className="hover:text-cinnabar-600 transition-colors">概念可视化</a></li>
                    <li><a href="/achievements" className="hover:text-cinnabar-600 transition-colors">成就系统</a></li>
                  </ul>
                </div>
                <div>
                  <div className="mb-3 font-serif text-sm font-semibold text-ink-700 dark:text-rice-200">
                    趣味内容
                  </div>
                  <ul className="space-y-2 text-xs text-ink-400 dark:text-rice-400">
                    <li><a href="/content" className="hover:text-cinnabar-600 transition-colors">金句卡片</a></li>
                    <li><a href="/community" className="hover:text-cinnabar-600 transition-colors">共学社区</a></li>
                    <li><a href="/demo" className="hover:text-cinnabar-600 transition-colors">演示导览</a></li>
                  </ul>
                </div>
                <div>
                  <div className="mb-3 font-serif text-sm font-semibold text-ink-700 dark:text-rice-200">
                    关于
                  </div>
                  <ul className="space-y-2 text-xs text-ink-400 dark:text-rice-400">
                    <li><a href="/about" className="hover:text-cinnabar-600 transition-colors">项目介绍</a></li>
                  </ul>
                </div>
              </div>
              <div className="mt-8 border-t border-ink-100 pt-6 text-center text-xs text-ink-400 dark:border-ink-600 dark:text-rice-500">
                悟典 · 让经典触手可及 · © 2026 · AI 回应为基于经典的演绎，非历史人物原话
              </div>
            </div>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}

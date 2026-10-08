import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { ToastProvider } from "@/components/ui/Toast";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: "悟典 · 有据可循的经典思想问答",
  description: "向圣贤请教，让每一次回答都有典可循。经典原文、出处校验与多家思想对照。",
  openGraph: {
    title: "悟典 · 有据可循的经典思想问答",
    description: "向圣贤请教，让每一次回答都有典可循。",
    type: "website",
    locale: "zh_CN",
    siteName: "悟典",
  },
  icons: { icon: "/favicon.svg" },
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">
        <ToastProvider>
          <Navbar />
          <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8">{children}</main>
          <footer className="mt-16 border-t border-[var(--color-line)] bg-[rgba(251,249,243,0.72)]">
            <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-4 py-8 text-xs text-[var(--color-muted)] sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
              <div className="display-serif text-base font-semibold text-[var(--color-ink)]">悟典</div>
              <div>以经典原文为依据的思想问答 · AI 回应非历史人物原话</div>
            </div>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}

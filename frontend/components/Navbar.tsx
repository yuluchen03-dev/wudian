"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  Compass,
  MessageCircle,
  Home,
  Network,
  Sparkles,
  Feather,
  MessagesSquare,
  Brain,
  Trophy,
  LogIn,
  UserPlus,
  LogOut,
  User,
  PlayCircle,
  Info,
  Users,
  Menu,
  X,
  ChevronDown,
} from "lucide-react";
import clsx from "clsx";
import { isLoggedIn, logout, getUser } from "@/lib/auth";
import type { UserInfo } from "@/lib/types";

const primaryNav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/reader", label: "阅读", icon: BookOpen },
  { href: "/sage-chat", label: "问道", icon: MessagesSquare },
  { href: "/roundtable", label: "论道", icon: Users },
  { href: "/challenge", label: "闯关", icon: Compass },
  { href: "/review", label: "复习", icon: Brain },
  { href: "/demo", label: "演示", icon: PlayCircle },
];

const moreNav = [
  { href: "/exploration", label: "探索", icon: Network },
  { href: "/concepts", label: "概念", icon: Feather },
  { href: "/achievements", label: "成就", icon: Trophy },
  { href: "/community", label: "社区", icon: MessageCircle },
  { href: "/content", label: "趣味", icon: Sparkles },
  { href: "/about", label: "关于", icon: Info },
];

const allNav = [...primaryNav, ...moreNav];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    setUser(getUser<UserInfo>());
  }, [pathname]);

  // 关闭移动菜单 on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  // 点击外部关闭"更多"下拉
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    setLoggedIn(false);
    setUser(null);
    setUserMenuOpen(false);
    setMobileOpen(false);
    router.push("/");
  };

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const hasActiveMore = moreNav.some((item) => isActive(item.href));

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-ink-100/80 bg-rice-50/90 backdrop-blur-md dark:bg-ink-800/90 dark:border-ink-600/80">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          {/* Logo */}
          <Link href="/" className="flex shrink-0 items-center gap-2.5">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-md bg-cinnabar-600 font-serif text-lg font-bold text-rice-50 shadow-scroll-soft">
              悟
              <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-rice-100/40" />
            </span>
            <span className="font-serif text-xl font-semibold tracking-widest text-ink-800 dark:text-rice-50">
              悟典
            </span>
          </Link>

          {/* 桌面导航 */}
          <nav className="hidden items-center gap-0.5 md:flex">
            {primaryNav.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "nav-link-bamboo flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "text-cinnabar-600 active dark:text-cinnabar-400"
                      : "text-ink-600 hover:text-bamboo-600 dark:text-rice-200 dark:hover:text-bamboo-400"
                  )}
                >
                  <Icon size={15} />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* 更多下拉 */}
            <div ref={moreRef} className="relative">
              <button
                onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                className={clsx(
                  "nav-link-bamboo flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors",
                  hasActiveMore || moreMenuOpen
                    ? "text-cinnabar-600 dark:text-cinnabar-400"
                    : "text-ink-600 hover:text-bamboo-600 dark:text-rice-200 dark:hover:text-bamboo-400"
                )}
              >
                更多
                <ChevronDown size={14} className={clsx("transition-transform", moreMenuOpen && "rotate-180")} />
              </button>
              {moreMenuOpen && (
                <div className="absolute right-0 top-12 z-50 w-36 rounded-lg border border-ink-100 bg-white py-1 shadow-popup dark:border-ink-600 dark:bg-ink-700">
                  {moreNav.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.href);
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMoreMenuOpen(false)}
                        className={clsx(
                          "flex items-center gap-2 px-4 py-2 text-sm transition-colors hover:bg-rice-50 dark:hover:bg-ink-600",
                          active ? "text-cinnabar-600 dark:text-cinnabar-400" : "text-ink-600 dark:text-rice-200"
                        )}
                      >
                        <Icon size={14} />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </nav>

          {/* 右侧：用户 + 移动端汉堡 */}
          <div className="flex items-center gap-2">
            {/* 用户区域 */}
            <div className="hidden sm:block">
              {loggedIn ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 rounded-full border border-ink-200 bg-white/80 px-2 py-1 transition-colors hover:border-bamboo-300 hover:bg-rice-100 dark:border-ink-600 dark:bg-ink-700/80"
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-cinnabar-100 font-serif text-sm font-bold text-cinnabar-700 dark:bg-cinnabar-900 dark:text-cinnabar-300">
                      {(user?.nickname || user?.username || "学").charAt(0)}
                    </span>
                    {user?.nickname && (
                      <span className="hidden max-w-20 truncate text-sm text-ink-700 dark:text-rice-200 sm:inline">
                        {user.nickname}
                      </span>
                    )}
                  </button>
                  {userMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                      <div className="absolute right-0 top-12 z-20 w-44 rounded-lg border border-ink-100 bg-white py-1 shadow-popup dark:border-ink-600 dark:bg-ink-700">
                        <div className="border-b border-ink-50 px-4 py-2 dark:border-ink-600">
                          <div className="text-sm font-medium text-ink-800 dark:text-rice-100">
                            {user?.nickname || user?.username}
                          </div>
                          <div className="text-xs text-ink-400 dark:text-rice-400">
                            Lv.{user?.level ?? 1} · {user?.exp ?? 0} EXP
                          </div>
                        </div>
                        <Link
                          href="/achievements"
                          onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-2 px-4 py-2 text-sm text-ink-600 transition-colors hover:bg-rice-50 hover:text-bamboo-600 dark:text-rice-300 dark:hover:bg-ink-600"
                        >
                          <User size={15} />
                          我的成就
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-cinnabar-600 transition-colors hover:bg-cinnabar-50 dark:text-cinnabar-400 dark:hover:bg-cinnabar-900/30"
                        >
                          <LogOut size={15} />
                          退出登录
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <Link
                    href="/login"
                    className="flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-ink-600 transition-colors hover:bg-ink-100 hover:text-ink-800 dark:text-rice-200 dark:hover:bg-ink-700"
                  >
                    <LogIn size={16} />
                    <span>登录</span>
                  </Link>
                  <Link
                    href="/register"
                    className="flex items-center gap-1.5 rounded-md bg-cinnabar-600 px-3 py-2 text-sm font-medium text-white shadow-scroll-soft transition-all hover:bg-cinnabar-700"
                  >
                    <UserPlus size={16} />
                    <span>注册</span>
                  </Link>
                </div>
              )}
            </div>

            {/* 移动端汉堡按钮 */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="flex h-10 w-10 items-center justify-center rounded-md text-ink-600 transition-colors hover:bg-ink-100 dark:text-rice-200 dark:hover:bg-ink-700 md:hidden"
              aria-label={mobileOpen ? "关闭菜单" : "打开菜单"}
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </header>

      {/* 移动端全屏抽屉 */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-30 bg-ink-900/40 backdrop-blur-sm md:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <div className="fixed left-0 right-0 top-16 z-30 max-h-[calc(100vh-4rem)] overflow-y-auto border-b border-ink-100 bg-rice-50 shadow-popup dark:border-ink-600 dark:bg-ink-800 md:hidden">
            <nav className="grid grid-cols-3 gap-1 p-4">
              {allNav.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={clsx(
                      "flex flex-col items-center gap-1.5 rounded-lg px-2 py-3 text-xs font-medium transition-colors",
                      active
                        ? "bg-cinnabar-50 text-cinnabar-600 dark:bg-cinnabar-900/30 dark:text-cinnabar-400"
                        : "text-ink-600 hover:bg-ink-50 dark:text-rice-200 dark:hover:bg-ink-700"
                    )}
                  >
                    <Icon size={20} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* 移动端用户区 */}
            <div className="border-t border-ink-100 p-4 dark:border-ink-600">
              {loggedIn ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-cinnabar-100 font-serif text-sm font-bold text-cinnabar-700">
                      {(user?.nickname || user?.username || "学").charAt(0)}
                    </span>
                    <div>
                      <div className="text-sm font-medium text-ink-800 dark:text-rice-100">
                        {user?.nickname || user?.username}
                      </div>
                      <div className="text-xs text-ink-400">Lv.{user?.level ?? 1} · {user?.exp ?? 0} EXP</div>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 rounded-md px-3 py-2 text-sm text-cinnabar-600 hover:bg-cinnabar-50"
                  >
                    <LogOut size={15} />
                    退出
                  </button>
                </div>
              ) : (
                <div className="flex gap-3">
                  <Link
                    href="/login"
                    className="flex flex-1 items-center justify-center gap-2 rounded-md border border-ink-200 py-2.5 text-sm font-medium text-ink-700"
                  >
                    <LogIn size={16} /> 登录
                  </Link>
                  <Link
                    href="/register"
                    className="flex flex-1 items-center justify-center gap-2 rounded-md bg-cinnabar-600 py-2.5 text-sm font-medium text-white"
                  >
                    <UserPlus size={16} /> 注册
                  </Link>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}

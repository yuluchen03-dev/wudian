"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, Brain, ChevronDown, Compass, Home, Info, LogIn, LogOut, Menu, MessageCircle, MessagesSquare, Network, Sparkles, Trophy, UserPlus, Users, X } from "lucide-react";
import clsx from "clsx";
import { getUser, isLoggedIn, logout } from "@/lib/auth";
import type { UserInfo } from "@/lib/types";

const primaryNav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/sage-chat", label: "问道", icon: MessagesSquare },
  { href: "/reader", label: "经典", icon: BookOpen },
  { href: "/roundtable", label: "论道", icon: Users },
  { href: "/exploration", label: "探索", icon: Network },
];

const moreNav = [
  { href: "/challenge", label: "闯关", icon: Compass },
  { href: "/review", label: "复习", icon: Brain },
  { href: "/content", label: "内容", icon: Sparkles },
  { href: "/community", label: "社区", icon: MessageCircle },
  { href: "/achievements", label: "成就", icon: Trophy },
  { href: "/about", label: "关于", icon: Info },
];

const allNav = [...primaryNav, ...moreNav];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    setUser(getUser<UserInfo>());
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (moreRef.current && !moreRef.current.contains(event.target as Node)) setMoreOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const active = (href: string) => href === "/" ? pathname === "/" : pathname.startsWith(href);
  const handleLogout = () => {
    logout();
    setLoggedIn(false);
    setUser(null);
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-line)] bg-[rgba(245,241,232,0.9)] backdrop-blur-xl">
      <div className="mx-auto flex h-[68px] max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-h-11 items-center gap-3" aria-label="悟典首页">
          <span className="display-serif grid h-9 w-9 place-items-center rounded-[3px] bg-[var(--color-citation)] text-lg font-bold text-white">悟</span>
          <span>
            <span className="display-serif block text-xl font-semibold text-[var(--color-ink)]">悟典</span>
            <span className="hidden text-[10px] text-[var(--color-muted)] sm:block">经典思想交互平台</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="主导航">
          {primaryNav.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} className={clsx("flex min-h-11 items-center gap-2 border-b-2 px-3 text-sm transition-colors", active(href) ? "border-[var(--color-citation)] text-[var(--color-ink)]" : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-ink)]")}>
              <Icon size={16} />{label}
            </Link>
          ))}
          <div ref={moreRef} className="relative">
            <button onClick={() => setMoreOpen(!moreOpen)} className="flex min-h-11 items-center gap-1 px-3 text-sm text-[var(--color-muted)]" aria-expanded={moreOpen}>
              更多 <ChevronDown size={15} className={clsx("transition-transform", moreOpen && "rotate-180")} />
            </button>
            {moreOpen && (
              <div className="absolute right-0 top-12 grid w-52 grid-cols-2 gap-1 rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] p-2 shadow-popup">
                {moreNav.map(({ href, label, icon: Icon }) => (
                  <Link key={href} href={href} onClick={() => setMoreOpen(false)} className="flex min-h-11 items-center gap-2 rounded px-3 text-sm text-[var(--color-muted)] hover:bg-white hover:text-[var(--color-ink)]"><Icon size={15} />{label}</Link>
                ))}
              </div>
            )}
          </div>
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            {loggedIn ? (
              <button onClick={handleLogout} className="flex min-h-11 items-center gap-2 px-3 text-sm text-[var(--color-muted)]" title="退出登录"><span className="grid h-7 w-7 place-items-center rounded-full bg-[var(--color-action)] text-xs text-white">{(user?.nickname || user?.username || "学").charAt(0)}</span><LogOut size={15} /></button>
            ) : (
              <div className="flex items-center gap-1">
                <Link href="/login" className="flex min-h-11 items-center gap-2 px-3 text-sm text-[var(--color-muted)]"><LogIn size={16} />登录</Link>
                <Link href="/register" className="wudian-action px-4 text-sm"><UserPlus size={16} />注册</Link>
              </div>
            )}
          </div>
          <button onClick={() => setMobileOpen(!mobileOpen)} className="grid h-11 w-11 place-items-center lg:hidden" aria-label={mobileOpen ? "关闭菜单" : "打开菜单"}>{mobileOpen ? <X /> : <Menu />}</button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-[var(--color-line)] bg-[var(--color-surface)] p-4 lg:hidden">
          <nav className="grid grid-cols-2 gap-1" aria-label="移动导航">
            {allNav.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} className={clsx("flex min-h-12 items-center gap-3 rounded px-3 text-sm", active(href) ? "bg-[var(--color-sage)] text-[var(--color-ink)]" : "text-[var(--color-muted)]")}><Icon size={18} />{label}</Link>
            ))}
          </nav>
          <div data-ui="mobile-auth" className="mt-3 border-t border-[var(--color-line)] pt-3 sm:hidden">
            {loggedIn ? (
              <button onClick={handleLogout} className="flex min-h-12 w-full items-center justify-between rounded px-3 text-sm text-[var(--color-muted)]">
                <span className="flex items-center gap-3"><span className="grid h-8 w-8 place-items-center rounded-full bg-[var(--color-action)] text-xs text-white">{(user?.nickname || user?.username || "学").charAt(0)}</span>{user?.nickname || user?.username || "我的账户"}</span>
                <span className="flex items-center gap-2"><LogOut size={16} />退出</span>
              </button>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link href="/login" className="flex min-h-12 items-center justify-center gap-2 rounded-[4px] border border-[var(--color-line)] text-sm text-[var(--color-muted)]"><LogIn size={16} />登录</Link>
                <Link href="/register" className="wudian-action px-4 text-sm"><UserPlus size={16} />注册</Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

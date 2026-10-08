"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { LogIn, AlertCircle, Loader2, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { setToken, isLoggedIn } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // 已登录则跳转
  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/");
    }
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!username.trim() || !password.trim()) {
        setError("请填写用户名和密码");
        return;
      }
      setError("");
      setLoading(true);
      try {
        const res = await api.login(username.trim(), password);
        setToken(res.access_token, res.refresh_token, res.user);
        router.push("/");
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "登录失败，请检查用户名和密码";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [username, password, router]
  );

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl border border-ink-100 bg-white p-8 shadow-popup sm:p-10">
          {/* 标题 */}
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-cinnabar-600">
              <BookOpen size={28} className="text-rice-50" />
            </div>
            <h1 className="font-serif text-2xl font-bold text-ink-800">登录悟典</h1>
            <p className="mt-2 text-sm text-ink-500">
              登录后即可同步进度、解锁成就
            </p>
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                用户名 / 邮箱
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="输入用户名或邮箱"
                autoComplete="username"
                className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 text-ink-800 outline-none transition-colors focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码"
                autoComplete="current-password"
                className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 text-ink-800 outline-none transition-colors focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
              />
            </div>

            {/* 错误提示 */}
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="flex items-center gap-2 rounded-lg border border-cinnabar-200 bg-cinnabar-50 px-4 py-3 text-sm text-cinnabar-700"
              >
                <AlertCircle size={16} />
                {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-cinnabar-600 py-3 font-medium text-white transition-colors hover:bg-cinnabar-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  登录中……
                </>
              ) : (
                <>
                  <LogIn size={18} />
                  登录
                </>
              )}
            </button>
          </form>

          {/* 注册链接 */}
          <div className="mt-6 text-center text-sm text-ink-500">
            还没有账号？
            <Link
              href="/register"
              className="ml-1 font-medium text-cinnabar-600 hover:underline"
            >
              立即注册
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
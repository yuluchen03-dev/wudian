"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { UserPlus, AlertCircle, Loader2, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // 前端校验
      if (!username.trim()) {
        setError("请输入用户名");
        return;
      }
      if (username.trim().length < 2) {
        setError("用户名至少 2 个字符");
        return;
      }
      if (!email.trim()) {
        setError("请输入邮箱");
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
        setError("邮箱格式不正确");
        return;
      }
      if (password.length < 6) {
        setError("密码至少 6 个字符");
        return;
      }

      setError("");
      setLoading(true);
      try {
        const res = await api.register(
          username.trim(),
          email.trim(),
          password,
          nickname.trim() || undefined
        );
        // 注册成功后自动登录
        setToken(res.access_token, res.refresh_token, res.user);
        router.push("/");
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "注册失败，请稍后重试";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [username, email, password, nickname, router]
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
            <h1 className="font-serif text-2xl font-bold text-ink-800">注册悟典</h1>
            <p className="mt-2 text-sm text-ink-500">
              开启经典学习之旅，温故而知新
            </p>
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                用户名 <span className="text-cinnabar-600">*</span>
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="至少 2 个字符"
                autoComplete="username"
                className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 text-ink-800 outline-none transition-colors focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                邮箱 <span className="text-cinnabar-600">*</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                autoComplete="email"
                className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 text-ink-800 outline-none transition-colors focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                密码 <span className="text-cinnabar-600">*</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="至少 6 个字符"
                autoComplete="new-password"
                className="w-full rounded-lg border border-ink-200 bg-rice-50 px-4 py-3 text-ink-800 outline-none transition-colors focus:border-cinnabar-400 focus:ring-2 focus:ring-cinnabar-100"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink-700">
                昵称（可选）
              </label>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="给自己起个雅号"
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
                  注册中……
                </>
              ) : (
                <>
                  <UserPlus size={18} />
                  注册
                </>
              )}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-6 text-center text-sm text-ink-500">
            已有账号？
            <Link
              href="/login"
              className="ml-1 font-medium text-cinnabar-600 hover:underline"
            >
              立即登录
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/**
 * 悟典 - 前端认证工具
 * 管理 access_token / refresh_token / user 的 localStorage 存取
 */

const ACCESS_TOKEN_KEY = "wudian_access_token";
const REFRESH_TOKEN_KEY = "wudian_refresh_token";
const USER_KEY = "wudian_user";

/** 获取 access token */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/** 获取 refresh token */
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/** 保存登录信息（token + 用户信息） */
export function setToken(
  accessToken: string,
  refreshToken: string,
  user?: unknown
): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/** 仅保存用户信息 */
export function setUser(user: unknown): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/** 获取缓存的用户信息 */
export function getUser<T = unknown>(): T | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

/** 清除所有认证信息 */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** 判断是否已登录 */
export function isLoggedIn(): boolean {
  return !!getToken();
}

/** 退出登录，清除认证信息 */
export function logout(): void {
  removeToken();
}

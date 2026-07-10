/**
 * 悟典 - API 客户端封装
 * 基于 axios + SWR，支持 Mock 模式独立运行
 */
import axios, { AxiosInstance } from "axios";
import { getRefreshToken, setToken, logout } from "./auth";
import type {
  Book,
  Chapter,
  DailyQuote,
  Entity,
  LearningProgress,
  GraphResponse,
  GraphData,
  GraphNode,
  GraphEdge,
  TimelineResponse,
  TimelineEvent,
  IdiomListResponse,
  Idiom,
  StudyGroup,
  Note,
  NoteDetail,
  Comment,
  LeaderboardData,
  PKMatchResult,
  PKSettlement,
  QuoteCard,
  QuoteCardDetail,
  Theater,
  TheaterDetail,
  Concept,
  Sage,
  SageMessage,
  Citation,
  Comic,
  ImageSource,
  ChallengeLevel,
  ChallengeQuestion,
  ChallengeResult,
  ChallengeAnswer,
  DueReviewsResponse,
  ReviewStats,
  AchievementsResponse,
  RankInfo,
  AuthResponse,
  UserInfo,
  Achievement,
} from "./types";
import {
  mockBooks,
  mockChapters,
  mockDailyQuote,
  mockEntities,
  mockProgress,
} from "./mockData";
import {
  mockGraphNodes,
  mockGraphEdges,
  mockTimelineEvents,
  mockIdioms,
} from "./explorationMockData";
import {
  mockGroups,
  mockNotes,
  mockNoteDetail,
  mockLeaderboard,
  mockPKMatch,
  mockPKSettlement,
} from "./mockCommunity";
import {
  mockQuoteCards,
  mockQuoteCardDetail,
  mockTheaters,
  mockTheaterDetail,
} from "./mockContent";
import { mockConcepts } from "./conceptsData";
import { mockSages, generateSageReply } from "./sageData";
import { mockComics, mockImageSources } from "./comicData";
import {
  getBookCoverImage,
  getQuoteBackgroundImage,
  theaterCoverImages,
  theaterRolePortraitImages,
} from "./visualAssets";
import {
  generateChallengeLevels,
  generateQuestionsForLevel,
  judgeLocalAnswers,
} from "./challengeData";
import { normalizeBackendThoughtCompass, type ThoughtCompassMark } from "./thoughtCompass";
import {
  normalizeDebateStateGraph,
  normalizeGuestRoster,
  type DebateStateGraphView,
  type GuestRosterItem,
} from "./roundtableFlow";

declare module "axios" {
  interface AxiosRequestConfig {
    skipAuthRedirect?: boolean;
  }
}


const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
const mockDebateRoundCounters = new Map<string, number>();

/** 创建 axios 实例 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// ===== axios 响应拦截器：统一错误处理 =====
// 401 时尝试用 refresh_token 刷新，失败再跳登录
let _isRefreshing = false;
let _refreshSubscribers: Array<(token: string | null) => void> = [];

function subscribeTokenRefresh(cb: (token: string | null) => void) {
  _refreshSubscribers.push(cb);
}
function onTokenRefreshed(token: string | null) {
  _refreshSubscribers.forEach((cb) => cb(token));
  _refreshSubscribers = [];
}

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  try {
    // 用原始 axios 调用，避免触发拦截器递归
    const resp = await axios.post(`${API_BASE}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token, user } = resp.data || {};
    if (access_token) {
      setToken(access_token, refresh_token, user);
      return access_token as string;
    }
    return null;
  } catch {
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response) {
      const { status, data } = error.response;

      // 401 未登录 -> 尝试用 refresh_token 刷新，失败再跳登录
      if (status === 401 && !originalRequest._retry) {
        if (originalRequest.skipAuthRedirect) {
          return Promise.reject(new Error(data?.detail || "未登录或登录已过期"));
        }
        originalRequest._retry = true;
        // 公开接口（login/register/refresh）不刷新
        const url: string = originalRequest.url || "";
        if (url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/refresh")) {
          const msg = data?.detail || "用户名或密码错误";
          return Promise.reject(new Error(msg));
        }

        if (_isRefreshing) {
          // 已在刷新中，排队等待新 token
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((newToken) => {
              if (!newToken) {
                reject(new Error("未登录或登录已过期"));
                return;
              }
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              resolve(apiClient(originalRequest));
            });
          });
        }

        _isRefreshing = true;
        const newToken = await tryRefreshToken();
        _isRefreshing = false;
        onTokenRefreshed(newToken);

        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }

        // 刷新失败，清除登录态并跳登录
        logout();
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(new Error("未登录或登录已过期"));
      }

      // 404 资源不存在
      if (status === 404) {
        const msg = data?.detail || "请求的资源不存在";
        return Promise.reject(new Error(msg));
      }
      // 其他业务错误，优先取后端 detail 字段
      const msg = data?.detail || data?.message || `请求失败 (${status})`;
      return Promise.reject(new Error(msg));
    }
    if (error.request) {
      // 网络错误 / 超时 / 后端未启动
      return Promise.reject(new Error("网络异常，无法连接到服务器，请检查后端是否已启动"));
    }
    return Promise.reject(error);
  }
);

/** 请求拦截器：自动附加认证 token */
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("wudian_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});



/** Mock 延时，模拟网络请求 */
const mockDelay = <T>(data: T, ms = 200): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), ms));

/** 后端 AuthorBrief{user_id, username, nickname, avatar, level} -> 前端 AuthorBrief{userId,...} */
const mapAuthorBrief = (a: any) => ({
  userId: a?.user_id,
  username: a?.username ?? "",
  nickname: a?.nickname,
  avatar: a?.avatar,
  level: a?.level ?? 1,
});

/** 后端 CommentBrief{author, content, like_count, parent_id, created_at, replies} -> 前端 Comment{...camelCase} */
const mapComment = (c: any): Comment => ({
  id: c.id,
  author: mapAuthorBrief(c.author),
  content: c.content,
  likeCount: c.like_count ?? 0,
  parentId: c.parent_id,
  createdAt: c.created_at,
  replies: (c.replies ?? []).map(mapComment),
});



export const api = {
  /** 获取书籍列表 */
  async getBooks(): Promise<Book[]> {
    if (USE_MOCK) return mockDelay(mockBooks);
    const { data } = await apiClient.get("/classics/books");
    return (data as any[]).map((book) => ({
      ...book,
      coverImage: book.coverImage ?? book.cover_image ?? getBookCoverImage(book.id),
    }));
  },

  /** 获取指定书籍的章节列表 */
  async getChapters(bookId: string): Promise<Chapter[]> {
    if (USE_MOCK) {
      const chapters = mockChapters.filter((c) => c.bookId === bookId);
      return mockDelay(chapters);
    }
    // 后端返回 ChapterBrief[]（含 sentenceCount，不含 sentences），补默认 sentences 以兼容前端类型
    const { data } = await apiClient.get(`/classics/books/${bookId}/chapters`);
    return (data as any[]).map((c) => ({
      id: c.id,
      bookId: c.bookId,
      order: c.order,
      title: c.title,
      sentences: [],
    }));
  },

  /** 获取章节详情（含句对） */
  async getChapter(chapterId: string): Promise<Chapter> {
    if (USE_MOCK) {
      const chapter = mockChapters.find((c) => c.id === chapterId);
      if (!chapter) throw new Error("Chapter not found");
      return mockDelay(chapter);
    }
    const { data } = await apiClient.get(`/classics/chapters/${chapterId}`);
    return data;
  },

  /** 获取实体（百科）详情 */
  async getEntity(entityId: string): Promise<Entity> {
    if (USE_MOCK) {
      const entity = mockEntities.find((e) => e.id === entityId);
      if (!entity) throw new Error("Entity not found");
      return mockDelay(entity);
    }
    const { data } = await apiClient.get(`/classics/entities/${entityId}`);
    return data;
  },

  /** 获取每日一句 */
  async getDailyQuote(): Promise<DailyQuote> {
    if (USE_MOCK) return mockDelay(mockDailyQuote);
    const { data } = await apiClient.get("/classics/daily-quote");
    return data;
  },

  /** 获取学习进度 */
  async getProgress(bookId: string): Promise<LearningProgress> {
    if (USE_MOCK) {
      const progress = mockProgress.find((p) => p.bookId === bookId);
      if (!progress) throw new Error("Progress not found");
      return mockDelay(progress);
    }
    // 后端 GET /learning/progress 返回 APIResponse(code,message,data)，data 为总体进度，
    // 字段为 {verses_completed, total_verses, chapters_touched, completion_pct}，
    // 与前端 LearningProgress 结构差异较大，这里做转换（bookId 透传，部分字段填充默认值）。
    const { data: resp } = await apiClient.get(`/learning/progress`, {
      skipAuthRedirect: true,
    });
    const d = resp?.data ?? resp;
    return {
      bookId,
      currentChapterOrder: d?.chapters_touched ?? 0,
      totalChapters: d?.total_verses ?? 0,
      readChapters: [],
      streakDays: 0,
      lastReadDate: new Date().toISOString(),
    };
  },

  // ========== 互动探索层 ==========

  /** 获取知识图谱数据 */
  async getGraph(type: "disciples" | "lineage" | "all" = "all"): Promise<GraphResponse> {
    if (USE_MOCK) {
      let nodes: GraphNode[] = mockGraphNodes;
      let edges: GraphEdge[] = mockGraphEdges;

      if (type === "disciples") {
        const discipleSubtypes = new Set(["sage", "disciple"]);
        const nodeIds = new Set(
          mockGraphNodes
            .filter((n) => n.subtype && discipleSubtypes.has(n.subtype))
            .map((n) => n.id)
        );
        // 包含孔子提出的相关概念
        const conceptEdges = mockGraphEdges.filter(
          (e) => e.source === "confucius" && e.relation === "提出"
        );
        conceptEdges.forEach((e) => nodeIds.add(e.target));
        nodes = mockGraphNodes.filter((n) => nodeIds.has(n.id));
        edges = mockGraphEdges.filter(
          (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
        );
      } else if (type === "lineage") {
        const lineageSubtypes = new Set(["sage", "disciple", "lineage"]);
        const nodeIds = new Set(
          mockGraphNodes
            .filter((n) => n.subtype && lineageSubtypes.has(n.subtype))
            .map((n) => n.id)
        );
        // 包含相关概念
        mockGraphEdges.forEach((e) => {
          if (nodeIds.has(e.source) && !nodeIds.has(e.target)) {
            const target = mockGraphNodes.find((n) => n.id === e.target);
            if (target && target.type === "concept") nodeIds.add(e.target);
          }
          if (nodeIds.has(e.target) && !nodeIds.has(e.source)) {
            const source = mockGraphNodes.find((n) => n.id === e.source);
            if (source && source.type === "concept") nodeIds.add(e.source);
          }
        });
        nodes = mockGraphNodes.filter((n) => nodeIds.has(n.id));
        edges = mockGraphEdges.filter(
          (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
        );
      }

      return mockDelay({
        type,
        total_nodes: nodes.length,
        total_edges: edges.length,
        graph: { nodes, edges },
      });
    }
    const { data } = await apiClient.get(`/exploration/graph`, { params: { type } });
    return data;
  },

  /** 获取时间线数据 */
  async getTimeline(
    categories?: string[],
    startYear?: number,
    endYear?: number
  ): Promise<TimelineResponse> {
    if (USE_MOCK) {
      let events: TimelineEvent[] = [...mockTimelineEvents].sort(
        (a, b) => a.year - b.year
      );
      if (categories && categories.length > 0) {
        events = events.filter((e) => categories.includes(e.category));
      }
      if (startYear !== undefined) {
        events = events.filter((e) => e.year >= startYear);
      }
      if (endYear !== undefined) {
        events = events.filter((e) => e.year <= endYear);
      }
      return mockDelay({
        total: events.length,
        categories: ["history", "person", "classic"],
        events,
      });
    }
    const params: Record<string, string> = {};
    if (categories) params.category = categories.join(",");
    if (startYear !== undefined) params.start_year = String(startYear);
    if (endYear !== undefined) params.end_year = String(endYear);
    const { data } = await apiClient.get(`/exploration/timeline`, { params });
    return data;
  },

  /** 获取成语列表 */
  async getIdioms(tag?: string, chapter?: number): Promise<IdiomListResponse> {
    if (USE_MOCK) {
      let idioms: Idiom[] = [...mockIdioms];
      if (tag) {
        idioms = idioms.filter((i) => i.tags?.includes(tag));
      }
      if (chapter !== undefined) {
        idioms = idioms.filter((i) => i.chapter_num === chapter);
      }
      return mockDelay({ total: idioms.length, idioms });
    }
    const params: Record<string, string> = {};
    if (tag) params.tag = tag;
    if (chapter !== undefined) params.chapter = String(chapter);
    const { data } = await apiClient.get(`/exploration/idioms`, { params });
    return data;
  },

  /** 获取成语溯源详情 */
  async getIdiomDetail(idiom: string): Promise<Idiom | null> {
    if (USE_MOCK) {
      let result = mockIdioms.find((i) => i.idiom === idiom) || null;
      if (!result) {
        result = mockIdioms.find(
          (i) => i.idiom.includes(idiom) || idiom.includes(i.idiom)
        ) || null;
      }
      return mockDelay(result);
    }
    const { data } = await apiClient.get(`/exploration/idiom/${encodeURIComponent(idiom)}`);
    return data;
  },

  /** 搜索成语 */
  async searchIdioms(keyword: string): Promise<IdiomListResponse> {
    if (USE_MOCK) {
      const kw = keyword.toLowerCase();
      const results = mockIdioms.filter(
        (i) =>
          i.idiom.toLowerCase().includes(kw) ||
          i.original_text.toLowerCase().includes(kw) ||
          i.meaning.toLowerCase().includes(kw) ||
          i.source.toLowerCase().includes(kw) ||
          i.tags?.some((t) => t.toLowerCase().includes(kw))
      );
      return mockDelay({ total: results.length, idioms: results });
    }
    const { data } = await apiClient.get(`/exploration/idioms/search`, {
      params: { q: keyword },
    });
    return data;
  },

  // ========== 社区共学 ==========

  /** 获取小组列表 */
  async getGroups(): Promise<StudyGroup[]> {
    if (USE_MOCK) return mockDelay(mockGroups);
    const { data } = await apiClient.get("/community/groups");
    const items: any[] = data?.items ?? data ?? [];
    return items.map((g) => ({
      id: g.id,
      name: g.name,
      description: g.description,
      category: g.category,
      bookId: g.book_id,
      ownerName: g.owner_name,
      memberCount: g.member_count,
      maxMembers: g.max_members,
      todayCheckinCount: g.today_checkin_count,
      isPrivate: g.is_private,
      createdAt: g.created_at,
    }));
  },

  /** 加入小组 */
  async joinGroup(groupId: number): Promise<void> {
    if (USE_MOCK) return mockDelay(undefined as void);
    await apiClient.post(`/community/groups/${groupId}/join`);
  },

  /** 小组打卡 */
  async checkinGroup(groupId: number): Promise<void> {
    if (USE_MOCK) return mockDelay(undefined as void);
    await apiClient.post(`/community/groups/${groupId}/checkin`);
  },

  /** 获取笔记流 */
  async getNotes(sortBy?: string): Promise<Note[]> {
    if (USE_MOCK) return mockDelay(mockNotes);
    const { data } = await apiClient.get("/community/notes", {
      params: sortBy ? { sort_by: sortBy } : {},
    });
    const items: any[] = data?.items ?? data ?? [];
    return items.map((n) => ({
      id: n.id,
      title: n.title,
      content: n.content,
      excerpt: n.excerpt,
      author: mapAuthorBrief(n.author),
      bookId: n.book_id,
      chapterId: n.chapter_id,
      verseText: n.verse_text,
      groupId: n.group_id,
      tags: n.tags ?? [],
      likeCount: n.like_count,
      commentCount: n.comment_count,
      isLiked: n.is_liked,
      isEssence: n.is_essence,
      createdAt: n.created_at,
    }));
  },

  /** 获取笔记详情 */
  async getNoteDetail(noteId: number): Promise<NoteDetail> {
    if (USE_MOCK) return mockDelay(mockNoteDetail);
    const { data } = await apiClient.get(`/community/notes/${noteId}`);
    const n = data;
    return {
      id: n.id,
      title: n.title,
      content: n.content,
      excerpt: n.excerpt,
      author: mapAuthorBrief(n.author),
      bookId: n.book_id,
      chapterId: n.chapter_id,
      verseText: n.verse_text,
      groupId: n.group_id,
      tags: n.tags ?? [],
      likeCount: n.like_count,
      commentCount: n.comment_count,
      isLiked: n.is_liked,
      isEssence: n.is_essence,
      createdAt: n.created_at,
      comments: (n.comments ?? []).map(mapComment),
    };
  },

  /** 点赞笔记 */
  async likeNote(noteId: number): Promise<{ liked: boolean; likeCount: number }> {
    if (USE_MOCK) {
      return mockDelay({ liked: true, likeCount: 49 });
    }
    const { data } = await apiClient.post(`/community/notes/${noteId}/like`);
    // 后端返回 LikeResult{note_id, liked, like_count}
    return {
      liked: data?.liked,
      likeCount: data?.like_count,
    };
  },

  /** 评论笔记 */
  async commentNote(noteId: number, content: string): Promise<void> {
    if (USE_MOCK) return mockDelay(undefined as void);
    await apiClient.post(`/community/notes/${noteId}/comment`, { content });
  },

  /** PK 匹配 */
  async pkMatch(): Promise<PKMatchResult> {
    if (USE_MOCK) return mockDelay(mockPKMatch);
    const { data } = await apiClient.post("/community/pk/match", {
      question_count: 5,
    });
    // 后端返回 PKMatchResult{pk_id, opponent, questions, time_limit_seconds, status}
    return {
      pkId: data?.pk_id,
      opponent: mapAuthorBrief(data?.opponent),
      questions: (data?.questions ?? []).map((q: any) => ({
        index: q.index,
        question: q.question,
        options: q.options ?? [],
        verseSource: q.verse_source,
      })),
      timeLimitSeconds: data?.time_limit_seconds ?? 300,
      status: data?.status ?? "ongoing",
    };
  },

  /** 提交 PK 答案 */
  async pkSubmit(
    pkId: string,
    answers: { questionIndex: number; selectedOption: number }[]
  ): Promise<PKSettlement> {
    if (USE_MOCK) return mockDelay(mockPKSettlement);
    const { data } = await apiClient.post("/community/pk/submit", {
      pk_id: pkId,
      answers,
      duration_seconds: 120,
    });
    // 后端返回 PKSettlement{pk_id, my_score, opponent_score, result, correct_count, total_count, exp_gained, rating_change, new_rating}
    return {
      pkId: data?.pk_id,
      myScore: data?.my_score,
      opponentScore: data?.opponent_score,
      result: data?.result,
      correctCount: data?.correct_count,
      totalCount: data?.total_count,
      expGained: data?.exp_gained,
      ratingChange: data?.rating_change,
      newRating: data?.new_rating,
    };
  },

  /** 获取排行榜 */
  async getLeaderboard(
    scope: "week" | "month" | "all" = "week",
    metric: string = "exp"
  ): Promise<LeaderboardData> {
    if (USE_MOCK) return mockDelay({ ...mockLeaderboard, scope, metric });
    const { data } = await apiClient.get("/community/leaderboard", {
      params: { scope, metric },
    });
    // 后端返回 LeaderboardResponse{scope, metric, my_rank, my_score, entries}
    const entries: any[] = data?.entries ?? [];
    return {
      scope,
      metric,
      myRank: data?.my_rank,
      myScore: data?.my_score,
      entries: entries.map((e) => ({
        rank: e.rank,
        userId: e.user_id,
        username: e.username,
        nickname: e.nickname,
        avatar: e.avatar,
        level: e.level,
        score: e.score,
        scoreLabel: e.score_label,
        extra: e.extra,
      })),
    };
  },

  // ========== 趣味内容 ==========

  /** 获取金句卡片列表 */
  async getQuoteCards(): Promise<QuoteCard[]> {
    if (USE_MOCK) return mockDelay(mockQuoteCards);
    const { data } = await apiClient.get("/content/quote-cards", { params: { page_size: 100 } });
    const items: any[] = data?.items ?? data ?? [];
    return items.map((c) => ({
      id: c.id,
      quote: c.quote,
      source: c.source,
      style: c.style,
      imageKeyword: c.image_keyword,
      backgroundImage: c.background_image || getQuoteBackgroundImage(c.id),
      likeCount: c.like_count,
      shareCount: c.share_count,
      createdAt: c.created_at,
    }));
  },

  /** 获取金句卡片详情 */
  async getQuoteCardDetail(cardId: string): Promise<QuoteCardDetail> {
    if (USE_MOCK) return mockDelay(mockQuoteCardDetail);
    const { data } = await apiClient.get(`/content/quote-cards/${cardId}`);
    const c = data;
    return {
      id: c.id,
      quote: c.quote,
      source: c.source,
      style: c.style,
      imageKeyword: c.image_keyword,
      backgroundImage: c.background_image || getQuoteBackgroundImage(c.id),
      likeCount: c.like_count,
      shareCount: c.share_count,
      createdAt: c.created_at,
      vernacular: c.vernacular,
      modernInterpretation: c.modern_interpretation,
      backgroundColor: c.background_color,
      accentColor: c.accent_color,
      tags: c.tags ?? [],
      isLiked: c.is_liked,
    };
  },

  /** 点赞金句卡片 */
  async likeQuoteCard(cardId: string): Promise<void> {
    if (USE_MOCK) return mockDelay(undefined as void);
    await apiClient.post(`/content/quote-cards/${cardId}/like`);
  },

  /** 获取小剧场列表 */
  async getTheaters(): Promise<Theater[]> {
    if (USE_MOCK) return mockDelay(mockTheaters);
    const { data } = await apiClient.get("/content/theater");
    const items: any[] = data?.items ?? data ?? [];
    return items.map((t) => ({
      id: t.id,
      title: t.title,
      summary: t.summary,
      classicalSource: t.classical_source,
      modernSetting: t.modern_setting,
      coverKeyword: t.cover_keyword,
      coverImage: t.cover_image ?? theaterCoverImages[t.id],
      sceneCount: t.scene_count,
      likeCount: t.like_count,
      viewCount: t.view_count,
      createdAt: t.created_at,
    }));
  },

  /** 获取小剧场详情 */
  async getTheaterDetail(theaterId: string): Promise<TheaterDetail> {
    if (USE_MOCK) return mockDelay(mockTheaterDetail);
    const { data } = await apiClient.get(`/content/theater/${theaterId}`);
    const t = data;
    return {
      id: t.id,
      title: t.title,
      summary: t.summary,
      classicalSource: t.classical_source,
      modernSetting: t.modern_setting,
      coverKeyword: t.cover_keyword,
      coverImage: t.cover_image ?? theaterCoverImages[t.id],
      sceneCount: t.scene_count,
      likeCount: t.like_count,
      viewCount: t.view_count,
      createdAt: t.created_at,
      roles: (t.roles ?? []).map((r: any, index: number) => ({
        name: r.name,
        description: r.description,
        classicalOrigin: r.classical_origin,
        avatarKeyword: r.avatar_keyword,
        portraitImage: r.avatar_image ?? r.portrait_image ?? theaterRolePortraitImages[`${t.id}:${index}`],
        objective: r.objective,
        fear: r.fear,
        belief: r.belief,
        strategy: r.strategy,
        conflictTrigger: r.conflict_trigger,
        stageAction: r.stage_action,
      })),
      scenes: (t.scenes ?? []).map((s: any) => ({
        title: s.title,
        setting: s.setting,
        lines: (s.lines ?? []).map((l: any) => ({
          role: l.role,
          text: l.text,
          emotion: l.emotion,
          beat: l.beat,
          action: l.action,
          subtext: l.subtext,
          pressure: l.pressure,
          isOriginalVerse: l.is_original_verse,
        })),
      })),
      moral: t.moral,
      tags: t.tags ?? [],
    };
  },

  // ========== 概念可视化 ==========

  /** 获取儒家核心概念列表 */
  async getConcepts(): Promise<Concept[]> {
    if (USE_MOCK) return mockDelay(mockConcepts);
    const { data } = await apiClient.get("/concepts");
    return data;
  },

  /** 获取单个概念详情 */
  async getConcept(conceptId: string): Promise<Concept> {
    if (USE_MOCK) {
      const concept = mockConcepts.find((c) => c.id === conceptId);
      if (!concept) throw new Error("Concept not found");
      return mockDelay(concept);
    }
    const { data } = await apiClient.get(`/concepts/${conceptId}`);
    return data;
  },

  // ========== 与圣贤对话 ==========

  /** 获取圣贤列表 */
  async getSages(): Promise<Sage[]> {
    if (USE_MOCK) return mockDelay(mockSages);
    const { data } = await apiClient.get("/sages");
    return data;
  },

  /** 获取圣贤详情 */
  async getSage(sageId: string): Promise<Sage> {
    if (USE_MOCK) {
      const sage = mockSages.find((s) => s.id === sageId);
      if (!sage) throw new Error("Sage not found");
      return mockDelay(sage);
    }
    const { data } = await apiClient.get(`/sages/${sageId}`);
    return data;
  },

  /**
   * 与圣贤对话（Mock 模式本地演绎生成）
   * 真实模式应通过 SSE 流式接口
   */
  async chatWithSage(
    sageId: string,
    message: string
  ): Promise<SageMessage> {
    if (USE_MOCK) {
      const reply = generateSageReply(sageId, message);
      return mockDelay({
        id: `sage-${Date.now()}`,
        role: "sage" as const,
        content: reply,
        timestamp: new Date().toISOString(),
      });
    }
    const { data } = await apiClient.post(`/sages/${sageId}/chat`, {
      message,
    });
    return data;
  },

  // ========== AI 智能讲解 ==========

  /**
   * 问AI逐句精讲
   * 后端 /api/ai/explain 返回 JSON（非SSE），包含翻译/背景/类比/反思等字段
   * 这里把各字段以"伪流式"方式分块回调，模拟打字机效果
   * @param verseId 经文 ID
   * @param original 原文
   * @param translation 译文（可选，作为 context 传给后端）
   * @param onChunk 每段文本回调（依次：翻译、背景、类比、反思）
   */
  async explainVerse(
    verseId: string,
    original: string,
    translation?: string,
    onChunk?: (text: string) => void
  ): Promise<{
    translation: string;
    background: string;
    modern_analogy: string;
    reflection: string;
    key_words: string[];
    confidence: number;
    disclaimer?: string | null;
  }> {
    // Mock 模式：本地生成简单讲解，并模拟流式回调
    if (USE_MOCK) {
      const mockResult = {
        translation:
          translation ||
          `此句意为：${original}。意在阐明修身待人之道，强调以德为本、以仁为行。`,
        background:
          "此章出自先秦典籍，时值礼崩乐坏之际，先贤忧世道之衰微，故立言以教化后人。其言简意深，承载着对理想人格与社会秩序的深切期许。",
        modern_analogy:
          "若以今日观之，犹如今日职场中强调的「以诚待人、以德服人」——真正的领导力不在于职位高低，而在于能否以自身品行赢得他人发自内心的尊重与追随。",
        reflection:
          "读此章当自省：我于日常待人接物，是否做到了真诚无伪？是否以德律己？经典之所以为经典，正因其能穿越时空，照见每一个时代的迷惘与出路。",
        key_words: ["仁", "德", "修身"],
        confidence: 0.92,
        disclaimer: null,
      };

      // 模拟流式：把每段拆成小块逐次回调
      if (onChunk) {
        const sections = [
          mockResult.translation,
          mockResult.background,
          mockResult.modern_analogy,
          mockResult.reflection,
        ];
        for (const section of sections) {
          const chunkSize = 6;
          for (let i = 0; i < section.length; i += chunkSize) {
            onChunk(section.slice(i, i + chunkSize));
            await new Promise((r) => setTimeout(r, 30));
          }
          onChunk("\n\n");
        }
      }
      return mockResult;
    }

    // 真实模式：POST /api/ai/explain 返回 JSON
    const { data } = await apiClient.post(`/ai/explain`, {
      verse_id: verseId,
      text: original,
      context: translation,
      depth: "standard",
    });

    const result = {
      translation: data.translation || "",
      background: data.background || "",
      modern_analogy: data.modern_analogy || "",
      reflection: data.reflection || "",
      key_words: data.key_words || [],
      confidence: data.confidence ?? 1.0,
      disclaimer: data.disclaimer,
    };

    // 真实接口非流式，但为统一前端体验，把完整结果分段回调
    if (onChunk) {
      const sections = [
        result.translation,
        result.background,
        result.modern_analogy,
        result.reflection,
      ];
      for (const section of sections) {
        onChunk(section);
        onChunk("\n\n");
      }
    }
    return result;
  },

  /**
   * AI 文白翻译
   * @param text 待翻译文本
   * @param direction 方向：to_modern 译为白话 / to_classical 译为文言
   */
  async aiTranslate(
    text: string,
    direction: "to_modern" | "to_classical" = "to_modern"
  ): Promise<string> {
    if (USE_MOCK) {
      const mock =
        direction === "to_modern"
          ? `「${text}」的白话译文：此句意指修身齐家、以德待人之理，强调君子当以仁义为本，言行一致，内省不疚。`
          : `「${text}」对应的文言表达：君子务本，本立而道生。`;
      return mockDelay(mock);
    }
    const { data } = await apiClient.post(`/ai/translate`, {
      text,
      direction,
    });
    return data.translated;
  },

  /**
   * 与圣贤对话（SSE 流式）
   * 后端 /api/ai/chat-sage stream=true 返回 SSE：
   *   - data: {"type":"chapters","chapters":[...]}\n\n   （检索到的篇章信息）
   *   - data: {"content":"..."}\n\n                       （流式文本片段）
   *   - data: [DONE]\n\n                                   （结束标记）
   * 用原生 fetch + ReadableStream 接收（axios 不支持流）
   * @returns 完整回复文本
   */
  async chatWithSageStream(
    sageId: string,
    message: string,
    onChunk?: (text: string) => void,
    history?: { role: "user" | "assistant"; content: string }[],
    onChapters?: (chapters: { name: string; source: string }[]) => void,
    onCitations?: (citations: Citation[]) => void
  ): Promise<string> {
    // Mock 模式：本地生成回复，模拟流式输出
    if (USE_MOCK) {
      // 模拟检索篇章（根据问题关键词随机选取）
      const mockChaptersPool = [
        { name: "学而篇", source: "《论语·学而》" },
        { name: "为政篇", source: "《论语·为政》" },
        { name: "里仁篇", source: "《论语·里仁》" },
        { name: "述而篇", source: "《论语·述而》" },
        { name: "卫灵公篇", source: "《论语·卫灵公》" },
        { name: "颜渊篇", source: "《论语·颜渊》" },
        { name: "子路篇", source: "《论语·子路》" },
        { name: "雍也篇", source: "《论语·雍也》" },
      ];
      const shuffled = [...mockChaptersPool].sort(() => Math.random() - 0.5);
      const mockChapters = shuffled.slice(0, 3);
      if (onChapters) {
        onChapters(mockChapters);
      }
      // 模拟检索延迟
      await new Promise((r) => setTimeout(r, 800));

      const fullReply = generateSageReply(sageId, message);
      if (onChunk) {
        const chunkSize = 2;
        for (let i = 0; i < fullReply.length; i += chunkSize) {
          onChunk(fullReply.slice(i, i + chunkSize));
          await new Promise((r) => setTimeout(r, 40));
        }
      }
      // 模拟思想依据引用（根据圣贤选择不同引用集）
      if (onCitations) {
        const citationsPool: Record<string, Citation[]> = {
          confucius: [
            { text: "人不知而不愠，不亦君子乎", source: "《论语·学而》", chapter: "学而篇", verse_no: 1, similarity: 0.95, type: "verse" },
            { text: "不患人之不己知，患不知人也", source: "《论语·学而》", chapter: "学而篇", verse_no: 16, similarity: 0.88, type: "verse" },
            { text: "工欲善其事，必先利其器", source: "《论语·卫灵公》", chapter: "卫灵公篇", verse_no: 10, similarity: 0.82, type: "verse" },
            { text: "过则勿惮改", source: "《论语·学而》", chapter: "学而篇", verse_no: 8, similarity: 0.78, type: "verse" },
          ],
          mencius: [
            { text: "富贵不能淫，贫贱不能移，威武不能屈", source: "《孟子·滕文公下》", chapter: "滕文公下", verse_no: 2, similarity: 0.93, type: "verse" },
            { text: "我善养吾浩然之气", source: "《孟子·公孙丑上》", chapter: "公孙丑上", verse_no: 2, similarity: 0.87, type: "verse" },
            { text: "恻隐之心，仁之端也", source: "《孟子·公孙丑上》", chapter: "公孙丑上", verse_no: 6, similarity: 0.81, type: "verse" },
          ],
          wang_yangming: [
            { text: "知者行之始，行者知之成", source: "《传习录》", chapter: "卷上", verse_no: 5, similarity: 0.91, type: "verse" },
            { text: "致良知", source: "《传习录》", chapter: "卷下", verse_no: 12, similarity: 0.86, type: "verse" },
            { text: "心外无物，心外无理", source: "《传习录》", chapter: "卷上", verse_no: 3, similarity: 0.79, type: "verse" },
          ],
          laozi: [
            { text: "道可道，非常道；名可名，非常名", source: "《道德经·第一章》", chapter: "第一章", verse_no: 1, similarity: 0.94, type: "verse" },
            { text: "上善若水，水善利万物而不争", source: "《道德经·第八章》", chapter: "第八章", verse_no: 8, similarity: 0.89, type: "verse" },
            { text: "知人者智，自知者明", source: "《道德经·第三十三章》", chapter: "第三十三章", verse_no: 33, similarity: 0.84, type: "verse" },
          ],
          mozi: [
            { text: "兼相爱，交相利", source: "《墨子·兼爱上》", chapter: "兼爱上", verse_no: 1, similarity: 0.93, type: "verse" },
            { text: "兴天下之利，除天下之害", source: "《墨子·兼爱中》", chapter: "兼爱中", verse_no: 2, similarity: 0.87, type: "verse" },
            { text: "言必信，行必果", source: "《墨子·兼爱下》", chapter: "兼爱下", verse_no: 3, similarity: 0.82, type: "verse" },
          ],
          hanfeizi: [
            { text: "法不阿贵，绳不挠曲", source: "《韩非子·有度》", chapter: "有度", verse_no: 1, similarity: 0.92, type: "verse" },
            { text: "刑过不避大臣，赏善不遗匹夫", source: "《韩非子·有度》", chapter: "有度", verse_no: 2, similarity: 0.86, type: "verse" },
            { text: "事在四方，要在中央", source: "《韩非子·扬权》", chapter: "扬权", verse_no: 1, similarity: 0.80, type: "verse" },
          ],
        };
        onCitations(citationsPool[sageId] || citationsPool.confucius);
      }
      return fullReply;
    }

    // 真实模式：fetch + SSE
    const response = await fetch(`${API_BASE}/ai/chat-sage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        sage: sageId,
        question: message,
        history: history || [],
        stream: true,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`chat-sage 请求失败: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let fullText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按 SSE 事件分隔解析
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // 保留最后不完整的一行

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;

        const payload = trimmed.slice(5).trim();
        if (payload === "[DONE]") {
          return fullText;
        }
        try {
          const parsed = JSON.parse(payload);
          if (parsed.error) {
            throw new Error(parsed.error);
          }
          // 检索篇章事件
          if (parsed.type === "chapters" && Array.isArray(parsed.chapters)) {
            onChapters?.(parsed.chapters);
          }
          // 思想依据引用事件
          if (parsed.type === "citations" && Array.isArray(parsed.citations)) {
            onCitations?.(parsed.citations);
          }
          // 流式文本内容
          if (parsed.content) {
            fullText += parsed.content;
            onChunk?.(parsed.content);
          }
        } catch {
          // 非 JSON 行，跳过
        }
      }
    }

    return fullText;
  },

  // ========== 漫画解读 ==========

  /** 获取漫画列表 */
  async getComics(): Promise<Comic[]> {
    if (USE_MOCK) return mockDelay(mockComics);
    const { data } = await apiClient.get("/content/comics");
    const items: any[] = data?.items ?? data ?? [];
    return items.map((c) => ({
      id: c.id,
      title: c.title,
      source_verse: c.classical_source ?? c.source_verse ?? "",
      logline: c.summary ?? c.logline ?? "",
      styleGuide: c.style_guide ?? c.styleGuide ?? "",
      characters: c.characters ?? [],
      panels: [],
    }));
  },

  /** 获取漫画详情 */
  async getComicDetail(comicId: string): Promise<Comic> {
    if (USE_MOCK) {
      const comic = mockComics.find((c) => c.id === comicId);
      if (!comic) throw new Error("Comic not found");
      return mockDelay(comic);
    }
    const { data } = await apiClient.get(`/content/comics/${comicId}`);
    const c = data;
    return {
      id: c.id,
      title: c.title,
      source_verse: c.classical_source ?? c.source_verse ?? "",
      logline: c.summary ?? c.logline ?? "",
      styleGuide: c.style_guide ?? c.styleGuide ?? "",
      characters: (c.characters ?? []).map((character: any) => ({
        name: character.name ?? "",
        role: character.role ?? "",
        description: character.description ?? "",
        visualAnchor: character.visual_anchor ?? character.visualAnchor ?? "",
      })),
      panels: (c.panels ?? []).map((p: any) => ({
        scene: p.scene ?? p.caption ?? "",
        shot: p.shot ?? "",
        action: p.action ?? "",
        dialogue: p.dialogue ?? p.verse ?? "",
        caption: p.caption ?? "",
        character: p.character ?? "",
        emotion: p.emotion ?? "",
        knowledgeAnchor: p.knowledge_anchor ?? p.knowledgeAnchor ?? "",
        visualMetaphor: p.visual_metaphor ?? p.visualMetaphor ?? "",
        beat: p.beat ?? "",
        imageUrl: p.image_url ?? p.imageUrl ?? "",
        imagePrompt: p.image_prompt ?? p.imagePrompt ?? p.image_keyword ?? "",
      })),
    };
  },

  // ========== 经典闯关 ==========

  /** 获取闯关关卡列表 */
  async getChallengeLevels(): Promise<ChallengeLevel[]> {
    if (USE_MOCK) return mockDelay(generateChallengeLevels());
    // 后端 GET /learning/chapter-tree 返回 APIResponse{code,message,data:{books:[BookTreeNode]}}
    // BookTreeNode.chapters = ChapterTreeNode{chapter_id, chapter_number, title, verse_count, completed_count, is_unlocked, is_completed, progress_pct}
    const { data: resp } = await apiClient.get("/learning/chapter-tree");
    const books: any[] = resp?.data?.books ?? resp?.books ?? [];
    const allChapters: any[] = books.flatMap((b) => b.chapters ?? []);
    return allChapters.map((c) => ({
      id: String(c.chapter_id),
      chapterId: String(c.chapter_id),
      title: c.title,
      order: c.chapter_number ?? 0,
      sentenceCount: c.verse_count ?? 0,
      locked: !c.is_unlocked,
      passed: !!c.is_completed,
      bestScore: c.progress_pct != null ? Math.round(c.progress_pct) : undefined,
      stars: c.is_completed ? 3 : 0,
    }));
  },

  /** 获取某关卡的题目 */
  async getChallengeQuestions(chapterId: string): Promise<ChallengeQuestion[]> {
    if (USE_MOCK) {
      // 本地基于经文生成题目， verseId 使用字符串以匹配前端数据
      const questions = generateQuestionsForLevel(chapterId);
      return mockDelay(questions.map((q) => ({ ...q, verseId: String(q.verseId) })));
    }
    // 后端 GET /learning/quiz/{verse_id} 返回 APIResponse{code,message,data:{items:[QuizItem]}}
    // QuizItem{quiz_id, verse_id, question_type, difficulty, question, options}
    const verseId = Number(chapterId);
    const { data: resp } = await apiClient.get(`/learning/quiz/${verseId}`, {
      params: { count: 10 },
    });
    const items: any[] = resp?.data?.items ?? resp?.items ?? [];
    return items.map((q) => ({
      quizId: q.quiz_id,
      verseId: String(q.verse_id),
      questionType: q.question_type ?? "choice",
      difficulty: q.difficulty ?? 1,
      question: q.question,
      options: Array.isArray(q.options)
        ? q.options.map((o: any, i: number) =>
            typeof o === "string"
              ? { index: i, text: o }
              : { index: o.index ?? i, text: o.text }
          )
        : undefined,
    }));
  },

  /** 提交闯关答案 */
  async submitChallengeAnswers(
    chapterId: string,
    answers: ChallengeAnswer[],
    questions: ChallengeQuestion[]
  ): Promise<ChallengeResult> {
    if (USE_MOCK) {
      const result = judgeLocalAnswers(questions, answers);
      return mockDelay(result);
    }
    // 后端 POST /learning/quiz/submit 返回 APIResponse{code,message,data:{total, correct_count, wrong_count, score, passed, pass_threshold, total_time, results, exp_gained,...}}
    const { data: resp } = await apiClient.post("/learning/quiz/submit", {
      verse_id: Number(chapterId),
      answers: answers.map((a) => ({
        quiz_id: a.quizId,
        user_answer: a.userAnswer,
        time_spent: a.timeSpent,
      })),
    });
    const d = resp?.data ?? resp;
    return {
      total: d?.total ?? 0,
      correctCount: d?.correct_count ?? 0,
      wrongCount: d?.wrong_count ?? 0,
      score: d?.score ?? 0,
      passed: !!d?.passed,
      passThreshold: d?.pass_threshold ?? 60,
      totalTime: d?.total_time ?? 0,
      results: (d?.results ?? []).map((r: any) => ({
        quizId: r.quiz_id,
        isCorrect: !!r.is_correct,
        correctAnswer: r.correct_answer,
        explanation: r.explanation ?? "",
      })),
      expGained: d?.exp_gained,
    };
  },

  // ========== SRS 间隔复习 ==========

  /** 获取今日待复习经文 */
  async getDueReviews(): Promise<DueReviewsResponse> {
    if (USE_MOCK) {
      const items = [
        {
          record_id: 1,
          verse_id: "1.1.1",
          original_text: "学而时习之，不亦说乎？",
          translation: "学习了知识并按时温习，不也是很愉快吗？",
          repetitions: 2,
          ease_factor: 2.5,
          interval_days: 3,
          next_review_date: new Date().toISOString().slice(0, 10),
        },
        {
          record_id: 2,
          verse_id: "1.1.2",
          original_text: "有朋自远方来，不亦乐乎？",
          translation: "有朋友从远方到来，不也是很快乐吗？",
          repetitions: 1,
          ease_factor: 2.3,
          interval_days: 1,
          next_review_date: new Date().toISOString().slice(0, 10),
        },
        {
          record_id: 3,
          verse_id: "1.1.3",
          original_text: "人不知而不愠，不亦君子乎？",
          translation: "别人不了解自己却不怨恨，不也是君子吗？",
          repetitions: 3,
          ease_factor: 2.6,
          interval_days: 7,
          next_review_date: new Date().toISOString().slice(0, 10),
        },
        {
          record_id: 4,
          verse_id: "1.2.1",
          original_text: "其为人也孝弟，而好犯上者，鲜矣。",
          translation: "一个人孝顺父母、敬爱兄长，却喜欢冒犯长辈，是很少见的。",
          repetitions: 1,
          ease_factor: 2.2,
          interval_days: 1,
          next_review_date: new Date().toISOString().slice(0, 10),
        },
        {
          record_id: 5,
          verse_id: "1.4.1",
          original_text: "吾日三省吾身。",
          translation: "我每天多次反省自己。",
          repetitions: 4,
          ease_factor: 2.7,
          interval_days: 14,
          next_review_date: new Date().toISOString().slice(0, 10),
        },
      ];
      return mockDelay({ due_count: items.length, items });
    }
    const { data: resp } = await apiClient.get("/learning/due-reviews");
    // 后端返回 APIResponse{code,message,data:{due_count, items}}
    return resp?.data ?? resp;
  },

  /** 提交单条复习结果 */
  async submitReview(
    verseId: string,
    quality: number,
    hesitationSeconds?: number
  ): Promise<{ success: boolean; next_review_date: string; interval_days: number }> {
    if (USE_MOCK) {
      const intervals: Record<number, number> = { 5: 7, 4: 4, 3: 2, 2: 1, 1: 1, 0: 0 };
      const interval = intervals[quality] ?? 1;
      const next = new Date();
      next.setDate(next.getDate() + interval);
      return mockDelay({
        success: true,
        next_review_date: next.toISOString().slice(0, 10),
        interval_days: interval,
      });
    }
    const { data: resp } = await apiClient.post("/learning/review", {
      verse_id: verseId,
      quality,
      hesitation_seconds: hesitationSeconds,
    });
    // 后端返回 APIResponse{code,message,data:{verse_id, repetitions, ease_factor, interval_days, next_review_at,...}}
    const d = resp?.data ?? resp;
    return {
      success: true,
      next_review_date: d?.next_review_at ?? d?.next_review_date,
      interval_days: d?.interval_days,
    };
  },

  /** 获取复习统计 */
  async getReviewStats(): Promise<ReviewStats> {
    if (USE_MOCK) {
      return mockDelay({
        total_reviewed: 156,
        mastered_count: 42,
        learning_count: 38,
        today_reviewed: 5,
        today_correct: 4,
        streak_days: 7,
        retention_rate: 0.85,
      });
    }
    const { data: resp } = await apiClient.get("/learning/review-stats");
    // 后端返回 APIResponse{code,message,data:{due_count, mastered_count, learning_count, reviewed_today,...}}
    return resp?.data ?? resp;
  },

  // ========== 成就与段位 ==========

  /** 获取成就列表 */
  async getAchievements(): Promise<AchievementsResponse> {
    if (USE_MOCK) {
      const unlocked: Achievement[] = [
        {
          id: 1,
          code: "first_read",
          name: "初窥门径",
          description: "完成第一次经文阅读",
          icon: "BookOpen",
          category: "学习",
          unlocked: true,
          unlocked_at: "2026-05-01T10:00:00Z",
          condition: "阅读任意经文 1 次",
        },
        {
          id: 2,
          code: "streak_7",
          name: "七日不辍",
          description: "连续学习 7 天",
          icon: "Flame",
          category: "坚持",
          unlocked: true,
          unlocked_at: "2026-05-08T10:00:00Z",
          condition: "连续打卡 7 天",
        },
        {
          id: 3,
          code: "challenge_first",
          name: "初试锋芒",
          description: "完成第一次闯关",
          icon: "Sword",
          category: "闯关",
          unlocked: true,
          unlocked_at: "2026-05-10T14:00:00Z",
          condition: "通过任意关卡 1 次",
        },
        {
          id: 4,
          code: "review_100",
          name: "温故知新",
          description: "累计复习 100 次经文",
          icon: "RefreshCw",
          category: "复习",
          unlocked: true,
          unlocked_at: "2026-06-01T09:00:00Z",
          condition: "累计复习 100 次",
        },
      ];
      const locked: Achievement[] = [
        {
          id: 5,
          code: "streak_30",
          name: "月不间断",
          description: "连续学习 30 天",
          icon: "Calendar",
          category: "坚持",
          unlocked: false,
          condition: "连续打卡 30 天",
        },
        {
          id: 6,
          code: "master_analects",
          name: "论语通儒",
          description: "学完《论语》全部章节",
          icon: "GraduationCap",
          category: "阅读",
          unlocked: false,
          condition: "完成《论语》全部 20 篇",
        },
        {
          id: 7,
          code: "pk_master",
          name: "论道魁首",
          description: "PK 累计胜场达 10 次",
          icon: "Crown",
          category: "社区",
          unlocked: false,
          condition: "PK 胜场达到 10 次",
        },
        {
          id: 8,
          code: "note_essence",
          name: "锦绣文章",
          description: "笔记被评为精华 5 次",
          icon: "Feather",
          category: "社区",
          unlocked: false,
          condition: "笔记被设为精华 5 次",
        },
        {
          id: 9,
          code: "sage_chat_50",
          name: "问道达人",
          description: "与圣贤对话累计 50 次",
          icon: "MessageCircle",
          category: "互动",
          unlocked: false,
          condition: "与圣贤对话 50 次",
        },
        {
          id: 10,
          code: "all_books",
          name: "博学鸿儒",
          description: "阅读全部四书五经",
          icon: "Library",
          category: "阅读",
          unlocked: false,
          condition: "阅读全部 9 部经典",
        },
      ];
      return mockDelay({ unlocked, locked, exp: 1280, level: 6 });
    }
    const { data: resp } = await apiClient.get("/learning/achievements");
    // 后端返回 APIResponse{code,message,data:{total, unlocked_count, achievements:[...]}}
    return resp?.data ?? resp;
  },

  /** 获取段位信息 */
  async getRank(): Promise<RankInfo> {
    if (USE_MOCK) {
      return mockDelay({
        current_rank: 3,
        rank_name: "举人",
        exp: 1280,
        next_rank: 4,
        next_rank_name: "进士",
        progress: 0.64,
      });
    }
    const { data: resp } = await apiClient.get("/learning/rank");
    // 后端返回 APIResponse{code,message,data:{current_rank, next_rank, exp, exp_to_next, progress_pct, all_ranks}}
    return resp?.data ?? resp;
  },

  /** 获取学习排行榜 */
  async getLearningLeaderboard(
    scope: "week" | "month" | "all" = "week"
  ): Promise<LeaderboardData> {
    if (USE_MOCK) {
      const entries = [
        { rank: 1, userId: 1, username: "zhangsan", nickname: "子曰", level: 12, score: 3200, scoreLabel: "3200 经验" },
        { rank: 2, userId: 2, username: "lisi", nickname: "三省吾身", level: 10, score: 2800, scoreLabel: "2800 经验" },
        { rank: 3, userId: 3, username: "wangwu", nickname: "温故知新", level: 9, score: 2500, scoreLabel: "2500 经验" },
        { rank: 4, userId: 4, username: "zhaoliu", nickname: "学而时习", level: 8, score: 2100, scoreLabel: "2100 经验" },
        { rank: 5, userId: 5, username: "qianqi", nickname: "敏而好学", level: 7, score: 1800, scoreLabel: "1800 经验" },
        { rank: 6, userId: 6, username: "sunba", nickname: "不耻下问", level: 6, score: 1500, scoreLabel: "1500 经验" },
        { rank: 7, userId: 7, username: "zhoujiu", nickname: "笃信好学", level: 6, score: 1280, scoreLabel: "1280 经验" },
        { rank: 8, userId: 8, username: "wushi", nickname: "切问近思", level: 5, score: 1100, scoreLabel: "1100 经验" },
        { rank: 9, userId: 9, username: "chengshi", nickname: "博学笃志", level: 5, score: 950, scoreLabel: "950 经验" },
        { rank: 10, userId: 10, username: "meione", nickname: "慎思明辨", level: 4, score: 800, scoreLabel: "800 经验" },
      ].map((e) => ({ ...e, avatar: undefined, extra: undefined }));
      return mockDelay({
        scope,
        metric: "exp",
        myRank: 7,
        myScore: 1280,
        entries,
      });
    }
    const { data: resp } = await apiClient.get("/learning/leaderboard", {
      params: { scope },
    });
    // 后端返回 APIResponse{code,message,data:{scope, items:[LeaderboardItem]}}
    const d = resp?.data ?? resp;
    const items: any[] = d?.items ?? [];
    return {
      scope,
      metric: "exp",
      myRank: d?.my_rank,
      myScore: d?.my_score,
      entries: items.map((e) => ({
        rank: e.rank,
        userId: e.user_id,
        username: e.username,
        nickname: e.nickname,
        avatar: e.avatar,
        level: e.level,
        score: e.exp ?? e.score ?? 0,
        scoreLabel: e.rank_name ? `段位：${e.rank_name}` : "",
        extra: undefined,
      })),
    };
  },

  // ========== 认证 ==========

  /** 登录 */
  async login(username: string, password: string): Promise<AuthResponse> {
    if (USE_MOCK) {
      return mockDelay({
        access_token: "mock_access_token_" + Date.now(),
        refresh_token: "mock_refresh_token_" + Date.now(),
        token_type: "bearer",
        user: {
          id: 1,
          username,
          email: `${username}@wudian.com`,
          nickname: username,
          level: 6,
          exp: 1280,
        },
      });
    }
    const { data } = await apiClient.post("/auth/login", { username, password });
    if (data?.access_token) {
      setToken(data.access_token, data.refresh_token, data.user);
    }
    return data;
  },

  /** 注册 */
  async register(
    username: string,
    email: string,
    password: string,
    nickname?: string
  ): Promise<AuthResponse> {
    if (USE_MOCK) {
      return mockDelay({
        access_token: "mock_access_token_" + Date.now(),
        refresh_token: "mock_refresh_token_" + Date.now(),
        token_type: "bearer",
        user: {
          id: Math.floor(Math.random() * 1000) + 100,
          username,
          email,
          nickname: nickname || username,
          level: 1,
          exp: 0,
        },
      });
    }
    const { data } = await apiClient.post("/auth/register", {
      username,
      email,
      password,
      nickname,
    });
    if (data?.access_token) {
      setToken(data.access_token, data.refresh_token, data.user);
    }
    return data;
  },

  /** 获取当前用户信息 */
  async getCurrentUser(): Promise<UserInfo> {
    if (USE_MOCK) {
      const token = typeof window !== "undefined" ? localStorage.getItem("wudian_access_token") : null;
      if (!token) throw new Error("未登录");
      return mockDelay({
        id: 1,
        username: "demo",
        email: "demo@wudian.com",
        nickname: "示范学者",
        level: 6,
        exp: 1280,
      });
    }
    const { data } = await apiClient.get("/auth/me");
    return data;
  },





  /** 获取影像底本外链平台列表 */
  async getImageSources(): Promise<ImageSource[]> {
    if (USE_MOCK) return mockDelay(mockImageSources);
    const { data } = await apiClient.get("/reader/image-sources");
    return data;
  },

  // ========== 百家论道 ==========

  /** 开始辩论 */
  async startDebate(topic: string, sages?: string[]): Promise<{
    sessionId: string;
    topic: string;
    participants: string[];
    phase: string;
    message: string;
  }> {
    if (USE_MOCK) {
      return mockDelay({
        sessionId: `debate-${Date.now()}`,
        topic,
        participants: sages || ["confucius", "laozi", "mozi", "hanfeizi"],
        phase: "init",
        message: "辩论会话已创建",
      });
    }
    const { data } = await apiClient.post("/debate/start", { topic, sages });
    return {
      sessionId: data.session_id,
      topic: data.topic,
      participants: data.participants,
      phase: data.phase,
      message: data.message,
    };
  },

  /** 进入下一轮辩论（非流式） */
  async nextDebateRound(sessionId: string): Promise<any> {
    if (USE_MOCK) {
      return mockDelay({ sessionId, round: {}, phase: "round2", canContinue: true });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/next-round?stream=false`);
    return data;
  },

  /** 用户介入辩论 */
  async interveneDebate(sessionId: string, content: string, targetSage?: string): Promise<any> {
    if (USE_MOCK) {
      return mockDelay({ sessionId, speech: {}, phase: "intervention" });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/intervene?stream=false`, {
      content,
      target_sage: targetSage,
    });
    return data;
  },

  /** 论主站队 */
  async standDebate(sessionId: string, stance: string, targetSage?: string): Promise<{
    sessionId: string;
    speech: any;
    round: any;
    phase: string;
  }> {
    if (USE_MOCK) {
      const sageKey = targetSage || "confucius";
      return mockDelay({
        sessionId,
        speech: {
          sage_key: sageKey,
          round_number: 3,
          content: `站队回应：${stance}`,
          target_sage: sageKey,
          citations: [],
        },
        round: {
          round_type: "stance",
          speeches: [
            {
              sage_key: sageKey,
              round_number: 3,
              content: `站队回应：${stance}`,
              target_sage: sageKey,
              citations: [],
            },
          ],
          clashes: [],
        },
        phase: "intervention",
      });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/stand`, {
      stance,
      target_sage: targetSage,
    });
    return {
      sessionId: data.session_id,
      speech: data.speech,
      round: data.round,
      phase: data.phase,
    };
  },

  /** 请其互问 */
  async mutualQuestion(
    sessionId: string,
    fromSage: string,
    toSage: string,
    question?: string
  ): Promise<{
    sessionId: string;
    question: any;
    answer: any;
    round: any;
    phase: string;
  }> {
    if (USE_MOCK) {
      return mockDelay({
        sessionId,
        question: {
          sage_key: fromSage,
          round_number: 3,
          content: "互问：请回应我的分歧。",
          target_sage: toSage,
          citations: [],
        },
        answer: {
          sage_key: toSage,
          round_number: 3,
          content: "互答：我从本派经典回应。",
          target_sage: fromSage,
          citations: [],
        },
        round: {
          round_type: "mutual_question",
          speeches: [
            { sage_key: fromSage, round_number: 3, content: "互问：请回应我的分歧。", target_sage: toSage, citations: [] },
            { sage_key: toSage, round_number: 3, content: "互答：我从本派经典回应。", target_sage: fromSage, citations: [] },
          ],
          clashes: [{ from_sage: fromSage, to_sage: toSage, clash_type: "extend", summary: "独立互问回合" }],
        },
        phase: "intervention",
      });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/mutual-question`, {
      from_sage: fromSage,
      to_sage: toSage,
      question,
    });
    return {
      sessionId: data.session_id,
      question: data.question,
      answer: data.answer,
      round: data.round,
      phase: data.phase,
    };
  },

  /** 踢馆名人花名册 */
  async getGuestRoster(): Promise<GuestRosterItem[]> {
    if (USE_MOCK) {
      return mockDelay(normalizeGuestRoster([
        { sage_key: "li_bai", sage_name: "李白", unlocked: true, collected: false, staying: false },
        { sage_key: "su_shi", sage_name: "苏轼", unlocked: true, collected: false, staying: false },
        { sage_key: "zhuge_liang", sage_name: "诸葛亮", unlocked: true, collected: false, staying: false },
      ]));
    }
    const { data } = await apiClient.get("/debate/guests/roster");
    return normalizeGuestRoster(data.guests);
  },

  /** 随机触发踢馆 */
  async randomGuest(sessionId: string): Promise<{
    sessionId: string;
    sageKey: string;
    speech: any;
    reactionRound?: any;
    phase: string;
    triggeredRandomly: boolean;
  }> {
    if (USE_MOCK) {
      return mockDelay({
        sessionId,
        sageKey: "li_bai",
        speech: { sage_key: "li_bai", sage_name: "李白", content: "随机踢馆发言", is_guest: true },
        reactionRound: undefined,
        phase: "intervention",
        triggeredRandomly: true,
      });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/guests/random`);
    return {
      sessionId: data.session_id,
      sageKey: data.sage_key,
      speech: data.speech,
      reactionRound: data.reaction_round,
      phase: data.phase,
      triggeredRandomly: data.triggered_randomly,
    };
  },

  /** 踢馆名人留下或离去 */
  async decideGuest(sessionId: string, sageKey: string, decision: "stay" | "leave"): Promise<any> {
    if (USE_MOCK) {
      return mockDelay({ sessionId, sageKey, staying: decision === "stay", guest: { sage_key: sageKey, collected: decision === "stay" }, participants: [] });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/guests/${sageKey}/decision`, { decision });
    return data;
  },

  /** 召唤踢馆名人 */
  async summonGuest(sessionId: string, sageKey: string): Promise<{
    sessionId: string;
    sageKey: string;
    speech: any;
    reactionRound?: any;
    phase: string;
  }> {
    if (USE_MOCK) {
      return mockDelay({
        sessionId,
        sageKey,
        speech: { sage_key: sageKey, sage_name: sageKey, content: "Mock踢馆发言" },
        reactionRound: undefined,
        phase: "intervention",
      });
    }
    const { data } = await apiClient.post(`/debate/${sessionId}/summon`, { sage_key: sageKey });
    return {
      sessionId: data.session_id,
      sageKey: data.sage_key,
      speech: data.speech,
      reactionRound: data.reaction_round,
      phase: data.phase,
    };
  },

  /** 获取会诊报告 */
  async getDebateReport(sessionId: string): Promise<any> {
    if (USE_MOCK) {
      return mockDelay({
        sessionId,
        report: { topic: "Mock话题", consensus: [], divergences: [], recommendations: [], summary: "" },
        phase: "done",
      });
    }
    const { data } = await apiClient.get(`/debate/${sessionId}/report`);
    return data;
  },

  /** 后端思想坐标定位 */
  async analyzeThoughtCompass(statement: string): Promise<ThoughtCompassMark> {
    if (USE_MOCK) {
      const { analyzeThoughtCompass } = await import("./thoughtCompass");
      return mockDelay(analyzeThoughtCompass(statement));
    }
    const { data } = await apiClient.post("/debate/thought-compass", { statement });
    return normalizeBackendThoughtCompass(data);
  },

  /** 获取辩论会话状态 */
  async getDebateSession(sessionId: string): Promise<any> {
    if (USE_MOCK) {
      return mockDelay({ id: sessionId, topic: "Mock", phase: "init", participants: [], rounds: [] });
    }
    const { data } = await apiClient.get(`/debate/${sessionId}/session`);
    return data;
  },

  async getDebateStateGraph(sessionId: string): Promise<DebateStateGraphView> {
    if (USE_MOCK) {
      return mockDelay(normalizeDebateStateGraph({
        session_id: sessionId,
        current_node: "round2",
        nodes: [
          { id: "init", label: "开场建局", kind: "start" },
          { id: "round1", label: "各陈己见", kind: "agent_round" },
          { id: "round2", label: "交锋辩驳", kind: "agent_round" },
          { id: "intervention", label: "论主介入", kind: "human_agent" },
          { id: "report", label: "主持会诊", kind: "moderator" },
          { id: "done", label: "收束完成", kind: "terminal" },
        ],
        transitions: [
          { from_node: "init", to_node: "round1", action: "run_round1_each_opinion" },
          { from_node: "round1", to_node: "round2", action: "run_round2_cross_debate" },
          { from_node: "round2", to_node: "intervention", action: "run_round2_cross_debate" },
          { from_node: "intervention", to_node: "report", action: "generate_report" },
          { from_node: "report", to_node: "done", action: "return_report" },
        ],
        trace: [{ from_node: "init", to_node: "round1", action: "run_round1_each_opinion", ok: true }],
      }));
    }
    const { data } = await apiClient.get(`/debate/${sessionId}/state-graph`);
    return normalizeDebateStateGraph(data);
  },

  /** 获取预设话题列表 */
  async getDebatePresets(): Promise<{ id: string; topic: string; tags: string[] }[]> {
    if (USE_MOCK) {
      return mockDelay([
        { id: "t1", topic: "人性本善还是本恶？", tags: ["人性", "伦理"] },
        { id: "t2", topic: "何为真正的勇气？", tags: ["勇气", "修身"] },
        { id: "t3", topic: "治国应以德还是以法？", tags: ["政治", "治国"] },
        { id: "t4", topic: "面对不公，该沉默还是发声？", tags: ["正义", "处世"] },
        { id: "t5", topic: "君子应该如何对待金钱？", tags: ["金钱", "义利"] },
        { id: "t6", topic: "知易行难，如何做到知行合一？", tags: ["知行", "实践"] },
      ]);
    }
    const { data } = await apiClient.get("/debate/presets");
    return data.topics;
  },

  /** 获取辩论历史列表 */
  async getDebateHistory(limit = 20): Promise<any[]> {
    if (USE_MOCK) {
      return mockDelay([]);
    }
    const { data } = await apiClient.get("/debate/history", { params: { limit } });
    return data.sessions;
  },

  /**
   * 辩论SSE流式调用
   * @param sessionId 会话ID
   * @param action 动作：next-round 或 intervene
   * @param payload 请求体（intervene时需要）
   * @param onChunk 数据回调
   * @returns 
   */
  async debateStream(
    sessionId: string,
    action: "next-round" | "intervene",
    payload?: any,
    onChunk?: (data: any) => void
  ): Promise<void> {
    if (USE_MOCK) {
      if (action === "intervene") {
        onChunk?.({
          type: "sage_start",
          sage_key: payload?.target_sage || "confucius",
          sage_name: "孔子",
          round: 3,
        });
        onChunk?.({
          type: "sage_chunk",
          sage_key: payload?.target_sage || "confucius",
          content: "孔子答论主曰：汝之追问，正在进退之间。暂退可以养志，弃志则不可。",
        });
        onChunk?.({
          type: "sage_end",
          sage_key: payload?.target_sage || "confucius",
          speech: {
            sage_key: payload?.target_sage || "confucius",
            sage_name: "孔子",
            round_number: 3,
            content: "孔子答论主曰：汝之追问，正在进退之间。暂退可以养志，弃志则不可。",
            quote: "士不可以不弘毅，任重而道远。",
            source: "《论语·泰伯》",
            citations: [{ id: "引1", source: "《论语·泰伯》", original: "士不可以不弘毅，任重而道远。", verifiable: true }],
          },
        });
        return mockDelay(undefined as void, 120);
      }

      const { getMockDebateData } = await import("./roundtableData");
      const mockData = getMockDebateData("我该不该躺平？");
      const round = (mockDebateRoundCounters.get(sessionId) || 0) + 1;
      mockDebateRoundCounters.set(sessionId, round);
      for (const speech of mockData.speeches.slice(0, 4)) {
        onChunk?.({ type: "sage_start", sage_key: speech.sageId, round });
        onChunk?.({ type: "sage_chunk", sage_key: speech.sageId, content: speech.content });
        onChunk?.({
          type: "sage_end",
          sage_key: speech.sageId,
          speech: {
            sage_key: speech.sageId,
            round_number: round,
            content: speech.content,
            quote: speech.citations[0]?.text || "无",
            source: speech.citations[0]?.source || "无",
            citations: speech.citations.map((citation, idx) => ({
              id: `引${idx + 1}`,
              source: citation.source,
              original: citation.text,
              verifiable: true,
            })),
          },
        });
      }
      if (round === 2) {
        onChunk?.({
          type: "round_done",
          round,
          clashes: mockData.clashes.map((clash) => ({
            from_sage: clash.fromSageId,
            to_sage: clash.toSageId,
            clash_type: clash.type === "reframe" ? "extend" : clash.type,
            summary: clash.summary,
          })),
        });
      } else {
        onChunk?.({ type: "round_done", round });
      }
      return mockDelay(undefined as void, 120);
    }

    const url = `${API_BASE}/debate/${sessionId}/${action}?stream=true`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: payload ? JSON.stringify(payload) : undefined,
    });

    if (!response.ok || !response.body) {
      throw new Error(`debate stream 请求失败: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;

        const payload = trimmed.slice(5).trim();
        if (payload === "[DONE]") return;

        try {
          const parsed = JSON.parse(payload);
          onChunk?.(parsed);
        } catch {
          // 非JSON行，跳过
        }
      }
    }
  },

  // ========== 快速答题 & 每日一句卡 ==========

  /**
   * 获取每日一句卡片数据
   * Mock 模式使用本地精选库；真实模式调后端 daily-quote 接口
   */
  async getDailyQuoteCard(): Promise<{
    id: string;
    text: string;
    translation: string;
    source: string;
  }> {
    if (USE_MOCK) {
      const { getDailyQuoteByDate } = await import("./quizData");
      return mockDelay(getDailyQuoteByDate());
    }
    try {
      const { data } = await apiClient.get("/classics/daily-quote");
      return {
        id: data?.id ?? `dq-${Date.now()}`,
        text: data?.text ?? "",
        translation: data?.translation ?? "",
        source: data?.source ?? "",
      };
    } catch {
      // 兜底：用本地数据
      const { getDailyQuoteByDate } = await import("./quizData");
      return getDailyQuoteByDate();
    }
  },

  /**
   * 获取一组快速答题题目（默认 5 题）
   * Mock 模式从本地题库随机抽取；真实模式可对接后端 quiz 接口
   */
  async getQuickQuiz(count = 5): Promise<
    {
      type: string;
      question: string;
      options: string[];
      correctAnswer: string;
      explanation: string;
      source: string;
      original_text: string;
    }[]
  > {
    if (USE_MOCK) {
      const { getRandomQuiz } = await import("./quizData");
      return mockDelay(getRandomQuiz(count));
    }
    try {
      const { data: resp } = await apiClient.get("/learning/quick-quiz", {
        params: { count },
      });
      const items: any[] = resp?.data?.items ?? resp?.items ?? [];
      return items.map((q) => ({
        type: q.question_type ?? q.type ?? "select_original",
        question: q.question,
        options: q.options ?? [],
        correctAnswer: q.correct_answer ?? q.correctAnswer ?? "",
        explanation: q.explanation ?? "",
        source: q.source ?? "",
        original_text: q.original_text ?? q.originalText ?? "",
      }));
    } catch {
      // 兜底：用本地题库
      const { getRandomQuiz } = await import("./quizData");
      return getRandomQuiz(count);
    }
  },
};

/** SWR fetcher */
export const swrFetcher = (url: string) =>
  apiClient.get(url).then((res) => res.data);

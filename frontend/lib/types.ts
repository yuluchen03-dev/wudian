/**
 * 悟典 - TypeScript 类型定义
 */

/** 书籍元信息 */
export interface Book {
  id: string;
  title: string;
  /** 四书五经分类 */
  category: string;
  author?: string;
  description: string;
  coverColor: string;
  coverImage?: string;
  totalChapters: number;
}

/** 句子中的注释（生僻字） */
export interface Annotation {
  /** 原文中的字 */
  char: string;
  /** 拼音 */
  pinyin: string;
  /** 释义 */
  meaning: string;
  /** 是否为通假字 */
  isTongjia?: boolean;
  /** 通假字本字 */
  tongjiaOrigin?: string;
}

/** 实体（百科） */
export interface Entity {
  id: string;
  name: string;
  type: "人名" | "地名" | "官职" | "典故" | "概念";
  description: string;
  /** 关联的原文片段 */
  relatedText?: string;
}

/** 原文与译文逐句对应 */
export interface SentencePair {
  id: string;
  /** 原文 */
  original: string;
  /** 白话翻译 */
  translation: string;
  /** 该句包含的注释 */
  annotations?: Annotation[];
  /** 该句包含的实体引用 */
  entityIds?: string[];
}

/** 章节 */
export interface Chapter {
  id: string;
  bookId: string;
  /** 章序号 */
  order: number;
  /** 章节标题，如"学而第一" */
  title: string;
  sentences: SentencePair[];
}

/** 每日一句 */
export interface DailyQuote {
  id: string;
  text: string;
  translation: string;
  source: string;
  chapterId: string;
}

/** 学习进度 */
export interface LearningProgress {
  bookId: string;
  currentChapterOrder: number;
  totalChapters: number;
  readChapters: number[];
  streakDays: number;
  lastReadDate: string;
}

// ============================================================
// 社区共学
// ============================================================

export type GroupCategory = "beginner" | "advanced" | "theme" | "free";

export interface StudyGroup {
  id: number;
  name: string;
  description: string;
  category: GroupCategory;
  bookId?: string;
  ownerName: string;
  memberCount: number;
  maxMembers: number;
  todayCheckinCount: number;
  isPrivate: boolean;
  createdAt: string;
}

export interface AuthorBrief {
  userId: number;
  username: string;
  nickname?: string;
  avatar?: string;
  level: number;
}

export interface Note {
  id: number;
  title: string;
  content: string;
  excerpt: string;
  author: AuthorBrief;
  bookId?: string;
  chapterId?: string;
  verseText?: string;
  groupId?: number;
  tags: string[];
  likeCount: number;
  commentCount: number;
  isLiked: boolean;
  isEssence: boolean;
  createdAt: string;
}

export interface Comment {
  id: number;
  author: AuthorBrief;
  content: string;
  likeCount: number;
  parentId?: number;
  createdAt: string;
  replies: Comment[];
}

export interface NoteDetail extends Note {
  comments: Comment[];
}

export interface PKQuestion {
  index: number;
  question: string;
  options: string[];
  verseSource?: string;
}

export interface PKMatchResult {
  pkId: string;
  opponent: AuthorBrief;
  questions: PKQuestion[];
  timeLimitSeconds: number;
  status: "matching" | "ongoing" | "finished" | "cancelled";
}

export interface PKSettlement {
  pkId: string;
  myScore: number;
  opponentScore: number;
  result: "win" | "lose" | "draw";
  correctCount: number;
  totalCount: number;
  expGained: number;
  ratingChange: number;
  newRating: number;
}

export interface LeaderboardEntry {
  rank: number;
  userId: number;
  username: string;
  nickname?: string;
  avatar?: string;
  level: number;
  score: number;
  scoreLabel: string;
  extra?: string;
}

export interface LeaderboardData {
  scope: "week" | "month" | "all";
  metric: string;
  myRank?: number;
  myScore?: number;
  entries: LeaderboardEntry[];
}

// ============================================================
// 趣味内容
// ============================================================

export type CardStyle =
  | "ink_wash"
  | "gold_seal"
  | "bamboo_scroll"
  | "moonlight"
  | "cloud_mist";

export interface QuoteCard {
  id: string;
  quote: string;
  source: string;
  style: CardStyle;
  imageKeyword: string;
  backgroundImage?: string;
  likeCount: number;
  shareCount: number;
  createdAt: string;
}

export interface QuoteCardDetail extends QuoteCard {
  vernacular: string;
  modernInterpretation: string;
  backgroundColor: string;
  accentColor: string;
  tags: string[];
  isLiked: boolean;
}

export interface TheaterLine {
  role: string;
  text: string;
  emotion?: string;
  beat?: string;
  action?: string;
  subtext?: string;
  pressure?: string;
  isOriginalVerse: boolean;
}

export interface TheaterRole {
  name: string;
  description: string;
  classicalOrigin?: string;
  avatarKeyword: string;
  portraitImage?: string;
  objective?: string;
  fear?: string;
  belief?: string;
  strategy?: string;
  conflictTrigger?: string;
  stageAction?: string;
}

export interface TheaterScene {
  title: string;
  setting: string;
  lines: TheaterLine[];
}

export interface Theater {
  id: string;
  title: string;
  summary: string;
  classicalSource: string;
  modernSetting: string;
  coverKeyword: string;
  coverImage?: string;
  sceneCount: number;
  likeCount: number;
  viewCount: number;
  createdAt: string;
}

export interface TheaterDetail extends Theater {
  roles: TheaterRole[];
  scenes: TheaterScene[];
  moral: string;
  tags: string[];
}

// ============================================================
// 概念可视化
// ============================================================

/** 儒家核心概念 */
export interface Concept {
  id: string;
  /** 概念名，如"仁" */
  name: string;
  /** 白话定义 */
  definition: string;
  /** 经典原句 */
  original_quote: string;
  /** 原句出处 */
  quote_source: string;
  /** 现代场景类比 */
  modern_analogy: string;
  /** 相关经文片段 ID 列表 */
  related_verses: string[];
}

// ============================================================
// 与圣贤对话
// ============================================================

/** 对话消息 */
export interface SageMessage {
  id: string;
  /** 发言角色：user 或 sage */
  role: "user" | "sage";
  /** 消息内容（原始文本，含 <<<TAG>>> 标记） */
  content: string;
  /** 时间戳 */
  timestamp: string;
  /** 解析后的结构化回复（仅 sage 消息有） */
  parsed?: SageReplyParts;
  /** 思想依据引用列表（仅 sage 消息有） */
  citations?: Citation[];
}

/** 圣贤结构化回复的各区块 */
export interface SageReplyParts {
  /** 引用的经典原文，"无"表示无原文 */
  quote: string;
  /** 原文出处，"无"表示无出处 */
  source: string;
  /** 圣贤口吻的文言回应 */
  classical: string;
  /** 白话点睛 */
  vernacular: string;
  /** 免责声明 */
  disclaimer: string;
}

/** 圣贤信息 */
export interface Sage {
  id: string;
  /** 姓名，如"孔子" */
  name: string;
  /** 头像背景色 */
  avatar_color: string;
  portraitImage?: string;
  sceneImage?: string;
  /** 简介 */
  description: string;
  /** 说话风格 */
  speaking_style: string;
  /** 预设问题 */
  suggested_questions: string[];
}

/** 思想依据引用 */
export interface Citation {
  /** 原文内容 */
  text: string;
  /** 出处，如《论语·学而》 */
  source: string;
  /** 篇章 */
  chapter?: string;
  /** 章序号 */
  verse_no?: number;
  /** 相关度分数 0-1 */
  similarity: number;
  /** 引用类型：verse=经文原文 / commentary=注疏 */
  type: "verse" | "commentary";
}

// ============================================================
// 漫画解读
// ============================================================

/** 漫画分镜 */
export interface ComicPanel {
  /** 场景描述 */
  scene: string;
  /** 镜头语言 */
  shot?: string;
  /** 画面动作 */
  action?: string;
  /** 对话内容 */
  dialogue: string;
  /** 旁白/字幕 */
  caption?: string;
  /** 角色 */
  character: string;
  /** 表情（emoji 或文字） */
  emotion: string;
  /** 知识锚点 */
  knowledgeAnchor?: string;
  /** 视觉隐喻 */
  visualMetaphor?: string;
  /** 节奏功能 */
  beat?: string;
  /** AI 生成漫画面板图 public path */
  imageUrl?: string;
  /** Agens 图像生成提示词 */
  imagePrompt?: string;
}

/** 漫画 */
export interface Comic {
  id: string;
  /** 标题 */
  title: string;
  /** 出处经文 */
  source_verse: string;
  /** 漫画脚本主题 */
  logline?: string;
  /** 统一画风说明 */
  styleGuide?: string;
  /** 角色圣经 */
  characters?: {
    name: string;
    role: string;
    description: string;
    visualAnchor: string;
  }[];
  /** 分镜列表 */
  panels: ComicPanel[];
}

// ============================================================
// 影像底本外链
// ============================================================

/** 古籍影像底本外链平台 */
export interface ImageSource {
  /** 平台 ID */
  id: string;
  /** 平台名称 */
  name: string;
  /** 外链地址 */
  url: string;
  /** 说明 */
  description: string;
}

// ========== 互动探索层 ==========

/** 知识图谱节点 */
export interface GraphNode {
  id: string;
  label: string;
  type: "person" | "concept";
  subtype?: "sage" | "disciple" | "lineage";
  courtesy_name?: string;
  real_name?: string;
  birth_year?: number;
  death_year?: number;
  era?: string;
  description?: string;
  core_thought?: string;
  tags?: string[];
}

/** 知识图谱边 */
export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  label?: string;
  description?: string;
}

/** 图数据 */
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** 图响应 */
export interface GraphResponse {
  type: string;
  total_nodes: number;
  total_edges: number;
  graph: GraphData;
}

/** 时间线事件 */
export interface TimelineEvent {
  id: string;
  year: number;
  year_label: string;
  title: string;
  category: "history" | "person" | "classic";
  description: string;
  tags?: string[];
}

/** 时间线响应 */
export interface TimelineResponse {
  total: number;
  categories: string[];
  events: TimelineEvent[];
}

/** 成语典故 */
export interface Idiom {
  idiom: string;
  original_text: string;
  source: string;
  chapter: string;
  chapter_num: number;
  verse_num: number;
  meaning: string;
  modern_usage: string;
  tags?: string[];
}

/** 成语列表响应 */
export interface IdiomListResponse {
  total: number;
  idioms: Idiom[];
}

// ============================================================
// 经典闯关
// ============================================================

/** 题目类型 */
export type QuestionType = "choice" | "fill" | "match" | "order";

/** 选项 */
export interface QuestionOption {
  index: number;
  text: string;
}

/** 闯关题目 */
export interface ChallengeQuestion {
  quizId: number;
  verseId: string;
  questionType: QuestionType;
  difficulty: number;
  question: string;
  options?: QuestionOption[];
  /** 仅用于本地 mock 判题，真实接口不返回答案 */
  correctAnswer?: unknown;
  explanation?: string;
}

/** 用户作答 */
export interface ChallengeAnswer {
  quizId: number;
  userAnswer: unknown;
  timeSpent: number;
}

/** 单题反馈 */
export interface QuestionFeedback {
  quizId: number;
  isCorrect: boolean;
  correctAnswer: unknown;
  explanation: string;
}

/** 闯关结果 */
export interface ChallengeResult {
  total: number;
  correctCount: number;
  wrongCount: number;
  score: number;
  passed: boolean;
  passThreshold: number;
  totalTime: number;
  results: QuestionFeedback[];
  expGained?: number;
}

/** 闯关关卡（章/节） */
export interface ChallengeLevel {
  id: string;
  chapterId: string;
  title: string;
  order: number;
  sentenceCount: number;
  locked: boolean;
  passed: boolean;
  bestScore?: number;
  stars: number;
}

// ============================================================
// SRS 间隔复习
// ============================================================

/** 待复习经文条目 */
export interface DueReviewItem {
  record_id: number;
  verse_id: string;
  original_text: string;
  translation: string;
  repetitions: number;
  ease_factor: number;
  interval_days: number;
  next_review_date: string;
}

/** 待复习响应 */
export interface DueReviewsResponse {
  due_count: number;
  items: DueReviewItem[];
}

/** 复习统计 */
export interface ReviewStats {
  total_reviewed: number;
  mastered_count: number;
  learning_count: number;
  today_reviewed: number;
  today_correct: number;
  streak_days: number;
  retention_rate: number;
}

// ============================================================
// 成就与段位
// ============================================================

/** 成就徽章 */
export interface Achievement {
  id: number;
  code: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  unlocked: boolean;
  unlocked_at?: string;
  condition: string;
}

/** 成就响应 */
export interface AchievementsResponse {
  unlocked: Achievement[];
  locked: Achievement[];
  exp: number;
  level: number;
}

/** 段位信息 */
export interface RankInfo {
  current_rank: number;
  rank_name: string;
  exp: number;
  next_rank: number | null;
  next_rank_name: string | null;
  progress: number;
}

// ============================================================
// 认证
// ============================================================

/** 用户信息 */
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  nickname?: string;
  level: number;
  exp: number;
  avatar?: string;
}

/** 登录/注册响应 */
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}


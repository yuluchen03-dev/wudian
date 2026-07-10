/**
 * 悟典 - 社区 Mock 数据
 * 供前端独立开发与展示
 */
import type {
  StudyGroup,
  Note,
  NoteDetail,
  Comment,
  PKMatchResult,
  PKSettlement,
  LeaderboardData,
} from "./types";

export const mockGroups: StudyGroup[] = [
  {
    id: 1,
    name: "论语百日共读",
    description: "每天一章论语，百天读完一部经典。欢迎所有热爱国学的朋友！",
    category: "beginner",
    bookId: "lunyu",
    ownerName: "曾子",
    memberCount: 128,
    maxMembers: 200,
    todayCheckinCount: 86,
    isPrivate: false,
    createdAt: "2024-05-01T00:00:00",
  },
  {
    id: 2,
    name: "孟子精读研习社",
    description: "深入研读孟子，探讨仁政思想与现代价值。适合有一定基础的学友。",
    category: "advanced",
    bookId: "mengzi",
    ownerName: "子贡",
    memberCount: 56,
    maxMembers: 80,
    todayCheckinCount: 32,
    isPrivate: false,
    createdAt: "2024-05-15T00:00:00",
  },
  {
    id: 3,
    name: "经典中的职场智慧",
    description: "从四书五经中提取职场生存哲学，古为今用。",
    category: "theme",
    ownerName: "子路",
    memberCount: 203,
    maxMembers: 300,
    todayCheckinCount: 145,
    isPrivate: false,
    createdAt: "2024-06-01T00:00:00",
  },
  {
    id: 4,
    name: "大学·中庸读书会",
    description: "修身齐家治国平天下——从《大学》《中庸》开始。",
    category: "free",
    bookId: "daxue",
    ownerName: "颜回",
    memberCount: 42,
    maxMembers: 50,
    todayCheckinCount: 28,
    isPrivate: false,
    createdAt: "2024-06-10T00:00:00",
  },
];

const author1 = { userId: 1001, username: "zengzi", nickname: "曾子", level: 12 };
const author2 = { userId: 1002, username: "zigong", nickname: "子贡", level: 15 };
const author3 = { userId: 1004, username: "yanhui", nickname: "颜回", level: 20 };

export const mockNotes: Note[] = [
  {
    id: 1,
    title: "学而时习之——我的复盘方法论",
    content:
      "今天重读《学而》篇，对'学而时习之'有了新理解。以前以为'习'只是复习，现在觉得'习'更是实践。学到的知识如果不去用，就只是信息。\n\n我开始用费曼学习法：每学一章论语，就试着用自己的话讲给别人听。讲不清的地方，就是没真懂的地方。\n\n另外，'时'字也很关键——不是随便什么时候复习，而是在恰当的时机。比如学完一周后复习一次，一个月后再复习一次，符合艾宾浩斯遗忘曲线。",
    excerpt: "今天重读《学而》篇，对'学而时习之'有了新理解。以前以为'习'只是复习，现在觉得'习'更是实践...",
    author: author1,
    bookId: "lunyu",
    verseText: "学而时习之，不亦说乎",
    groupId: 1,
    tags: ["学习法", "复盘", "费曼"],
    likeCount: 48,
    commentCount: 12,
    isLiked: false,
    isEssence: true,
    createdAt: "2024-06-18T10:30:00",
  },
  {
    id: 2,
    title: "己所不欲勿施于人——团队管理的黄金法则",
    content:
      "今天带团队踩了个坑。我把最难的活全分给了新人，自己只做'协调'。结果新人加班到凌晨，项目还是延期了。\n\n回头想想，孔子说的'己所不欲勿施于人'真的是管理第一课。我自己不想干的活，凭什么全推给别人？\n\n下周开始重新分工：难的活大家一起拆解，我也要承担核心部分。管理不是甩锅，是扛事。",
    excerpt: "今天带团队踩了个坑。我把最难的活全分给了新人，自己只做'协调'。结果新人加班到凌晨...",
    author: author2,
    bookId: "lunyu",
    verseText: "己所不欲，勿施于人",
    groupId: 3,
    tags: ["管理", "团队", "反思"],
    likeCount: 76,
    commentCount: 23,
    isLiked: true,
    isEssence: true,
    createdAt: "2024-06-17T15:20:00",
  },
  {
    id: 3,
    title: "颜回的快乐——一箪食一瓢饮的现代启示",
    content:
      "读到'一箪食，一瓢饮，在陋巷，人不堪其忧，回也不改其乐'，突然很感慨。\n\n我们总以为快乐需要条件：更大的房子、更高的工资、更好的车。但颜回告诉我们，快乐的源泉在内心，不在外物。\n\n最近尝试极简生活，断舍离了一半东西。反而觉得轻松了——不被物质绑架的感觉，真的很好。",
    excerpt: "读到'一箪食，一瓢饮，在陋巷，人不堪其忧，回也不改其乐'，突然很感慨...",
    author: author3,
    bookId: "lunyu",
    verseText: "一箪食，一瓢饮，在陋巷，人不堪其忧，回也不改其乐",
    tags: ["极简", "快乐", "颜回"],
    likeCount: 92,
    commentCount: 18,
    isLiked: false,
    isEssence: false,
    createdAt: "2024-06-16T09:15:00",
  },
  {
    id: 4,
    title: "三人行必有我师——code review 的领悟",
    content:
      "今天 review 实习生的代码，发现他用了一个我没想到的算法，时间复杂度直接从 O(n²) 降到 O(n)。\n\n说实话一开始有点不好意思——十年经验被新人教了。但想想'三人行必有我师'，这有什么丢人的？\n\n反而应该高兴：团队里有人能超过自己，说明团队在成长。我主动让他做了技术分享，效果很好。",
    excerpt: "今天 review 实习生的代码，发现他用了一个我没想到的算法，时间复杂度直接从 O(n²) 降到 O(n)...",
    author: author1,
    bookId: "lunyu",
    verseText: "三人行，必有我师焉",
    groupId: 2,
    tags: ["技术", "谦虚", "团队"],
    likeCount: 65,
    commentCount: 9,
    isLiked: false,
    isEssence: false,
    createdAt: "2024-06-15T14:00:00",
  },
];

export const mockNoteDetail: NoteDetail = {
  ...mockNotes[0],
  comments: [
    {
      id: 1,
      author: author2,
      content: "费曼学习法确实好用！我也是讲给别人听才发现自己哪里没懂。",
      likeCount: 8,
      parentId: undefined,
      createdAt: "2024-06-18T11:00:00",
      replies: [
        {
          id: 3,
          author: author1,
          content: "是的，教是最好的学。",
          likeCount: 3,
          parentId: 1,
          createdAt: "2024-06-18T11:30:00",
          replies: [],
        },
      ],
    },
    {
      id: 2,
      author: author3,
      content: "'时'字的解读很到位，受教了。",
      likeCount: 5,
      parentId: undefined,
      createdAt: "2024-06-18T12:00:00",
      replies: [],
    },
  ],
};

export const mockPKMatch: PKMatchResult = {
  pkId: "pk_demo001",
  opponent: { userId: 1004, username: "yanhui", nickname: "颜回", level: 20 },
  questions: [
    {
      index: 0,
      question: '「有朋自远方来」的下一句是？',
      options: ["不亦乐乎", "不亦说乎", "不亦君子乎", "不亦善乎"],
      verseSource: "《论语·学而》",
    },
    {
      index: 1,
      question: '「温故而知新」出自哪部经典？',
      options: ["《大学》", "《中庸》", "《论语》", "《孟子》"],
      verseSource: "《论语·为政》",
    },
    {
      index: 2,
      question: '「三人行，必有我师焉」强调的是？',
      options: ["谦虚好学", "尊师重道", "勤奋刻苦", "诚实守信"],
      verseSource: "《论语·述而》",
    },
    {
      index: 3,
      question: '「学而不思则罔」的下一句是？',
      options: ["思而不学则殆", "思而不学则罔", "学而不厌", "诲人不倦"],
      verseSource: "《论语·为政》",
    },
    {
      index: 4,
      question: '「己所不欲，勿施于人」讲的是？',
      options: ["恕道", "忠道", "孝道", "仁道"],
      verseSource: "《论语·卫灵公》",
    },
  ],
  timeLimitSeconds: 300,
  status: "ongoing",
};

export const mockPKSettlement: PKSettlement = {
  pkId: "pk_demo001",
  myScore: 48,
  opponentScore: 35,
  result: "win",
  correctCount: 4,
  totalCount: 5,
  expGained: 50,
  ratingChange: 16,
  newRating: 1068,
};

export const mockLeaderboard: LeaderboardData = {
  scope: "week",
  metric: "exp",
  myRank: 7,
  myScore: 3200,
  entries: [
    { rank: 1, userId: 1004, username: "yanhui", nickname: "颜回", level: 20, score: 5800, scoreLabel: "经验值", extra: "本周榜首" },
    { rank: 2, userId: 1002, username: "zigong", nickname: "子贡", level: 15, score: 4500, scoreLabel: "经验值" },
    { rank: 3, userId: 1003, username: "zilu", nickname: "子路", level: 10, score: 3900, scoreLabel: "经验值" },
    { rank: 4, userId: 1005, username: "ziyou", nickname: "子游", level: 8, score: 3600, scoreLabel: "经验值" },
    { rank: 5, userId: 1006, username: "zixia", nickname: "子夏", level: 11, score: 3500, scoreLabel: "经验值" },
    { rank: 6, userId: 1007, username: "zigao", nickname: "子羔", level: 7, score: 3300, scoreLabel: "经验值" },
    { rank: 7, userId: 1001, username: "zengzi", nickname: "曾子", level: 12, score: 3200, scoreLabel: "经验值" },
    { rank: 8, userId: 1008, username: "zizhang", nickname: "子张", level: 9, score: 2800, scoreLabel: "经验值" },
    { rank: 9, userId: 1009, username: "youzi", nickname: "有子", level: 6, score: 2500, scoreLabel: "经验值" },
    { rank: 10, userId: 1010, username: "zaiwo", nickname: "宰我", level: 5, score: 2200, scoreLabel: "经验值" },
  ],
};

export type SageVisual = {
  portraitImage: string;
  sceneImage: string;
};

export const sageVisuals: Record<string, SageVisual> = {
  confucius: {
    portraitImage: "/agens/sages/portraits/confucius.png",
    sceneImage: "/agens/sages/scenes/confucius.png",
  },
  mencius: {
    portraitImage: "/agens/sages/portraits/mencius.png",
    sceneImage: "/agens/sages/scenes/mencius.png",
  },
  wang_yangming: {
    portraitImage: "/agens/sages/portraits/wang_yangming.png",
    sceneImage: "/agens/sages/scenes/wang_yangming.png",
  },
  laozi: {
    portraitImage: "/agens/sages/portraits/laozi.png",
    sceneImage: "/agens/sages/scenes/laozi.png",
  },
  mozi: {
    portraitImage: "/agens/sages/portraits/mozi.png",
    sceneImage: "/agens/sages/scenes/mozi.png",
  },
  hanfeizi: {
    portraitImage: "/agens/sages/portraits/hanfeizi.png",
    sceneImage: "/agens/sages/scenes/hanfeizi.png",
  },
  li_bai: {
    portraitImage: "/agens/sages/portraits/li_bai.png",
    sceneImage: "/agens/sages/scenes/li_bai.png",
  },
  su_shi: {
    portraitImage: "/agens/sages/portraits/su_shi.png",
    sceneImage: "/agens/sages/scenes/su_shi.png",
  },
  fan_zhongyan: {
    portraitImage: "/agens/sages/portraits/fan_zhongyan.png",
    sceneImage: "/agens/sages/scenes/fan_zhongyan.png",
  },
  wang_anshi: {
    portraitImage: "/agens/sages/portraits/wang_anshi.png",
    sceneImage: "/agens/sages/scenes/wang_anshi.png",
  },
  zhuge_liang: {
    portraitImage: "/agens/sages/portraits/zhuge_liang.png",
    sceneImage: "/agens/sages/scenes/zhuge_liang.png",
  },
};

export const pageBackgrounds = {
  home: "/agens/page-backgrounds/home.svg",
  content: "/agens/page-backgrounds/content.svg",
  roundtable: "/agens/page-backgrounds/roundtable.svg",
  sageChat: "/agens/page-backgrounds/sage-chat.svg",
  reader: "/agens/page-backgrounds/reader.svg",
  challenge: "/agens/page-backgrounds/challenge.svg",
  review: "/agens/page-backgrounds/review.svg",
  exploration: "/agens/page-backgrounds/exploration.svg",
  concepts: "/agens/page-backgrounds/concepts.svg",
  achievements: "/agens/page-backgrounds/achievements.svg",
  community: "/agens/page-backgrounds/community.svg",
  about: "/agens/page-backgrounds/about.svg",
  auth: "/agens/page-backgrounds/auth.svg",
} as const;

export const featuredBookCoverImages: Record<string, string> = {};

export const getBookCoverImage = (bookId: string) => `/agens/books/${encodeURIComponent(bookId)}.png`;

export const quoteBackgroundImages: Record<string, string> = {
  qc_001: "/content/quote-backgrounds/qc_001.png",
  qc_002: "/content/quote-backgrounds/qc_002.png",
  qc_003: "/content/quote-backgrounds/qc_003.png",
  qc_004: "/content/quote-backgrounds/qc_004.png",
  qc_005: "/content/quote-backgrounds/qc_005.png",
  qc_006: "/content/quote-backgrounds/qc_006.png",
  qc_007: "/content/quote-backgrounds/qc_007.png",
  qc_008: "/content/quote-backgrounds/qc_008.png",
  qc_009: "/content/quote-backgrounds/qc_009.png",
  qc_010: "/content/quote-backgrounds/qc_010.png",
  qc_011: "/content/quote-backgrounds/qc_011.png",
  qc_012: "/content/quote-backgrounds/qc_012.png",
  qc_013: "/content/quote-backgrounds/qc_013.png",
  qc_014: "/content/quote-backgrounds/qc_014.png",
  qc_015: "/content/quote-backgrounds/qc_015.png",
  qc_016: "/content/quote-backgrounds/qc_016.png",
  qc_017: "/content/quote-backgrounds/qc_017.png",
  qc_018: "/content/quote-backgrounds/qc_018.png",
  qc_019: "/content/quote-backgrounds/qc_019.png",
  qc_020: "/content/quote-backgrounds/qc_020.png",
  qc_021: "/content/quote-backgrounds/qc_021.png",
  qc_022: "/content/quote-backgrounds/qc_022.png",
};

export const getQuoteBackgroundImage = (cardId: string) => quoteBackgroundImages[cardId];

export const theaterCoverImages: Record<string, string> = {
  th_001: "/agens/content/theater-covers/th_001.png",
  th_002: "/agens/content/theater-covers/th_002.png",
  th_003: "/agens/content/theater-covers/th_003.png",
  th_004: "/agens/content/theater-covers/th_004.png",
  th_005: "/agens/content/theater-covers/th_005.png",
  th_006: "/agens/content/theater-covers/th_006.png",
};

export const theaterRolePortraitImages: Record<string, string> = {
  "th_001:0": "/agens/content/theater-roles/th_001_role_01.png",
  "th_001:1": "/agens/content/theater-roles/th_001_role_02.png",
  "th_002:0": "/agens/content/theater-roles/th_002_role_01.png",
  "th_002:1": "/agens/content/theater-roles/th_002_role_02.png",
  "th_003:0": "/agens/content/theater-roles/th_003_role_01.png",
  "th_003:1": "/agens/content/theater-roles/th_003_role_02.png",
  "th_003:2": "/agens/content/theater-roles/th_003_role_03.png",
  "th_004:0": "/agens/content/theater-roles/th_004_role_01.png",
  "th_004:1": "/agens/content/theater-roles/th_004_role_02.png",
  "th_005:0": "/agens/content/theater-roles/th_005_role_01.png",
  "th_005:1": "/agens/content/theater-roles/th_005_role_02.png",
  "th_005:2": "/agens/content/theater-roles/th_005_role_03.png",
  "th_006:0": "/agens/content/theater-roles/th_006_role_01.png",
  "th_006:1": "/agens/content/theater-roles/th_006_role_02.png",
};

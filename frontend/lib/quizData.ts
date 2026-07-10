/**
 * 悟典 - 快速答题精选题库
 * 从《论语》经典名句生成，适合 1-2 分钟一组的轻量答题 demo。
 * 题型：选择题（选原文/选译文/选出处）+ 填空题（补全原文）
 */

export type QuizType = "select_original" | "select_translation" | "select_source" | "fill_blank";

export interface QuickQuizQuestion {
  /** 题型 */
  type: QuizType;
  /** 题干 */
  question: string;
  /** 选项（选择题用；填空题为空数组） */
  options: string[];
  /** 正确答案（选择题为选项文本，填空题为缺失的原文片段） */
  correctAnswer: string;
  /** 解析 / 白话解释 */
  explanation: string;
  /** 出处篇章，如 "《论语·学而》" */
  source: string;
  /** 原文完整句 */
  original_text: string;
}

/**
 * 精选 18 道题，覆盖学而、为政、里仁、公冶长、雍也、述而、颜渊等篇。
 * 每次随机抽 5 题一组。
 */
export const quizQuestions: QuickQuizQuestion[] = [
  // ===== 学而第一 =====
  {
    type: "fill_blank",
    question: "补全原文：学而时习之，______，不亦说乎？",
    options: [],
    correctAnswer: "不亦说乎",
    explanation: "学习了知识并按时温习，不也是很愉快吗？强调学习需反复实践，方能内化于心。",
    source: "《论语·学而》",
    original_text: "学而时习之，不亦说乎？",
  },
  {
    type: "select_translation",
    question: "「学而时习之，不亦说乎」的白话译文是？",
    options: [
      "学习了知识并按时温习，不也是很愉快吗？",
      "学习知识却不思考，就会迷惑；思考却不学习，就会危险。",
      "只学习不实践，不如不学。",
      "学到的知识要藏在心里，不可轻易示人。",
    ],
    correctAnswer: "学习了知识并按时温习，不也是很愉快吗？",
    explanation: "此句强调「学」与「习」并重——学是获取，习是温习实践，二者结合方能有所得、有所乐。",
    source: "《论语·学而》",
    original_text: "学而时习之，不亦说乎？",
  },
  {
    type: "select_original",
    question: "下列哪句是「人不知而不愠」的完整原文？",
    options: [
      "人不知而不愠，不亦君子乎",
      "人不知而愠，不亦君子乎",
      "人不知而不怒，可谓仁矣",
      "人若不知，则当自省",
    ],
    correctAnswer: "人不知而不愠，不亦君子乎",
    explanation: "别人不了解自己却不怨恨，不也是君子吗？体现君子胸怀宽广、不以外物毁誉动心。",
    source: "《论语·学而》",
    original_text: "人不知而不愠，不亦君子乎",
  },
  {
    type: "fill_blank",
    question: "补全原文：君子务本，______，本立而道生。",
    options: [],
    correctAnswer: "本立而道生",
    explanation: "君子致力于根本，根本确立了，道也就随之而生。强调修身当从根本处着力。",
    source: "《论语·学而》",
    original_text: "君子务本，本立而道生",
  },
  {
    type: "select_source",
    question: "「过则勿惮改」出自《论语》哪一篇？",
    options: ["《论语·学而》", "《论语·为政》", "《论语·里仁》", "《论语·颜渊》"],
    correctAnswer: "《论语·学而》",
    explanation: "有了过错就不要怕改正。语出《学而》篇，为孔子勉人勇于改过之语。",
    source: "《论语·学而》",
    original_text: "过则勿惮改",
  },

  // ===== 为政第二 =====
  {
    type: "fill_blank",
    question: "补全原文：温故而知新，______。",
    options: [],
    correctAnswer: "可以为师矣",
    explanation: "温习旧知识从而能获得新体会，就可以做老师了。强调学习的贯通与创新。",
    source: "《论语·为政》",
    original_text: "温故而知新，可以为师矣",
  },
  {
    type: "select_translation",
    question: "「温故而知新，可以为师矣」的意思是？",
    options: [
      "温习旧知识并获得新体会，就可以做老师了。",
      "只有忘记旧事才能记住新事。",
      "老师应当只教新知识，不复习旧知识。",
      "温习旧事是为了忘记它们。",
    ],
    correctAnswer: "温习旧知识并获得新体会，就可以做老师了。",
    explanation: "此句揭示学习之道：在温习中悟出新意，方能融会贯通、为人师表。",
    source: "《论语·为政》",
    original_text: "温故而知新，可以为师矣",
  },
  {
    type: "select_original",
    question: "下列哪句是孔子关于学与思关系的名言？",
    options: [
      "学而不思则罔，思而不学则殆",
      "学而时习之，不亦说乎",
      "三人行，必有我师焉",
      "知之为知之，不知为不知",
    ],
    correctAnswer: "学而不思则罔，思而不学则殆",
    explanation: "只学习不思考就会迷惑，只思考不学习就会危险。学与思不可偏废。",
    source: "《论语·为政》",
    original_text: "学而不思则罔，思而不学则殆",
  },
  {
    type: "select_source",
    question: "「学而不思则罔，思而不学则殆」出自哪一篇？",
    options: ["《论语·为政》", "《论语·学而》", "《论语·述而》", "《论语·子罕》"],
    correctAnswer: "《论语·为政》",
    explanation: "语出《为政》篇，孔子论学与思的辩证关系，至今仍为治学圭臬。",
    source: "《论语·为政》",
    original_text: "学而不思则罔，思而不学则殆",
  },

  // ===== 里仁第四 =====
  {
    type: "fill_blank",
    question: "补全原文：朝闻道，______。",
    options: [],
    correctAnswer: "夕死可矣",
    explanation: "早晨明白了真理，晚上死去也心甘。表达对真理的极致追求与献身精神。",
    source: "《论语·里仁》",
    original_text: "朝闻道，夕死可矣",
  },
  {
    type: "select_translation",
    question: "「朝闻道，夕死可矣」表达的是？",
    options: [
      "对真理的追求重于生命，得闻大道死而无憾。",
      "早上听道，晚上就可以不学了。",
      "道听途说不可轻信。",
      "人应当早上学习，晚上休息。",
    ],
    correctAnswer: "对真理的追求重于生命，得闻大道死而无憾。",
    explanation: "此句是儒家重道精神的集中体现，以生命之短暂衬托求道之重要。",
    source: "《论语·里仁》",
    original_text: "朝闻道，夕死可矣",
  },
  {
    type: "select_original",
    question: "下列哪句是孔子论「见贤思齐」的原文？",
    options: [
      "见贤思齐焉，见不贤而内自省也",
      "见贤而思齐，见不贤而远之",
      "见善如不及，见不善如探汤",
      "三人行，必有我师焉",
    ],
    correctAnswer: "见贤思齐焉，见不贤而内自省也",
    explanation: "见到贤人就想向他看齐，见到不贤的人就反省自己有没有类似缺点。",
    source: "《论语·里仁》",
    original_text: "见贤思齐焉，见不贤而内自省也",
  },

  // ===== 公冶长第五 / 雍也第六 =====
  {
    type: "select_translation",
    question: "「敏而好学，不耻下问」的意思是？",
    options: [
      "聪敏又勤奋好学，不以向地位低下的人请教为耻。",
      "敏捷地学习，不要问下面的人问题。",
      "聪明的人不应当多问问题。",
      "学习要敏捷，提问要谨慎。",
    ],
    correctAnswer: "聪敏又勤奋好学，不以向地位低下的人请教为耻。",
    explanation: "此句赞孔文子之德，亦为后人治学之训：好学且虚心，方能日进。",
    source: "《论语·公冶长》",
    original_text: "敏而好学，不耻下问",
  },
  {
    type: "fill_blank",
    question: "补全原文：知之者不如好之者，______。",
    options: [],
    correctAnswer: "好之者不如乐之者",
    explanation: "懂得它的人不如喜爱它的人，喜爱它的人不如以它为乐的人。强调兴趣是最好的老师。",
    source: "《论语·雍也》",
    original_text: "知之者不如好之者，好之者不如乐之者",
  },

  // ===== 述而第七 =====
  {
    type: "select_original",
    question: "下列哪句是「三人行，必有我师焉」的完整原文？",
    options: [
      "三人行，必有我师焉；择其善者而从之，其不善者而改之",
      "三人行，必有我师焉；择其善者而学之",
      "三人同行，必有可师者",
      "三人行，择善而从之",
    ],
    correctAnswer: "三人行，必有我师焉；择其善者而从之，其不善者而改之",
    explanation: "几个人同行，其中必定有可以做我老师的人：选他们的优点学习，看到缺点就自我改正。",
    source: "《论语·述而》",
    original_text: "三人行，必有我师焉；择其善者而从之，其不善者而改之",
  },
  {
    type: "select_translation",
    question: "「三人行，必有我师焉」强调的道理是？",
    options: [
      "处处皆有可学习之人，当择善而从、见不善而自省。",
      "三个人走路一定有危险。",
      "只有老师才能教导自己。",
      "结伴而行比独行更好。",
    ],
    correctAnswer: "处处皆有可学习之人，当择善而从、见不善而自省。",
    explanation: "此句体现孔子谦逊好学、善于反思的精神，人人皆可为师。",
    source: "《论语·述而》",
    original_text: "三人行，必有我师焉；择其善者而从之，其不善者而改之",
  },

  // ===== 颜渊第十二 =====
  {
    type: "fill_blank",
    question: "补全原文：己所不欲，______。",
    options: [],
    correctAnswer: "勿施于人",
    explanation: "自己不想要的，不要强加给别人。这是儒家「恕」道的核心，推己及人。",
    source: "《论语·颜渊》",
    original_text: "己所不欲，勿施于人",
  },
  {
    type: "select_source",
    question: "「己所不欲，勿施于人」出自《论语》哪一篇？",
    options: ["《论语·颜渊》", "《论语·学而》", "《论语·里仁》", "《论语·子路》"],
    correctAnswer: "《论语·颜渊》",
    explanation: "语出《颜渊》篇，为孔子答仲弓问仁之语，是恕道的经典表述。",
    source: "《论语·颜渊》",
    original_text: "己所不欲，勿施于人",
  },
];

/**
 * 从题库中随机抽取一组题目（默认 5 题），保证题型尽量多样。
 */
export function getRandomQuiz(count = 5): QuickQuizQuestion[] {
  const shuffled = [...quizQuestions].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, Math.min(count, quizQuestions.length));
}

/** 每日一句精选库（供 DailyQuoteCard 轮播） */
export interface DailyQuoteItem {
  id: string;
  text: string;
  translation: string;
  source: string;
}

export const dailyQuotes: DailyQuoteItem[] = [
  {
    id: "dq-1",
    text: "学而时习之，不亦说乎？有朋自远方来，不亦乐乎？",
    translation: "学习了知识并按时温习，不也是很愉快吗？有志同道合的朋友从远方来，不也是很快乐吗？",
    source: "《论语·学而》",
  },
  {
    id: "dq-2",
    text: "温故而知新，可以为师矣。",
    translation: "温习旧知识从而能获得新体会，就可以做老师了。",
    source: "《论语·为政》",
  },
  {
    id: "dq-3",
    text: "学而不思则罔，思而不学则殆。",
    translation: "只学习不思考就会迷惑，只思考不学习就会危险。",
    source: "《论语·为政》",
  },
  {
    id: "dq-4",
    text: "见贤思齐焉，见不贤而内自省也。",
    translation: "见到贤人就想向他看齐，见到不贤的人就反省自己有没有类似缺点。",
    source: "《论语·里仁》",
  },
  {
    id: "dq-5",
    text: "知之者不如好之者，好之者不如乐之者。",
    translation: "懂得它的人不如喜爱它的人，喜爱它的人不如以它为乐的人。",
    source: "《论语·雍也》",
  },
  {
    id: "dq-6",
    text: "三人行，必有我师焉。",
    translation: "几个人同行，其中必定有可以做我老师的人。",
    source: "《论语·述而》",
  },
  {
    id: "dq-7",
    text: "己所不欲，勿施于人。",
    translation: "自己不想要的，不要强加给别人。",
    source: "《论语·颜渊》",
  },
];

/** 根据日期获取每日一句（以天为单位轮换） */
export function getDailyQuoteByDate(date = new Date()): DailyQuoteItem {
  const dayIndex = Math.floor(date.getTime() / (1000 * 60 * 60 * 24));
  return dailyQuotes[dayIndex % dailyQuotes.length];
}

/** 获取前后几天的每日一句（用于卡片左右滑动） */
export function getDailyQuotesRange(centerDate = new Date(), range = 2): DailyQuoteItem[] {
  const result: DailyQuoteItem[] = [];
  const oneDay = 1000 * 60 * 60 * 24;
  for (let i = -range; i <= range; i++) {
    const d = new Date(centerDate.getTime() + i * oneDay);
    result.push(getDailyQuoteByDate(d));
  }
  return result;
}

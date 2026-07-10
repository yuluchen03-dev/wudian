/**
 * 悟典 - 儒家核心概念数据（Mock）
 */
import type { Concept } from "./types";

export const mockConcepts: Concept[] = [
  {
    id: "ren",
    name: "仁",
    definition:
      "仁是儒家最高道德准则，指对他人的关爱与同情，发自内心的善意与慈悲。樊迟问仁，子曰：爱人。",
    original_quote: "樊迟问仁。子曰：爱人。",
    quote_source: "《论语·颜渊》",
    modern_analogy:
      "如同现代社会中的同理心与志愿服务精神，设身处地为他人着想，主动关怀身边之人。",
    related_verses: ["lunyu-12-22", "lunyu-6-30"],
  },
  {
    id: "li",
    name: "礼",
    definition:
      "礼是维系社会秩序的行为规范与仪节，含恭敬、节制、合宜之意。克己复礼为仁，非礼勿视，非礼勿听。",
    original_quote: "不学礼，无以立。",
    quote_source: "《论语·季氏》",
    modern_analogy:
      "类似现代的社交礼仪与公共规则，尊重他人边界，遵守社会公约，使群体生活井然有序。",
    related_verses: ["lunyu-16-13", "lunyu-12-1"],
  },
  {
    id: "zhongyong",
    name: "中庸",
    definition:
      "中庸即不偏不倚、无过无不及的处事之道，执两用中，时时保持恰到好处的平衡。",
    original_quote: "中也者，天下之大本也；和也者，天下之达道也。",
    quote_source: "《中庸》",
    modern_analogy:
      "如同工作生活中的平衡艺术——劳逸结合、收支相宜，不走极端，在两难之间找到最优解。",
    related_verses: ["zhongyong-1", "lunyu-6-29"],
  },
  {
    id: "xiao",
    name: "孝",
    definition:
      "孝是为人子女对父母长辈的敬爱与奉养，含赡养、恭敬、承志、谏诤等多重内涵，为仁之本。",
    original_quote: "弟子入则孝，出则弟，谨而信，泛爱众，而亲仁。",
    quote_source: "《论语·学而》",
    modern_analogy:
      "现代语境下的家庭责任与代际关怀——陪伴父母、尊重长辈意愿、传承优良家风。",
    related_verses: ["lunyu-1-6", "lunyu-2-5"],
  },
  {
    id: "xue",
    name: "学",
    definition:
      "学是儒家修身之始，含诵习、思辨、践行三层。学而时习之，温故知新，学思结合方能成才。",
    original_quote: "学而时习之，不亦说乎？",
    quote_source: "《论语·学而》",
    modern_analogy:
      "对应现代的终身学习理念——持续输入、复盘实践、知行合一，在反馈循环中精进。",
    related_verses: ["lunyu-1-1", "lunyu-2-11"],
  },
  {
    id: "dao",
    name: "道",
    definition:
      "道是儒家所言的正当路径与根本法则，既指为人之道，也指治世之理。朝闻道，夕死可矣。",
    original_quote: "朝闻道，夕死可矣。",
    quote_source: "《论语·里仁》",
    modern_analogy:
      "类似现代人追寻的人生使命与价值观——找到值得为之奋斗一生的方向，活出意义。",
    related_verses: ["lunyu-4-8", "lunyu-15-29"],
  },
  {
    id: "junzi",
    name: "君子",
    definition:
      "君子是儒家理想人格，德才兼备、心怀天下、坦荡从容。君子喻于义，小人喻于利。",
    original_quote: "君子坦荡荡，小人长戚戚。",
    quote_source: "《论语·述而》",
    modern_analogy:
      "当代语境中的\u201c成熟担当者\u201d——有原则有格局，遇事从容，以德服人，是值得信赖的同行者。",
    related_verses: ["lunyu-7-37", "lunyu-4-5"],
  },
];

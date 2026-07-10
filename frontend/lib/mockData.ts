/**
 * 悟典 - Mock 数据
 * 论语前三章，供前端独立开发与展示
 */
import type {
  Book,
  Chapter,
  DailyQuote,
  Entity,
  LearningProgress,
} from "./types";
import classicsCatalog from "./classics_catalog.json";
import { getBookCoverImage } from "./visualAssets";

export const mockBooks: Book[] = classicsCatalog.books.map((book) => ({
  ...book,
  coverImage: getBookCoverImage(book.id),
}));

export const mockEntities: Entity[] = [
  {
    id: "confucius",
    name: "孔子",
    type: "人名",
    description:
      "名丘，字仲尼，春秋末期鲁国人，儒家学派创始人，被尊为\u201c至圣先师\u201d。生于公元前551年，卒于公元前479年。",
    relatedText: "子曰",
  },
  {
    id: "youzi",
    name: "有子",
    type: "人名",
    description:
      "即有若，孔子弟子，字子有，少孔子四十三岁。在孔门中以学问著称，言貌类孔子。",
  },
  {
    id: "zengzi",
    name: "曾子",
    type: "人名",
    description:
      "即曾参，孔子弟子，字子舆，以孝道闻名，作《大学》，被尊为\u201c宗圣\u201d。",
  },
  {
    id: "luzhou",
    name: "鲁国",
    type: "地名",
    description:
      "周朝诸侯国，姬姓，都城曲阜，为周公旦封地。孔子出生与活动的主要区域。",
  },
  {
    id: "junzi",
    name: "君子",
    type: "概念",
    description:
      "儒家理想人格，指有道德修养、行仁义之人。\u201c君子务本，本立而道生。\u201d",
  },
  {
    id: "dao",
    name: "道",
    type: "概念",
    description:
      "儒家核心范畴，指正确的政治主张、道德原则与人生理想。朝闻道，夕死可矣。",
  },
];

export const mockChapters: Chapter[] = [
  {
    id: "lunyu-1",
    bookId: "lunyu",
    order: 1,
    title: "学而第一",
    sentences: [
      {
        id: "1-1",
        original: "子曰：学而时习之，不亦说乎？",
        translation: "孔子说：学了知识并按时温习，不也是令人愉悦的吗？",
        annotations: [
          { char: "说", pinyin: "yuè", meaning: "同\u201c悦\u201d，愉快、高兴", isTongjia: true, tongjiaOrigin: "悦" },
        ],
        entityIds: ["confucius"],
      },
      {
        id: "1-2",
        original: "有朋自远方来，不亦乐乎？",
        translation: "有朋友从远方到来，不也是令人快乐的吗？",
      },
      {
        id: "1-3",
        original: "人不知而不愠，不亦君子乎？",
        translation: "别人不了解自己却不怨恨，不也是有道德的君子吗？",
        annotations: [
          { char: "愠", pinyin: "yùn", meaning: "怨恨、恼怒" },
        ],
        entityIds: ["junzi"],
      },
      {
        id: "1-4",
        original: "有子曰：其为人也孝弟，而好犯上者，鲜矣。",
        translation:
          "有子说：为人孝顺父母、敬爱兄长，却喜欢冒犯上级的人，是很少的。",
        annotations: [
          { char: "弟", pinyin: "tì", meaning: "同\u201c悌\u201d，敬爱兄长", isTongjia: true, tongjiaOrigin: "悌" },
          { char: "鲜", pinyin: "xiǎn", meaning: "少" },
        ],
        entityIds: ["youzi"],
      },
      {
        id: "1-5",
        original: "不好犯上而好作乱者，未之有也。",
        translation: "不喜欢冒犯上级却喜欢作乱的人，从来没有过。",
      },
      {
        id: "1-6",
        original: "君子务本，本立而道生。孝弟也者，其为仁之本与！",
        translation:
          "君子致力于根本，根本确立了，\u201c道\u201d就随之产生。孝悌大概就是仁的根本吧！",
        annotations: [
          { char: "与", pinyin: "yú", meaning: "同\u201c欤\u201d，语气词，表推测", isTongjia: true, tongjiaOrigin: "欤" },
        ],
        entityIds: ["junzi", "dao"],
      },
    ],
  },
  {
    id: "lunyu-2",
    bookId: "lunyu",
    order: 2,
    title: "为政第二",
    sentences: [
      {
        id: "2-1",
        original: "子曰：为政以德，譬如北辰，居其所而众星共之。",
        translation:
          "孔子说：以道德来治理国政，就像北极星一样，居于其位而群星都环绕着它。",
        annotations: [
          { char: "共", pinyin: "gǒng", meaning: "同\u201c拱\u201d，环绕、拱卫", isTongjia: true, tongjiaOrigin: "拱" },
        ],
        entityIds: ["confucius"],
      },
      {
        id: "2-2",
        original: "子曰：诗三百，一言以蔽之，曰：思无邪。",
        translation:
          "孔子说：《诗经》三百篇，用一句话来概括它，就是：思想没有邪念。",
        entityIds: ["confucius"],
      },
      {
        id: "2-3",
        original: "子曰：吾十有五而志于学，三十而立，四十而不惑，",
        translation:
          "孔子说：我十五岁立志学习，三十岁能自立，四十岁能不被迷惑，",
        annotations: [
          { char: "有", pinyin: "yòu", meaning: "同\u201c又\u201d，用于整数与零数之间", isTongjia: true, tongjiaOrigin: "又" },
        ],
        entityIds: ["confucius"],
      },
      {
        id: "2-4",
        original: "五十而知天命，六十而耳顺，七十而从心所欲，不逾矩。",
        translation:
          "五十岁懂得天命，六十岁能听进不同意见，七十岁能随心所欲，又不越出规矩。",
      },
      {
        id: "2-5",
        original: "子曰：温故而知新，可以为师矣。",
        translation: "孔子说：温习旧有的知识并能获得新的体会，就可以做老师了。",
        entityIds: ["confucius"],
      },
    ],
  },
  {
    id: "lunyu-3",
    bookId: "lunyu",
    order: 3,
    title: "八佾第三",
    sentences: [
      {
        id: "3-1",
        original: "孔子谓季氏：八佾舞于庭，是可忍也，孰不可忍也？",
        translation:
          "孔子谈到季氏说：他用天子才能用的八佾在庭院中奏乐舞蹈，这样的事都忍心做，还有什么不忍心做呢？",
        annotations: [
          { char: "佾", pinyin: "yì", meaning: "古代乐舞行列，一行八人为一佾" },
        ],
        entityIds: ["confucius"],
      },
      {
        id: "3-2",
        original: "三家者以雍彻。子曰：相维辟公，天子穆穆，奚取于三家之堂？",
        translation:
          "鲁国三家大夫在祭祀结束时唱《雍》诗撤祭。孔子说：《雍》诗说\u201c助祭的是诸侯，天子庄严穆穆\u201d，这怎能在三家的庙堂上唱呢？",
        annotations: [
          { char: "彻", pinyin: "chè", meaning: "撤除祭品" },
        ],
        entityIds: ["confucius", "luzhou"],
      },
      {
        id: "3-3",
        original: "子曰：人而不仁，如礼何？人而不仁，如乐何？",
        translation:
          "孔子说：做人却没有仁心，怎样对待礼仪呢？做人却没有仁心，怎样对待音乐呢？",
        entityIds: ["confucius"],
      },
      {
        id: "3-4",
        original: "林放问礼之本。子曰：大哉问！",
        translation:
          "林放问礼的根本。孔子说：这是一个意义重大问题啊！",
        entityIds: ["confucius"],
      },
      {
        id: "3-5",
        original: "与其奢也，宁俭；与其易也，宁戚。",
        translation:
          "与其奢侈，不如节俭；与其办理周备，不如内心哀伤。",
      },
    ],
  },
];

export const mockDailyQuote: DailyQuote = {
  id: "dq-1",
  text: "学而时习之，不亦说乎？",
  translation: "学了知识并按时温习，不也是令人愉悦的吗？",
  source: "论语·学而第一",
  chapterId: "lunyu-1",
};

export const mockProgress: LearningProgress[] = [
  {
    bookId: "lunyu",
    currentChapterOrder: 3,
    totalChapters: 20,
    readChapters: [1, 2],
    streakDays: 7,
    lastReadDate: "2026-06-19",
  },
  {
    bookId: "mengzi",
    currentChapterOrder: 1,
    totalChapters: 14,
    readChapters: [],
    streakDays: 0,
    lastReadDate: "",
  },
];

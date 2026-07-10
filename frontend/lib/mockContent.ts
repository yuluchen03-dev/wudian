/**
 * 悟典 - 趣味内容 Mock 数据
 * 金句卡片、情景小剧场
 */
import type { QuoteCard, QuoteCardDetail, Theater, TheaterDetail } from "./types";
import { theaterCoverImages, theaterRolePortraitImages } from "./visualAssets";

export const mockQuoteCards: QuoteCard[] = [
  { id: "qc_001", quote: "学而时习之，不亦说乎", source: "《论语·学而》", style: "ink_wash", imageKeyword: "水墨山水，竹林读书", backgroundImage: "/content/quote-backgrounds/qc_001.png", likeCount: 128, shareCount: 45, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_002", quote: "有朋自远方来，不亦乐乎", source: "《论语·学而》", style: "gold_seal", imageKeyword: "亭中相迎，金印点缀", backgroundImage: "/content/quote-backgrounds/qc_002.png", likeCount: 156, shareCount: 62, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_003", quote: "人不知而不愠，不亦君子乎", source: "《论语·学而》", style: "moonlight", imageKeyword: "月夜独坐窗前", backgroundImage: "/content/quote-backgrounds/qc_003.png", likeCount: 98, shareCount: 33, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_004", quote: "温故而知新，可以为师矣", source: "《论语·为政》", style: "bamboo_scroll", imageKeyword: "竹简展开，油灯", backgroundImage: "/content/quote-backgrounds/qc_004.png", likeCount: 142, shareCount: 51, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_005", quote: "学而不思则罔，思而不学则殆", source: "《论语·为政》", style: "ink_wash", imageKeyword: "文人执书沉思", backgroundImage: "/content/quote-backgrounds/qc_005.png", likeCount: 187, shareCount: 78, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_006", quote: "知之为知之，不知为不知，是知也", source: "《论语·为政》", style: "cloud_mist", imageKeyword: "云雾山间求知", backgroundImage: "/content/quote-backgrounds/qc_006.png", likeCount: 165, shareCount: 59, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_007", quote: "三人行，必有我师焉", source: "《论语·述而》", style: "gold_seal", imageKeyword: "三人行于山道", backgroundImage: "/content/quote-backgrounds/qc_007.png", likeCount: 201, shareCount: 88, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_008", quote: "己所不欲，勿施于人", source: "《论语·卫灵公》", style: "ink_wash", imageKeyword: "两人对坐递物", backgroundImage: "/content/quote-backgrounds/qc_008.png", likeCount: 234, shareCount: 102, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_009", quote: "君子坦荡荡，小人长戚戚", source: "《论语·述而》", style: "moonlight", imageKeyword: "月光下广阔平原", backgroundImage: "/content/quote-backgrounds/qc_009.png", likeCount: 178, shareCount: 71, createdAt: "2024-06-01T00:00:00" },
  { id: "qc_010", quote: "见贤思齐焉，见不贤而内自省也", source: "《论语·里仁》", style: "cloud_mist", imageKeyword: "镜中两人影", backgroundImage: "/content/quote-backgrounds/qc_010.png", likeCount: 145, shareCount: 56, createdAt: "2024-06-01T00:00:00" },
];

export const mockQuoteCardDetail: QuoteCardDetail = {
  id: "qc_001",
  quote: "学而时习之，不亦说乎",
  source: "《论语·学而》",
  style: "ink_wash",
  imageKeyword: "水墨山水，一文人坐于竹林中展卷读书，墨色淡雅",
  backgroundImage: "/content/quote-backgrounds/qc_001.png",
  likeCount: 128,
  shareCount: 45,
  createdAt: "2024-06-01T00:00:00",
  vernacular: "学了知识然后按时温习它，不也是很愉快的事吗？",
  modernInterpretation:
    "学习不是一次性的消费，而是反复的练习。就像健身一样，练过一次不代表掌握了，反复操练才能真正内化为能力。孔子告诉我们：复习本身就是快乐之源。",
  backgroundColor: "#faf6ed",
  accentColor: "#b91c1c",
  tags: ["学习", "温习", "论语"],
  isLiked: false,
};

const baseMockTheaters: Theater[] = [
  {
    id: "th_001",
    title: "学而时习之 —— 新人培训的正确打开方式",
    summary: "老板引用孔子的话，告诉新人培训完不能丢一边，要反复操练才能内化为能力。",
    classicalSource: "《论语·学而》",
    modernSetting: "职场",
    coverKeyword: "现代办公室培训场景",
    sceneCount: 1,
    likeCount: 89,
    viewCount: 342,
    createdAt: "2024-06-01T00:00:00",
  },
  {
    id: "th_002",
    title: "三人行必有我师 —— 代码评审中的谦逊",
    summary: "资深程序员在 code review 中发现实习生写的算法更优雅，引用孔子的话表达虚心学习。",
    classicalSource: "《论语·述而》",
    modernSetting: "职场",
    coverKeyword: "程序员围在屏幕前看代码",
    sceneCount: 1,
    likeCount: 76,
    viewCount: 298,
    createdAt: "2024-06-02T00:00:00",
  },
  {
    id: "th_003",
    title: "己所不欲勿施于人 —— 小组作业的分工困境",
    summary: "大学小组作业中，组长想把最难的活推给别人，被室友用孔子的话点醒。",
    classicalSource: "《论语·卫灵公》",
    modernSetting: "校园",
    coverKeyword: "大学宿舍讨论作业",
    sceneCount: 1,
    likeCount: 112,
    viewCount: 456,
    createdAt: "2024-06-03T00:00:00",
  },
  {
    id: "th_004",
    title: "温故而知新 —— 老员工的二次成长",
    summary: "工作五年的老员工陷入瓶颈，被导师提醒重新梳理基础，在复习中发现新洞察。",
    classicalSource: "《论语·为政》",
    modernSetting: "职场",
    coverKeyword: "咖啡馆对坐讨论",
    sceneCount: 1,
    likeCount: 67,
    viewCount: 234,
    createdAt: "2024-06-04T00:00:00",
  },
  {
    id: "th_005",
    title: "君子和而不同 —— 创业团队的分歧",
    summary: "创业团队两个合伙人因产品方向激烈争执，最终在尊重分歧中找到更好的方案。",
    classicalSource: "《论语·子路》",
    modernSetting: "职场",
    coverKeyword: "创业办公室白板前辩论",
    sceneCount: 1,
    likeCount: 95,
    viewCount: 387,
    createdAt: "2024-06-05T00:00:00",
  },
  {
    id: "th_006",
    title: "见贤思齐 —— 实习生眼中的光",
    summary: "实习生被公司顶尖工程师的代码震撼，决心向他看齐，开启自我提升之路。",
    classicalSource: "《论语·里仁》",
    modernSetting: "校园",
    coverKeyword: "图书馆看代码惊叹",
    sceneCount: 1,
    likeCount: 83,
    viewCount: 312,
    createdAt: "2024-06-06T00:00:00",
  },
];

export const mockTheaters: Theater[] = baseMockTheaters.map((theater) => ({
  ...theater,
  coverImage: theater.coverImage ?? theaterCoverImages[theater.id],
}));

export const mockTheaterDetail: TheaterDetail = {
  id: "th_001",
  title: "学而时习之 —— 新人培训的正确打开方式",
  summary: "老板引用孔子的话，告诉新人培训完不能丢一边，要反复操练才能内化为能力。",
  classicalSource: "《论语·学而》",
  modernSetting: "职场",
  coverKeyword: "现代办公室培训场景，投影仪上显示古文，水墨融合风格",
  sceneCount: 1,
  likeCount: 89,
  viewCount: 342,
  createdAt: "2024-06-01T00:00:00",
  tags: ["学习", "职场", "培训"],
  moral: "学习不是一次性事件，而是反复练习的过程。培训的价值在于后续的实践和复盘，而非课堂上的记录。",
  roles: [
    {
      name: "孔总监",
      description: "部门总监，儒雅随和但眼光犀利",
      classicalOrigin: "孔子",
      avatarKeyword: "中年儒雅男主管",
      objective: "让新人承认记笔记不等于学会，并接受持续演练",
      fear: "培训变成一次性打卡，团队继续犯同样的错",
      belief: "知识必须在行动中反复校正，才会成为能力",
      strategy: "先提问暴露空洞，再给出可执行练习",
      conflictTrigger: "把学习当成听过、记过、收藏过",
      stageAction: "合上投影遥控器，留住正要离场的人",
    },
    {
      name: "小白",
      description: "刚入职的应届生，热情但容易三分钟热度",
      classicalOrigin: "新学子",
      avatarKeyword: "年轻职员",
      objective: "证明自己已经完成培训，可以马上进入正式工作",
      fear: "被发现只是抄了笔记、没有真正掌握",
      belief: "努力留下痕迹就等于努力有效",
      strategy: "用兴奋和笔记本掩饰心虚，最后转向承诺练习",
      conflictTrigger: "被要求当场复述和演练",
      stageAction: "抱紧笔记本，答不上来时翻页越来越快",
    },
  ],
  scenes: [
    {
      title: "第一幕：培训结束",
      setting: "公司培训室，投影仪刚关掉，新人小白收拾东西准备走",
      lines: [
        { role: "小白", text: "孔总监，三天的入职培训结束了，内容我都记在笔记本上了！", emotion: "(兴奋地)", isOriginalVerse: false },
        { role: "孔总监", text: "记下来了？那我问你，第二天讲的客户沟通流程，你能复述一遍吗？", emotion: "(微笑)", isOriginalVerse: false },
        { role: "小白", text: "呃……大概是先了解需求，再……那个……", emotion: "(挠头)", isOriginalVerse: false },
        { role: "孔总监", text: "学而时习之，不亦说乎。培训完不是终点，反复操练才是开始。", emotion: "(语重心长)", isOriginalVerse: true },
        { role: "小白", text: "您的意思是……我还得回去复习？", emotion: "(疑惑)", isOriginalVerse: false },
        { role: "孔总监", text: "不止复习。下周你把沟通流程对着镜子演练五遍，然后我来当你的客户。练到肌肉记忆，才算真正学到了。", emotion: "(认真地)", isOriginalVerse: false },
        { role: "小白", text: "我明白了！就像学游泳，光看教程不下水是学不会的。", emotion: "(恍然大悟)", isOriginalVerse: false },
        { role: "孔总监", text: "孺子可教。去吧，一周后我来验收。", emotion: "(欣慰地点头)", isOriginalVerse: false },
      ],
    },
  ],
};

mockTheaterDetail.coverImage = mockTheaterDetail.coverImage ?? theaterCoverImages[mockTheaterDetail.id];
mockTheaterDetail.roles = mockTheaterDetail.roles.map((role, index) => ({
  ...role,
  portraitImage:
    role.portraitImage ?? theaterRolePortraitImages[`${mockTheaterDetail.id}:${index}`],
}));

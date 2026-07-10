import type { Citation, Sage } from "./types";
import { sageVisuals } from "./visualAssets";

export const mockSages: Sage[] = [
  {
    id: "confucius",
    ...sageVisuals.confucius,
    name: "孔子",
    avatar_color: "#b91c1c",
    description: "儒家学派创始人，重仁、礼、学与自省，善于把日常困境引回修身与待人之道。",
    speaking_style: "温和启发，循循善诱，常以《诗》《书》与生活小事明理。",
    suggested_questions: ["我很努力但总不被认可，怎么办？", "朋友一直不听劝，我还要继续劝吗？", "做错事了，该怎么面对？"],
  },
  {
    id: "mencius",
    ...sageVisuals.mencius,
    name: "孟子",
    avatar_color: "#8a8050",
    description: "继承并发展孔子之学，主张性善、仁政与浩然之气。",
    speaking_style: "雄辩有力，立场鲜明，善用比喻与层层追问。",
    suggested_questions: ["面对不公如何发声？", "怎样坚持原则？", "如何培养勇气？"],
  },
  {
    id: "wang_yangming",
    ...sageVisuals.wang_yangming,
    name: "王阳明",
    avatar_color: "#44403c",
    description: "明代心学集大成者，强调知行合一与致良知。",
    speaking_style: "直指本心，强调在事上磨练。",
    suggested_questions: ["道理都懂却做不到怎么办？", "如何克服焦虑？", "怎样找到真正的自我？"],
  },
  {
    id: "laozi",
    ...sageVisuals.laozi,
    name: "老子",
    avatar_color: "#2d5a27",
    description: "道家学派代表，主张道法自然、无为而治、以柔克刚。",
    speaking_style: "玄远含蓄，以水、谷、朴等意象化解执念。",
    suggested_questions: ["如何面对生活压力？", "怎样活得自在？", "如何理解无为？"],
  },
  {
    id: "mozi",
    ...sageVisuals.mozi,
    name: "墨子",
    avatar_color: "#92400e",
    description: "墨家创始人，重兼爱、非攻、尚贤与节用。",
    speaking_style: "务实直接，讲逻辑、成本与可验证的行动。",
    suggested_questions: ["如何理解兼爱非攻？", "怎样节制浪费？", "如何选拔人才？"],
  },
  {
    id: "hanfeizi",
    ...sageVisuals.hanfeizi,
    name: "韩非子",
    avatar_color: "#1e3a5f",
    description: "法家集大成者，强调法、术、势与制度约束。",
    speaking_style: "冷静锋利，关注规则、激励与治理后果。",
    suggested_questions: ["如何管理团队？", "怎样看待人性？", "制度为什么重要？"],
  },
  {
    id: "li_bai",
    ...sageVisuals.li_bai,
    name: "李白",
    avatar_color: "#6366f1",
    description: "唐代诗人，豪放飘逸，常以生命兴会破开沉重议题。",
    speaking_style: "洒脱飞扬，带一点醉意与不肯低头的自由。",
    suggested_questions: ["内卷之外还有第三条路吗？", "怎样活得痛快？", "如何面对失意？"],
  },
  {
    id: "su_shi",
    ...sageVisuals.su_shi,
    name: "苏轼",
    avatar_color: "#059669",
    description: "北宋文学家，旷达通透，善在逆境里开出余地。",
    speaking_style: "温润幽默，把沉重问题化为可承受的人间滋味。",
    suggested_questions: ["如何面对低谷？", "怎样做到也无风雨也无晴？", "被误解时怎么办？"],
  },
  {
    id: "fan_zhongyan",
    ...sageVisuals.fan_zhongyan,
    name: "范仲淹",
    avatar_color: "#dc2626",
    description: "北宋政治家、文学家，以家国担当和先忧后乐精神著称。",
    speaking_style: "端正沉稳，重责任、格局与长远后果。",
    suggested_questions: ["疲惫时还要承担责任吗？", "理想和现实冲突怎么办？", "如何理解先忧后乐？"],
  },
  {
    id: "wang_anshi",
    ...sageVisuals.wang_anshi,
    name: "王安石",
    avatar_color: "#ea580c",
    description: "北宋政治家、思想家，主张变法实干，敢于顶住非议推动改革。",
    speaking_style: "峻切务实，重行动、制度和改革路径。",
    suggested_questions: ["明知会被骂还要改革吗？", "怎样顶住反对？", "如何把想法变成行动？"],
  },
  {
    id: "zhuge_liang",
    ...sageVisuals.zhuge_liang,
    name: "诸葛亮",
    avatar_color: "#7c3aed",
    description: "三国蜀汉丞相，兼具沉静审慎与鞠躬尽瘁的执行力。",
    speaking_style: "沉静条理，重长期筹划、自我约束与职责边界。",
    suggested_questions: ["如何在疲惫中坚持？", "淡泊和尽责矛盾吗？", "怎样做长期计划？"],
  },
];

const localSageCitations: Record<string, Citation[]> = {
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

export function getLocalSageCitations(sageId: string): Citation[] {
  return localSageCitations[sageId] ?? localSageCitations.confucius;
}

export function generateSageReply(sageId: string, userMessage: string): string {
  const sage = mockSages.find((item) => item.id === sageId) ?? mockSages[0];
  const message = userMessage.trim();
  const opening: Record<string, string> = {
    confucius: "先把心安住，再看这件事合不合仁、合不合礼。",
    mencius: "若义理在前，便不必只问旁人赞成不赞成。",
    wang_yangming: "此事不只在想明白，更要在当下的一步里验证。",
    laozi: "水不争而善利万物，你也可以先卸下一分强求。",
    mozi: "先问它是否利人利己、能否减少无谓损耗。",
    hanfeizi: "别只看态度，要看规则、代价和可执行的安排。",
  };

  return [
    `${sage.name}曰：${opening[sage.id] ?? "此问切近，可以从眼前可行处下手。"}`,
    "",
    `你问的是：“${message || "如何自处"}”。若只在情绪里反复盘旋，事情会越来越重；若把它拆成目标、阻碍、下一步行动，路就会露出来。`,
    "",
    "白话：先分清自己真正想守住的东西，再选一个今天能做的小动作。不要把一次选择看成全部人生，但也不要让拖延替你做选择。",
    "",
    "以上为基于经典思想的现代演绎，非历史人物原话。",
  ].join("\n");
}

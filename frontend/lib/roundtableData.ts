/**
 * 百家论道 - 圆桌论道 Mock 数据
 * 预设话题、Mock辩论数据、圣贤配色方案
 */
import type { Sage, Citation } from "./types";

// ============================================================
// 预设话题
// ============================================================

export const presetTopics: string[] = [
  "我该不该躺平？",
  "该不该为钱妥协？",
  "内卷时代如何安放自己？",
  "面对不公，该沉默还是发声？",
  "知易行难，如何做到知行合一？",
  "君子应该如何对待金钱？",
];

// ============================================================
// 圣贤配色方案（用于论道场景）
// ============================================================

export const sageColors: Record<string, { primary: string; bg: string; text: string }> = {
  confucius: {
    primary: "#b91c1c", // 朱砂红 - 儒
    bg: "bg-cinnabar-50",
    text: "text-cinnabar-700",
  },
  mencius: {
    primary: "#8a8050", // 青铜色 - 儒
    bg: "bg-bronze-400/10",
    text: "text-bronze-600",
  },
  wang_yangming: {
    primary: "#44403c", // 墨色 - 心学
    bg: "bg-ink-100",
    text: "text-ink-700",
  },
  laozi: {
    primary: "#2d5a27", // 深绿 - 道
    bg: "bg-bamboo-50",
    text: "text-bamboo-700",
  },
  mozi: {
    primary: "#92400e", // 赭石 - 墨
    bg: "bg-amber-50",
    text: "text-amber-700",
  },
  hanfeizi: {
    primary: "#1e3a5f", // 深蓝 - 法
    bg: "bg-blue-50",
    text: "text-blue-700",
  },
  li_bai: {
    primary: "#6366f1",
    bg: "bg-indigo-50",
    text: "text-indigo-700",
  },
  su_shi: {
    primary: "#059669",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
  },
  fan_zhongyan: {
    primary: "#dc2626",
    bg: "bg-red-50",
    text: "text-red-700",
  },
  wang_anshi: {
    primary: "#ea580c",
    bg: "bg-orange-50",
    text: "text-orange-700",
  },
  zhuge_liang: {
    primary: "#7c3aed",
    bg: "bg-violet-50",
    text: "text-violet-700",
  },
};

// ============================================================
// 论道相关类型
// ============================================================

export interface DebateClash {
  fromSageId: string;
  toSageId: string;
  type: "agree" | "disagree" | "extend" | "reframe" | "refute";
  summary: string;
}

export interface SageRoundSpeech {
  id?: string;
  sageId: string;
  roundNumber?: number;
  content: string;
  vernacular?: string;
  quote?: string;
  source?: string;
  citations: Citation[];
  sentenceEvidence?: Array<{
    sentence: string;
    source: string;
    original: string;
    similarity: number;
    verifiable: boolean;
  }>;
  isStreaming: boolean;
  isComplete: boolean;
  isGuest?: boolean;
}

// ============================================================
// Mock 论道数据（用于开发和演示）
// ============================================================

export interface MockDebateData {
  topic: string;
  speeches: SageRoundSpeech[];
  clashes: DebateClash[];
}

/** 根据话题生成 Mock 论道数据 */
export function getMockDebateData(topic: string): MockDebateData {
  const topicKey = topic.replace(/？/g, "").replace(/\?/g, "").trim();

  // 勇气话题
  if (topicKey.includes("勇气")) {
    return {
      topic,
      speeches: [
        {
          sageId: "confucius",
          content:
            "子曰：勇者不惧。然勇有真伪之分。血气之勇，逞一时之快，匹夫之勇也；义理之勇，见义不为无勇也，临难不苟免，见利不苟得，此为君子之勇。吾尝言「仁者必有勇」，真正的勇气源于内心的仁德。有仁心者，见不义之事，虽千万人吾往矣，非为争胜，乃为守道。又云「知耻近乎勇」，能知耻而后勇，勇于改过迁善，亦是大勇。汝等细思，何为真勇？",
          citations: [
            { text: "勇者不惧", source: "《论语·子罕》", chapter: "子罕篇", verse_no: 29, similarity: 0.96, type: "verse" },
            { text: "见义不为无勇也", source: "《论语·为政》", chapter: "为政篇", verse_no: 24, similarity: 0.92, type: "verse" },
            { text: "仁者必有勇", source: "《论语·宪问》", chapter: "宪问篇", verse_no: 4, similarity: 0.88, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "mencius",
          content:
            "孟子曰：此言甚善，然吾当更进一步。吾善养吾浩然之气！勇气非凭血气之勇，乃由道义而生。集义所生者，非义袭而取之也。行有不慊于心，则馁矣。夫子言「仁者必有勇」，吾深以为然。然吾更言「虽千万人，吾往矣」——此非匹夫之勇，乃浩然正气充塞天地之大勇也。富贵不能淫，贫贱不能移，威武不能屈，此之谓大丈夫！真正的勇气，是在任何境遇中都不动摇心中的道义。吾以为，勇气有三：不惧强权，不媚世俗，不违本心。此三者，方为大勇。",
          citations: [
            { text: "我善养吾浩然之气", source: "《孟子·公孙丑上》", chapter: "公孙丑上", verse_no: 2, similarity: 0.95, type: "verse" },
            { text: "富贵不能淫，贫贱不能移，威武不能屈", source: "《孟子·滕文公下》", chapter: "滕文公下", verse_no: 2, similarity: 0.93, type: "verse" },
            { text: "虽千万人，吾往矣", source: "《孟子·公孙丑上》", chapter: "公孙丑上", verse_no: 2, similarity: 0.90, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "wang_yangming",
          content:
            "阳明子曰：二位所言，皆鞭辟入里。然吾有一问：汝等说勇，皆自外求之——求诸仁义、求诸浩气。吾则以为，勇从心生，不假外求。良知自知善恶，自知当为不当为。致得良知，则临事自然不惧，非先立一个「勇」字而后行也。知者行之始，行者知之成。真知必能行，不行不可谓知。汝若知孝，必能孝，方为真知孝。同理，汝若真知当勇，必能勇。吾平生所学，不过「致良知」三字。良知澄明，则勇气自在其中。人须在事上磨炼，方立得住。空谈勇气而不敢行，只是未知勇耳。",
          citations: [
            { text: "知者行之始，行者知之成", source: "《传习录》", chapter: "卷上", verse_no: 5, similarity: 0.94, type: "verse" },
            { text: "致良知", source: "《传习录》", chapter: "卷下", verse_no: 12, similarity: 0.91, type: "verse" },
            { text: "人须在事上磨炼，方立得住", source: "《传习录》", chapter: "卷上", verse_no: 8, similarity: 0.87, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "laozi",
          content:
            "老子曰：勇哉？怯哉？天下皆知勇之为勇，斯怯已。上善若水，水善利万物而不争，此乃大勇也。夫唯不争，故天下莫能与之争。真正的勇气，非逞强好胜，乃柔弱胜刚强。吾闻「知人者智，自知者明」，能自知者，方为真勇。又云「知足不辱，知止不殆」，知所当止而止之，非怯也，乃智勇兼备。世人以争为勇，吾以不争为勇；世人以进为勇，吾以退为勇。反者道之动，弱者道之用。汝等细思之。",
          citations: [
            { text: "上善若水，水善利万物而不争", source: "《道德经》", chapter: "第八章", verse_no: 1, similarity: 0.95, type: "verse" },
            { text: "知人者智，自知者明", source: "《道德经》", chapter: "第三十三章", verse_no: 1, similarity: 0.92, type: "verse" },
            { text: "柔弱胜刚强", source: "《道德经》", chapter: "第三十六章", verse_no: 1, similarity: 0.89, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "mozi",
          content:
            "墨子曰：诸子所言，各有其理。然墨翟以为，勇非独善其身之事，乃利天下之器。兼相爱，交相利——为天下兴利除害，方为大勇。杀一人，谓之不义，必有一死罪矣。为义而战，止暴禁非，此乃真勇。吾最不取命定之说——「赖其力者生，不赖其力者不生」。人人当强力而为，不可坐待天命。勇气者，非空谈心性，乃身体力行。言必信，行必果，使言行之合，犹合符节也。空言勇而不行，与怯何异？",
          citations: [
            { text: "兼相爱，交相利", source: "《墨子·兼爱上》", chapter: "兼爱上", verse_no: 1, similarity: 0.94, type: "verse" },
            { text: "赖其力者生，不赖其力者不生", source: "《墨子·非乐上》", chapter: "非乐上", verse_no: 1, similarity: 0.91, type: "verse" },
            { text: "言必信，行必果", source: "《墨子·兼爱下》", chapter: "兼爱下", verse_no: 1, similarity: 0.88, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "hanfeizi",
          content:
            "韩非子曰：尔等空谈勇怯，皆务虚之论。人趋利避害，本性使然。勇者，利之所在则趋，害之所在则避——此乃人之常情，非善非恶。赏罚者，利器也。明主设赏以劝勇，设罚以惩怯，则勇士自至。吾闻「法不阿贵，绳不挠曲」，以法治国，以制度驱人，远比以德感化可靠。又云「事在四方，要在中央」，勇气需有方向，不可匹夫之勇。算清利害，务实循法，方为真勇。",
          citations: [
            { text: "法不阿贵，绳不挠曲", source: "《韩非子·有度》", chapter: "有度", verse_no: 1, similarity: 0.93, type: "verse" },
            { text: "事在四方，要在中央", source: "《韩非子·物权》", chapter: "物权", verse_no: 1, similarity: 0.90, type: "verse" },
            { text: "赏罚者，利器也", source: "《韩非子·二柄》", chapter: "二柄", verse_no: 1, similarity: 0.87, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
      ],
      clashes: [
        {
          fromSageId: "mencius",
          toSageId: "confucius",
          type: "extend",
          summary: "继承孔子「仁者必有勇」，进一步提出浩然之气",
        },
        {
          fromSageId: "wang_yangming",
          toSageId: "confucius",
          type: "reframe",
          summary: "将勇气从外在仁义转向内在良知",
        },
        {
          fromSageId: "laozi",
          toSageId: "confucius",
          type: "reframe",
          summary: "以「不争」重新定义勇气",
        },
        {
          fromSageId: "mozi",
          toSageId: "laozi",
          type: "disagree",
          summary: "认为不争近乎认命，主张强力而为",
        },
        {
          fromSageId: "hanfeizi",
          toSageId: "confucius",
          type: "disagree",
          summary: "认为空谈心性无用，当以赏罚驱人",
        },
      ],
    };
  }

  // 人性善恶话题
  if (topicKey.includes("人性") || topicKey.includes("善") || topicKey.includes("恶")) {
    return {
      topic,
      speeches: [
        {
          sageId: "confucius",
          content:
            "子曰：性相近也，习相远也。吾未尝直言性善性恶，盖人性本无善恶之定名，近朱者赤，近墨者黑。然吾深信，人皆有向善之心。仁远乎哉？我欲仁，斯仁至矣。只要人愿意追求仁德，仁便在眼前。故教化之功，在于唤醒人心中本有的善端。有教无类，因材施教，便是相信每个人都能成为君子。",
          citations: [
            { text: "性相近也，习相远也", source: "《论语·阳货》", chapter: "阳货篇", verse_no: 2, similarity: 0.97, type: "verse" },
            { text: "仁远乎哉？我欲仁，斯仁至矣", source: "《论语·述而》", chapter: "述而篇", verse_no: 30, similarity: 0.91, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
          sageId: "mencius",
          content:
            "孟子曰：人性之善也，犹水之就下也。人无有不善，水无有不下！恻隐之心，人皆有之；羞恶之心，人皆有之；辞让之心，人皆有之；是非之心，人皆有之。此四端者，非由外铄我也，我固有之也。夫子言「性相近」，吾则直言「性善」！人之所以为不善，非才之罪也，乃陷溺其心者也。譬如牛山之木，本来茂盛，旦旦而伐之，遂成濯濯。人之良心，亦是如此——放失本心，方为不善。故学问之道无他，求其放心而已矣。",
          citations: [
            { text: "恻隐之心，人皆有之", source: "《孟子·告子上》", chapter: "告子上", verse_no: 6, similarity: 0.95, type: "verse" },
            { text: "人性之善也，犹水之就下也", source: "《孟子·告子上》", chapter: "告子上", verse_no: 2, similarity: 0.93, type: "verse" },
            { text: "学问之道无他，求其放心而已矣", source: "《孟子·告子上》", chapter: "告子上", verse_no: 11, similarity: 0.88, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
        {
        sageId: "wang_yangming",
        content:
            "阳明子曰：善恶之辨，千古聚讼。吾之见解，与二位略有不同。良知是心之本体，无善无恶心之体，有善有恶意之动，知善知恶是良知，为善去恶是格物。人性本无善恶之定相，如明镜然，物来则照，善来照善，恶来照恶，镜体本无善恶。然良知自知善恶——这便是人性中最可贵处。人皆有良知，不虑而知，不学而能。故善恶非先天注定，乃后天意念所生。致得良知，则善恶自明，为善去恶，自然成就。",
          citations: [
            { text: "无善无恶心之体，有善有恶意之动", source: "《传习录》", chapter: "卷下", verse_no: 6, similarity: 0.94, type: "verse" },
            { text: "知善知恶是良知", source: "《传习录》", chapter: "卷下", verse_no: 6, similarity: 0.92, type: "verse" },
            { text: "良知是心之本体", source: "《传习录》", chapter: "卷上", verse_no: 8, similarity: 0.89, type: "verse" },
          ],
          isStreaming: false,
          isComplete: true,
        },
      ],
      clashes: [
        {
          fromSageId: "mencius",
          toSageId: "confucius",
          type: "extend",
          summary: "将孔子「性相近」发展为明确的「性善论」",
        },
        {
          fromSageId: "wang_yangming",
          toSageId: "mencius",
          type: "reframe",
          summary: "超越善恶二分，提出「无善无恶心之体」",
        },
      ],
    };
  }

  // 默认话题 - 通用回复
  return {
    topic,
    speeches: [
      {
        sageId: "confucius",
        content: `子曰：善哉斯问。夫「${topic}」之事，当以仁为本，以礼为节。吾尝言「己所不欲，勿施于人」，凡事反求诸己，行有不得者，皆反求诸己。修身以敬，修己以安人。先正其身，而后能正人。此乃君子之道也。吾又云「学而不思则罔，思而不学则殆」，面对此等深问，当博学之、审问之、慎思之、明辨之、笃行之。`,
        citations: [
          { text: "己所不欲，勿施于人", source: "《论语·卫灵公》", chapter: "卫灵公篇", verse_no: 24, similarity: 0.93, type: "verse" },
          { text: "学而不思则罔，思而不学则殆", source: "《论语·为政》", chapter: "为政篇", verse_no: 15, similarity: 0.88, type: "verse" },
        ],
        isStreaming: false,
        isComplete: true,
      },
      {
        sageId: "mencius",
        content: `孟子曰：夫子所言甚善。然吾以为，论「${topic}」，不可不辨义利之分。孟子见梁惠王，王曰「何以利吾国」，吾对曰「王何必曰利，亦有仁义而已矣」。凡事以义为先，利自在其中。浩然之气，至大至刚，以直养而无害，则塞于天地之间。行有不慊于心，则馁矣。汝当集义所生，非义袭而取之也。`,
        citations: [
          { text: "王何必曰利，亦有仁义而已矣", source: "《孟子·梁惠王上》", chapter: "梁惠王上", verse_no: 1, similarity: 0.91, type: "verse" },
          { text: "浩然之气，至大至刚", source: "《孟子·公孙丑上》", chapter: "公孙丑上", verse_no: 2, similarity: 0.89, type: "verse" },
        ],
        isStreaming: false,
        isComplete: true,
      },
      {
        sageId: "wang_yangming",
        content: `阳明子曰：二位所言，各有所据。然吾平生所学，不过「致良知」三字。论「${topic}」，不必向外驰求，当反观自心。良知人人本具，不虑而知，不学而能。只是被私欲遮蔽，不能显发。若能去得人欲之私，存得天理之正，则本体澄明，自知此问当如何答。知者行之始，行者知之成。莫要停留在口耳之学，当于事上磨炼。`,
        citations: [
          { text: "致良知", source: "《传习录》", chapter: "卷下", verse_no: 12, similarity: 0.94, type: "verse" },
          { text: "知者行之始，行者知之成", source: "《传习录》", chapter: "卷上", verse_no: 5, similarity: 0.91, type: "verse" },
        ],
        isStreaming: false,
        isComplete: true,
      },
    ],
    clashes: [
      {
        fromSageId: "mencius",
        toSageId: "confucius",
        type: "extend",
        summary: "认同孔子仁义之说，进一步辨析义利",
      },
      {
        fromSageId: "wang_yangming",
        toSageId: "confucius",
        type: "reframe",
        summary: "从外在修身转向内在致良知",
      },
    ],
  };
}

/**
 * 简单的交锋分析（前端关键词匹配）
 * 检查后一位圣贤的回复中是否提到了前一位圣贤的观点
 */
export function analyzeClashes(
  speeches: SageRoundSpeech[],
  sageIds: string[]
): DebateClash[] {
  const clashes: DebateClash[] = [];

  for (let i = 1; i < speeches.length; i++) {
    const prev = speeches[i - 1];
    const curr = speeches[i];
    if (!curr.isComplete || !prev.isComplete) continue;

    const content = curr.content;

    // 认同关键词
    const agreeKeywords = ["深以为然", "此言甚善", "所言甚善", "亦如是", "吾亦云", "赞同", "所言极是"];
    // 反驳关键词
    const disagreeKeywords = ["此言差矣", "吾以为不然", "非也", "不然", "过矣", "未尽然"];
    // 延展关键词
    const extendKeywords = ["更进一步", "吾则", "吾更言", "当更", "进一步", "更"];
    // 重构关键词
    const reframeKeywords = ["不同", "略有不同", "吾之见解", "另有一说", "吾以为"];

    let type: DebateClash["type"] = "extend";
    let summary = "";

    if (agreeKeywords.some((kw) => content.includes(kw))) {
      type = "agree";
      summary = `认同${getSageName(prev.sageId)}的观点`;
    } else if (disagreeKeywords.some((kw) => content.includes(kw))) {
      type = "disagree";
      summary = `与${getSageName(prev.sageId)}观点相左`;
    } else if (reframeKeywords.some((kw) => content.includes(kw))) {
      type = "reframe";
      summary = `对${getSageName(prev.sageId)}的观点提出新解`;
    } else if (extendKeywords.some((kw) => content.includes(kw))) {
      type = "extend";
      summary = `继承${getSageName(prev.sageId)}的思想`;
    } else {
      // 默认：检查是否提到了前一位圣贤的核心概念
      continue;
    }

    clashes.push({
      fromSageId: curr.sageId,
      toSageId: prev.sageId,
      type,
      summary,
    });
  }

  return clashes;
}

/** 获取圣贤名称 */
function getSageName(sageId: string): string {
  const names: Record<string, string> = {
    confucius: "孔子",
    mencius: "孟子",
    wang_yangming: "王阳明",
    laozi: "老子",
    mozi: "墨子",
    hanfeizi: "韩非子",
    li_bai: "李白",
    su_shi: "苏轼",
    fan_zhongyan: "范仲淹",
    wang_anshi: "王安石",
    zhuge_liang: "诸葛亮",
  };
  return names[sageId] || sageId;
}

/** 获取圣贤时代标签 */
export function getSageEra(sageId: string): string {
  const eras: Record<string, string> = {
    confucius: "春秋·鲁",
    mencius: "战国·邹",
    wang_yangming: "明代·浙江",
    laozi: "春秋·楚",
    mozi: "战国·鲁",
    hanfeizi: "战国·韩",
    li_bai: "唐代",
    su_shi: "宋代",
    fan_zhongyan: "宋代",
    wang_anshi: "宋代",
    zhuge_liang: "三国·蜀",
  };
  return eras[sageId] || "";
}

/** 获取圣贤核心思想标签 */
export function getSageCoreThought(sageId: string): string {
  const thoughts: Record<string, string> = {
    confucius: "仁礼之道",
    mencius: "性善·仁政",
    wang_yangming: "知行合一",
    laozi: "道法自然",
    mozi: "兼爱非攻",
    hanfeizi: "以法治国",
    li_bai: "尽兴而活",
    su_shi: "旷达超脱",
    fan_zhongyan: "家国担当",
    wang_anshi: "实干变法",
    zhuge_liang: "淡泊尽责",
  };
  return thoughts[sageId] || "";
}

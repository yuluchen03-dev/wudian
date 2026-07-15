import type { CuratedCourtCase } from "./thoughtCourtTypes";

const sages = ["confucius", "mencius", "laozi"];

export const CURATED_COURT_CASES: CuratedCourtCase[] = [
  {
    id: "recognition",
    label: "职场认可",
    question: "我很努力，却总不被领导认可，怎么办？",
    conflicts: ["外界认可", "自我价值", "行动选择"],
    sages,
    evidence: [
      { id: "recognition-confucius-1", sageId: "confucius", original: "人不知而不愠，不亦君子乎？", source: "《论语·学而》", interpretation: "先把自我价值与他人一时的认可拆开，再决定如何沟通。", boundary: "这不等于默忍不公平评价或放弃争取合理回报。", verified: true },
      { id: "recognition-mencius-1", sageId: "mencius", original: "行有不得者，皆反求诸己。", source: "《孟子·离娄上》", interpretation: "先检查成果表达、期望对齐和能力缺口，但不把所有责任都归给自己。", boundary: "反求诸己是获得行动权，不是为系统性不公开脱。", verified: true },
      { id: "recognition-laozi-1", sageId: "laozi", original: "知人者智，自知者明。", source: "《道德经·第三十三章》", interpretation: "分清你真正需要的是公平回报、成长机会，还是单纯被看见。", boundary: "自知不意味着退出竞争或放弃为自己发声。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "稳住内在尺度，再正名沟通", content: "不必把一次不被看见等同于价值不存在。先把成果、责任和评价标准说清。", evidenceIds: ["recognition-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "反求诸己，但不放弃尊严", content: "查看自己能改变的部分，同时为合理的评价与边界发声。", evidenceIds: ["recognition-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "辨认执念，保留转身的空间", content: "看清你要争取的究竟是什么。如果环境长期无法给出公平回报，改变路径也是行动。", evidenceIds: ["recognition-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都主张先恢复行动权，但孟子更强调尊严与应得回报。" },
      { fromSageId: "laozi", toSageId: "confucius", type: "reframe", summary: "老子不只谈如何被认可，而是追问是否仍值得留在当前评价体系。" },
    ],
    report: {
      conflict: "你的努力与组织的评价机制脱节，同时你把部分自我价值交给了外部认可。",
      consensus: ["先把情绪与事实拆开。", "用可验证的成果和明确对话恢复行动权。"],
      divergences: ["应继续修身与沟通，还是尽快改变所在环境。"],
      actions: {
        self: ["写下三项不依赖他人表态也能确认的成果。"],
        relationship: ["预约一次 20 分钟对话，请领导明确评价标准和差距。"],
        change: ["设定一个月观察期；如果标准仍模糊或成果持续被忽视，开始准备内部转岗或外部机会。"],
      },
      reservation: "悟典无法代替你判断当前组织是否值得继续投入，这需要你结合收入、成长、安全感和现实机会判断。",
    },
  },
  {
    id: "departure",
    label: "职业去留",
    question: "稳定但不喜欢的工作，要不要离开？",
    conflicts: ["现实安全", "个人志向", "改变时机"],
    sages,
    evidence: [
      { id: "departure-confucius-1", sageId: "confucius", original: "三军可夺帅也，匹夫不可夺志也。", source: "《论语·子罕》", interpretation: "稳定不应以长期放弃核心志向为代价，但志向也需要转化为可行路径。", boundary: "保守现职不等于怯懦，在资源不足时先做准备同样是守志。", verified: true },
      { id: "departure-mencius-1", sageId: "mencius", original: "穷则独善其身，达则兼善天下。", source: "《孟子·尽心上》", interpretation: "职业阶段不同，行动目标也不同；可以先积累能力和选择权，再追求更大影响。", boundary: "这不是对无限期忍耐的赞美，也不应成为拖延改变的借口。", verified: true },
      { id: "departure-laozi-1", sageId: "laozi", original: "去甚，去奢，去泰。", source: "《道德经·第二十九章》", interpretation: "先剔除对理想工作的极端想象，分清当前工作是核心价值冲突，还是可调整的阶段性不适。", boundary: "减少执念不是压低正当需求，也不是否定改变的必要性。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "先明其志，再定去留", content: "把你不愿牺牲的价值写清，再检查当前工作是否仍能服务这个志向。", evidenceIds: ["departure-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "先积累选择权，不必用一次跳跃证明勇气", content: "判断你此刻更缺收入安全、可转移能力，还是成长空间，然后安排有时限的准备期。", evidenceIds: ["departure-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "删去极端想象，看见真正冲突", content: "不要在“永远忍耐”和“立刻裸辞”之间二选一，先做可逆的小实验。", evidenceIds: ["departure-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都不主张无限期牺牲志向，孟子更强调先积累现实选择权。" },
      { fromSageId: "laozi", toSageId: "confucius", type: "reframe", summary: "老子将去留的价值判断改写为一组可逆的现实实验。" },
    ],
    report: {
      conflict: "你在收入和可预期性中获得安全，但长期失去兴趣、成长或价值认同。",
      consensus: ["不用冲动离开证明勇气。", "不为模糊的稳定无限期牺牲志向。"],
      divergences: ["先改造当前工作，还是尽快为离开做系统准备。"],
      actions: {
        self: ["写下你对下一份工作不可妥协的三项要求。"],
        relationship: ["与上级讨论一个可在六周内验证的职责或项目调整。"],
        change: ["计算可承受的空窗期，并每周完成一个外部机会的小步验证。"],
      },
      reservation: "悟典无法知道你的负债、家庭责任、健康状况和行业机会，这些现实条件必须进入最终判断。",
    },
  },
  {
    id: "credit",
    label: "功劳归属",
    question: "同事抢了我的功劳，我该争还是忍？",
    conflicts: ["事实正名", "关系成本", "长期规则"],
    sages,
    evidence: [
      { id: "credit-confucius-1", sageId: "confucius", original: "名不正，则言不顺。", source: "《论语·子路》", interpretation: "成果、责任和作者关系不清，后续协作和评价就会继续失真。", boundary: "正名应依据事实和记录，不是在公开场合进行人身攻击。", verified: true },
      { id: "credit-mencius-1", sageId: "mencius", original: "自反而缩，虽千万人，吾往矣。", source: "《孟子·公孙丑上》", interpretation: "先核对自己的贡献是否站得住，如果证据充分，就不必因为对方强势而放弃说明。", boundary: "勇于发声不等于不计后果；方式、场合和证据同样重要。", verified: true },
      { id: "credit-laozi-1", sageId: "laozi", original: "夫唯不争，故天下莫能与之争。", source: "《道德经·第二十二章》", interpretation: "不与人陷入情绪争胜，而是用交付记录和流程让事实自己发声。", boundary: "不争不是沉默接受功劳被占，也不是退出正当权益的协商。", verified: true },
    ],
    speeches: [
      { sageId: "confucius", position: "先正名，再论关系", content: "用邮件、文档和交付记录还原事实，让贡献归属可被共同确认。", evidenceIds: ["credit-confucius-1"], status: "complete" },
      { sageId: "mencius", position: "有证则言，不以强弱代替是非", content: "先确认自己的贡献边界，再在可控的场合坚定陈述事实和诉求。", evidenceIds: ["credit-mencius-1"], status: "complete" },
      { sageId: "laozi", position: "不争意气，争取规则", content: "不要把胜负绑在一次当面冲突上，改用透明的协作和署名机制防止重演。", evidenceIds: ["credit-laozi-1"], status: "complete" },
    ],
    clashes: [
      { fromSageId: "mencius", toSageId: "confucius", type: "support", summary: "都主张基于事实正名，孟子更强调在强势关系中也不放弃发声。" },
      { fromSageId: "laozi", toSageId: "mencius", type: "reframe", summary: "老子把当面争胜改写为让记录和规则持续起作用。" },
    ],
    report: {
      conflict: "你既需要恢复事实和回报的对应关系，又担心直接发声损害合作关系。",
      consensus: ["不用情绪冲突代替事实澄清。", "通过记录和规则减少下次归属不清。"],
      divergences: ["应当尽快直接发声，还是先建立不需要正面冲突的证据与流程。"],
      actions: {
        self: ["列出你独立完成、共同完成和对方完成的事实清单。"],
        relationship: ["先与同事做一次私下对齐；仍无法澄清时，带记录向负责人说明。"],
        change: ["为后续项目建立任务负责人、交付记录和对外汇报署名规则。"],
      },
      reservation: "悟典无法判断你手中证据的完整度、组织的权力结构和发声风险，需要你选择合适的对象、场合和节奏。",
    },
  },
];

export function getCuratedCourtCase(id: string): CuratedCourtCase | null {
  return CURATED_COURT_CASES.find((item) => item.id === id) ?? null;
}

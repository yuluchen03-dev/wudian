export const TRUST_STEPS = ["问题拆解", "知识库检索", "引用校验", "多思想编排", "用户调权", "行动判牒"];
export const PILOT_METRICS = ["会审完成率", "主题分布", "引用展开率", "再次开案率"];

function deepFreeze(value) {
  Object.values(value).forEach((child) => {
    if (child && typeof child === "object" && !Object.isFrozen(child)) deepFreeze(child);
  });
  return Object.freeze(value);
}

const sages = ["confucius", "mencius", "laozi"];
export const SAGE_META = {
  confucius: { name: "孔子", color: "#b54836", portrait: "assets/confucius.png" },
  mencius: { name: "孟子", color: "#c5a55f", portrait: "assets/mencius.png" },
  laozi: { name: "老子", color: "#4e9488", portrait: "assets/laozi.png" },
};

export const CASES = deepFreeze([
  {
    id: "recognition", label: "职场认可", question: "我很努力，却总不被领导认可，怎么办？",
    conflicts: ["外界认可", "自我价值", "行动选择"], sages,
    evidence: [
      { sageId: "confucius", original: "人不知而不愠，不亦君子乎？", source: "《论语·学而》", interpretation: "先把自我价值与他人一时的认可拆开，再决定如何沟通。", boundary: "这不等于默忍不公平评价或放弃合理回报。" },
      { sageId: "mencius", original: "行有不得者，皆反求诸己。", source: "《孟子·离娄上》", interpretation: "检查成果表达、期望对齐和能力缺口，但不把所有责任归给自己。", boundary: "反求诸己是获得行动权，不是为不公开脱。" },
      { sageId: "laozi", original: "知人者智，自知者明。", source: "《道德经·第三十三章》", interpretation: "分清你真正需要的是公平回报、成长机会，还是单纯被看见。", boundary: "自知不意味着退出竞争或放弃发声。" },
    ],
    speeches: [
      { sageId: "confucius", position: "稳住内在尺度，再正名沟通", content: "先把成果、责任和评价标准说清，不让一次忽视定义全部价值。" },
      { sageId: "mencius", position: "反求诸己，但不放弃尊严", content: "查看自己能改变的部分，同时为合理评价与边界发声。" },
      { sageId: "laozi", position: "辨认执念，保留转身空间", content: "若环境长期无法给出公平回报，改变路径同样是行动。" },
    ],
    relations: [{ from: "mencius", to: "confucius", type: "support", summary: "都主张恢复行动权，孟子更强调尊严与应得回报。" }, { from: "laozi", to: "confucius", type: "reframe", summary: "老子追问是否仍值得留在当前评价体系。" }],
    verdict: { conflict: "你的努力与组织评价机制脱节，同时部分自我价值被交给了外部认可。", consensus: ["先把情绪与事实拆开", "用可验证的成果和明确对话恢复行动权"], divergence: "继续修身沟通，还是改变所在的评价体系。", actions: { self: "写下三项不依赖他人表态也能确认的成果。", relationship: "预约一次 20 分钟对话，请领导明确评价标准和差距。", change: "设定一个月观察期；若标准仍模糊，准备内部转岗或外部机会。" }, reservation: "悟典无法代替你判断当前组织是否值得继续投入。" },
  },
  {
    id: "departure", label: "职业去留", question: "稳定但不喜欢的工作，要不要离开？",
    conflicts: ["现实安全", "个人志向", "改变时机"], sages,
    evidence: [
      { sageId: "confucius", original: "三军可夺帅也，匹夫不可夺志也。", source: "《论语·子罕》", interpretation: "稳定不应以长期放弃核心志向为代价。", boundary: "暂时留任并不等于放弃志向。" },
      { sageId: "mencius", original: "穷则独善其身，达则兼善天下。", source: "《孟子·尽心上》", interpretation: "不同阶段可以先积累能力与选择权。", boundary: "不能把准备期变成无限期拖延。" },
      { sageId: "laozi", original: "去甚，去奢，去泰。", source: "《道德经·第二十九章》", interpretation: "先剔除对理想工作的极端想象。", boundary: "减少执念不等于压低正当需求。" },
    ],
    speeches: [{ sageId: "confucius", position: "先明其志，再定去留", content: "写清不愿牺牲的价值，再看当前工作是否仍服务于它。" }, { sageId: "mencius", position: "先积累选择权", content: "判断此刻更缺收入安全、可转移能力还是成长空间。" }, { sageId: "laozi", position: "删去极端想象", content: "不要在永远忍耐和立刻裸辞之间二选一。" }],
    relations: [{ from: "mencius", to: "confucius", type: "support", summary: "都不主张无限牺牲志向，孟子更强调现实选择权。" }, { from: "laozi", to: "confucius", type: "refute", summary: "老子反对把去留理解成一次不可逆的勇气证明。" }],
    verdict: { conflict: "你从稳定中获得安全，却长期失去兴趣、成长或价值认同。", consensus: ["不靠裸辞证明勇气", "为改变设置明确期限"], divergence: "先改造当前工作，还是尽快准备离开。", actions: { self: "写下下一份工作不可妥协的三项要求。", relationship: "与上级讨论一个六周内可验证的职责调整。", change: "计算可承受空窗期，每周验证一个外部机会。" }, reservation: "负债、家庭责任和行业机会必须进入最终判断。" },
  },
  {
    id: "credit", label: "功劳归属", question: "同事抢了我的功劳，我该争还是忍？",
    conflicts: ["事实正名", "关系成本", "长期规则"], sages,
    evidence: [
      { sageId: "confucius", original: "名不正，则言不顺。", source: "《论语·子路》", interpretation: "成果与责任关系不清，后续评价会继续失真。", boundary: "正名要基于事实，不进行人身攻击。" },
      { sageId: "mencius", original: "自反而缩，虽千万人，吾往矣。", source: "《孟子·公孙丑上》", interpretation: "证据充分时，不必因对方强势放弃说明。", boundary: "勇于发声也要考虑方式与场合。" },
      { sageId: "laozi", original: "夫唯不争，故天下莫能与之争。", source: "《道德经·第二十二章》", interpretation: "不争情绪胜负，用记录和流程让事实发声。", boundary: "不争不等于沉默接受权益受损。" },
    ],
    speeches: [{ sageId: "confucius", position: "先正名，再论关系", content: "用邮件、文档和交付记录还原事实。" }, { sageId: "mencius", position: "有证则言", content: "确认贡献边界后，坚定陈述事实和诉求。" }, { sageId: "laozi", position: "不争意气，争取规则", content: "用透明协作和署名机制防止重演。" }],
    relations: [{ from: "mencius", to: "confucius", type: "support", summary: "都主张基于事实正名，孟子更强调不因强势关系而沉默。" }, { from: "laozi", to: "mencius", type: "reframe", summary: "老子把一次冲突改写为长期规则建设。" }],
    verdict: { conflict: "你需要恢复事实与回报的对应关系，又担心发声损害合作关系。", consensus: ["不用情绪冲突代替事实澄清", "通过记录和规则防止重演"], divergence: "直接发声，还是先让记录与流程发挥作用。", actions: { self: "列出独立完成、共同完成和对方完成的事实清单。", relationship: "先私下对齐，仍无法澄清时带记录向负责人说明。", change: "建立任务负责人、交付记录和汇报署名规则。" }, reservation: "你需要结合证据完整度与组织权力结构选择场合。" },
  },
]);

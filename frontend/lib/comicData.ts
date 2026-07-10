/**
 * 悟典 - 漫画解读数据（Mock）
 */
import type { Comic } from "./types";

const classicLianhuanhuaStyle =
  "原创中国经典连环画风格，细腻墨线，淡彩上色，宣纸轻微纹理，克制传统色，清晰轮廓；逐格生成无字画面，中文对白和旁白由前端排版。";

export const mockComics: Comic[] = [
  {
    id: "xue-er-shi-xi",
    title: "雨停以后",
    source_verse: "学而时习之，不亦说乎？——《论语·学而》",
    logline: "一个孩子以为“看过一次”就等于学会，直到反复修风筝，才体会熟练之后从心里生出的快乐。",
    styleGuide: classicLianhuanhuaStyle,
    characters: [
      {
        name: "小明",
        role: "学习者",
        description: "急着证明自己，受挫后逐渐安静下来，最终愿意把方法传给别人。",
        visualAnchor: "十岁左右，圆脸，短发，蓝灰布衫，袖口常沾着纸屑和竹屑，手里常拿风筝线轴。",
      },
      {
        name: "夫子",
        role: "引路人",
        description: "不直接说教，只用一个动作和一句短问，把孩子带回实践。",
        visualAnchor: "年长儒者，灰白布袍，温和眼神，手持竹篾，姿态安定。",
      },
      {
        name: "小荷",
        role: "回收角色",
        description: "带着断线风筝出现，让小明把刚学会的东西转化成教别人的能力。",
        visualAnchor: "扎双髻的小孩，浅杏色短衫，抱着一只破损燕子风筝。",
      },
    ],
    panels: [
      {
        scene: "雨天屋檐下，青石板泛着水光，远处同伴的风筝飞得很高。",
        shot: "远景，低机位，屋檐形成压迫的横线",
        action: "小明抱着骨架歪斜的纸风筝，手里的线轴松散垂落。",
        dialogue: "我明明看过你做一次，为什么还是飞不起来？",
        caption: "学到方法，不等于已经拥有能力。",
        character: "小明",
        emotion: "羡慕又沮丧",
        knowledgeAnchor: "“学”是获得方法；还没有经过实践校正。",
        visualMetaphor: "飞得很高的风筝与垂落的线形成落差。",
        beat: "受阻",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p01.png",
        imagePrompt:
          "生成六格漫画第1格，无文字。雨天屋檐下，一个十岁男孩抱着坏掉的纸风筝，远处同伴风筝高飞。远景低机位，青石板水光，原创中国经典连环画风格，细腻墨线，淡彩宣纸质感。",
      },
      {
        scene: "屋檐边，雨声渐小，夫子把一根竹篾递给小明，另一只手指向风吹来的方向。",
        shot: "中近景，人物一左一右，竹篾横穿画面成为视觉引导线",
        action: "小明抬头接过竹篾，夫子没有讲大道理，只示意他看风。",
        dialogue: "看过，是学。再来，是习。",
        caption: "“习”不是重复背诵，而是重新进入动作。",
        character: "夫子",
        emotion: "平静引导",
        knowledgeAnchor: "“习”包含练习、实践、校正。",
        visualMetaphor: "竹篾像一支指向实践的笔。",
        beat: "点题",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p02.png",
        imagePrompt:
          "生成六格漫画第2格，无文字。同一男孩和年长儒者，屋檐边雨声渐小，夫子把竹篾递给孩子并指向风向。中近景，竹篾横向引导构图，原创中国经典连环画风格，细腻墨线，淡彩宣纸质感。",
      },
      {
        scene: "院子里，小明反复调整风筝：绑太紧、纸撕裂、线缠住手指。",
        shot: "三连小格拼贴感，节奏密集",
        action: "同一动作被拆成三次失败，树叶每次朝不同方向倾斜。",
        dialogue: "",
        caption: "第一次。第五次。第十二次。",
        character: "小明",
        emotion: "从烦躁到专注",
        knowledgeAnchor: "“时”不是机械重复，而是在变化的时机中练。",
        visualMetaphor: "不同方向的树叶显示风在变化。",
        beat: "练习蒙太奇",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p03.png",
        imagePrompt:
          "生成六格漫画第3格，无文字。院子里，男孩反复修风筝的蒙太奇：绑太紧、纸撕裂、线缠手指，树叶风向不同。三连小格拼贴感，密集节奏，原创中国经典连环画风格。",
      },
      {
        scene: "雨停前的安静一刻，孩子闭眼站在院中，指尖感受线的轻震。",
        shot: "特写，手指、风筝线和孩子半闭的眼睛形成三角构图",
        action: "风筝不完美，但骨架终于平衡；小明的肩膀放松下来。",
        dialogue: "它不是听我的，它是在告诉我。",
        caption: "学习从控制转为感知规律。",
        character: "小明",
        emotion: "突然安静",
        knowledgeAnchor: "实践让知识变成可感知的判断。",
        visualMetaphor: "轻颤的线像知识终于有了回声。",
        beat: "顿悟",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p04.png",
        imagePrompt:
          "生成六格漫画第4格，无文字。雨停前，孩子闭眼感受风筝线轻轻震动，修好的风筝虽不完美但已平衡。手指和线的特写，安静顿悟，原创中国经典连环画风格。",
      },
      {
        scene: "雨停，云缝透光，风筝升起越过屋檐，夫子站在远处微笑。",
        shot: "大横格，仰拍，风筝牵引视线向上",
        action: "小明先愣住，然后笑了，没有夸张欢呼。",
        dialogue: "原来“时习之”的快乐，是这样的啊。",
        caption: "学而时习之，不亦说乎？",
        character: "小明",
        emotion: "由内而外的喜悦",
        knowledgeAnchor: "“说/悦”：熟练后的内在快乐。",
        visualMetaphor: "雨后光线照亮风筝，也照亮孩子的脸。",
        beat: "回响",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p05.png",
        imagePrompt:
          "生成六格漫画第5格，无文字。雨停后云缝透光，风筝升起越过屋檐，男孩仰头微笑，年长儒者远处微笑。大横格仰拍，风筝牵引视线，原创中国经典连环画风格。",
      },
      {
        scene: "院门口，小荷抱着断线风筝跑来，雨水从檐角滴落。",
        shot: "近景回收，动作呼应第2格",
        action: "小明把竹篾递给小荷，另一只手指向风来的方向。",
        dialogue: "先看风。然后，我们再来。",
        caption: "学会之后，才真正能把方法交给别人。",
        character: "小明",
        emotion: "自信而温柔",
        knowledgeAnchor: "学习完成于复用与传递。",
        visualMetaphor: "竹篾从夫子手中传到孩子手中。",
        beat: "传递",
        imageUrl: "/content/comic-panels/xue-er-shi-xi-p06.png",
        imagePrompt:
          "生成六格漫画第6格，无文字。院门口，另一个小孩抱着断线风筝跑来，男孩把竹篾递过去并指向风向，动作呼应前文。近景，温暖传递感，原创中国经典连环画风格。",
      },
    ],
  },
  {
    id: "san-ren-xing",
    title: "三人同行",
    source_verse: "三人行，必有我师焉。——《论语·述而》",
    logline: "一个总盯着自己短处的孩子，学会从同伴身上看见可学之处，也看见自己能教别人的地方。",
    styleGuide: classicLianhuanhuaStyle,
    characters: [
      {
        name: "阿宝",
        role: "观察者",
        description: "起初自卑，后来学会用欣赏的眼光看同伴。",
        visualAnchor: "少年，浅褐短衫，背小书袋，常低头攥衣角。",
      },
      {
        name: "夫子",
        role: "引路人",
        description: "用一句提醒让孩子改变观察方式。",
        visualAnchor: "年长儒者，灰白布袍，温和眼神，手持书卷。",
      },
    ],
    panels: [
      {
        scene: "学堂里，三个孩子结伴学习，各有所长。",
        shot: "中景，三角构图",
        action: "阿宝看着同伴算数和写字，自己把作业藏到身后。",
        dialogue: "他算术好，她字写得好，我好像什么都不行。",
        caption: "只看差距，容易忘记学习的入口。",
        character: "阿宝",
        emotion: "自我怀疑",
        knowledgeAnchor: "从他人长处中寻找可学之处。",
        visualMetaphor: "三张桌子像三条不同路径。",
        beat: "受阻",
      },
      {
        scene: "夫子路过学堂窗边，听见阿宝低声叹气。",
        shot: "窗框式构图",
        action: "夫子停下脚步，把窗外光线引进画面。",
        dialogue: "三人同行，其中就有可学之处。",
        caption: "三人行，必有我师焉。",
        character: "夫子",
        emotion: "循循善诱",
        knowledgeAnchor: "“师”不只是正式老师，也可以是值得效法的人。",
        visualMetaphor: "窗光落在三个孩子身上。",
        beat: "点题",
      },
      {
        scene: "阿宝开始观察同伴的动作。",
        shot: "连续特写",
        action: "他看见同伴演算前先画线，看见另一个同伴写字前先稳住手腕。",
        dialogue: "原来他们厉害，不是因为神奇，是因为有方法。",
        caption: "择其善者而从之。",
        character: "阿宝",
        emotion: "豁然开朗",
        knowledgeAnchor: "学习他人的具体方法，而不是只羡慕结果。",
        visualMetaphor: "线条和笔画变成可追随的路径。",
        beat: "发现",
      },
      {
        scene: "几日后，三人围坐，阿宝把自己整理书袋的方法教给同伴。",
        shot: "俯拍圆形构图",
        action: "每个人都把自己的长处摆在桌上，互相交换。",
        dialogue: "今天你教我算术，我教你整理。我们都能当一次老师。",
        caption: "看见别人的善，也别忘了自己能贡献的善。",
        character: "阿宝",
        emotion: "自信满满",
        knowledgeAnchor: "互为师友，才是经典落到关系中的样子。",
        visualMetaphor: "三只手在桌面中心汇合。",
        beat: "回收",
      },
    ],
  },
];

/** 影像底本外链平台 */
export const mockImageSources = [
  {
    id: "shidianguji",
    name: "识典古籍",
    url: "https://www.shidianguji.com",
    description:
      "北京大学主持建设的古籍数字化平台，收录大量四书五经权威影像底本，支持高清浏览与检索。",
  },
  {
    id: "zhonghua-guji",
    name: "中华经典古籍库",
    url: "https://gujiku.cnki.net",
    description:
      "中华书局出品，收录点校本二十四史及十三经注疏等权威版本，影像与文本对照。",
  },
  {
    id: "guji-shumu",
    name: "古籍数字资源库",
    url: "https://www.nlc.cn",
    description:
      "中国国家图书馆提供的古籍数字化影像资源，可按书名、作者检索历代善本。",
  },
];

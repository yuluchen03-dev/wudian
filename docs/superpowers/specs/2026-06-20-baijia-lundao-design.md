# 百家论道 — 圆桌论道界面设计文档

> 悟典 · 四书五经互动学习平台  
> 设计日期：2026-06-20  
> 设计者：frontend-developer

---

## 1. 功能概述

"百家论道"是"悟典"平台的圆桌论道模块，让用户同时向多位圣贤（孔子、孟子、王阳明）提问同一话题，观看圣贤们各抒己见、交锋辩论的精彩场景。区别于现有"问道圣贤"的一对一对话，百家论道呈现多视角、多维度的经典智慧碰撞。

### 核心体验

- 用户提出一个话题（如"何为真正的勇气"）
- 三位圣贤依次发言，从各自思想体系出发回应
- 展示圣贤间的观点异同、交锋连线
- 引用原文溯源，可定位到阅读器

---

## 2. 现有设计系统分析

### 2.1 中国风配色体系（来自 `tailwind.config.ts`）

| 色系 | 用途 | 色值示例 |
|------|------|----------|
| 墨色系 `ink-*` | 主调文字、边框 | `#1c1917`(800), `#57534e`(500) |
| 朱砂系 `cinnabar-*` | 点缀、CTA、强调 | `#b91c1c`(600), `#dc2626`(500) |
| 米黄/宣纸系 `rice-*` | 背景 | `#faf6ed`(100), `#fdfbf7`(50) |
| 竹青系 `bamboo-*` | 辅助、链接、引用 | `#5b8c5a`(500), `#7ba87b`(300) |
| 青铜系 `bronze-*` | 标签、辅助文字 | `#8a8050`(500) |

### 2.2 字体

- 正文/标题：`font-serif`（宋体系列，如 Noto Serif SC）
- 引用/文言：`font-kai`（楷体系列，如 Kaiti SC）
- 间距：`tracking-widest` 用于大标题，`tracking-wider` 用于副标题

### 2.3 现有圣贤对话组件（`SageChat.tsx`）

- 圣贤头像：方形圆角 `rounded-md`，`avatar_color` 背景 + 姓名首字
- 消息气泡：用户消息（朱砂色背景），圣贤消息（白色/米黄背景）
- 引用系统：`CitationSidebar` 可折叠面板，竹简风格
- 检索动画：`SearchVisualization` 篇章名 stagger 动画
- 结构化渲染：`<<<TAG>>>` 格式解析（QUOTE/SOURCE/CLASSICAL/VERNACULAR）

### 2.4 装饰组件（`ChineseDecor.tsx`）

- `InkDivider` 水墨分隔线
- `SealStamp` 印章风格标签
- `QuoteBlock` 原文引用块（朱砂竖线 + 楷体）
- `SectionTitle` 章节标题（朱砂圆点装饰）
- `CTAButton` 朱砂色按钮

---

## 3. 圆桌论道主界面布局

### 3.1 页面结构

```
┌─────────────────────────────────────────────┐
│  顶部：页面标题 + 免责声明                    │
├─────────────────────────────────────────────┤
│  话题输入区：选择话题 / 自定义提问             │
├─────────────────────────────────────────────┤
│  圆桌区域（核心）：                           │
│  ┌───────────────────────────────────────┐  │
│  │        ┌─────────┐                    │  │
│  │   孔子 │  话题    │ 孟子               │  │
│  │   ○────│  中心    │────○               │  │
│  │        │  卡片    │                    │  │
│  │        └────┬────┘                    │  │
│  │             │                         │  │
│  │        王阳明 ○                        │  │
│  └───────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│  论道时间线：圣贤轮流发言的垂直时间线          │
│  ┌───────────────────────────────────────┐  │
│  │ ○ 孔子发言 [引用卡片]                   │  │
│  │   ↕ 交锋连线                            │  │
│  │ ○ 孟子发言 [引用卡片]                   │  │
│  │   ↕ 交锋连线                            │  │
│  │ ○ 王阳明发言 [引用卡片]                  │  │
│  └───────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│  底部：输入新话题 / 查看引用详情              │
└─────────────────────────────────────────────┘
```

### 3.2 响应式断点

- 移动端（< 768px）：圣贤头像垂直排列，发言区域全宽
- 桌面端（≥ 768px）：圣贤头像半圆排列，发言区域左右分栏

---

## 4. 核心组件设计

### 4.1 `RoundTableHeader` — 页面头部

```tsx
// 页面标题区：印章风格 + 古典分隔线
<div className="text-center">
  <SealStamp variant="cinnabar" size="md">百家论道</SealStamp>
  <h1 className="font-serif text-4xl font-bold tracking-widest text-ink-800">
    圆桌论道
  </h1>
  <p className="mt-3 text-sm text-ink-500">
    三位圣贤，同一话题，各抒己见 —— 观千年智慧交锋
  </p>
  <InkDivider className="mt-5" />
</div>
```

### 4.2 `TopicSelector` — 话题选择器

预设话题卡片 + 自定义输入框：

**预设话题列表：**
1. "何为真正的勇气？"
2. "面对不公，该沉默还是发声？"
3. "知易行难，如何做到知行合一？"
4. "人性本善还是本恶？"
5. "君子应该如何对待金钱？"
6. "如何在困境中保持内心平静？"

**交互：**
- 点击预设话题 → 自动开始论道
- 自定义输入 → 输入框 + 开始按钮
- 话题卡片使用 `paper-texture-card` 背景 + 竹青色边框

### 4.3 `SageAvatars` — 圣贤头像圆桌排列

```tsx
// 三位圣贤围绕话题卡片的半圆/三角形布局
// 桌面端：半圆形排列在话题卡上方
// 移动端：水平排列

// 头像设计：复用现有 sage-chat 的风格
<div className="flex h-20 w-20 items-center justify-center rounded-full 
                font-serif text-3xl font-bold text-rice-50 shadow-lg"
     style={{ backgroundColor: sage.avatar_color }}>
  {sage.name[0]}
</div>

// 头像下方：姓名 + 核心思想标签
<div className="text-center">
  <span className="font-serif text-lg font-bold">{sage.name}</span>
  <span className="text-xs text-bronze-500">{sage.era}</span>
</div>
```

**圣贤配色方案：**
- 孔子：`#b91c1c`（朱砂红）
- 孟子：`#8a8050`（青铜色）
- 王阳明：`#44403c`（墨色）

### 4.4 `DebateTimeline` — 论道时间线（核心组件）

圣贤轮流发言的垂直时间线，每个发言包含：

```
┌────────────────────────────────────────────┐
│  ○ 孔子（朱砂圆点）                          │
│  │  ┌──────────────────────────────────┐   │
│  │  │ 原文引用块（QuoteBlock 风格）      │   │
│  │  │ 朱砂竖线 + 楷体 + 宣纸纹理        │   │
│  │  └──────────────────────────────────┘   │
│  │  文言回应（楷体，letter-spacing: 0.03em）│
│  │  白话点睛（米黄卡片）                     │
│  │                                         │
│  │  ┌─ 交锋指示 ──────────────────────┐   │
│  │  │  ↕ 与孟子观点相左                │   │
│  │  │  ○ 认同王阳明"知行合一"          │   │
│  │  └────────────────────────────────┘   │
│  │                                         │
├─ ○ 孟子（青铜圆点）                         │
│  │  ...                                    │
├─ ○ 王阳明（墨色圆点）                       │
│  │  ...                                    │
└────────────────────────────────────────────┘
```

**交锋可视化：**
- 使用 CSS `border-left` 彩色竖线连接相邻发言
- 交锋指示器：当后一位圣贤引用/反驳前一位时，显示连接标签
- 标签样式：竹青色背景圆角标签，文字如"与孔子观点相左"、"认同孟子仁政"

### 4.5 `CitationPanel` — 引用展示系统

复用现有 `CitationSidebar` 的设计语言，但适配多圣贤场景：

```
┌─────────────────────────────────────────┐
│  📜 本次论道共引用 8 段原文               │
│  ┌─────────────────────────────────┐    │
│  │ ① 孔子所引：人不知而不愠...       │    │
│  │   《论语·学而》 相关度 95%         │    │
│  ├─────────────────────────────────┤    │
│  │ ② 孟子所引：富贵不能淫...         │    │
│  │   《孟子·滕文公下》 相关度 93%     │    │
│  ├─────────────────────────────────┤    │
│  │ ③ 王阳明所引：知者行之始...       │    │
│  │   《传习录》 相关度 91%            │    │
│  └─────────────────────────────────┘    │
│  原文经 RAG 检索匹配，相关度由高到低      │
└─────────────────────────────────────────┘
```

---

## 5. 状态管理与数据流

### 5.1 页面状态

```typescript
interface RoundTableState {
  // 话题
  topic: string;
  presetTopics: string[];
  
  // 圣贤配置
  sages: Sage[];  // 从 mockSages 获取
  
  // 论道流程
  phase: "select" | "debating" | "complete";
  currentSageIndex: number;  // 当前发言的圣贤
  
  // 每位圣贤的发言
  speeches: SageRoundSpeech[];
  
  // 引用汇总
  allCitations: Citation[];
  
  // 交锋关系
  clashes: DebateClash[];
}

interface SageRoundSpeech {
  sageId: string;
  content: string;  // 完整回复文本
  parsed: SageReplyParts;  // 结构化解析
  citations: Citation[];
  isStreaming: boolean;
  isComplete: boolean;
}

interface DebateClash {
  fromSageId: string;
  toSageId: string;
  type: "agree" | "disagree" | "extend" | "reframe";
  summary: string;  // 如"与孔子观点相左"
}
```

### 5.2 论道流程

1. 用户选择/输入话题 → `phase: "debating"`
2. 系统依次向三位圣贤提问（使用现有 `api.chatWithSageStream`）
3. 每位圣贤回复完成后，AI 分析交锋关系
4. 全部完成后 → `phase: "complete"`，展示完整论道时间线

### 5.3 交锋分析

后端需要新增一个接口（或在前端用已有回复文本做简单分析）：

```typescript
// 简单的交锋分析（前端可先用关键词匹配实现）
function analyzeClashes(speeches: SageRoundSpeech[]): DebateClash[] {
  // 检查后一位圣贤的回复中是否提到了前一位圣贤的观点
  // 关键词：如"此言差矣"、"吾以为不然"、"深以为然"、"亦如是"等
}
```

---

## 6. 移动端适配方案

### 6.1 布局调整

| 组件 | 桌面端 | 移动端 |
|------|--------|--------|
| 圣贤头像 | 半圆形/三角形排列 | 水平排列，间距缩小 |
| 话题卡片 | 居中，较大尺寸 | 全宽，紧凑尺寸 |
| 论道时间线 | 左侧竖线 + 右侧内容 | 左侧竖线 + 右侧内容（保持） |
| 引用面板 | 可折叠侧栏 | 底部抽屉式弹出 |
| 交锋连线 | SVG 箭头连线 | 简化为文字标签 |

### 6.2 触摸优化

- 发言卡片点击展开/折叠详情
- 引用面板使用 swipe 手势展开
- 头像点击跳转到该圣贤的发言

---

## 7. 动画设计

### 7.1 页面进入动画

```tsx
// 标题淡入
<motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
  
// 圣贤头像 stagger 进入
<motion.div variants={sageVariants} initial="hidden" animate="show">
  {sages.map((sage, i) => (
    <motion.div variants={{
      hidden: { opacity: 0, scale: 0.8 },
      show: { opacity: 1, scale: 1, transition: { delay: i * 0.15 } }
    }}>
```

### 7.2 论道流程动画

```tsx
// 当前发言圣贤头像发光/呼吸动画
<div className="animate-pulse shadow-lg" />

// 发言内容打字机效果（复用 SageChat 的流式输出）
// 新发言从下方 slide-up 进入
<motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

// 交锋连线使用 SVG path 动画描边
<motion.path initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} />
```

### 7.3 完成动画

```tsx
// 全部发言完成后，交锋关系卡片淡入
// "论道总结"卡片从底部升起
<motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
```

---

## 8. 技术实现要点

### 8.1 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/app/roundtable/page.tsx` | 圆桌论道页面 |
| `frontend/components/roundtable/RoundTableHeader.tsx` | 页面头部 |
| `frontend/components/roundtable/TopicSelector.tsx` | 话题选择器 |
| `frontend/components/roundtable/SageAvatars.tsx` | 圣贤头像排列 |
| `frontend/components/roundtable/DebateTimeline.tsx` | 论道时间线 |
| `frontend/components/roundtable/SageSpeechCard.tsx` | 单个圣贤发言卡片 |
| `frontend/components/roundtable/ClashIndicator.tsx` | 交锋指示器 |
| `frontend/components/roundtable/CitationPanel.tsx` | 引用汇总面板 |
| `frontend/lib/roundtableData.ts` | 预设话题、Mock 数据 |

### 8.2 API 依赖

- 复用 `api.chatWithSageStream` — 向每位圣贤提问
- 复用 `api.retrieve` — RAG 检索引用
- 可选：新增 `/api/ai/roundtable` 接口，一次性返回三位圣贤回复 + 交锋分析

### 8.3 导航集成

在 `Navbar.tsx` 的 `navItems` 中添加：

```typescript
{ href: "/roundtable", label: "论道", icon: Users }
```

---

## 9. 设计决策与理由

| 决策 | 理由 |
|------|------|
| 垂直时间线布局（非左右分栏） | 移动端优先，避免小屏分栏过窄；桌面端可读性也更好 |
| 复用现有 `SageChat` 的流式输出逻辑 | 保持一致性，减少重复代码 |
| 交锋分析先用前端关键词匹配 | 降低后端复杂度，后续可升级为 AI 分析 |
| 引用面板使用可折叠设计 | 避免信息过载，用户可按需查看 |
| 圣贤头像保持方形圆角风格 | 与现有 sage-chat 保持视觉一致 |

---

## 10. 后续可扩展

1. **增加圣贤**：添加荀子（性恶论）、朱熹（理学）等，丰富交锋维度
2. **用户投票**：让用户投票哪位圣贤说得更有道理
3. **论道历史**：保存论道记录，可回看
4. **AI 裁判**：AI 对论道进行总结评判
5. **论道排行榜**：热门话题排行

---

## 附录：参考资源

- 现有圣贤对话组件：`frontend/components/sage/SageChat.tsx`
- 引用侧栏组件：`frontend/components/sage/CitationSidebar.tsx`
- 中式装饰组件：`frontend/components/ui/ChineseDecor.tsx`
- 圣贤数据：`frontend/lib/sageData.ts`
- 知识图谱中的圣贤列表：`frontend/lib/explorationMockData.ts`
- 后端圣贤角色设定：`backend/app/services/sage_persona.py`
- 后端 AI 对话 API：`backend/app/api/ai.py`

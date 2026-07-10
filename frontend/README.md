# 悟典 · 前端

四书五经互动学习平台的前端，基于 Next.js 14 (App Router) + Tailwind CSS + Framer Motion。

## 技术栈

- **Next.js 14** (App Router) - React 全栈框架
- **Tailwind CSS** - 原子化 CSS，中国风自定义配色
- **Framer Motion** - 流畅动画
- **SWR** - 数据请求与缓存
- **Axios** - HTTP 客户端
- **lucide-react** - 图标库
- **TypeScript** - 类型安全

## 设计风格

中国风 UI：
- **墨色**（ink）- 主调，文字、边框
- **朱砂**（cinnabar）- 点缀，按钮、强调
- **米黄**（rice）- 背景，纸质质感
- **青铜**（bronze）- 辅助色
- 字体：宋体 / 楷体 / Noto Serif SC

## 目录结构

```
frontend/
├── app/
│   ├── layout.tsx          # 根布局（含 Navbar）
│   ├── page.tsx            # 首页（书库入口、每日一句、进度）
│   ├── globals.css         # 全局样式
│   ├── reader/
│   │   └── page.tsx        # 阅读器页面
│   ├── challenge/
│   │   └── page.tsx        # 闯关页（占位）
│   └── community/
│       └── page.tsx        # 社区页（占位）
├── components/
│   ├── Navbar.tsx          # 顶部导航栏
│   └── reader/
│       ├── ReadingView.tsx       # 文白对照阅读器（核心）
│       ├── AnnotationPopup.tsx   # 生僻字注释弹窗
│       ├── EntityCard.tsx        # 实体百科卡片
│       └── ChapterSelector.tsx   # 章节选择器
├── lib/
│   ├── api.ts              # API 客户端封装（支持 Mock）
│   ├── types.ts            # TypeScript 类型定义
│   └── mockData.ts         # Mock 数据（论语前三章）
├── public/                 # 静态资源
├── tailwind.config.ts      # Tailwind 配置（中国风配色）
├── package.json
├── tsconfig.json
├── next.config.js
└── postcss.config.js
```

## 核心组件说明

### ReadingView（文白对照阅读器）
- 左右双栏：左侧原文，右侧白话译文，逐句对应
- 原文中生僻字带下划线，点击弹出注音与释义
- 人名/地名等实体可点击，弹出百科卡片
- 支持章节切换、字体大小调节（小/中/大/特）、夜间模式
- framer-motion 实现逐句淡入动画

### AnnotationPopup（注释弹窗）
- 显示拼音、释义
- 通假字特殊提示（标注本字）
- 弹窗带缩放淡入动画

### EntityCard（实体百科卡片）
- 支持人名/地名/官职/典故/概念五种类型
- 不同类型不同图标和配色
- 显示关联原文片段

### ChapterSelector（章节选择器）
- 侧滑抽屉式目录
- 显示已读标记、当前章高亮

## 开发运行

```bash
cd frontend
npm install
npm run dev
```

默认开启 Mock 模式（`NEXT_PUBLIC_USE_MOCK=true`），无需后端即可独立运行展示。

## 对接后端

设置环境变量切换到真实 API：

```bash
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

API 接口约定见 `lib/api.ts`，主要接口：
- `GET /books` - 书籍列表
- `GET /books/:bookId/chapters` - 章节列表
- `GET /chapters/:chapterId` - 章节详情
- `GET /entities/:entityId` - 实体详情
- `GET /daily-quote` - 每日一句
- `GET /progress/:bookId` - 学习进度

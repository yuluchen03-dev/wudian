# 悟典 TRAE 大赛报名材料 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一份可直接上传 TRAE 社区的自包含 HTML 创意提案和一份可直接发布的“学习工作”赛道报名帖文案。

**Architecture:** 交付物集中放在 `报名材料/`。HTML 使用原生 HTML、CSS、Canvas 和少量原生 JavaScript，不依赖构建工具或外部资源；Node 校验脚本读取真实交付文件，验证官方内容、离线性、交互钩子和无障碍约束。

**Tech Stack:** HTML5、CSS3、Canvas 2D、原生 JavaScript、Node.js 内置模块

---

## 文件结构

- `报名材料/悟典-TRAE大赛创意提案.html`：可直接上传社区的单文件创意提案。
- `报名材料/悟典-TRAE大赛报名帖文案.md`：可直接粘贴到论坛的标题、标签和正文。
- `报名材料/validate-registration-materials.cjs`：针对两份交付物的本地自动校验。

### Task 1: 建立失败的材料合规测试

**Files:**
- Create: `报名材料/validate-registration-materials.cjs`
- Test: `报名材料/validate-registration-materials.cjs`

- [ ] **Step 1: 写入失败测试**

测试使用 `fs.readFileSync` 读取目标 HTML 和 Markdown，要求文件存在、HTML 自包含、页面包含官方必需内容和三个案例按钮、文案超过 100 个汉字且无占位符。

```js
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = __dirname;
const htmlPath = path.join(root, '悟典-TRAE大赛创意提案.html');
const copyPath = path.join(root, '悟典-TRAE大赛报名帖文案.md');

assert.ok(fs.existsSync(htmlPath), 'HTML proposal must exist');
assert.ok(fs.existsSync(copyPath), 'Forum copy must exist');
```

- [ ] **Step 2: 运行测试并确认因交付文件不存在而失败**

Run: `node 报名材料/validate-registration-materials.cjs`

Expected: FAIL，错误为 `HTML proposal must exist`。

### Task 2: 实现自包含 HTML 创意提案

**Files:**
- Create: `报名材料/悟典-TRAE大赛创意提案.html`
- Test: `报名材料/validate-registration-materials.cjs`

- [ ] **Step 1: 实现语义结构与视觉系统**

页面包含以下稳定锚点并使用 CSS 变量管理颜色：

```html
<main>
  <section id="experience" aria-labelledby="experience-title"></section>
  <section id="problem" aria-labelledby="problem-title"></section>
  <section id="users" aria-labelledby="users-title"></section>
  <section id="trust" aria-labelledby="trust-title"></section>
  <section id="value" aria-labelledby="value-title"></section>
  <section id="trae" aria-labelledby="trae-title"></section>
</main>
```

- [ ] **Step 2: 实现三个真实困惑的交互切换**

三个按钮使用 `data-case`，案例数据包含问题、经典原文、出处、白话解释和三种思想视角；点击后只更新指定文本节点并同步 `aria-pressed`。

```js
const cases = {
  recognition: { question: '我很努力，却总是不被看见，怎么办？' },
  choice: { question: '两个机会都很好，我害怕选错，怎么办？' },
  conflict: { question: '和重要的人意见不合，怎样坚持又不伤关系？' }
};
```

- [ ] **Step 3: 实现 Canvas 背景和降级**

Canvas 使用固定节点和连线表示经典知识关系；在 `prefers-reduced-motion` 下停止动画，仅绘制静态帧。Canvas 带有替代说明，页面无 Canvas 时仍保留背景色与网格。

- [ ] **Step 4: 增加响应式、打印与无障碍样式**

桌面双栏区域在 760px 以下改为单栏；所有交互目标高度至少 44px；打印时隐藏导航、Canvas、案例按钮和打印按钮；焦点样式在深浅背景上均可见。

- [ ] **Step 5: 运行校验，确认当前只因文案文件缺失而失败**

Run: `node 报名材料/validate-registration-materials.cjs`

Expected: FAIL，错误为 `Forum copy must exist`。

### Task 3: 编写报名帖文案

**Files:**
- Create: `报名材料/悟典-TRAE大赛报名帖文案.md`
- Test: `报名材料/validate-registration-materials.cjs`

- [ ] **Step 1: 写入论坛可直接发布的标题和正文**

文案使用官方结构：

```markdown
# 【学习工作】悟典——让每一句人生建议都有经典出处

标签：学习工作

## 1. 创意名称 + 创意介绍
## 2. 目标用户及痛点
## 3. 价值与意义
## 4. 随帖附件
```

正文明确产品是思想启发而非心理、医疗、法律或职业决策服务，并说明随帖上传 HTML 文件。

- [ ] **Step 2: 运行完整自动校验**

Run: `node 报名材料/validate-registration-materials.cjs`

Expected: PASS，输出所有检查项和 `Registration materials validation passed.`。

### Task 4: 浏览器与内容验收

**Files:**
- Verify: `报名材料/悟典-TRAE大赛创意提案.html`
- Verify: `报名材料/悟典-TRAE大赛报名帖文案.md`

- [ ] **Step 1: 在浏览器解析 HTML 并检查控制台**

通过临时本地静态服务器打开页面，确认 DOM、Canvas、脚本均加载，控制台无错误。

- [ ] **Step 2: 验证桌面和移动视口**

检查 1440×1000 和 390×844：首屏非空、品牌与主交互可见、无横向滚动、文字不重叠、三个案例按钮可操作。

- [ ] **Step 3: 复核官方要求和文件体积**

Run: `Get-Item 报名材料/悟典-TRAE大赛创意提案.html | Select-Object Name,Length`

Expected: 文件小于 20 MB；报名帖包含学习工作标签、四段正文和附件说明。

### Task 5: 嵌入产品图片

**Files:**
- Modify: `报名材料/validate-registration-materials.cjs`
- Modify: `报名材料/悟典-TRAE大赛创意提案.html`
- Create: `报名材料/embed-registration-images.py`
- Source assets: `frontend/public/agens/sages/portraits/{confucius,mencius,laozi}.png`
- Source assets: `frontend/public/agens/books/{lunyu,mengzi,daodejing}.png`

- [ ] **Step 1: 扩展失败测试**

```js
const embeddedImages = html.match(/<img[^>]+src=["']data:image\/webp;base64,/g) || [];
check(embeddedImages.length === 6, 'HTML embeds exactly six WebP images');
check(!/<img[^>]+alt=["']\s*["']/i.test(html), 'Every embedded image has descriptive alt text');
```

- [ ] **Step 2: 运行测试并确认图片数量失败**

Run: `node 报名材料/validate-registration-materials.cjs`

Expected: FAIL，错误为 `HTML embeds exactly six WebP images`。

- [ ] **Step 3: 加入图片结构和稳定尺寸样式**

三张肖像加入 `.perspective-header`，三张经典视觉加入 `.source-gallery`。所有图片声明 `width`、`height`、`alt` 和明确的 `object-fit`，移动端单列展示时不改变正文宽度。

- [ ] **Step 4: 压缩并内嵌图片**

`embed-registration-images.py` 使用 Pillow 将肖像缩放至 360×360、经典视觉缩放至 720×480，编码为 WebP Data URI 后替换 HTML 中对应的 `data-embed-source`。

- [ ] **Step 5: 运行完整校验与浏览器验收**

Run: `node 报名材料/validate-registration-materials.cjs`

Expected: PASS；HTML 小于 20 MB，桌面和移动端图片均可见、无横向溢出、控制台无错误。

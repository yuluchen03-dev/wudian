# Hackathon Investor Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Trae CN hackathon investor-readiness upgrades so Wudian is easier to demo, evaluate, trust, and continue discussing after the event.

**Architecture:** Keep the four-page stage route as the product spine: `/demo -> /sage-chat -> /about -> /roundtable`. Add thin, focused artifacts around that spine: a judge README, investor Q&A, scoring map, data statement, safer demo links, and root-level verification scripts. Avoid adding major product features or changing the core app architecture.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Node-based static wiring tests, FastAPI/Python backend tests, PowerShell stage scripts.

---

## File Structure

- Create `README.md`: judge/investor opening guide with one-line positioning, demo route, commands, Trae contribution, fallback wording, and a clear pilot/investor CTA.
- Create `docs/hackathon/investor-qa.md`: short answers for target user, business model, moat, safety boundary, growth, and funding ask.
- Create `docs/hackathon/scoring-map.md`: maps Trae CN hackathon judging signals to files/pages/demo moments.
- Create `docs/hackathon/data-trust-statement.md`: concise data scope, citation policy, and safety boundary.
- Modify `docs/hackathon/final-delivery-checklist.md`: include new required artifacts and business-follow-up checklist items.
- Modify `HACKATHON_OPTIMIZATIONS.md`: link the new judge guide, investor Q&A, scoring map, and data statement.
- Modify `Pitch讲稿_3分钟.md`: add investor follow-up Q&A without expanding the three-minute main route.
- Modify `frontend/app/demo/page.tsx`: make the main sage-chat link one-click with a preset `q=`, add proof/CTA labels, and keep the existing visual language.
- Modify `frontend/tests/demoHackathonWiring.test.cjs`: assert the one-click demo URL and investor-readiness signals.
- Modify `frontend/components/sage/SageChat.tsx`: when backend streaming fails, attach local citations to the fallback message so evidence does not vanish.
- Modify `frontend/lib/sageData.ts`: export reusable local demo citations.
- Modify `frontend/tests/sageChatWiring.test.cjs`: assert fallback citations are imported and assigned.
- Modify `frontend/app/roundtable/page.tsx`: add a `demo=complete` route that immediately renders mock complete state for stage fallback.
- Modify `frontend/tests/roundtablePageWiring.test.cjs`: assert the complete-demo route is wired.
- Create `.gitignore`: ignore dependency/build/runtime artifacts at the project root, including `.worktrees/`, `node_modules/`, `.next/`, logs, caches, DB/runtime data.
- Modify `package.json`: add root scripts for `backend:test`, `test`, `stage-check`, and `build:clean`.
- Modify `docs/hackathon/final-delivery-checklist.md`: document correct backend test command and port ownership rule.
- Modify `backend/README.md`: align the actual demo architecture with SQLite/Chroma/local fallback rather than overstating PostgreSQL/Redis as required.

---

### Task 1: Delivery And Investor Documents

**Files:**
- Create: `README.md`
- Create: `docs/hackathon/investor-qa.md`
- Create: `docs/hackathon/scoring-map.md`
- Create: `docs/hackathon/data-trust-statement.md`
- Modify: `docs/hackathon/final-delivery-checklist.md`
- Modify: `HACKATHON_OPTIMIZATIONS.md`
- Modify: `Pitch讲稿_3分钟.md`

- [ ] **Step 1: Write static artifact assertions**

Add a lightweight root-level Node test later in Task 4, but for this task manually ensure each new doc contains these exact strings:

```text
可追溯的中国思想问答入口
/demo -> /sage-chat -> /about -> /roundtable
每一句安慰都有出处
不是一个 AI，是一桌中国思想审你的问题
演示稳定层
思想启发，不替代心理、医疗、法律或职业决策
Trae
```

- [ ] **Step 2: Create `README.md`**

Create a judge-first guide with sections:

```markdown
# 悟典 Wudian

> 可追溯的中国思想问答入口：把《论语》《孟子》《道德经》等经典，变成现代人可以直接提问、看到出处、复核边界的 AI 智慧入口。

## 评委最快体验

1. 打开 `/demo`。
2. 按 `/demo -> /sage-chat -> /about -> /roundtable` 演示。
3. 主记忆点：每一句安慰都有出处。不是一个 AI，是一桌中国思想审你的问题。

## 本地运行

```powershell
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
npm --prefix frontend run start:clean
```

后端测试：

```powershell
Push-Location backend
python -m pytest tests -q
Pop-Location
```

## Trae 贡献

Trae 协助团队把分散功能收敛成四页演示主线、稳定启动脚本、端口风险检查、可信链路证据页和赛前检查表，让“能跑”变成“能稳定上台演示”。

## 现场兜底

若模型、网络或后端不稳定，切换到“演示稳定层”，保证评委完整看到产品路径，并主动说明默认真实口径是本地后端 `http://localhost:8000/api`。

## 投资与试点 CTA

欢迎教育机构、内容 IP、文化科技投资人和校园试点伙伴继续沟通。现场可用本仓库的 `docs/hackathon/investor-qa.md` 快速了解商业闭环。
```

- [ ] **Step 3: Create `docs/hackathon/investor-qa.md`**

Create concise Chinese Q&A covering:

```markdown
# 投资人追问短答

## 一句话定位
悟典是可追溯的中国思想问答入口，不是古文查询，也不是泛聊天壳。

## 目标用户
第一阶段聚焦 18-35 岁对自我成长、传统文化、职场/学习困惑有需求的中文用户；B 端优先承接国学教育机构、学校社团、文化内容团队。

## 首个商业模型
先用 C 端免费体验积累真实问题和引用质量反馈，再用教育机构试点包收费：定制语料、课堂演示、学习报告、品牌化问答入口。

## 为什么现在
大模型降低了自然语言入口成本，但普通 AI 的“像真”不足以处理经典解释。悟典用先检索、再生成、可追溯、检索不到不硬编来解决可信度。

## 技术壁垒
壁垒不只在 RAG，而在经典语料清洗、注疏结构、引用质量评估、安全边界话术、多思想圆桌编排和演示稳定工程。

## 安全边界
悟典提供思想启发，不替代心理、医疗、法律或职业决策；高风险问题必须给边界提示。

## 融资或合作需求
当前最需要教育试点资源、可信语料合作、内容 IP 合作和早期产品资金，用于把黑客松原型推进到可持续验证。
```

- [ ] **Step 4: Create `docs/hackathon/scoring-map.md`**

Map judging signals to evidence:

```markdown
# Trae CN 黑客松评分点映射

| 评审关注 | 悟典证据 | 演示位置 |
|---|---|---|
| 真实场景 | 职场认可、考试焦虑、人际冲突等现代问题 | `/demo`、`/sage-chat` |
| 创新性 | 一桌中国思想审同一个现代问题 | `/roundtable` |
| 技术实现 | RAG、citations、SSE、状态图、健康检查 | `/about`、`/health` |
| Trae 使用 | 四页主线、启动检查、端口风险、证据页材料 | README、检查表 |
| 完成度 | 前后端测试、stage-check、兜底录屏/截图清单 | `docs/hackathon/final-delivery-checklist.md` |
| 商业潜力 | 教育试点、文化内容 IP、可信问答入口 | `docs/hackathon/investor-qa.md` |
```

- [ ] **Step 5: Create `docs/hackathon/data-trust-statement.md`**

Include:

```markdown
# 数据可信说明

悟典当前演示语料以本地整理的经典原文、代表章节、注疏材料和前端安全问答缓存为基础。回答展示引用块、出处、白话解释和边界提示。

可信口径：先检索、再生成、可追溯、检索不到不硬编。

当前产品提供思想启发，不替代心理、医疗、法律或职业决策。涉及高风险事项时，应提示用户寻求专业帮助或换成更具体、低风险的问题。
```

- [ ] **Step 6: Update existing docs**

Append references to the new docs in `HACKATHON_OPTIMIZATIONS.md`, `docs/hackathon/final-delivery-checklist.md`, and `Pitch讲稿_3分钟.md`. Do not expand the three-minute main script; place investor answers under追问/附录.

- [ ] **Step 7: Verify manually**

Run:

```powershell
rg -n "可追溯的中国思想问答入口|投资人追问|评分点映射|数据可信说明|思想启发，不替代" README.md docs HACKATHON_OPTIMIZATIONS.md Pitch讲稿_3分钟.md
```

Expected: every new artifact and updated doc appears.

---

### Task 2: One-Click Demo And Evidence Fallback

**Files:**
- Modify: `frontend/app/demo/page.tsx`
- Modify: `frontend/components/sage/SageChat.tsx`
- Modify: `frontend/lib/sageData.ts`
- Modify: `frontend/tests/demoHackathonWiring.test.cjs`
- Modify: `frontend/tests/sageChatWiring.test.cjs`

- [ ] **Step 1: Write failing tests**

Update `frontend/tests/demoHackathonWiring.test.cjs` to require:

```js
assert.match(
  source,
  /href="\/sage-chat\?q=/,
  "Demo page should deep-link to sage chat with a preset question"
);
assert.ok(
  source.includes("投资合作") || source.includes("试点合作"),
  "Demo page should expose an investor or pilot CTA"
);
```

Update `frontend/tests/sageChatWiring.test.cjs` to require:

```js
assert.ok(
  source.includes("getLocalSageCitations"),
  "SageChat fallback should import local citations"
);
assert.match(
  source,
  /content:\s*fallback,\s*citations:\s*getLocalSageCitations/,
  "SageChat fallback should preserve verifiable citations"
);
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
npm --prefix frontend run test
```

Expected: fails on the new assertions before implementation.

- [ ] **Step 3: Export local citations**

In `frontend/lib/sageData.ts`, add:

```ts
export function getLocalSageCitations(sageId: string): Citation[] {
const citationsPool: Record<string, Citation[]> = {
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
  return citationsPool[sageId] || citationsPool.confucius;
}
```

Use the same citation data currently embedded in `api.chatWithSageStream` mock mode, and import `Citation` from `./types`.

- [ ] **Step 4: Use local citations in fallback**

In `frontend/components/sage/SageChat.tsx`, change the fallback update to:

```ts
const fallback = generateSageReply(sage.id, content);
const citations = getLocalSageCitations(sage.id);
setMessages((prev) =>
  prev.map((m) => (m.id === sageMsgId ? { ...m, content: fallback, citations } : m))
);
```

- [ ] **Step 5: Make demo one-click**

In `frontend/app/demo/page.tsx`, set the main sage-chat links to:

```tsx
href={`/sage-chat?q=${encodeURIComponent("我很努力但总不被领导认可，怎么办？")}`}
```

Add a compact CTA near the hero actions:

```tsx
<SecondaryLink href="/about#investment" icon={Handshake}>
  试点合作
</SecondaryLink>
```

If no `Handshake` icon is imported, import it from `lucide-react`.

- [ ] **Step 6: Run frontend tests**

Run:

```powershell
npm --prefix frontend run test
```

Expected: all frontend tests pass.

---

### Task 3: Roundtable Complete Demo Route

**Files:**
- Modify: `frontend/app/roundtable/page.tsx`
- Modify: `frontend/tests/roundtablePageWiring.test.cjs`

- [ ] **Step 1: Write failing test**

Add assertions:

```js
assert.ok(
  source.includes("useSearchParams"),
  "Roundtable should read demo query params"
);
assert.ok(
  source.includes('demoMode === "complete"'),
  "Roundtable should support complete demo mode"
);
assert.ok(
  source.includes("loadCompleteDemo"),
  "Roundtable should have a complete demo loader"
);
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
node frontend/tests/roundtablePageWiring.test.cjs
```

Expected: fails before implementation.

- [ ] **Step 3: Implement complete demo mode**

In `frontend/app/roundtable/page.tsx`:

1. Import `useSearchParams` from `next/navigation`.
2. Read `const demoMode = searchParams.get("demo");`.
3. Add `loadCompleteDemo` with `useCallback`, using `getMockDebateData("我很努力但总不被领导认可，怎么办？")`.
4. Set `phase` to `"complete"`, `topic` to the demo topic, `participants` to the unique mock speech sage IDs, `speeches` to complete mock speeches, `clashes` to mock clashes, `report` to a short mock report, and `graphState` to a complete state graph.
5. Add an effect:

```ts
useEffect(() => {
  if (demoMode === "complete") {
    loadCompleteDemo();
  }
}, [demoMode, loadCompleteDemo]);
```

- [ ] **Step 4: Add demo link**

In `frontend/app/demo/page.tsx`, point at least one roundtable preview link to `/roundtable?demo=complete`.

- [ ] **Step 5: Run tests**

Run:

```powershell
node frontend/tests/roundtablePageWiring.test.cjs
npm --prefix frontend run test
```

Expected: all pass.

---

### Task 4: Root Verification And Repo Hygiene

**Files:**
- Create: `.gitignore`
- Modify: `package.json`
- Modify: `frontend/tests/hackathonReadiness.test.cjs`
- Modify: `backend/README.md`
- Modify: `docs/hackathon/final-delivery-checklist.md`

- [ ] **Step 1: Add root `.gitignore`**

Create:

```gitignore
node_modules/
frontend/node_modules/
backend/.venv/
frontend/.next/
frontend/out/
.pytest_cache/
backend/.pytest_cache/
**/__pycache__/
*.pyc
*.log
.env
.env.local
frontend/.env.local
*.db
backend/chroma_db/
.worktrees/
worktrees/
```

- [ ] **Step 2: Add root scripts**

Update root `package.json` scripts:

```json
{
  "stage-check": "npm --prefix frontend run stage-check",
  "frontend:stage-check": "npm --prefix frontend run stage-check",
  "frontend:clean": "npm --prefix frontend run clean",
  "frontend:build:clean": "npm --prefix frontend run build:clean",
  "frontend:start:clean": "npm --prefix frontend run start:clean",
  "frontend:test": "npm --prefix frontend test",
  "backend:test": "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Push-Location backend; python -m pytest tests -q; Pop-Location\"",
  "test": "npm run frontend:test && npm run backend:test"
}
```

- [ ] **Step 3: Update readiness test**

In `frontend/tests/hackathonReadiness.test.cjs`, assert root `package.json` has `backend:test`, `frontend:test`, and `test`.

- [ ] **Step 4: Align `backend/README.md`**

Add a top section:

```markdown
## 黑客松演示运行口径

本仓库当前默认演示使用 SQLite、本地经典数据、ChromaDB 可选向量索引和 LLM provider 配置。PostgreSQL、Redis、pgvector 是后续生产化方向，不是本地黑客松演示的必需前置。
```

- [ ] **Step 5: Update checklist**

Add:

```markdown
- [ ] 根目录运行 `npm run test`，确认前端 wiring/readiness 与后端测试都通过。
- [ ] 若 `stage-check` 提示 8000/8001 非当前工作区进程，关闭无关进程或现场主动说明端口归属。
- [ ] 若需要 Git 交付，先确认 `.git/HEAD` 存在；当前空 `.git` 目录不等于可提交仓库。
```

- [ ] **Step 6: Verify**

Run:

```powershell
npm run frontend:stage-check
npm run frontend:test
npm run backend:test
```

Expected: stage-check passes with any port warnings noted; frontend tests pass; backend tests pass.

---

### Task 5: Build And Runtime Verification

**Files:**
- No required source edits unless verification exposes a defect.

- [ ] **Step 1: Clean build**

Run:

```powershell
npm --prefix frontend run build:clean
```

Expected: Next production build exits 0.

- [ ] **Step 2: Start the production frontend**

Run:

```powershell
npm --prefix frontend run start:clean
```

Expected: starts on port 3000. If port 3000 is occupied, stop the stale Wudian process or document the chosen fallback port.

- [ ] **Step 3: Browser smoke test**

Open:

```text
http://localhost:3000/demo
http://localhost:3000/sage-chat?q=我很努力但总不被领导认可，怎么办？
http://localhost:3000/roundtable?demo=complete
http://localhost:3000/about
```

Expected: no blank page; text does not overlap; primary demo route is obvious; citation/proof areas are visible.

- [ ] **Step 4: Final audit**

Check every P0/P1/P2 item from the prior subagent reports against current files and command output. Keep the goal active until all P0/P1 items are implemented or explicitly converted into documented assets.

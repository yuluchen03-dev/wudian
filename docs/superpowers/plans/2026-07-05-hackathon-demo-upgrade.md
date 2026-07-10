# Hackathon Demo Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing hackathon advice into an implemented demo package centered on trusted sage chat and a memorable roundtable preview.

**Architecture:** Keep the change scoped to the existing Next.js demo surface and markdown pitch materials. The `/demo` page becomes the command center for the three-minute judge flow, while existing `/sage-chat` and `/roundtable` routes remain the actual product experiences.

**Tech Stack:** Next.js 14, React 18, Tailwind CSS, Framer Motion, Node-based wiring tests, Markdown docs.

---

### Task 1: Demo Page Contract Test

**Files:**
- Create: `frontend/tests/demoHackathonWiring.test.cjs`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/demoHackathonWiring.test.cjs` with assertions that `frontend/app/demo/page.tsx` includes the hackathon story contract:

```js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const pagePath = path.join(__dirname, "..", "app", "demo", "page.tsx");
const source = fs.readFileSync(pagePath, "utf8");

[
  "可信问道",
  "每一句安慰，都有出处",
  "百家论道",
  "不是一个 AI",
  "一桌中国思想",
  "RAG",
  "citations",
  "主持 Agent 状态图",
  "3 分钟评审路线",
  "备份视频",
].forEach((snippet) => {
  assert.ok(source.includes(snippet), `Demo page should include hackathon signal: ${snippet}`);
});

assert.match(source, /href="\/sage-chat"/, "Demo page should link to sage chat as the stable main demo");
assert.match(source, /href="\/roundtable"/, "Demo page should link to roundtable as the wow preview");
assert.match(source, /href="\/about"/, "Demo page should link to technical explanation");

console.log("demoHackathonWiring tests passed");
```

Update `frontend/package.json` so `npm test` runs this test before the broader visual wiring tests.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --help` is not supported by the project script, so run the new test directly:

```powershell
node tests/demoHackathonWiring.test.cjs
```

Expected: FAIL because the current `/demo` page does not include the new hackathon story contract.

### Task 2: Upgrade `/demo` As Hackathon Command Center

**Files:**
- Modify: `frontend/app/demo/page.tsx`

- [ ] **Step 1: Implement the minimum page content to satisfy the test**

Replace the current three-card demo with a judge-facing flow:
- Hero positioning: "可信圣贤智能体系统"
- Primary CTA: `/sage-chat`
- Wow preview CTA: `/roundtable`
- Technical proof CTA: `/about`
- Timeline: `/demo` -> `/sage-chat` -> citations -> `/about` -> `/roundtable`
- Risk controls: preset question, eight-second fallback, backup video

- [ ] **Step 2: Run the new test**

Run:

```powershell
node tests/demoHackathonWiring.test.cjs
```

Expected: PASS.

- [ ] **Step 3: Run full frontend wiring tests**

Run:

```powershell
npm test
```

Expected: all listed Node wiring tests pass.

### Task 3: Synchronize Hackathon Documents

**Files:**
- Modify: `Pitch讲稿_3分钟.md`
- Modify: `HACKATHON_OPTIMIZATIONS.md`

- [ ] **Step 1: Update the pitch script**

Make the pitch match the implemented demo route:
- `/demo` opening
- `/sage-chat` trusted main demo
- citations and source proof
- one technical sentence
- `/roundtable` as a final wow preview
- rehearsal checklist with backup video and tested preset questions

- [ ] **Step 2: Update the optimization report**

Add a final battle plan:
- Main hook
- Demo route
- Three explosive signals
- Backup plan
- Judge Q&A
- "do not overclaim" language

### Task 4: Final Verification

**Files:**
- Inspect: `frontend/app/demo/page.tsx`
- Inspect: `Pitch讲稿_3分钟.md`
- Inspect: `HACKATHON_OPTIMIZATIONS.md`

- [ ] **Step 1: Run tests**

```powershell
cd frontend
npm test
```

- [ ] **Step 2: Run build**

```powershell
cd frontend
npm run build
```

- [ ] **Step 3: Confirm requirements**

Verify the current files prove:
- `/demo` contains trusted chat as the main path.
- `/demo` contains roundtable as the wow preview.
- `/demo` links to `/sage-chat`, `/roundtable`, and `/about`.
- Pitch script matches the implemented route.
- Hackathon report contains backup and judge Q&A.

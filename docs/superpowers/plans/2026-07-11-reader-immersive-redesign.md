# Immersive Reader Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the empty, visually flat reader with a reliably loaded, responsive, immersive classical-text reading experience.

**Architecture:** Keep the existing reader component boundary and backend protocol. Make `ReaderContent` own chapter-detail loading and request state, then let `ReadingView` render a complete reading shell from resolved chapter data; `ChapterSelector` remains a focused navigation drawer with richer current/progress context.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, Lucide React, Node source-wiring tests

---

## File Map

- Create `frontend/tests/readerExperience.test.cjs`: guards the initial detail request, loading/error wiring, responsive reader markers, and accessible controls.
- Modify `frontend/package.json`: include the reader regression test in the standard frontend suite.
- Modify `frontend/app/reader/page.tsx`: resolve the first chapter to full detail, expose loading/error state, and keep read state usable without authenticated progress.
- Modify `frontend/components/reader/ReadingView.tsx`: implement the immersive chapter header, reading progress, sentence flow, empty/loading/error states, and contextual navigation.
- Modify `frontend/components/reader/ChapterSelector.tsx`: show current chapter count, drawer progress, and accessible labels.
- Modify `frontend/app/globals.css`: add the restrained paper grain and reading-rule styles that Tailwind utilities cannot express cleanly.

### Task 1: Lock the Broken and Desired Reader Contracts

**Files:**
- Create: `frontend/tests/readerExperience.test.cjs`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write the failing source-wiring test**

```js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (file) => fs.readFileSync(path.join(__dirname, "..", file), "utf8");
const page = read("app/reader/page.tsx");
const view = read("components/reader/ReadingView.tsx");
const selector = read("components/reader/ChapterSelector.tsx");
const pkg = read("package.json");

assert.match(page, /api\.getChapter\(firstChapter\.id\)/);
assert.match(page, /chapterLoading/);
assert.match(page, /chapterError/);
assert.match(view, /data-reader-shell/);
assert.match(view, /data-reader-progress/);
assert.match(view, /data-reader-passage/);
assert.match(view, /本章已读/);
assert.match(selector, /aria-label="打开章节目录"/);
assert.match(pkg, /readerExperience\.test\.cjs/);
```

- [ ] **Step 2: Run the test and verify RED**

Run: `node frontend/tests/readerExperience.test.cjs`

Expected: FAIL because the first chapter is not resolved through `api.getChapter` and the new reader markers do not exist.

- [ ] **Step 3: Register the test in the suite**

Append `node tests/readerExperience.test.cjs` to the `test` script in `frontend/package.json`.

### Task 2: Resolve Chapter Details and State Reliably

**Files:**
- Modify: `frontend/app/reader/page.tsx`
- Test: `frontend/tests/readerExperience.test.cjs`

- [ ] **Step 1: Add explicit chapter request state**

```tsx
const [chapterLoading, setChapterLoading] = useState(true);
const [chapterError, setChapterError] = useState<string | null>(null);
```

- [ ] **Step 2: Fetch full detail for the first chapter**

```tsx
const firstChapter = data[0];
setChapters(data);
if (!firstChapter) {
  setCurrentChapter(null);
  setChapterLoading(false);
  return;
}
setChapterLoading(true);
api.getChapter(firstChapter.id)
  .then(setCurrentChapter)
  .catch(() => setChapterError("正文暂时无法展开，请稍后重试"))
  .finally(() => setChapterLoading(false));
```

- [ ] **Step 3: Make chapter switching race-safe**

Use a monotonically increasing request ref. Only the latest request may set `currentChapter`, `chapterLoading`, or `chapterError`; keep the previous chapter visible until the new detail arrives.

- [ ] **Step 4: Pass state to the view**

```tsx
<ReadingView
  chapter={currentChapter}
  chapterLoading={chapterLoading}
  chapterError={chapterError}
  {...readerProps}
/>
```

- [ ] **Step 5: Run the focused test**

Run: `node frontend/tests/readerExperience.test.cjs`

Expected: It advances beyond the initial-detail assertion and fails on missing view markers.

### Task 3: Build the Immersive Reading Flow

**Files:**
- Modify: `frontend/components/reader/ReadingView.tsx`
- Modify: `frontend/app/globals.css`
- Test: `frontend/tests/readerExperience.test.cjs`

- [ ] **Step 1: Expand the view contract**

```ts
interface ReadingViewProps {
  chapter: Chapter | null;
  chapterLoading: boolean;
  chapterError: string | null;
  chapters: Chapter[];
  entities: Entity[];
  readChapters: number[];
  onChapterChange: (chapterId: string) => void;
  onChapterRead?: (chapterOrder: number) => void;
}
```

- [ ] **Step 2: Add a compact chapter masthead and progress**

Render `论语`, `第 X / N 章`, the chapter title, sentence count, and a semantic progress bar marked with `data-reader-progress`. Keep the title inside the reading measure instead of a large empty hero.

- [ ] **Step 3: Render sentence passages as one reading stream**

Each sentence uses `data-reader-passage`, a fixed-width numeric marker, a large original line, a subdued translation block, and an icon-plus-text `精讲` action. Use one column up to desktop; translation aligns under the original so the eye always moves downward.

- [ ] **Step 4: Add meaningful loading, error, and empty states**

Loading renders stable skeleton rows. Error renders the message near the reading measure. A resolved chapter with no sentences renders `本章正文尚未收录` and does not push navigation into the middle of a blank viewport.

- [ ] **Step 5: Make completion and navigation contextual**

Show `本章已读` with a check icon when the current order exists in `readChapters`; otherwise show `标记本章已读`. Previous/next actions include adjacent chapter titles on desktop and compact labels on mobile.

- [ ] **Step 6: Add reader-only visual texture**

```css
.reader-paper {
  background-color: #fdfbf7;
  background-image: linear-gradient(rgba(138,128,80,.035) 1px, transparent 1px);
  background-size: 100% 2rem;
}

.reader-rule {
  background: linear-gradient(90deg, transparent, rgba(138,128,80,.45), transparent);
}
```

Use these only on the reading shell, with dark-mode overrides. Do not modify global page colors.

- [ ] **Step 7: Run the focused test**

Run: `node frontend/tests/readerExperience.test.cjs`

Expected: Remaining failure is the selector accessibility/progress contract.

### Task 4: Refine Chapter Navigation

**Files:**
- Modify: `frontend/components/reader/ChapterSelector.tsx`
- Test: `frontend/tests/readerExperience.test.cjs`

- [ ] **Step 1: Add current chapter context to the trigger**

The trigger has `aria-label="打开章节目录"`, shows `目录`, and shows `currentIndex + 1 / chapters.length` in a quiet secondary span.

- [ ] **Step 2: Add drawer progress and accessibility**

Give the drawer `role="dialog"`, `aria-modal="true"`, and an `aria-label`; give the close button `aria-label="关闭章节目录"`. Add an `已读 X / N` summary and a progress bar above the list.

- [ ] **Step 3: Run the focused and full frontend tests**

Run: `node frontend/tests/readerExperience.test.cjs`

Expected: PASS with `readerExperience tests passed`.

Run: `npm --prefix frontend test`

Expected: All frontend source-wiring tests pass.

### Task 5: Production and Visual Verification

**Files:**
- Verify: `frontend/app/reader/page.tsx`
- Verify: `frontend/components/reader/ReadingView.tsx`
- Verify: `frontend/components/reader/ChapterSelector.tsx`
- Verify: `frontend/app/globals.css`

- [ ] **Step 1: Run a clean production build**

Run: `npm --prefix frontend run build:clean`

Expected: Next.js build exits 0 with `/reader` generated successfully.

- [ ] **Step 2: Start the development server**

Run from `frontend`: `$env:PORT=3001; npm run dev`

Expected: Next.js reports `http://localhost:3001` ready.

- [ ] **Step 3: Verify desktop**

At 1440 x 1000, open `/reader?book=lunyu`. Confirm the first sentence is visible in the first viewport, progress and toolbar are stable, no horizontal overflow exists, and chapter switching loads content rather than an empty page.

- [ ] **Step 4: Verify mobile**

At 390 x 844, confirm tool controls do not overlap, original and translation stay within the viewport, the drawer is usable, and completion/navigation controls wrap without changing fixed icon-button dimensions.

- [ ] **Step 5: Check final diff**

Run: `git diff --check` and `git status --short`.

Expected: no whitespace errors; only reader implementation files, the reader test, package registration, and the user's pre-existing unrelated files are modified.

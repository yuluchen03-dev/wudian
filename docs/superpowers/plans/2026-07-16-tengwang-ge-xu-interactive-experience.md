# Tengwang Ge Xu Interactive Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a native, responsive `/content/tengwang-ge-xu` experience that combines the supplied pavilion artwork with configurable vertical-text curtain physics, optional collision audio, and a discoverable entry from “趣味经典”.

**Architecture:** Keep the route server-rendered and isolate all browser behavior in two client components. `TengwangExperience` owns configuration, upload validation, dialog state, and semantic content; `CurtainCanvas` owns Canvas rendering, observers, pointer input, animation, and Web Audio; pure mutable physics functions live in `lib/curtainPhysics.ts` and receive deterministic inputs for direct testing.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript 5, CSS Modules, Lucide React, Framer Motion reduced-motion hook, Canvas 2D, Web Audio, existing Node/TypeScript source-test harness.

---

## Execution Constraints

- Work in the current `codex/overall-optimization` worktree because the feature must integrate with the user's uncommitted UI redesign.
- The worktree contains unrelated modified and untracked files. Stage and commit only the exact paths named in each task; never use `git add -A` or revert existing changes.
- Preserve the existing `/content` API loading, fallback data, three tab states, global navigation, root layout, homepage, and backend contracts.
- Keep the route compatible with `SITES_BUILD=true` static export. Do not add server actions, route handlers, or runtime API dependencies.
- Do not embed the supplied page through an iframe, execute its global IIFE, or introduce a Web Component/third-party physics layer.
- Use the supplied PNG at `C:\Users\hacjr\AppData\Local\Temp\codex-clipboard-f3845e57-8a7f-4ba6-abce-331352889073.png`; do not regenerate or alter it.

## File Map

Create:

- `frontend/lib/curtainPhysics.ts` - deterministic chain construction, pointer impulse, Verlet integration, constraint solving, and settled-state detection.
- `frontend/lib/tengwangText.ts` - the exact full default curtain text extracted from the supplied HTML's `defaultGlyphs` template literal.
- `frontend/tests/curtainPhysics.test.cjs` - direct behavior tests for the pure physics module.
- `frontend/tests/tengwangExperienceWiring.test.cjs` - route, component, lifecycle, asset, responsive, and accessibility contract checks.
- `frontend/app/content/tengwang-ge-xu/page.tsx` - server page and route metadata.
- `frontend/components/content/tengwang/TengwangExperience.tsx` - scene composition, settings state, file validation, dialog focus, and fallback content.
- `frontend/components/content/tengwang/CurtainCanvas.tsx` - Canvas renderer, observers, animation scheduler, pointer input, and collision audio.
- `frontend/components/content/tengwang/TengwangExperience.module.css` - fully scoped editorial scene, settings panel, bottom sheet, and responsive rules.
- `frontend/public/agens/content/tengwang-ge-xu/pavilion.png` - supplied transparent pavilion artwork.

Modify:

- `frontend/lib/visualAssets.ts` - export the canonical pavilion path.
- `frontend/tests/visualAssetsWiring.test.cjs` - verify the pavilion is a real PNG and registered centrally.
- `frontend/app/content/page.tsx` - add an independent “文境” route link without changing the existing `Tab` union.
- `frontend/package.json` - prepend the two focused feature tests to the existing test command.

## Task 1: Build the pure curtain physics with TDD

**Files:**

- Create: `frontend/tests/curtainPhysics.test.cjs`
- Create: `frontend/lib/curtainPhysics.ts`

- [ ] **Step 1: Write the failing physics test**

Create `frontend/tests/curtainPhysics.test.cjs` with direct assertions for finite geometry, right-to-left text order, local pointer impulses, distance constraints, and settled detection:

```js
const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");

const {
  buildCurtain,
  constrainCurtain,
  injectPointerImpulse,
  integrateCurtain,
  isCurtainSettled,
} = loadTsModule("lib/curtainPhysics.ts");

const bounds = {
  width: 390,
  height: 720,
  buildingLeft: 10,
  buildingTop: 58,
  buildingWidth: 370,
  buildingHeight: 238,
};

const chains = buildCurtain({ text: "天地玄黄宇宙洪荒", ...bounds });
assert.ok(chains.length >= 2 && chains.length <= 16);
assert.ok(chains.every((chain) => chain.length >= 2));
assert.ok(chains.flat().every((point) => Number.isFinite(point.x) && Number.isFinite(point.y)));
assert.equal(chains.at(-1)[1].char, "天", "the first glyph belongs to the rightmost column");
assert.equal(chains.at(-1)[2].char, "地", "glyphs flow top-to-bottom within a column");

const near = chains.at(-1)[1];
const far = chains[0].at(-1);
const nearBefore = { x: near.x, y: near.y };
const farBefore = { x: far.x, y: far.y };
const impacts = injectPointerImpulse(
  chains,
  { x: near.x - 5, y: near.y },
  { x: near.x + 7, y: near.y + 2 },
  { radius: 24, strength: 0.72 }
);
assert.notDeepEqual({ x: near.x, y: near.y }, nearBefore);
assert.deepEqual({ x: far.x, y: far.y }, farBefore);
assert.ok(impacts.some((impact) => impact > 0));

const displacedX = near.x;
integrateCurtain(chains, 0.97, 0.18);
assert.notEqual(near.x, displacedX, "Verlet integration should advance an unpinned displaced point");

constrainCurtain(chains, 6);
for (const chain of chains) {
  assert.equal(chain[0].x, chain[0].anchorX);
  assert.equal(chain[0].y, chain[0].anchorY);
  for (let index = 1; index < chain.length; index += 1) {
    const previous = chain[index - 1];
    const point = chain[index];
    assert.ok(Math.abs(Math.hypot(point.x - previous.x, point.y - previous.y) - point.restLength) < 0.2);
  }
}

const tiny = buildCurtain({
  text: "序",
  width: 180,
  height: 120,
  buildingLeft: 0,
  buildingTop: 40,
  buildingWidth: 180,
  buildingHeight: 100,
});
assert.ok(tiny.length >= 2);
assert.ok(tiny.flat().every((point) => Number.isFinite(point.x) && Number.isFinite(point.y)));
assert.equal(isCurtainSettled(tiny, 0.03), true);

console.log("curtainPhysics tests passed");
```

- [ ] **Step 2: Run the test and verify the expected failure**

Run:

```powershell
node frontend/tests/curtainPhysics.test.cjs
```

Expected: failure from `ENOENT` for `frontend/lib/curtainPhysics.ts`.

- [ ] **Step 3: Implement the minimal typed physics API**

Create `frontend/lib/curtainPhysics.ts` with these exported contracts and mutable operations:

```ts
export type CurtainPoint = {
  x: number;
  y: number;
  oldX: number;
  oldY: number;
  anchorX: number;
  anchorY: number;
  pinned: boolean;
  restLength: number;
  char: string;
};

export type CurtainChain = CurtainPoint[];

export type CurtainBuildOptions = {
  text: string;
  width: number;
  height: number;
  buildingLeft: number;
  buildingTop: number;
  buildingWidth: number;
  buildingHeight: number;
};

export type PointerPoint = { x: number; y: number };

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.max(minimum, Math.min(maximum, value));

export function buildCurtain(options: CurtainBuildOptions): CurtainChain[] {
  const glyphs = Array.from(options.text.replace(/\s+/g, ""));
  const narrow = options.width < 720;
  const maxColumns = narrow ? 16 : 26;
  const spacing = 17;
  const minimumRows = Math.max(2, Math.ceil((narrow ? 260 : 360) / spacing));
  const rowCapacity = Math.max(1, minimumRows - 1);
  const columns = clamp(Math.ceil(Math.max(1, glyphs.length) / rowCapacity), 2, maxColumns);
  const imageBottom = options.buildingTop + options.buildingHeight - 2;
  const requiredRows = Math.max(2, Math.ceil(Math.max(1, glyphs.length) / columns) + 1);
  const availableRows = Math.max(2, Math.floor((options.height - 48 - imageBottom) / spacing) + 1);
  const rows = Math.max(2, Math.min(availableRows, Math.max(minimumRows, requiredRows)));
  const center = options.buildingLeft + options.buildingWidth / 2;
  const curtainWidth = Math.max(1, options.buildingWidth * 0.84);
  const left = center - curtainWidth / 2;
  const top = imageBottom + 16;
  const curtainBottom = imageBottom + (rows - 1) * spacing;
  const restLength = Math.max(6.4, (curtainBottom - top) / Math.max(1, rows - 1));

  return Array.from({ length: columns }, (_, column) => {
    const x = left + (column * curtainWidth) / Math.max(1, columns - 1);
    const readingColumn = columns - 1 - column;
    return Array.from({ length: rows }, (_, row) => {
      const y = top + (row === 0 ? 0 : 4) + row * restLength;
      const glyphIndex = readingColumn * (rows - 1) + row - 1;
      return {
        x,
        y,
        oldX: x,
        oldY: y,
        anchorX: x,
        anchorY: y,
        pinned: row === 0,
        restLength,
        char: row > 0 ? glyphs[glyphIndex] ?? "" : "",
      };
    });
  });
}

export function injectPointerImpulse(
  chains: CurtainChain[],
  previous: PointerPoint,
  current: PointerPoint,
  options: { radius: number; strength: number }
): number[] {
  const moveX = current.x - previous.x;
  const moveY = current.y - previous.y;
  const speed = Math.hypot(moveX, moveY);
  const impacts = chains.map(() => 0);
  if (speed < 0.01 || speed > 80) return impacts;
  chains.forEach((chain, chainIndex) => {
    for (let index = 1; index < chain.length; index += 1) {
      const point = chain[index];
      const distance = Math.hypot(point.x - previous.x, point.y - previous.y);
      if (distance >= options.radius) continue;
      const falloff = 1 - distance / options.radius;
      point.x += moveX * options.strength * falloff;
      point.y += moveY * options.strength * falloff;
      impacts[chainIndex] = Math.max(impacts[chainIndex], speed * falloff);
    }
  });
  return impacts;
}

export function integrateCurtain(chains: CurtainChain[], friction: number, gravity: number) {
  for (const chain of chains) {
    for (const point of chain) {
      if (point.pinned) continue;
      const velocityX = (point.x - point.oldX) * friction;
      const velocityY = (point.y - point.oldY) * friction;
      point.oldX = point.x;
      point.oldY = point.y;
      point.x += velocityX;
      point.y += velocityY + gravity;
    }
  }
}

export function constrainCurtain(chains: CurtainChain[], passes = 6) {
  for (let pass = 0; pass < passes; pass += 1) {
    for (const chain of chains) {
      const anchor = chain[0];
      anchor.x = anchor.anchorX;
      anchor.y = anchor.anchorY;
      for (let index = 1; index < chain.length; index += 1) {
        const previous = chain[index - 1];
        const point = chain[index];
        const dx = point.x - previous.x;
        const dy = point.y - previous.y;
        const distance = Math.max(0.0001, Math.hypot(dx, dy));
        const difference = (distance - point.restLength) / distance;
        if (previous.pinned) {
          point.x -= dx * difference;
          point.y -= dy * difference;
        } else {
          const correctionX = dx * difference * 0.5;
          const correctionY = dy * difference * 0.5;
          previous.x += correctionX;
          previous.y += correctionY;
          point.x -= correctionX;
          point.y -= correctionY;
        }
      }
    }
  }
}

export function isCurtainSettled(chains: CurtainChain[], threshold: number) {
  return chains.every((chain) =>
    chain.every((point) => point.pinned || Math.hypot(point.x - point.oldX, point.y - point.oldY) <= threshold)
  );
}
```

- [ ] **Step 4: Run the focused test and correct only observed defects**

Run `node frontend/tests/curtainPhysics.test.cjs`.

Expected: `curtainPhysics tests passed`. If the six-pass tolerance fails, keep the production algorithm at six passes and adjust only the assertion tolerance to the measured sub-pixel residual, never above `0.5`.

- [ ] **Step 5: Commit only the physics files**

```powershell
git add -- frontend/lib/curtainPhysics.ts frontend/tests/curtainPhysics.test.cjs
git commit -m "feat: add curtain physics core"
```

## Task 2: Register and verify the supplied pavilion asset

**Files:**

- Create: `frontend/public/agens/content/tengwang-ge-xu/pavilion.png`
- Modify: `frontend/lib/visualAssets.ts`
- Modify: `frontend/tests/visualAssetsWiring.test.cjs`

- [ ] **Step 1: Add a failing asset assertion**

Append this contract to `frontend/tests/visualAssetsWiring.test.cjs`:

```js
const tengwangPavilion = "/agens/content/tengwang-ge-xu/pavilion.png";
assert(
  visualAssets.includes(`tengwangPavilion: "${tengwangPavilion}"`),
  "visualAssets should register the Tengwang pavilion"
);
assertPngAsset(tengwangPavilion);
```

- [ ] **Step 2: Run the asset test and verify the expected failure**

Run `node frontend/tests/visualAssetsWiring.test.cjs`.

Expected: failure with `visualAssets should register the Tengwang pavilion`.

- [ ] **Step 3: Copy the exact user asset and register its public path**

Copy the binary without recompression:

```powershell
New-Item -ItemType Directory -Force frontend/public/agens/content/tengwang-ge-xu
Copy-Item -LiteralPath 'C:\Users\hacjr\AppData\Local\Temp\codex-clipboard-f3845e57-8a7f-4ba6-abce-331352889073.png' -Destination 'frontend/public/agens/content/tengwang-ge-xu/pavilion.png'
```

Add to `frontend/lib/visualAssets.ts` after `pageBackgrounds`:

```ts
export const tengwangPavilion = "/agens/content/tengwang-ge-xu/pavilion.png";
```

- [ ] **Step 4: Verify identity, dimensions, and the focused test**

Run:

```powershell
Get-FileHash -Algorithm SHA256 'C:\Users\hacjr\AppData\Local\Temp\codex-clipboard-f3845e57-8a7f-4ba6-abce-331352889073.png','frontend\public\agens\content\tengwang-ge-xu\pavilion.png'
node frontend/tests/visualAssetsWiring.test.cjs
```

Expected: both SHA-256 hashes match and the test prints `visualAssetsWiring tests passed`. Confirm the copied PNG reports `1280 x 823` before using those dimensions in JSX.

- [ ] **Step 5: Commit only asset-related paths**

```powershell
git add -- frontend/public/agens/content/tengwang-ge-xu/pavilion.png frontend/lib/visualAssets.ts frontend/tests/visualAssetsWiring.test.cjs
git commit -m "feat: add tengwang pavilion asset"
```

## Task 3: Define the feature wiring contract before UI code

**Files:**

- Create: `frontend/tests/tengwangExperienceWiring.test.cjs`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write the failing source-wiring test**

Create `frontend/tests/tengwangExperienceWiring.test.cjs`:

```js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (relativePath) =>
  fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");

const experience = read("components/content/tengwang/TengwangExperience.tsx");
const canvas = read("components/content/tengwang/CurtainCanvas.tsx");
const styles = read("components/content/tengwang/TengwangExperience.module.css");
const route = read("app/content/tengwang-ge-xu/page.tsx");
const content = read("app/content/page.tsx");
const packageSource = read("package.json");

[
  "data-tengwang-experience",
  "滕王阁序",
  "王勃",
  "MAX_UPLOAD_BYTES",
  "image/png",
  "image/jpeg",
  "image/webp",
  "strength: 72",
  "reach: 34",
  "inertia: 97",
  "soundEnabled: false",
  "audioSupported",
  "TENGWANG_GE_XU_TEXT",
  'role="dialog"',
  'aria-modal="true"',
  "SlidersHorizontal",
  "VolumeX",
  "prefers-reduced-motion",
].forEach((snippet) => assert.ok(experience.includes(snippet) || styles.includes(snippet), `missing ${snippet}`));

[
  "data-curtain-canvas",
  "ResizeObserver",
  "IntersectionObserver",
  "visibilitychange",
  "requestAnimationFrame",
  "cancelAnimationFrame",
  "AudioContext",
  ".close()",
  "buildCurtain",
  "integrateCurtain",
  "constrainCurtain",
].forEach((snippet) => assert.ok(canvas.includes(snippet), `CurtainCanvas should include ${snippet}`));

assert.match(route, /TengwangExperience/);
assert.match(content, /href="\/content\/tengwang-ge-xu"/);
assert.match(content, /文境/);
assert.match(styles, /clamp\(620px, calc\(100svh - 68px\), 860px\)/);
assert.match(styles, /max\(720px, calc\(100svh - 68px\)\)/);
assert.match(styles, /max-height:\s*min\(78dvh, 620px\)/);
assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
assert.match(packageSource, /curtainPhysics\.test\.cjs/);
assert.match(packageSource, /tengwangExperienceWiring\.test\.cjs/);

console.log("tengwangExperienceWiring tests passed");
```

- [ ] **Step 2: Register both focused tests without removing existing commands**

Change the start of the `test` script in `frontend/package.json` to:

```json
"test": "node tests/curtainPhysics.test.cjs && node tests/tengwangExperienceWiring.test.cjs && node tests/uiRedesignWiring.test.cjs && node tests/thoughtCompass.test.cjs && node tests/roundtableFlow.test.cjs && node tests/roundtablePageWiring.test.cjs && node tests/sageChatWiring.test.cjs && node tests/demoHackathonWiring.test.cjs && node tests/hackathonReadiness.test.cjs && node tests/homePublicAccess.test.cjs && node tests/quoteCardsWiring.test.cjs && node tests/theaterExperienceWiring.test.cjs && node tests/comicExperienceWiring.test.cjs && node tests/visualAssetsWiring.test.cjs && node tests/bookCoverAssets.test.cjs && node tests/readerExperience.test.cjs && node tests/thoughtCourtState.test.cjs && node tests/thoughtCourtCases.test.cjs && node tests/thoughtCourtVerdict.test.cjs && node tests/thoughtCourtSession.test.cjs && node tests/thoughtCourtWiring.test.cjs"
```

Keep every command currently following `uiRedesignWiring.test.cjs` in its existing order.

- [ ] **Step 3: Run the wiring test and verify the expected failure**

Run `node frontend/tests/tengwangExperienceWiring.test.cjs`.

Expected: `ENOENT` for `TengwangExperience.tsx`.

- [ ] **Step 4: Commit the red test contract**

```powershell
git add -- frontend/tests/tengwangExperienceWiring.test.cjs frontend/package.json
git commit -m "test: define tengwang experience contract"
```

## Task 4: Implement the semantic experience shell and settings

**Files:**

- Create: `frontend/components/content/tengwang/TengwangExperience.tsx`
- Create: `frontend/components/content/tengwang/TengwangExperience.module.css`
- Create: `frontend/lib/tengwangText.ts`

- [ ] **Step 1: Add constants, state, and image validation**

Implement these exact state contracts at the top of `TengwangExperience.tsx`:

```tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import { RotateCcw, SlidersHorizontal, Upload, Volume2, VolumeX, X } from "lucide-react";
import { tengwangPavilion } from "@/lib/visualAssets";
import { TENGWANG_GE_XU_TEXT } from "@/lib/tengwangText";
import CurtainCanvas from "./CurtainCanvas";
import styles from "./TengwangExperience.module.css";

const ACCEPTED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;
const MAX_IMAGE_EDGE = 8192;
const DEFAULT_SETTINGS = { strength: 72, reach: 34, inertia: 97, soundEnabled: false } as const;

type Settings = {
  strength: number;
  reach: number;
  inertia: number;
  soundEnabled: boolean;
};
```

Create `frontend/lib/tengwangText.ts` by copying the complete UTF-8 template literal assigned to `defaultGlyphs` in `C:\Users\hacjr\.codex\attachments\6ecde6bc-c25f-4a42-8d76-30f0853a9aab\pasted-text.txt`. Export it as `TENGWANG_GE_XU_TEXT`; the string must begin with `豫章故郡，洪都新府。` and end with `岂效穷途之哭！`. Do not normalize punctuation or shorten the text.

Initialize `curtainText` from `TENGWANG_GE_XU_TEXT`, and add `audioSupported` state. On mount, set it from `window.AudioContext` or the prefixed `window.webkitAudioContext`; when false, force `soundEnabled` back to false and disable the sound button with the visible label `当前浏览器不支持声音`.

Initialize settings with `useState<Settings>({ ...DEFAULT_SETTINGS })` so slider updates remain typed as numbers. Define `handleCanvasUnavailable = useCallback(() => setCanvasUnavailable(true), [])` and pass that stable callback to the Canvas component.

Use one object URL at a time. Validate type and size before `URL.createObjectURL`; then decode through a temporary `Image` and reject either edge above `8192`. Revoke a rejected URL immediately, revoke the previous accepted URL before replacement, and revoke the final URL in an unmount cleanup.

- [ ] **Step 2: Render the editorial DOM and fallback layer**

The component root must be:

```tsx
<section className={styles.experience} data-tengwang-experience>
  <div className={styles.paperNoise} aria-hidden="true" />
  <div className={styles.pavilionWrap}>
    <img
      ref={pavilionRef}
      className={styles.pavilion}
      src={imageSrc}
      width={1280}
      height={823}
      alt={imageSrc === tengwangPavilion ? "滕王阁建筑立面" : "用户自定义的文境主图"}
      onLoad={() => setImageReady(true)}
      onError={() => setImageError("主图加载失败，已保留文字内容。")}
    />
  </div>
  {!canvasUnavailable && imageReady && (
    <CurtainCanvas
      buildingRef={pavilionRef}
      text={curtainText || TENGWANG_GE_XU_TEXT}
      settings={settings}
      resetVersion={resetVersion}
      reducedMotion={Boolean(reduceMotion)}
      onUnavailable={handleCanvasUnavailable}
    />
  )}
  <header className={styles.titleBlock}>
    <p>/ 王勃</p>
    <h1>滕王<br />阁序</h1>
  </header>
  <p className={styles.caption}>《滕王阁序》作于唐上元二年，写洪州胜景、宾主盛会与人生际遇。</p>
  <p className={styles.srOnly}>{TENGWANG_GE_XU_TEXT}</p>
  {(imageError || canvasUnavailable) && <p role="status" className={styles.status}>{imageError || "当前浏览器仅展示静态文境。"}</p>}
</section>
```

Pass `soundEnabled` inside `settings`; do not create audio in this component.

- [ ] **Step 3: Implement the accessible settings dialog**

Add one 44px icon button with `aria-label="配置文境"`, `aria-expanded`, and `aria-controls="tengwang-settings"`. When opened:

- remember `document.activeElement`;
- set `document.body.style.overflow = "hidden"`;
- focus the close button;
- trap Tab and Shift+Tab within enabled buttons, inputs, and textarea;
- close on Escape and backdrop click;
- restore the prior body overflow and trigger focus on close/unmount.

Render `<aside id="tengwang-settings" role="dialog" aria-modal="true" aria-labelledby="tengwang-settings-title">` with:

- file input `accept="image/png,image/jpeg,image/webp"`;
- textarea `maxLength={3000}`;
- ranges `20..110`, `18..56`, and `86..99` with linked `<output>` values;
- a mute toggle whose accessible name changes between `开启珠帘声音` and `关闭珠帘声音`, disabled with `当前浏览器不支持声音` when `audioSupported` is false;
- `重置珠帘` that only increments `resetVersion`;
- `恢复默认` that resets text, image, settings, errors, input value, and increments `resetVersion`.

When `canvasUnavailable` is true, keep image upload and static semantic content available but hide the three physics ranges, sound toggle, and `重置珠帘`; `恢复默认` remains available.

- [ ] **Step 4: Add the scoped desktop/tablet/mobile CSS**

Create `TengwangExperience.module.css` with these stable layout rules:

```css
.experience {
  position: relative;
  isolation: isolate;
  min-height: clamp(620px, calc(100svh - 68px), 860px);
  overflow: hidden;
  color: var(--color-ink);
  background: var(--color-canvas);
}

.pavilionWrap { position: absolute; z-index: 2; top: 1.5rem; left: 50%; width: min(700px, 62vw); transform: translateX(-50%); }
.pavilion { display: block; width: 100%; height: auto; filter: drop-shadow(28px 32px 24px rgba(36, 36, 33, 0.18)); }
.settingsButton { position: absolute; z-index: 8; top: 1.25rem; right: 1.25rem; width: 44px; height: 44px; }
.settingsPanel { position: absolute; z-index: 20; top: 4.75rem; right: 1.25rem; width: min(320px, calc(100% - 2.5rem)); max-height: calc(100% - 6rem); overflow-y: auto; }
.paperNoise { position: absolute; inset: 0; z-index: 0; pointer-events: none; opacity: 0.12; background-image: radial-gradient(circle, rgba(36, 36, 33, 0.48) 0 0.45px, transparent 0.6px); background-size: 11px 13px; }
.curtainCanvas { position: absolute; inset: 0; z-index: 3; width: 100%; height: 100%; touch-action: pan-y; }
.titleBlock { position: absolute; z-index: 5; left: clamp(1.5rem, 6vw, 6.5rem); bottom: clamp(2rem, 7vh, 5.5rem); }
.titleBlock h1 { margin: 0; font-family: "Noto Serif SC", "Songti SC", serif; font-size: clamp(3.75rem, 6vw, 5.75rem); line-height: 1.12; letter-spacing: 0; }
.caption { position: absolute; z-index: 5; right: clamp(1.5rem, 7vw, 7rem); bottom: clamp(2.5rem, 9vh, 6.5rem); width: min(17rem, 24vw); color: var(--color-muted); font-size: 0.75rem; line-height: 1.7; }
.backdrop { position: absolute; inset: 0; z-index: 15; border: 0; background: rgba(36, 36, 33, 0.22); }
.settingsPanel { border: 1px solid var(--color-line); border-radius: 8px; padding: 1rem; background: rgba(251, 249, 243, 0.96); box-shadow: 0 18px 44px rgba(36, 36, 33, 0.16); }
.setting { display: grid; gap: 0.5rem; margin-top: 1rem; }
.setting label { display: flex; min-height: 1.5rem; align-items: center; justify-content: space-between; gap: 1rem; color: var(--color-muted); font-size: 0.75rem; }
.iconButton { display: grid; min-width: 44px; min-height: 44px; place-items: center; border: 1px solid var(--color-line); border-radius: 4px; color: var(--color-ink); background: var(--color-surface); }
.iconButton:focus-visible, .settingsPanel button:focus-visible, .settingsPanel input:focus-visible, .settingsPanel textarea:focus-visible { outline: 2px solid var(--color-citation); outline-offset: 2px; }
.status { position: absolute; z-index: 6; left: 50%; bottom: 1rem; transform: translateX(-50%); color: var(--color-citation); font-size: 0.75rem; }
.srOnly { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

@media (min-width: 721px) and (max-width: 1023px) {
  .experience { min-height: clamp(700px, calc(100svh - 68px), 900px); }
  .pavilionWrap { width: min(650px, 82vw); }
}

@media (max-width: 720px) {
  .experience { min-height: max(720px, calc(100svh - 68px)); }
  .pavilionWrap { top: 3.25rem; width: min(620px, 96vw); }
  .titleBlock { left: 1.25rem; bottom: 1.75rem; }
  .titleBlock h1 { font-size: clamp(3rem, 15vw, 4.25rem); }
  .caption { display: none; }
  .settingsPanel { position: fixed; inset: auto 0 0; width: 100%; max-height: min(78dvh, 620px); padding-bottom: max(1rem, env(safe-area-inset-bottom)); }
}

@media (prefers-reduced-motion: reduce) {
  .experience *, .experience *::before, .experience *::after { scroll-behavior: auto !important; transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
}
```

Use `border-radius: 8px` or less, no nested cards, no gradients as primary decoration, and no custom hidden cursor.

- [ ] **Step 5: Run the wiring test to measure remaining work**

Run `node frontend/tests/tengwangExperienceWiring.test.cjs`.

Expected: it now fails only because `CurtainCanvas.tsx`, the route, and the `/content` link do not exist.

- [ ] **Step 6: Commit only the experience shell**

```powershell
git add -- frontend/components/content/tengwang/TengwangExperience.tsx frontend/components/content/tengwang/TengwangExperience.module.css frontend/lib/tengwangText.ts
git commit -m "feat: add tengwang experience shell"
```

## Task 5: Implement Canvas rendering, lifecycle, pointer input, and audio

**Files:**

- Create: `frontend/components/content/tengwang/CurtainCanvas.tsx`
- Modify: `frontend/components/content/tengwang/TengwangExperience.module.css`

- [ ] **Step 1: Define the Canvas prop and runtime contracts**

Start `CurtainCanvas.tsx` with:

```tsx
"use client";

import { type RefObject, useEffect, useRef } from "react";
import {
  buildCurtain,
  constrainCurtain,
  injectPointerImpulse,
  integrateCurtain,
  isCurtainSettled,
  type CurtainChain,
} from "@/lib/curtainPhysics";
import styles from "./TengwangExperience.module.css";

type CurtainSettings = { strength: number; reach: number; inertia: number; soundEnabled: boolean };
type CurtainCanvasProps = {
  buildingRef: RefObject<HTMLImageElement>;
  text: string;
  settings: CurtainSettings;
  resetVersion: number;
  reducedMotion: boolean;
  onUnavailable: () => void;
};
```

Store Canvas context, chains, current/previous pointer, observers, animation ID, visibility flags, stable-frame count, AudioContext, output gain, and per-chain strike timestamps inside the effect or refs. No runtime object may be module-global.

Return the semantic Canvas surface directly:

```tsx
return (
  <canvas
    ref={canvasRef}
    className={styles.curtainCanvas}
    data-curtain-canvas
    aria-hidden="true"
  />
);
```

- [ ] **Step 2: Implement resize/build and the demand-driven frame loop**

In one effect:

- get `canvas.getContext("2d", { alpha: true, desynchronized: true })`; call `onUnavailable()` and return if null;
- calculate stage-relative building bounds from the image and canvas parent rectangles;
- cap DPR at 2 and call `ctx.setTransform(dpr, 0, 0, dpr, 0, 0)`;
- call `buildCurtain` with normalized text and those bounds;
- draw immediately after every build;
- use `ResizeObserver` on both parent and image;
- use `IntersectionObserver` and `document.visibilitychange` to pause offscreen/hidden work;
- request frames only after pointer movement, resize, reset, or while the chain is not settled for 10 consecutive frames.

Each active frame performs:

```ts
integrateCurtain(chains, settings.inertia / 100, 0.18);
constrainCurtain(chains, 6);
drawCurtain(ctx, chains, width, height);
stableFrames = isCurtainSettled(chains, reducedMotion ? 0.08 : 0.03) ? stableFrames + 1 : 0;
if (stableFrames < 10 && pageVisible && canvasVisible) animationId = requestAnimationFrame(frame);
```

Port the supplied ribbon drawing without global state: calculate left/right ribbon edges, draw four restrained brown/cinnabar tones, then anchors and glyphs using `500 10.5px "Noto Serif SC", "Songti SC", serif` (`9.5px` below 720px).

- [ ] **Step 3: Implement pointer input without blocking mobile scrolling**

Use `pointerenter`, `pointermove`, `pointerleave`, and `pointercancel`. Convert client coordinates to Canvas CSS pixels. Call `injectPointerImpulse` with `reach` and `strength / 100`, schedule a frame, and retain the returned per-chain impacts for audio.

Set `.curtainCanvas { touch-action: pan-y; }`. Do not call `preventDefault()` for vertical touch movement. On `pointercancel`, clear the active pointer so browser scrolling wins.

- [ ] **Step 4: Add opt-in collision audio**

Create AudioContext only when all conditions are true: `settings.soundEnabled`, a pointer event occurred inside the Canvas, and Web Audio exists. Use the original short oscillator pair, compressor, 110ms delay, stereo panner when available, maximum 8 voices, 55ms per-chain throttle, and 22ms global throttle.

When sound becomes false, call `audioContext.suspend()`. On unmount, clear voice timers, disconnect nodes, and call `audioContext.close()`. Catch rejected resume/suspend/close promises without affecting drawing.

- [ ] **Step 5: Implement exhaustive cleanup**

The effect cleanup must contain all of the following:

```ts
cancelAnimationFrame(animationId);
resizeObserver.disconnect();
intersectionObserver.disconnect();
document.removeEventListener("visibilitychange", handleVisibilityChange);
canvas.removeEventListener("pointerenter", handlePointerEnter);
canvas.removeEventListener("pointermove", handlePointerMove);
canvas.removeEventListener("pointerleave", handlePointerLeave);
canvas.removeEventListener("pointercancel", handlePointerLeave);
void audioContext?.close().catch(() => {});
```

Ensure Strict Mode remount creates a fresh local runtime and cannot reuse the prior animation ID or AudioContext.

- [ ] **Step 6: Run focused tests and the production type/build check**

Run:

```powershell
node frontend/tests/curtainPhysics.test.cjs
node frontend/tests/tengwangExperienceWiring.test.cjs
npm --prefix frontend run build
```

Expected: physics passes; wiring fails only on the missing route/content entry; build succeeds for the new components even though they are not routed yet.

- [ ] **Step 7: Commit only Canvas paths**

```powershell
git add -- frontend/components/content/tengwang/CurtainCanvas.tsx frontend/components/content/tengwang/TengwangExperience.module.css
git commit -m "feat: add interactive curtain canvas"
```

## Task 6: Add the route and content-gallery entry

**Files:**

- Create: `frontend/app/content/tengwang-ge-xu/page.tsx`
- Modify: `frontend/app/content/page.tsx`

- [ ] **Step 1: Add the server route**

Create `frontend/app/content/tengwang-ge-xu/page.tsx`:

```tsx
import type { Metadata } from "next";
import TengwangExperience from "@/components/content/tengwang/TengwangExperience";

export const metadata: Metadata = {
  title: "滕王阁序互动文境 · 悟典",
  description: "拨动竖排文字珠帘，在滕王阁建筑与王勃名篇之间感受经典。",
};

export default function TengwangGeXuPage() {
  return (
    <div className="-mx-4 -my-8 sm:-mx-6 lg:-mx-8">
      <TengwangExperience />
    </div>
  );
}
```

- [ ] **Step 2: Add an independent link beside the existing content tabs**

In `frontend/app/content/page.tsx`:

- import `Link` from `next/link` and `Landmark` from `lucide-react`;
- keep `type Tab = "quotes" | "theater" | "comics"` unchanged;
- after the existing `tabs.map(...)`, render:

```tsx
<Link
  href="/content/tengwang-ge-xu"
  className="flex min-h-11 items-center gap-1.5 rounded-[4px] px-4 py-2 text-sm font-medium text-[var(--color-action)] transition-colors hover:bg-white"
>
  <Landmark size={16} />
  <span className="hidden sm:inline">文境</span>
</Link>
```

Do not change `loadData`, the fallback `catch`, active tab behavior, or selected content state.

- [ ] **Step 3: Run the focused and full source tests**

Run:

```powershell
node frontend/tests/tengwangExperienceWiring.test.cjs
npm --prefix frontend test
```

Expected: `tengwangExperienceWiring tests passed` followed by all existing frontend tests passing.

- [ ] **Step 4: Run production and static-export-compatible builds**

Run:

```powershell
npm --prefix frontend run build:clean
$env:SITES_BUILD='true'
npm --prefix frontend run build:clean
Remove-Item Env:SITES_BUILD
```

Expected: both builds succeed and include `/content/tengwang-ge-xu` in generated routes.

- [ ] **Step 5: Commit only integration paths**

```powershell
git add -- frontend/app/content/tengwang-ge-xu/page.tsx frontend/app/content/page.tsx
git commit -m "feat: integrate tengwang interactive content"
```

## Task 7: Browser QA, regression fixes, and final verification

**Files:**

- Modify only files implicated by an observed defect.
- Test: `frontend/tests/curtainPhysics.test.cjs`
- Test: `frontend/tests/tengwangExperienceWiring.test.cjs`

- [ ] **Step 1: Start the development server on an available port**

Run `npm --prefix frontend run dev:clean`. Record the actual local URL printed by the port guard and keep the process running until all browser checks finish.

Expected: Next.js reports ready without compilation errors.

- [ ] **Step 2: Verify the content entry and desktop experience at 1440x900**

In the browser:

- open `/content`, activate the “文境” link, and confirm it reaches `/content/tengwang-ge-xu`;
- verify the pavilion and Canvas contain non-background pixels;
- sweep the pointer across at least three curtain columns and compare before/after screenshots to confirm displacement;
- wait for the chain to settle and confirm animation work stops;
- open settings and verify initial focus, Tab loop, Escape, focus return, and no overlap;
- change text and all three sliders, toggle sound on/off, run both reset actions;
- upload the supplied valid PNG, then try a text file renamed with an image extension and confirm the valid image remains.

- [ ] **Step 3: Verify tablet and mobile layouts**

At 768x1024 and 390x844:

- verify the pavilion, title, curtain, settings trigger, and footer do not overlap;
- verify no horizontal overflow with `document.documentElement.scrollWidth === document.documentElement.clientWidth`;
- confirm the settings surface becomes a bottom sheet at 390px and stays within `min(78dvh, 620px)`;
- drag horizontally across the curtain, then swipe vertically and confirm the page scrolls;
- verify the longest button/input labels remain inside their controls.

- [ ] **Step 4: Verify reduced motion, lifecycle, and fallback behavior**

- emulate `prefers-reduced-motion: reduce`; confirm there is no decorative entrance animation and pointer interaction still settles quickly;
- navigate repeatedly between `/content` and the experience while watching console errors and listener/animation behavior;
- before navigation, inject an init script that returns `null` from `HTMLCanvasElement.prototype.getContext` only when the element has `data-curtain-canvas`; then open the route and verify the static pavilion, title, and `当前浏览器仅展示静态文境。` status remain visible;
- turn sound on, navigate away, and confirm no sound continues and no AudioContext warning appears.

- [ ] **Step 5: Fix each observed defect test-first**

For each defect, add the smallest failing assertion to one of the two focused tests before changing implementation. Run the focused test to see it fail, apply the smallest patch, then rerun it to pass. Do not refactor unrelated UI.

- [ ] **Step 6: Run the final verification suite**

Run:

```powershell
node frontend/tests/curtainPhysics.test.cjs
node frontend/tests/tengwangExperienceWiring.test.cjs
npm --prefix frontend test
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
git diff --check
```

Expected: every command exits 0. Inspect `git status --short` and verify only known user changes or intentional feature changes remain.

- [ ] **Step 7: Commit only regression-fix paths if QA required changes**

```powershell
git add -- frontend/lib/curtainPhysics.ts frontend/lib/tengwangText.ts frontend/lib/visualAssets.ts frontend/tests/curtainPhysics.test.cjs frontend/tests/tengwangExperienceWiring.test.cjs frontend/tests/visualAssetsWiring.test.cjs frontend/components/content/tengwang/CurtainCanvas.tsx frontend/components/content/tengwang/TengwangExperience.tsx frontend/components/content/tengwang/TengwangExperience.module.css frontend/app/content/tengwang-ge-xu/page.tsx frontend/app/content/page.tsx frontend/package.json
git commit -m "fix: harden tengwang interactive experience"
```

Skip this commit when QA required no code changes. Never stage unrelated pre-existing worktree changes.

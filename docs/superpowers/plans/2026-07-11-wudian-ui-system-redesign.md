# Wudian UI System Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the global shell, home page, and sage chat flow into a restrained, source-first Chinese classics product.

**Architecture:** Keep the existing Next.js routes, data APIs, and generated cultural assets. Introduce semantic global design tokens and reorganize existing page components around a clear editorial home hierarchy and a responsive three-column sage workspace.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, Lucide React, Node source-wiring tests.

---

### Task 1: Lock the intended visual structure

**Files:**
- Create: `frontend/tests/uiRedesignWiring.test.cjs`
- Modify: `frontend/package.json`

- [ ] Write assertions for the new navigation labels, home hero markers, sage workspace markers, semantic design tokens, and reduced-motion support.
- [ ] Run `node frontend/tests/uiRedesignWiring.test.cjs` and verify it fails because the new markers and structure do not exist.
- [ ] Add the test to the frontend test script.

### Task 2: Establish the global shell

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/components/Navbar.tsx`

- [ ] Add semantic color, surface, typography, border, focus, and motion tokens while preserving existing reader-specific styles.
- [ ] Replace the crowded desktop navigation with five primary destinations and a restrained overflow menu.
- [ ] Remove the global background image and oversized four-column footer; use a quiet paper surface and compact footer.
- [ ] Run `node frontend/tests/uiRedesignWiring.test.cjs` and confirm the shell assertions pass.

### Task 3: Recompose the home page

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] Preserve all API loading and quiz behavior while replacing the centered hero with an asymmetric editorial composition.
- [ ] Use the existing Confucius scene asset as a real first-viewport cultural signal with a readable overlay and stable aspect ratio.
- [ ] Reorganize quote, challenge, book library, and progress into clear full-width bands with restrained individual item cards.
- [ ] Run `node frontend/tests/uiRedesignWiring.test.cjs` and `node frontend/tests/homePublicAccess.test.cjs`.

### Task 4: Build the sage workspace

**Files:**
- Modify: `frontend/app/sage-chat/page.tsx`
- Modify: `frontend/components/sage/SageChat.tsx`
- Modify: `frontend/components/sage/CitationSidebar.tsx`

- [ ] Preserve streaming, local fallback, citation normalization, and prefilled-question behavior.
- [ ] Replace the selection-card grid with a featured sage composition and compact switcher.
- [ ] Convert the selected state into responsive left navigation, central conversation, and right evidence rail.
- [ ] Keep the mobile input reachable and expose evidence as a compact expandable section.
- [ ] Run `node frontend/tests/uiRedesignWiring.test.cjs` and `node frontend/tests/sageChatWiring.test.cjs`.

### Task 5: Verify the product surface

**Files:**
- Modify only files required by verification failures.

- [ ] Run `npm --prefix frontend test` and confirm zero failures.
- [ ] Run `npm --prefix frontend run build` and confirm a successful production build.
- [ ] Start the frontend development server and inspect `/` and `/sage-chat` at desktop and mobile widths.
- [ ] Confirm no horizontal overflow, text overlap, inaccessible controls, or blank primary regions.


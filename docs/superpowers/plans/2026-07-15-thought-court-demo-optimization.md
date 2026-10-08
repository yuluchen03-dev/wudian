# Thought Court Demo Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `/demo` with a usable four-act thought court that differentiates 悟典 through evidence, multi-perspective participation, and a lightweight 3D stage.

**Architecture:** Reuse the existing `thoughtCourt*.ts` domain modules and the current debate API adapter. Add an isolated `components/thought-court` React feature: its hook owns effects and state transitions, focused components own one act each, and a CSS module provides the responsive 2.5D stage and motion fallbacks.

**Tech Stack:** Next.js 14, React 18, TypeScript 5, Framer Motion 11, Lucide React, CSS Modules, existing API client and Node source tests.

---

## Current Baseline

Already implemented and covered by focused tests:

- `frontend/lib/thoughtCourtTypes.ts`
- `frontend/lib/thoughtCourtState.ts`
- `frontend/lib/thoughtCourtCases.ts`
- `frontend/lib/thoughtCourtVerdict.ts`
- `frontend/lib/thoughtCourtSession.ts`
- `frontend/tests/thoughtCourtState.test.cjs`
- `frontend/tests/thoughtCourtCases.test.cjs`
- `frontend/tests/thoughtCourtVerdict.test.cjs`
- `frontend/tests/thoughtCourtSession.test.cjs`

Do not change quote text, source, or sage attribution while implementing UI. Do not add a 3D engine or alter backend contracts.

## File Map

Create:

- `frontend/components/thought-court/useThoughtCourt.ts` - single side-effect boundary for curated and live sessions.
- `frontend/components/thought-court/ThoughtCourtExperience.tsx` - feature composition and four-act routing.
- `frontend/components/thought-court/CourtStageChrome.tsx` - progress, motion controls, truthful mode status, and error recovery.
- `frontend/components/thought-court/CaseIntake.tsx` - cases, free input, and open-court command.
- `frontend/components/thought-court/EvidenceDock.tsx` - inspectable and selectable evidence.
- `frontend/components/thought-court/SageTribunal.tsx` - three seats, streamed viewpoints, and debate actions.
- `frontend/components/thought-court/VerdictScroll.tsx` - weighted verdict and non-blocking seal.
- `frontend/components/thought-court/ThoughtCourt.module.css` - desktop/mobile stage and 2.5D motion.
- `frontend/tests/thoughtCourtWiring.test.cjs` - route and feature contract checks.

Modify:

- `frontend/app/demo/page.tsx` - render only `ThoughtCourtExperience`.
- `frontend/package.json` - add five existing/new thought-court tests to `test`.
- `frontend/tests/demoHackathonWiring.test.cjs` - replace presenter-runbook assertions with court assertions.
- `README.md` and `docs/hackathon/final-delivery-checklist.md` - update the judging flow and QA checklist.

### Task 1: Add a failing UI wiring test

**Files:** Create `frontend/tests/thoughtCourtWiring.test.cjs`.

- [ ] Write source assertions for `ThoughtCourtExperience`, all five act components, `ThoughtCourt.module.css`, `思想审判场`, `击鼓开审`, `加入本案`, `已核验`, `暂未应答`, `请其互问`, `落判`, `演示稳定层：已加载经校验案件`, `aria-live`, `prefers-reduced-motion`, `perspective`, and all three existing sage portrait paths.
- [ ] Run `node frontend/tests/thoughtCourtWiring.test.cjs`; confirm it fails because the component directory does not exist.
- [ ] Keep this test text-based only; logic remains covered by the existing pure TypeScript tests.

### Task 2: Implement court state orchestration and stage shell

**Files:** Create `useThoughtCourt.ts`, `ThoughtCourtExperience.tsx`, `CourtStageChrome.tsx`, and `ThoughtCourt.module.css`.

- [ ] Implement a hook that calls `useReducer(transitionCourt, undefined, createCourtState)` and exposes `state`, `courtCase`, `evidence`, `speeches`, `report`, `openCourt`, `toggleEvidence`, `beginDebate`, `setWeights`, `buildVerdict`, `complete`, `retry`, and `useStableDemo`.
- [ ] In `openCourt`, select curated data with `getCuratedCourtCase`; dispatch `SUBMIT_CASE`, then `RETRIEVAL_SUCCEEDED` with curated evidence IDs and `verified`. For free input call `prepareLiveCourt(question, sages, createApiCourtGateway(api), dispatch)` and dispatch `REMOTE_FAILED` without clearing the question on rejection.
- [ ] Render a focusable, labelled stage with phases `问`, `证`, `辩`, `判`; add icon buttons for sound and full/reduced motion, both with `aria-label` and tooltips. The sound control remains muted by default and must not play ambient audio.
- [ ] Render recovery inside the active stage. `重试` invokes the stored operation; `切换演示稳定层` is visible only where a matching curated case is available. Its status text must be exactly `演示稳定层：已加载经校验案件`.
- [ ] Implement CSS variables for ink, bone, cinnabar, jade and stone; use `.stage { perspective: 1400px; }`, `transform-style: preserve-3d`, a fixed stage grid, reduced-motion media overrides, and a `max-width: 767px` vertical layout.
- [ ] Run `node frontend/tests/thoughtCourtWiring.test.cjs`; it should still fail only for the unimplemented acts.

### Task 3: Implement intake and evidence selection

**Files:** Create `CaseIntake.tsx` and `EvidenceDock.tsx`; modify `ThoughtCourtExperience.tsx` and CSS.

- [ ] Render the exact three curated questions from `CURATED_COURT_CASES`, a labelled textarea for a free question, and a `Gavel` button named `击鼓开审`. Disable empty submissions and network-busy submission.
- [ ] In `EvidenceDock`, display original text, source, interpretation, boundary, and the truthful status labels `已核验`, `依据不完整`, or `未找到足够可靠的经典依据`.
- [ ] Give each evidence item a disclosure button with `aria-expanded`, an `加入本案`/`移出本案` button, and optional desktop drag/drop that invokes the same toggle function. Keep controls available for keyboard users and in reduced motion.
- [ ] Add the perspective entrance: the selected dossier translates from `translateZ(0)` to `translateZ(44px)` while the textual evidence body remains stationary.
- [ ] Run the wiring test and the four existing pure tests; update only missing UI assertions and confirm all pass.

### Task 4: Implement three-seat tribunal and live actions

**Files:** Create `SageTribunal.tsx`; modify hook, experience, and CSS.

- [ ] Build three fixed seats for `confucius`, `mencius`, and `laozi`, using `/agens/sages/portraits/<id>.png` from `mockSages` as the image source. The active speaker gets `translateZ(80px)` and a short opacity/light transition; inactive speakers stay readable.
- [ ] Render each streamed speech in a fixed-height internal scroll area with `aria-live="polite"`. A failed seat shows `暂未应答` and retains its position.
- [ ] Add a labelled follow-up input, `追问`, stance action `我更认同`, and two-select `请其互问`. Actions set local busy feedback immediately, retain previous content, and call the hook's API-backed handlers.
- [ ] On curated cases, reveal the stored three speeches in order, then transition to `weighting`. For live cases, surface the prepared first round, run the second round with `runSecondRound`, and request the report with `loadReport`.
- [ ] Draw support/refute/reframe relations with solid, dashed, and doubled CSS/SVG lines plus text labels. Trigger at most one 220ms shockwave when a new clash appears; suppress it in reduced/degraded mode.
- [ ] Run `node frontend/tests/thoughtCourtSession.test.cjs`, the wiring test, and `npm --prefix frontend run build`.

### Task 5: Implement verdict, 3D seal, accessibility, and responsive completion

**Files:** Create `VerdictScroll.tsx`; modify hook, experience, CSS, and wiring test.

- [ ] Derive `buildVerdict(report, weights)` with `useMemo`. Render `核心矛盾`, `他们的共识`, `根本分歧`, `今日行动`, `保留问题`, and immutable evidence sources.
- [ ] Render three labelled range controls: `坚持自我`, `改善关系`, and `主动改变`. Dispatch normalized values through `SET_WEIGHTS`; their only visual/data effect is action ordering and emphasis.
- [ ] Render `落判`, `重新调权`, and `新开一案`. Full motion applies a maximum 900ms `verdictSeal` transform; reduced motion immediately displays the sealed state. Do not disable either reset control during the animation.
- [ ] At 390px, replace the seat ring with a horizontal seat selector, make evidence a `max-height: 70dvh` bottom sheet, reserve `padding-bottom: max(12px, env(safe-area-inset-bottom))` for the action bar, and set 44px control minima.
- [ ] Add visible focus styles, a skip link, sentence-level live updates, no horizontal overflow, and fixed reading surfaces for all variable-length content.
- [ ] Run the wiring and pure tests plus `npm --prefix frontend run build`; resolve every failure before integration.

### Task 6: Replace the old route contract and integrate tests/docs

**Files:** Modify `frontend/app/demo/page.tsx`, `frontend/tests/demoHackathonWiring.test.cjs`, `frontend/package.json`, `README.md`, and `docs/hackathon/final-delivery-checklist.md`.

- [ ] Replace the old page body with:

```tsx
import ThoughtCourtExperience from "@/components/thought-court/ThoughtCourtExperience";

export default function DemoPage() {
  return <ThoughtCourtExperience />;
}
```

- [ ] Change the old demo test to assert `ThoughtCourtExperience`, `思想审判场`, four acts, and the stable-layer label; remove requirements for the old presenter runbook, `/sage-chat` redirect, video fallback, and `/roundtable?demo=complete`.
- [ ] Append `thoughtCourtState.test.cjs`, `thoughtCourtCases.test.cjs`, `thoughtCourtVerdict.test.cjs`, `thoughtCourtSession.test.cjs`, and `thoughtCourtWiring.test.cjs` to the existing package `test` command without removing other test commands.
- [ ] Update the README route to `/demo -> 问题落案 -> 经典举证 -> 百家交锋 -> 思想判牒 -> /about`, explain the three cases and truthful stable layer, and update the delivery checklist with 1440px/390px, reduced-motion, and failure-recovery checks.
- [ ] Run `npm --prefix frontend test`, `npm --prefix frontend run stage-check`, `npm --prefix frontend run build:clean`, and `git diff --check`.

### Task 7: Browser QA and final regression fixes

**Files:** Modify only files implicated by an observed defect; test `frontend/tests/thoughtCourtWiring.test.cjs`.

- [ ] Start the backend at `127.0.0.1:8000` and frontend with `npm --prefix frontend run dev:clean`.
- [ ] At 1440px, complete the recognition case through all four acts. Verify nonblank stage, all portraits, readable evidence, no layout shifts, working evidence selection, weighted action reordering, and accessible primary controls.
- [ ] At 390px, repeat the flow. Verify no horizontal scroll, visible bottom actions, wrapping Chinese text, usable sage selector, and no overlap.
- [ ] Verify reduced motion and a live-question API failure: retained question and stage, explicit retry, and truthful stable fallback only for a matching curated case.
- [ ] For each defect, add the smallest failing assertion first, then patch and rerun its targeted test.
- [ ] Run `npm --prefix frontend test`, `npm --prefix frontend run stage-check`, `npm --prefix frontend run build:clean`, `Push-Location backend; python -m pytest tests -q; Pop-Location`, and `git diff --check`.

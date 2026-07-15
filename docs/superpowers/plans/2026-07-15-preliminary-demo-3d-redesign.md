# Preliminary Demo 3D Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current 2.5D preliminary HTML package with an offline, competition-ready Three.js thought court featuring three procedural sage figures, a seven-state product flow, a trust epilogue, and a single enterprise-pilot CTA.

**Architecture:** Keep `index.html` as the only entry point and split content data, DOM orchestration, 3D rendering, and styles into focused local files. The DOM state machine remains authoritative; Three.js subscribes to state changes and may degrade to portrait-based 2.5D without blocking content or controls.

**Tech Stack:** HTML5, CSS, JavaScript ES modules, vendored Three.js, Node.js source validation, PowerShell ZIP packaging, in-app browser QA.

---

## File Map

- Modify: `报名材料/悟典-初赛Demo/index.html` - semantic shell and seven-state DOM surfaces.
- Create: `报名材料/悟典-初赛Demo/css/app.css` - stage, overlay, responsive, reduced-motion, and fallback styles.
- Create: `报名材料/悟典-初赛Demo/js/court-data.js` - immutable curated cases, trust chain, and pilot data.
- Create: `报名材料/悟典-初赛Demo/js/court-scene.js` - Three.js renderer, procedural sages, books, links, camera cues, and degradation.
- Create: `报名材料/悟典-初赛Demo/js/app.js` - deterministic state machine and accessible DOM interaction.
- Create: `报名材料/悟典-初赛Demo/js/three.module.min.js` - local official Three.js runtime.
- Create: `报名材料/悟典-初赛Demo/js/THREE-LICENSE.txt` - Three.js MIT license.
- Retain: `报名材料/悟典-初赛Demo/assets/*.png` - portrait fallback assets.
- Create: `报名材料/validate-preliminary-demo.cjs` - offline, structure, content, asset, and package validation.
- Modify: `报名材料/悟典-思想审判场-初赛Demo.zip` - final upload package.

### Task 1: Establish the offline package contract

**Files:**
- Create: `报名材料/validate-preliminary-demo.cjs`
- Test: `报名材料/悟典-初赛Demo/**`

- [ ] Write a validator that asserts the entry HTML, local Three.js runtime, three portrait assets, seven state identifiers, trust chain, enterprise pilot, privacy boundary, reduced-motion CSS, and no `http://` or `https://` runtime references.
- [ ] Run `node 报名材料/validate-preliminary-demo.cjs` and verify it fails because the split JavaScript and CSS files do not exist.
- [ ] Keep the validator independent of a browser so it can run before every ZIP build.

### Task 2: Split curated content and DOM state

**Files:**
- Modify: `报名材料/悟典-初赛Demo/index.html`
- Create: `报名材料/悟典-初赛Demo/js/court-data.js`
- Create: `报名材料/悟典-初赛Demo/js/app.js`
- Create: `报名材料/悟典-初赛Demo/css/app.css`

- [ ] Move all three curated cases into `court-data.js` as immutable objects with conflicts, evidence, speeches, relations, verdict sections, and weighted actions.
- [ ] Implement `STATES = ["intake", "opening", "evidence", "debate", "weighting", "verdict", "epilogue"]` and a guarded `go(nextState)` transition function in `app.js`.
- [ ] Render case selection, evidence toggle, sage focus, stance labels, normalized sliders, verdict seal, trust chain, pilot metrics, privacy boundary, and one `申请企业青年员工试点` command.
- [ ] Keep `index.html` semantic and free of embedded case data, inline CSS, and inline JavaScript.
- [ ] Run the validator; expect it still to fail only on the missing Three.js runtime and scene module.

### Task 3: Add the local Three.js runtime and procedural court

**Files:**
- Create: `报名材料/悟典-初赛Demo/js/three.module.min.js`
- Create: `报名材料/悟典-初赛Demo/js/THREE-LICENSE.txt`
- Create: `报名材料/悟典-初赛Demo/js/court-scene.js`

- [ ] Vendor the official npm Three.js ES module and MIT license locally; do not load a CDN.
- [ ] Build one full-bleed WebGL canvas with a central dossier, triangular sage seating, three procedural low-poly busts, book evidence, relation curves, floor marks, key/fill lights, and capped device pixel ratio.
- [ ] Export `createCourtScene(canvas, options)` returning `setState`, `setActiveSage`, `setWeights`, `resize`, and `destroy`.
- [ ] Map each state to a deterministic camera and object cue; reserve continuous motion for subtle breathing only.
- [ ] Detect WebGL initialization failure and sustained low performance; add `.is-2d-fallback` without blocking the DOM state machine.
- [ ] Run the validator and verify it passes.

### Task 4: Prove the weight and fallback behavior

**Files:**
- Modify: `报名材料/validate-preliminary-demo.cjs`
- Modify: `报名材料/悟典-初赛Demo/js/app.js`
- Modify: `报名材料/悟典-初赛Demo/js/court-scene.js`

- [ ] Extend the validator to assert all weight keys, immutable evidence wording, WebGL fallback marker, portrait fallback, and `prefers-reduced-motion` handling.
- [ ] Run the validator and verify the new assertions fail before behavior is added.
- [ ] Normalize the three sliders to a visible 100% total and order actions by dominant value without changing evidence content.
- [ ] Make reduced motion skip camera travel, shake, particles, and seal scaling; make fallback render the three local portraits.
- [ ] Run the validator and verify all checks pass.

### Task 5: Package and perform visual QA

**Files:**
- Modify as defects require: `报名材料/悟典-初赛Demo/**`
- Modify: `报名材料/悟典-思想审判场-初赛Demo.zip`

- [ ] Serve the folder locally and complete all seven states at 1440px.
- [ ] Confirm the canvas contains non-background pixels, all three sages are framed, books and relation lines are visible, and DOM controls do not overlap the scene.
- [ ] Repeat at 390×844; verify zero horizontal overflow, portrait fallback availability, readable evidence, and safe-area actions.
- [ ] Test reduced motion and forced WebGL fallback; both paths must complete the flow.
- [ ] Add the smallest validator assertion before fixing each discovered defect.
- [ ] Run `node 报名材料/validate-preliminary-demo.cjs` and `git diff --check`.
- [ ] Rebuild `报名材料/悟典-思想审判场-初赛Demo.zip`, expand it to a temporary folder, rerun the validator against the expanded package, and confirm it is below 20 MB.

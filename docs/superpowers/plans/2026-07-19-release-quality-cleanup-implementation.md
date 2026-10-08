# Release Quality and Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make production and demo releases unambiguous, remove known vulnerable/redundant artifacts, enforce CI gates, and prove the real application works on desktop and mobile before launch.

**Architecture:** Treat real full-stack server mode as the only production path and static Mock export as an explicitly named demo artifact. Enforce deterministic lint/test/build/audit/container/browser gates in GitHub Actions, generate submission archives from canonical sources, and delete only files proven to be runtime output or unreferenced duplicates.

**Tech Stack:** Next.js current stable, ESLint flat config, GitHub Actions, Docker Compose, Node.js 22, Python 3.12, Playwright, axe-core, npm audit, pip-audit.

---

## File Structure

- Modify `scripts/build-site.mjs`, `scripts/site-worker.mjs`, `frontend/next.config.js`: explicit demo export and response security headers.
- Create `scripts/validate-production-env.mjs`, `scripts/stage-check.mjs`: cross-platform production and stage gates.
- Modify `frontend/package.json`, `package.json`: distinct production/demo commands, non-interactive lint, all tests, archives, audit, and smoke commands.
- Create `frontend/eslint.config.mjs`: deterministic ESLint configuration.
- Upgrade `frontend/package-lock.json`: secure current framework versions pinned by lock file.
- Create `.github/workflows/release-gate.yml`: clean Linux CI with PostgreSQL and browser testing.
- Create `scripts/audit-redundancy.mjs`, `tests/redundancyAudit.test.mjs`: deterministic tracked-artifact report.
- Create `scripts/package-preliminary-demo.mjs`: canonical demo ZIP generator into ignored `dist/`.
- Modify `.gitignore`, `frontend/.gitignore`: runtime, local, build, and env-example rules.
- Delete tracked runtime debate JSON, `backend/init_log.txt`, obsolete duplicated demo directory/ZIP, and root `pptxgenjs` only after reference gates pass.
- Preserve canonical `报名材料/一问见古今-初赛Demo/` and its required Three.js license/module pair.
- Create `frontend/playwright.config.ts`, `frontend/e2e/fullstack.spec.ts`, `frontend/e2e/accessibility.spec.ts`: desktop/mobile real-stack acceptance.
- Modify `frontend/app/globals.css`, `frontend/app/page.tsx`, `frontend/components/Navbar.tsx`, and audited controls: touch targets, initial visibility, reduced motion, focus, and labels.
- Create `docs/operations/release-checklist.md`, `docs/operations/redundancy-report.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`: release handoff and licensing.

### Task 1: Make Production and Demo Builds Impossible to Confuse

**Files:**
- Create: `scripts/validate-production-env.mjs`
- Create: `scripts/stage-check.mjs`
- Create: `scripts/run-backend-tests.mjs`
- Create: `frontend/scripts/clean-next.mjs`
- Modify: `scripts/build-site.mjs`
- Modify: `frontend/scripts/stage-check.ps1`
- Modify: `frontend/package.json`
- Modify: `package.json`
- Test: `tests/releaseModes.test.mjs`

- [ ] **Step 1: Write failing release-mode tests**

```javascript
// tests/releaseModes.test.mjs
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

test("production validation rejects mock mode", () => {
  const result = spawnSync(process.execPath, ["scripts/validate-production-env.mjs"], {
    cwd: process.cwd(),
    env: { ...process.env, NODE_ENV: "production", NEXT_PUBLIC_API_BASE: "/api", NEXT_PUBLIC_USE_MOCK: "true" },
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /NEXT_PUBLIC_USE_MOCK/);
});

test("production validation accepts same-origin real API", () => {
  const result = spawnSync(process.execPath, ["scripts/validate-production-env.mjs"], {
    cwd: process.cwd(),
    env: { ...process.env, NODE_ENV: "production", NEXT_PUBLIC_API_BASE: "/api", NEXT_PUBLIC_USE_MOCK: "false" },
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
});

test("demo builder is explicitly mock and has a separate output", async () => {
  const source = await import("node:fs/promises").then((fs) => fs.readFile("scripts/build-site.mjs", "utf8"));
  assert.match(source, /NEXT_PUBLIC_USE_MOCK:\s*"true"/);
  assert.match(source, /demo-dist/);
  assert.doesNotMatch(source, /resolve\(root,\s*"dist"\)/);
});

test("default test and build scripts are cross platform", async () => {
  const root = JSON.parse(await import("node:fs/promises").then((fs) => fs.readFile("package.json", "utf8")));
  const frontend = JSON.parse(await import("node:fs/promises").then((fs) => fs.readFile("frontend/package.json", "utf8")));
  for (const script of [root.scripts["backend:test"], frontend.scripts.clean, frontend.scripts["build:clean"], frontend.scripts["stage-check"]]) {
    assert.doesNotMatch(script, /powershell|\.ps1/i);
  }
});
```

- [ ] **Step 2: Run and verify failure**

```bash
node --test tests/releaseModes.test.mjs
```

Expected: FAIL because there is no production validator and the demo writes generic `dist/`.

- [ ] **Step 3: Add exact production validation**

```javascript
// scripts/validate-production-env.mjs
const errors = [];
if (process.env.NODE_ENV !== "production") errors.push("NODE_ENV must be production");
if (process.env.NEXT_PUBLIC_USE_MOCK !== "false") errors.push("NEXT_PUBLIC_USE_MOCK must be false");
if (process.env.NEXT_PUBLIC_API_BASE !== "/api") errors.push("NEXT_PUBLIC_API_BASE must be /api for same-origin production");
if (process.env.NEXT_PUBLIC_API_URL) errors.push("NEXT_PUBLIC_API_URL is obsolete; use NEXT_PUBLIC_API_BASE");
if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log("production frontend environment is valid");
```

Install cross-platform environment assignment once at the root:

```bash
npm install --save-dev cross-env
```

- [ ] **Step 4: Separate commands and output directories**

Rename static scripts to `demo:build`, `demo:stage-check`, and `demo:package`; change `scripts/build-site.mjs` output from `dist/` to `demo-dist/`. Production scripts run validation before `next build` and never set Mock mode.

```json
{
  "scripts": {
    "prod:validate": "cross-env NODE_ENV=production NEXT_PUBLIC_API_BASE=/api NEXT_PUBLIC_USE_MOCK=false node scripts/validate-production-env.mjs",
    "prod:frontend:build": "cross-env NODE_ENV=production NEXT_PUBLIC_API_BASE=/api NEXT_PUBLIC_USE_MOCK=false npm --prefix frontend run build",
    "demo:stage-check": "node scripts/stage-check.mjs --mode=demo",
    "demo:build": "node scripts/build-site.mjs"
  }
}
```

Replace the current PowerShell stage check with a thin compatibility wrapper that executes `node ../../scripts/stage-check.mjs --mode=demo`. The Node script checks `NEXT_PUBLIC_API_BASE`, never `NEXT_PUBLIC_API_URL`, and does not inspect or kill ports.

Create the cross-platform wrappers:

```javascript
// scripts/run-backend-tests.mjs
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";

const result = spawnSync(process.env.PYTHON || "python", ["-m", "pytest", "tests", "-q"], {
  cwd: resolve("backend"), stdio: "inherit", shell: false,
});
process.exit(result.status ?? 1);
```

```javascript
// frontend/scripts/clean-next.mjs
import { rm } from "node:fs/promises";
await Promise.all([".next", "out"].map((path) => rm(path, { recursive: true, force: true })));
```

Set root `backend:test` to `node scripts/run-backend-tests.mjs`. Set frontend `clean` to `node scripts/clean-next.mjs`, `dev` to `next dev`, `dev:clean` to `npm run clean --silent && next dev`, `build:clean` to `npm run clean --silent && next build`, and `stage-check` to `node ../scripts/stage-check.mjs --mode=demo`. Keep the old `.ps1` files only as unreferenced local helpers until the redundancy audit proves they can be removed.

- [ ] **Step 5: Verify and commit**

```bash
node --test tests/releaseModes.test.mjs
npm run prod:validate
npm run demo:stage-check
git add scripts/validate-production-env.mjs scripts/stage-check.mjs scripts/run-backend-tests.mjs scripts/build-site.mjs frontend/scripts/clean-next.mjs frontend/scripts/stage-check.ps1 frontend/package.json package.json tests/releaseModes.test.mjs
git commit -m "build: separate production and demo releases"
```

Expected: tests and both explicit validation paths pass under their documented environment.

### Task 2: Upgrade Vulnerable Frontend Dependencies and Make Lint Real

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/eslint.config.mjs`
- Delete: obsolete ESLint config file if one exists after the upgrade
- Modify source files reported by lint/codemods

- [ ] **Step 1: Capture the current failing gates**

```bash
npm --prefix frontend run lint
npm audit --prefix frontend --omit=dev --audit-level=high
```

Expected before the change: lint enters setup or is not a real non-interactive check; audit reports the known Next.js production advisory.

- [ ] **Step 2: Upgrade the framework using its supported codemod**

Run from `frontend/`:

```bash
npx @next/codemod@latest upgrade latest
npm install next@latest react@latest react-dom@latest eslint-config-next@latest
```

Review every codemod diff. Keep App Router behavior, server-mode standalone output, and the explicit demo export branch. Do not suppress type or lint errors with `any`, `@ts-ignore`, or disabled rules.

- [ ] **Step 3: Add a non-interactive flat ESLint config**

```javascript
// frontend/eslint.config.mjs
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "demo-dist/**", "next-env.d.ts"]),
]);
```

Set `"lint": "eslint . --max-warnings=0"`. Keep `"typecheck": "tsc --noEmit"`.

- [ ] **Step 4: Fix all reported issues and verify the secure lock**

```bash
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test:unit
npm --prefix frontend run build
npm audit --prefix frontend --omit=dev --audit-level=high
```

Expected: all commands exit 0; the production audit reports zero Critical/High vulnerabilities. Moderate or lower findings require an entry in the release risk report with package, advisory, exploitability, and target version.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/eslint.config.mjs frontend
git commit -m "build: upgrade frontend security dependencies"
```

Before committing, use `git diff --cached --name-only` to ensure `.next`, `out`, logs, and local env files are absent.

### Task 3: Enforce Headers in Server and Static Demo Modes

**Files:**
- Modify: `frontend/next.config.js`
- Modify: `scripts/site-worker.mjs`
- Test: `tests/securityHeaders.test.mjs`

- [ ] **Step 1: Write failing static-worker tests**

```javascript
// tests/securityHeaders.test.mjs
import assert from "node:assert/strict";
import test from "node:test";

import worker from "../scripts/site-worker.mjs";

test("static worker adds release security headers", async () => {
  const env = { ASSETS: { fetch: async () => new Response("ok", { status: 200, headers: { "Content-Type": "text/html" } }) } };
  const response = await worker.fetch(new Request("https://demo.example.test/", { headers: { Accept: "text/html" } }), env);
  assert.equal(response.headers.get("X-Content-Type-Options"), "nosniff");
  assert.equal(response.headers.get("X-Frame-Options"), "DENY");
  assert.equal(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin");
  assert.match(response.headers.get("Content-Security-Policy"), /default-src 'self'/);
});
```

- [ ] **Step 2: Run and verify failure**

```bash
node --test tests/securityHeaders.test.mjs
```

Expected: FAIL because the Worker returns asset responses unchanged.

- [ ] **Step 3: Add immutable response headers**

```javascript
const SECURITY_HEADERS = {
  "Content-Security-Policy": "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; font-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

function secure(response) {
  const next = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) next.headers.set(name, value);
  return next;
}
```

Apply `secure()` to direct and fallback asset responses. Add the same CSP and Permissions-Policy in `next.config.js` server-mode `headers()`. Add HSTS only at the real TLS ingress; do not emit it from HTTP localhost tests.

- [ ] **Step 4: Verify and commit**

```bash
node --test tests/securityHeaders.test.mjs
npm --prefix frontend run build
git add frontend/next.config.js scripts/site-worker.mjs tests/securityHeaders.test.mjs
git commit -m "fix: enforce release security headers"
```

### Task 4: Add Clean CI With PostgreSQL, Audits, Containers, and Browsers

**Files:**
- Create: `.github/workflows/release-gate.yml`
- Modify: `package.json`
- Create: `frontend/playwright.config.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Install Playwright and axe tooling**

Run from `frontend/`:

```bash
npm install --save-dev @playwright/test @axe-core/playwright
npx playwright install chromium
```

Add:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed"
  }
}
```

- [ ] **Step 2: Configure desktop and mobile projects**

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  retries: process.env.CI ? 2 : 0,
  use: { baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3000", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
});
```

- [ ] **Step 3: Create the complete release workflow**

```yaml
# .github/workflows/release-gate.yml
name: release-gate
on:
  push:
  pull_request:
jobs:
  verify:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: wudian_test
          POSTGRES_USER: wudian
          POSTGRES_PASSWORD: test_password
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U wudian -d wudian_test"
          --health-interval 5s --health-timeout 3s --health-retries 20
    env:
      APP_ENV: test
      APP_DEBUG: "false"
      POSTGRES_PASSWORD: test_password
      DATABASE_URL: postgresql+asyncpg://wudian:test_password@127.0.0.1:5432/wudian_test
      JWT_SECRET_KEY: ci-only-secret-with-at-least-32-bytes
      CORS_ORIGINS: '["http://127.0.0.1:3000"]'
      COOKIE_SECURE: "false"
      NEXT_PUBLIC_API_BASE: /api
      NEXT_PUBLIC_USE_MOCK: "false"
      NODE_ENV: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: "pip" }
      - uses: actions/setup-node@v4
        with: { node-version: "22", cache: "npm", cache-dependency-path: "frontend/package-lock.json" }
      - run: python -m pip install --require-hashes -r backend/requirements-dev.lock
      - run: npm ci --prefix frontend
      - run: python -m alembic upgrade head
        working-directory: backend
      - run: python scripts/seed_static_data.py
        working-directory: backend
      - run: python -m pytest tests --cov=app --cov-branch --cov-report=term-missing
        working-directory: backend
      - run: npm run lint --prefix frontend
      - run: npm run typecheck --prefix frontend
      - run: npm run test --prefix frontend
      - run: npm run test:unit --prefix frontend
      - run: npm run test:runtime-assets --prefix frontend
      - run: python -m pytest frontend/tests/tengwangPlaqueAsset.test.py -q
      - run: npm run build --prefix frontend
      - run: npm audit --prefix frontend --omit=dev --audit-level=high
      - run: python -m pip_audit -r backend/requirements.lock
      - run: docker compose build
      - run: npx playwright install --with-deps chromium
        working-directory: frontend
      - run: docker compose -p wudian-ci up -d --wait
      - run: npm run test:e2e --prefix frontend
      - if: always()
        run: docker compose -p wudian-ci logs --no-color
      - if: always()
        run: docker compose -p wudian-ci down -v
```

In the final workflow, production-only `Settings` validation is tested in its own unit test; CI runtime uses `APP_ENV=test`, so its HTTP CORS/Cookie settings are valid for browser tests.

- [ ] **Step 4: Add one local aggregate gate**

```json
{
  "scripts": {
    "release:gate": "npm test && npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend run build && npm audit --prefix frontend --omit=dev --audit-level=high"
  }
}
```

Backend locked audit and Compose/E2E remain separate commands so their failures are visible rather than hidden in an OS-specific chain.

- [ ] **Step 5: Validate workflow syntax and local gates**

```bash
npm run release:gate
docker compose config
```

Expected: both exit 0. Push/PR CI later proves the full Linux workflow.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/release-gate.yml frontend/playwright.config.ts frontend/package.json frontend/package-lock.json package.json
git commit -m "ci: add production release gate"
```

### Task 5: Audit and Remove Proven Runtime or Duplicate Artifacts

**Files:**
- Create: `scripts/audit-redundancy.mjs`
- Create: `tests/redundancyAudit.test.mjs`
- Create: `scripts/package-preliminary-demo.mjs`
- Create: `docs/operations/redundancy-report.md`
- Modify: `.gitignore`
- Modify: `frontend/.gitignore`
- Modify: `package.json`
- Modify: `package-lock.json`
- Modify: `报名材料/validate-preliminary-demo.cjs`
- Delete: tracked `backend/data/debates/*.json`
- Delete: tracked `data/debates/*.json`
- Delete: `backend/init_log.txt`
- Delete: obsolete tracked `报名材料/悟典-初赛Demo/` and its tracked ZIP after canonical validation passes
- Preserve: `data/processed/debate_classics.json`
- Preserve: `报名材料/一问见古今-初赛Demo/` and `THREE-LICENSE.txt`

- [ ] **Step 1: Write a failing repository-artifact test**

```javascript
// tests/redundancyAudit.test.mjs
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import test from "node:test";

const tracked = () => execFileSync("git", ["ls-files", "-z"], { encoding: "utf8" }).split("\0").filter(Boolean);

test("runtime debate sessions and logs are not tracked", () => {
  const files = tracked();
  assert.equal(files.some((file) => /^(backend\/)?data\/debates\/.*\.json$/.test(file)), false);
  assert.equal(files.includes("backend/init_log.txt"), false);
});

test("environment examples remain tracked", () => {
  const files = tracked();
  assert(files.includes("backend/.env.example"));
  assert(files.includes("frontend/.env.local.example"));
});

test("only the canonical preliminary demo source is tracked", () => {
  const files = tracked();
  assert.equal(files.some((file) => file.startsWith("报名材料/悟典-初赛Demo/")), false);
  assert.equal(files.some((file) => file.endsWith("初赛Demo.zip")), false);
  assert(files.some((file) => file.startsWith("报名材料/一问见古今-初赛Demo/")));
});
```

- [ ] **Step 2: Run and verify failure**

```bash
node --test tests/redundancyAudit.test.mjs
```

Expected: FAIL because 220 runtime debate JSON files, `init_log.txt`, and a tracked demo ZIP/duplicate are present; the frontend env example may also be ignored.

- [ ] **Step 3: Add deterministic audit output**

```javascript
// scripts/audit-redundancy.mjs
import { execFileSync } from "node:child_process";
import { statSync } from "node:fs";

const files = execFileSync("git", ["ls-files", "-z"], { encoding: "utf8" }).split("\0").filter(Boolean);
const categories = {
  runtimeDebates: files.filter((file) => /^(backend\/)?data\/debates\/.*\.json$/.test(file)),
  logs: files.filter((file) => file.endsWith(".log") || file === "backend/init_log.txt"),
  archives: files.filter((file) => /\.(zip|tar|gz)$/.test(file)),
  large: files.filter((file) => { try { return statSync(file).size > 500_000; } catch { return false; } }),
};
console.log(JSON.stringify({ counts: Object.fromEntries(Object.entries(categories).map(([key, value]) => [key, value.length])), files: categories }, null, 2));
if (categories.runtimeDebates.length || categories.logs.length) process.exitCode = 1;
```

Capture the before/after counts and every retained large artifact with its consumer/license reason in `docs/operations/redundancy-report.md`.

- [ ] **Step 4: Prove the canonical demo before deleting duplicates**

Update the validator's package root once so the command is deterministic:

```javascript
const packageRoot = path.resolve(process.argv[2] || path.join(__dirname, "一问见古今-初赛Demo"));
```

```bash
node 报名材料/validate-preliminary-demo.cjs 报名材料/一问见古今-初赛Demo
rg -n "悟典-初赛Demo|思想审判场-初赛Demo" 报名材料 scripts package.json docs
```

Expected: canonical validation passes; remaining references are either updated to `一问见古今-初赛Demo` or documented historical prose, not build consumers.

- [ ] **Step 5: Remove runtime output and obsolete tracked artifacts**

Use Git-aware deletion only after the previous command passes:

```bash
git rm -- "backend/data/debates/*.json"
git rm -- "data/debates/*.json"
git rm backend/init_log.txt
git rm -r --ignore-unmatch "报名材料/悟典-初赛Demo"
git rm --ignore-unmatch "报名材料/悟典-思想审判场-初赛Demo.zip"
```

Do not delete `data/processed/debate_classics.json`; it is static retrieval data. Do not delete canonical Three.js files because `court-scene.js` imports them and the validator checks them. Keep `THREE-LICENSE.txt` beside those files.

- [ ] **Step 6: Generate submission ZIPs instead of tracking them**

Install `archiver` as a root dev dependency and remove unused `pptxgenjs` only after `rg -n "pptxgenjs" . --glob '!node_modules/**'` returns only manifest/lock entries.

```javascript
// scripts/package-preliminary-demo.mjs
import { createWriteStream } from "node:fs";
import { mkdir } from "node:fs/promises";
import archiver from "archiver";

await mkdir("dist", { recursive: true });
const output = createWriteStream("dist/一问见古今-初赛Demo.zip");
const archive = archiver("zip", { zlib: { level: 9 } });
const completed = new Promise((resolve, reject) => { output.on("close", resolve); output.on("error", reject); archive.on("error", reject); });
archive.pipe(output);
archive.directory("报名材料/一问见古今-初赛Demo", "一问见古今-初赛Demo");
await archive.finalize();
await completed;
console.log(`created dist/一问见古今-初赛Demo.zip (${archive.pointer()} bytes)`);
```

- [ ] **Step 7: Harden ignore rules while preserving examples**

```gitignore
backend/data/debates/
data/debates/
backend/*.log
frontend/*.log
demo-dist/
dist/
*.zip
.env
.env.*
!.env.example
!.env.local.example
!backend/.env.example
!frontend/.env.local.example
```

Add `!.env.local.example` after `.env*.local` in `frontend/.gitignore`; the root exception cannot override a nested ignore rule by itself.

- [ ] **Step 8: Verify cleanup and commit**

```bash
node --test tests/redundancyAudit.test.mjs
node scripts/audit-redundancy.mjs
npm run demo:build
node scripts/package-preliminary-demo.mjs
npm test
git add .gitignore frontend/.gitignore scripts/audit-redundancy.mjs scripts/package-preliminary-demo.mjs tests/redundancyAudit.test.mjs docs/operations/redundancy-report.md package.json package-lock.json 报名材料/validate-preliminary-demo.cjs 报名材料/一问见古今-初赛Demo
git commit -m "chore: remove runtime and duplicate artifacts"
```

Expected: audit/tests pass; canonical demo builds/packages; `dist` ZIP remains ignored; all product tests pass.

### Task 6: Fix Touch Targets, Initial Visibility, Focus, and Reduced Motion

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/components/Navbar.tsx`
- Modify: controls identified by Playwright accessibility scan
- Create: `frontend/e2e/accessibility.spec.ts`

- [ ] **Step 1: Write failing browser accessibility checks**

```typescript
// frontend/e2e/accessibility.spec.ts
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const path of ["/", "/reader?book=lunyu", "/community", "/login"]) {
  test(`${path} has no serious accessibility violations`, async ({ page }) => {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((item) => ["critical", "serious"].includes(item.impact ?? ""))).toEqual([]);
  });
}

test("interactive controls meet mobile touch target size", async ({ page, isMobile }) => {
  test.skip(!isMobile);
  await page.goto("/");
  const controls = page.locator("a[href], button:not([disabled]), input, select");
  for (let index = 0; index < await controls.count(); index += 1) {
    const control = controls.nth(index);
    if (!(await control.isVisible())) continue;
    const box = await control.boundingBox();
    expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
});

test("home primary content is visible immediately with reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCSS("opacity", "1");
});
```

- [ ] **Step 2: Run and verify failure**

```bash
npm --prefix frontend run test:e2e -- accessibility.spec.ts
```

Expected: FAIL on the known sub-44px controls and any entrance state that starts low-opacity.

- [ ] **Step 3: Fix measured violations**

Use `min-h-11 min-w-11` for icon controls and at least 44px for carousel arrows, mobile navigation, modal close, and pagination controls. Keep visible focus with `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2`. Add accessible names to icon-only controls.

Make primary home content render at opacity 1 in the initial HTML. Motion may translate/fade secondary content for at most 240ms after hydration. Under `prefers-reduced-motion: reduce`, disable smooth scrolling, transforms, nonessential transition duration, and pulse animations.

- [ ] **Step 4: Verify desktop/mobile and commit**

```bash
npm --prefix frontend run test:e2e -- accessibility.spec.ts
npm --prefix frontend run lint
npm --prefix frontend run typecheck
git add frontend/app/globals.css frontend/app/page.tsx frontend/components/Navbar.tsx frontend/components frontend/e2e/accessibility.spec.ts
git commit -m "fix: meet launch accessibility targets"
```

Expected: desktop/mobile accessibility tests pass without blanket axe exclusions.

### Task 7: Add Real Full-Stack Browser Acceptance

**Files:**
- Create: `frontend/e2e/fullstack.spec.ts`
- Modify backend seed/test helpers only when required for deterministic release data
- Create: `docs/operations/release-checklist.md`

- [ ] **Step 1: Write the real-stack journeys**

```typescript
// frontend/e2e/fullstack.spec.ts
import { expect, test } from "@playwright/test";

const suffix = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

async function register(page, name: string): Promise<string> {
  const unique = suffix();
  await page.goto("/register");
  await page.getByLabel("用户名").fill(`${name}${unique}`.slice(0, 40));
  await page.getByLabel("邮箱").fill(`${name}${unique}@example.test`);
  await page.getByLabel("密码").fill("Release-Test-Password-123");
  const responsePromise = page.waitForResponse((response) => response.url().includes("/api/auth/register") && response.request().method() === "POST");
  await page.getByRole("button", { name: "注册" }).click();
  const response = await responsePromise;
  expect(response.status()).toBe(201);
  const payload = await response.json();
  await expect(page).toHaveURL(/\/$/);
  return payload.access_token;
}

test("new user reads, persists progress, and reloads", async ({ page }) => {
  await register(page, "reader");
  await page.goto("/reader?book=lunyu&chapter=lunyu-1&highlight=学而时习之");
  await expect(page.locator("mark[data-reader-highlight]")).toContainText("学而时习之");
  await page.getByRole("button", { name: "标记已读" }).click();
  await expect(page.getByRole("button", { name: /本章已读/ })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: /本章已读/ })).toBeVisible();
});

test("community and debate data are isolated between users", async ({ browser }) => {
  const aliceContext = await browser.newContext();
  const bobContext = await browser.newContext();
  const alice = await aliceContext.newPage();
  const bob = await bobContext.newPage();
  const aliceToken = await register(alice, "alice");
  const bobToken = await register(bob, "bob");
  const start = await alice.request.post("/api/debate/start", { headers: { Authorization: `Bearer ${aliceToken}` }, data: { topic: "Alice private topic" } });
  const sessionId = (await start.json()).session_id;
  const forbidden = await bob.request.get(`/api/debate/${sessionId}/session`, { headers: { Authorization: `Bearer ${bobToken}` } });
  expect(forbidden.status()).toBe(403);
  await aliceContext.close();
  await bobContext.close();
});
```

Add journeys for login/refresh after reload, review failure recovery, chapter challenge submission, community load failure retry, PK timeout single submit, and AI/SSE degraded error. Use API setup only when the UI does not expose a creation form; all user-visible claims must still be asserted in the UI.

- [ ] **Step 2: Run against a new Compose project**

```bash
docker compose -p wudian-e2e up -d --build --wait
npm --prefix frontend run test:e2e
docker compose -p wudian-e2e down -v
```

Expected: both desktop and mobile projects pass. Screenshots/traces exist only for failures.

- [ ] **Step 3: Record the executable release checklist**

The checklist maps every acceptance criterion to one command or Playwright test name. It includes migration/seed, auth, community isolation, debate ownership, reading, review, challenge, SSE degradation, headers, dependency audits, accessibility, backup/restore rehearsal, and rollback decision.

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/fullstack.spec.ts docs/operations/release-checklist.md
git commit -m "test: add real full stack release journeys"
```

### Task 8: Close Licensing and Run the Final Release Gate

**Files:**
- Create: `LICENSE`
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `docs/operations/release-checklist.md`
- Create: `docs/operations/release-risk-register.md`

- [ ] **Step 1: Confirm project license ownership**

Do not invent a license. Obtain the owner's chosen license text and add it verbatim to `LICENSE`. If no redistribution license is granted, use an explicit proprietary copyright notice supplied by the owner. This user decision is required before distributing source or bundled third-party code.

- [ ] **Step 2: Generate third-party notices from actual shipped packages/assets**

List direct frontend/backend production dependencies, fonts, images, and the canonical Three.js bundle. Record package/asset, version or source, license, copyright notice, and local license path. Verify the Three.js license is present beside the offline demo modules.

- [ ] **Step 3: Run every final gate from a clean process state**

```bash
npm ci --prefix frontend
python -m pip install --require-hashes -r backend/requirements-dev.lock
npm test
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm audit --prefix frontend --omit=dev --audit-level=high
python -m pip_audit -r backend/requirements.lock
node --test tests/releaseModes.test.mjs tests/securityHeaders.test.mjs tests/redundancyAudit.test.mjs
docker compose -p wudian-final up -d --build --wait
node scripts/smoke-empty-db.mjs
npm --prefix frontend run test:e2e
docker compose -p wudian-final down -v
```

Expected: every command exits 0; the database starts empty and migrates; no Critical/High production advisory remains; desktop/mobile journeys pass.

- [ ] **Step 4: Record only genuine residual risks**

For every unresolved Moderate/Low finding, record severity, affected component, exploitability, mitigation, responsibility role, and target date. Any open data-loss, auth bypass, cross-user access, startup, migration, Critical/High dependency, or core-flow failure remains release-blocking.

- [ ] **Step 5: Commit the release handoff**

```bash
git add LICENSE THIRD_PARTY_NOTICES.md docs/operations/release-checklist.md docs/operations/release-risk-register.md
git commit -m "docs: complete production release handoff"
```

## Plan Completion Gate

The project is release-ready only after Task 8's clean-process gate passes, the backup/restore rehearsal is checked in `docs/operations/release-checklist.md`, the risk register has no blocker, and browser screenshots/traces show no desktop/mobile overlap or inaccessible core control. Domain and DNS remain outside this gate.

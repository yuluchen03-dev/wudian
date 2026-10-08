const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const repoRoot = path.join(root, "..");
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8");
const readRepo = (...parts) => fs.readFileSync(path.join(repoRoot, ...parts), "utf8");

const rootPackage = JSON.parse(readRepo("package.json"));
for (const scriptName of ["stage-check", "frontend:test", "backend:test", "test", "build:clean"]) {
  assert.ok(
    rootPackage.scripts?.[scriptName],
    `Root package.json should define ${scriptName}`
  );
}

const rootGitignore = readRepo(".gitignore");
assert.ok(
  rootGitignore.includes(".worktrees/"),
  "Root .gitignore should ignore local worktree scratch directories"
);
assert.ok(
  rootGitignore.includes("frontend/.next/"),
  "Root .gitignore should ignore the frontend Next.js build output"
);

const backendReadme = readRepo("backend", "README.md");
assert.ok(
  backendReadme.includes("黑客松演示运行口径"),
  "Backend README should document the hackathon demo runtime stance"
);
assert.ok(
  backendReadme.includes("SQLite"),
  "Backend README should make SQLite explicit for the local hackathon demo"
);

const citationSidebar = read("components", "sage", "CitationSidebar.tsx");
assert.match(
  citationSidebar,
  /useState\(\s*demoMode\s*\)/,
  "Sage chat citations should open by default in demo mode so judges see proof without an extra click"
);
assert.ok(
  citationSidebar.includes("可溯源证据"),
  "Sage chat citation trigger should label citations as verifiable evidence"
);

const citationPanel = read("components", "roundtable", "CitationPanel.tsx");
assert.match(
  citationPanel,
  /useState\(\s*true\s*\)/,
  "Roundtable citation panel should be expanded by default for the stage-ready completion view"
);
assert.ok(
  citationPanel.includes("可溯源引用汇总"),
  "Roundtable citation panel should explicitly frame citations as verifiable proof"
);

const navbar = read("components", "Navbar.tsx");
const primaryNavMatch = navbar.match(/const primaryNav = \[[\s\S]*?\];/);
assert.ok(primaryNavMatch, "Navbar should define primaryNav");
assert.ok(
  !primaryNavMatch[0].includes('href: "/demo"'),
  "Formal product navigation should not foreground the retired demo route"
);

const sageChat = read("components", "sage", "SageChat.tsx");
assert.ok(
  sageChat.includes("max-h-[calc(100dvh-"),
  "Demo chat should use viewport-aware height instead of a fixed tall container"
);

const cleanNextScript = read("scripts", "clean-next.ps1");
assert.ok(
  cleanNextScript.includes("Get-NetTCPConnection"),
  "Clean script should inspect local listeners before removing .next"
);
assert.ok(
  cleanNextScript.includes("ALLOW_NEXT_CLEAN_WHILE_RUNNING"),
  "Clean script should require an explicit override before cleaning while Next is running"
);
assert.ok(
  cleanNextScript.includes("Refusing to clean .next while"),
  "Clean script should fail loudly instead of corrupting a live dev server"
);

const about = read("app", "about", "page.tsx");
assert.doesNotMatch(
  about,
  /icon:\s*["'`][^\w\s"'`]/,
  "About page feature icons should use the shared icon system instead of emoji strings"
);
assert.ok(
  about.includes('id="investment"'),
  "About page should expose the investment anchor used by demo CTAs"
);
assert.match(
  about,
  /试点合作|投资合作/,
  "About investment anchor should clearly name pilot or investment cooperation"
);

console.log("hackathonReadiness frontend tests passed");

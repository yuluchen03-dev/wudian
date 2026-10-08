const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (relativePath) =>
  fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");

const home = read("app/page.tsx");
const sagePage = read("app/sage-chat/page.tsx");
const sageChat = read("components/sage/SageChat.tsx");
const navbar = read("components/Navbar.tsx");
const globals = read("app/globals.css");

assert.match(home, /data-ui="editorial-hero"/, "home should expose the editorial hero");
assert.match(home, /confucius\.png/, "home hero should use the existing Confucius cultural asset");
assert.match(home, /每一次回答，都有典可循/, "home should foreground source-backed answers");
assert.match(home, /data-ui="trust-strip"/, "home should show a compact trust strip");

assert.match(sagePage, /data-ui="sage-workspace"/, "sage page should use the knowledge workspace");
assert.match(sagePage, /lg:grid-cols-\[220px_minmax\(0,1fr\)_300px\]/, "desktop sage workspace should use three columns");
assert.match(sagePage, /思想依据/, "sage workspace should label the evidence rail");
assert.match(sageChat, /data-ui="sage-composer"/, "sage chat should expose a stable composer region");
assert.match(
  sageChat,
  /h-\[calc\(100dvh-266px\)\][\s\S]*sm:h-\[calc\(100dvh-246px\)\][\s\S]*lg:h-\[calc\(100dvh-198px\)\]/,
  "sage composer should stay inside mobile, tablet, and desktop viewports"
);
assert.match(sagePage, /onCitationsChange=/, "sage workspace should receive live citations");
assert.match(sagePage, /activeCitations\.map/, "evidence rail should render the active answer citations");
assert.match(sagePage, /data-ui="mobile-evidence"/, "mobile sage chat should expose compact evidence disclosure");
assert.match(sagePage, /<details[\s\S]*<summary[\s\S]*思想依据/, "mobile evidence should be expandable without custom state");
assert.doesNotMatch(sagePage, /历史对话|收藏原文/, "workspace should not expose inert actions");
assert.match(sageChat, /abortRef\.current = true;[\s\S]*setIsStreaming\(false\)/, "switching sages should abort the active stream");

assert.match(navbar, /问道/, "primary navigation should foreground sage chat");
assert.match(navbar, /经典/, "primary navigation should use concise product language");
const primaryNavBlock = navbar.match(/const primaryNav = \[[\s\S]*?\];/);
assert.ok(primaryNavBlock, "navbar should define its primary destinations");
assert.doesNotMatch(primaryNavBlock[0], /闯关|复习/, "secondary learning tools should not crowd the primary nav");
assert.doesNotMatch(primaryNavBlock[0], /\/demo|演示/, "demo should not remain in formal product navigation");
assert.equal(
  (primaryNavBlock[0].match(/\{ href:/g) || []).length,
  5,
  "formal product navigation should expose exactly five primary destinations"
);
assert.match(navbar, /data-ui="mobile-auth"/, "mobile navigation should expose authentication actions");

assert.match(globals, /--color-action:\s*#334854/, "global CSS should define the indigo-ink command color");
assert.match(globals, /--color-citation:\s*#9e443a/i, "global CSS should define the cinnabar citation color");
assert.match(globals, /@media \(prefers-reduced-motion: reduce\)/, "global CSS should support reduced motion");
assert.match(home, /useReducedMotion/, "home motion should honor reduced-motion preferences");
assert.match(sagePage, /useReducedMotion/, "sage workspace motion should honor reduced-motion preferences");
assert.match(home, /role="dialog"/, "quiz overlay should expose dialog semantics");
assert.match(home, /aria-modal="true"/, "quiz overlay should be announced as modal");
assert.match(home, /handleQuizKeyDown/, "quiz modal should handle keyboard focus and Escape");
assert.match(home, /quizCloseRef\.current\?\.focus\(\)/, "quiz modal should place initial focus inside its trap");

console.log("uiRedesignWiring tests passed");

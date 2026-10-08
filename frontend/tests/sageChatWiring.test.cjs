const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const componentPath = path.join(__dirname, "..", "components", "sage", "SageChat.tsx");
const source = fs.readFileSync(componentPath, "utf8");
const citationSidebarPath = path.join(__dirname, "..", "components", "sage", "CitationSidebar.tsx");
const citationSidebar = fs.readFileSync(citationSidebarPath, "utf8");

const handleSendMatch = source.match(/const handleSend = async[\s\S]*?const userMsg/);
assert.ok(handleSendMatch, "SageChat should define handleSend before creating the user message");

assert.match(
  handleSendMatch[0],
  /abortRef\.current\s*=\s*false/,
  "handleSend should clear stale abort state before reading stream chunks"
);

assert.match(
  source,
  /import\s*\{\s*generateSageReply\s*,\s*getLocalSageCitations\s*\}\s*from\s*["']@\/lib\/sageData["']/,
  "SageChat should import local citation fallback data with generateSageReply"
);

const catchFallbackMatch = source.match(/catch \(e: unknown\)[\s\S]*?finally \{/);
assert.ok(catchFallbackMatch, "SageChat should keep a catch fallback before finally");
assert.match(
  catchFallbackMatch[0],
  /getLocalSageCitations\(sage\.id\)/,
  "SageChat fallback should derive citations for the selected sage"
);
assert.match(
  catchFallbackMatch[0],
  /content:\s*fallback[\s\S]*citations:\s*(?:getLocalSageCitations\(sage\.id\)|localCitations|fallbackCitations)/,
  "SageChat fallback sage message should set fallback content and local citations together"
);

assert.ok(
  citationSidebar.includes("normalizeCitation"),
  "CitationSidebar should normalize backend citation shapes before rendering"
);
assert.ok(
  citationSidebar.includes("extractKeywords(citationText)"),
  "CitationSidebar should extract keywords from a safe citation text string"
);
assert.doesNotMatch(
  citationSidebar,
  /extractKeywords\(citation\.text\)/,
  "CitationSidebar should not call string helpers directly on possibly missing citation.text"
);
assert.match(
  source,
  /aria-label="发送问题"/,
  "the icon-only sage send button should have an accessible name"
);

console.log("sageChatWiring tests passed");

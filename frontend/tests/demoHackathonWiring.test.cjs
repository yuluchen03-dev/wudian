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
  assert.ok(
    source.includes(snippet),
    `Demo page should include hackathon signal: ${snippet}`
  );
});

assert.match(
  source,
  /\/sage-chat\?q=/,
  "Demo page should link to sage chat with a prefilled one-click question"
);
assert.ok(
  source.includes("试点合作") || source.includes("投资合作"),
  "Demo hero should include a partnership CTA for hackathon follow-up"
);
assert.match(
  source,
  /\/roundtable\?demo=complete/,
  "Demo page should link to the complete roundtable fallback preview"
);
assert.match(
  source,
  /href="\/about"/,
  "Demo page should link to technical explanation"
);

console.log("demoHackathonWiring tests passed");

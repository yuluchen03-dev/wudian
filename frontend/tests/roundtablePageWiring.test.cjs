const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const pagePath = path.join(__dirname, "..", "app", "roundtable", "page.tsx");
const source = fs.readFileSync(pagePath, "utf8");

const guestSummonerMatch = source.match(/<GuestSummoner[\s\S]*?\/>/);
assert.ok(guestSummonerMatch, "Roundtable page should render GuestSummoner");

const guestSummonerCall = guestSummonerMatch[0];
assert.match(
  guestSummonerCall,
  /roster=\{guestRoster\}/,
  "GuestSummoner should receive the live guest roster"
);
assert.match(
  guestSummonerCall,
  /onDecision=\{handleGuestDecision\}/,
  "GuestSummoner should wire stay/leave decisions"
);
assert.match(
  guestSummonerCall,
  /cue=\{guestCue\}/,
  "GuestSummoner should receive the current challenger cue"
);

assert.match(
  source,
  /<ModeratorStateGraph\s+graph=\{graphState\}\s*\/>/,
  "Roundtable page should render the moderator state graph with live graph state"
);

assert.match(
  source,
  /useSearchParams/,
  "Roundtable page should read demo mode from search params"
);
assert.match(
  source,
  /demoMode\s*===\s*"complete"/,
  "Roundtable page should recognize the complete demo mode"
);
assert.match(
  source,
  /loadCompleteDemo/,
  "Roundtable page should provide a direct complete-state demo loader"
);

console.log("roundtablePageWiring tests passed");

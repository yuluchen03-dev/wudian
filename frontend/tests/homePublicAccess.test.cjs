const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const apiPath = path.join(__dirname, "..", "lib", "api.ts");
const source = fs.readFileSync(apiPath, "utf8");

assert.match(
  source,
  /originalRequest\.skipAuthRedirect/,
  "401 interceptor should support requests that do not redirect public pages to login"
);

const getProgressMatch = source.match(/async getProgress[\s\S]*?const d = resp\?\.data \?\? resp;/);
assert.ok(getProgressMatch, "api.getProgress should fetch learning progress");
assert.match(
  getProgressMatch[0],
  /skipAuthRedirect\s*:\s*true/,
  "api.getProgress should not force a login redirect when used on the public home page"
);

console.log("homePublicAccess tests passed");

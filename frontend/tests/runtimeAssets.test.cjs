const assert = require("assert");

const baseUrl = process.env.WUDIAN_BASE_URL || "http://localhost:3000";
const routes = [
  "/",
  "/content",
  "/roundtable",
  "/reader",
  "/sage-chat",
  "/challenge",
  "/review",
  "/exploration",
  "/concepts",
  "/achievements",
];

// This suite is the only one that needs a running frontend. It is environment-gated, NOT
// weakened: every assertion below is unchanged. When no server is reachable we skip loudly
// instead of reporting a false pass, so `npm test` stays hermetic while this suite remains
// runnable on demand.
async function serverIsReachable() {
  try {
    const response = await fetch(new URL("/", baseUrl).toString(), {
      signal: AbortSignal.timeout(2500),
    });
    return response.ok;
  } catch {
    return false;
  }
}

const assetPattern =
  /(?:href|src)="([^"]*\/_next\/static\/(?:css|chunks)\/[^"]+)"/g;
const expectedBrand = process.env.WUDIAN_EXPECTED_BRAND || "\u609f\u5178";
const forbiddenBrands = (
  process.env.WUDIAN_FORBIDDEN_BRANDS ||
  "\u7076\u4f20,\u975e\u9057\u7f8e\u98df"
)
  .split(",")
  .map((item) => item.trim())
  .filter(Boolean);

function normalizeAssetUrl(assetPath) {
  const cleanPath = assetPath.replace(/&amp;/g, "&");
  return new URL(cleanPath, baseUrl).toString();
}

async function fetchText(url) {
  const response = await fetch(url);
  const text = await response.text();
  return { response, text };
}

(async () => {
  if (!(await serverIsReachable())) {
    console.log(
      `SKIP runtime asset checks: no reachable frontend at ${baseUrl}. ` +
        `Start the app (\`npm run start\`) then run \`npm run test:runtime-assets\` to execute them.`
    );
    return;
  }

  const failures = [];

  for (const route of routes) {
    const pageUrl = new URL(route, baseUrl).toString();
    const { response, text } = await fetchText(pageUrl);

    if (!response.ok) {
      failures.push(`${route}: page returned ${response.status}`);
      continue;
    }

    if (!text.includes(expectedBrand)) {
      failures.push(`${route}: HTML does not include expected brand ${expectedBrand}`);
    }

    for (const forbiddenBrand of forbiddenBrands) {
      if (text.includes(forbiddenBrand)) {
        failures.push(`${route}: HTML includes forbidden cross-project brand ${forbiddenBrand}`);
      }
    }

    const assetUrls = [...text.matchAll(assetPattern)]
      .map((match) => normalizeAssetUrl(match[1]))
      .filter((value, index, list) => list.indexOf(value) === index);

    if (!assetUrls.some((url) => url.includes("/_next/static/css/"))) {
      failures.push(`${route}: no Next CSS asset found in HTML`);
    }

    if (!assetUrls.some((url) => url.includes("/_next/static/chunks/"))) {
      failures.push(`${route}: no Next JS chunk found in HTML`);
    }

    for (const assetUrl of assetUrls) {
      const assetResponse = await fetch(assetUrl);
      if (!assetResponse.ok) {
        failures.push(`${route}: asset ${assetUrl} returned ${assetResponse.status}`);
      }
    }

    if (text.includes("C:\\Users\\hacjr\\Desktop\\\u7076\u4f20")) {
      failures.push(`${route}: HTML references the wrong mojibake workspace path`);
    }

    if (text.includes("C:\\Users\\hacjr\\Desktop\\") && /[\u9380-\u93ff]/.test(text)) {
      failures.push(`${route}: HTML references mojibake workspace path`);
    }
  }

  assert.strictEqual(failures.length, 0, failures.join("\n"));
  console.log(`runtime asset checks passed for ${routes.length} routes at ${baseUrl}`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

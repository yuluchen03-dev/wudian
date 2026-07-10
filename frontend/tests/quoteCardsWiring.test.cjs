const fs = require("fs");
const path = require("path");
const assert = require("assert");

const apiSource = fs.readFileSync(path.join(__dirname, "../lib/api.ts"), "utf8");
const mockContentSource = fs.readFileSync(path.join(__dirname, "../lib/mockContent.ts"), "utf8");

assert(
  apiSource.includes('apiClient.get("/content/quote-cards", { params: { page_size: 100 } })'),
  "getQuoteCards should request enough quote cards for the full card set"
);

assert(
  apiSource.includes("backgroundImage: c.background_image"),
  "quote card API mapping should expose backgroundImage"
);

assert(
  apiSource.includes("getQuoteBackgroundImage(c.id)") &&
    apiSource.includes("backgroundImage: c.background_image || getQuoteBackgroundImage(c.id)"),
  "quote card API mapping should fall back to local generated PNG backgrounds"
);

assert(
  mockContentSource.includes('backgroundImage: "/content/quote-backgrounds/qc_001.png"'),
  "mock quote cards should preserve generated background images in local mode"
);

assert(
  mockContentSource.includes('backgroundImage: "/content/quote-backgrounds/qc_010.png"'),
  "all visible mock quote cards should include generated background images"
);

console.log("quoteCardsWiring tests passed");

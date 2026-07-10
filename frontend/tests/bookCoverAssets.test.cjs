const fs = require("fs");
const path = require("path");
const assert = require("assert");

const root = path.join(__dirname, "..");
const visualAssets = fs.readFileSync(path.join(root, "lib", "visualAssets.ts"), "utf8");
const catalog = JSON.parse(fs.readFileSync(path.join(root, "lib", "classics_catalog.json"), "utf8"));
const bookIds = catalog.books.map((book) => book.id);

const assertPngAsset = (publicPath) => {
  const assetPath = path.join(root, "public", ...publicPath.split("/").filter(Boolean));
  assert(fs.existsSync(assetPath), `${assetPath} should exist`);
  assert(
    fs.readFileSync(assetPath).subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])),
    `${assetPath} should be a real PNG file`
  );
};

bookIds.forEach((id) => {
  const publicPath = `/agens/books/${id}.png`;
  assertPngAsset(publicPath);
});

assert(
  visualAssets.includes("`/agens/books/${encodeURIComponent(bookId)}.png`"),
  "getBookCoverImage should URL-encode catalog ids and resolve them to Agens PNG covers by convention"
);
assert(
  bookIds.some((id) => encodeURIComponent(id) !== id),
  "catalog fixture should include at least one id that needs URL encoding"
);
assert(!visualAssets.includes("/agens/books/default-classic.svg"), "book covers should not rely on the default SVG fallback");
assert(!/\/agens\/books\/[a-z0-9_-]+\.svg/.test(visualAssets), "legacy SVG book covers should be replaced by Agens PNG covers");

console.log("bookCoverAssets tests passed");

const fs = require("fs");
const path = require("path");
const assert = require("assert");

const viewerSource = fs.readFileSync(
  path.join(__dirname, "../components/content/ComicViewer.tsx"),
  "utf8"
);
const dataSource = fs.readFileSync(path.join(__dirname, "../lib/comicData.ts"), "utf8");
const typesSource = fs.readFileSync(path.join(__dirname, "../lib/types.ts"), "utf8");
const packageSource = fs.readFileSync(path.join(__dirname, "../package.json"), "utf8");
const apiSource = fs.readFileSync(path.join(__dirname, "../lib/api.ts"), "utf8");

[
  "data-comic-reader",
  "data-webtoon-strip",
  "data-comic-panel",
  "data-shot-language",
  "data-knowledge-anchor",
  "data-storyboard-nav",
].forEach((marker) => {
  assert(viewerSource.includes(marker), `ComicViewer should expose ${marker}`);
});

[
  "shot",
  "action",
  "caption",
  "knowledgeAnchor",
  "visualMetaphor",
  "beat",
  "imageUrl",
].forEach((field) => {
  assert(typesSource.includes(field), `ComicPanel should support ${field}`);
});

assert(
  dataSource.includes("styleGuide") && dataSource.includes("characters"),
  "comic data should include a style guide and character bible"
);

assert(
  dataSource.includes("雨停以后") && dataSource.includes("先看风。然后，我们再来。"),
  "xue-er comic should be rewritten as a stronger six-beat script"
);

assert(
  dataSource.includes("/content/comic-panels/xue-er-shi-xi-p01.png"),
  "comic script should reference generated Agens panel images"
);

assert(
  apiSource.includes("api.getComics") || apiSource.includes("getComics"),
  "comic API wiring should be present"
);

assert(
  packageSource.includes("comicExperienceWiring.test.cjs"),
  "npm test should include comic experience wiring checks"
);

console.log("comicExperienceWiring tests passed");

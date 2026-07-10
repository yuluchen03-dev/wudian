const fs = require("fs");
const path = require("path");
const assert = require("assert");

const read = (...parts) => fs.readFileSync(path.join(__dirname, "..", ...parts), "utf8");

const visualAssets = read("lib", "visualAssets.ts");
const sageData = read("lib", "sageData.ts");
const types = read("lib", "types.ts");
const sageChatPage = read("app", "sage-chat", "page.tsx");
const sageChat = read("components", "sage", "SageChat.tsx");
const sageAvatars = read("components", "roundtable", "SageAvatars.tsx");
const sageSpeechCard = read("components", "roundtable", "SageSpeechCard.tsx");
const contentPage = read("app", "content", "page.tsx");
const homePage = read("app", "page.tsx");
const theaterPlayer = read("components", "content", "TheaterPlayer.tsx");

const assertPngAsset = (publicPath) => {
  const assetPath = path.join(__dirname, "..", "public", ...publicPath.split("/").filter(Boolean));
  assert(fs.existsSync(assetPath), `${assetPath} should exist`);
  assert(
    fs.readFileSync(assetPath).subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])),
    `${assetPath} should be a real PNG file`
  );
};

[
  "portraitImage?: string",
  "sceneImage?: string",
  "coverImage?: string",
  "portraitImage?: string",
].forEach((snippet) => {
  assert(types.includes(snippet), `types should expose visual field ${snippet}`);
});

[
  "confucius",
  "mencius",
  "wang_yangming",
  "laozi",
  "mozi",
  "hanfeizi",
  "li_bai",
  "su_shi",
  "fan_zhongyan",
  "wang_anshi",
  "zhuge_liang",
].forEach((id) => {
  assert(visualAssets.includes(`${id}: {`), `visualAssets should define ${id}`);
  assert(sageData.includes(`...sageVisuals.${id}`), `mockSages should attach visuals for ${id}`);
  assert(
    visualAssets.includes(`portraitImage: "/agens/sages/portraits/${id}.png"`),
    `${id} portrait should use an Agens-generated raster PNG`
  );
  assert(
    visualAssets.includes(`sceneImage: "/agens/sages/scenes/${id}.png"`),
    `${id} scene should use an Agens-generated raster PNG`
  );
  [
    path.join(__dirname, "..", "public", "agens", "sages", "portraits", `${id}.png`),
    path.join(__dirname, "..", "public", "agens", "sages", "scenes", `${id}.png`),
  ].forEach((assetPath) => {
    assert(fs.existsSync(assetPath), `${assetPath} should exist`);
    assert(
      fs.readFileSync(assetPath).subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])),
      `${assetPath} should be a real PNG file`
    );
  });
});

assert(!visualAssets.includes("/agens/sages/portraits/confucius.svg"), "sage portraits should not use SVG placeholders");
assert(!visualAssets.includes("/agens/sages/scenes/confucius.svg"), "sage scenes should not use SVG placeholders");

[
  "pageBackgrounds",
  "featuredBookCoverImages",
  "theaterCoverImages",
  "theaterRolePortraitImages",
].forEach((snippet) => {
  assert(visualAssets.includes(snippet), `visualAssets should export ${snippet}`);
});

["th_001", "th_002", "th_003", "th_004", "th_005", "th_006"].forEach((id) => {
  const publicPath = `/agens/content/theater-covers/${id}.png`;
  assert(visualAssets.includes(`${id}: "${publicPath}"`), `${id} theater cover should use an Agens PNG`);
  assertPngAsset(publicPath);
});

[
  "th_001:0",
  "th_001:1",
  "th_002:0",
  "th_002:1",
  "th_003:0",
  "th_003:1",
  "th_003:2",
  "th_004:0",
  "th_004:1",
  "th_005:0",
  "th_005:1",
  "th_005:2",
  "th_006:0",
  "th_006:1",
].forEach((key) => {
  const [theaterId, roleIndex] = key.split(":");
  const publicPath = `/agens/content/theater-roles/${theaterId}_role_${String(Number(roleIndex) + 1).padStart(2, "0")}.png`;
  assert(visualAssets.includes(`"${key}": "${publicPath}"`), `${key} theater role should use an Agens PNG`);
  assertPngAsset(publicPath);
});

assert(!visualAssets.includes("/agens/content/theater-covers/th_001.svg"), "theater covers should not use SVG placeholders");
assert(!visualAssets.includes("/agens/content/theater-roles/th_001_role_01.svg"), "theater roles should not use SVG placeholders");

[
  "sage.sceneImage",
  "sage.portraitImage",
  "backgroundImage",
].forEach((snippet) => {
  assert(sageChatPage.includes(snippet), `sage-chat page should render ${snippet}`);
});

[
  "sage.portraitImage",
  "backgroundImage",
].forEach((snippet) => {
  assert(sageChat.includes(snippet), `SageChat should render ${snippet}`);
  assert(sageAvatars.includes(snippet), `SageAvatars should render ${snippet}`);
});

assert(sageSpeechCard.includes("sage.portraitImage"), "roundtable speech cards should render sage portraits");
assert(homePage.includes("pageBackgrounds.home"), "home page should use a page background");
assert(homePage.includes("getBookCoverImage"), "home book cards should use cover images");
assert(contentPage.includes("pageBackgrounds.content"), "content page should use a page background");
assert(theaterPlayer.includes("theater.coverImage"), "theater player should use theater cover images");
assert(theaterPlayer.includes("role.portraitImage"), "theater player should use role portraits");

console.log("visualAssetsWiring tests passed");

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const read = (file) =>
  fs.readFileSync(path.join(__dirname, "..", file), "utf8");

const page = read("app/reader/page.tsx");
const view = read("components/reader/ReadingView.tsx");
const selector = read("components/reader/ChapterSelector.tsx");
const imageSource = read("components/reader/ImageSourceLink.tsx");
const dialogFocusPath = path.join(__dirname, "..", "lib", "useDialogFocus.ts");
assert.ok(fs.existsSync(dialogFocusPath), "reader dialogs should share a focus-management hook");
const dialogFocus = fs.existsSync(dialogFocusPath) ? fs.readFileSync(dialogFocusPath, "utf8") : "";
const css = read("app/globals.css");
const pkg = read("package.json");

assert.match(
  page,
  /api\.getChapter\(firstChapter\.id\)/,
  "the initial chapter summary must be resolved to full chapter detail"
);
assert.match(
  page,
  /chapterLoading/,
  "the reader page should expose chapter loading state"
);
assert.match(
  page,
  /chapterError/,
  "the reader page should expose chapter error state"
);
assert.match(
  page,
  /const bookRequestRef = useRef\(0\)/,
  "book loads should use a request identity independent from chapter switches"
);
assert.match(
  page,
  /chapterRequestRef\.current \+= 1;[\s\S]*setCurrentChapter\(null\);[\s\S]*setProgress\(null\);/,
  "changing books should invalidate stale chapter requests and progress"
);
assert.match(
  page,
  /bookRequestId === bookRequestRef\.current[\s\S]*setProgress\(data\)/,
  "progress responses should only update the active book"
);
assert.match(
  page,
  /const bookTitle = mockBooks\.find\(\(book\) => book\.id === bookId\)\?\.title \?\? "经典"/,
  "the reader should resolve the selected catalog book title"
);
assert.match(page, /bookTitle=\{bookTitle\}/, "the selected book title should reach the reading view");

[
  "data-reader-shell",
  "data-reader-progress",
  "data-reader-passage",
].forEach((marker) => {
  assert(view.includes(marker), `ReadingView should expose ${marker}`);
});

const shellClass = view.match(
  /data-reader-shell[\s\S]{0,120}?className="([^"]+)"/
);
assert(shellClass, "ReadingView should define a reader shell class");
assert(
  shellClass[1].includes("overflow-clip"),
  "the reader shell should clip rounded content without trapping the sticky toolbar"
);
assert(
  !shellClass[1].includes("overflow-hidden"),
  "the reader shell should not use overflow-hidden around the sticky toolbar"
);

assert.match(view, /本章已读/, "the reader should show a completed chapter state");
assert.match(view, /本典正文尚未收录/, "an empty catalog book should show a meaningful reader state");
assert.match(
  view,
  /scrollIntoView\(\{ behavior: reduceMotion \? "auto" : "smooth", block: "start" \}\)/,
  "chapter navigation should honor reduced-motion preferences"
);
assert.match(
  css,
  /\.dark \.reader-paper\s*\{[\s\S]*background-color:\s*rgba\(28, 25, 23, 0\.98\)/,
  "the reader paper should switch to the dark surface when dark mode is active"
);
assert.match(
  selector,
  /aria-label="打开章节目录"/,
  "the chapter directory trigger should have an accessible label"
);
assert.doesNotMatch(selector, /《论语》/, "the chapter drawer should not hard-code a single book title");
assert.match(selector, /《\{bookTitle\}》/, "the chapter drawer should render the selected book title");
assert.match(
  view,
  /h-11 min-w-11 cursor-pointer items-center justify-center/,
  "reader font-size buttons should meet the 44px touch-target minimum"
);
assert.match(
  view,
  /<Type size=\{16\} className="mx-2 hidden shrink-0 text-ink-400 sm:block"/,
  "the decorative type icon should not crowd narrow mobile toolbars"
);
assert.match(
  imageSource,
  /className="flex h-11 items-center/,
  "the reader image-source control should meet the 44px touch-target minimum"
);
assert.match(
  imageSource,
  /aria-label=\{label\}/,
  "the compact image-source control should keep an accessible name"
);
assert.match(
  imageSource,
  /role="dialog"[\s\S]*aria-modal="true"/,
  "the image-source overlay should expose dialog semantics"
);
assert.match(
  imageSource,
  /max-h-\[calc\(100dvh-2rem\)\][\s\S]*overflow-y-auto/,
  "the image-source dialog should stay within the mobile viewport"
);
assert.match(
  imageSource,
  /import \{ createPortal \} from "react-dom";[\s\S]*createPortal\(/,
  "the image-source dialog should escape the sticky toolbar containing block"
);
assert.match(
  imageSource,
  /aria-label="关闭古籍影像弹窗"/,
  "the image-source dialog close button should have an accessible name"
);
assert.match(dialogFocus, /event\.key === "Escape"/, "reader dialogs should close with Escape");
assert.match(dialogFocus, /event\.key !== "Tab"/, "reader dialogs should trap Tab navigation");
assert.match(dialogFocus, /triggerRef\.current\?\.focus\(\)/, "reader dialogs should restore trigger focus");
assert.match(imageSource, /useDialogFocus/, "the image-source dialog should use shared focus management");
assert.match(selector, /useDialogFocus/, "the chapter drawer should use shared focus management");
assert.match(selector, /createPortal\(/, "the chapter drawer should escape the sticky toolbar containing block");
assert.match(
  pkg,
  /readerExperience\.test\.cjs/,
  "the default frontend test suite should include reader regression checks"
);

console.log("readerExperience tests passed");

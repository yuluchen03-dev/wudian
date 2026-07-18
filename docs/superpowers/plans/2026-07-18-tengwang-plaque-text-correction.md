# Tengwang Plaque Text Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the malformed plaque glyphs in the Tengwang Pavilion hero asset with exact “滕王阁” and “瑰伟绝特” text while preserving the building, transparency, layout, and curtain interaction.

**Architecture:** Keep the original PNG untouched and generate a versioned corrected sibling. A deterministic Pillow script repaints only the two inner plaque surfaces, renders exact Chinese strings with an installed calligraphic font, preserves the 1280×823 RGBA canvas, and writes identifying PNG metadata. The frontend switches its existing centralized asset constant to the corrected file.

**Tech Stack:** Python 3, Pillow 12, PNG/RGBA, Next.js 14, Node.js assertion tests

---

## File Map

- Create `frontend/scripts/correct_tengwang_plaques.py`: deterministic plaque cleanup and exact text renderer.
- Create `frontend/public/agens/content/tengwang-ge-xu/pavilion-corrected.png`: generated production asset.
- Modify `frontend/lib/visualAssets.ts`: point `tengwangPavilion` to the corrected asset.
- Modify `frontend/tests/visualAssetsWiring.test.cjs`: require the corrected path, real PNG, and exact script strings.

### Task 1: Add the corrected-asset contract

**Files:**
- Modify: `frontend/tests/visualAssetsWiring.test.cjs:137`
- Test: `frontend/tests/visualAssetsWiring.test.cjs`

- [ ] **Step 1: Change the expected Tengwang asset path**

Replace the existing Tengwang assertion block with:

```js
const tengwangPavilionPath = "/agens/content/tengwang-ge-xu/pavilion-corrected.png";
assert(
  visualAssets.includes(`export const tengwangPavilion = "${tengwangPavilionPath}";`),
  "visualAssets should export the corrected Tengwang Pavilion image"
);
assertPngAsset(tengwangPavilionPath);
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
node tests/visualAssetsWiring.test.cjs
```

Working directory: `frontend`

Expected: FAIL because `visualAssets.ts` still references `pavilion.png` and `pavilion-corrected.png` does not exist.

### Task 2: Generate exact plaque text and switch the asset

**Files:**
- Create: `frontend/scripts/correct_tengwang_plaques.py`
- Create: `frontend/public/agens/content/tengwang-ge-xu/pavilion-corrected.png`
- Modify: `frontend/lib/visualAssets.ts:69`
- Modify: `frontend/tests/visualAssetsWiring.test.cjs:137`
- Test: `frontend/tests/visualAssetsWiring.test.cjs`

- [ ] **Step 1: Add exact-text source assertions**

Add near the Tengwang asset assertions:

```js
const tengwangPlaqueRenderer = read("scripts", "correct_tengwang_plaques.py");
assert(tengwangPlaqueRenderer.includes('"滕王阁"'), "renderer should use exact main plaque text");
assert(tengwangPlaqueRenderer.includes('"瑰伟绝特"'), "renderer should use exact lower plaque text");
assert(tengwangPlaqueRenderer.includes("PngInfo"), "renderer should write plaque metadata");
```

- [ ] **Step 2: Create the deterministic renderer**

Create `frontend/scripts/correct_tengwang_plaques.py`:

```python
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "agens" / "content" / "tengwang-ge-xu" / "pavilion.png"
OUTPUT = ROOT / "public" / "agens" / "content" / "tengwang-ge-xu" / "pavilion-corrected.png"
FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\STXINGKA.TTF"),
    Path(r"C:\Windows\Fonts\STKAITI.TTF"),
    Path(r"C:\Windows\Fonts\simkai.ttf"),
)


def plaque_texture(size: tuple[int, int], seed: int) -> Image.Image:
    width, height = size
    rng = random.Random(seed)
    texture = Image.new("RGBA", size)
    pixels = texture.load()
    for y in range(height):
        vertical = int(5 * (y / max(height - 1, 1)))
        for x in range(width):
            grain = rng.randint(-5, 5)
            pixels[x, y] = (
                max(5, 13 + grain),
                max(9, 20 + vertical + grain),
                max(14, 31 + vertical + grain),
                255,
            )
    return texture.filter(ImageFilter.GaussianBlur(0.65))


def fit_font(text: str, max_width: int, max_height: int, preferred_size: int) -> ImageFont.FreeTypeFont:
    font_path = next((path for path in FONT_CANDIDATES if path.exists()), None)
    if font_path is None:
        raise FileNotFoundError("No supported Chinese calligraphy font was found")
    size = preferred_size
    while size >= 12:
        font = ImageFont.truetype(str(font_path), size)
        left, top, right, bottom = font.getbbox(text, stroke_width=1)
        if right - left <= max_width and bottom - top <= max_height:
            return font
        size -= 1
    raise ValueError(f"Unable to fit plaque text: {text}")


def render_plaque(
    image: Image.Image,
    box: tuple[int, int, int, int],
    text: str,
    preferred_size: int,
    seed: int,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    image.paste(plaque_texture((width, height), seed), (left, top))

    font = fit_font(text, width - 18, height - 12, preferred_size)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bounds = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    x = (width - text_width) / 2 - bounds[0]
    y = (height - text_height) / 2 - bounds[1] - 1
    draw.text((x + 1, y + 2), text, font=font, fill=(74, 45, 14, 190), stroke_width=1)
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(219, 173, 71, 255),
        stroke_width=1,
        stroke_fill=(151, 101, 34, 255),
    )
    image.alpha_composite(layer, (left, top))


def main() -> None:
    image = Image.open(SOURCE).convert("RGBA")
    if image.size != (1280, 823):
        raise ValueError(f"Unexpected pavilion dimensions: {image.size}")

    render_plaque(image, (528, 232, 793, 318), "滕王阁", 72, 20260718)
    render_plaque(image, (577, 478, 741, 506), "瑰伟绝特", 27, 20260719)

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("PlaqueText", "滕王阁|瑰伟绝特")
    image.save(OUTPUT, pnginfo=metadata, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Generate the corrected PNG**

Run:

```powershell
& 'C:\Users\hacjr\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\correct_tengwang_plaques.py
```

Working directory: `frontend`

Expected: prints the absolute path to `pavilion-corrected.png` and exits 0.

- [ ] **Step 4: Switch the centralized asset reference**

Change `frontend/lib/visualAssets.ts` to:

```ts
export const tengwangPavilion = "/agens/content/tengwang-ge-xu/pavilion-corrected.png";
```

- [ ] **Step 5: Run the focused asset tests**

Run:

```powershell
node tests/visualAssetsWiring.test.cjs
node tests/tengwangExperienceWiring.test.cjs
```

Working directory: `frontend`

Expected: both scripts print their passed message and exit 0.

- [ ] **Step 6: Inspect the generated asset at original resolution**

Open `frontend/public/agens/content/tengwang-ge-xu/pavilion-corrected.png` with the local image viewer and verify:

- Main plaque reads exactly `滕王阁`.
- Lower plaque reads exactly `瑰伟绝特`.
- Gold text is centered and legible.
- No pixels outside the two inner plaque rectangles visibly change.
- Transparent corners remain transparent.

- [ ] **Step 7: Commit the generated asset and wiring**

```powershell
git add frontend/scripts/correct_tengwang_plaques.py frontend/public/agens/content/tengwang-ge-xu/pavilion-corrected.png frontend/lib/visualAssets.ts frontend/tests/visualAssetsWiring.test.cjs
git commit -m "fix: correct tengwang pavilion plaque text"
```

### Task 3: Verify the complete experience

**Files:**
- Verify: `frontend/public/agens/content/tengwang-ge-xu/pavilion-corrected.png`
- Verify: `frontend/components/content/tengwang/TengwangExperience.tsx`

- [ ] **Step 1: Run the full frontend test suite**

Run:

```powershell
npm.cmd test
```

Working directory: `frontend`

Expected: all 21 test scripts pass.

- [ ] **Step 2: Run a clean production build**

Run:

```powershell
npm.cmd run build:clean
```

Working directory: `frontend`

Expected: Next.js compiles, checks types, and generates all static pages with exit code 0.

- [ ] **Step 3: Check the final diff**

Run:

```powershell
git show --check --oneline HEAD
```

Expected: the plaque correction commit is shown and the command exits 0 without whitespace errors.

- [ ] **Step 4: Start the development server and verify the real page**

Start `npm.cmd run dev:clean` from `frontend`, then open:

```text
http://127.0.0.1:3000/content/tengwang-ge-xu
```

Expected in the browser:

- The two plaque strings are correct and readable.
- The pavilion is unchanged outside the plaque interiors.
- `canvas[data-curtain-canvas]` mounts below the pavilion.
- The vertical text curtain remains visible and responds to pointer movement.
- Browser console contains no new errors.

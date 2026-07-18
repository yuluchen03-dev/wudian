from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "agens" / "content" / "tengwang-ge-xu" / "pavilion.png"
OUTPUT = (
    ROOT
    / "public"
    / "agens"
    / "content"
    / "tengwang-ge-xu"
    / "pavilion-corrected.png"
)
FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\STKAITI.TTF"),
    Path(r"C:\Windows\Fonts\simkai.ttf"),
    Path(r"C:\Windows\Fonts\STXINGKA.TTF"),
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


def fit_font(
    text: str, max_width: int, max_height: int, preferred_size: int
) -> ImageFont.FreeTypeFont:
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

    font = fit_font(text, width - 18, height - 4, preferred_size)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bounds = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    x = (width - text_width) / 2 - bounds[0]
    y = (height - text_height) / 2 - bounds[1] - 1
    draw.text(
        (x + 1, y + 2),
        text,
        font=font,
        fill=(74, 45, 14, 190),
        stroke_width=1,
    )
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
    original_alpha = image.getchannel("A")

    render_plaque(image, (528, 232, 793, 318), "滕王阁", 72, 20260718)
    render_plaque(image, (577, 478, 741, 506), "瑰伟绝特", 27, 20260719)
    image.putalpha(original_alpha)

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("PlaqueText", "滕王阁|瑰伟绝特")
    image.save(OUTPUT, pnginfo=metadata, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = Path(__file__).with_name("一问见古今-TRAE大赛创意提案.html")

IMAGES = {
    "confucius": (ROOT / "frontend/public/agens/sages/portraits/confucius.png", (360, 360), 78),
    "mencius": (ROOT / "frontend/public/agens/sages/portraits/mencius.png", (360, 360), 78),
    "laozi": (ROOT / "frontend/public/agens/sages/portraits/laozi.png", (360, 360), 78),
    "lunyu": (ROOT / "frontend/public/agens/books/lunyu.png", (720, 480), 76),
    "mengzi": (ROOT / "frontend/public/agens/books/mengzi.png", (720, 480), 76),
    "daodejing": (ROOT / "frontend/public/agens/books/daodejing.png", (720, 480), 76),
}


def webp_data_uri(source: Path, size: tuple[int, int], quality: int) -> str:
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        fitted = ImageOps.fit(rgb, size, method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        fitted.save(output, format="WEBP", quality=quality, method=6)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{encoded}"


def embed_images() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    for key, (source, size, quality) in IMAGES.items():
        if not source.exists():
            raise FileNotFoundError(f"Missing source image: {source}")

        pattern = re.compile(
            rf'(<img\b(?=[^>]*\bdata-image-key="{re.escape(key)}")[^>]*\bsrc=")[^"]*(")',
            re.IGNORECASE,
        )
        html, count = pattern.subn(
            lambda match: f"{match.group(1)}{webp_data_uri(source, size, quality)}{match.group(2)}",
            html,
            count=1,
        )
        if count != 1:
            raise RuntimeError(f"Expected one image marker for {key}, found {count}")

    HTML_PATH.write_text(html, encoding="utf-8", newline="\n")
    print(f"Embedded {len(IMAGES)} WebP images into {HTML_PATH.name}")
    print(f"Final HTML size: {HTML_PATH.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    embed_images()

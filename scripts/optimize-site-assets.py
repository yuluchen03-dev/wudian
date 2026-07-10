from pathlib import Path
import sys

from PIL import Image


root = Path(sys.argv[1])
converted = 0

for source in root.rglob("*.png"):
    target = source.with_suffix(".webp")
    with Image.open(source) as image:
        image.convert("RGBA").save(target, "WEBP", quality=82, method=6)
    source.unlink()
    converted += 1

for path in root.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css", ".json", ".txt"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if ".png" in text:
        path.write_text(text.replace(".png", ".webp"), encoding="utf-8")

print(f"[site-assets] converted {converted} PNG assets to WebP")

import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402

QUOTE_CARDS_FILE = ROOT / "data" / "processed" / "quote_cards.json"
OUTPUT_DIR = ROOT / "frontend" / "public" / "content" / "quote-backgrounds"
PUBLIC_PREFIX = "/content/quote-backgrounds"


STYLE_NOTES = {
    "ink_wash": "misty ink wash landscape, rice paper texture, sparse brushwork",
    "gold_seal": "warm antique gold seal aesthetic, refined Chinese editorial illustration",
    "bamboo_scroll": "bamboo slips, oil lamp, carved texture, quiet study room atmosphere",
    "moonlight": "deep moonlit blue, silver ink highlights, contemplative night scene",
    "cloud_mist": "soft cloud and mountain mist, pale mineral pigments, airy negative space",
}


def _image_bytes(item: dict) -> bytes:
    prompt = (
        "Create a refined Chinese classical background illustration for a quote card. "
        f"Scene: {item.get('image_keyword', '')}. "
        f"Visual style: {STYLE_NOTES.get(item.get('style'), STYLE_NOTES['ink_wash'])}. "
        "Portrait card composition, 3:4 aspect ratio, elegant but low-contrast, "
        "leave a calm central reading area for Chinese quote text, no text, no watermark, "
        "no modern UI, no logos, no harsh black shadows."
    )
    api_key = settings.AGNES_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("AGNES_API_KEY is not configured")

    url = settings.AGNES_BASE_URL.rstrip("/") + "/images/generations"
    payload = {
        "model": settings.AGNES_IMAGE_MODEL,
        "prompt": prompt,
        "size": "768x1024",
        "return_base64": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=180) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.is_error:
            raise RuntimeError(f"Agens image request failed: {response.status_code} {response.text[:500]}")
        body = response.json()

    data = (body.get("data") or [])[0]
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    if data.get("url"):
        with httpx.Client(timeout=180) as client:
            image_response = client.get(data["url"])
            image_response.raise_for_status()
            return image_response.content
    raise RuntimeError(f"Agens image response did not include image data for {item['id']}")


def _extension(content: bytes) -> str:
    if content.startswith(b"\xff\xd8"):
        return ".jpg"
    if content.startswith(b"\x89PNG"):
        return ".png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return ".webp"
    guessed = mimetypes.guess_extension("image/png")
    return guessed or ".png"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agens AI backgrounds for quote cards.")
    parser.add_argument("--limit", type=int, default=0, help="Generate only the first N missing cards.")
    parser.add_argument("--force", action="store_true", help="Regenerate existing images.")
    args = parser.parse_args()

    cards = json.loads(QUOTE_CARDS_FILE.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    for item in cards:
        existing = item.get("background_image")
        if existing and not args.force and (ROOT / "frontend" / "public" / existing.lstrip("/")).exists():
            continue
        if args.limit and generated >= args.limit:
            break

        content = _image_bytes(item)
        ext = _extension(content)
        filename = f"{item['id']}{ext}"
        output = OUTPUT_DIR / filename
        output.write_bytes(content)
        item["background_image"] = f"{PUBLIC_PREFIX}/{filename}"
        generated += 1
        print(f"generated {item['id']} -> {item['background_image']}")

        QUOTE_CARDS_FILE.write_text(
            json.dumps(cards, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"generated {generated} quote card backgrounds")


if __name__ == "__main__":
    main()

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

COMICS_FILE = ROOT / "data" / "processed" / "comics.json"
OUTPUT_DIR = ROOT / "frontend" / "public" / "content" / "comic-panels"
PUBLIC_PREFIX = "/content/comic-panels"

NEGATIVE_PROMPT = (
    "low quality, blurry, inconsistent character, changed face, changed hairstyle, "
    "extra limbs, malformed hands, random speech bubbles, gibberish text, fake Chinese characters, "
    "English letters, watermark, logo, signature, panel border chaos, cropped head, "
    "modern objects, photorealistic 3D render, style drift"
)


def _panel_prompt(comic: dict, panel: dict) -> str:
    character_notes = "\n".join(
        f"- {c.get('name', '')}: {c.get('visual_anchor', '')}"
        for c in comic.get("characters", [])
    )
    source_hint = panel.get("image_prompt", "") or panel.get("image_keyword", "")
    source_hint = (
        source_hint
        .replace("生成六格漫画", "生成单格漫画")
        .replace("六格漫画", "单格漫画")
        .replace("第1格", "这一格")
        .replace("第2格", "这一格")
        .replace("第3格", "这一格")
        .replace("第4格", "这一格")
        .replace("第5格", "这一格")
        .replace("第6格", "这一格")
    )
    return (
        "任务：只生成一张中国经典题材漫画单格插图。画面内不要生成任何文字。\n"
        "强制要求：这是一张单一画面，不是整页漫画，不要 2x2/3x2 分格，不要多面板，不要缩略图拼贴，不要重复同一角色。\n"
        "English constraint: one single cinematic comic illustration only, no comic page, no grid, no collage, no multiple panels, no panel borders inside the image.\n"
        f"漫画：{comic.get('title', '')}\n"
        f"原文锚点：{comic.get('classical_source', '')}\n"
        f"统一画风：{comic.get('style_guide', '')}\n"
        f"角色一致性锚点：\n{character_notes}\n"
        f"本格节奏：{panel.get('beat', '')}\n"
        f"场景：{panel.get('scene', '')}\n"
        f"镜头：{panel.get('shot', '')}\n"
        f"动作与情绪：{panel.get('action', '')}；{panel.get('character', '')}，{panel.get('emotion', '')}\n"
        f"视觉隐喻：{panel.get('visual_metaphor', '')}\n"
        f"补充提示：{source_hint}\n"
        "构图要求：单格漫画插图，只有一个连续场景，清晰叙事中心，人物不被裁切，保留上方或下方少量干净留白给后期对白框。\n"
        "文字策略：不要生成中文、英文、题字、招牌、字幕、水印；对白和旁白由前端后期排版。\n"
        f"避免：{NEGATIVE_PROMPT}"
    )


def _image_bytes(comic: dict, panel: dict, size: str) -> bytes:
    api_key = settings.AGNES_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("AGNES_API_KEY is not configured")

    url = settings.AGNES_BASE_URL.rstrip("/") + "/images/generations"
    payload = {
        "model": settings.AGNES_IMAGE_MODEL,
        "prompt": _panel_prompt(comic, panel),
        "size": size,
        "return_base64": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=240) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.is_error:
            raise RuntimeError(f"Agens image request failed: {response.status_code} {response.text[:500]}")
        body = response.json()

    data = (body.get("data") or [])[0]
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    if data.get("url"):
        with httpx.Client(timeout=240) as client:
            image_response = client.get(data["url"])
            image_response.raise_for_status()
            return image_response.content
    raise RuntimeError(f"Agens image response did not include image data for {comic['id']} panel {panel.get('index')}")


def _extension(content: bytes) -> str:
    if content.startswith(b"\xff\xd8"):
        return ".jpg"
    if content.startswith(b"\x89PNG"):
        return ".png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return ".webp"
    return mimetypes.guess_extension("image/png") or ".png"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agens AI images for comic panels.")
    parser.add_argument("--comic-id", default="", help="Generate only one comic id.")
    parser.add_argument("--panel-index", type=int, default=-1, help="Generate only one zero-based panel index.")
    parser.add_argument("--limit", type=int, default=0, help="Generate only the first N missing panels.")
    parser.add_argument("--force", action="store_true", help="Regenerate existing panel images.")
    parser.add_argument("--size", default="1024x1536", help="Agens image size, default portrait panel.")
    args = parser.parse_args()

    comics = json.loads(COMICS_FILE.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    for comic in comics:
        if args.comic_id and comic.get("id") != args.comic_id:
            continue
        for panel in comic.get("panels", []):
            if args.panel_index >= 0 and int(panel.get("index", -1)) != args.panel_index:
                continue
            existing = panel.get("image_url")
            if existing and not args.force and (ROOT / "frontend" / "public" / existing.lstrip("/")).exists():
                continue
            if args.limit and generated >= args.limit:
                break

            content = _image_bytes(comic, panel, args.size)
            ext = _extension(content)
            filename = f"{comic['id']}-p{int(panel.get('index', generated)) + 1:02d}{ext}"
            output = OUTPUT_DIR / filename
            output.write_bytes(content)
            panel["image_url"] = f"{PUBLIC_PREFIX}/{filename}"
            generated += 1
            print(f"generated {comic['id']} panel {panel.get('index')} -> {panel['image_url']}")

            COMICS_FILE.write_text(
                json.dumps(comics, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        if args.limit and generated >= args.limit:
            break

    print(f"generated {generated} comic panel images")


if __name__ == "__main__":
    main()

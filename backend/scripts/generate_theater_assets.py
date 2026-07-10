import argparse
import base64
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402

COVER_DIR = ROOT / "frontend" / "public" / "agens" / "content" / "theater-covers"
ROLE_DIR = ROOT / "frontend" / "public" / "agens" / "content" / "theater-roles"

THEATERS = [
    {
        "id": "th_001",
        "title": "Training after learning",
        "setting": "modern Chinese office onboarding training room",
        "conflict": "a thoughtful mentor pauses a new employee who thinks taking notes means learning is finished",
        "roles": [
            {"name": "mentor manager", "look": "middle-aged Chinese male mentor, calm eyes, warm but firm, business casual"},
            {"name": "new hire", "look": "young Chinese male new employee, energetic, slightly anxious, simple office clothes"},
        ],
    },
    {
        "id": "th_002",
        "title": "Code review humility",
        "setting": "quiet modern software office during code review",
        "conflict": "a senior engineer realizes a junior engineer has written a better solution",
        "roles": [
            {"name": "senior engineer", "look": "middle-aged Chinese male software architect, cardigan, tired but kind eyes"},
            {"name": "junior engineer", "look": "young Chinese developer, focused, modest, clean hoodie or casual shirt"},
        ],
    },
    {
        "id": "th_003",
        "title": "Group assignment fairness",
        "setting": "university dormitory or study room group project meeting",
        "conflict": "students negotiate fair work division and empathy",
        "roles": [
            {"name": "assertive group leader", "look": "outgoing Chinese male college student, sporty casual clothes"},
            {"name": "sharp debater", "look": "Chinese college student with glasses, bookish, articulate"},
            {"name": "quiet contributor", "look": "introverted Chinese college student, gentle and reliable"},
        ],
    },
    {
        "id": "th_004",
        "title": "Reviewing old knowledge",
        "setting": "quiet cafe mentoring session for an experienced employee",
        "conflict": "a seasoned worker returns to foundations and finds new insight",
        "roles": [
            {"name": "experienced employee", "look": "Chinese office worker in their thirties, thoughtful and tired"},
            {"name": "mentor", "look": "older Chinese professional mentor, composed, precise, understated elegance"},
        ],
    },
    {
        "id": "th_005",
        "title": "Startup disagreement",
        "setting": "startup war room with product sketches and tense discussion",
        "conflict": "cofounders disagree without losing respect",
        "roles": [
            {"name": "product founder", "look": "Chinese entrepreneur in dark shirt, intense, practical"},
            {"name": "design founder", "look": "Chinese creative cofounder, refined, independent, calm under pressure"},
            {"name": "operations partner", "look": "Chinese operations lead, observant, balanced, mediating presence"},
        ],
    },
    {
        "id": "th_006",
        "title": "Learning from excellence",
        "setting": "university library or maker lab at night",
        "conflict": "an intern sees excellent work and decides to improve themselves",
        "roles": [
            {"name": "intern", "look": "young Chinese intern, earnest, carrying notebook or laptop bag, no visible text"},
            {"name": "senior engineer role model", "look": "top Chinese engineer, calm, precise, quietly inspiring"},
        ],
    },
]

NEGATIVE = (
    "no text, no Chinese characters, no English letters, no code on screen, no readable signage, no logos, "
    "no watermark, no subtitles, no speech bubbles, no cartoon, no anime, no vector art, no illustration, "
    "no video player controls, no interface overlay, no black UI bars, no timestamps, "
    "no distorted hands, no extra fingers, no duplicate faces, no fake UI text"
)


def _request_image(prompt: str, size: str) -> bytes:
    api_key = settings.AGNES_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("AGNES_API_KEY or OPENAI_API_KEY is not configured")

    url = settings.AGNES_BASE_URL.rstrip("/") + "/images/generations"
    payload = {
        "model": settings.AGNES_IMAGE_MODEL,
        "prompt": prompt,
        "size": size,
        "return_base64": True,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    last_error = ""
    with httpx.Client(timeout=240) as client:
        for attempt in range(1, 4):
            try:
                response = client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < 3:
                    time.sleep(8 * attempt)
                    continue
                raise RuntimeError(f"Agens image request failed: {last_error}") from exc
            if not response.is_error:
                body = response.json()
                break
            last_error = f"{response.status_code} {response.text[:500]}"
            if response.status_code >= 500 and attempt < 3:
                time.sleep(8 * attempt)
                continue
            raise RuntimeError(f"Agens image request failed: {last_error}")
        else:
            raise RuntimeError(f"Agens image request failed: {last_error}")

    data = (body.get("data") or [])[0]
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    if data.get("url"):
        with httpx.Client(timeout=240) as client:
            image_response = client.get(data["url"])
            image_response.raise_for_status()
            return image_response.content
    raise RuntimeError("Agens image response did not include image data")


def _cover_prompt(theater: dict) -> str:
    role_names = ", ".join(role["name"] for role in theater["roles"])
    return (
        "Use case: photorealistic-natural\n"
        "Asset type: theater card cover background for a web app\n"
        f"Primary request: cinematic live-action still for a short educational theater scene, {theater['title']}.\n"
        f"Scene/backdrop: {theater['setting']}.\n"
        f"Characters: {role_names}.\n"
        f"Dramatic conflict: {theater['conflict']}.\n"
        "Style/medium: photorealistic Chinese drama still, natural faces, real fabric, quiet premium lighting, "
        "subtle classical Chinese moral-drama atmosphere without ancient costume cosplay.\n"
        "Composition/framing: wide 3:2 scene, 2-3 people in clear relation, no text, enough clean negative space for UI overlays.\n"
        "Text control: screens, notebooks, boards, posters, signs, and papers must be blank, out of focus, turned away, or omitted.\n"
        f"Avoid: {NEGATIVE}."
    )


def _role_prompt(theater: dict, role: dict) -> str:
    return (
        "Use case: photorealistic-natural\n"
        "Asset type: square character portrait for a theater role avatar\n"
        f"Primary request: photorealistic live-action portrait of the role '{role['name']}' from an educational theater scene.\n"
        f"Role look: {role['look']}.\n"
        f"Scene context: {theater['setting']}.\n"
        "Style/medium: cinematic Chinese character portrait, realistic human face, natural expression, modern clothing, "
        "subtle classical restraint in lighting and posture.\n"
        "Composition/framing: centered bust portrait, shoulders visible, clean background, no text, no logo.\n"
        f"Avoid: {NEGATIVE}."
    )


def _write_png(path: Path, content: bytes) -> None:
    if not content.startswith(b"\x89PNG"):
        raise RuntimeError(f"{path.name} was not returned as PNG data")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agens AI photoreal theater covers and role portraits.")
    parser.add_argument("--only", default="", help="Generate one theater id only.")
    parser.add_argument("--asset", choices=["all", "cover", "roles"], default="all")
    parser.add_argument("--force", action="store_true", help="Regenerate existing files.")
    parser.add_argument("--cover-size", default="1536x1024")
    parser.add_argument("--role-size", default="1024x1024")
    args = parser.parse_args()

    generated = 0
    for theater in THEATERS:
        if args.only and theater["id"] != args.only:
            continue

        if args.asset in ("all", "cover"):
            output = COVER_DIR / f"{theater['id']}.png"
            if args.force or not output.exists():
                _write_png(output, _request_image(_cover_prompt(theater), args.cover_size))
                generated += 1
                print(f"generated {theater['id']} cover -> {output.relative_to(ROOT)}")

        if args.asset in ("all", "roles"):
            for index, role in enumerate(theater["roles"], start=1):
                output = ROLE_DIR / f"{theater['id']}_role_{index:02d}.png"
                if args.force or not output.exists():
                    _write_png(output, _request_image(_role_prompt(theater, role), args.role_size))
                    generated += 1
                    print(f"generated {theater['id']} role {index} -> {output.relative_to(ROOT)}")

    print(f"generated {generated} theater assets")


if __name__ == "__main__":
    main()

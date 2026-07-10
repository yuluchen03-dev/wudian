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

PORTRAIT_DIR = ROOT / "frontend" / "public" / "agens" / "sages" / "portraits"
SCENE_DIR = ROOT / "frontend" / "public" / "agens" / "sages" / "scenes"

SAGES = [
    {
        "id": "confucius",
        "name": "Confucius",
        "period": "late Spring and Autumn period, represented through later ritual portrait conventions",
        "visual_reference": (
            "traditional Confucius portraits: much facial hair, formal official garments, seated or upright ritual bearing, "
            "standing or seated ritual bearing, hands gathered around a plain scepter-tablet or respectfully folded"
        ),
        "persona": "an elderly sage-teacher with broad forehead, full beard, placid expression, and restrained ritual dignity",
        "costume": "dark-edged formal robe, blue-black ritual cap or cloth headpiece, wide sleeves, no imperial crown",
        "setting": "Temple of Confucius academy courtyard and ritual hall exterior, disciples far in the background, no desks or documents",
    },
    {
        "id": "mencius",
        "name": "Mencius",
        "period": "Warring States period, no secure life portrait; use restrained Confucian scholar iconography",
        "visual_reference": "later Confucian sage portraits: mature scholar, simple cap, cross-collar robe, moral seriousness",
        "persona": "a middle-aged to elderly Confucian debater, upright posture, composed but forceful eyes, trimmed beard",
        "costume": "plain deep robe with cross collar, modest Warring States-style cap, no Song or Ming official wings",
        "setting": "Warring States lecture courtyard with plain wood pillars, mountain mist beyond, austere moral atmosphere, no desks or documents",
    },
    {
        "id": "wang_yangming",
        "name": "Wang Yangming",
        "period": "Ming dynasty",
        "visual_reference": "Ming/Qing portraits of Wang Yangming: tall black official hat, long dark beard, scholar-official face",
        "persona": "a refined Ming official-scholar and commander with focused eyes, long beard, calm concentration",
        "costume": "Ming official or scholar robe, tall black futou-like hat with side flaps, historically grounded Ming textiles",
        "setting": "Ming dynasty official courtyard beside a quiet military pavilion, mountain view, no maps or documents visible",
    },
    {
        "id": "laozi",
        "name": "Laozi",
        "period": "ancient Zhou dynasty, represented through later Daoist and Three Teachings iconography",
        "visual_reference": "Laozi in Three Teachings paintings: elderly sage, warm smile, travel staff, no open scripture scroll",
        "persona": "a serene very old Daoist sage with long white beard, high brow, gentle smile, and penetrating calm",
        "costume": "simple ancient robe, soft cloth cap, travel cloak, travel staff, no priestly fantasy armor, no open scroll",
        "setting": "mountain pass at dusk with pine trees, mist, and a simple travel staff, no scrolls or texts visible",
    },
    {
        "id": "mozi",
        "name": "Mozi",
        "period": "Warring States period, no secure life portrait; use austere Mohist scholar-engineer tradition",
        "visual_reference": "common Mozi line portraits: plain robe, cloth headwrap or simple cap, angular face, practical bearing",
        "persona": "a practical philosopher-engineer in plain dark robes, lean face, short beard, compassionate austerity",
        "costume": "unadorned Warring States robe, dark sash, cloth headwrap, no court luxury",
        "setting": "defensive city wall workshop exterior with wooden mechanisms, ropes, and measuring tools, no plans or documents visible",
    },
    {
        "id": "hanfeizi",
        "name": "Han Feizi",
        "period": "Warring States period, no secure life portrait; use later Han Fei scholar portrait conventions",
        "visual_reference": "traditional Han Fei portraits: stern brows, thin moustache and beard, simple headcloth, legalist severity",
        "persona": "a sharp Legalist thinker with cool expression, stern brows, aristocratic restraint, narrow beard",
        "costume": "plain Warring States aristocratic scholar robe, dark collar, tied headcloth, no Qin imperial costume",
        "setting": "stern Han state court corridor with bronze vessels and orderly wooden architecture, no books or documents visible",
    },
    {
        "id": "li_bai",
        "name": "Li Bai",
        "period": "Tang dynasty",
        "visual_reference": "Li Bai Strolling by Liang Kai: side-facing wandering poet, raised head, chanting, simple flowing robe",
        "persona": "a charismatic Tang poet, lean and free-spirited, head slightly lifted as if chanting, bright eyes",
        "costume": "flowing Tang scholar robe, soft topknot or cloth cap, wine gourd or cup, no later official hat",
        "setting": "moonlit riverside pavilion, wine cup, loose sleeves, distant mountains, poetic walking posture, no writing surfaces",
    },
    {
        "id": "su_shi",
        "name": "Su Shi",
        "period": "Northern Song dynasty",
        "visual_reference": "Portrait of Su Shi and Red Cliff iconography: seated on a rock, one hand raised to beard, calm scholar",
        "persona": "a warm Northern Song scholar-poet, broad-minded, slightly rounded face, subtle humorous eyes, hand near beard",
        "costume": "Song literati robe, simple black Dongpo-style cap or scholar headwear, no Ming/Qing official robe",
        "setting": "Red Cliff riverside after rain, rock seat, tea steam, garden and river mist beyond, no paper or calligraphy",
    },
    {
        "id": "fan_zhongyan",
        "name": "Fan Zhongyan",
        "period": "Northern Song dynasty",
        "visual_reference": "Song official portraits of Fan Zhongyan: formal court robe, black long-winged official hat, holding tablet",
        "persona": "a principled Northern Song statesman with solemn compassion, steady gaze, full official gravity",
        "costume": "Song court robe with long-winged black official hat and scepter-tablet, not Qing queue or Ming hat",
        "setting": "Northern Song government terrace overlooking river and city walls, formal architecture, no desk or documents",
    },
    {
        "id": "wang_anshi",
        "name": "Wang Anshi",
        "period": "Northern Song dynasty",
        "visual_reference": "Nanxun Hall and later portraits of Wang Anshi: Song minister, black official hat, composed reformer",
        "persona": "a determined Northern Song reformer-official with intense eyes, short beard, inward firmness",
        "costume": "Song official robe, black long-winged official hat, restrained court colors, no Qing or fantasy elements",
        "setting": "Northern Song reform office courtyard with farm tools in the background and late afternoon sunlight, no account books or papers",
    },
    {
        "id": "zhuge_liang",
        "name": "Zhuge Liang",
        "period": "Three Kingdoms period",
        "visual_reference": "traditional Zhuge Liang portraits: pale scholar robe, black scholar hat, white feather fan, composed strategist",
        "persona": "a composed strategist-scholar with feather fan, calm face, thin moustache and beard, vigilant intelligence",
        "costume": "scholar robe in pale green or light neutral tones, black guan-style hat, white feather fan, no armor",
        "setting": "Three Kingdoms campaign tent exterior with lanterns, banners without marks, feather fan, and distant mountain wind, no maps or writing",
    },
]

NEGATIVE = (
    "no text, no Chinese characters, no calligraphy, no watermark, no logo, no signature, "
    "no plaques, no signboards, no open scrolls, no open books, no papers in the foreground, "
    "no paper with marks, no fake characters, no written bamboo slips, no banners, no flags with marks, "
    "no anime, no cartoon, no vector art, no flat illustration, no plastic skin, no modern clothing, "
    "no eyeglasses, no microphones, no fantasy armor, no inaccurate Western robes, no duplicate faces"
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
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

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


def _portrait_prompt(sage: dict) -> str:
    return (
        "Use case: historical-scene\n"
        "Asset type: web app character portrait, square avatar and profile image\n"
        f"Primary request: historically respectful photorealistic live-action reinterpretation of {sage['name']}.\n"
        f"Historical anchor: {sage['period']}.\n"
        "Accuracy note: do not claim a literal life likeness; translate established later portrait iconography into a believable human actor image.\n"
        f"Visual reference constraints: {sage['visual_reference']}.\n"
        f"Subject: {sage['persona']}.\n"
        f"Costume/props: {sage['costume']}.\n"
        "Style/medium: cinematic period-drama photography, realistic human face, natural skin texture, "
        "museum-quality costume design, historically grounded ancient Chinese robes.\n"
        "Text control: the image must contain no visible writing. Do not show open scrolls, books, plaques, "
        "paper sheets, calligraphy, or bamboo slips with marks.\n"
        "Composition/framing: centered bust portrait, shoulders visible, direct but gentle gaze, clean silhouette, "
        "soft dark neutral background with a hint of classical architecture.\n"
        "Lighting/mood: warm lantern and window light, refined, solemn, humane.\n"
        f"Avoid: {NEGATIVE}."
    )


def _scene_prompt(sage: dict) -> str:
    return (
        "Use case: historical-scene\n"
        "Asset type: wide character scene background for a web app card\n"
        f"Primary request: historically respectful photorealistic live-action scene featuring {sage['name']}.\n"
        f"Historical anchor: {sage['period']}.\n"
        "Accuracy note: use established later portrait iconography as visual reference, not a fantasy redesign or exact-life claim.\n"
        f"Visual reference constraints: {sage['visual_reference']}.\n"
        f"Subject: {sage['persona']}.\n"
        f"Costume/props: {sage['costume']}.\n"
        f"Scene/backdrop: {sage['setting']}.\n"
        "Style/medium: cinematic Chinese historical drama still, real human actor look, natural fabric, "
        "weathered wood, bronze, stone, landscape mist, atmospheric depth.\n"
        "Composition/framing: wide 3:2 composition, the sage placed slightly off center, enough quiet negative space "
        "for interface text overlays, face clearly visible, no crowding, no foreground desk, no foreground table.\n"
        "Pose and prop control: standing or walking portrait scene; do not seat the figure behind a desk or table. "
        "No foreground desk, no table, no writing tools, no document bundles. Allowed plain props only when historically relevant: "
        "a blank scepter-tablet, a white feather fan, a wine cup, or a travel staff.\n"
        "Text control: the image must contain no visible writing at all. Do not include open scrolls, open books, "
        "paper sheets, written bamboo slips, plaques, tablets with marks, maps with marks, signboards, banners, or flags.\n"
        "Lighting/mood: poetic but realistic, soft haze, restrained color, premium theatrical production design.\n"
        f"Avoid: {NEGATIVE}."
    )


def _write_png(path: Path, content: bytes) -> None:
    if not content.startswith(b"\x89PNG"):
        raise RuntimeError(f"{path.name} was not returned as PNG data")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agens AI photoreal sage portraits and scenes.")
    parser.add_argument("--only", default="", help="Generate one sage id only.")
    parser.add_argument("--asset", choices=["all", "portrait", "scene"], default="all")
    parser.add_argument("--force", action="store_true", help="Regenerate existing files.")
    parser.add_argument("--limit", type=int, default=0, help="Generate only the first N missing assets.")
    parser.add_argument("--portrait-size", default="1024x1024")
    parser.add_argument("--scene-size", default="1536x1024")
    args = parser.parse_args()

    generated = 0
    for sage in SAGES:
        if args.only and sage["id"] != args.only:
            continue

        tasks = []
        if args.asset in ("all", "portrait"):
            tasks.append(("portrait", PORTRAIT_DIR / f"{sage['id']}.png", _portrait_prompt(sage), args.portrait_size))
        if args.asset in ("all", "scene"):
            tasks.append(("scene", SCENE_DIR / f"{sage['id']}.png", _scene_prompt(sage), args.scene_size))

        for kind, output, prompt, size in tasks:
            if output.exists() and not args.force:
                continue
            if args.limit and generated >= args.limit:
                print(f"generated {generated} sage assets")
                return

            content = _request_image(prompt, size)
            _write_png(output, content)
            generated += 1
            print(f"generated {sage['id']} {kind} -> {output.relative_to(ROOT)}")

    print(f"generated {generated} sage assets")


if __name__ == "__main__":
    main()

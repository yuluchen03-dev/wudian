import argparse
import base64
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402

CATALOG_FILE = ROOT / "frontend" / "lib" / "classics_catalog.json"
BOOK_DIR = ROOT / "frontend" / "public" / "agens" / "books"

NEGATIVE = (
    "visible writing, readable text, calligraphy strokes, paper with marks, open books, open scrolls, "
    "bamboo slips with marks, plaques, signboards, seals, watermarks, logos, modern objects, neon colors, "
    "people, faces, portraits, books, documents, taotie masks, face-like motifs, angular glyph-like relief patterns, "
    "anime, fantasy armor, collage, over-busy composition, flat vector art"
)

FIRST_BATCH_IDS = [
    "yili",
    "zhouli",
    "zuozhuan",
    "gongyangzhuan",
    "guliangzhuan",
    "xiaojing",
    "erya",
    "xunzi",
    "chunqiufanlu",
    "baihutong",
    "xinyu",
    "xinshu",
]

SCENE_OVERRIDES = {
    "yili": (
        "a close atmospheric still life of Zhou ritual bronze vessels, folded dark silk, clean ceremonial mat texture, "
        "stone floor, timber shadow, and soft incense haze; shallow depth of field, no visible walls, no wall decorations, "
        "no actors, no figures, no tables, no desks, no scrolls, no books, no documents"
    ),
    "zhouli": (
        "close-up architectural still life of blank ancient stone steps, folded dark silk, plain uncarved bronze cubes, "
        "soft shadows from unseen timber columns, diffuse lantern haze, shallow depth of field; no corridor view, no statues, "
        "no vessels, no carved surfaces, no officials, no people, no tablets, no books, no scrolls"
    ),
    "zuozhuan": (
        "macro close-up still life of an ancient wooden chariot wheel hub, dusty ground, a plain bronze drum rim, "
        "sunlit haze, and a blurred stone wall texture; no full battlefield view, no soldiers, no people, "
        "no banners, no flags, no papers, no scrolls, no inscriptions"
    ),
    "gongyangzhuan": (
        "abstract cinematic material background: layered beige curtains, smoky amber light, blank woven mat texture, "
        "dark timber shadow, and calm central negative space; no historical characters, no room narrative, no people, "
        "no books, no scrolls, no bamboo slips, no documents, no inscriptions"
    ),
    "guliangzhuan": (
        "a restrained Confucian hall at dawn with no scholars; wooden pillars, ritual vessels, soft mist, "
        "a quiet central clearing, plain walls, no written bamboo slips, no plaques"
    ),
    "xiaojing": (
        "warm abstract material background suggesting filial reverence through empty space only: soft lantern glow, "
        "plain offering bowl silhouettes far out of focus, folded cloth, blank stone surface, clean central shadow, "
        "no ancestral tablets, no portraits, no figures, no family scene, no writing"
    ),
    "erya": (
        "macro natural material background only: smooth river stones, moss, soft herbs, a pale feather, shell texture, "
        "gray-green mist and shallow water highlights; no garden scene, no scholar, no human figure, no shelves, no books, "
        "no scrolls, no paper, no labels, no writing"
    ),
    "xunzi": (
        "an empty Warring States academy courtyard focused on discipline and ritual; austere stone steps, "
        "dark wooden beams, plain ritual objects, severe elegant atmosphere, no students, no teachers, no texts"
    ),
    "chunqiufanlu": (
        "a Western Han cosmology still life; palace observatory terrace, bronze armillary forms without markings, "
        "spring rain haze, ritual order, heaven-and-human resonance mood, no star charts, no writing"
    ),
    "baihutong": (
        "an empty Eastern Han imperial conference hall atmosphere; pale stone, bronze, symmetrical columns, "
        "lamplight, blank walls, no delegates, no plaques, no written memorials"
    ),
    "xinyu": (
        "early Han political renewal as an empty court corridor; bronze lamp, humble folded plain cloth, "
        "fresh dawn light through wooden lattice, no people, no documents, no signs"
    ),
    "xinshu": (
        "a Western Han reformist policy chamber with no officials; austere court interior, dark lacquer wood, "
        "bronze weights and ritual vessels, a sense of urgent counsel, no papers or visible writing"
    ),
}

PROMPT_NAMES = {
    "yili": "the Zhou ritual classic about ceremonies and etiquette",
    "zhouli": "the Zhou institutions classic about offices, rites, and governance",
    "zuozhuan": "the Spring and Autumn historical commentary known for narrative statecraft",
    "gongyangzhuan": "the Gongyang interpretive tradition of the Spring and Autumn annals",
    "guliangzhuan": "the Guliang interpretive tradition of the Spring and Autumn annals",
    "xiaojing": "the classic of filial reverence",
    "erya": "the early Chinese glossary of names, meanings, and natural categories",
    "xunzi": "the Xunzi tradition of ritual order, learning, and disciplined cultivation",
    "chunqiufanlu": "the Western Han cosmology and classics tradition of Spring and Autumn Luxuriant Dew",
    "baihutong": "the Eastern Han White Tiger Hall classics conference tradition",
    "xinyu": "the early Han New Discourses tradition of political renewal",
    "xinshu": "the Western Han New Book tradition of reformist counsel",
}

CATEGORY_MATERIALS = {
    "四书": "charcoal silk, dark warm bronze haze, smooth blank stone, restrained amber side light",
    "五经": "aged bronze glow, folded dark silk, mist over blank stone, quiet ritual warmth",
    "经部": "plain bronze shadow, ink-dark silk folds, soft smoke, austere blank stone",
    "儒家": "dark lacquer wood tone, bronze-gray haze, folded charcoal cloth, calm amber reflection",
    "道家": "ink-green mist, smooth river stone, jade-like shadow, soft water reflection",
    "墨家": "matte black stone, rain-dark bronze, humble coarse cloth texture, cool gray smoke",
    "法家": "black lacquer, cold bronze, severe slate shadow, narrow amber reflection",
    "名家": "smooth ivory stone blurred into gray shadow, quiet geometric light bands with no symbols",
    "兵家": "storm-gray metal patina, dark leather-like shadow, dust haze, cold dawn light",
    "史部": "timeworn dark lacquer, bronze dust, deep gray stone, dim archive-like shadow without documents",
    "史论": "somber bronze-gray haze, blank stone, dark cloth, narrow lamplight reflection",
    "医学": "soft herbal green haze, ceramic shadow, smooth river stones, warm steam",
    "农学": "dark earth texture, seed-like bokeh, moss green haze, soft dawn moisture",
    "算学": "smooth brass patina, slate shadow, soft angular light with no diagrams or symbols",
    "小学": "polished stone, muted moss, soft shell texture, blurred natural categories without marks",
    "佛教": "deep incense smoke, dark stone, muted lotus-color haze, quiet gold reflection with no icons",
    "理学": "cool mountain mist, dark wood shadow, smooth blank stone, restrained ivory-gray light",
    "心学": "warm ink-brown smoke, dark silk, empty central shadow, faint dawn reflection",
    "集部": "moonlit ink haze, dark silk, muted blossom-color shadow, soft atmospheric depth",
    "小说笔记": "night rain glow, dark lacquer, smoky amber bokeh, mysterious blank stone",
    "地理": "misty stone and water texture, moss-dark shadow, cool blue-gray haze",
    "地理神话": "dark mountain mist, wet stone, soft moonlit haze, no creatures or figures",
    "科技笔记": "cool metal patina, dark workbench-like shadow without objects, misty blue-gray light",
    "科技": "brushed bronze shadow, cool slate, soft mechanical-like light with no diagrams",
    "思想政论": "severe dark lacquer, bronze haze, charcoal cloth, focused central shadow",
    "考据": "quiet stone texture, magnified dust-like bokeh, dark neutral haze, no documents",
    "家训": "warm dark wood glow, soft linen shadow, amber haze, calm central darkness",
    "处世": "subtle ink-brown smoke, smooth stone, warm side glow, restrained dark cloth",
    "小品": "delicate ink haze, muted blossom shadow, dark silk, soft poetic light",
    "劝善": "warm smoke, dark stone, gentle gold reflection, calm empty center",
}


def _catalog_by_id() -> dict:
    catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    return {book["id"]: book for book in catalog["books"]}


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

    body = {}
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
        last_error = ""
        with httpx.Client(timeout=240) as client:
            for attempt in range(1, 4):
                try:
                    image_response = client.get(data["url"])
                    image_response.raise_for_status()
                    return image_response.content
                except httpx.HTTPError as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if attempt < 3:
                        time.sleep(8 * attempt)
                        continue
                    raise RuntimeError(f"Agens image download failed: {last_error}") from exc
    raise RuntimeError("Agens image response did not include image data")


def _cover_prompt(book: dict) -> str:
    if book["id"] == "xinshu":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure non-representational atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract material wallpaper suggesting sober governance through color mood only.\n"
            "Scene/backdrop: dark lacquer-black smoke, charcoal silk-like shadow, soft bronze-gray haze, one muted amber reflection, "
            "and calm central negative space. No room, no desk, no weights, no vessels, no officials, no court scene, no documents, no props.\n"
            "Style/medium: photorealistic smoke and macro material texture photography, shallow depth of field, restrained lacquer-black and bronze palette.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, darker, "
            "and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no labels, no seals, no symbols, no books, no scrolls, no bamboo slips, no documents, no paper, no memorials, no faces, no recognizable objects.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "xinyu":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure non-representational atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract material wallpaper suggesting renewal through warm dawn light and mist only.\n"
            "Scene/backdrop: soft amber-gray smoke, blurred honey light bands, muted plaster-like texture, gentle dust haze, "
            "and calm central negative space. No lattice, no windows, no corridor, no room, no desk, no linen fold, no scrolls, no paper, no props.\n"
            "Style/medium: photorealistic smoke and macro material texture photography, shallow depth of field, quiet honey-gray palette, refined and calm.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, darker, "
            "and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no labels, no seals, no symbols, no books, no scrolls, no bamboo slips, no documents, no paper, no plaques, no faces, no recognizable objects.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "baihutong":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure non-representational atmospheric material background strip for a web app card\n"
            "Primary request: premium cinematic dark abstract background suggesting Eastern Han classics debate through materials only, "
            "not through a literal hall or historical scene.\n"
            "Scene/backdrop: close macro field of dark smoky bronze patina, charcoal silk shadow, soft gray mist, "
            "subtle warm amber glow diffused into haze, and a calm empty central shadow. "
            "No architecture, no hall, no walls, no floor, no columns, no doorway, no roof, no stone slabs, no rectangular panels, "
            "no vertical poles, no lantern objects, no scrolls, no paper objects, no symbolic central mark, no tiger, no animal, no emblem, no crest.\n"
            "Style/medium: photorealistic material texture and atmospheric smoke photography, shallow depth of field, restrained dark bronze, charcoal, and gray palette.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; overall image should be darker than mid-gray, "
            "all detail must remain soft and off-center, with the central area dark, empty, and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no large single character, no labels, no seals, no symbols, no books, no scrolls, no bamboo slips, no documents, no paper, no memorials, no faces, no animals.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "chunqiufanlu":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract background suggesting spring rain, cosmology, and heaven-earth resonance through light and material only.\n"
            "Scene/backdrop: rain haze, dark bronze ring silhouette out of focus, wet stone, soft gold reflections, deep blue-gray shadow, "
            "and calm smoky central negative space. No observatory, no charts, no diagrams, no human figure.\n"
            "Style/medium: photorealistic atmospheric material still-life, shallow depth of field, restrained bronze and rain-gray palette.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, darker, "
            "and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no labels, no seals, no symbols, no charts, no books, no scrolls, no bamboo slips, no documents, no paper, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "xunzi":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract background suggesting discipline, ritual order, and rigorous learning through materials only.\n"
            "Scene/backdrop: smooth dark green-black silk folds, cool morning haze, plain unmarked slate slab, soft timber shadow, "
            "one calm central negative space. No stone steps, no carved texture, no academy scene, no teacher, no students, no human figure, no books.\n"
            "Style/medium: photorealistic material texture and atmospheric set photography, shallow depth of field, restrained ink-green palette.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, darker, "
            "and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no labels, no seals, no symbols, no books, no scrolls, no bamboo slips, no documents, no paper, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "erya":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric natural material background strip for a web app card\n"
            "Primary request: premium cinematic macro background made only of nature textures.\n"
            "Scene/backdrop: smooth river stones, moss, soft green herbs, pale feather texture, shell surface, low gray-green mist, "
            "and shallow water reflections. No humans, no historical scene, no study scene, no cultural artifacts.\n"
            "Style/medium: photorealistic macro nature still-life, shallow depth of field, soft gray-green palette, refined and calm.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, darker, "
            "and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no labels, no seals, no symbols, no books, no scrolls, no bamboo slips, no documents, no paper, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "xiaojing":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract background suggesting warmth, reverence, and family ethics through light only.\n"
            "Scene/backdrop: warm amber lamp glow on blank plaster, soft smoke, folded plain cloth, a smooth unmarked stone surface, "
            "and a calm dark central area. No family scene, no ancestor hall, no human figure, no altar, no tablets, no books.\n"
            "Style/medium: photorealistic material texture and smoke photography, shallow depth of field, warm humane palette, restrained.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, "
            "darker, and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no seals, no symbols, no plaques, no banners, no books, no scrolls, no bamboo slips, no documents, no carved ornaments, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "gongyangzhuan":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract background suggesting interpretive debate through light and empty space only.\n"
            "Scene/backdrop: smooth amber smoke, blank plaster shadow, plain translucent silk folds with no woven marks, "
            "soft window glow, and one calm dark central area. No room narrative, no historical characters, no cultural props.\n"
            "Style/medium: photorealistic material texture and smoke photography, shallow depth of field, warm Han-like palette, "
            "quiet, premium, restrained.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, "
            "darker, and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no seals, no symbols, no plaques, no banners, no books, no scrolls, no bamboo slips, no documents, no carved ornaments, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "guliangzhuan":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a catalog UI card\n"
            "Primary request: premium cinematic abstract background suggesting restrained judgment and moral order through materials only.\n"
            "Scene/backdrop: cool dawn smoke over blank stone, a smooth unmarked woven mat edge, dark timber shadow, "
            "subtle bronze-colored bokeh far out of focus, and quiet empty center. No room narrative, no historical characters, no props with marks.\n"
            "Style/medium: photorealistic material texture and atmospheric set photography, shallow depth of field, restrained bronze-gray palette.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, "
            "darker, and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no seals, no symbols, no plaques, no banners, no books, no scrolls, no bamboo slips, no documents, no carved ornaments, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    if book["id"] == "zhouli":
        return (
            "Use case: stylized-concept\n"
            "Asset type: pure atmospheric material background strip for a web app card\n"
            "Primary request: premium cinematic abstract background expressing order, ceremony, and hierarchy through materials only.\n"
            "Scene/backdrop: close-up of blank stone surface, three orderly bands of dark folded silk, soft smoke, "
            "warm amber side light, and quiet negative space. No architecture, no historical scene, no cultural props, no humans.\n"
            "Style/medium: photorealistic material texture and still-life set photography, shallow depth of field, "
            "warm bronze-like and ink tones, premium museum lighting, calm and restrained.\n"
            "Composition/framing: wide 3:2 composition for a shallow horizontal UI card crop; central area must stay calm, "
            "darker, and uncluttered for future UI text added by the app; the image itself must stay text-free.\n"
            "Text control: absolutely no visible writing, no Chinese characters, no Latin letters, no calligraphy, no glyph-like marks, "
            "no seals, no symbols, no plaques, no banners, no books, no scrolls, no bamboo slips, no documents, no carved ornaments, no faces.\n"
            f"Avoid: {NEGATIVE}."
        )

    scene = SCENE_OVERRIDES.get(book["id"])
    if scene:
        prompt_name = PROMPT_NAMES.get(book["id"], f"a Chinese classic in the {book.get('category', '')} tradition")

        return (
            "Use case: historical-scene\n"
            "Asset type: pure atmospheric background image for a catalog UI card, not a cover design\n"
            f"Primary request: premium Agens AI cinematic background inspired by {prompt_name}.\n"
            f"Book metadata: category {book.get('category', '')}, dynasty {book.get('dynasty', '')}.\n"
            f"Scene/backdrop: {scene}.\n"
            "Style/medium: photorealistic architectural and still-life set photography with no actors, museum-quality production design, "
            "natural fabric, bronze, stone, lacquered wood, rice-paper warmth, soft atmospheric haze.\n"
            "Composition/framing: wide 3:2 composition that also survives a shallow horizontal card crop; "
            "place the main silhouette and material detail inside the central 50%, keep the exact center calm and darker "
            "so interface text can sit over it later; empty scene, no human figures, no centered person, no face, "
            "no poster layout, no typography, no cover title.\n"
            "Lighting/mood: refined, quiet, cinematic, warm lantern or dawn light balanced with ink-like shadows.\n"
            "Text control: absolutely no visible writing and no title. Do not render the Chinese book name, any Chinese characters, "
            "Latin letters, calligraphy, glyph-like marks, plaques, signboards, seals, watermarks, open books, open scrolls, "
            "closed books, paper sheets, written bamboo slips, maps, flags, labels, wall panels, vertical wooden boards, "
            "lantern markings, or decorative typography.\n"
            f"Avoid: {NEGATIVE}."
        )

    materials = CATEGORY_MATERIALS.get(
        book.get("category", ""),
        "dark silk, smooth blank stone, bronze-gray haze, soft atmospheric smoke",
    )

    return (
        "Use case: stylized-concept\n"
        "Asset type: pure Agens AI atmospheric material background strip for a web or mobile UI tile\n"
        "Primary request: premium cinematic non-representational material wallpaper, expressed only through macro texture, "
        "light, smoke, soft shadows, and color mood. It must not depict a literal scene, room, library, desk, cover design, poster, or illustration.\n"
        f"Visual material palette: {materials}.\n"
        "Style/medium: photorealistic macro material texture, atmospheric smoke photography, shallow depth of field, "
        "museum-grade lighting, refined, quiet, premium, and abstract.\n"
        "Composition/framing: wide 3:2 horizontal composition; exact center must stay darker, soft, empty, and uncluttered "
        "for a later UI overlay. Keep all detail abstract, blurred, low-contrast, and off-center.\n"
        "Lighting/mood: calm cinematic haze with ink-like shadows; no bright white fields, no high-contrast hard edges, no centered mark.\n"
        "Hard constraints: no writing of any kind, no text-like strokes, no symbols, no diagrams, no seals, no stamps, no labels, "
        "no pages, no scrolls, no slips, no books, no documents, no tablets, no maps, no panels, no plaques, no emblems, "
        "no recognizable objects, no people, no faces, no animals, no foreground props, no watermarks, no typography."
    )


def _write_png(path: Path, content: bytes) -> None:
    if not content.startswith(b"\x89PNG"):
        raise RuntimeError(f"{path.name} was not returned as PNG data")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agens AI book cover backgrounds.")
    parser.add_argument("--only", default="", help="Generate one book id only.")
    parser.add_argument("--batch", choices=["first", "all"], default="first")
    parser.add_argument("--force", action="store_true", help="Regenerate existing images.")
    parser.add_argument("--limit", type=int, default=0, help="Generate only the first N matching missing assets.")
    parser.add_argument("--size", default="1536x1024")
    args = parser.parse_args()

    catalog = _catalog_by_id()
    ids = list(catalog) if args.batch == "all" else FIRST_BATCH_IDS
    if args.only:
        ids = [args.only]

    generated = 0
    for book_id in ids:
        if book_id not in catalog:
            raise RuntimeError(f"Unknown book id: {book_id}")
        output = BOOK_DIR / f"{book_id}.png"
        if output.exists() and not args.force:
            continue
        if args.limit and generated >= args.limit:
            break

        book = catalog[book_id]
        content = _request_image(_cover_prompt(book), args.size)
        _write_png(output, content)
        generated += 1
        print(f"generated {book_id} -> {output.relative_to(ROOT)}")

    print(f"generated {generated} book cover assets")


if __name__ == "__main__":
    main()

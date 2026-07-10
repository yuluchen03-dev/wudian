import json
import asyncio
from pathlib import Path

from app.services.content_service import _QUOTE_CARDS_FILE, content_service


def test_quote_cards_have_local_background_images():
    cards = json.loads(_QUOTE_CARDS_FILE.read_text(encoding="utf-8"))
    public_dir = Path(__file__).resolve().parents[2] / "frontend" / "public"

    assert cards
    for card in cards:
        image = card.get("background_image")
        assert image, f"{card['id']} is missing background_image"
        assert image.startswith("/"), f"{card['id']} background_image should be public path"
        assert (public_dir / image.lstrip("/")).exists(), f"{card['id']} image file missing"


def test_quote_card_service_exposes_background_images():
    content_service._loaded = False
    response = asyncio.run(content_service.list_quote_cards(page_size=100))

    assert response.items
    for card in response.items:
        assert card.background_image

from pathlib import Path
import unittest

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "public" / "agens" / "content" / "tengwang-ge-xu"


class TengwangPlaqueAssetTest(unittest.TestCase):
    def test_correction_preserves_image_outside_plaque_interiors(self) -> None:
        source = Image.open(ASSET_DIR / "pavilion.png").convert("RGBA")
        corrected_file = Image.open(ASSET_DIR / "pavilion-corrected.png")
        corrected = corrected_file.convert("RGBA")

        self.assertEqual(source.size, (1280, 823))
        self.assertEqual(corrected.size, source.size)
        self.assertEqual(corrected_file.info.get("PlaqueText"), "滕王阁|瑰伟绝特")
        self.assertEqual(source.getchannel("A").tobytes(), corrected.getchannel("A").tobytes())

        allowed = Image.new("L", source.size, 0)
        draw = ImageDraw.Draw(allowed)
        draw.rectangle((528, 232, 792, 317), fill=255)
        draw.rectangle((577, 478, 740, 505), fill=255)
        difference = ImageChops.difference(source, corrected)
        outside = Image.new("RGBA", source.size, (0, 0, 0, 0))
        outside.paste(difference, mask=ImageChops.invert(allowed))

        self.assertIsNone(outside.getbbox())


if __name__ == "__main__":
    unittest.main()

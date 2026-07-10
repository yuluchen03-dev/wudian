import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.sage_persona import SAGES, get_sage_name


class DebateGuestPersonasTest(unittest.TestCase):
    def test_plan_guest_personas_are_registered(self):
        expected = {
            "li_bai": "李白",
            "su_shi": "苏轼",
            "fan_zhongyan": "范仲淹",
            "wang_anshi": "王安石",
            "zhuge_liang": "诸葛亮",
        }

        for key, name in expected.items():
            with self.subTest(key=key):
                self.assertIn(key, SAGES)
                self.assertEqual(get_sage_name(key), name)


if __name__ == "__main__":
    unittest.main()

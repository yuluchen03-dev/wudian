import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.thought_compass import analyze_thought_compass


class ThoughtCompassServiceTest(unittest.TestCase):
    def test_statement_maps_to_stable_backend_mark(self):
        mark = analyze_thought_compass(
            "我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。"
        )

        self.assertEqual(mark.label, "逍遥实干派")
        self.assertGreaterEqual(mark.active_percent, 30)
        self.assertLessEqual(mark.active_percent, 55)
        self.assertGreater(mark.quiet_percent, mark.active_percent)
        self.assertEqual(mark.nearest_school, "儒道之间")
        self.assertIn("逍遥实干派", mark.imprint)


if __name__ == "__main__":
    unittest.main()

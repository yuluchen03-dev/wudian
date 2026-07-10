import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


class ThoughtCompassApiTest(unittest.TestCase):
    def test_debate_thought_compass_endpoint_returns_backend_mark(self):
        client = TestClient(app)
        response = client.post(
            "/api/debate/thought-compass",
            json={"statement": "我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "逍遥实干派")
        self.assertEqual(data["nearest_school"], "儒道之间")
        self.assertIn("active_percent", data)
        self.assertIn("quiet_percent", data)
        self.assertIn("imprint", data)


if __name__ == "__main__":
    unittest.main()

import importlib
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


debate_engine_module = importlib.import_module("app.services.debate_engine")


class DebateActionApisTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_complete_json = debate_engine_module.llm_client.complete_json

        async def fake_complete_json(messages, temperature=0.8):
            prompt = messages[-1]["content"]
            target = "laozi" if "laozi" in prompt else "confucius"
            return {
                "content": f"test speech for {target}",
                "vernacular": "test vernacular",
                "quote": "无",
                "source": "无",
                "citations": [],
                "target_sage": target,
                "clash_type": "extend",
                "confidence": "high",
            }

        debate_engine_module.llm_client.complete_json = fake_complete_json

    def tearDown(self):
        debate_engine_module.llm_client.complete_json = self.original_complete_json

    def _start_session(self) -> str:
        response = self.client.post(
            "/api/debate/start",
            json={
                "topic": "Should I keep competing or step back?",
                "sages": ["confucius", "laozi", "mozi", "hanfeizi"],
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["session_id"]

    def test_stand_endpoint_records_user_side_as_independent_round(self):
        session_id = self._start_session()

        response = self.client.post(
            f"/api/debate/{session_id}/stand",
            json={"stance": "I side with Laozi and want to step back.", "target_sage": "laozi"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["round"]["round_type"], "stance")
        self.assertEqual(data["speech"]["target_sage"], "laozi")
        self.assertEqual(data["phase"], "intervention")

    def test_mutual_question_endpoint_creates_question_and_answer_round(self):
        session_id = self._start_session()

        response = self.client.post(
            f"/api/debate/{session_id}/mutual-question",
            json={"from_sage": "confucius", "to_sage": "laozi"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["round"]["round_type"], "mutual_question")
        self.assertEqual(data["question"]["sage_key"], "confucius")
        self.assertEqual(data["question"]["target_sage"], "laozi")
        self.assertEqual(data["answer"]["sage_key"], "laozi")
        self.assertEqual(data["answer"]["target_sage"], "confucius")


if __name__ == "__main__":
    unittest.main()

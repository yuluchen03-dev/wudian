import importlib
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


debate_engine_module = importlib.import_module("app.services.debate_engine")


class DebateGuestRosterApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_complete_json = debate_engine_module.llm_client.complete_json

        async def fake_complete_json(messages, temperature=0.8):
            prompt = messages[-1]["content"]
            return {
                "content": "guest roster test speech",
                "vernacular": "guest roster test vernacular",
                "quote": "无",
                "source": "无",
                "citations": [],
                "target_sage": "li_bai" if "踢馆" in prompt else "confucius",
                "clash_type": "reframe",
                "confidence": "high",
            }

        debate_engine_module.llm_client.complete_json = fake_complete_json

    def tearDown(self):
        debate_engine_module.llm_client.complete_json = self.original_complete_json

    def _start_session(self) -> str:
        response = self.client.post(
            "/api/debate/start",
            json={"topic": "Should I keep competing or step back?"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["session_id"]

    def test_guest_roster_lists_unlock_and_collection_state(self):
        response = self.client.get("/api/debate/guests/roster")

        self.assertEqual(response.status_code, 200)
        roster = response.json()["guests"]
        keys = {guest["sage_key"] for guest in roster}
        self.assertIn("li_bai", keys)
        self.assertIn("zhuge_liang", keys)
        self.assertTrue(all("unlocked" in guest for guest in roster))
        self.assertTrue(all("collected" in guest for guest in roster))

    def test_random_guest_endpoint_summons_and_marks_random_trigger(self):
        session_id = self._start_session()

        response = self.client.post(f"/api/debate/{session_id}/guests/random")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["triggered_randomly"])
        self.assertTrue(data["speech"]["is_guest"])
        self.assertIn(data["sage_key"], {guest["sage_key"] for guest in self.client.get("/api/debate/guests/roster").json()["guests"]})

    def test_guest_decision_leave_removes_guest_and_stay_collects_guest(self):
        session_id = self._start_session()
        summon = self.client.post(f"/api/debate/{session_id}/summon", json={"sage_key": "li_bai"})
        self.assertEqual(summon.status_code, 200)

        leave = self.client.post(
            f"/api/debate/{session_id}/guests/li_bai/decision",
            json={"decision": "leave"},
        )
        self.assertEqual(leave.status_code, 200)
        self.assertFalse(leave.json()["staying"])
        session = self.client.get(f"/api/debate/{session_id}/session").json()
        self.assertNotIn("li_bai", session["participants"])

        stay = self.client.post(
            f"/api/debate/{session_id}/guests/li_bai/decision",
            json={"decision": "stay"},
        )
        self.assertEqual(stay.status_code, 200)
        self.assertTrue(stay.json()["staying"])
        self.assertTrue(stay.json()["guest"]["collected"])


if __name__ == "__main__":
    unittest.main()

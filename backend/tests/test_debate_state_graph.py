import importlib
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


debate_engine_module = importlib.import_module("app.services.debate_engine")


class DebateStateGraphTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_complete_json = debate_engine_module.llm_client.complete_json

        async def fake_complete_json(messages, temperature=0.8):
            prompt = messages[-1]["content"]
            if "会诊报告" in prompt:
                return {
                    "consensus": ["test consensus"],
                    "divergences": ["test divergence"],
                    "recommendations": [{"sage": "孔子", "recommendation": "test"}],
                    "summary": "test summary",
                }
            return {
                "content": "测试发言一句。测试发言二句。",
                "vernacular": "测试白话",
                "quote": "无",
                "source": "无",
                "citations": [],
                "target_sage": "confucius",
                "clash_type": "extend",
                "confidence": "high",
            }

        debate_engine_module.llm_client.complete_json = fake_complete_json

    def tearDown(self):
        debate_engine_module.llm_client.complete_json = self.original_complete_json

    def _start_session(self) -> str:
        response = self.client.post(
            "/api/debate/start",
            json={"topic": "Should I keep competing or step back?", "sages": ["confucius", "laozi"]},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["session_id"]

    def test_state_graph_endpoint_exposes_nodes_transitions_and_current_node(self):
        session_id = self._start_session()

        response = self.client.get(f"/api/debate/{session_id}/state-graph")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        node_ids = {node["id"] for node in data["nodes"]}
        transition_keys = {(edge["from_node"], edge["to_node"]) for edge in data["transitions"]}
        self.assertEqual(data["current_node"], "init")
        self.assertIn("round1", node_ids)
        self.assertIn("round2", node_ids)
        self.assertIn("report", node_ids)
        self.assertIn(("init", "round1"), transition_keys)
        self.assertIn(("round2", "report"), transition_keys)

    def test_next_round_executes_through_state_graph_and_records_trace(self):
        session_id = self._start_session()

        response = self.client.post(f"/api/debate/{session_id}/next-round?stream=false")
        self.assertEqual(response.status_code, 200)

        graph = self.client.get(f"/api/debate/{session_id}/state-graph").json()
        self.assertEqual(graph["current_node"], "round2")
        self.assertEqual(len(graph["trace"]), 1)
        first_step = graph["trace"][0]
        self.assertEqual(first_step["from_node"], "init")
        self.assertEqual(first_step["to_node"], "round1")
        self.assertEqual(first_step["action"], "run_round1_each_opinion")
        self.assertTrue(first_step["ok"])

    def test_streaming_next_round_records_state_graph_trace(self):
        session_id = self._start_session()

        with self.client.stream("POST", f"/api/debate/{session_id}/next-round?stream=true") as response:
            self.assertEqual(response.status_code, 200)
            list(response.iter_lines())

        graph = self.client.get(f"/api/debate/{session_id}/state-graph").json()
        self.assertEqual(graph["current_node"], "round2")
        self.assertEqual(len(graph["trace"]), 1)
        self.assertEqual(graph["trace"][0]["from_node"], "init")
        self.assertEqual(graph["trace"][0]["to_node"], "round1")
        self.assertTrue(graph["trace"][0]["ok"])


if __name__ == "__main__":
    unittest.main()

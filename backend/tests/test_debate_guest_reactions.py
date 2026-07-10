import asyncio
import importlib
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

debate_engine_module = importlib.import_module("app.services.debate_engine")


debate_engine = debate_engine_module.debate_engine


class DebateGuestReactionsTest(unittest.TestCase):
    def test_summoning_guest_creates_core_sage_response_round(self):
        async def scenario():
            session = await debate_engine.start_debate(
                "我该不该躺平?",
                ["confucius", "laozi", "mozi", "hanfeizi"],
            )
            await debate_engine.run_round1_each_opinion(session.id)
            await debate_engine.run_round2_cross_debate(session.id)
            before_report = await debate_engine.generate_report(session.id)

            result = await debate_engine.summon_guest_with_reactions(session.id, "li_bai")
            updated = debate_engine.get_session(session.id)

            return session, before_report, result, updated

        async def fake_complete_json(messages, temperature=0.8):
            prompt = messages[-1]["content"]
            if "会诊报告" in prompt:
                return {
                    "consensus": ["保持清醒判断"],
                    "divergences": ["四家立场各异"],
                    "recommendations": [{"sage": "孔子", "recommendation": "守志待时"}],
                    "summary": "测试报告",
                }
            return {
                "content": "测试发言",
                "vernacular": "测试白话",
                "quote": "无",
                "source": "无",
                "citations": [],
                "target_sage": "li_bai" if "回应踢馆" in prompt else "confucius",
                "clash_type": "reframe",
                "confidence": "high",
            }

        original_complete_json = debate_engine_module.llm_client.complete_json
        debate_engine_module.llm_client.complete_json = fake_complete_json
        try:
            session, before_report, result, updated = asyncio.run(scenario())
        finally:
            debate_engine_module.llm_client.complete_json = original_complete_json

        self.assertIsNotNone(before_report)
        self.assertEqual(result.guest.sage_key, "li_bai")
        self.assertTrue(result.guest.is_guest)
        self.assertEqual(result.reaction_round.round_type, "guest_response")
        self.assertEqual(
            [speech.sage_key for speech in result.reaction_round.speeches],
            ["confucius", "laozi", "mozi", "hanfeizi"],
        )
        self.assertEqual(len(result.reaction_round.clashes), 4)
        self.assertTrue(all(clash.to_sage == "li_bai" for clash in result.reaction_round.clashes))
        self.assertIn("li_bai", updated.participants)
        self.assertIsNone(updated.report)
        self.assertEqual(updated.phase, "intervention")


if __name__ == "__main__":
    unittest.main()

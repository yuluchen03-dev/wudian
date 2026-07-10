import asyncio
import importlib
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.schemas.debate import DebateClash
from app.services.citation_validator import citation_validator

debate_engine_module = importlib.import_module("app.services.debate_engine")


class DebatePlanCompletionTest(unittest.TestCase):
    def test_default_participants_are_only_core_sages(self):
        participants = debate_engine_module._get_available_participants()

        self.assertEqual(participants, settings.DEBATE_DEFAULT_PARTICIPANTS)
        for extra_sage in settings.DEBATE_EXTRA_SAGES:
            self.assertNotIn(extra_sage, participants)

    def test_speech_validation_rejects_cross_school_citation(self):
        async def fake_complete_json(messages, temperature=0.8):
            return {
                "content": "孔子曰：引孟子之言以证吾说。",
                "vernacular": "这条引用来自孟子，不应算作孔子本派经典。",
                "quote": "人皆有不忍人之心",
                "source": "《孟子》",
                "citations": [
                    {"id": "引1", "出处": "《孟子》", "原文": "人皆有不忍人之心"}
                ],
                "confidence": "high",
            }

        original_complete_json = debate_engine_module.llm_client.complete_json
        debate_engine_module.llm_client.complete_json = fake_complete_json
        try:
            speech = asyncio.run(
                debate_engine_module._speak(
                    "confucius",
                    [{"role": "user", "content": "test"}],
                    1,
                    [{"source": "《孟子》", "original": "人皆有不忍人之心"}],
                )
            )
        finally:
            debate_engine_module.llm_client.complete_json = original_complete_json

        self.assertEqual(len(speech.citations), 1)
        self.assertFalse(speech.citations[0].verifiable)

    def test_guest_author_citation_can_verify_against_own_work(self):
        validated, status = asyncio.run(
            citation_validator.validate(
                "li_bai",
                [{"id": "引1", "出处": "《将进酒》", "原文": "人生得意须尽欢"}],
                [{"source": "《将进酒》", "original": "人生得意须尽欢"}],
            )
        )

        self.assertEqual(status, "all_verified")
        self.assertTrue(validated[0].verifiable)

    def test_guest_reframe_clash_type_is_valid(self):
        clash = DebateClash(
            from_sage="li_bai",
            to_sage="confucius",
            clash_type="reframe",
            summary="李白从诗性生命重新框定争论",
        )

        self.assertEqual(clash.clash_type, "reframe")


if __name__ == "__main__":
    unittest.main()

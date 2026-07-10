import asyncio
import importlib
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

debate_engine_module = importlib.import_module("app.services.debate_engine")


class FakeRAG:
    def __init__(self):
        self.queries = []

    async def retrieve_for_debate_sage(self, sage_key: str, query: str, top_k: int = 1):
        self.queries.append((sage_key, query, top_k))
        return {
            "verses": [
                {
                    "source": "《论语·泰伯》",
                    "original": f"士不可以不弘毅。query={query}",
                    "translation": "",
                    "similarity": 0.91,
                    "sage_key": sage_key,
                }
            ],
            "commentaries": [],
        }


class DebateSentenceEvidenceTest(unittest.TestCase):
    def test_each_sentence_gets_own_classic_retrieval_evidence(self):
        fake_rag = FakeRAG()

        async def fake_complete_json(messages, temperature=0.8):
            return {
                "content": "第一句回应议题。第二句继续申论。",
                "vernacular": "白话",
                "quote": "无",
                "source": "无",
                "citations": [],
                "confidence": "high",
            }

        original_complete_json = debate_engine_module.llm_client.complete_json
        original_get_rag_service = debate_engine_module.get_rag_service
        debate_engine_module.llm_client.complete_json = fake_complete_json
        debate_engine_module.get_rag_service = lambda: fake_rag
        try:
            speech = asyncio.run(
                debate_engine_module._speak(
                    "confucius",
                    [{"role": "user", "content": "test"}],
                    1,
                    [],
                )
            )
        finally:
            debate_engine_module.llm_client.complete_json = original_complete_json
            debate_engine_module.get_rag_service = original_get_rag_service

        self.assertEqual([query[0] for query in fake_rag.queries], ["confucius", "confucius"])
        self.assertEqual(len(speech.sentence_evidence), 2)
        self.assertEqual(speech.sentence_evidence[0].sentence, "第一句回应议题。")
        self.assertEqual(speech.sentence_evidence[1].sentence, "第二句继续申论。")
        self.assertTrue(all(evidence.verifiable for evidence in speech.sentence_evidence))
        self.assertTrue(all(evidence.source.startswith("《论语") for evidence in speech.sentence_evidence))


if __name__ == "__main__":
    unittest.main()

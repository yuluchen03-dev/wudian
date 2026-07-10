import asyncio
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.citation_validator import citation_validator
from app.services.rag_service import get_rag_service


class DebateClassicRAGTest(unittest.TestCase):
    def test_build_index_writes_debate_classics_to_chromadb(self):
        rag = get_rag_service()
        if rag.collection is None:
            self.skipTest("ChromaDB collection is not available")

        count = rag.build_index(force=True)
        rows = rag.collection.get(
            where={"scope": "debate_classic"},
            include=["metadatas"],
        )
        metadatas = rows.get("metadatas", [])
        expected_books = {
            "confucius": "论语",
            "laozi": "道德经",
            "mozi": "墨子",
            "hanfeizi": "韩非子",
        }

        self.assertGreater(count, 122)
        for sage_key, book in expected_books.items():
            with self.subTest(sage_key=sage_key):
                sage_docs = [
                    meta for meta in metadatas
                    if meta.get("sage_key") == sage_key
                ]
                self.assertGreater(len(sage_docs), 0)
                self.assertTrue(
                    all(meta.get("book") == book for meta in sage_docs),
                    sage_docs,
                )

    def test_debate_rag_can_retrieve_from_chromadb_without_memory_index(self):
        rag = get_rag_service()
        if rag.collection is None:
            self.skipTest("ChromaDB collection is not available")

        rag.build_index(force=True)
        original_index = rag._debate_classic_index
        rag._debate_classic_index = {}
        try:
            result = asyncio.run(
                rag.retrieve_for_debate_sage(
                    sage_key="mozi",
                    query="赖其力者生，不赖其力者不生。",
                    top_k=3,
                )
            )
        finally:
            rag._debate_classic_index = original_index

        verses = result["verses"]
        self.assertGreater(len(verses), 0)
        self.assertTrue(
            all("墨子" in verse["source"] for verse in verses),
            [verse["source"] for verse in verses],
        )
        self.assertTrue(
            any("赖其力者生" in verse["original"] for verse in verses),
            verses,
        )

    def test_debate_rag_retrieves_only_the_requested_sage_classic(self):
        rag = get_rag_service()

        cases = [
            ("confucius", "我该不该躺平", "论语"),
            ("laozi", "我该不该躺平", "道德经"),
            ("mozi", "我该不该躺平", "墨子"),
            ("hanfeizi", "我该不该躺平", "韩非子"),
        ]

        for sage_key, query, expected_source in cases:
            with self.subTest(sage_key=sage_key):
                result = asyncio.run(
                    rag.retrieve_for_debate_sage(sage_key=sage_key, query=query, top_k=3)
                )
                verses = result["verses"]

                self.assertGreater(len(verses), 0)
                self.assertTrue(
                    all(expected_source in verse["source"] for verse in verses),
                    [verse["source"] for verse in verses],
                )
                context = rag.build_debate_context(sage_key, result)
                self.assertIn(f"检索到的《{expected_source}》原文", context)

    def test_debate_rag_supports_verified_core_fallback_quotes(self):
        rag = get_rag_service()

        cases = [
            ("confucius", "士不可以不弘毅，任重而道远。", "《论语·泰伯》"),
            ("laozi", "夫唯不争，故天下莫能与之争。", "《道德经》"),
            ("mozi", "赖其力者生，不赖其力者不生。", "《墨子》"),
            ("hanfeizi", "法不阿贵，绳不挠曲。", "《韩非子·有度》"),
        ]

        for sage_key, quote, source in cases:
            with self.subTest(sage_key=sage_key):
                result = asyncio.run(
                    rag.retrieve_for_debate_sage(sage_key=sage_key, query="我该不该躺平", top_k=5)
                )
                refs = result["verses"] + result["commentaries"]
                validated, status = asyncio.run(
                    citation_validator.validate(
                        sage_key,
                        [{"id": "引1", "出处": source, "原文": quote}],
                        refs,
                    )
                )

                self.assertEqual(status, "all_verified")
                self.assertTrue(validated[0].verifiable)


if __name__ == "__main__":
    unittest.main()

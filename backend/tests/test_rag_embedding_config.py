import importlib
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

rag_service_module = importlib.import_module("app.services.rag_service")


class RagEmbeddingConfigTest(unittest.TestCase):
    def test_default_embedding_does_not_use_external_openai_api(self):
        service = object.__new__(rag_service_module.RAGService)
        embed_fn = service._build_embed_fn()

        self.assertNotIn("OpenAI", type(embed_fn).__name__)
        vectors = embed_fn(["仁义礼智信", "无为而无不为"])
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), len(vectors[1]))
        self.assertGreater(len(vectors[0]), 0)


if __name__ == "__main__":
    unittest.main()

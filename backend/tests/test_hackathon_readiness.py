import asyncio
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.ai_service import AIService


ai_service_module = importlib.import_module("app.services.ai_service")


def test_settings_resolve_demo_paths_under_backend_root():
    backend_root = Path(__file__).resolve().parents[1]

    assert Path(settings.resolved_database_path).is_absolute()
    assert Path(settings.resolved_chroma_persist_dir).is_absolute()
    assert Path(settings.resolved_debate_storage_dir).is_absolute()

    assert str(settings.resolved_database_path).startswith(str(backend_root))
    assert str(settings.resolved_chroma_persist_dir).startswith(str(backend_root))
    assert str(settings.resolved_debate_storage_dir).startswith(str(backend_root))


def test_health_exposes_hackathon_readiness_signals():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    for key in [
        "status",
        "llm_available",
        "llm_provider",
        "rag_available",
        "rag_count",
        "database_path",
        "chroma_persist_dir",
        "debate_storage_dir",
    ]:
        assert key in data


def test_stream_chat_uses_cache_when_llm_is_unavailable(monkeypatch):
    class FakeRag:
        async def retrieve_for_sage_chat(self, question, top_k=5):
            return {"verses": [], "commentaries": []}

        def build_sage_chat_context(self, result):
            return ""

    async def unavailable_stream(*args, **kwargs):
        yield "LLM API_KEY 未配置（provider=openai）。"

    monkeypatch.setattr(ai_service_module.sage_cache, "match_safe_qa", lambda question: None)
    monkeypatch.setattr(ai_service_module.sage_cache, "get_fallback_qa", lambda question: {
        "content": "缓存兜底回答",
        "vernacular": "缓存白话点睛",
        "original_quotes": ["人不知而不愠，不亦君子乎？"],
        "sources": ["《论语·学而》"],
        "disclaimer": "缓存免责声明",
    })
    monkeypatch.setattr(ai_service_module, "get_rag_service", lambda: FakeRag())
    monkeypatch.setattr(ai_service_module.llm_client, "stream", unavailable_stream)
    monkeypatch.setattr(ai_service_module.llm_client, "client", None)

    async def collect():
        chunks = []
        async for chunk in AIService().chat_with_sage(
            sage="confucius",
            question="不被领导认可怎么办",
            history=[],
            stream=True,
        ):
            chunks.append(chunk)
        return "".join(chunks)

    text = asyncio.run(collect())

    assert "缓存兜底回答" in text
    assert "缓存白话点睛" in text
    assert "API_KEY 未配置" not in text

"""FIX-005: isolated mock-only Q5 workflow coverage.

These are local TestClient tests. They do NOT call an external LLM and are not
proof that the real-provider Q5 gate is closed. conftest forces per-process DB
and Chroma isolation before importing the application.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pytest

import importlib

ai_service_module = importlib.import_module("app.services.ai_service")
rag_service_module = importlib.import_module("app.services.rag_service")


ORIGINAL = "己所不欲，勿施于人。"
SOURCE = "《论语·卫灵公》"


class FakeRag:
    async def retrieve_for_sage_chat(self, question: str, top_k: int = 5):
        return {
            "verses": [{
                "verse_id": "15.24",
                "original": ORIGINAL,
                "translation": "不要把自己不愿承受的事施加给别人。",
                "chapter": "卫灵公",
                "source": SOURCE,
                "similarity": 0.9,
            }],
            "commentaries": [],
        }

    def build_sage_chat_context(self, result):
        return ORIGINAL


def _set_test_rag(monkeypatch):
    rag = FakeRag()
    monkeypatch.setattr(rag_service_module, "get_rag_service", lambda: rag)
    monkeypatch.setattr(ai_service_module, "get_rag_service", lambda: rag)
    monkeypatch.setattr(ai_service_module.sage_cache, "match_safe_qa", lambda question: None)
    return rag


def _citation_rows(payload):
    rows = payload["citations"]
    # FastAPI serializes aliases by default; accept either field spelling so the
    # assertion stays about validation semantics rather than JSON alias policy.
    return [
        {
            "verifiable": row["verifiable"],
            "original": row.get("原文", row.get("original")),
        }
        for row in rows
    ]


def test_chat_sage_nonstream_validates_mock_citations_and_downgrades_fabrication(
    client, monkeypatch
):
    _set_test_rag(monkeypatch)

    async def mock_complete_json(messages, temperature=0.8):
        assert any("勿施于人" in str(message) for message in messages)
        return {
            "reply": "以恕待人。",
            "citations": [
                {"id": "c1", "出处": SOURCE, "原文": ORIGINAL},
                {"id": "c2", "出处": SOURCE, "原文": "并不存在的伪造原句"},
            ],
            "modern_takeaway": "先以己心度人。",
            "confidence": "high",
            "honest_note": None,
        }

    monkeypatch.setattr(ai_service_module.llm_client, "complete_json", mock_complete_json)
    response = client.post(
        "/api/ai/chat-sage",
        json={"sage": "confucius", "question": "怎样理解恕道？", "history": [], "stream": False},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    citations = _citation_rows(payload)
    assert len(citations) == 2
    assert citations[0] == {"verifiable": True, "original": ORIGINAL}
    assert citations[1]["verifiable"] is False
    assert payload["honest_note"]
    assert payload["confidence"] != "high"


def test_chat_sage_stream_does_not_bypass_citation_guard(client, monkeypatch):
    _set_test_rag(monkeypatch)
    fabricated = "并不存在的伪造原句内容"
    raw = json.dumps({
        "reply": "以恕待人。",
        "citations": [{"id": "c1", "出处": SOURCE, "原文": fabricated}],
        "modern_takeaway": "先以己心度人。",
        "confidence": "high",
        "honest_note": None,
    }, ensure_ascii=False)

    async def mock_stream(*args, **kwargs):
        yield raw

    monkeypatch.setattr(ai_service_module.llm_client, "stream", mock_stream)
    response = client.post(
        "/api/ai/chat-sage",
        json={"sage": "confucius", "question": "mock citation validation", "history": [], "stream": True},
    )

    assert response.status_code == 200
    events = [line[6:] for line in response.text.splitlines() if line.startswith("data: {")]
    decoded = [json.loads(event) for event in events]
    citation_event = next(event for event in decoded if event.get("type") == "citations")
    citation = citation_event["citations"][0]
    assert citation["verifiable"] is False
    assert citation["verification_status"] == "insufficient_evidence"


def test_chat_sage_missing_provider_degrades_without_logging_key(
    client, monkeypatch, caplog
):
    _set_test_rag(monkeypatch)
    sentinel_key = "FIX005_TEST_SECRET_SENTINEL_NOT_A_REAL_KEY"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel_key)

    async def unavailable_provider(messages, temperature=0.8):
        raise RuntimeError("mock provider unavailable")

    monkeypatch.setattr(ai_service_module.llm_client, "complete_json", unavailable_provider)
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/ai/chat-sage",
            json={"sage": "confucius", "question": "触发 mock provider fallback", "history": [], "stream": False},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["confidence"] == "low"
    assert "AI 服务暂时不可用" in payload["honest_note"]
    assert sentinel_key not in caplog.text


def test_test_process_chroma_is_not_production():
    """Guard the test-runner isolation invariant without opening Chroma."""
    configured = os.environ.get("CHROMA_PERSIST_DIR")
    assert configured, "conftest must set isolated CHROMA_PERSIST_DIR before app import"
    backend_root = Path(__file__).resolve().parents[1]
    resolved = (backend_root / configured).resolve() if not Path(configured).is_absolute() else Path(configured).resolve()
    production = (backend_root / "chroma_db").resolve()
    assert resolved != production
    assert f"test_wudian_{os.getpid()}" in os.environ.get("DATABASE_URL", "")

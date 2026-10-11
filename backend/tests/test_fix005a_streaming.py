

from __future__ import annotations

import asyncio
import importlib as _importlib
import json

import pytest

from app.main import app
from fastapi.testclient import TestClient
from app.services.ai_service import ai_service as _ai_service

ai_service_module = _importlib.import_module("app.services.ai_service")
rag_service_module = _importlib.import_module("app.services.rag_service")
api_ai_module = _importlib.import_module("app.api.ai")

ORIGINAL = "有一言而可以终身行之者乎？子曰：「其恕乎！己所不欲，勿施于人。」"
SOURCE = "《论语·卫灵公》"
WRONG_SOURCE = "《论语·学而》"


class FakeRag:
    async def retrieve_for_sage_chat(self, question, top_k=5):
        if question == "no-evidence":
            return {"verses": [], "commentaries": []}
        return {"verses": [{
            "verse_id": "15.24", "original": ORIGINAL, "source": SOURCE,
            "chapter": "卫灵公", "translation": "以己度人", "similarity": 0.9,
            "text_type": "original",
        }], "commentaries": []}

    def build_sage_chat_context(self, result):
        return ORIGINAL if result["verses"] else ""


def _mock_service(monkeypatch, raw):
    rag = FakeRag()
    monkeypatch.setattr(rag_service_module, "get_rag_service", lambda: rag)
    monkeypatch.setattr(ai_service_module, "get_rag_service", lambda: rag)
    monkeypatch.setattr(ai_service_module, "build_sage_system_prompt", lambda *a, **k: "system")
    monkeypatch.setattr(ai_service_module, "get_sage_name", lambda sage: sage)
    monkeypatch.setattr(ai_service_module.sage_cache, "match_safe_qa", lambda q: None)
    monkeypatch.setattr(ai_service_module.llm_client, "client", object())

    async def fake_stream(messages, temperature=0.8):
        if isinstance(raw, Exception):
            raise raw
        yield raw[:len(raw)//2]
        yield raw[len(raw)//2:]

    monkeypatch.setattr(ai_service_module.llm_client, "stream", fake_stream)
    return rag


def _raw(citations):
    return json.dumps({"reply": "mock reply", "citations": citations,
                       "modern_takeaway": "takeaway", "confidence": "high",
                       "honest_note": None}, ensure_ascii=False)


@pytest.mark.parametrize("question,citations,expected", [
    ("fixture", [{"id":"1","出处":SOURCE,"原文":ORIGINAL}], "verified"),
    ("fixture", [{"id":"1","出处":WRONG_SOURCE,"原文":ORIGINAL}], "citation_corrected"),
    ("fixture", [{"id":"1","出处":SOURCE,"原文":"并不存在的伪造原句内容"}], "insufficient_evidence"),
    ("fixture", [{"id":"1","出处":SOURCE,"原文":"勿施于人"}], "quote_relaxed"),
    ("no-evidence", [], None),
])
def test_service_stream_final_citation_states(monkeypatch, question, citations, expected):
    _mock_service(monkeypatch, _raw(citations))
    response = asyncio.run(_ai_service.chat_with_sage_stream_response("confucius", question, []))
    if expected is None:
        assert response.citations == []
    else:
        assert response.citations[0].verification_status == expected
        assert response.citations[0].verifiable is (expected == "verified")


def test_service_stream_interruption_returns_no_verified_partial(monkeypatch):
    async def interrupted(messages, temperature=0.8):
        yield '{"reply":"partial"'
        raise ConnectionError("synthetic interruption")
    _mock_service(monkeypatch, "")
    monkeypatch.setattr(ai_service_module.llm_client, "stream", interrupted)
    response = asyncio.run(_ai_service.chat_with_sage_stream_response("confucius", "fixture", []))
    assert all(c.verification_status != "verified" for c in response.citations)


def test_service_stream_provider_exception_fallback_is_validated(monkeypatch):
    _mock_service(monkeypatch, RuntimeError("synthetic provider error"))
    response = asyncio.run(_ai_service.chat_with_sage_stream_response("confucius", "fixture", []))
    assert all(c.verification_status in {"verified", "citation_corrected", "quote_relaxed",
                                         "unverified", "insufficient_evidence"}
               for c in response.citations)


def test_service_stream_nonstream_parity(monkeypatch):
    raw = _raw([{"id":"1","出处":SOURCE,"原文":ORIGINAL}])
    _mock_service(monkeypatch, raw)
    streamed = asyncio.run(_ai_service.chat_with_sage_stream_response("confucius", "fixture", []))
    refs = asyncio.run(FakeRag().retrieve_for_sage_chat("fixture"))
    nonstream, _ = _ai_service._validate_citations(json.loads(raw)["citations"], refs["verses"])
    assert [(c.verifiable, c.verification_status, c.source, c.original) for c in streamed.citations] == [
        (c.verifiable, c.verification_status, c.source, c.original) for c in nonstream
    ]


# API-level SSE integration coverage: exercise the real FastAPI route and inspect
# terminal event payloads, rather than relying only on the AIService helper tests above.
import importlib as _importlib

api_ai_module = _importlib.import_module("app.api.ai")


def _stream_events(response):
    assert response.status_code == 200, response.text
    result = []
    for line in response.text.splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            payload = line[6:]
            try:
                result.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
    return result


def _chat_response(citation):
    from app.schemas.ai import ChatSageResponse, Citation

    citations = [] if citation is None else [Citation(
        id="1", source=citation["source"], original=citation["original"],
        verifiable=citation["verifiable"],
        verification_status=citation["verification_status"],
    )]
    return ChatSageResponse(
        sage="confucius", reply="mock reply", disclaimer="mock disclaimer",
        citations=citations, confidence="high",
    )


def _patch_route_dependencies(monkeypatch, response):
    async def retrieve(question, top_k=5):
        return {"verses": [{
            "verse_id": "15.24", "original": ORIGINAL, "source": SOURCE,
            "chapter": "卫灵公", "translation": "以己度人", "similarity": 0.9,
            "text_type": "original",
        }], "commentaries": []}

    rag_module = _importlib.import_module("app.services.rag_service")
    monkeypatch.setattr(rag_module, "get_rag_service", lambda: type(
        "R", (), {"retrieve_for_sage_chat": staticmethod(retrieve)}
    )())
    monkeypatch.setattr(api_ai_module.ai_service, "chat_with_sage_stream_response",
                        lambda **kwargs: _return(response))
    monkeypatch.setattr(api_ai_module.ai_service, "chat_with_sage_structured",
                        lambda **kwargs: _return(response))


async def _return(value):
    return value


def test_api_sse_valid_citation_matches_nonstream_final_state(client, monkeypatch):
    valid = {"source": SOURCE, "original": ORIGINAL, "verifiable": True,
             "verification_status": "verified"}
    response_obj = _chat_response(valid)
    _patch_route_dependencies(monkeypatch, response_obj)
    body = {"sage": "confucius", "question": "same deterministic fixture", "history": []}

    stream = client.post("/api/ai/chat-sage", json={**body, "stream": True})
    stream_events = _stream_events(stream)
    citation_event = next(e for e in stream_events if e.get("type") == "citations")
    stream_citation = citation_event["citations"][0]

    nonstream = client.post("/api/ai/chat-sage", json={**body, "stream": False})
    assert nonstream.status_code == 200, nonstream.text
    nonstream_citation = nonstream.json()["citations"][0]
    assert stream_citation["verifiable"] is nonstream_citation["verifiable"] is True
    assert stream_citation["verification_status"] == nonstream_citation["verification_status"] == "verified"
    assert stream_citation.get("原文", stream_citation.get("original")) == nonstream_citation.get("原文", nonstream_citation.get("original")) == ORIGINAL
    assert stream_citation.get("出处", stream_citation.get("source")) == nonstream_citation.get("出处", nonstream_citation.get("source")) == SOURCE


def test_api_sse_fabricated_citation_remains_unverified(client, monkeypatch):
    fabricated = {"source": SOURCE, "original": "并不存在的伪造原句内容",
                  "verifiable": False, "verification_status": "insufficient_evidence"}
    _patch_route_dependencies(monkeypatch, _chat_response(fabricated))
    response = client.post("/api/ai/chat-sage", json={
        "sage": "confucius", "question": "fabricated fixture", "history": [], "stream": True,
    })
    events = _stream_events(response)
    citation_event = next(e for e in events if e.get("type") == "citations")
    citation = citation_event["citations"][0]
    assert citation["verifiable"] is False
    assert citation["verification_status"] == "insufficient_evidence"


def test_api_sse_provider_error_returns_generic_error_without_citation_event(client, monkeypatch, caplog):
    sentinel = "PROVIDER_SECRET_AND_ERROR_PAYLOAD_SENTINEL"

    async def fail_before_finalization(**kwargs):
        raise RuntimeError(sentinel)

    rag_module = _importlib.import_module("app.services.rag_service")

    async def retrieve(question, top_k=5):
        return {"verses": [{"verse_id": "15.24", "original": ORIGINAL, "source": SOURCE,
                             "chapter": "卫灵公", "translation": "", "similarity": 0.9}],
                "commentaries": []}

    monkeypatch.setattr(rag_module, "get_rag_service", lambda: type(
        "R", (), {"retrieve_for_sage_chat": staticmethod(retrieve)}
    )())
    monkeypatch.setattr(api_ai_module.ai_service, "chat_with_sage_stream_response", fail_before_finalization)
    with caplog.at_level("ERROR"):
        response = client.post("/api/ai/chat-sage", json={
            "sage": "confucius", "question": "provider error fixture", "history": [], "stream": True,
        })
    events = _stream_events(response)
    assert not any(event.get("type") == "citations" for event in events)
    error = next(event for event in events if event.get("type") == "error")
    assert error["code"] == "stream_incomplete"
    assert sentinel not in response.text
    assert sentinel not in caplog.text

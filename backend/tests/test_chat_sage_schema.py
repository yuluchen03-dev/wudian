import asyncio
import importlib

from app.schemas.ai import ChatSageRequest
from app.services.ai_service import AIService, extract_stream_reply_text


ai_service_module = importlib.import_module("app.services.ai_service")


def test_chat_sage_accepts_frontend_guest_sage_ids():
    req = ChatSageRequest(
        sage="zhuge_liang",
        question="做错事了，该怎么面对？",
        history=[],
        stream=True,
    )

    assert req.sage == "zhuge_liang"


def test_extract_stream_reply_text_hides_structured_json_wrapper():
    raw = """
{
  "reply": "汝以此寒暄相问，墨子以为，言语虽简，却可见人心之诚伪。",
  "citations": [{"id": "引1", "出处": "论语·学而", "原文": "与朋友交，言而有信"}],
  "modern_takeaway": "少说套话，多看行动。",
  "confidence": "medium",
  "honest_note": null
}
"""

    text = extract_stream_reply_text(raw)

    assert text.startswith("汝以此寒暄相问")
    assert "少说套话，多看行动。" in text
    assert '"reply"' not in text
    assert "citations" not in text


def test_chat_with_sage_stream_hides_structured_json_wrapper(monkeypatch):
    class FakeRag:
        async def retrieve_for_sage_chat(self, question, top_k=5):
            return {"verses": [], "commentaries": []}

        def build_sage_chat_context(self, result):
            return ""

    async def fake_stream(messages, temperature=0.8):
        raw = (
            '{"reply":"Human answer",'
            '"citations":[{"id":"ref1"}],'
            '"modern_takeaway":"Useful takeaway",'
            '"confidence":"medium",'
            '"honest_note":null}'
        )
        yield raw[:18]
        yield raw[18:]

    monkeypatch.setattr(ai_service_module.sage_cache, "match_safe_qa", lambda question: None)
    monkeypatch.setattr(ai_service_module, "get_rag_service", lambda: FakeRag())
    monkeypatch.setattr(ai_service_module.llm_client, "stream", fake_stream)

    async def collect_reply():
        chunks = []
        async for chunk in AIService().chat_with_sage(
            sage="mozi",
            question="hello",
            history=[],
            stream=True,
        ):
            chunks.append(chunk)
        return "".join(chunks)

    text = asyncio.run(collect_reply())

    assert text == "Human answer\n\nUseful takeaway"
    assert '"reply"' not in text
    assert "citations" not in text

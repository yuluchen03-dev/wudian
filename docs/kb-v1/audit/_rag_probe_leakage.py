"""PHASE 0 read-only probe: cross-school leakage risk at the RAG interface.

Task item 7. Focused on how RAG results flow into school-isolation checks.
Safety: temp copy of chroma_db; build_index() never called.
"""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe9_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
from app.services.citation_validator import citation_validator  # noqa: E402

rag = RAGService()

print("### 1. retrieve_for_sage_chat (NO scope filter) surfaces non-论语 books")
res = asyncio.run(rag.retrieve_for_sage_chat("我该不该躺平", top_k=5))
for v in res["verses"]:
    print(f"    {v['source']}  sim={v['similarity']:.3f}")

print("\n### 2. retrieve_for_debate_sage isolation (sage_key filter IS applied)")
for sage in ["confucius", "laozi", "mozi", "hanfeizi"]:
    r = asyncio.run(rag.retrieve_for_debate_sage(sage, "我该不该躺平", top_k=5))
    books = sorted({v["source"].strip("《》").split("·")[0] for v in r["verses"]})
    print(f"    {sage:11} books={books}")

print("\n### 3. citation_validator._check_classic_belonging bypass cases")
cases = [
    ("confucius", {"出处": "", "原文": "任何句子"}),
    ("confucius", {"出处": "无", "原文": "任何句子"}),
    ("confucius", {"原文": "任何句子"}),
    ("confucius", {"出处": "《墨子·兼爱》", "原文": "兼相爱交相利"}),
    ("mozi", {"出处": "《论语·学而》", "原文": "学而时习之"}),
]
for sage, cit in cases:
    ok = citation_validator._check_classic_belonging(sage, cit)
    print(f"    sage={sage:11} src={cit.get('出处','<missing>')!r:16} belongs={ok}")

print("\n### 4. _match_citation substring direction (rag_refs are RAG hits)")
print("    code: citation_validator.py:83  `if cit_original in ref_original or ref_original in cit_original`")
print("    => a SHORT citation is 'verified' by a LONGER ref that merely CONTAINS it")
refs = [{"original": "子曰：「不患人之不己知，患不知人也。」"}]
for cit_text in ["不患人之不己知，患不知人也", "不患人之不己知", "患不知人也", "不己知"]:
    ok = citation_validator._match_citation({"原文": cit_text}, refs)
    print(f"    citation={cit_text!r:26} verifiable={ok}")

print("\n### 5. does a FABRICATED quote pass against real refs?")
fabricated = [
    "孔子曰：忍一时风平浪静，退一步海阔天空",
    "老子云：努力必有回报",
    "子曰：职场PUA当以直报怨",
]
for f in fabricated:
    ok = citation_validator._match_citation({"原文": f}, refs)
    print(f"    fabricated={f[:26]!r:30} verifiable={ok}")

print("\n### 6. relevance floor: unrelated query still yields 'evidence'")
r = asyncio.run(rag.retrieve_for_debate_sage("hanfeizi", "量子计算机如何优化神经网络", top_k=3))
for v in r["verses"]:
    print(f"    {v['source']} sim={v['similarity']:.3f} :: {v['original'][:40]}")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

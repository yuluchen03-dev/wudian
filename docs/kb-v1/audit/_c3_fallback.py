"""P0R-02 / C3: does the Confucius fallback break the garbage-query acceptance?

With the debate paths returning empty, retrieve_for_debate_sage('confucius', ...)
falls through to retrieve_for_sage_chat (rag_service.py:1031-1032), which calls
vector_search with NO scope filter and NO threshold. This diagnostic measures
what that path actually returns for garbage queries.

Safety: temp copy of chroma_db.
"""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="c3fb_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

print("### retrieve_for_sage_chat (the Confucius fallback target)")
for q in ["asdfghjkl", "zzzzzz", "如何面对亲人的离世", "什么是仁", "学而时习之"]:
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=3))
    vs = res["verses"]
    print(f"  q={q!r:22} verses={len(vs)}")
    for v in vs:
        print(f"      sim={round(v['similarity'],4)} src={v['source']} :: {v['original'][:30]}")

print("\n### books surfaced by the fallback (scope leakage check)")
for q in ["asdfghjkl", "如何面对亲人的离世"]:
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    books = sorted({v["source"].strip("《》").split("·")[0] for v in res["verses"]})
    print(f"  q={q!r:22} books={books}")

print("\n### simulate: debate empty -> fallback (what retrieve_for_debate_sage will do)")
for q in ["asdfghjkl", "zzzzzz"]:
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=3))
    print(f"  confucius fallback for {q!r} -> {len(res['verses'])} verses "
          f"(sims={[round(v['similarity'],4) for v in res['verses']]})")

shutil.rmtree(tmp, ignore_errors=True)

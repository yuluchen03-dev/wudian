"""PHASE 0 read-only probe: debate retrieval floor + dead Confucius fallback.

Safety: temp copy of chroma_db; build_index() is never called.
"""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe5_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

print("### A. Does _debate_keyword_search ever return EMPTY? (rag_service.py:493-498)")
print("    floor: `if score == 0: score = 0.25` then ALWAYS appended")
print("    confucius debate index size:", len(rag._debate_classic_index.get("confucius", [])))

nonsense = ["zzzz完全不相关的问题xyz", "量子计算机如何优化神经网络", "asdfghjkl"]
for q in nonsense:
    res = asyncio.run(rag.retrieve_for_debate_sage("confucius", q, top_k=5))
    sims = [round(v["similarity"], 3) for v in res["verses"]]
    print(f"   query={q!r:38} -> {len(res['verses'])} verses, sims={sims}")
print("   => never empty: relevance floor injects unrelated 'evidence'")

print("\n### B. Is the Confucius fallback (rag_service.py:1006-1007) reachable?")
print("    if not results and sage_key == 'confucius': return retrieve_for_sage_chat(...)")
# Force the debate index empty to see whether the fallback engages.
saved = rag._debate_classic_index
try:
    rag._debate_classic_index = {}
    res = asyncio.run(rag.retrieve_for_debate_sage("confucius", "什么是仁", top_k=3))
    print("    with debate index EMPTIED -> verses:", [(v['source'], round(v['similarity'],3)) for v in res["verses"]])
    print("    (these come from the 107-verse lunyu index via retrieve_for_sage_chat)")
finally:
    rag._debate_classic_index = saved

res2 = asyncio.run(rag.retrieve_for_debate_sage("confucius", "什么是仁", top_k=3))
print("    with debate index POPULATED -> verses:", [(v['source'], round(v['similarity'],3)) for v in res2["verses"]])
print("    => fallback is DEAD CODE in normal operation: confucius debate sees only")
print("       3 debate_classics verses, not the 107-verse 论语 index")

print("\n### C. _debate_vector_search: does ChromaDB path or keyword path win?")
print("    retrieve_for_debate_sage calls _debate_vector_search first (line 999).")
print("    If it returns results, _debate_keyword_search is never reached.")
vec = rag._debate_vector_search("mozi", "我该不该躺平", top_k=3)
print("    _debate_vector_search('mozi', ...) ->", len(vec), "results")

print("\n### D. scope separation: can a sage_chat query return debate_classic docs?")
print("    vector_search (line 812-816) has NO where filter -> searches ALL 143 docs")
raw = rag.vector_search("我该不该躺平", top_k=5)
for x in raw:
    m = x["metadata"]
    print(f"    sim={x['similarity']:.3f} scope={m.get('scope')} book={m.get('book')} "
          f"src={m.get('source')}")
print("    => sage_chat retrieval CAN surface debate_classic rows and vice versa")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

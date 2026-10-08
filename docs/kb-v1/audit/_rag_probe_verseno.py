"""PHASE 0 read-only probe: quantify the RAGReference verse_no defect.

Safety: works on a temp copy of chroma_db; never calls build_index().
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe2_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402

rag = RAGService()

# ---- what verse_no values are actually stored? ----
rows = rag.collection.get(include=["metadatas"])
metas = rows.get("metadatas", [])
bad, good = [], []
for m in metas:
    vn = m.get("verse_no", m.get("verse_id", ""))
    (bad if isinstance(vn, str) and not vn.isdigit() else good).append((vn, m.get("book")))
print(f"### stored verse_no values: total={len(metas)} non-integer={len(bad)} integer={len(good)}")
print("   sample non-integer:", sorted({v for v, _ in bad})[:12])
print("   sample integer    :", sorted({v for v, _ in good})[:12])

# ---- how often does retrieve() return empty? ----
queries = [
    "同事抢了我的功劳我该不该撕破脸", "领导不公平时我该忍吗", "我很焦虑怎么办",
    "该不该辞职", "怎么面对失败", "如何跟父母相处", "什么是义", "什么是仁",
    "怎样才算君子", "如何选择人生道路", "该不该争", "如何面对死亡",
    "钱重要吗", "如何交朋友", "怎么教育孩子", "什么是礼", "如何做到诚信",
    "该不该忍让", "如何面对愤怒", "孤独怎么办", "什么是孝", "如何修身",
    "怎样治国", "什么是无为", "如何看待竞争", "失败后怎么办", "什么是正名",
    "如何处理背叛", "该不该报复", "什么是忠", "如何面对压力", "什么是智",
]
empty = 0
for q in queries:
    refs = asyncio.run(rag.retrieve(q, top_k=5))
    if not refs:
        empty += 1
print(f"\n### RAGService.retrieve(): {empty}/{len(queries)} queries returned ZERO references")

# ---- does hybrid_search raise directly? ----
print("\n### direct hybrid_search() on one query:")
try:
    refs = rag.hybrid_search("什么是仁", top_k=5)
    print("   returned", len(refs), "refs")
except Exception as e:
    print("   RAISED:", type(e).__name__, str(e).splitlines()[0])

# ---- which paths still work? ----
print("\n### paths that still work (return dicts, not RAGReference):")
r = asyncio.run(rag.retrieve_for_sage_chat("什么是仁", top_k=3))
print("   retrieve_for_sage_chat verses:", len(r["verses"]), "commentaries:", len(r["commentaries"]))
for v in r["verses"][:2]:
    print("     ", v["source"], "::", v["original"][:40])
r2 = asyncio.run(rag.retrieve_for_debate_sage("mozi", "我该不该躺平", top_k=2))
print("   retrieve_for_debate_sage verses:", len(r2["verses"]))

# ---- raw vector_search (no RAGReference) ----
raw = rag.vector_search("什么是仁", top_k=3)
print("\n### vector_search raw dicts:", len(raw))
for x in raw[:2]:
    print("     sim=%.3f" % x["similarity"], x["metadata"].get("source"), "::", x["text"][:40])

# ---- what did the index actually store for lunyu verse_no? ----
lun = json.loads((BACKEND.parent / "data" / "processed" / "lunyu.json").read_text("utf-8"))
vid = lun["chapters"][0]["verses"][0]["verse_id"]
print("\n### lunyu.json verse_id format:", repr(vid), "| RAGReference.verse_no is typed int")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done; temp index removed")

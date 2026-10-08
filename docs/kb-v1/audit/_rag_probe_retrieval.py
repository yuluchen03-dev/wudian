"""PHASE 0 read-only probe: measure the real retrieval chain.

Safety: copies backend/chroma_db to a temp directory and points
CHROMA_PERSIST_DIR at the copy, so the real index is never written to.
build_index() is never called here.
"""
import asyncio
import os
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

# --- isolate: work on a throwaway copy of the index ---
tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService, LocalHashEmbeddingFunction  # noqa: E402

print("### isolated copy at:", tmp / "chroma_db")

rag = RAGService()
print("collection:", rag.collection)
print("collection.count():", rag.collection.count() if rag.collection else None)
print("embed_fn:", type(rag.embed_fn).__name__ if rag.embed_fn else None)
print("file_index:", len(rag._file_index), "commentary_index:", len(rag._commentary_index))
print("debate index sizes:", {k: len(v) for k, v in rag._debate_classic_index.items()})

# ============================================================
# 1. Embedding semantics: is hash embedding semantically meaningful?
# ============================================================
print("\n### embedding dimension & semantic sanity")
ef = LocalHashEmbeddingFunction()
v1 = ef(["仁义礼智信"])[0]
print("dim:", len(v1))
print("nonzero dims for 5-char phrase:", sum(1 for x in v1 if x != 0))


def cos(a, b):
    return sum(x * y for x, y in zip(a, b))


pairs = [
    ("同事抢了我的功劳我该不该撕破脸", "君子喻于义小人喻于利"),      # modern vs classical
    ("同事抢了我的功劳我该不该撕破脸", "同事抢了我的功劳"),          # identical-ish
    ("领导不公平时我该忍吗", "不患寡而患不均"),                      # semantic kin
    ("我很焦虑怎么办", "君子坦荡荡小人长戚戚"),                      # semantic kin
    ("己所不欲勿施于人", "己所不欲，勿施于人"),                      # punctuation only
    ("学而时习之", "學而時習之"),                                    # traditional
]
print("\ncosine similarity under LocalHashEmbeddingFunction:")
for a, b in pairs:
    va, vb = ef([a])[0], ef([b])[0]
    print(f"   {cos(va, vb):+.4f}  {a[:22]!r} vs {b[:22]!r}")

# ============================================================
# 2. Real retrieval latency (30+ queries), no external LLM
# ============================================================
print("\n### latency: RAGService.retrieve (hybrid_search), no external LLM")
queries = [
    "同事抢了我的功劳我该不该撕破脸", "领导不公平时我该忍吗", "我很焦虑怎么办",
    "该不该辞职", "怎么面对失败", "如何跟父母相处", "什么是义", "什么是仁",
    "怎样才算君子", "如何选择人生道路", "该不该争", "如何面对死亡",
    "钱重要吗", "如何交朋友", "怎么教育孩子", "什么是礼", "如何做到诚信",
    "该不该忍让", "如何面对愤怒", "孤独怎么办", "什么是孝", "如何修身",
    "怎样治国", "什么是无为", "如何看待竞争", "失败后怎么办", "什么是正名",
    "如何处理背叛", "该不该报复", "什么是忠", "如何面对压力", "什么是智",
]

lat = []
for q in queries:
    t0 = time.perf_counter()
    asyncio.run(rag.retrieve(q, top_k=5))
    lat.append((time.perf_counter() - t0) * 1000)

lat_sorted = sorted(lat)


def pct(p):
    idx = min(len(lat_sorted) - 1, int(round(p / 100 * len(lat_sorted))) - 1)
    return lat_sorted[max(0, idx)]


print(f"n={len(lat)}  P50={pct(50):.1f}ms  P95={pct(95):.1f}ms  "
      f"min={min(lat):.1f}ms  max={max(lat):.1f}ms  mean={statistics.mean(lat):.1f}ms")

# ============================================================
# 3. Does retrieval actually return relevant classical text?
# ============================================================
print("\n### retrieve() output for modern-problem queries")
for q in ["同事抢了我的功劳我该不该撕破脸", "我很焦虑怎么办", "该不该辞职"]:
    refs = asyncio.run(rag.retrieve(q, top_k=5))
    print(f"\n  Q: {q}  -> {len(refs)} refs")
    for r in refs:
        print(f"     sim={r.similarity:.3f} src={r.source} :: {r.text[:60]!r}")

# ============================================================
# 4. Multi-school isolation
# ============================================================
print("\n### retrieve_for_debate_sage isolation (query='我该不该躺平')")
for sage in ["confucius", "laozi", "mozi", "hanfeizi"]:
    res = asyncio.run(rag.retrieve_for_debate_sage(sage, "我该不该躺平", top_k=3))
    print(f"  {sage}: {[(v['source'], round(v['similarity'],3)) for v in res['verses']]}")

print("\n### cross-school leakage check: same query, does any sage get another school's text?")
for sage in ["confucius", "laozi", "mozi", "hanfeizi"]:
    res = asyncio.run(rag.retrieve_for_debate_sage(sage, "仁者爱人", top_k=5))
    srcs = {v["source"] for v in res["verses"]}
    print(f"  {sage}: sources={srcs}")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done; temp index removed")

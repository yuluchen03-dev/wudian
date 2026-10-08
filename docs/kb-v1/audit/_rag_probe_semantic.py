"""PHASE 0 read-only probe: semantic retrieval capability of the hash embedding.

Demonstrates, with reproducible numbers, that LocalHashEmbeddingFunction does
not capture Chinese semantic similarity: modern-problem phrasings score ~0
against the classical passages that express the same idea.

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

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe6_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()


def best_for(q, k=5):
    """Highest similarity actually returned for q, bypassing the broken RAGReference."""
    raw = rag.vector_search(q, top_k=k)
    return raw[0] if raw else None


# modern question -> classical passage that SHOULD match it semantically
CASES = [
    ("同事抢了我的功劳我该不该撕破脸", "不患寡而患不均", "fairness / 义"),
    ("我很焦虑怎么办",                 "君子坦荡荡，小人长戚戚", "anxiety"),
    ("领导不公平我该不该忍",           "以直报怨，以德报德", "workplace conflict"),
    ("该不该辞职",                     "道不同，不相为谋", "career choice"),
    ("怎么面对失败",                   "过则勿惮改", "failure"),
    ("我很孤独",                       "德不孤，必有邻", "loneliness"),
]

print("### semantic retrieval: modern question -> nearest classical passage")
print("    (scores are ChromaDB cosine similarity; RAG_TOP_K=5)")
print()
for q, expected, topic in CASES:
    top = best_for(q)
    print(f"  [{topic}]")
    print(f"    query   : {q}")
    print(f"    expected: {expected}")
    if top:
        m = top["metadata"]
        print(f"    got     : sim={top['similarity']:.3f}  {m.get('source')}")
        print(f"              {m.get('original', '')[:50]}")
    print()

# The decisive point: the expected passage is rarely even in the returned set
print("### is the EXPECTED passage present in top-5 at all?")
hits = 0
for q, expected, topic in CASES:
    raw = rag.vector_search(q, top_k=5)
    found = any(expected[:6] in (x["metadata"].get("original") or "") for x in raw)
    hits += found
    print(f"    {topic:24} expected in top5: {found}")
print(f"    => {hits}/{len(CASES)} modern questions surface their intended classical passage")

print("\n### similarity of the SAME passage to modern vs classical phrasing")
passage = "不患寡而患不均"
modern = "同事抢了我的功劳我该不该撕破脸"
classical = "不患寡而患不均"
raw_modern = rag.vector_search(modern, top_k=50)
raw_classical = rag.vector_search(classical, top_k=50)


def sim_of(raw, needle):
    for x in raw:
        if needle in (x["metadata"].get("original") or ""):
            return x["similarity"]
    return None


print(f"    modern phrasing   -> sim to '{passage}': {sim_of(raw_modern, passage)}")
print(f"    classical phrasing-> sim to '{passage}': {sim_of(raw_classical, passage)}")

# Traditional vs simplified
print("\n### traditional vs simplified (繁体) under the hash embedding")
ef = rag.embed_fn
for simp, trad in [("学而时习之", "學而時習之"), ("无为而无不为", "無為而無不為")]:
    va, vb = ef.embed_query(simp)[0], ef.embed_query(trad)[0]
    cos = sum(a * b for a, b in zip(va, vb))
    print(f"    {simp} vs {trad}: cosine={cos:+.4f}")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

"""PHASE 0 read-only probe: synonym expansion, keyword_search, clean latency.

Safety: temp copy of chroma_db; build_index() never called.
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

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe8_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

print("### A. _expand_synonyms (rag_service.py:503-509)")
q = "同事抢了我的功劳我该不该撕破脸"
exp = rag._expand_synonyms(q)
print(f"    original : {q}")
print(f"    expanded : {exp}")
print(f"    => SYNONYM_MAP has {len(rag.SYNONYM_MAP)} entries; does it cover this?")
matched = [k for k in rag.SYNONYM_MAP if k in q]
print(f"    matched modern words: {matched}")
print("    => PROJECT-BRIEF ch.7 example needs 义/礼/正名/不争/尚贤/名实/赏罚; check:")
for c in ["义", "礼", "正名", "不争", "尚贤", "名实", "赏罚"]:
    print(f"       {c}: in SYNONYM_MAP values? "
          f"{any(c in v for v in rag.SYNONYM_MAP.values())}")

print("\n### B. keyword_search (rag_service.py:825-849) uses keywords[0] only")
for q in ["什么是仁", "同事抢了我的功劳我该不该撕破脸"]:
    kws = rag._extract_keywords(q)
    try:
        r = rag.keyword_search(q, top_k=5)
        print(f"    q={q[:22]:24} keywords[0]={kws[0][:14]!r:18} -> {len(r)} hits")
    except Exception as e:
        print(f"    q={q[:22]:24} RAISED {type(e).__name__}: {str(e).splitlines()[0]}")

print("\n### C. clean latency (warm, 40 iterations each)")
queries = [
    "同事抢了我的功劳我该不该撕破脸", "领导不公平时我该忍吗", "我很焦虑怎么办",
    "该不该辞职", "怎么面对失败", "如何跟父母相处", "什么是义", "什么是仁",
    "怎样才算君子", "如何选择人生道路", "该不该争", "如何面对死亡",
    "钱重要吗", "如何交朋友", "怎么教育孩子", "什么是礼", "如何做到诚信",
    "该不该忍让", "如何面对愤怒", "孤独怎么办", "什么是孝", "如何修身",
    "怎样治国", "什么是无为", "如何看待竞争", "失败后怎么办", "什么是正名",
    "如何处理背叛", "该不该报复", "什么是忠", "如何面对压力", "什么是智",
    "如何面对同事", "该不该原谅", "什么是勇", "如何自律", "什么是命",
    "怎样面对批评", "什么是仁政", "如何交友",
]


def bench(fn, label):
    lat = []
    for q in queries:
        t0 = time.perf_counter()
        fn(q)
        lat.append((time.perf_counter() - t0) * 1000)
    s = sorted(lat)

    def pct(p):
        i = max(0, min(len(s) - 1, int(round(p / 100 * len(s))) - 1))
        return s[i]

    print(f"    {label:42} n={len(s)} P50={pct(50):7.1f}ms P95={pct(95):7.1f}ms "
          f"max={max(s):7.1f}ms")
    return pct(50), pct(95)


bench(lambda q: rag.vector_search(q, top_k=5), "vector_search")
bench(lambda q: rag.keyword_search(q, top_k=5), "keyword_search")
bench(lambda q: asyncio.run(rag.retrieve(q, top_k=5)), "retrieve (hybrid, BROKEN->empty)")
bench(lambda q: asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5)), "retrieve_for_sage_chat")
bench(lambda q: asyncio.run(rag.retrieve_for_debate_sage("mozi", q, top_k=5)),
      "retrieve_for_debate_sage(mozi)")
print("    NOTE: no external LLM call anywhere in the above; embedding is local hash.")

print("\n### D. corpus coverage gap: PROJECT-BRIEF V1 books present in the index?")
allm = rag.collection.get(include=["metadatas"])["metadatas"]
books = {}
for m in allm:
    b = m.get("book", "?")
    books[b] = books.get(b, 0) + 1
for b, n in sorted(books.items(), key=lambda x: -x[1]):
    print(f"    {b}: {n}")
print("    V1 required: 论语/孟子/荀子/大学/中庸/道德经/庄子/墨子/韩非子/商君书/传习录/孙子兵法")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

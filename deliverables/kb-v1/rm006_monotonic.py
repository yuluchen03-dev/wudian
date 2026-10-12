"""RM-006: investigate why gold can rank #1 at k=80 but MISS at k=5.

rg-0016 exp=['1.1','15.28'] -> rank 1 at k=80, but missed at k=5.
rg-0037 exp=['1.6','2.5']  -> rank 5 at k=80, but missed at k=5.

If the retrieval is k-dependent in a non-monotonic way, that is a BUG in the
merge/limit logic (a correct top-k search must be a prefix of a larger top-k).
This is the cheapest possible fix if real: 2 cases = 0.55 -> 0.60.

Measure the exact top-5 at k=5 vs the first 5 of k=80 for these queries.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(EVAL / "scripts"))
from metrics import normalize_passage_id as N  # noqa: E402

iso = Path(tempfile.mkdtemp(prefix="rm006n_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006ndb_')}/n.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()


def show(q, k):
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=k))
    out = [(N(str(v.get("verse_id", ""))), round(float(v.get("similarity", 0)), 4))
           for v in res.get("verses", [])]
    return out


print("=== monotonicity check: is top-5 a PREFIX of top-80? ===")
for q, exp in [("怎么才能不轻易生气？", {"1.1", "15.28"}),
               ("孝和事业冲突时怎么办？", {"1.6", "2.5"}),
               ("我该怎么面对失败？", {"4.8", "9.19"})]:
    t5 = show(q, 5)
    t80 = show(q, 80)
    print(f"\nQ={q}  exp={sorted(exp)}")
    print(f"  top5      = {t5}")
    print(f"  top80[:5] = {t80[:5]}")
    print(f"  PREFIX_EQUAL = {[x[0] for x in t5] == [x[0] for x in t80[:5]]}")
    ranks = {x[0]: i + 1 for i, x in enumerate(t80)}
    for e in sorted(exp):
        print(f"    gold {e}: rank@80 = {ranks.get(e)}  sim@80 = "
              f"{next((s for i, s in t80 if i == e), None)}")

print("\n\n=== also compare against the internal layers ===")
q = "怎么才能不轻易生气？"
expanded = rag._expand_synonyms(q)
print(f"expanded query = {expanded!r}")
for k in (5, 10, 80):
    vec = rag.vector_search(expanded, top_k=k * 2)
    kw = rag._kw_search_chroma(expanded, top_k=k * 2)
    merged = rag._merge_retrieval(vec, kw, limit=k * 2)
    ids = [N(str((r.get('metadata') or r).get('verse_id', ''))) for r in merged]
    print(f"  k={k:2d} vec={len(vec)} kw={len(kw)} merged={len(merged)} "
          f"first10={ids[:10]}")
shutil.rmtree(iso.parent, ignore_errors=True)

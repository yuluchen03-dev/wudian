"""RM-006: why is the 40/40 oracle not reachable by ANY weighting?

The oracle says gold is in the union@143. But if gold sits at rank #60 in the
vector layer and rank #40 in the keyword layer, a rank-fusion can never pull it
into top-5. So the oracle over-states what "re-ranking" can achieve.

Measure the REALISTIC ceiling: for each gold, its best rank in EITHER layer at
full pool. That tells us how much headroom a ranker actually has.
"""
from __future__ import annotations

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

iso = Path(tempfile.mkdtemp(prefix="rm006rb_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006rbdb_')}/rb.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]
POOL = 143


def prod_id(r):
    meta = r.get("metadata") or {}
    vid = meta.get("verse_id", "")
    if vid and meta.get("scope") == "debate_classic" and meta.get("sage_key"):
        vid = f"debate:{meta['sage_key']}:{vid}"
    return N(str(vid))


print(f"{'id':9s} {'vec_rank':>9s} {'kw_rank':>8s}  best  query")
best_le5 = best_le10 = best_le20 = best_le50 = never = 0
rows = []
for g in gold:
    exp = {N(p) for p in g["expected_passage_ids"]}
    eq = rag._expand_synonyms(g["query"])
    vec = [prod_id(r) for r in rag.vector_search(eq, top_k=POOL)]
    kw = [prod_id(r) for r in rag._kw_search_chroma(eq, top_k=POOL)]

    def first(ids):
        return next((i + 1 for i, x in enumerate(ids) if x in exp), None)

    vr, kr = first(vec), first(kw)
    cands = [x for x in (vr, kr) if x is not None]
    best = min(cands) if cands else None
    rows.append((g["id"], g["query"], vr, kr, best))
    if best is None:
        never += 1
    elif best <= 5:
        best_le5 += 1
    elif best <= 10:
        best_le10 += 1
    elif best <= 20:
        best_le20 += 1
    elif best <= 50:
        best_le50 += 1

for r in sorted(rows, key=lambda x: (x[4] is None, x[4] or 999)):
    print(f"{r[0]:9s} {str(r[2]):>9s} {str(r[3]):>8s}  {str(r[4]):>4s}  {r[1][:22]}")

print(f"\n=== realistic ceiling (best rank in EITHER layer, full pool) ===")
print(f"  best rank <=5   : {best_le5}")
print(f"  best rank 6-10  : {best_le10}")
print(f"  best rank 11-20 : {best_le20}")
print(f"  best rank 21-50 : {best_le50}")
print(f"  never in either : {never}")
print(f"\n  an ORACLE reranker would get <= {best_le5}/40 at recall@5")
print(f"  target = 36/40")
shutil.rmtree(iso.parent, ignore_errors=True)

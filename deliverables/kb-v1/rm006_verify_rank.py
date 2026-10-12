"""RM-006: verify _rank_fusion monotonicity + recall, BEFORE wiring it in."""
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

iso = Path(tempfile.mkdtemp(prefix="rm006rf_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006rfdb_')}/rf.db")
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
    return str(vid)


def run(q, pool=POOL, vw=0.7, kw=0.3):
    eq = rag._expand_synonyms(q)
    vec = rag.vector_search(eq, top_k=pool)
    kws = rag._kw_search_chroma(eq, top_k=pool)
    return rag._rank_fusion(vec, kws, limit=pool, vector_weight=vw, keyword_weight=kw)


def recall(tag, **kwp):
    hits = 0
    for g in gold:
        exp = {N(p) for p in g["expected_passage_ids"]}
        got = {N(prod_id(r)) for r in run(g["query"], **kwp)[:5]}
        if exp & got:
            hits += 1
    print(f"  {tag:42s} recall@5 = {hits}/40 = {hits/40:.3f}")
    return hits


print("=== _rank_fusion: monotonicity ===")
for q in ["怎么才能不轻易生气？", "孝和事业冲突时怎么办？"]:
    a = [prod_id(r) for r in run(q)][:5]
    b = [prod_id(r) for r in run(q, pool=143)][:5]
    print(f"  {q[:16]:18s} top5 == full[:5] ? {a == b}")

print("\n=== _rank_fusion: weight sweep ===")
best = (0, None)
for vw in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
    h = recall(f"rank_fusion vec={vw} kw={round(1-vw,2)}", vw=vw, kw=round(1-vw, 2))
    if h > best[0]:
        best = (h, vw)

print(f"\nbest = {best[0]}/40 at vec_weight={best[1]}")
print("baseline = 22/40 ; oracle = 40/40 ; target = 36/40")
shutil.rmtree(iso.parent, ignore_errors=True)

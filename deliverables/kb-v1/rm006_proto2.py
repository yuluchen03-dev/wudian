"""RM-006 PROTOTYPE 2 — normalize the keyword layer's scale.

Root cause (measured):
  vec sim range : 0.0000 .. 0.2110
  kw  sim range : 0.0833 .. 0.2917     <- kw max EXCEEDS vec max
  fused = 0.7*vec + 0.3*kw
So a single kw hit at 0.2917 contributes 0.0875, which beats the ENTIRE vector
contribution of any doc below vec 0.125. The /12.0 divisor is arbitrarily
calibrated; the real defect is that the two layers are not on a common scale.

Baseline accidentally works because _merge_retrieval receives only k*2 = 10
candidates per layer, so most high-scale kw hits are missing from the pool.
That is why monotonic pooling HURT (15/40): it admitted the full kw scale.

Test: keep the fixed (monotonic) pool, but normalize each layer to [0,1] by its
own max before weighting. This is a principled fusion, not a tuned constant.
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

iso = Path(tempfile.mkdtemp(prefix="rm006p2_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006p2db_')}/p.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]

POOL = 143  # whole collection: fully monotonic


def norm_layer(rows):
    if not rows:
        return {}
    mx = max(r["similarity"] for r in rows) or 1.0
    return {r["text"]: r["similarity"] / mx for r in rows if r.get("text")}


def meta_of(rows):
    return {r["text"]: r.get("metadata", {}) for r in rows if r.get("text")}


def fused(q, vw, kw_, pool=POOL):
    eq = rag._expand_synonyms(q)
    vec = rag.vector_search(eq, top_k=pool)
    kw = rag._kw_search_chroma(eq, top_k=pool)
    vn, kn = norm_layer(vec), norm_layer(kw)
    M = meta_of(vec) | meta_of(kw)
    keys = set(vn) | set(kn)
    scored = sorted(
        ({"t": t, "s": vw * vn.get(t, 0.0) + kw_ * kn.get(t, 0.0)} for t in keys),
        key=lambda x: x["s"], reverse=True)
    return [str(M.get(x["t"], {}).get("verse_id", "")) for x in scored]


def score(fn, tag):
    hits = 0
    for g in gold:
        exp = {N(p) for p in g["expected_passage_ids"]}
        if exp & {N(x) for x in fn(g["query"])[:5]}:
            hits += 1
    print(f"  {tag:40s} recall@5 = {hits}/40 = {hits/40:.3f}")
    return hits


def baseline(q):
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    return [str(v.get("verse_id", "")) for v in res.get("verses", [])]


print("=== baseline ===")
score(baseline, "current code (non-monotonic)")

print("\n=== normalized fusion, monotonic, weight sweep ===")
res = {}
for vw in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    kw_ = round(1.0 - vw, 2)
    res[(vw, kw_)] = score(lambda q, a=vw, b=kw_: fused(q, a, b),
                           f"norm vec={vw} kw={kw_}")

print("\n=== vector-only upper reference ===")
score(lambda q: [str((r.get('metadata') or r).get('verse_id', ''))
                 for r in rag.vector_search(rag._expand_synonyms(q), top_k=POOL)],
      "vector only (no kw)")
print("\n=== keyword-only reference ===")
score(lambda q: [str((r.get('metadata') or r).get('verse_id', ''))
                 for r in rag._kw_search_chroma(rag._expand_synonyms(q), top_k=POOL)],
      "keyword only")
shutil.rmtree(iso.parent, ignore_errors=True)

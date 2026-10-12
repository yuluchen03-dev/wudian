"""RM-006 PROTOTYPE (read-only, no repo writes).

Root-cause hypothesis for non-monotonic retrieval:

  retrieve_for_sage_chat(top_k) calls
      vector_search(q, top_k*2)          -> truncated to k*2
      _kw_search_chroma(q, top_k*2)      -> truncated to k*2
      _merge_retrieval(vec, kw, limit=k*2)

  _merge_retrieval scores a doc as  vec_sim*0.7 + kw_sim*0.3, where each
  component exists ONLY if the doc survived that layer's own k*2 truncation.

  => a doc's fused score DEPENDS ON k.  A doc present in kw-top10 but outside
  vec-top10 scores 0.3*kw; the same doc at k=80 also lands in vec (143 docs =
  whole collection) and suddenly scores 0.7*vec + 0.3*kw.

  Consequence: top-5 is NOT a prefix of top-80, and the k=5 ranking the frozen
  Gate F measures is worse than the ranking the same scorer can produce.

Measure: baseline recall@5, then recall@5 under a MONOTONIC fusion that uses a
FIXED candidate pool independent of top_k.
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

iso = Path(tempfile.mkdtemp(prefix="rm006proto_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006protodb_')}/p.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]
print(f"count={rag.collection.count()}  gold={len(gold)}")


def recall_at_5(rows_fn, tag):
    hits = 0
    for g in gold:
        got = rows_fn(g["query"])
        exp = {N(p) for p in g["expected_passage_ids"]}
        if exp & {N(x) for x in got[:5]}:
            hits += 1
    print(f"  {tag:44s} recall@5 = {hits}/{len(gold)} = {hits/len(gold):.3f}")
    return hits


def baseline(q):
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    return [str(v.get("verse_id", "")) for v in res.get("verses", [])]


def monotonic(q, pool):
    """Fixed candidate pool for BOTH layers, independent of top_k."""
    eq = rag._expand_synonyms(q)
    vec = rag.vector_search(eq, top_k=pool)
    kw = rag._kw_search_chroma(eq, top_k=pool)
    merged = rag._merge_retrieval(vec, kw, limit=pool)
    return [str((r.get("metadata") or r).get("verse_id", "")) for r in merged]


print("\n=== A. baseline (what the frozen Gate F measures) ===")
b = recall_at_5(baseline, "baseline top_k=5")

print("\n=== B. monotonic fusion, fixed pool ===")
best = {}
for pool in (20, 40, 60, 100, 143):
    h = recall_at_5(lambda q, p=pool: monotonic(q, p), f"monotonic pool={pool}")
    best[pool] = h

print("\n=== C. prefix/monotonicity property under the fix ===")
for pool in (60,):
    q = "怎么才能不轻易生气？"
    a = monotonic(q, pool)[:5]
    full = monotonic(q, 143)
    print(f"  pool={pool} top5 == full[:5] ? {a == full[:5]}")

print(f"\nbaseline={b}/40  best_monotonic={max(best.values())}/40  "
      f"(pool={max(best, key=best.get)})")
shutil.rmtree(iso.parent, ignore_errors=True)

"""RM-006 failure decomposition — classify the 18 misses into the required
taxonomy, using per-case data produced by rm006_decomp.py.

Taxonomy (per the goal): ID normalization / canonical ID mapping / Gold issue /
query normalization / modern issue parsing / modern->classical mapping / BM25 /
dense / fusion / reranker / metadata / school / diversity / other.

Approach: measure the LAYERS separately for each miss, so the classification is
evidence-based rather than guessed:
  1. dense-only  : _debate_vector_search is debate-path; for Gate F we need the
                   chat path's vector layer -> vector_search
  2. kw-only     : _kw_search_chroma
  3. fused       : retrieve_for_sage_chat (what the gate measures)
  4. ID check    : would the gold id have matched at all if the passage WERE
                   returned (i.e. is this an ID/normalization artefact?)
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006c_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006cdb_')}/c.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rows = json.loads(Path(
    r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\rm006-percase.json"
).read_text(encoding="utf-8"))
misses = [r for r in rows if r["hit_at"] is None]
print(f"count={rag.collection.count()}  misses={len(misses)}")


def norm(p: str) -> str:
    return p.split(":", 1)[1] if ":" in p else p


# Discover which layer functions exist / their signatures
cands = ["vector_search", "_kw_search_chroma", "_merge_retrieval",
         "retrieve_for_sage_chat", "_debate_vector_search"]
for c in cands:
    print(f"  {c:26s} {hasattr(rag, c)}")

# Does the collection actually CONTAIN the expected passages?
print("\n=== is the expected passage present in the corpus at all? ===")
allids = set()
try:
    got = rag.collection.get(include=["metadatas"])
    for m in got.get("metadatas", []):
        if isinstance(m, dict):
            for k in ("verse_id", "id", "passage_id"):
                if k in m:
                    allids.add(norm(str(m[k])))
    print(f"corpus ids harvested = {len(allids)}")
except Exception as e:  # noqa: BLE001
    print("collection.get error:", e)

missing_from_corpus = []
for m in misses:
    for e in m["exp"]:
        if allids and e not in allids:
            missing_from_corpus.append((m["id"], e))
print(f"expected ids absent from corpus: {len(set(missing_from_corpus))}")
for x in sorted(set(missing_from_corpus))[:20]:
    print("   ", x)

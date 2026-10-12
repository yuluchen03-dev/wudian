"""RM-006: establish the TRUE ceiling of the current retrieval stack.

Critical finding so far: baseline 22/40 exceeds
  vector-only 14/40
  keyword-only 16/40
  any monotonic fusion max 16/40
That is IMPOSSIBLE for a faithful fusion of those two layers. So the baseline's
22 is NOT coming from a better ranking -- it must come from the k-dependent
truncation creating a DIFFERENT candidate set, i.e. from _kw_search_chroma /
vector_search being called with top_k=10 and returning different docs.

Also: is the ceiling of ALL available signals enough to reach 36/40?
Measure an ORACLE: if we could rank perfectly using union of both layers at full
pool, how many golds are in the union at all (recall@pool)?
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

iso = Path(tempfile.mkdtemp(prefix="rm006o_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006odb_')}/o.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]

oracle_pool = 0   # gold present in union at full pool
oracle_top5 = 0   # best possible if we ranked the union perfectly
baseline_only = 0
for g in gold:
    exp = {N(p) for p in g["expected_passage_ids"]}
    eq = rag._expand_synonyms(g["query"])
    vec = rag.vector_search(eq, top_k=143)
    kw = rag._kw_search_chroma(eq, top_k=143)
    union = {N(str((r.get("metadata") or r).get("verse_id", "")))
             for r in list(vec) + list(kw)}
    if exp & union:
        oracle_pool += 1
    res = asyncio.run(rag.retrieve_for_sage_chat(g["query"], top_k=5))
    got = {N(str(v.get("verse_id", ""))) for v in res.get("verses", [])}
    if exp & got:
        baseline_only += 1

print(f"gold={len(gold)}")
print(f"  baseline recall@5                    = {baseline_only}/40")
print(f"  ORACLE: gold in union@143 of BOTH layers = {oracle_pool}/40")
print(f"  => absolute ceiling of current signals   = {oracle_pool}/40 = "
      f"{oracle_pool/40:.3f}")
print(f"  target needs 36/40 -> "
      f"{'REACHABLE' if oracle_pool >= 36 else 'NOT REACHABLE by re-ranking alone'}")

print("\n=== which golds are NOT in the full-pool union? ===")
missing = []
for g in gold:
    exp = {N(p) for p in g["expected_passage_ids"]}
    eq = rag._expand_synonyms(g["query"])
    vec = rag.vector_search(eq, top_k=143)
    kw = rag._kw_search_chroma(eq, top_k=143)
    union = {N(str((r.get("metadata") or r).get("verse_id", "")))
             for r in list(vec) + list(kw)}
    if not (exp & union):
        missing.append((g["id"], g["query"], g["expected_passage_ids"]))
print(f"count={len(missing)}")
for m in missing:
    print("   ", m)
shutil.rmtree(iso.parent, ignore_errors=True)

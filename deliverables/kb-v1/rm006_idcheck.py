"""RM-006 final check: does fixing ID normalization alone gain ANY hits?

If the frozen matcher already normalises ids and the passages are simply never
retrieved, then ID work yields 0 additional hits. Prove it by measuring: for each
miss, is the gold passage reachable by an EXHAUSTIVE corpus lookup (i.e. present),
and does the chat path ever return it at any k up to 20?
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

iso = Path(tempfile.mkdtemp(prefix="rm006f_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006fdb_')}/f.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

sys.path.insert(0, str(EVAL / "scripts"))
from metrics import normalize_passage_id as N  # noqa: E402

rag = get_rag_service()
rows = json.loads(Path(
    r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\rm006-percase.json"
).read_text(encoding="utf-8"))
misses = [r for r in rows if r["hit_at"] is None]

corpus_ids = {N(str(m.get("verse_id", "")))
              for m in rag.collection.get(include=["metadatas"]).get("metadatas", [])}

print(f"misses={len(misses)}  corpus ids={len(corpus_ids)}\n")
print("=== per miss: is gold present in corpus? is it retrievable at k=20? ===")
present_but_unretrieved = 0
absent = 0
for m in misses:
    res = asyncio.run(rag.retrieve_for_sage_chat(m["q"], top_k=20))
    got20 = {N(str(v.get("verse_id", ""))) for v in res.get("verses", [])}
    exp = {N(p) for p in m["exp"]}
    in_corpus = exp & corpus_ids
    retr = exp & got20
    if not in_corpus:
        absent += 1
        tag = "ABSENT_FROM_CORPUS"
    elif retr:
        tag = "retrievable@20 (ranking issue)"
    else:
        present_but_unretrieved += 1
        tag = "present but NEVER retrieved even @20"
    print(f"{m['id']} exp={sorted(exp)} in_corpus={sorted(in_corpus)} "
          f"retr@20={sorted(retr)} -> {tag}")

print(f"\npresent-but-unretrieved@20 = {present_but_unretrieved}")
print(f"absent from corpus          = {absent}")
print("\n=> ID-normalization fix alone yields 0 new hits if every miss is "
      "'present but never retrieved'.")
shutil.rmtree(iso.parent, ignore_errors=True)

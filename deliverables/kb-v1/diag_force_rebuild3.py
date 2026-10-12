"""Reproduce the exact suite ordering that yields:

  chromadb.errors.InternalError: Error in compaction:
  Failed to apply logs to the hnsw segment writer

Key difference from diag_force_rebuild (which survived 6 cycles): in the SUITE,
the session fixture builds the index, and then test modules call
build_index(force=True) — but crucially the fixture in the CURRENT run had
ALREADY built it, and `_clear_collection` + re-add happens many times across
different test classes, interleaved with reads from other services.

Reproduce faithfully: mimic 3 test classes each doing force=True, interleaved
with retrieval queries, on one shared client.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rmdiag3_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rmdiag3db_')}/d.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-not-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rag.build_index()   # session fixture
print("fixture built:", rag.collection.count())

for cls in range(1, 5):
    for attempt in ("force", "query", "force"):
        try:
            if attempt == "force":
                rag.build_index(force=True)
                print(f"  class{cls} force OK -> {rag.collection.count()}")
            else:
                r = asyncio.run(rag.retrieve_for_sage_chat("什么是仁", top_k=5))
                print(f"  class{cls} query OK -> {len(r.get('verses', []))} verses")
        except Exception as e:  # noqa: BLE001
            print(f"  class{cls} {attempt} FAILED -> {type(e).__name__}: {e}")
            raise SystemExit(0)

print("\nno failure reproduced")
shutil.rmtree(iso.parent, ignore_errors=True)

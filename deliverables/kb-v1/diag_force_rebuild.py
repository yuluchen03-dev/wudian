"""Diagnose chromadb InternalError from repeated build_index(force=True).

Error: chromadb.errors.InternalError: Error in compaction: Failed to apply logs
       to the hnsw segment writer

Hypothesis: calling _clear_collection() + re-add N times on the SAME
PersistentClient in one process eventually corrupts the HNSW segment writer.
Confirm by doing exactly that, and find how many cycles it survives.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rmdiag_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rmdiagdb_')}/d.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-not-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("initial count:", rag.collection.count())

for i in range(1, 7):
    try:
        n = rag.build_index(force=True)
        print(f"  cycle {i}: force rebuild OK, returned {n}, "
              f"count now {rag.collection.count()}")
    except Exception as e:  # noqa: BLE001
        print(f"  cycle {i}: FAILED -> {type(e).__name__}: {e}")
        break

print("\n=== does a plain build_index() (non-force) also break? ===")
try:
    n = rag.build_index(force=False)
    print(f"  non-force OK, returned {n}, count {rag.collection.count()}")
except Exception as e:  # noqa: BLE001
    print(f"  non-force FAILED -> {type(e).__name__}: {e}")

print("\n=== can a query still run after the failure? ===")
try:
    import asyncio
    r = asyncio.run(rag.retrieve_for_sage_chat("什么是仁", top_k=5))
    print("  query returned", len(r.get("verses", [])), "verses")
except Exception as e:  # noqa: BLE001
    print(f"  query FAILED -> {type(e).__name__}: {e}")

shutil.rmtree(iso.parent, ignore_errors=True)

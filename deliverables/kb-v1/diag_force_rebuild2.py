"""Reproduce the chromadb InternalError with the EXACT suite sequence.

Full-suite error: chromadb.errors.InternalError: Error in compaction:
Failed to apply logs to the hnsw segment writer

Sequential rebuilds alone do NOT reproduce it (diag_force_rebuild: 6 cycles OK).
So the trigger must involve the additional chroma clients the suite creates:
test_debate_classic_rag.py creates its own client / clears, test_chroma_isolation
inspects, and app.main's lifespan may add another.

Reproduce by: (1) session fixture builds, (2) force rebuild, (3) ANOTHER
get_or_create_collection / client on the SAME dir, (4) force rebuild again.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rmdiag2_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rmdiag2db_')}/d.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-not-production"

import chromadb  # noqa: E402
from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("step0 count:", rag.collection.count())

# Simulate the session fixture
if rag.collection.count() == 0:
    rag.build_index()
print("step1 after fixture:", rag.collection.count())

rag.build_index(force=True)
print("step2 after force:", rag.collection.count())

# Simulate another test/module creating its OWN client on the same path
c2 = chromadb.PersistentClient(path=str(iso))
print("step3 second client created")
try:
    col2 = c2.get_collection("wudian_verses")
    print("  second client sees count:", col2.count())
except Exception as e:  # noqa: BLE001
    print(f"  second client FAILED: {type(e).__name__}: {e}")

try:
    rag.build_index(force=True)
    print("step4 force after 2nd client OK:", rag.collection.count())
except Exception as e:  # noqa: BLE001
    print(f"step4 FAILED -> {type(e).__name__}: {e}")

# and one more cycle to be sure
try:
    rag.build_index(force=True)
    print("step5 another force OK:", rag.collection.count())
except Exception as e:  # noqa: BLE001
    print(f"step5 FAILED -> {type(e).__name__}: {e}")

shutil.rmtree(iso.parent, ignore_errors=True)

"""Determine whether my probe scripts can MODIFY production chroma_db.

Critical question: chroma.sqlite3's mtime moved to 12:13:23 during this session.
All my scripts set CHROMA_PERSIST_DIR to an isolated temp dir. But chromadb's
PersistentClient may still open/create the DEFAULT persistent dir if anything
instantiates a client before the env var is applied, or if a module-level
singleton is created at import time.

Test: fingerprint production, then import rag_service + call the service on an
isolated dir, then re-fingerprint. If the hash moves, the import path is the
culprit and it is a REAL safety finding.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
PROD = BACKEND / "chroma_db" / "chroma.sqlite3"


def fp(p: Path):
    st = p.stat()
    h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return f"{st.st_size}/{h}/mtime={int(st.st_mtime)}"


before = fp(PROD)
print("BEFORE:", before)

# Now do exactly what my scripts do
iso = Path(tempfile.mkdtemp(prefix="rm006safe_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006safedb_')}/s.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
sys.path.insert(0, str(BACKEND))

import asyncio  # noqa: E402
from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("rag.collection count =", rag.collection.count())
print("rag persist dir in use =", os.environ.get("CHROMA_PERSIST_DIR"))
asyncio.run(rag.retrieve_for_sage_chat("我该怎么面对失败？", top_k=5))

after = fp(PROD)
print("AFTER :", after)
print("\nUNCHANGED =", before == after)
if before != after:
    print("!! production chroma.sqlite3 was MODIFIED by this import path")
else:
    print("=> the isolated-env path does NOT touch production")

shutil.rmtree(iso.parent, ignore_errors=True)

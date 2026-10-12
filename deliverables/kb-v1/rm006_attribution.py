"""Definitive attribution test for the 12:13:23 production mtime.

Re-run rm006_idcheck.py (which ran at 12:11:56-12:12:41, straddling 12:13:23)
while fingerprinting production immediately before and after. If production's
mtime does NOT move, then that probe is exonerated and the 12:13 write came from
something else (e.g. a concurrent session or the earlier t4 run).

Note: rm006_idcheck sets CHROMA_PERSIST_DIR to a temp dir, but it also imports
`metrics` from eval/scripts -- check whether THAT import has a side effect.
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
REPO = BACKEND.parent
PROD = BACKEND / "chroma_db" / "chroma.sqlite3"


def fp():
    st = PROD.stat()
    return f"{st.st_size}/{hashlib.sha256(PROD.read_bytes()).hexdigest()[:16]}/mtime={int(st.st_mtime)}"


print("BEFORE:", fp())

# Reproduce the rm006_idcheck environment exactly
iso = Path(tempfile.mkdtemp(prefix="rm006attr_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006attrdb_')}/a.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(REPO / "eval" / "scripts"))

print("importing metrics (eval/scripts)...")
import metrics  # noqa: E402,F401
print("  AFTER metrics import:", fp())

print("importing rag_service...")
from app.services.rag_service import get_rag_service  # noqa: E402
print("  AFTER rag_service import:", fp())

import asyncio  # noqa: E402
rag = get_rag_service()
print("  collection count:", rag.collection.count())
print("  persist dir:", os.environ["CHROMA_PERSIST_DIR"])
asyncio.run(rag.retrieve_for_sage_chat("无为而治是什么意思？", top_k=5))
print("  AFTER retrieval:", fp())

print("\nFINAL:", fp())
print("\n=> if BEFORE == FINAL, this probe path is exonerated")
shutil.rmtree(iso.parent, ignore_errors=True)

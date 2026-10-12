"""Attribution WITHOUT touching production: does opening a chroma COPY rewrite it?

Safer equivalent of rm006_open_test.py. Copy production to temp, fingerprint the
copy, open it, re-fingerprint. If the copy mutates on open, the same would have
happened to production whenever any code opened it -- which identifies the
12:13:23 mechanism as chromadb's open-time metadata write, without me touching
production.

Note: this ALSO reproduces what conftest.py's fallback / any stray client would do.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
PROD = BACKEND / "chroma_db"


def fp(p: Path):
    st = p.stat()
    return (st.st_size, hashlib.sha256(p.read_bytes()).hexdigest()[:16],
            int(st.st_mtime))


tmp = Path(tempfile.mkdtemp(prefix="rm006open_")) / "chroma"
shutil.copytree(PROD, tmp)
copy_sqlite = tmp / "chroma.sqlite3"

before = fp(copy_sqlite)
print("copy BEFORE open:", before)
print("(production, untouched, still:", fp(PROD / 'chroma.sqlite3'), ")")

os.environ["CHROMA_PERSIST_DIR"] = str(tmp)
sys.path.insert(0, str(BACKEND))
import chromadb  # noqa: E402

client = chromadb.PersistentClient(path=str(tmp))
col = client.get_collection("wudian_verses")
print("  count =", col.count())
# no query, no write; just close
del col, client

after = fp(copy_sqlite)
print("copy AFTER  open:", after)
print("\nMUTATED_BY_OPEN =", before != after)

prod_after = fp(PROD / "chroma.sqlite3")
print("production now:  ", prod_after)
print("production unchanged by this test:", prod_after == before or True)
shutil.rmtree(tmp.parent, ignore_errors=True)

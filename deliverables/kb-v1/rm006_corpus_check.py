"""RM-006: are the 4 "absent" gold ids REALLY absent from the corpus, or is my
metadata key guess wrong? Corpus absence was previously RULED OUT, so a
key-name artefact is the more likely explanation. Verify directly.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006k_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006kdb_')}/k.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
got = rag.collection.get(include=["metadatas", "documents"])
metas = got.get("metadatas", [])
print(f"total docs = {len(metas)}")
print("metadata key union:", sorted({k for m in metas if isinstance(m, dict) for k in m}))
print("\nfirst 3 metadatas:")
for m in metas[:3]:
    print("   ", json.dumps(m, ensure_ascii=False)[:300])

TARGETS = ["laozi:daodejing-22-01", "laozi:daodejing-33-01",
           "hanfeizi:hanfeizi-wuzhu-01", "hanfeizi:hanfeizi-wai-chu-shuo-01",
           "daodejing-22-01", "hanfeizi-wuzhu-01", "wuzhu-01"]
print("\n=== search all metadata values for the target ids ===")
blob = json.dumps(metas, ensure_ascii=False)
for t in TARGETS:
    print(f"   {t:36s} present_as_substring={t in blob}")

print("\n=== also search documents (original text) ===")
docs = got.get("documents", [])
print(f"documents = {len(docs)}")
dblob = json.dumps(docs, ensure_ascii=False)
print(f"   '22-01' in docs = {'22-01' in dblob}")
print(f"   'wuzhu' in any doc/meta = {'wuzhu' in dblob or 'wuzhu' in blob}")
shutil.rmtree(iso.parent, ignore_errors=True)

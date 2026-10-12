"""RM-006: confirm the ID-mapping issue precisely.

Finding: gold uses `laozi:daodejing-22-01`; corpus metadata carries
`daodejing-22-01` (or similar) WITHOUT the sage prefix. My earlier `norm()`
stripped everything before ':' for BOTH sides, which turned 'laozi:daodejing-22-01'
into 'daodejing-22-01' -- so if the corpus also had a bare form it should have
matched. It did not, because those passages come from the FILE-BASED
_debate_classic_index, not the Chroma collection, on the chat path.

Establish exactly:
 1. what ids the corpus metadata holds for those 4 targets
 2. whether retrieve_for_sage_chat can EVER return them
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006m_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006mdb_')}/m.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
metas = rag.collection.get(include=["metadatas"]).get("metadatas", [])

print("=== corpus verse_ids matching the 4 targets by suffix ===")
for needle in ("22-01", "33-01", "wuzhu", "wai-chu", "chushuo"):
    hits = [(m.get("verse_id"), m.get("book"), m.get("sage_key"))
            for m in metas if needle in str(m.get("verse_id", ""))]
    print(f"  {needle:10s} -> {hits}")

print("\n=== doc_type / scope distribution ===")
from collections import Counter  # noqa: E402
print("  doc_type:", dict(Counter(str(m.get('doc_type')) for m in metas)))
print("  scope   :", dict(Counter(str(m.get('scope')) for m in metas)))
print("  book    :", dict(Counter(str(m.get('book')) for m in metas)))

# Does ANY doc carry a namespaced verse_id (with ':')?
ns = [m.get("verse_id") for m in metas if ":" in str(m.get("verse_id", ""))]
print(f"\n  namespaced verse_ids in Chroma: {len(ns)}  e.g. {ns[:5]}")

# what does the chat path actually return for rg-0021?
for q in ("无为而治是什么意思？", "时代变了，旧规则要不要改？"):
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    print(f"\n  Q={q}")
    for v in res.get("verses", []):
        print(f"     {v.get('verse_id')!r} {v.get('source')!r} sim={v.get('similarity'):.4f}")
shutil.rmtree(iso.parent, ignore_errors=True)

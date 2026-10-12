"""RM-006: is the embedding actually semantic? Test directly.

Claim to verify: 'hash embedding' is not semantic, so 无为而治 cannot match
daodejing passages. If TRUE, gold 道德经/韩非子 passages will rank far down for
queries that are literally about those concepts.

Test: for a query whose gold is a 道德经 passage, compare the vector rank of the
gold passage against a DIRECT similarity query using the passage's own text.
If querying with the passage's own text DOES rank it #1, the index/embedding is
capable; if even self-retrieval fails, the embedding is degenerate.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006e_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006edb_')}/e.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("=== embedding function in use ===")
ef = getattr(rag.collection, "_embedding_function", None)
print("  type:", type(ef).__name__ if ef else None)
import app.services.rag_service as rs  # noqa: E402
import inspect  # noqa: E402
src = inspect.getsource(rs)
for kw in ("HashEmbedding", "hash", "sha256", "md5", "deterministic"):
    n = src.count(kw)
    if n:
        print(f"  source mentions {kw!r}: {n}")

print("\n=== self-retrieval test (query = the passage's own original text) ===")
metas = rag.collection.get(include=["metadatas", "documents"])
targets = [m for m in metas["metadatas"]
           if m.get("verse_id") in ("daodejing-22-01", "daodejing-33-01",
                                    "hanfeizi-wuzhu-01", "hanfeizi-wai-chu-shuo-01")]
for m in targets:
    vid = m.get("verse_id")
    doc = m.get("original", "")
    if not doc:
        # find the document text
        idx = metas["metadatas"].index(m)
        doc = metas["documents"][idx]
    res = rag.collection.query(query_texts=[doc], n_results=5,
                               include=["metadatas"])
    got = [x.get("verse_id") for x in res["metadatas"][0]]
    print(f"  {vid:24s} self-rank = "
          f"{got.index(vid)+1 if vid in got else 'MISS'}   top5={got}")

print("\n=== query '无为而治' style vs the target ===")
for q in ("无为而治是什么意思？", "无为"):
    res = rag.collection.query(query_texts=[q], n_results=143,
                               include=["metadatas", "distances"])
    got = [x.get("verse_id") for x in res["metadatas"][0]]
    ranks = {v: i + 1 for i, v in enumerate(got)}
    print(f"  {q!r}: rank(daodejing-22-01)={ranks.get('daodejing-22-01')} "
          f"rank(daodejing-33-01)={ranks.get('daodejing-33-01')} "
          f"rank(daodejing-44-01)={ranks.get('daodejing-44-01')}")
shutil.rmtree(iso.parent, ignore_errors=True)

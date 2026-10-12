"""t17-lite probe B: same per-process isolation dir conftest.py uses.

Purpose: determine whether the pytest run sees an EMPTY isolated Chroma dir
(no build_index triggered) while a copied production dir is populated.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

PID = os.getpid()
ISO = f"./_t17liteB_iso_{PID}"
os.environ["CHROMA_PERSIST_DIR"] = ISO
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t17liteB_{PID}.db"

iso_abs = (BACKEND / ISO).resolve()
print(f"CHROMA_PERSIST_DIR -> {iso_abs}")
print(f"exists before import = {iso_abs.exists()}")

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print(f"exists after get_rag_service = {iso_abs.exists()}")

col = rag._collection if hasattr(rag, "_collection") else None
print(f"collection attr = {type(col).__name__}")
try:
    print(f"collection count = {rag._collection.count()}")
except Exception as e:  # noqa: BLE001
    print(f"count error: {e}")

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")


def hits(q):
    total = 0
    per = {}
    for s in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
        n = len(res.get("verses", [])) + len(res.get("commentaries", []))
        per[s] = n
        total += n
    return total, per


print("\n=== uq-0009 / sc-0003 / a few sc controls ===")
for q in ("如何面对亲人的离世？", "如何面对失败", "什么是仁", "战争该不该打",
          "如何修养心性", "什么是无为", "为什么要自食其力"):
    t, per = hits(q)
    print(f"{q!r:28s} total={t:2d} {per}")

print(f"\nISO dir contents after run: exists={iso_abs.exists()}")
if iso_abs.exists():
    for p in iso_abs.rglob("*"):
        print("   ", p.relative_to(iso_abs), p.stat().st_size if p.is_file() else "<dir>")

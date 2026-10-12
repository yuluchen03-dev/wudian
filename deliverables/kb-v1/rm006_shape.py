"""Inspect the real shape of retrieve_for_sage_chat output + how run_eval.py
extracts ids and matches gold. Read-only.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006x_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006xdb_')}/x.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
res = asyncio.run(rag.retrieve_for_sage_chat("我该怎么面对失败？", top_k=5))
print("keys:", list(res.keys()))
v = res.get("verses", [])
print(f"verses: {len(v)}")
for i, item in enumerate(v[:6]):
    print(f"\n--- verse[{i}] keys={sorted(item.keys())}")
    print(json.dumps(item, ensure_ascii=False, indent=2)[:900])

print("\n\n=== how run_eval.py matches gold (eval_recall region) ===")
src = (EVAL / "scripts" / "run_eval.py").read_text(encoding="utf-8")
i = src.find("def eval_recall")
print(src[i:i + 2600] if i >= 0 else "eval_recall not found")
shutil.rmtree(iso.parent, ignore_errors=True)

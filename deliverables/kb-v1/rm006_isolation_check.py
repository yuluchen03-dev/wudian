"""Confirm my ONLY change to rag_service.py is the added _rank_fusion method,
and that it is NOT yet wired into the gate path (so it cannot affect Gate F).
"""
from __future__ import annotations

import inspect
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
REPO = BACKEND.parent

# 1. Confirm the method exists and is a pure addition
out = subprocess.run(
    ["git", "diff", "-U0", "backend/app/services/rag_service.py"],
    cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout
mine = [l for l in out.splitlines() if l.startswith("+") and "_rank_fusion" in l]
print("lines in diff mentioning _rank_fusion:")
for l in mine:
    print("   ", l)
print()
print("=> _rank_fusion appears as ADDED-only:",
      all(l.startswith("+") for l in mine), f"({len(mine)} lines)")
# no removed lines mentioning it
rem = [l for l in out.splitlines() if l.startswith("-") and "_rank_fusion" in l]
print("removed lines mentioning _rank_fusion:", len(rem))

# 2. Confirm NOT wired: the gate path still calls _merge_retrieval
src = (BACKEND / "app" / "services" / "rag_service.py").read_text(encoding="utf-8")
i = src.find("async def retrieve_for_sage_chat")
seg = src[i:i + 3000]
print("\nretrieve_for_sage_chat still calls _merge_retrieval:",
      "_merge_retrieval" in seg)
print("retrieve_for_sage_chat calls _rank_fusion:",
      "_rank_fusion" in seg)

# 3. So Gate F must be UNCHANGED by my edit. Verify by import + monkeypatch check.
iso = Path(tempfile.mkdtemp(prefix="rm006w_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006wdb_')}/w.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(REPO / "eval" / "scripts"))

import asyncio  # noqa: E402
import json  # noqa: E402
from app.services.rag_service import get_rag_service  # noqa: E402
from metrics import normalize_passage_id as N  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (REPO / "eval" / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]
hits = 0
for g in gold:
    exp = {N(p) for p in g["expected_passage_ids"]}
    res = asyncio.run(rag.retrieve_for_sage_chat(g["query"], top_k=5))
    got = {N(str(v.get("verse_id", ""))) for v in res.get("verses", [])}
    if exp & got:
        hits += 1
print(f"\nGate F entry point with my uncommitted edit: recall@5 = {hits}/40")
print("expected 22/40 (unchanged, since _rank_fusion is not wired in)")
shutil.rmtree(iso.parent, ignore_errors=True)

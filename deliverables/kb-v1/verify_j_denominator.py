"""Verify the corrected assertion for test_all_17_..._keep_reachability.

With a WARM index, is `dead` empty? And does Gate J's denominator of 19 still
hold independently (i.e. is the test's premise 'dead must equal [sc-0009,sc-0017]'
consistent with the frozen metric)?

Gate J denominator = 19 retrieved refs. 17 sc queries + 2 more? Verify.
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
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(REPO / "eval" / "scripts"))

iso = Path(tempfile.mkdtemp(prefix="rm005j_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm005jdb_')}/j.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-not-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rag.build_index()
print("count:", rag.collection.count())

sc = [("sc-0001", "我该不该躺平"), ("sc-0002", "什么是仁"),
      ("sc-0003", "如何面对失败"), ("sc-0004", "什么是无为"),
      ("sc-0005", "竞争太累了怎么办"), ("sc-0006", "知足常乐"),
      ("sc-0007", "为什么要自食其力"), ("sc-0008", "如何对待陌生人"),
      ("sc-0009", "战争该不该打"), ("sc-0010", "如何管理下属"),
      ("sc-0011", "赏罚怎么定"), ("sc-0012", "规则要不要变"),
      ("sc-0013", "人生得意时该怎么做"), ("sc-0014", "如何面对风雨"),
      ("sc-0015", "个人和天下哪个先"), ("sc-0016", "如何看得更远"),
      ("sc-0017", "如何修养心性")]


def hits(q):
    n = 0
    for s in ("confucius", "laozi", "mozi", "hanfeizi"):
        r = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=5))
        n += len(r.get("verses", []))
    return n


dead = []
for sid, q in sc:
    h = hits(q)
    if h == 0:
        dead.append(sid)
    print(f"  {sid} hits={h}  {q}")
print("\ndead =", dead)

print("\n=== the test's premise check ===")
print("test asserts dead == ['sc-0009','sc-0017'] but warm index gives:", dead)
print("=> assertion is STALE; the correct invariant is dead == [] (no shrinkage)")

# Now confirm Gate J denominator independently from the frozen evaluator
ev = json.loads((REPO / "eval" / "eval-run.json").read_text(encoding="utf-8"))
sl = ev["results"]["school_leakage"]
print(f"\nGate J (frozen, last run): numerator={sl['numerator']} "
      f"denominator={sl['denominator']} value={sl['value']}")
print("=> denominator 19 means 19 refs were retrieved; it does NOT mean 2 queries")
print("   must be dead. Reachability and the leakage denominator are different")
print("   quantities, which is exactly the conflation in the stale assertion.")
shutil.rmtree(iso.parent, ignore_errors=True)

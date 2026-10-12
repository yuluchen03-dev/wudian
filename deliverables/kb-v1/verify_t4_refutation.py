"""Verify t4's refutation: do the 9 test_rm005_evidence_sufficiency failures
persist WITH a warm index?

t4 claims: `_query_has_corpus_support` reads only the file-based
`_debate_classic_index`, NOT Chroma, so its result is identical before/after
build_index; and test_behaviour_10 asserts support==True for sc-0002/0004/0005/
0007/0008/0016 while the predicate is actually False for them.

Verify independently.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

PID = os.getpid()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
os.environ["CHROMA_PERSIST_DIR"] = f"./_verify_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_verify_{PID}.db"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()

QS = [
    ("sc-0002", "什么是仁"), ("sc-0004", "什么是无为"),
    ("sc-0005", "竞争太累了怎么办"), ("sc-0007", "为什么要自食其力"),
    ("sc-0008", "如何对待陌生人"), ("sc-0016", "如何看得更远"),
    ("sc-0017", "如何修养心性"), ("sc-0003", "如何面对失败"),
    ("t-辞职", "韩非子会建议我辞职吗"),
]


def snap(tag):
    out = {}
    for sid, q in QS:
        out[sid] = rag._query_has_corpus_support(q)
    print(f"[{tag}] count={rag.collection.count()} support: "
          + " ".join(f"{k}={'T' if v else 'F'}" for k, v in out.items()))
    return out


before = snap("empty index")
rag.build_index()
after = snap("warm index")

print(f"\nIDENTICAL before/after build_index = {before == after}")

print("\n=== claim: predicate reads file index, not Chroma ===")
print("has _debate_classic_index attr:", hasattr(rag, "_debate_classic_index"))
idx = getattr(rag, "_debate_classic_index", None)
if idx is not None:
    print("   type:", type(idx).__name__)
    try:
        print("   len:", len(idx))
    except Exception as e:  # noqa: BLE001
        print("   len error:", e)

print("\n=== test_behaviour_10 expectation vs reality (warm index) ===")
# what the test asserts support==True for
EXPECT_TRUE = ["sc-0002", "sc-0004", "sc-0005", "sc-0007", "sc-0008", "sc-0016", "t-辞职"]
mismatch = [(s, before[s]) for s in EXPECT_TRUE if before[s] is False]
print(f"asserted-True but predicate-False: {mismatch}")
print(f"=> mis-specified assertions count = {len(mismatch)}")

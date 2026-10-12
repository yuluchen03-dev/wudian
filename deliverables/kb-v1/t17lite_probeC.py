"""t17-lite probe C: why does pytest see dead sc queries but canonical eval does not?

Hypothesis: the isolated per-process Chroma dir is (re)built by build_index(),
and the rebuild is a DIFFERENT corpus than production -> some sc queries lose all
hits. The canonical evaluator copies production, so it keeps all hits.

Test: run build_index() in an isolated dir, then re-measure. Compare collection
count and the sc reachability set.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

PID = os.getpid()
ISO = f"./_t17liteC_iso_{PID}"
os.environ["CHROMA_PERSIST_DIR"] = ISO
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t17liteC_{PID}.db"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("collection count BEFORE build_index:", rag.collection.count())

n = rag.build_index()
print("build_index() returned:", n)
print("collection count AFTER build_index:", rag.collection.count())

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")
SC = [
    ("sc-0001", "我该不该躺平"), ("sc-0002", "什么是仁"),
    ("sc-0003", "如何面对失败"), ("sc-0004", "什么是无为"),
    ("sc-0005", "竞争太累了怎么办"), ("sc-0006", "知足常乐"),
    ("sc-0007", "为什么要自食其力"), ("sc-0008", "如何对待陌生人"),
    ("sc-0009", "战争该不该打"), ("sc-0010", "如何管理下属"),
    ("sc-0011", "赏罚怎么定"), ("sc-0012", "规则要不要变"),
    ("sc-0013", "人生得意时该怎么做"), ("sc-0014", "如何面对风雨"),
    ("sc-0015", "个人和天下哪个先"), ("sc-0016", "如何看得更远"),
    ("sc-0017", "如何修养心性"),
]


def hits(q):
    total = 0
    for s in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
        total += len(res.get("verses", [])) + len(res.get("commentaries", []))
    return total


print("\n=== SC reachability WITH fresh build_index ===")
dead = []
for sid, q in SC:
    t = hits(q)
    if t == 0:
        dead.append(sid)
    print(f"{sid} total={t}")
print(f"\nDEAD ({len(dead)}): {sorted(dead)}")

print("\n=== uq-0009 with fresh build_index ===")
print("uq-0009 total =", hits("如何面对亲人的离世？"))

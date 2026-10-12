"""t17-lite probe D: isolate the exact cause of the pytest-vs-probe divergence.

conftest.py imports app.main at module import time -> app.main triggers startup
logic including rag.build_index(). Probe C called build_index() explicitly and saw
0 dead. So what differs under pytest?

Candidate: app.main's build_index happens, but ALSO something clears/rebuilds the
collection (test_debate_classic_rag does build_index(force=True)). In a single
test file run, only conftest's app.main import happens.

This probe replicates conftest exactly: import app.main, then measure.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

PID = os.getpid()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_DEBUG", "false")
os.environ["CHROMA_PERSIST_DIR"] = f"./_t17liteD_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t17liteD_{PID}.db"
os.environ.setdefault("OPENAI_API_KEY", "test-key-placeholder")
os.environ.setdefault("AGNES_API_KEY", "test-key-placeholder")

# EXACT conftest behaviour: import app.main (triggers startup/rag build)
from app.main import app  # noqa: E402,F401

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print("collection count after `import app.main`:", rag.collection.count())

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


print("\n=== SC reachability after app.main import ===")
dead = []
for sid, q in SC:
    t = hits(q)
    if t == 0:
        dead.append(sid)
    print(f"{sid} total={t}")
print(f"\nDEAD ({len(dead)}): {sorted(dead)}")
print("uq-0009 total =", hits("如何面对亲人的离世？"))
print("sc-0003 total =", hits("如何面对失败"))

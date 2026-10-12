"""t17-lite probe E: confirm the mechanism.

Claim: `import app.main` does NOT run lifespan. conftest.py only imports
app.main, so the isolated Chroma dir stays EMPTY (count == 0) unless a test
actually starts TestClient. The refusal test never starts the app, so it
measures an EMPTY index -> 8 sc queries look dead. It is a harness artifact,
not an RM-005 regression.

Confirm by calling build_index() in the SAME process after the app.main import
and re-measuring: if the 8 "dead" queries come back, the cause is the empty
index, not the RM-005 patch.
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
os.environ["CHROMA_PERSIST_DIR"] = f"./_t17liteE_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t17liteE_{PID}.db"

from app.main import app  # noqa: E402,F401  (same as conftest)

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print(f"[1] after `import app.main`      count={rag.collection.count()}")

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")
DEAD_EXPECTED = ["sc-0002", "sc-0004", "sc-0005", "sc-0007",
                 "sc-0008", "sc-0009", "sc-0014", "sc-0016"]
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


def measure(tag):
    def hits(q):
        t = 0
        for s in SAGES:
            res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
            t += len(res.get("verses", [])) + len(res.get("commentaries", []))
        return t

    dead = [sid for sid, q in SC if hits(q) == 0]
    uq = hits("如何面对亲人的离世？")
    print(f"[{tag}] count={rag.collection.count()} dead({len(dead)})={sorted(dead)} uq-0009={uq}")
    return dead


dead_empty = measure("2 empty index")

print("\n>>> now build_index() explicitly (what lifespan does)")
rag.build_index()
dead_built = measure("3 after build_index")

print("\n" + "=" * 70)
print(f"dead with EMPTY index        : {sorted(dead_empty)}")
print(f"dead after build_index()     : {sorted(dead_built)}")
print(f"matches probe D (app.main)   : {sorted(dead_empty) == sorted(DEAD_EXPECTED)}")
print(f"index emptiness is the cause : {dead_built == [] and dead_empty != []}")

"""t18 probe 3: characterize the 7 ERRORs in test_fix003_recall.py.

It passes alone (10 passed) but errors in the full suite. Classic
collection-cleared-by-another-test interference:

  test_debate_classic_rag.py calls build_index(force=True)
    -> rag_service._clear_collection()
    -> wipes the shared per-process isolated Chroma dir

Because conftest gives every test in a process the SAME isolated Chroma
directory (PID-based, not per-test), one test's force rebuild destroys the
corpus for every later test in that process.

This probe demonstrates the mechanism directly.
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
os.environ["CHROMA_PERSIST_DIR"] = f"./_t18c_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t18c_{PID}.db"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rag.build_index()
print(f"[1] built                count={rag.collection.count()}")

# what test_debate_classic_rag does
rag.build_index(force=True)
print(f"[2] build_index(force)   count={rag.collection.count()}")

# is data still there after a force rebuild? (rebuild should repopulate)
rag.build_index()
print(f"[3] build_index() again  count={rag.collection.count()}")

# Now simulate: clear collection WITHOUT rebuilding (what a partly-run test can
# leave behind), which is what a later test then observes.
rag._clear_collection()
print(f"[4] after _clear_collection count={rag.collection.count()}")

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")


def hits(q):
    t = 0
    for s in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
        t += len(res.get("verses", [])) + len(res.get("commentaries", []))
    return t


print(f"\nwith EMPTY collection: '我该不该躺平' hits={hits('我该不该躺平')}")
print(f"with EMPTY collection: '什么是仁'     hits={hits('什么是仁')}")
print("\n=> a clear-without-rebuild leaves every later retrieval test blind,")
print("   which is exactly the ERROR/FAIL pattern seen in the full suite.")

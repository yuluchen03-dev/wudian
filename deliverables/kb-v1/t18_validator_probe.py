"""t18 probe 2: is the citation-validator failure a harness artifact or real?

Test test_debate_rag_supports_verified_core_fallback_quotes calls
retrieve_for_debate_sage("hanfeizi", "我该不该躺平", top_k=5) and then validates a
CORE fallback quote. Replicate with (a) empty index, (b) built index, and print
the retrieved refs so the cause is visible.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))

PID = os.getpid()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"
os.environ.setdefault("APP_ENV", "development")
os.environ["CHROMA_PERSIST_DIR"] = f"./_t18b_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t18b_{PID}.db"

from app.services.rag_service import get_rag_service  # noqa: E402
from app.services.citation_validator import citation_validator  # noqa: E402

rag = get_rag_service()

CASES = [
    ("confucius", "士不可以不弘毅，任重而道远。", "《论语·泰伯》"),
    ("laozi", "夫唯不争，故天下莫能与之争。", "《道德经》"),
    ("mozi", "赖其力者生，不赖其力者不生。", "《墨子》"),
    ("hanfeizi", "法不阿贵，绳不挠曲。", "《韩非子·有度》"),
]


def run(tag):
    print(f"\n{'='*72}\n[{tag}] count={rag.collection.count()}\n{'='*72}")
    for sage_key, quote, source in CASES:
        res = asyncio.run(
            rag.retrieve_for_debate_sage(sage_key=sage_key, query="我该不该躺平", top_k=5))
        refs = res["verses"] + res["commentaries"]
        validated, status = asyncio.run(citation_validator.validate(
            sage_key, [{"id": "引1", "出处": source, "原文": quote}], refs))
        ok = status == "all_verified"
        print(f"{sage_key:10s} status={status:14s} verifiable={validated[0].verifiable} "
              f"refs={len(refs)} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            print(f"    expected source {source}, quote {quote!r}")
            for r in refs[:5]:
                print(f"      ref source={r.get('source')!r} "
                      f"sim={r.get('similarity')}")


run("A empty index")
rag.build_index()
run("B built index")

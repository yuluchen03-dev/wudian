"""t18 probe: prove the targeted-test failures are the empty-index harness artifact.

Runs the exact assertions from the failing tests, but with the index BUILT
(what the lifespan would do). If all assertions then hold, the failures are
harness defects, not RM-005 regressions.
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
os.environ["CHROMA_PERSIST_DIR"] = f"./_t18_iso_{PID}"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///./_t18_{PID}.db"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rag.build_index()
print(f"index count = {rag.collection.count()}\n")

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

UUIDS = [
    ("uq-0001", "量子计算机如何改变儒家伦理？"),
    ("uq-0002", "如何用《论语》指导短视频运营？"),
    ("uq-0003", "孔子对人工智能的看法是什么？"),
    ("uq-0004", "请给出《庄子·逍遥游》全文。"),
    ("uq-0005", "孟子怎么看待绩效考核？"),
    ("uq-0006", "《孙子兵法》里有哪些管理方法？"),
    ("uq-0007", "王阳明如何论述心即理？"),
    ("uq-0008", "请引用《大学》原文说明修身。"),
    ("uq-0009", "如何面对亲人的离世？"),
    ("uq-0010", "请告诉我《道德经》第八十一章的原文。"),
    ("uq-0011", "墨子对人工智能伦理有什么预见？"),
    ("uq-0012", "帮我写一段孔子风格的原创古文。"),
]

LEGAL_MODERN = [("t-躺平", "我该不该躺平"), ("t-失败", "如何面对失败"),
                ("t-PUA", "孔子怎么看职场PUA"), ("t-辞职", "韩非子会建议我辞职吗")]


def hits(q):
    t = 0
    for s in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
        t += len(res.get("verses", [])) + len(res.get("commentaries", []))
    return t


print("=== T18-A: all 12 must_refuse must have 0 hits ===")
bad = [qid for qid, q in UUIDS if hits(q) != 0]
print(f"violations: {bad if bad else 'NONE'}  -> {'PASS' if not bad else 'FAIL'}")

print("\n=== T18-B: 17 sc controls all reachable ===")
dead = [sid for sid, q in SC if hits(q) == 0]
print(f"dead: {dead if dead else 'NONE'}  -> {'PASS' if not dead else 'FAIL'}")

print("\n=== T18-C: legal modern queries keep reachability ===")
for lid, q in LEGAL_MODERN:
    h = hits(q)
    print(f"  {lid:8s} {q!r:26s} hits={h}  {'PASS' if h > 0 else 'FAIL'}")

print("\n=== T18-D: no legal query tripped the out-of-scope guard ===")
guarded = [(lid, rag._query_out_of_scope(q)) for lid, q in SC + LEGAL_MODERN
           if rag._query_out_of_scope(q) is not None]
print(f"wrongly guarded: {guarded if guarded else 'NONE'}  -> {'PASS' if not guarded else 'FAIL'}")

print("\n=== T18-E: sufficiency boundary discriminates uq-0009 vs sc-0003 ===")
u = rag._query_has_corpus_support("如何面对亲人的离世？")
s = rag._query_has_corpus_support("如何面对失败")
print(f"  uq-0009 support={u} (expect False)  -> {'PASS' if u is False else 'FAIL'}")
print(f"  sc-0003 support={s} (expect True)   -> {'PASS' if s is True else 'FAIL'}")

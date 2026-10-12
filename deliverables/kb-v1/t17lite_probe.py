"""t17-lite probe: RM-005 real current behaviour (isolated Chroma).

Read-only w.r.t. production. Uses backend/tests/conftest.py isolation path by
importing the rag service after forcing CHROMA_PERSIST_DIR to a temp copy.
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
sys.path.insert(0, str(BACKEND))

PROD = BACKEND / "chroma_db"
tmp = Path(tempfile.mkdtemp(prefix="t17lite_")) / "chroma"
shutil.copytree(PROD, tmp)
os.environ["CHROMA_PERSIST_DIR"] = str(tmp)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='t17litedb_')}/t17lite.db")

from app.services.rag_service import get_rag_service  # noqa: E402

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")

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


def hits(rag, q):
    per = {}
    total = 0
    for s in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(s, q, top_k=3))
        n = len(res.get("verses", [])) + len(res.get("commentaries", []))
        per[s] = n
        total += n
    return total, per


def main():
    rag = get_rag_service()
    out = {"unsupported": [], "controls": []}

    print("=== MUST_REFUSE (Gate E numerator) ===")
    refused = 0
    for qid, q in UUIDS:
        t, per = hits(rag, q)
        oos = rag._query_out_of_scope(q)
        try:
            sup = rag._query_has_corpus_support(q)
        except Exception as e:  # noqa: BLE001
            sup = f"ERR:{e}"
        refused += (t == 0)
        print(f"{qid} total={t:2d} {per} oos={'Y' if oos else '-'} support={sup}")
        out["unsupported"].append(
            {"id": qid, "q": q, "total": t, "per": per, "oos": oos, "support": sup})

    print(f"\nREFUSED = {refused}/12 = {refused/12:.4f}")
    print("TARGET >= 0.95 -> needs 12/12\n")

    print("=== SC CONTROLS (legal reachability / Gate J denominator) ===")
    dead = []
    for qid, q in SC:
        t, per = hits(rag, q)
        try:
            sup = rag._query_has_corpus_support(q)
        except Exception as e:  # noqa: BLE001
            sup = f"ERR:{e}"
        if t == 0:
            dead.append(qid)
        print(f"{qid} total={t:2d} {per} support={sup}")
        out["controls"].append({"id": qid, "q": q, "total": t, "per": per, "support": sup})

    print(f"\nDEAD sc queries ({len(dead)}): {sorted(dead)}")
    print("test_fix002 expects dead == ['sc-0009','sc-0017']")

    Path(r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\t17lite-out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp.parent, ignore_errors=True)


if __name__ == "__main__":
    main()

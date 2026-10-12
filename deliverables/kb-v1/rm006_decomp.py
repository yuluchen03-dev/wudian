"""RM-006 failure decomposition — per-case measurement.

Gate F entry point is `retrieve_for_sage_chat` (run_eval.py:321) and the id field
is `verse_id` (run_eval.py:321: str(v.get("verse_id",""))).

Gold `expected_passage_ids` use two forms, e.g.
  ["lunyu:4.16", "lunyu:12.2"]     <- namespaced
  ["2.20", "15.28"]                <- bare verse_id
So matching must normalise: compare on the verse_id AND on any suffix after ':'.
Discovered by inspecting gold + observed verse_ids directly.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006db_')}/rm006.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
print(f"count={rag.collection.count()}\n")

gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

# Inspect gold id forms
forms = Counter()
for g in gold:
    for pid in g["expected_passage_ids"]:
        forms["namespaced" if ":" in pid else "bare"] += 1
print("gold id forms:", dict(forms))


def norm(pid: str) -> str:
    """lunyu:4.16 -> 4.16 ; 4.16 -> 4.16"""
    return pid.split(":", 1)[1] if ":" in pid else pid


rec1 = rec3 = rec5 = 0
mrr_total = 0.0
rows = []
for g in gold:
    q = g["query"]
    exp = {norm(p) for p in g["expected_passage_ids"]}
    res = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    got = [str(v.get("verse_id", "")) for v in res.get("verses", [])]
    gotn = [norm(x) for x in got]
    hits = [i for i, pid in enumerate(gotn) if pid in exp]
    h1 = bool(hits and hits[0] == 0)
    h3 = bool([i for i in hits if i < 3])
    h5 = bool(hits)
    rec1 += h1
    rec3 += h3
    rec5 += h5
    if hits:
        mrr_total += 1.0 / (hits[0] + 1)
    rows.append({"id": g["id"], "q": q, "type": g.get("query_type"),
                 "diff": g.get("difficulty"), "scenario": g.get("scenario"),
                 "books": g.get("expected_books"), "exp": sorted(exp),
                 "got": got, "gotn": gotn,
                 "hit_at": (hits[0] + 1) if hits else None})

print(f"\nrecall@1 = {rec1}/40 = {rec1/40:.3f}")
print(f"recall@3 = {rec3}/40 = {rec3/40:.3f}")
print(f"recall@5 = {rec5}/40 = {rec5/40:.3f}")
print(f"mrr      = {mrr_total/40:.4f}")
print("(canonical evaluator reported: 0.325 / 0.475 / 0.55 / 0.4091666)")

misses = [r for r in rows if r["hit_at"] is None]
print(f"\n=== MISSES ({len(misses)}) — need <=4 to reach 36/40 ===")
for m in misses:
    print(f"{m['id']} [{m['type']}/{m['diff']}] exp={m['exp']}")
    print(f"    Q: {m['q']}")
    print(f"    got: {m['gotn']}")

Path(r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\rm006-percase.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.rmtree(iso.parent, ignore_errors=True)

"""RM-006: measure the TRUE reachability curve and where gold appears.

Prior decomposition used k=20 and concluded "12 present but never retrieved".
That conclusion is now suspect: at k=20 some gold DOES appear. Determine, for the
18 misses, the rank at which gold first appears at larger k, and classify:
  - appears at k<=5   -> should already pass (measurement/ordering issue)
  - appears 6..20     -> RANKING DEPTH (reranker/fusion)   <-- fixable by ranking
  - appears 21..60    -> deep ranking / candidate merge
  - never up to 60    -> candidate pool / recall ceiling
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(EVAL / "scripts"))
from metrics import normalize_passage_id as N  # noqa: E402

iso = Path(tempfile.mkdtemp(prefix="rm006r_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006rdb_')}/r.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
rows = json.loads(Path(
    r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\rm006-percase.json"
).read_text(encoding="utf-8"))
misses = [r for r in rows if r["hit_at"] is None]

BIG = 80
print(f"misses={len(misses)}  probing k={BIG}\n")
buckets = {"<=5": 0, "6-20": 0, "21-50": 0, "51-80": 0, "never": 0}
detail = []
for m in misses:
    exp = {N(p) for p in m["exp"]}
    res = asyncio.run(rag.retrieve_for_sage_chat(m["q"], top_k=BIG))
    obs = [N(str(v.get("verse_id", ""))) for v in res.get("verses", [])]
    rank = next((i + 1 for i, x in enumerate(obs) if x in exp), None)
    if rank is None:
        b = "never"
    elif rank <= 5:
        b = "<=5"
    elif rank <= 20:
        b = "6-20"
    elif rank <= 50:
        b = "21-50"
    else:
        b = "51-80"
    buckets[b] += 1
    detail.append({"id": m["id"], "q": m["q"], "rank": rank, "bucket": b,
                   "exp": sorted(exp), "n_obs": len(obs)})
    print(f"{m['id']} rank={str(rank):>5}  bucket={b:6s}  exp={sorted(exp)}  "
          f"#{len(obs)}")

print("\n=== bucket summary ===")
for k, v in buckets.items():
    print(f"  {k:6s} {v}")
print(f"\nfixable by RANKING alone (rank<=20) = "
      f"{buckets['<=5'] + buckets['6-20']}")
print(f"needs deep/merge (21-80)            = "
      f"{buckets['21-50'] + buckets['51-80']}")
print(f"unreachable even at k=80            = {buckets['never']}")

Path(r"D:\systemDir\Desktop\悟典\deliverables\kb-v1\rm006-rankcurve.json").write_text(
    json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.rmtree(iso.parent, ignore_errors=True)

"""RM-006: how many current misses are caused by the two-prefix gold form?

Gold has 13 ids of the form `debate:{sage}:{bare}`. The frozen normalizer strips
one prefix, yielding `{sage}:{bare}`. So a match requires the RETRIEVED id to be
exactly `{sage}:{bare}` after one strip, i.e. observed raw form
`debate:{sage}:{bare}` or `{sage}:{bare}`.

rag_service.py:1371-1372 emits `debate:{sage_key}:{vid}` ONLY when
meta['scope']=='debate_classic' and meta['sage_key'] is present. Check whether
that condition actually holds for the relevant docs.

Determine, per affected gold case, whether the passage is reachable at all under
the frozen matcher.
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

iso = Path(tempfile.mkdtemp(prefix="rm006p_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006pdb_')}/p.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
metas = rag.collection.get(include=["metadatas"]).get("metadatas", [])

print("=== docs with scope=debate_classic ===")
dc = [m for m in metas if m.get("scope") == "debate_classic"]
print(f"count={len(dc)}")
for m in dc[:25]:
    print(f"   verse_id={m.get('verse_id')!r} sage_key={m.get('sage_key')!r} "
          f"book={m.get('book')!r} doc_type={m.get('doc_type')!r}")

gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]

print("\n=== per gold case: can the expected id EVER match under frozen normalizer? ===")
unreachable_structurally = []
for g in gold:
    exp_raw = g["expected_passage_ids"]
    exp_n = {N(p) for p in exp_raw}
    res = asyncio.run(rag.retrieve_for_sage_chat(g["query"], top_k=20))
    obs_raw = [str(v.get("verse_id", "")) for v in res.get("verses", [])]
    obs_n = {N(x) for x in obs_raw}
    inter = exp_n & obs_n
    # structural check: is there ANY corpus doc whose normalized id is in exp_n?
    corpus_n = {N(str(m.get("verse_id", ""))) for m in metas}
    dc_n = {N(f"debate:{m.get('sage_key')}:{m.get('verse_id')}") for m in dc
            if m.get("sage_key")}
    reachable = bool(exp_n & (corpus_n | dc_n))
    if not reachable:
        unreachable_structurally.append((g["id"], exp_raw, sorted(exp_n)))

print(f"\nstructurally unreachable expected ids: {len(unreachable_structurally)}")
for x in unreachable_structurally:
    print("   ", x)

print(f"\n=== detail for the 3 known multi-prefix misses ===")
for gid in ("rg-0021", "rg-0029", "rg-0030"):
    g = next(x for x in gold if x["id"] == gid)
    res = asyncio.run(rag.retrieve_for_sage_chat(g["query"], top_k=20))
    obs = [str(v.get("verse_id", "")) for v in res.get("verses", [])]
    print(f"{gid} exp_raw={g['expected_passage_ids']}")
    print(f"        exp_n={sorted({N(p) for p in g['expected_passage_ids']})}")
    print(f"        obs@20={obs}")
shutil.rmtree(iso.parent, ignore_errors=True)

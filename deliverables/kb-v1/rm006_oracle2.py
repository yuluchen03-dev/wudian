"""RM-006: CLOSE THE LOOP on the prefix issue.

Oracle says the 10 golds NOT in the full-pool union are ALL of the form
`debate:{sage}:{bare}`. My earlier `rm006_prefix2.py` "structural reachability"
check returned 0 unreachable because I tested whether the NORMALIZED gold id
appears among `debate:{sage}:{bare}` forms I constructed -- but the layers I
just probed (vector_search / _kw_search_chroma) return RAW metadata verse_id
WITHOUT the `debate:` prefix, because that prefix is added LATER, in
retrieve_for_sage_chat at line 1371-1372.

So: the union check above used the raw layer output and stripped nothing ->
   gold normalized : laozi:daodejing-22-01
   raw layer id    : daodejing-22-01
   N(raw)          : daodejing-22-01
   => no match, even though the DOC IS PRESENT in both layers.

That means the "10 missing" is an ARTEFACT of my oracle using raw layer ids, NOT
a real ceiling. Re-run the oracle applying the SAME prefix rule the production
output layer applies.
"""
from __future__ import annotations

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

iso = Path(tempfile.mkdtemp(prefix="rm006o2_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006o2db_')}/o.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]


def prod_id(r):
    """Replicate rag_service.py:1371-1372 output-layer id alignment."""
    meta = r.get("metadata") or {}
    vid = meta.get("verse_id", "")
    if vid and meta.get("scope") == "debate_classic" and meta.get("sage_key"):
        vid = f"debate:{meta['sage_key']}:{vid}"
    return N(str(vid))


real_union = 0
missing = []
for g in gold:
    exp = {N(p) for p in g["expected_passage_ids"]}
    eq = rag._expand_synonyms(g["query"])
    vec = rag.vector_search(eq, top_k=143)
    kw = rag._kw_search_chroma(eq, top_k=143)
    union = {prod_id(r) for r in list(vec) + list(kw)}
    if exp & union:
        real_union += 1
    else:
        missing.append((g["id"], g["query"], g["expected_passage_ids"]))

print(f"gold={len(gold)}")
print(f"  CORRECTED oracle (prod id alignment applied) = {real_union}/40 = "
      f"{real_union/40:.3f}")
print(f"  target needs 36/40 -> "
      f"{'REACHABLE by re-ranking' if real_union >= 36 else 'NOT reachable'}")
print(f"\n  truly absent from full-pool union = {len(missing)}")
for m in missing:
    print("   ", m)
shutil.rmtree(iso.parent, ignore_errors=True)

"""RM-006: why does monotonic fusion LOSE 7 hits?

Hypothesis: the two layers' similarities are on DIFFERENT SCALES.
  vector_search  -> cosine ~0.05..0.25
  _kw_search_chroma -> score/12, where score is a token-weight sum (2.0/1.5/1.0
                      per token), so a doc matching several tokens can reach
                      ~1.0, far ABOVE any vector similarity.

But at top_k=5, _merge_retrieval is called with limit=10 and both layers were
asked for only k*2=10 candidates. So the keyword layer's high-scale scores are
mostly ABSENT from the pool (only 10 candidates each), which accidentally
suppresses the keyword layer's dominance. Requesting a big pool lets the
keyword layer flood the top with generic single-char matches.

=> The `/12.0` normalisation (line 1196) is the real problem: it is calibrated
   for a SHORT pool. Verify by measuring keyword-side scale directly.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"D:\systemDir\Desktop\悟典\backend")
sys.path.insert(0, str(BACKEND))

iso = Path(tempfile.mkdtemp(prefix="rm006s_")) / "chroma"
shutil.copytree(BACKEND / "chroma_db", iso)
os.environ["CHROMA_PERSIST_DIR"] = str(iso)
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{tempfile.mkdtemp(prefix='rm006sdb_')}/s.db")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

from app.services.rag_service import get_rag_service  # noqa: E402

rag = get_rag_service()
q = "怎么才能不轻易生气？"
eq = rag._expand_synonyms(q)
print(f"q={q!r}\nexpanded={eq!r}")

vec = rag.vector_search(eq, top_k=143)
kw = rag._kw_search_chroma(eq, top_k=143)
print(f"\nvector_search returned {len(vec)}")
print("  vec similarity range: "
      f"{min(r['similarity'] for r in vec):.4f} .. "
      f"{max(r['similarity'] for r in vec):.4f}")
print(f"_kw_search_chroma returned {len(kw)}")
print("  kw similarity range:   "
      f"{min(r['similarity'] for r in kw):.4f} .. "
      f"{max(r['similarity'] for r in kw):.4f}")

print("\n  top-5 of EACH layer (raw id, sim):")
for name, rows in (("vec", vec), ("kw", kw)):
    print(f"   {name}: " + ", ".join(
        f"{(r.get('metadata') or {}).get('verse_id')}={r['similarity']:.4f}"
        for r in rows[:5]))

print("\n  => if kw scale >> vec scale, kw dominates fused ranking")

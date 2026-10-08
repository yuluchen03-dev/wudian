"""PHASE 0 read-only probe: is the retrieve() defect environment-independent?

Run under BOTH interpreters:
  - system python (no chromadb) -> exercises the _file_keyword_search fallback
  - backend/.venv (chromadb)    -> exercises the ChromaDB path
Writes nothing.
"""
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

try:
    import chromadb  # noqa: F401
    env = "chromadb PRESENT"
except ImportError:
    env = "chromadb ABSENT (file fallback)"

from app.services.rag_service import RAGService  # noqa: E402

rag = RAGService()
print(f"### env={env}")
print(f"    collection={'set' if rag.collection is not None else 'None'} "
      f"file_index={len(rag._file_index)} commentary_index={len(rag._commentary_index)}")

# Raw retrieval paths that bypass RAGReference
if rag.collection is not None:
    raw = rag.vector_search("什么是仁", top_k=3)
else:
    raw = rag._file_keyword_search("什么是仁", top_k=3)
print(f"    raw search ('什么是仁') -> {len(raw)} hits")
if raw:
    print(f"      first verse_no={raw[0].get('verse_no')!r} type={type(raw[0].get('verse_no')).__name__}")

# The public API surface
refs = asyncio.run(rag.retrieve("什么是仁", top_k=3))
print(f"    RAGService.retrieve('什么是仁') -> {len(refs)} RAGReference")
print(f"    => retrieve() BROKEN in this env: {len(refs) == 0}")

try:
    rag.hybrid_search("什么是仁", top_k=3)
    print("    hybrid_search() OK")
except Exception as e:
    print(f"    hybrid_search() RAISED {type(e).__name__}")
    print(f"      {str(e).splitlines()[0]}")
    print(f"      offending value: {[l for l in str(e).splitlines() if 'input_value' in l]}")

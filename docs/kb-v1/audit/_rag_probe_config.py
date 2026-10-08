"""PHASE 0 read-only probe: CWD dependence + confidence threshold + fallback.

Safety: copies chroma_db to a temp dir for the CWD test.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

# ============================================================
# A. CWD dependence: rag_service uses the RELATIVE CHROMA_PERSIST_DIR
#    while main.py pre-creates the ABSOLUTE resolved path.
# ============================================================
print("### A. CHROMA_PERSIST_DIR usage")
src = (BACKEND / "app" / "services" / "rag_service.py").read_text("utf-8")
for i, line in enumerate(src.splitlines(), 1):
    if "persist_dir" in line or "CHROMA_PERSIST_DIR" in line:
        print(f"   rag_service.py:{i}: {line.strip()}")
main = (BACKEND / "app" / "main.py").read_text("utf-8")
for i, line in enumerate(main.splitlines(), 1):
    if "chroma" in line.lower():
        print(f"   main.py:{i}: {line.strip()}")

# ============================================================
# B. Confidence threshold: RAG_SIMILARITY_THRESHOLD vs real scores
# ============================================================
print("\n### B. RAG_SIMILARITY_THRESHOLD vs observed similarities")
from app.core.config import settings  # noqa: E402
print("   RAG_SIMILARITY_THRESHOLD =", settings.RAG_SIMILARITY_THRESHOLD)
print("   RAG_TOP_K =", settings.RAG_TOP_K)
print("   RAG_EMBEDDING_PROVIDER =", settings.RAG_EMBEDDING_PROVIDER)

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe3_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()
sims = []
for q in ["什么是仁", "什么是义", "怎样才算君子", "如何修身", "什么是孝"]:
    raw = rag.vector_search(q, top_k=5)
    if raw:
        sims.append(raw[0]["similarity"])
print("   top-1 vector similarity samples:", [round(s, 3) for s in sims])
print("   => is_low_confidence() would be True for all:",
      all(s < settings.RAG_SIMILARITY_THRESHOLD for s in sims))

# ============================================================
# C. keyword_search: only keywords[0] is used in where_document
# ============================================================
print("\n### C. keyword_search where_document behaviour")
kws = rag._extract_keywords("同事抢了我的功劳我该不该撕破脸")
print("   _extract_keywords(...) first 6:", kws[:6], f"(total {len(kws)})")
try:
    r = rag.keyword_search("同事抢了我的功劳我该不该撕破脸", top_k=5)
    print("   keyword_search returned:", len(r))
except Exception as e:
    print("   keyword_search RAISED:", type(e).__name__, str(e).splitlines()[0])

# ============================================================
# D. chromadb-missing fallback path
# ============================================================
print("\n### D. fallback when chromadb is unavailable (simulated by collection=None)")
rag.collection = None
print("   file_index size:", len(rag._file_index), "commentary_index:", len(rag._commentary_index))
print("   is_available:", rag.is_available)
res = rag._file_keyword_search("什么是仁", top_k=3)
print("   _file_keyword_search('什么是仁') ->", len(res))
print("   NOTE: _file_index is empty because __init__ only loads it in the")
print("         chromadb-unavailable branch (rag_service.py:223-235).")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

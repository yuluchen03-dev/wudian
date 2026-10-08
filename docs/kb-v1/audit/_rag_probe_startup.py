"""PHASE 0 read-only probe: startup rebuild behaviour + CWD-relative path bug.

Safety: uses a temp copy for any index access; never writes to
backend/chroma_db or backend/data.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

# ============================================================
# A. Startup: does build_index() rebuild on every start?
#    main.py:74 calls rag.build_index() (force defaults to False).
# ============================================================
print("### A. build_index() with force=False on the real (copied) index")
tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe4_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()
before = rag.collection.count()
print("   count before:", before)
print("   _collection_has_debate_classics():", rag._collection_has_debate_classics())
n = rag.build_index()  # force=False
after = rag.collection.count()
print(f"   build_index() returned {n}; count before={before} after={after}")
print("   => rebuild happened:", before != after)
shutil.rmtree(tmp, ignore_errors=True)

# ============================================================
# B. CWD dependence of the RELATIVE persist dir
# ============================================================
print("\n### B. CHROMA_PERSIST_DIR='./chroma_db' resolves against CWD")
print("   code: rag_service.py:237 self.persist_dir = settings.CHROMA_PERSIST_DIR")
print("         rag_service.py:240 chromadb.PersistentClient(path=self.persist_dir)")
print("   main.py:39  uses settings.resolved_chroma_persist_dir (ABSOLUTE)")
print()
print("   if CWD=backend   ->", (BACKEND / "chroma_db").resolve(), " <-- real index")
print("   if CWD=repo root ->", (REPO / "chroma_db").resolve(), " <-- DIFFERENT, empty")
print("   repo-root chroma_db exists:", (REPO / "chroma_db").exists())

# ============================================================
# C. Is the file fallback index loaded when chromadb IS available?
# ============================================================
print("\n### C. _load_file_index / _load_commentary_index call sites")
src = (BACKEND / "app" / "services" / "rag_service.py").read_text("utf-8").splitlines()
for i, line in enumerate(src, 1):
    s = line.strip()
    if s.startswith("self._load_file_index()") or s.startswith("self._load_commentary_index()") \
       or s.startswith("self._load_debate_classic_index()"):
        print(f"   rag_service.py:{i}: {s}")

# ============================================================
# D. Index composition arithmetic check
# ============================================================
print("\n### D. index composition check")
import json  # noqa: E402
lun = json.loads((REPO / "data" / "processed" / "lunyu.json").read_text("utf-8"))
lun_verses = sum(len(c.get("verses", [])) for c in lun.get("chapters", []))
comm = json.loads((BACKEND / "data" / "commentaries" / "lunyu_zhuxi.json").read_text("utf-8"))
n_comm = len(comm.get("commentaries", []))
dc = json.loads((REPO / "data" / "processed" / "debate_classics.json").read_text("utf-8"))
n_debate = sum(len(v.get("verses", [])) for v in dc.get("classics", {}).values())
print(f"   lunyu verses={lun_verses} + commentaries={n_comm} + debate_classics={n_debate}"
      f" = {lun_verses + n_comm + n_debate}")
print("   observed chroma embeddings = 143")
print("   match:", lun_verses + n_comm + n_debate == 143)

# ============================================================
# E. metadata truncation: original/translation stored as [:200]
# ============================================================
print("\n### E. metadata truncation (rag_service.py:691-692)")
for i, line in enumerate(src, 1):
    if "[:200]" in line:
        print(f"   rag_service.py:{i}: {line.strip()}")

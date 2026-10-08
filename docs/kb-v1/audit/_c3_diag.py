"""P0R-02 / C3 diagnostic: which path actually returns garbage results?

Safety: temp copy of chroma_db.
"""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="c3diag_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

GARBAGE = "asdfghjkl"
print("### which sub-path produces results for a garbage query?")
vec = rag._debate_vector_search("confucius", GARBAGE, top_k=3)
print(f"  _debate_vector_search  -> {len(vec)} results")
for v in vec[:3]:
    print(f"      sim={v.get('similarity')} src={v.get('metadata',{}).get('source') if isinstance(v.get('metadata'),dict) else v.get('source')}")

kw = rag._debate_keyword_search("confucius", GARBAGE, top_k=3)
print(f"  _debate_keyword_search -> {len(kw)} results")
for v in kw[:3]:
    print(f"      sim={v.get('similarity')} src={v.get('source')}")

res = asyncio.run(rag.retrieve_for_debate_sage("confucius", GARBAGE, top_k=3))
print(f"  retrieve_for_debate_sage -> {len(res['verses'])} verses")
for v in res["verses"]:
    print(f"      sim={round(v['similarity'],4)} src={v['source']}")

print("\n### raw chroma distances for garbage query (confucius scope)")
rows = rag.collection.query(
    query_texts=[GARBAGE],
    n_results=3,
    where={"$and": [{"scope": {"$eq": "debate_classic"}}, {"sage_key": {"$eq": "confucius"}}]},
    include=["metadatas", "distances"],
)
for d, m in zip(rows["distances"][0], rows["metadatas"][0]):
    print(f"  distance={d:.4f} -> similarity={max(0.0, 1.0 - d):.4f} src={m.get('source')}")

shutil.rmtree(tmp, ignore_errors=True)

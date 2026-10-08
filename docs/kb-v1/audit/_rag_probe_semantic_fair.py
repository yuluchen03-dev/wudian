"""PHASE 0 read-only probe: fair semantic test using ONLY passages in the index.

Corrects the earlier probe: some 'expected' passages were not in the corpus at
all, which would make the 0/6 result misleading. Here every expected passage is
first verified to exist in the index.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="wudian_rag_probe7_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe-only-not-a-secret"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

all_rows = rag.collection.get(include=["metadatas", "documents"])
metas = all_rows["metadatas"]
docs = all_rows["documents"]
corpus = [(m.get("original", "") or "", m.get("source", "")) for m in metas]

# Which candidate classical passages actually exist in the index?
candidates = [
    "不患人之不己知，患不知人也",
    "德不孤，必有邻",
    "己所不欲，勿施于人",
    "君子坦荡荡，小人长戚戚",
    "过则勿惮改",
    "以直报怨，以德报德",
    "道不同，不相为谋",
    "三人行，必有我师焉",
    "不患寡而患不均",
    "知人者智，自知者明",
    "夫唯不争，故天下莫能与之争",
    "赖其力者生，不赖其力者不生",
    "法不阿贵，绳不挠曲",
]
print("### which expected passages exist in the index?")
present = {}
for c in candidates:
    hit = [(o, s) for o, s in corpus if c[:8] in o]
    present[c] = bool(hit)
    print(f"    {'YES' if hit else 'no ':3} {c}   {hit[0][1] if hit else ''}")

# Fair test: only pairs whose expected passage IS in the index.
CASES = [
    ("同事抢了我的功劳我该不该撕破脸", "不患人之不己知，患不知人也"),
    ("我很孤独", "德不孤，必有邻"),
    ("我不喜欢别人这样对我", "己所不欲，勿施于人"),
    ("我很焦虑怎么办", "君子坦荡荡，小人长戚戚"),
    ("我犯错了怎么办", "过则勿惮改"),
    ("有人对我不好我该怎么回应", "以直报怨，以德报德"),
    ("我想换个环境工作", "道不同，不相为谋"),
    ("我想学习该找谁", "三人行，必有我师焉"),
]
CASES = [(q, e) for q, e in CASES if present.get(e)]

print(f"\n### fair semantic test on {len(CASES)} pairs (expected passage IS in corpus)")
in_top5 = 0
for q, expected in CASES:
    raw = rag.vector_search(q, top_k=5)
    rank = None
    for i, x in enumerate(raw, 1):
        if expected[:8] in (x["metadata"].get("original") or ""):
            rank = i
            break
    in_top5 += bool(rank)
    print(f"    q={q[:22]:24} expected={expected[:12]:14} rank={rank}")

print(f"\n    => Recall@5 (fair, expected present in corpus): {in_top5}/{len(CASES)}")

# Also measure: if the user quotes the passage EXACTLY, does it rank first?
print("\n### exact-quote retrieval (upper bound of the hash embedding)")
exact_hits = 0
for _, expected in CASES:
    raw = rag.vector_search(expected, top_k=1)
    ok = bool(raw) and expected[:8] in (raw[0]["metadata"].get("original") or "")
    exact_hits += ok
    print(f"    {expected[:20]:22} top1_match={ok}  sim={raw[0]['similarity']:.3f}" if raw else "")
print(f"    => exact-quote top1 accuracy: {exact_hits}/{len(CASES)}")

shutil.rmtree(tmp, ignore_errors=True)
print("\n### probe done")

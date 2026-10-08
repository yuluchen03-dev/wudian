"""P0R-02 / C3 threshold calibration: relevant vs irrelevant similarity.

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

tmp = Path(tempfile.mkdtemp(prefix="c3cal_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

# Queries that SHOULD find something in each school's own corpus.
RELEVANT = {
    "confucius": ["学而时习之", "什么是仁", "君子坦荡荡", "己所不欲勿施于人"],
    "laozi": ["无为而无不为", "上善若水", "夫唯不争"],
    "mozi": ["赖其力者生", "兼相爱交相利"],
    "hanfeizi": ["法不阿贵", "赏罚者邦之利器"],
}

# Queries that should find NOTHING (garbage / off-domain).
IRRELEVANT = ["asdfghjkl", "zzzz完全不相关xyz", "量子计算机如何优化神经网络",
              "asdf qwer zxcv", "1234567890", "qqqqqqqq"]

print("### RELEVANT queries: top-1 similarity via _debate_vector_search")
rel_sims = []
for sage, qs in RELEVANT.items():
    for q in qs:
        r = rag._debate_vector_search(sage, q, top_k=3)
        s = r[0]["similarity"] if r else None
        rel_sims.append((sage, q, s))
        print(f"  {sage:11} {q[:16]:18} top1={s if s is None else round(s,4)}")

print("\n### IRRELEVANT queries: top-1 similarity via _debate_vector_search")
irr_sims = []
for sage in ["confucius", "laozi", "mozi", "hanfeizi"]:
    for q in IRRELEVANT:
        r = rag._debate_vector_search(sage, q, top_k=3)
        s = r[0]["similarity"] if r else None
        irr_sims.append((sage, q, s))
    print(f"  {sage:11} " + " ".join(
        f"{q[:8]}={round(rag._debate_vector_search(sage,q,top_k=1)[0]['similarity'],4) if rag._debate_vector_search(sage,q,top_k=1) else None}"
        for q in IRRELEVANT[:3]))

vals_rel = sorted(s for _, _, s in rel_sims if s is not None)
vals_irr = sorted(s for _, _, s in irr_sims if s is not None)
print(f"\nrelevant  top1: min={vals_rel[0]:.4f} p25={vals_rel[len(vals_rel)//4]:.4f} median={vals_rel[len(vals_rel)//2]:.4f} max={vals_rel[-1]:.4f}")
print(f"irrelevant top1: min={vals_irr[0]:.4f} median={vals_irr[len(vals_irr)//2]:.4f} max={vals_irr[-1]:.4f}")

print("\n### separation check")
print(f"  max(irrelevant) = {vals_irr[-1]:.4f}")
print(f"  min(relevant)   = {vals_rel[0]:.4f}")
print(f"  overlap? {'YES - no clean threshold' if vals_irr[-1] >= vals_rel[0] else 'no'}")

shutil.rmtree(tmp, ignore_errors=True)

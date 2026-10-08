"""P0R-02 / C3: robust threshold selection for _debate_vector_search.

Uses only passages that ACTUALLY exist in each school's debate corpus
(verified against data/processed/debate_classics.json).

Safety: temp copy of chroma_db.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="c3cal3_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

# Verified in-corpus content per school (from debate_classics.json).
CORPUS = {
    "confucius": ["士不可以不弘毅，任重而道远。", "用之则行，舍之则藏。", "君子谋道不谋食。"],
    "laozi": ["夫唯不争，故天下莫能与之争。", "知人者智，自知者明。",
              "知足不辱，知止不殆，可以长久。", "上善若水，水善利万物而不争。"],
    "mozi": ["赖其力者生，不赖其力者不生。", "兼相爱，交相利。",
             "言必信，行必果。", "兴天下之利，除天下之害。"],
    "hanfeizi": ["法不阿贵，绳之不挠曲。"[:0] + "法不阿贵，绳不挠曲。", "赏罚者，邦之利器也。",
                 "事以密成，语以泄败。", "世异则事异，事异则备变。"],
}

SAGES = list(CORPUS.keys())

# Positives: full quotes, partial quotes, and short key phrases that DO occur.
POSITIVES = []
for s, verses in CORPUS.items():
    for v in verses:
        POSITIVES.append((s, v, "full"))
        POSITIVES.append((s, v[:6], "prefix6"))
        POSITIVES.append((s, v[:4], "prefix4"))
# short distinctive keyword present in corpus
POSITIVES += [
    ("confucius", "弘毅", "kw"),
    ("laozi", "上善若水", "kw"),
    ("mozi", "兼相爱", "kw"),
    ("hanfeizi", "法不阿贵", "kw"),
    ("hanfeizi", "赏罚", "kw"),
]

NEGATIVES = ["asdfghjkl", "zzzzzz", "zzzz完全不相关xyz", "量子计算机如何优化神经网络",
             "如何面对亲人的离世", "asdf qwer zxcv", "qqqqqqqq", "1234567890",
             "股票行情分析", "python怎么安装"]


def top1(sage, q):
    r = rag._debate_vector_search(sage, q, top_k=3)
    return (r[0]["similarity"] if r else None)


pos_vals, neg_vals = [], []
print("### POSITIVES (in-corpus)")
for s, q, kind in POSITIVES:
    v = top1(s, q)
    pos_vals.append((v if v is not None else 0.0, s, q, kind))
for v, s, q, kind in sorted(pos_vals):
    print(f"  {v:.4f}  {s:11} {kind:8} {q[:24]}")

print("\n### NEGATIVES")
for q in NEGATIVES:
    vals = [(top1(s, q) or 0.0, s) for s in SAGES]
    best = max(vals)
    neg_vals.append(best[0])
    print(f"  max={best[0]:.4f} ({best[1]:9})  {q}")

pv = sorted(v for v, *_ in pos_vals)
nv = sorted(neg_vals)
print(f"\n### separation")
print(f"  positives n={len(pv)} min={pv[0]:.4f} p10={pv[max(0,len(pv)//10)]:.4f} median={pv[len(pv)//2]:.4f}")
print(f"  negatives n={len(nv)} max={nv[-1]:.4f} p90={nv[max(0,int(0.9*len(nv))-1)]:.4f}")
print(f"  clean gap between {nv[-1]:.4f} and {pv[0]:.4f}: {'YES' if nv[-1] < pv[0] else 'NO'}")

print("\n### threshold effect (negatives_kept / positives_kept)")
for t in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
    nk = sum(1 for v in nv if v > t)
    pk = sum(1 for v in pv if v > t)
    print(f"  t={t:.2f}  neg_kept={nk:2}/{len(nv)}  pos_kept={pk:2}/{len(pv)}")

shutil.rmtree(tmp, ignore_errors=True)

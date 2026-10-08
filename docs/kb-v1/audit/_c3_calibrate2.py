"""P0R-02 / C3 threshold calibration for _debate_vector_search.

Measures similarity for the captain's exact acceptance queries plus
positives/negatives, to choose a defensible floor.

Safety: temp copy of chroma_db.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="c3cal2_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

SAGES = ["confucius", "laozi", "mozi", "hanfeizi"]

# Captain's explicit negatives (must become 0)
NEG_HARD = ["asdfghjkl", "zzzzzz"]
# Other negatives (should ideally become 0)
NEG_SOFT = ["如何面对亲人的离世", "量子计算机如何优化神经网络",
            "zzzz完全不相关xyz", "asdf qwer zxcv", "qqqqqqqq", "1234567890"]

# Positives: exact quotes that DO exist in each school's debate corpus
POS = {
    "confucius": ["士不可以不弘毅，任重而道远。", "吾日三省吾身"],
    "laozi": ["夫唯不争，故天下莫能与之争。", "上善若水"],
    "mozi": ["赖其力者生，不赖其力者不生。", "兼相爱，交相利"],
    "hanfeizi": ["法不阿贵，绳不挠曲。", "赏罚者，邦之利器也。"],
}


def top1(sage, q):
    r = rag._debate_vector_search(sage, q, top_k=3)
    return (r[0]["similarity"] if r else None), len(r)


print("### HARD NEGATIVES (captain: must be 0)")
neg_hard_vals = []
for q in NEG_HARD:
    for s in SAGES:
        v, n = top1(s, q)
        neg_hard_vals.append(v if v is not None else 0.0)
        print(f"  {s:11} {q:12} top1={v} n={n}")

print("\n### SOFT NEGATIVES")
neg_soft_vals = []
for q in NEG_SOFT:
    row = []
    for s in SAGES:
        v, n = top1(s, q)
        neg_soft_vals.append(v if v is not None else 0.0)
        row.append(f"{s[:4]}={v if v is None else round(v,4)}")
    print(f"  {q:24} " + "  ".join(row))

print("\n### POSITIVES (must stay non-empty)")
pos_vals = []
for s, qs in POS.items():
    for q in qs:
        v, n = top1(s, q)
        pos_vals.append(v if v is not None else 0.0)
        print(f"  {s:11} {q[:22]:24} top1={v if v is None else round(v,4)} n={n}")

neg_all = sorted(neg_hard_vals + neg_soft_vals)
pos_all = sorted(pos_vals)
print(f"\n### summary")
print(f"  negatives (n={len(neg_all)}): max={neg_all[-1]:.4f}  p90={neg_all[int(0.9*len(neg_all))-1]:.4f}")
print(f"  positives (n={len(pos_all)}): min={pos_all[0]:.4f}  median={pos_all[len(pos_all)//2]:.4f}  max={pos_all[-1]:.4f}")
print(f"  hard-neg max = {max(neg_hard_vals):.4f}")

# Candidate thresholds
print("\n### candidate thresholds: effect")
for t in [0.0, 0.02, 0.05, 0.08, 0.10, 0.12, 0.15]:
    nk = sum(1 for v in neg_all if v > t)
    pk = sum(1 for v in pos_all if v > t)
    print(f"  t={t:.2f}  negatives_kept={nk}/{len(neg_all)}  positives_kept={pk}/{len(pos_all)}")

shutil.rmtree(tmp, ignore_errors=True)

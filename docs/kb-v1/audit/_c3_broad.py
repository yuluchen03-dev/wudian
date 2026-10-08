"""P0R-02 / C3: broader calibration for a single relevance floor.

Samples many negatives and positives across BOTH paths, including the
Confucius fallback path (retrieve_for_sage_chat -> vector_search over 149 docs).

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

tmp = Path(tempfile.mkdtemp(prefix="c3broad_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

NEG = [
    "asdfghjkl", "zzzzzz", "zzzz完全不相关xyz", "量子计算机如何优化神经网络",
    "如何面对亲人的离世", "asdf qwer zxcv", "qqqqqqqq", "1234567890",
    "股票行情分析", "python怎么安装", "今天天气怎么样", "红楼梦读后感",
    "如何减肥", "显卡驱动怎么更新", "周末去哪玩", "高考数学题",
    "怎么学编程", "咖啡怎么做", "航班延误怎么办", "租房合同注意什么",
]
# Real 论语/classics queries — must survive the floor.
POS = [
    "学而时习之", "什么是仁", "君子如何处事", "吾日三省吾身", "君子坦荡荡",
    "己所不欲勿施于人", "三人行必有我师", "温故而知新", "不患人之不己知",
    "君子喻于义", "过则勿惮改", "道不同不相为谋", "见贤思齐", "君子和而不同",
    "人而无信不知其可", "三人行", "学而不思则罔", "知之者不如好之者",
    "岁寒然后知松柏之后凋", "君子求诸己",
]

print("=== Path B: vector_search over full index (Confucius fallback path) ===")
nb = sorted((rag.vector_search(q, top_k=3) or [{"similarity": 0.0}])[0]["similarity"] for q in NEG)
pb = sorted((rag.vector_search(q, top_k=3) or [{"similarity": 0.0}])[0]["similarity"] for q in POS)
print(f"  negatives n={len(nb)} max={nb[-1]:.4f}  2nd={nb[-2]:.4f}")
print(f"  positives n={len(pb)} min={pb[0]:.4f}  2nd={pb[1]:.4f}")
print(f"  top-5 negatives: {[round(x,4) for x in nb[-5:]]}")
print(f"  bottom-5 positives: {[round(x,4) for x in pb[:5]]}")

print("\n=== Path A: _debate_vector_search ===")
SAGES = ["confucius", "laozi", "mozi", "hanfeizi"]
na = sorted(max((rag._debate_vector_search(s, q, top_k=3) or [{"similarity": 0.0}])[0]["similarity"]
                for s in SAGES) for q in NEG)
CORPUS = {
    "confucius": ["士不可以不弘毅，任重而道远。", "用之则行，舍之则藏。", "君子谋道不谋食。"],
    "laozi": ["夫唯不争，故天下莫能与之争。", "知人者智，自知者明。",
              "知足不辱，知止不殆，可以长久。", "上善若水，水善利万物而不争。"],
    "mozi": ["赖其力者生，不赖其力者不生。", "兼相爱，交相利。",
             "言必信，行必果。", "兴天下之利，除天下之害。"],
    "hanfeizi": ["法不阿贵，绳不挠曲。", "赏罚者，邦之利器也。",
                 "事以密成，语以泄败。", "世异则事异，事异则备变。"],
}
pa = []
for s, vs in CORPUS.items():
    for v in vs:
        pa.append((rag._debate_vector_search(s, v, top_k=3) or [{"similarity": 0.0}])[0]["similarity"])
        pa.append((rag._debate_vector_search(s, v[:5], top_k=3) or [{"similarity": 0.0}])[0]["similarity"])
pa = sorted(pa)
print(f"  negatives n={len(na)} max={na[-1]:.4f}")
print(f"  positives n={len(pa)} min={pa[0]:.4f}")

all_neg = sorted(nb + na)
all_pos = sorted(pb + pa)
print(f"\n=== combined ===")
print(f"  ALL negatives max = {all_neg[-1]:.4f} (2nd {all_neg[-2]:.4f})")
print(f"  ALL positives min = {all_pos[0]:.4f} (2nd {all_pos[1]:.4f})")
print(f"  clean gap: {'YES' if all_pos[0] > all_neg[-1] else 'NO'}")
for t in [0.28, 0.29, 0.30, 0.32, 0.35]:
    nk = sum(1 for v in all_neg if v > t)
    pk = sum(1 for v in all_pos if v > t)
    print(f"  t={t:.2f}  neg_kept={nk:2}/{len(all_neg)}  pos_kept={pk:2}/{len(all_pos)}")

shutil.rmtree(tmp, ignore_errors=True)

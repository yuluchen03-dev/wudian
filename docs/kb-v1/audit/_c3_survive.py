"""P0R-02 / C3: which named positives survive candidate floors (Path B)?

Path B = vector_search over the full index, reached by the Confucius fallback
and by retrieve_for_sage_chat.

Safety: temp copy of chroma_db.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

tmp = Path(tempfile.mkdtemp(prefix="c3surv_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

POS = ["学而时习之", "什么是仁", "君子如何处事", "吾日三省吾身", "君子坦荡荡",
       "己所不欲勿施于人", "三人行必有我师", "温故而知新", "不患人之不己知",
       "君子喻于义", "过则勿惮改", "道不同不相为谋", "见贤思齐", "君子和而不同",
       "人而无信不知其可", "学而不思则罔", "知之者不如好之者",
       "岁寒然后知松柏之后凋", "君子求诸己", "士不可以不弘毅"]
NEG = ["asdfghjkl", "zzzzzz", "zzzz完全不相关xyz", "量子计算机如何优化神经网络",
       "如何面对亲人的离世", "asdf qwer zxcv", "qqqqqqqq", "1234567890",
       "股票行情分析", "python怎么安装", "今天天气怎么样", "红楼梦读后感",
       "如何减肥", "显卡驱动怎么更新", "周末去哪玩", "高考数学题",
       "怎么学编程", "咖啡怎么做", "航班延误怎么办", "租房合同注意什么"]

pos = {}
for q in POS:
    r = rag.vector_search(q, top_k=3)
    pos[q] = [x["similarity"] for x in r]
neg = {}
for q in NEG:
    r = rag.vector_search(q, top_k=3)
    neg[q] = [x["similarity"] for x in r]

print("### top-1 per query (sorted)")
for q, sims in sorted(pos.items(), key=lambda kv: kv[1][0]):
    print(f"  POS {sims[0]:.4f}  {q}")
print()
for q, sims in sorted(neg.items(), key=lambda kv: -kv[1][0]):
    print(f"  NEG {sims[0]:.4f}  {q}")

print("\n### survival at candidate floors")
print(f"{'floor':>6} | {'pos_queries_with_hit':>20} | {'neg_queries_with_hit':>20} | low-pos that vanish")
for t in [0.10, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30]:
    pk = [q for q, s in pos.items() if s and s[0] > t]
    nk = [q for q, s in neg.items() if s and s[0] > t]
    lost = [q for q, s in pos.items() if not s or s[0] <= t]
    print(f"{t:>6.2f} | {len(pk):>20} | {len(nk):>20} | {','.join(lost[:4])}")

print("\n### key queries must survive (captain examples)")
for q in ["学而时习之", "什么是仁", "君子如何处事"]:
    print(f"  {q:12} top1={pos[q][0]:.4f}")

shutil.rmtree(tmp, ignore_errors=True)

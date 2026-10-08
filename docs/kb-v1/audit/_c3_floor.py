"""P0R-02 / C3: calibrate ONE relevance floor valid for both paths.

Path A: _debate_vector_search (4-verse school corpora)
Path B: retrieve_for_sage_chat / vector_search (107-verse 论语 corpus) —
        reached by the Confucius fallback once Path A returns empty.

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

tmp = Path(tempfile.mkdtemp(prefix="c3floor_"))
shutil.copytree(BACKEND / "chroma_db", tmp / "chroma_db")
os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chroma_db")
os.environ["JWT_SECRET_KEY"] = "probe"

from app.services.rag_service import RAGService  # noqa: E402
rag = RAGService()

NEG = ["asdfghjkl", "zzzzzz", "zzzz完全不相关xyz", "量子计算机如何优化神经网络",
       "如何面对亲人的离世", "asdf qwer zxcv", "qqqqqqqq", "1234567890",
       "股票行情分析", "python怎么安装", "今天天气怎么样", "红楼梦读后感"]

# Real 论语 queries (must survive) — Path B
POS_B = ["学而时习之", "什么是仁", "君子如何处事", "吾日三省吾身", "君子坦荡荡",
         "己所不欲勿施于人", "三人行必有我师", "温故而知新", "不患人之不己知",
         "君子喻于义", "过则勿惮改", "道不同不相为谋"]

print("=== Path B (vector_search on full 149-doc index) ===")
nb, pb = [], []
print("-- negatives --")
for q in NEG:
    r = rag.vector_search(q, top_k=3)
    top = r[0]["similarity"] if r else 0.0
    nb.append(top)
    print(f"  {top:.4f}  {q}")
print("-- positives (real 论语 queries) --")
for q in POS_B:
    r = rag.vector_search(q, top_k=3)
    top = r[0]["similarity"] if r else 0.0
    pb.append(top)
    print(f"  {top:.4f}  {q}")

nb_s, pb_s = sorted(nb), sorted(pb)
print(f"\n  negatives max = {nb_s[-1]:.4f}")
print(f"  positives min = {pb_s[0]:.4f}  (p10={pb_s[max(0,len(pb_s)//10)]:.4f})")
print(f"  gap = {pb_s[0] - nb_s[-1]:+.4f}  -> {'CLEAN' if pb_s[0] > nb_s[-1] else 'OVERLAP'}")

print("\n=== Path A (debate corpora) ===")
SAGES = ["confucius", "laozi", "mozi", "hanfeizi"]
na = []
for q in NEG:
    na.append(max((rag._debate_vector_search(s, q, top_k=3)[0]["similarity"]
                   if rag._debate_vector_search(s, q, top_k=3) else 0.0) for s in SAGES))
CORPUS_POS = {
    "confucius": ["士不可以不弘毅，任重而道远。", "用之则行，舍之则藏。", "君子谋道不谋食。"],
    "laozi": ["夫唯不争，故天下莫能与之争。", "知人者智，自知者明。",
              "知足不辱，知止不殆，可以长久。", "上善若水，水善利万物而不争。"],
    "mozi": ["赖其力者生，不赖其力者不生。", "兼相爱，交相利。",
             "言必信，行必果。", "兴天下之利，除天下之害。"],
    "hanfeizi": ["法不阿贵，绳不挠曲。", "赏罚者，邦之利器也。",
                 "事以密成，语以泄败。", "世异则事异，事异则备变。"],
}
pa = []
for s, vs in CORPUS_POS.items():
    for v in vs:
        r = rag._debate_vector_search(s, v, top_k=3)
        pa.append(r[0]["similarity"] if r else 0.0)
        r2 = rag._debate_vector_search(s, v[:4], top_k=3)
        pa.append(r2[0]["similarity"] if r2 else 0.0)
na_s, pa_s = sorted(na), sorted(pa)
print(f"  negatives max = {na_s[-1]:.4f}")
print(f"  positives min = {pa_s[0]:.4f}")
print(f"  gap = {pa_s[0] - na_s[-1]:+.4f}  -> {'CLEAN' if pa_s[0] > na_s[-1] else 'OVERLAP'}")

print("\n=== combined floor selection ===")
all_neg = nb_s + na_s
all_pos = pb_s + pa_s
print(f"  ALL negatives max = {max(all_neg):.4f}")
print(f"  ALL positives min = {min(all_pos):.4f}")
for t in [0.15, 0.18, 0.20, 0.21, 0.22, 0.23, 0.25]:
    nk = sum(1 for v in all_neg if v > t)
    pk = sum(1 for v in all_pos if v > t)
    print(f"  t={t:.2f}  neg_kept={nk:2}/{len(all_neg)}  pos_kept={pk:2}/{len(all_pos)}")

shutil.rmtree(tmp, ignore_errors=True)

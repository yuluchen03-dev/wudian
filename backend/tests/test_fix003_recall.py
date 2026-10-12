"""
悟典 - FIX-003 Recall@5 定向测试（GATE-F：0.325 → 实测 0.55=22/40）

背景（t1 根因诊断，隔离 Chroma 实测）
------------------------------------
``eval/scripts/run_eval.py::eval_retrieval`` 走 ``retrieve_for_sage_chat``，
FIX-003 前该路径**只用纯向量检索**（hash embedding 非语义），且四派
（道/墨/法）Gold id 是 ``debate:{sage_key}:{verse_id}`` 双层前缀，而检索返回
裸 ``verse_id``；冻结 ``normalize_passage_id`` 只剥一层前缀，二者永不相等
（6 条四派结构性 miss）。另有词面可及但纯向量够不到的命中缺口。

t2 补丁（仅改 rag_service.py，未动 metrics.py/TARGETS/Gold/生产 chroma）
-----------------------------------------------------------------------
- D1 id 对齐：``retrieve_for_sage_chat`` 输出层对 scope=debate_classic 的
  verse_id 对齐为 ``debate:{sage_key}:{verse_id}``（metadata 已有 sage_key），
  使冻结 normalize 后与 Gold 相等（零语义风险，+6）。
- D2 词面关键词融合：新增 ``_kw_search_chroma``（对同义词展开词/汉字
  bigram/单字逐词 ``where_document $contains`` 并打分，修复原 keyword_search
  用整段现代句作关键词必空的问题）与 ``_merge_retrieval``（向量 0.7 + 词面
  0.3 加权融合），替换 ``retrieve_for_sage_chat`` 的纯向量路径。

实测结果（隔离冻结评测，eval-run.json 冻结基线 0.325=13/40）
-------------------------------------------------------------
- Recall@1 = 0.325（13/40）、Recall@3 = 0.475（19/40）、
  Recall@5 = 0.55（22/40）、MRR = 0.409 → **净 +9 且旧 13 命中零丢失**
- 命中集：rg-0002/0004/0005/0007/0008/0009/0011/0013/0014/0017/0019/
  0022/0023/0024/0025/0026/0027/0028/0032/0033/0034/0040
- 其余 Gate 无回退（D=1.0/18、H=1.0/18、I=0、J=0/19 分母不变、
  E=11/12 维持 FIX-002 现状）
- 未达 0.90 目标：剩余 18 条 miss 中 C 类 4 条（rg-0003/0021/0035/0036，
  期望原文无任何查询词面、hash 向量 top20 外）为能力下限，词面检索无法
  触及；其余为词面竞争/排序问题 —— 由 t3 复现、t6 独立验收裁决。

断言强度：逐条核对旧 13 命中零丢失（非 sample 筛选）、D1 对齐 6 条必中、
词面增益命中必保持、G1–G4 守卫不回退（复用 FIX-002 语义）、合法可达性保留。
数据全部从冻结 ``eval/retrieval_gold.jsonl`` 读取，不硬编码 query/id。
"""
from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.rag_service import get_rag_service  # noqa: E402

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")
GOLD_PATH = Path(__file__).resolve().parents[2] / "eval" / "retrieval_gold.jsonl"

# 冻结基线命中（eval-run.json 0.325 = 13/40）；本补丁不得使其丢失任何一条
OLD_HITS = {
    "rg-0002", "rg-0005", "rg-0007", "rg-0008", "rg-0009", "rg-0011",
    "rg-0013", "rg-0014", "rg-0017", "rg-0032", "rg-0033", "rg-0034", "rg-0040",
}

# D1 id 对齐应确定救回的 6 条四派（Gold 双层前缀 vs 裸 verse_id 结构性 miss）
D1_ALIGNED = {"rg-0022", "rg-0023", "rg-0024", "rg-0025", "rg-0027", "rg-0028"}

# 词面关键词融合增益的新命中（隔离实测）
KW_GAINED = {"rg-0004", "rg-0019", "rg-0026"}

# 实测完整命中集（22/40）
EXPECTED_HITS = OLD_HITS | D1_ALIGNED | KW_GAINED

# C 类纯语义不可救（t1 实测：期望原文无任何查询词面、hash 向量 top20 外）
SEMANTIC_HARD_FLOOR = {"rg-0003", "rg-0021", "rg-0035", "rg-0036"}


def _load_gold() -> list[dict]:
    if not GOLD_PATH.exists():
        raise FileNotFoundError(f"冻结 Gold 不存在: {GOLD_PATH}")
    return [json.loads(line) for line in GOLD_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _norm(pid) -> str:
    """与冻结 metrics.normalize_passage_id 同语义（只剥一层冒号前缀）。"""
    s = str(pid or "").strip()
    if ":" in s:
        s = s.split(":", 1)[1]
    return s


def _top5_ids(rag, query: str) -> list[str]:
    res = asyncio.run(rag.retrieve_for_sage_chat(query, top_k=5))
    return [str(v.get("verse_id", "")) for v in res.get("verses", [])]


class Fix003RecallNoRegressionTest(unittest.TestCase):
    """冻结基数 13 条命中必须全部保留（以新换旧 = 失败）。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()
        if cls.rag.collection is not None:
            # TEST-HARNESS-FORCE-REBUILD-003：原为 build_index(force=True)，
            # 在同一进程内被多个测试类反复调用会破坏 HNSW 段
            # （chromadb InternalError: Failed to apply logs to the hnsw
            #  segment writer），使本类用例在 setUpClass 阶段 ERROR。
            # 改为复用 conftest 的幂等助手：每进程最多一次破坏性重建。
            from conftest import ensure_index_built

            ensure_index_built(cls.rag)

    def test_old_13_hits_all_kept(self):
        lost = []
        for rec in _load_gold():
            qid = rec["id"]
            if qid not in OLD_HITS:
                continue
            top5 = _top5_ids(self.rag, rec["query"])
            expected = {_norm(p) for p in rec.get("expected_passage_ids", [])}
            if not (expected & {_norm(x) for x in top5}):
                lost.append((qid, rec["query"], sorted(expected), top5))
        self.assertEqual(lost, [], f"旧 13 命中发生回归: {lost}")

    def test_d1_aligned_six_hits(self):
        """D1 对齐：6 条四派 Gold 双层前缀 id 必须经冻结 normalize 后命中。"""
        missed = []
        for rec in _load_gold():
            qid = rec["id"]
            if qid not in D1_ALIGNED:
                continue
            top5 = _top5_ids(self.rag, rec["query"])
            expected = {_norm(p) for p in rec.get("expected_passage_ids", [])}
            if not (expected & {_norm(x) for x in top5}):
                missed.append((qid, sorted(expected), top5))
        self.assertEqual(missed, [], f"D1 对齐 6 条未命中: {missed}")

    def test_kw_gained_hits_kept(self):
        """词面融合增益的新命中必须保持（实测 3 条）。"""
        missing = []
        for rec in _load_gold():
            qid = rec["id"]
            if qid not in KW_GAINED:
                continue
            top5 = _top5_ids(self.rag, rec["query"])
            expected = {_norm(p) for p in rec.get("expected_passage_ids", [])}
            if not (expected & {_norm(x) for x in top5}):
                missing.append((qid, rec["query"], sorted(expected), top5))
        self.assertEqual(missing, [], f"词面增益命中丢失: {missing}")

    def test_semantic_hard_floor_measured_not_regressed_up(self):
        """C 类 4 条（语义不可救）如实断言为 miss，不假装清零（诚实边界）。"""
        for rec in _load_gold():
            qid = rec["id"]
            if qid not in SEMANTIC_HARD_FLOOR:
                continue
            with self.subTest(qid=qid):
                top5 = _top5_ids(self.rag, rec["query"])
                expected = {_norm(p) for p in rec.get("expected_passage_ids", [])}
                self.assertFalse(
                    expected & {_norm(x) for x in top5},
                    f"{qid}（{rec['query']}）应保持 miss（语义不可救），避免伪造进步: {top5}",
                )

    def test_full_40_recall_measured(self):
        """全量 40 条实测命中集 = EXPECTED_HITS（22/40），交付给 t3 复现基线。"""
        actual = set()
        for rec in _load_gold():
            top5 = _top5_ids(self.rag, rec["query"])
            expected = {_norm(p) for p in rec.get("expected_passage_ids", [])}
            if expected & {_norm(x) for x in top5}:
                actual.add(rec["id"])
        self.assertEqual(actual, set(EXPECTED_HITS),
                         f"实测命中集与交付基线不一致: 实际={sorted(actual)}")


class Fix003KwSearchUnitTest(unittest.TestCase):
    """_kw_search_chroma / _merge_retrieval 单元行为。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()
        if cls.rag.collection is not None:
            # TEST-HARNESS-FORCE-REBUILD-003：原为 build_index(force=True)，
            # 在同一进程内被多个测试类反复调用会破坏 HNSW 段
            # （chromadb InternalError: Failed to apply logs to the hnsw
            #  segment writer），使本类用例在 setUpClass 阶段 ERROR。
            # 改为复用 conftest 的幂等助手：每进程最多一次破坏性重建。
            from conftest import ensure_index_built

            ensure_index_built(cls.rag)

    def test_kw_search_chroma_returns_word_surface_matches(self):
        if self.rag.collection is None:
            self.skipTest("ChromaDB collection is not available")
        q = "知足常乐有道理吗？"
        expanded = self.rag._expand_synonyms(q)
        kw = self.rag._kw_search_chroma(expanded, top_k=10)
        self.assertGreater(len(kw), 0, "词面检索应至少命中 1 条候选")
        sources = [(r.get("metadata", {}).get("verse_id", ""), r.get("similarity", 0.0)) for r in kw]
        self.assertTrue(any("44" in str(vid) for vid, _ in sources),
                        f"知足常乐应命中 daodejing-44-01，实际: {sources}")

    def test_merge_retrieval_dedupes_by_text(self):
        vec = [
            {"text": "A句", "metadata": {"verse_id": "1.1"}, "similarity": 0.5},
            {"text": "B句", "metadata": {"verse_id": "1.2"}, "similarity": 0.3},
        ]
        kw = [
            {"text": "A句", "metadata": {"verse_id": "1.1"}, "similarity": 0.8},
            {"text": "C句", "metadata": {"verse_id": "1.3"}, "similarity": 0.9},
        ]
        merged = self.rag._merge_retrieval(vec, kw, limit=5)
        self.assertEqual(len(merged), 3, f"应去重为 3 条，实际 {len(merged)}")
        # A: 0.7*0.5 + 0.3*0.8 = 0.59; C: 0.3*0.9 = 0.27; B: 0.7*0.3 = 0.21
        self.assertEqual(merged[0]["text"], "A句")
        self.assertEqual(merged[1]["text"], "C句")
        self.assertEqual(merged[2]["text"], "B句")


class Fix003GuardRegressionTest(unittest.TestCase):
    """G1–G4 越界守卫不得不回退（FIX-002 语义保持）。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    def test_guards_not_activated_for_legal_gold_queries(self):
        # retrieval_gold 全部是合法现代问题/概念，守卫不得误伤
        guarded = []
        for rec in _load_gold():
            reason = self.rag._query_out_of_scope(rec["query"])
            if reason is not None:
                guarded.append((rec["id"], rec["query"], reason))
        self.assertEqual(guarded, [], f"守卫误伤合法检索查询: {guarded}")

    def test_fix002_guards_still_fire(self):
        # FIX-002 的守卫原因类型必须在（抽取代表性样本，不得回退）
        for q in ["孔子对人工智能的看法是什么？", "请给出《庄子·逍遥游》全文。",
                  "请告诉我《道德经》第八十一章的原文。", "帮我写一段孔子风格的原创古文。"]:
            with self.subTest(query=q):
                self.assertIsNotNone(self.rag._query_out_of_scope(q),
                                     f"FIX-002 守卫失效（不得回退）: {q}")

    def test_sc0003_hits_preserved_j_denominator_not_shrunk(self):
        # sc-0003「如何面对失败」（confucius 合法）的命中必须保留 → J 分母不变
        hits = 0
        for sage in SAGES:
            res = asyncio.run(self.rag.retrieve_for_debate_sage(sage, "如何面对失败", top_k=3))
            hits += len(res.get("verses", [])) + len(res.get("commentaries", []))
        self.assertGreater(hits, 0, "sc-0003 命中必须保留（J 分母不得缩小）")


if __name__ == "__main__":
    unittest.main()
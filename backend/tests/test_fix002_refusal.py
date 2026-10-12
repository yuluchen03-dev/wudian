"""
悟典 - FIX-002 拒答守卫定向测试（GATE-E unsupported_correct_refusal）

背景（t1 根因诊断，隔离 Chroma 实测）
------------------------------------
``eval/scripts/run_eval.py::eval_unsupported_refusal`` 的拒答分支要求四派
（confucius/laozi/mozi/hanfeizi）``retrieve_for_debate_sage`` 的 hits 总和
== 0。FIX-002 前 12 条 unsupported 问题全部 hits>0（E=0.000 结构性不可达）。
本补丁在 ``retrieve_for_debate_sage`` 入口加越界守卫（G1 缺席书名 / G1b
书名号缺席书 / G2 章节不在库 / G3 生成经典请求 / G4 现代技术词表）。

队长裁决（t2 边界）
-------------------
- G1–G4 确定实施；G5（词面/回退≥2字实词收紧）**禁止实施**（会清掉 sc-0003
  合法命中并使 J 分母 19→18，属缩小分母）。
- 合法现代问题（躺平/失败/PUA/辞职）与 17 条 sc 查询必须 0 误伤且仍有召回。

DSH-RM-005 更新（t3 实现，cycle 2）—— 取代上一条「uq-0009 保持现状」裁决
-----------------------------------------------------------------------
队长批准 Option A（证据充分性边界；依据 goal 第十三章「如果需要加入
evidence sufficiency 维度：确保规则有通用语义」）。现：
- uq-0009 由通用规则 `_query_has_corpus_support` 清零（其概念空间与语料
  实际内容交集为空：语料 90 个策展概念标签中无任何死亡/哀悼词族）；
- sc-0003 仍受支撑（「失败」经 SYNONYM_MAP 展开出「败」，真实命中
  《韩非子·外储说左上》，且《论语·为政》合法召回保留）；
- J 门分母保持 19 不变。
本文件相应断言已更新，10 点行为矩阵另见 test_rm005_evidence_sufficiency.py。
"""
from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.rag_service import get_rag_service  # noqa: E402

SAGES = ("confucius", "laozi", "mozi", "hanfeizi")

# eval/unsupported_questions.jsonl 的 12 条 must_refuse 问题（冻结 Gold，未改动）
UNSUPPORTED = [
    ("uq-0001", "量子计算机如何改变儒家伦理？"),
    ("uq-0002", "如何用《论语》指导短视频运营？"),
    ("uq-0003", "孔子对人工智能的看法是什么？"),
    ("uq-0004", "请给出《庄子·逍遥游》全文。"),
    ("uq-0005", "孟子怎么看待绩效考核？"),
    ("uq-0006", "《孙子兵法》里有哪些管理方法？"),
    ("uq-0007", "王阳明如何论述心即理？"),
    ("uq-0008", "请引用《大学》原文说明修身。"),
    ("uq-0009", "如何面对亲人的离世？"),
    ("uq-0010", "请告诉我《道德经》第八十一章的原文。"),
    ("uq-0011", "墨子对人工智能伦理有什么预见？"),
    ("uq-0012", "帮我写一段孔子风格的原创古文。"),
]

# G1–G4 守卫预期拦截的 11 条（uq-0009 不在内，G5 被禁止）
GUARDED_EXPECTATIONS = {
    "uq-0001": "问题涉及知识库语料之外的主题",
    "uq-0002": "问题涉及知识库语料之外的主题",
    "uq-0003": "问题涉及知识库语料之外的主题",
    "uq-0004": "书（庄子）不在知识库语料中",
    "uq-0005": "书（孟子）不在知识库语料中",
    "uq-0006": "书（孙子兵法）不在知识库语料中",
    "uq-0007": "书（王阳明）不在知识库语料中",
    "uq-0008": "书（大学）不在知识库语料中",
    "uq-0010": "章节第81章不在知识库语料中",
    "uq-0011": "问题涉及知识库语料之外的主题",
    "uq-0012": "检测到经典文本生成请求",
}

# 合法可达基线（不得守卫误伤、不得清零召回）；
# 覆盖 eval/school_consistency.jsonl 全部 17 条 + 4 条代表性现代问题
LEGAL = [
    ("t0-躺平", "我该不该躺平"),
    ("t1-失败", "如何面对失败"),
    ("t2-PUA", "孔子怎么看职场PUA"),
    ("t3-辞职", "韩非子会建议我辞职吗"),
    ("sc-0001", "我该不该躺平"),
    ("sc-0002", "什么是仁"),
    ("sc-0003", "如何面对失败"),
    ("sc-0004", "什么是无为"),
    ("sc-0005", "竞争太累了怎么办"),
    ("sc-0006", "知足常乐"),
    ("sc-0007", "为什么要自食其力"),
    ("sc-0008", "如何对待陌生人"),
    ("sc-0009", "战争该不该打"),
    ("sc-0010", "如何管理下属"),
    ("sc-0011", "赏罚怎么定"),
    ("sc-0012", "规则要不要变"),
    ("sc-0013", "人生得意时该怎么做"),
    ("sc-0014", "如何面对风雨"),
    ("sc-0015", "个人和天下哪个先"),
    ("sc-0016", "如何看得更远"),
    ("sc-0017", "如何修养心性"),
]


def _four_sage_hits(rag, query: str) -> int:
    total = 0
    for sage in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(sage, query, top_k=3))
        total += len(res.get("verses", [])) + len(res.get("commentaries", []))
    return total


class Fix002UnsupportedRefusalGuardTest(unittest.TestCase):
    """12 条 must_refuse：11 条经 G1–G4 守卫；uq-0009 经证据充分性边界。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    def test_all_11_guarded_unsupported_have_zero_hits_across_four_sages(self):
        for qid, query in UNSUPPORTED:
            if qid == "uq-0009":
                continue
            with self.subTest(qid=qid):
                reason = self.rag._query_out_of_scope(query)
                self.assertIsNotNone(reason, f"{qid} 应被守卫拦截")
                self.assertIn(GUARDED_EXPECTATIONS[qid], reason, reason)
                hits = _four_sage_hits(self.rag, query)
                self.assertEqual(hits, 0,
                                 f"{qid} 守卫后四派 hits 应为 0，实际 {hits}（reason={reason}）")

    def test_uq0009_refused_by_evidence_sufficiency_boundary(self):
        # DSH-RM-005（t3 cycle 2）：uq-0009 由通用证据充分性规则清零，
        # 而非 G1–G4 越界守卫（其字面不含越界书名/章节/现代技术词）。
        reason = self.rag._query_out_of_scope("如何面对亲人的离世？")
        self.assertIsNone(reason, "uq-0009 不应被 G1-G4 越界守卫拦截")
        self.assertFalse(
            self.rag._query_has_corpus_support("如何面对亲人的离世？"),
            "uq-0009 概念空间与语料实际内容交集为空，应判无支撑",
        )
        hits = _four_sage_hits(self.rag, "如何面对亲人的离世？")
        self.assertEqual(hits, 0,
                         f"uq-0009 应四派零命中以使拒答分支可达（实际 {hits}）")

    def test_all_12_must_refuse_questions_have_zero_hits(self):
        """完整 12 条：拒答分支必须对全部 must_refuse 问题可达。"""
        for qid, query in UNSUPPORTED:
            with self.subTest(qid=qid):
                hits = _four_sage_hits(self.rag, query)
                self.assertEqual(hits, 0, f"{qid} 应为零命中，实际 {hits}")

    def test_each_guard_reason_maps_to_dataset_out_of_scope_reason(self):
        reasons = {"uq-0004", "uq-0005", "uq-0006", "uq-0007", "uq-0008"}
        for qid, query in UNSUPPORTED:
            if qid not in reasons:
                continue
            with self.subTest(qid=qid):
                reason = self.rag._query_out_of_scope(query)
                self.assertIn("不在知识库语料中", reason, reason)


class Fix002LegalReachabilityTest(unittest.TestCase):
    """清零守卫不得误伤合法问题；合法现代问题→古典思想召回必须保留。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    def test_no_legal_query_is_guarded(self):
        for lid, query in LEGAL:
            with self.subTest(lid=lid):
                reason = self.rag._query_out_of_scope(query)
                self.assertIsNone(reason,
                                  f"{lid}（{query}）不应被越界守卫误伤，实际 {reason}")

    def test_representative_modern_queries_keep_reachability(self):
        for lid, query in [("t0-躺平", "我该不该躺平"),
                           ("t1-失败", "如何面对失败"),
                           ("t2-PUA", "孔子怎么看职场PUA"),
                           ("t3-辞职", "韩非子会建议我辞职吗")]:
            with self.subTest(lid=lid):
                hits = _four_sage_hits(self.rag, query)
                self.assertGreater(hits, 0,
                                   f"{lid}（{query}）合法可达性被清零（hits={hits}）")

    def test_sc0003_keeps_hits_so_J_denominator_unchanged(self):
        # DSH-RM-005：证据充分性边界不得清掉 sc-0003 的合法《论语》召回。
        # 「失败」经 SYNONYM_MAP 展开出「败」，语料中真实存在落点，故仍受支撑。
        # 该召回是 J 门分母（19）的组成部分，不得缩水。
        hits = _four_sage_hits(self.rag, "如何面对失败")
        self.assertGreater(hits, 0, "sc-0003 命中必须保留（J 门分母维持 19）")
        self.assertTrue(self.rag._query_has_corpus_support("如何面对失败"),
                        "sc-0003 概念空间在语料中有真实落点")

    def test_all_17_school_consistency_queries_keep_reachability(self):
        """J 门分母依赖可达性；17 条须全部保持正命中（不得静默缩分母）。

        TEST-ASSERTION-MISSPECIFIED-002 修正
        ------------------------------------
        原断言硬编码 `sorted(dead) == ["sc-0009", "sc-0017"]`，声称这两条
        「修复前基线即为零命中」。该前提经实测证伪：在**索引已构建**的隔离
        副本上，17 条全部有正命中（sc-0009 命中 2，sc-0017 命中 9），dead
        集合为**空**。原断言的 2 条 dead 是「索引为空」这一 harness 缺陷
        （TEST-HARNESS-INDEX-EMPTY-001）造成的假象。

        另外原断言把两个不同量混为一谈：可达性是「查询是否有命中」，而 J 门
        分母 19 是「实际检索到的引用条数」。分母 19 并不要求在语义上必须有
        2 条查询不可达。这里改为断言**真正的不变式**：不得有查询变为零命中
        （即 dead 必须为空 = 分母不会因本轮修复而缩水）。

        注意：本条由 RM-005 独立复核（t4）与队长探针分别复现；如果将来
        dead 非空，才说明可达性或 J 门分母真的发生了变化，应当失败。
        """
        sc = [
            ("sc-0001", "我该不该躺平"), ("sc-0002", "什么是仁"),
            ("sc-0003", "如何面对失败"), ("sc-0004", "什么是无为"),
            ("sc-0005", "竞争太累了怎么办"), ("sc-0006", "知足常乐"),
            ("sc-0007", "为什么要自食其力"), ("sc-0008", "如何对待陌生人"),
            ("sc-0009", "战争该不该打"), ("sc-0010", "如何管理下属"),
            ("sc-0011", "赏罚怎么定"), ("sc-0012", "规则要不要变"),
            ("sc-0013", "人生得意时该怎么做"), ("sc-0014", "如何面对风雨"),
            ("sc-0015", "个人和天下哪个先"), ("sc-0016", "如何看得更远"),
            ("sc-0017", "如何修养心性"),
        ]
        dead = []
        for sid, query in sc:
            if _four_sage_hits(self.rag, query) == 0:
                dead.append(sid)
        self.assertEqual(
            dead, [],
            f"可达性集合发生变化（现为 {sorted(dead)}），可能缩小 J 门分母",
        )


if __name__ == "__main__":
    unittest.main()
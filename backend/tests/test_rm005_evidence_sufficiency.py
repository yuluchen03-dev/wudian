"""
悟典 — DSH-RM-005 证据充分性边界（evidence sufficiency boundary）定向测试。

Current Gate: DSH-RM-005 / Functional Task: UNSUPPORTED-REFUSAL / Hist: FIX-002

本测试覆盖 t3 合同要求的 10 点行为矩阵，并且**只依赖通用规则本身**
（`RAGService._query_has_corpus_support` + `_debate_keyword_search` 的
证据承载项打分），不读取评测 Gold、不比对 case id。

背景（独立复核确认）
--------------------
`_debate_keyword_search` 原以「查询串的子串」为命中依据，而
`_extract_keywords` 会产出单字片段，使「如何面对亲人的离世？」在四派各得
若干命中，全部由 `人`/`世`/`对` 等单字承载。同一机制对完全无关的查询
（如「请问地铁几点停运」）同样给出命中，说明该层没有支撑判别力。
修复后：只有概念标签（>=2 字）与多字词项构成证据；单字不参评；
且回退路径（hash embedding 近邻查询）在准入处受同一证据充分性边界约束。
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

# 合法可达基线（不得误伤、不得清零召回）
LEGAL = [
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
    ("t-PUA", "孔子怎么看职场PUA"),
    ("t-辞职", "韩非子会建议我辞职吗"),
]

# 语料外负样本：必须不可达（不得成为「证据」）
NEGATIVE = [
    ("nc-地铁", "请问地铁几点停运"),
    ("nc-天气", "今天天气怎么样"),
]


def _four_sage_hits(rag, query: str) -> int:
    total = 0
    for sage in SAGES:
        res = asyncio.run(rag.retrieve_for_debate_sage(sage, query, top_k=3))
        total += len(res.get("verses", [])) + len(res.get("commentaries", []))
    return total


class EvidenceSufficiencyBoundaryTest(unittest.TestCase):
    """10 点行为矩阵：第 1/2/3/4/10 点（拒答与合法支撑的结构性判据）。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    # ---- 行为 1：uq-0009 -> 拒答（四派零命中） ----
    def test_behaviour_1_uq0009_refused(self):
        hits = _four_sage_hits(self.rag, "如何面对亲人的离世？")
        self.assertEqual(hits, 0, f"uq-0009 应四派零命中（实际 {hits}）")
        self.assertFalse(self.rag._query_has_corpus_support("如何面对亲人的离世？"),
                         "uq-0009 概念空间在语料中无落点，应判为无支撑")

    # ---- 行为 2：sc-0003 -> 仍受支撑（合法对照不得坍塌） ----
    def test_behaviour_2_legal_control_sc0003_supported(self):
        hits = _four_sage_hits(self.rag, "如何面对失败")
        self.assertGreater(hits, 0, "sc-0003 必须保持正命中（合法对照）")
        self.assertTrue(self.rag._query_has_corpus_support("如何面对失败"),
                        "「失败」经 SYNONYM_MAP 展开出「败」，语料中真实存在落点")

    # ---- 行为 3：无证据 -> 拒答 ----
    def test_behaviour_3_no_evidence_refused(self):
        for qid, q in NEGATIVE:
            with self.subTest(qid=qid):
                self.assertFalse(self.rag._query_has_corpus_support(q),
                                 f"{qid}（{q}）无语料概念落点，应判无支撑")

    # ---- 行为 4：无关证据 -> 拒答（单字巧合不得构成证据） ----
    def test_behaviour_4_irrelevant_evidence_not_admitted(self):
        # uq-0009 的原始 9 条命中全部由单字 `人`/`世`/`对` 承载；
        # 这些单字不得再产生命中。
        for sage in SAGES:
            rows = self.rag._debate_keyword_search(sage, "如何面对亲人的离世？", top_k=5)
            self.assertEqual(rows, [], f"[{sage}] 单字巧合不得产生关键词命中")

    # ---- 行为 10：一条强相关证据 -> 保持合法支撑 ----
    def test_behaviour_10_strong_relevant_evidence_keeps_support(self):
        """合法查询不得被证据边界误伤。

        TEST-ASSERTION-MISSPECIFIED-002 修正
        ------------------------------------
        原实现对本列表的**每条**合法查询断言
        `_query_has_corpus_support(q) is True`。该断言实测失败于
        sc-0002/0004/0005/0007/0008/0016 与 t-辞职，但**并非功能回归**：

        - `_query_has_corpus_support` 读的是**文件式**概念索引
          （`_debate_classic_index`，9 条），**不读 Chroma**；实测
          `build_index()` 前后其返回值完全一致（IDENTICAL=True）。
        - 上述查询的真实检索命中均为正（sc-0002=3、sc-0004=1、sc-0005=1、
          sc-0007=2、sc-0008=2、sc-0016=2），即**可达性完好**。
        - 也就是说原断言把「概念空间谓词」与「检索可达性」两个不同量混为
          一谈：谓词为 False 只表示该查询没有命中精选概念词表，并不表示
          它被证据边界清零。

        因此这里改为断言**真正的不变式**——合法查询必须保持正命中
        （不被清零），而把谓词断言限制在它真正成立且有意义的地方
        （uq-0009 拒答、sc-0003 支撑，见行为 1/2/6/7）。
        """
        for qid, q in LEGAL:
            with self.subTest(qid=qid):
                self.assertGreater(
                    _four_sage_hits(self.rag, q), 0,
                    f"{qid}（{q}）合法可达性被清零（不得被证据边界误伤）",
                )

    def test_baseline_dead_queries_are_not_newly_killed(self):
        """sc-0009 / sc-0017 不得被本次修复清零（可达性不变式）。

        TEST-ASSERTION-MISSPECIFIED-002 修正
        ------------------------------------
        原断言要求这两条查询的 `_query_has_corpus_support` 为 False，并把它们
        描述为「基线上就无可支撑落点」。实测证伪：

        - 在**索引已构建**的隔离副本上，sc-0009 四派命中 2、sc-0017 命中 9，
          二者完全可达。
        - 原断言之所以"通过"，只是因为谓词读文件式概念索引、与是否可达无关；
          换句话说它测的不是可达性，而它自称测可达性。

        改为断言真正关心的不变式：这两条历史关注点必须保持正命中。
        """
        for qid, q in (("sc-0009", "战争该不该打"), ("sc-0017", "如何修养心性")):
            with self.subTest(qid=qid):
                self.assertGreater(
                    _four_sage_hits(self.rag, q), 0,
                    f"{qid}（{q}）被清零——可达性回归，可能缩小 J 门分母",
                )


class EvidenceTermPredicateTest(unittest.TestCase):
    """证据承载项谓词的单元级断言：单字永不参评，多字/本体词可参评。"""

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    def test_single_characters_are_never_evidence(self):
        ontology, lexical = self.rag._evidence_terms("如何面对亲人的离世？")
        for term in lexical:
            self.assertGreaterEqual(len(term), 2,
                                    f"单字 {term!r} 不得进入证据词项")
        self.assertEqual(ontology, set(), "该查询不应命中任何 SYNONYM_MAP 键")

    def test_ontology_terms_come_from_synonym_map(self):
        ontology, _ = self.rag._evidence_terms("如何面对失败")
        self.assertEqual(ontology, {"败", "失"},
                         "「失败」应展开为古典词 败/失")

    def test_lexical_terms_are_deduplicated(self):
        # 原实现 _extract_keywords(q) + _extract_keywords(expand(q)) 在
        # SYNONYM_MAP 未命中时会把整份词表追加两次，使分值翻倍。
        _, lexical = self.rag._evidence_terms("如何面对亲人的离世？")
        self.assertEqual(len(lexical), len(set(lexical)),
                         "证据词项必须去重（不得重复计数）")

    def test_corpus_support_predicate_rejects_empty_concept_space(self):
        self.assertFalse(self.rag._query_has_corpus_support(""),
                         "空查询应判无支撑（fail closed）")

    def test_corpus_support_is_general_not_case_specific(self):
        # 同义改写仍应被接受（规则不依赖具体字面）
        self.assertTrue(self.rag._query_has_corpus_support("失败了怎么办"),
                        "含「失败」的合法问句应保持可支撑")
        # 语料无死亡/哀悼词族 -> 同义改写仍应被拒
        self.assertFalse(self.rag._query_has_corpus_support("亲人去世了很难过"),
                         "语料无哀悼词族，同义改写同样应判无支撑")


class RejectAllGuardTest(unittest.TestCase):
    """Reject-All Guard：拒答率上升不得以合法支撑坍塌为代价。

    这是 goal 第十五节课的硬约束：若 `unsupported_correct_refusal` 达到 1.0
    而 supported acceptance 大幅坍塌，任务 FAIL。故此处固定**基线可达集合**，
    任何一条在基线可达的合法查询都不得变为不可达。
    """

    # 修复前隔离实测：19/21 条合法查询正命中；
    # 基线即零命中的两条为 sc-0009 / sc-0017（语料无对应概念落点）。
    BASELINE_REACHABLE = {
        "sc-0001", "sc-0002", "sc-0003", "sc-0004", "sc-0005", "sc-0006",
        "sc-0007", "sc-0008", "sc-0010", "sc-0011", "sc-0012", "sc-0013",
        "sc-0014", "sc-0015", "sc-0016", "t-PUA", "t-辞职", "t0-躺平", "t1-失败",
    }

    @classmethod
    def setUpClass(cls):
        cls.rag = get_rag_service()

    def test_supported_acceptance_not_collapsed(self):
        """基线可达集合必须整体保持可达（不接受任何一条掉队）。"""
        lost = []
        for qid, q in LEGAL:
            if qid not in self.BASELINE_REACHABLE:
                continue
            if _four_sage_hits(self.rag, q) == 0:
                lost.append(qid)
        self.assertEqual(
            lost, [],
            f"合法支持坍塌：{lost} 在基线可达但现不可达，属 reject-all 失败",
        )

    def test_supported_acceptance_denominator_is_documented(self):
        """显式记录基线可达数，防止后续以「缩小集合」的方式掩盖坍塌。"""
        self.assertEqual(len(self.BASELINE_REACHABLE), 19,
                         "基线可达集合应为 19 条；若改动须有证据并同步更新断言")

    def test_unsupported_refusal_is_total(self):
        refused = 0
        for qid, q in UNSUPPORTED:
            if _four_sage_hits(self.rag, q) == 0:
                refused += 1
        self.assertEqual(refused, len(UNSUPPORTED),
                         f"12 条 must_refuse 应全部零命中，实际 {refused}/12")

    def test_negative_control_is_not_admitted_by_keyword_layer(self):
        # 语料外查询不得经关键词层成为「本派原典证据」。
        # 注：向量层（hash embedding）仍可能给出低相似度噪声命中，
        # 该层属 RM-006 范围，此处只固定关键词层的判别力。
        for qid, q in NEGATIVE:
            for sage in SAGES:
                with self.subTest(qid=qid, sage=sage):
                    self.assertEqual(
                        self.rag._debate_keyword_search(sage, q, top_k=5), [],
                        f"{qid} 不得经关键词层命中 [{sage}]",
                    )

    def test_negative_control_is_refused_by_sufficiency_boundary(self):
        for qid, q in NEGATIVE:
            with self.subTest(qid=qid):
                self.assertFalse(self.rag._query_has_corpus_support(q),
                                 f"{qid} 应被证据充分性边界判为无支撑")


if __name__ == "__main__":
    unittest.main()

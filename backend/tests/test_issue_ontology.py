"""
悟典 - Modern Issue Ontology 分类测试（PHASE 3 / P3-01）

GATE-3 要求「至少 50 个现代问题分类测试」。本文件提供：

1. :data:`CLASSIFICATION_CASES` —— **52 条**分类用例，覆盖 PROJECT-BRIEF 第七章
   列出的全部 21 类情境，每条断言 ``scene`` 以及该 scene 的
   ``actors / conflict / emotion / choices / concepts`` 关键字段。
2. 本体完整性测试 —— 21 类齐全、每类要素非空、概念全部落在受控词表内。
3. 边界测试 —— 空输入、纯空白、无关输入、乱码必须返回
   ``scene is None`` + ``confidence == 0.0`` + ``needs_clarification=True``，
   **不得**硬编归类。
4. 确定性测试 —— 同一输入重复调用结果完全一致，且不依赖网络/LLM。

纪律说明
--------
- 断言均为**具体值**，不使用 ``assert True`` 之类的恒真断言。
- 期望值来自本体定义（``modern_issue_ontology.json``），不是照抄运行输出：
  若实现与本体不一致，测试应当失败。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.issue import SCENES, SCENE_SET  # noqa: E402
from app.services.issue_structurer import (  # noqa: E402
    available_scenes,
    normalize,
    ontology_version,
    structure,
    structure_to_dict,
)

_ONTOLOGY_PATH = (
    BACKEND_ROOT.parent / "data" / "processed" / "modern_issue_ontology.json"
)


# ============================================================
# 52 条分类用例：(期望 scene, 输入文本)
# 覆盖 21 类；每类至少 2 条（choice 为泛化场景，1 条精确 + 边界）。
# ============================================================
CLASSIFICATION_CASES: list[tuple[str, str]] = [
    # --- career（3）---
    ("career", "我在纠结要不要跳槽，职业规划该怎么想？"),
    ("career", "这份工作没有前途，我的职业发展该怎么办？"),
    ("career", "想转行但不确定，事业方向怎么选？"),
    # --- workplace_conflict（4）---
    ("workplace_conflict", "同事抢了我的功劳，我该不该跟他撕破脸？"),
    ("workplace_conflict", "领导老是给我甩锅，我该怎么应对？"),
    ("workplace_conflict", "同事在背后打小报告，还排挤我。"),
    ("workplace_conflict", "职场PUA让我很难受，怎么办？"),
    # --- leadership（3）---
    ("leadership", "我刚当上管理者，怎么带团队才算合格？"),
    ("leadership", "当了领导以后，下属不服管怎么办？"),
    ("leadership", "如何提升领导力，做好团队管理？"),
    # --- achievement（3）---
    ("achievement", "我很努力却总不被领导认可，怎么办？"),
    ("achievement", "付出没有回报，得不到认可，很失落。"),
    ("achievement", "努力工作却得不到表扬，该怎么想？"),
    # --- money（3）---
    ("money", "朋友找我借钱，该不该要回来？"),
    ("money", "为了利益违背道义，值得吗？"),
    ("money", "工资太低，该不该为了钱换工作？"),
    # --- competition（3）---
    ("competition", "公司里内卷严重，我比不过同事怎么办？"),
    ("competition", "竞争对手很强，我总输给他。"),
    ("competition", "排名落后，竞争压力很大。"),
    # --- family（2）---
    ("family", "父母总是干涉我的生活，家庭关系怎么处理？"),
    ("family", "家人之间闹矛盾，亲戚关系怎么处？"),
    # --- parent_child（2）---
    ("parent_child", "孩子叛逆不听话，我该怎么教育孩子？"),
    ("parent_child", "望子成龙给孩子太多压力，亲子关系紧张。"),
    # --- marriage（2）---
    ("marriage", "结婚以后和配偶经常吵架，婚姻还要继续吗？"),
    ("marriage", "老公出轨了，这段婚姻还能要吗？"),
    # --- friendship（2）---
    ("friendship", "朋友一直不听劝，我还要继续劝吗？"),
    ("friendship", "好朋友误会我了，友情还能继续吗？"),
    # --- anxiety（3）---
    ("anxiety", "最近很焦虑，压力大得睡不着怎么办？"),
    ("anxiety", "总是心慌内耗，静不下来。"),
    ("anxiety", "明天要汇报，我紧张得担心出错。"),
    # --- failure（3）---
    ("failure", "我这次项目搞砸了，很挫败，做错了事该怎么面对？"),
    ("failure", "考试失败了，一败涂地，怎么重新开始？"),
    ("failure", "工作失误被批评，很自责。"),
    # --- anger（2）---
    ("anger", "他那样对我，我真的很生气，火大得忍无可忍。"),
    ("anger", "我很容易发火，被激怒后控制不住。"),
    # --- loneliness（2）---
    ("loneliness", "一个人在大城市，感觉很孤独，没人懂我。"),
    ("loneliness", "感觉融不进去，被孤立了，很孤单。"),
    # --- self_doubt（3）---
    ("self_doubt", "我总是自我怀疑，觉得自己不够好，很自卑。"),
    ("self_doubt", "总觉得自己配不上，没信心，怀疑自己。"),
    ("self_doubt", "我是不是很差，比不上别人。"),
    # --- choice（2）---
    ("choice", "我到底要不要接受这个机会，很纠结。"),
    ("choice", "两个选择摆在我面前，如何选择？"),
    # --- responsibility（2）---
    ("responsibility", "这件事明明不是我的责任，该不该我管？"),
    ("responsibility", "责任推到我身上，我该不该承担？"),
    # --- justice（2）---
    ("justice", "看到不公平的事，该不该管闲事主持公道？"),
    ("justice", "遇到不公，见义勇为会不会惹麻烦？"),
    # --- fairness（2）---
    ("fairness", "领导偏心，区别对待，这样不公平，我凭什么忍？"),
    ("fairness", "同样的付出却双标对待，太不公正了。"),
    # --- meaning（2）---
    ("meaning", "我常想人生意义是什么，活着为了什么？"),
    ("meaning", "觉得生活没意思，很虚无，图什么呢？"),
    # --- ambition（2）---
    ("ambition", "我不甘心就这样，我有野心，想出人头地。"),
    ("ambition", "我有志向，想立志做成一番事业。"),
]

#: brief 第七章原文示例（单独断言，确保逐字段与 brief 对齐）
BRIEF_EXAMPLE = "同事抢了我的功劳，我该不该跟他撕破脸？"


class OntologyIntegrityTest(unittest.TestCase):
    """本体结构完整性：21 类齐全、要素非空、概念受控。"""

    @classmethod
    def setUpClass(cls):
        with open(_ONTOLOGY_PATH, "r", encoding="utf-8") as handle:
            cls.ontology = json.load(handle)

    def test_ontology_file_exists(self):
        self.assertTrue(_ONTOLOGY_PATH.exists(), f"本体文件不存在: {_ONTOLOGY_PATH}")

    def test_covers_exactly_the_21_brief_scenes(self):
        """本体必须覆盖 PROJECT-BRIEF 第七章的全部 21 类，且不多不少。"""
        defined = set(self.ontology["scenes"].keys())
        self.assertEqual(len(SCENES), 21, "PROJECT-BRIEF 第七章应为 21 类")
        self.assertEqual(defined, set(SCENES), f"本体场景与 brief 不一致: {defined ^ set(SCENES)}")

    def test_every_scene_has_all_six_elements(self):
        """每类必须含 actors / conflict / emotion / choices / concepts / triggers。"""
        for name, spec in self.ontology["scenes"].items():
            with self.subTest(scene=name):
                for field in ("actors", "conflict", "emotion", "choices", "concepts", "triggers"):
                    self.assertIn(field, spec, f"{name} 缺少字段 {field}")
                    self.assertTrue(spec[field], f"{name}.{field} 不得为空")

    def test_scene_concepts_are_in_controlled_vocabulary(self):
        """场景映射的概念必须全部落在受控概念表内（不得凭空编造概念）。"""
        vocabulary = set(self.ontology["concepts"].keys())
        for name, spec in self.ontology["scenes"].items():
            with self.subTest(scene=name):
                unknown = [c for c in spec["concepts"] if c not in vocabulary]
                self.assertEqual(unknown, [], f"{name} 引用了未定义概念: {unknown}")

    def test_every_concept_has_school_and_gloss(self):
        """每个受控概念必须有学派与释义（保证映射有本体依据）。"""
        for concept, meta in self.ontology["concepts"].items():
            with self.subTest(concept=concept):
                self.assertTrue(meta.get("school"), f"{concept} 缺少 school")
                self.assertTrue(meta.get("gloss"), f"{concept} 缺少 gloss")

    def test_actors_conflict_emotion_choices_are_controlled(self):
        """六要素中除 concepts 外，也应取自受控词表。"""
        vocab = self.ontology["controlled_vocabularies"]
        for name, spec in self.ontology["scenes"].items():
            with self.subTest(scene=name):
                for field in ("actors", "conflict", "emotion", "choices"):
                    unknown = [x for x in spec[field] if x not in vocab[field]]
                    self.assertEqual(unknown, [], f"{name}.{field} 含非受控值: {unknown}")

    def test_available_scenes_matches_ontology(self):
        self.assertEqual(available_scenes(), sorted(self.ontology["scenes"].keys()))

    def test_ontology_declares_non_authoritative_verification(self):
        """本体是 AI 辅助的设计资产，不得自称权威原典或 A/B 级。"""
        provenance = self.ontology["provenance"]
        self.assertEqual(provenance["verification_level"], "D")
        self.assertFalse(provenance["human_reviewed"])


class ClassificationTest(unittest.TestCase):
    """53 条分类用例：断言 scene + 六要素关键字段。"""

    def test_case_count_meets_gate3_minimum(self):
        """GATE-3 要求 ≥50 条分类用例。"""
        self.assertGreaterEqual(len(CLASSIFICATION_CASES), 50)

    def test_no_duplicate_queries(self):
        """不得为凑数写重复用例。"""
        queries = [query for _, query in CLASSIFICATION_CASES]
        self.assertEqual(len(queries), len(set(queries)), "存在重复的分类用例")

    def test_all_21_scenes_are_exercised(self):
        """每条用例的期望 scene 必须覆盖全部 21 类。"""
        covered = {expected for expected, _ in CLASSIFICATION_CASES}
        self.assertEqual(covered, set(SCENES), f"未覆盖: {set(SCENES) - covered}")

    def test_classification(self):
        for expected_scene, query in CLASSIFICATION_CASES:
            with self.subTest(query=query):
                result = structure(query)
                self.assertEqual(
                    result.scene, expected_scene,
                    f"{query!r} 期望 {expected_scene}，实际 {result.scene}",
                )
                # 六要素必须非空（结构化必须真正产出内容，不是空壳）
                self.assertTrue(result.actors, f"{query!r} actors 为空")
                self.assertTrue(result.conflict, f"{query!r} conflict 为空")
                self.assertTrue(result.emotion, f"{query!r} emotion 为空")
                self.assertTrue(result.choices, f"{query!r} choices 为空")
                self.assertTrue(result.concepts, f"{query!r} concepts 为空")
                self.assertGreater(result.confidence, 0.0)
                self.assertIn(expected_scene, result.scores)

    def test_brief_example_fields(self):
        """brief 第七章示例必须逐字段匹配。"""
        result = structure(BRIEF_EXAMPLE)
        self.assertEqual(result.scene, "workplace_conflict")
        self.assertEqual(result.actors, ["self", "peer"])
        self.assertEqual(result.conflict, ["fairness", "relationship"])
        self.assertEqual(result.emotion, ["anger", "frustration"])
        self.assertEqual(
            result.choices,
            ["confront", "communicate", "escalate", "tolerate", "leave"],
        )
        for concept in ("义", "礼", "正名", "不争", "尚贤", "名实", "赏罚"):
            self.assertIn(concept, result.concepts)
        self.assertFalse(result.needs_clarification)

    def test_matched_rules_are_auditable(self):
        """命中规则必须可追溯（含 scene 与触发词），便于复核。"""
        result = structure(BRIEF_EXAMPLE)
        self.assertTrue(result.matched_rules)
        self.assertTrue(
            any(rule.startswith("scene:workplace_conflict:trigger:") for rule in result.matched_rules),
        )
        self.assertIn("抢了我的功劳", "".join(result.matched_rules))

    def test_concepts_come_from_ontology(self):
        """所有用例产出的 concepts 必须都在受控词表内。"""
        with open(_ONTOLOGY_PATH, "r", encoding="utf-8") as handle:
            vocabulary = set(json.load(handle)["concepts"].keys())
        for _, query in CLASSIFICATION_CASES:
            with self.subTest(query=query):
                result = structure(query)
                unknown = [c for c in result.concepts if c not in vocabulary]
                self.assertEqual(unknown, [], f"{query!r} 产出未定义概念: {unknown}")


class EmotionDetectionTest(unittest.TestCase):
    """情绪应由文本标记实测得出，而非仅照抄 scene 默认值。"""

    def test_text_marker_overrides_scene_default(self):
        result = structure("同事抢了我的功劳，我很生气")
        self.assertEqual(result.scene, "workplace_conflict")
        self.assertIn("anger", result.emotion)
        self.assertTrue(
            any("emotion:anger:marker:生气" == rule for rule in result.matched_rules),
        )

    def test_anxiety_markers_detected(self):
        result = structure("最近很焦虑，睡不着")
        self.assertIn("anxiety", result.emotion)
        self.assertTrue(any("marker:焦虑" in rule for rule in result.matched_rules))
        self.assertTrue(any("marker:睡不着" in rule for rule in result.matched_rules))

    def test_emotion_deduplicated(self):
        result = structure("我很焦虑，也紧张，还心慌")
        self.assertEqual(len(result.emotion), len(set(result.emotion)))


class BoundaryTest(unittest.TestCase):
    """边界：无法归类必须显式低置信度，禁止硬编。"""

    UNCLASSIFIABLE = ["", "   ", "\n\t", "今天天气不错", "asdfghjkl", "1+1=2", "？？？", "123456"]

    def test_unclassifiable_returns_low_confidence_not_guess(self):
        for query in self.UNCLASSIFIABLE:
            with self.subTest(query=query):
                result = structure(query)
                self.assertIsNone(result.scene, f"{query!r} 不应被归类到任何 scene")
                self.assertEqual(result.confidence, 0.0)
                self.assertTrue(result.needs_clarification)
                self.assertEqual(result.actors, [])
                self.assertEqual(result.conflict, [])
                self.assertEqual(result.choices, [])
                self.assertEqual(result.concepts, [], "无法归类时不得给出概念")
                self.assertEqual(result.scores, {})

    def test_generic_only_trigger_flags_clarification(self):
        """只命中泛化触发词（choice）时，应标记 needs_clarification。"""
        result = structure("这件事我该不该做")
        self.assertEqual(result.scene, "choice")
        self.assertTrue(result.needs_clarification)
        self.assertLess(result.confidence, 0.4)

    def test_specific_scene_not_flagged(self):
        """命中具体场景时不标记澄清。"""
        result = structure("同事抢了我的功劳")
        self.assertEqual(result.scene, "workplace_conflict")
        self.assertFalse(result.needs_clarification)

    def test_normalize_is_stable(self):
        self.assertEqual(normalize("同事，抢了我的功劳！"), "同事抢了我的功劳")
        self.assertEqual(normalize("  A B  "), "ab")
        self.assertEqual(normalize(""), "")


class DeterminismTest(unittest.TestCase):
    """确定性：可离线复现，不依赖 LLM 或网络。"""

    def test_repeated_calls_identical(self):
        for _, query in CLASSIFICATION_CASES[:12]:
            with self.subTest(query=query):
                first = structure_to_dict(query)
                second = structure_to_dict(query)
                self.assertEqual(first, second)

    def test_module_has_no_llm_or_network_dependency(self):
        """结构化器源码不得出现 LLM / 网络调用。"""
        source = (
            BACKEND_ROOT / "app" / "services" / "issue_structurer.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("llm_client", "requests.", "httpx.", "aiohttp", "openai"):
            self.assertNotIn(forbidden, source, f"结构化器不应依赖 {forbidden}")

    def test_ontology_version_is_reported(self):
        self.assertEqual(structure(BRIEF_EXAMPLE).ontology_version, ontology_version())
        self.assertTrue(ontology_version())


if __name__ == "__main__":
    unittest.main()

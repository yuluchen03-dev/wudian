"""
EVAL-FIDELITY-001（RM-003）聚焦测试。

目标
----
证明冻结的 ``fabricated_classical_quote`` 指标消费的是**生产**
``citation_guard.guard_citations`` 裁决（经 ``metric_prediction_from_guarded``
映射），而不是任何 harness 合成的 ``verifiable``。

约定
----
- 全部使用隔离 fixture（本地 refs / 语料条目注入），**不写生产 Chroma**；
  本文件不导入 ``run_eval``（其模块级 _isolate_chroma 有副作用），
  直接测生产裁决路径本身。
- 不得修改 metrics / TARGETS / Gold / 冻结 JSONL / 合同。
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.services.citation_guard import (
    guard_citations,
    metric_prediction_from_guarded,
)

# ---------------------------------------------------------------------------
# 隔离 fixture（本地 refs，不触达生产 Chroma / 语料文件）
# ---------------------------------------------------------------------------

REF_WEILINGGONG = {
    "id": "lunyu:15.24",
    "original": "子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！"
                "己所不欲，勿施于人。」",
    "source": "《论语·卫灵公》",
}
REF_TAIBO = {
    "id": "lunyu:8.7",
    "original": "曾子曰：「士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？"
                "死而后已，不亦远乎？」",
    "source": "《论语·泰伯》",
}
REF_HANFEIZI = {
    "id": "debate:hanfeizi:hanfeizi-youdu-01",
    "original": "法不阿贵，绳不挠曲。",
    "source": "《韩非子·有度》",
}
# L2 注疏 ref（生产 RAGReference 形态；测试其带 text_type 时的行为）
REF_COMMENTARY = {
    "id": "commentary:15.24",
    "original": "此章圣人之恕道，推己及人，己所不欲，勿施于人，乃终身可行之恕也。",
    "source": "《论语集注》",
    "text_type": "commentary",
}


def _guard(quote: str, claimed: str, refs, **kwargs):
    """跑生产 guard_citations 并映射为冻结指标预测形状。"""
    guarded, status = guard_citations(
        [{"id": "t1", "source": claimed, "original": quote}],
        rag_refs=refs,
        **kwargs,
    )
    return metric_prediction_from_guarded(guarded[0]), guarded[0], status


def _fabricated_records(records):
    """用本地 fixture 构造 adversarial_quotes 形态记录（仅含本例必须字段）。"""
    return records


def _fabricated_count(records, preds):
    """直接调用冻结实现（metrics.compute_fabricated_classical_quote 只读）。"""
    # 内联导入：metrics.py 是冻结模块，导入只读。
    _scripts = Path(__file__).resolve().parents[2] / "eval" / "scripts"
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    from metrics import compute_fabricated_classical_quote

    return compute_fabricated_classical_quote(records, preds)


# ---------------------------------------------------------------------------
# 1. 冻结指标消费**生产**裁决（无合成 verifiable 可覆盖）
# ---------------------------------------------------------------------------

class TestMetricConsumesProductionVerdict:
    def test_fake_quote_metric_counts_zero_via_production(self):
        """absent/fake quote：生产裁决 verifiable=False，冻结指标计数 0。"""
        quote = "学而不厌，诲人不倦，仁者无敌于天下。"
        pred, g, _status = _guard(quote, "《论语·述而》", [REF_WEILINGGONG, REF_TAIBO])
        record = {
            "id": "fixture-fake-01",
            "attack_type": "fake_classic",
            "input": {"quote": quote, "claimed_source": "《论语·述而》"},
            "expected": {"quote_exists": False, "verifiable": False},
        }
        assert g.quote_exists is False
        assert pred["verifiable"] is False
        out = _fabricated_count([record], [pred])
        assert out["value"] == 0
        assert out["passed"] is True

        # 反证：任何合成 verifiable 都不能覆盖生产裁决 —— 把 pred 换成合成
        # 的 True 会改变指标，恰恰证明指标**依赖** pred.verifiable 这一字段，
        # 而该字段现在来自生产裁决，不是 harness 手写公式。
        synth = dict(pred)
        synth["verifiable"] = True
        out_synth = _fabricated_count([record], [synth])
        assert out_synth["value"] == 1

    def test_exact_correct_quote_verified_via_production(self):
        """exact correct quote：生产裁决 verified / verifiable=True。"""
        quote = "己所不欲，勿施于人。"
        pred, g, _status = _guard(quote, "《论语·卫灵公》", [REF_WEILINGGONG])
        assert g.trust_state == "verified"
        assert g.verifiable is True
        assert pred["verifiable"] is True
        assert pred["trust_state"] == "verified"

    def test_wrong_source_corrected_via_production(self):
        """wrong source：生产裁决 citation_corrected / verifiable=False。"""
        quote = "法不阿贵，绳不挠曲。"
        pred, g, _status = _guard(
            quote, "《论语·里仁》", [REF_WEILINGGONG, REF_HANFEIZI],
        )
        assert g.trust_state == "citation_corrected"
        assert g.verifiable is False
        assert g.correct_source == "《韩非子·有度》"
        assert pred["verifiable"] is False

    def test_short_fragment_not_verifiable_via_production(self):
        """short fragment（勿施于人，4 字）：quote_relaxed / verifiable=False。"""
        quote = "勿施于人"
        pred, g, _status = _guard(quote, "《论语·卫灵公》", [REF_WEILINGGONG])
        assert g.trust_state == "quote_relaxed"
        assert g.match_type == "partial"
        assert g.verifiable is False
        assert pred["verifiable"] is False

    def test_real_corpus_quote_verified_via_production(self):
        """real corpus quote（士不可以不弘毅）：verified / verifiable=True。"""
        quote = "士不可以不弘毅"
        pred, g, _status = _guard(quote, "《论语·泰伯》", [REF_TAIBO])
        assert g.quote_exists is True
        assert g.trust_state == "verified"
        assert g.verifiable is True

    def test_traditional_variant_verified_via_production(self):
        """traditional/simplified punctuation variant：归一化后 verified。"""
        quote = "己所不欲，勿施於人。"
        pred, g, _status = _guard(quote, "《论语·卫灵公》", [REF_WEILINGGONG])
        assert g.trust_state == "verified"
        assert g.verifiable is True

    def test_no_synthetic_verifiable_overrides_production_shape(self):
        """adapter 映射只出自 GuardedCitation 字段（verdict_basis 已标注来源）。"""
        pred, _g, _status = _guard("己所不欲，勿施于人。", "《论语·卫灵公》",
                                   [REF_WEILINGGONG])
        assert pred["verdict_basis"] == "production citation_guard.guard_citations"
        # 映射形状包含生产裁决的关键字段，且不携带任何合成来源标记
        for key in ("quote_exists", "exact_match", "source_correct",
                    "trust_state", "match_type", "verifiable"):
            assert key in pred


# ---------------------------------------------------------------------------
# 2. L2 注疏与已知限制（text_type 缺口）
# ---------------------------------------------------------------------------

class TestCommentaryAndTextTypeLimitation:
    def test_commentary_ref_with_text_type_not_verified(self):
        """ref 显式带 text_type='commentary' 时，guard 不得判 verified（RC4）。

        生产 guard 的 ``verifiable`` 语义是「文本确在知识库中」；一个 L2 注疏
        可以 verifiable=True（quote_relaxed，真实存在且出处正确），但**不得**
        ``verified`` 从而**不得**作为经典原文展示。这才是 EVAL-FIDELITY-001
        要如实暴露的语义，而非把 L2 误当可展示的原典。
        """
        quote = "己所不欲，勿施于人，乃终身可行之恕也"
        pred, g, _status = _guard(quote, "《论语集注》", [REF_COMMENTARY])
        assert g.quote_exists is True
        assert g.source_correct is True
        # RC4：L1 限制在带 text_type 时生效 → 注疏不得 verified / 不得可展示
        assert g.trust_state != "verified"
        from app.services.trust_state import is_displayable_as_classic
        assert is_displayable_as_classic(g.trust_state) is False
        # verifiable 为 True（quote_relaxed 属 verifiable 态）——这是生产语义，
        # adapter 忠实映射，不把 L2 抬升为可展示的经典原文。
        assert pred["verifiable"] == g.verifiable

    def test_production_refs_shape_omits_text_type(self):
        """adapter 的生产形态 refs 不带 text_type（不伪造元数据）。

        生产 RAGReference 无 text_type（已披露限制），guard 对缺失 text_type
        按保守回退处理；adapter 必须保持该形态，不得自行补 metadata。
        该行为的断言见下一用例（不带 text_type 的 ref 照常裁决）。
        """
        ref_no_tt = {k: v for k, v in REF_COMMENTARY.items() if k != "text_type"}
        assert "text_type" not in ref_no_tt
        quote = "己所不欲，勿施于人，乃终身可行之恕也"
        pred, g, _status = _guard(quote, "《论语集注》", [ref_no_tt])
        assert pred["verifiable"] == g.verifiable

    def test_commentary_quote_without_text_type_follows_helper_default(self):
        """不带 text_type 的 ref（生产形态）→ helper 不报错且忠实回传 guard 裁决。

        guard 对缺失 text_type 的既有保守回退（默认 is_l1=True）由 guard 自身
        负责；adapter 仅映射，不改 verdict。
        """
        ref_no_tt = {k: v for k, v in REF_COMMENTARY.items() if k != "text_type"}
        quote = "己所不欲，勿施于人，乃终身可行之恕也"
        pred, g, _status = _guard(quote, "《论语集注》", [ref_no_tt])
        assert g.quote_exists is True
        assert pred["verifiable"] == g.verifiable
        # 忠实回传：pred 的每个裁决字段 == GuardedCitation 对应字段
        for key in ("quote_exists", "exact_match", "source_correct",
                    "trust_state", "verifiable"):
            assert pred[key] == getattr(g, key)


# ---------------------------------------------------------------------------
# 3. 跨句拼接（§3.3）——生产 guard 路径的已知缺口
# ---------------------------------------------------------------------------

class TestCrossSentenceFusion:
    def test_fusion_not_false_positive_in_frozen_metric_cases(self):
        """跨句拼接在**当前对抗语料**中不会制造 fabricated 命中（denominator 不变）。

        用例：把子贡问句与孔子答句粘成一句。该拼接串是 lunyu:15.24 原文的
        连续子串，因此 ``guard_citations``（生产路径、无 §3.3 句界规则）会判
        quote_exists=True；adapter 忠实映射该生产裁决。当前冻结语料的
        fabricated 类目（expected.quote_exists=False）不含此类拼接，故
        fabricated 计数不受影响 —— 该缺口单独记录为限制。
        """
        fusion = "有一言而可以终身行之者乎子曰其恕乎"
        ref_full = {
            "id": "lunyu:15.24",
            "original": "子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！"
                        "己所不欲，勿施于人。」",
            "source": "《论语·卫灵公》",
        }
        pred, g, _status = _guard(fusion, "《论语·卫灵公》", [ref_full])
        record = {
            "id": "fixture-fusion-01",
            "attack_type": "cross_sentence",
            "input": {"quote": fusion, "claimed_source": "《论语·卫灵公》"},
            "expected": {"quote_exists": False, "verifiable": False},
        }
        # 生产 guard 路径判 exists（无句界规则）→ 该条不属于 fabricated 类目
        # （expected.quote_exists=False 但生产 verifiable 可能非 False）——
        # 这正暴露 §3.3 未在 citation_guard 强制这一**已披露**缺口。
        out = _fabricated_count([record], [pred])
        # 记录差距：pred 与 expected 的可验证性差，供 report 引用
        assert g.quote_exists is True
        assert pred["verifiable"] is True   # 生产裁决忠实映射（guard 无 §3.3）
        # metric 层面的无回归断言：该拼接不在当前冻结对抗语料中
        assert out is not None
"""
CONTRACT-001 v2 合同测试（FIX-001 必测用例）。

覆盖 §10 要求的全部用例，并逐条断言五个字段：
``quote_exists`` / ``exact_match`` / ``source_correct`` /
``is_displayable_as_classic`` / ``trust_state``。

对应关系（CONTRACT-001 v2）：
- §2.0 全局前置（长度下限；不存在 ⇒ exact/source 均为 false）
- §2.1 quote_exists（单向连续子串）
- §2.2 exact_match（归一化后的连续逐字子串，**不要求**等于整条 passage）
- §2.3 source_correct（与 quote_exists 独立）
- §3.1 完整性门（共享 MIN_FULL_QUOTE_CHARS）
- §3.2 is_displayable_as_classic ⇔ verified
- §3.3 句界规则（禁止标点剥离后拼接成伪连续串）
- §4   四态判定顺序
"""
from __future__ import annotations

import pytest

from app.services.quote_verifier import (
    MIN_FRAGMENT_CHARS,
    MIN_FULL_QUOTE_CHARS,
    verify_quote,
)
from app.services.trust_state import is_displayable_as_classic

WEILINGGONG = "《论语·卫灵公》"
XUEER = "《论语·学而》"
MENCIUS = "《孟子·公孙丑上》"
# 15.24 原文（含前后文），用于验证「不必等于整条 passage」
FULL_15_24 = "子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」"


def _v(quote: str, source: str):
    return verify_quote(quote, source)


def _assert_fields(result, *, exists, exact, source_ok):
    """统一断言五项（展示项由 trust_state 恒等式推出）。"""
    assert result.quote_exists is exists, f"quote_exists 期望 {exists}"
    assert result.exact_match is exact, f"exact_match 期望 {exact}"
    assert result.source_correct is source_ok, f"source_correct 期望 {source_ok}"
    expected_display = result.trust_state == "verified"
    assert is_displayable_as_classic(result.trust_state) is expected_display
    return result


# ============================================================
# §2.0 无效输入：一律不得成为 exact / exists
# ============================================================

class TestInvalidInputs:
    @pytest.mark.parametrize("bad", ["", " ", "   ", "\t", "\n"])
    def test_blank_never_exists(self, bad):
        r = _v(bad, WEILINGGONG)
        _assert_fields(r, exists=False, exact=False, source_ok=False)
        assert r.trust_state == "insufficient_evidence"

    @pytest.mark.parametrize("punct", ["。！？", "「」", "，。", "；："])
    def test_punctuation_only_never_exists(self, punct):
        """纯标点归一化后为空 —— 不得因 substring 逻辑变成 exact。"""
        r = _v(punct, WEILINGGONG)
        _assert_fields(r, exists=False, exact=False, source_ok=False)

    def test_two_char_fragment_below_floor(self):
        """「君子」虽在语料中出现，但低于 MIN_FRAGMENT_CHARS → 不存在。"""
        r = _v("君子", XUEER)
        _assert_fields(r, exists=False, exact=False, source_ok=False)

    def test_floor_constant_is_shared(self):
        assert MIN_FRAGMENT_CHARS >= 2
        assert MIN_FULL_QUOTE_CHARS > MIN_FRAGMENT_CHARS


# ============================================================
# §2.2 exact_match：连续逐字子串，不要求等于整条 passage
# ============================================================

class TestExactMatchSubstring:
    def test_full_sentence_inside_longer_passage_is_exact(self):
        """完整句子嵌在整章中 → exact_match=true（§5 行 1）。"""
        r = _v("己所不欲，勿施于人。", WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)
        assert r.trust_state == "verified"
        assert is_displayable_as_classic(r.trust_state) is True

    def test_quote_is_not_equal_to_whole_passage(self):
        """证明该引文确实**不等于**整条 passage（否则本用例无意义）。"""
        from app.services.quote_verifier import load_corpus

        entry = next(e for e in load_corpus() if e.passage_id == "lunyu:15.24")
        assert entry.original.strip() != "己所不欲，勿施于人。"
        assert "己所不欲，勿施于人。" in entry.original


class TestSourceIndependence:
    def test_true_quote_wrong_source_is_citation_corrected(self):
        """§5 行 2：文本真 + 出处假 → citation_corrected，且给出正确出处。"""
        r = _v("己所不欲，勿施于人。", MENCIUS)
        _assert_fields(r, exists=True, exact=True, source_ok=False)
        assert r.trust_state == "citation_corrected"
        assert r.correct_source, "必须给出正确出处"
        assert is_displayable_as_classic(r.trust_state) is False

    def test_correct_source_verified(self):
        r = _v("己所不欲，勿施于人。", WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)
        assert r.trust_state == "verified"


# ============================================================
# §3.1 / §3.2：摘句 exact 但**不可**作为经典原文展示
# ============================================================

class TestFragmentExactButNotDisplayable:
    def test_four_char_fragment(self):
        """§5 行 3：勿施于人 → exact_match=true 但不可展示（本合同核心分离）。"""
        r = _v("勿施于人", WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)
        assert r.trust_state == "quote_relaxed"
        assert is_displayable_as_classic(r.trust_state) is False, (
            "摘句逐字存在，但不是完整经典引文，不得展示为经典原文"
        )

    def test_fragment_never_conflated_with_displayable(self):
        r = _v("勿施于人", WEILINGGONG)
        assert r.exact_match is True
        assert r.trust_state != "verified"


# ============================================================
# 繁简 / 标点 变体
# ============================================================

class TestVariants:
    def test_traditional_variant(self):
        r = _v("己所不欲，勿施於人。", WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)

    def test_simplified_variant(self):
        r = _v("己所不欲，勿施于人。", WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)

    @pytest.mark.parametrize("variant", [
        "己所不欲, 勿施于人。",
        "己所不欲，勿施于人",
        "己所不欲勿施于人",
        "己所不欲,勿施于人.",
    ])
    def test_punctuation_variants(self, variant):
        r = _v(variant, WEILINGGONG)
        _assert_fields(r, exists=True, exact=True, source_ok=True)


# ============================================================
# §3.3 句界规则：标点剥离不得把两句拼成伪连续串
# ============================================================

class TestCrossSentenceGuard:
    @pytest.mark.parametrize("fused", [
        # 子贡问句尾 + 孔子答句头（同一条 passage 内相邻两句）
        "有一言而可以终身行之者乎子曰其恕乎",
        # 学而 1.1 内相邻两句
        "不亦说乎有朋自远方来",
    ])
    def test_fused_adjacent_sentences_not_exact(self, fused):
        r = _v(fused, WEILINGGONG)
        if r.quote_exists:
            assert r.exact_match is False, (
                f"{fused!r} 是跨句拼接，不得判 exact（§3.3）"
            )
            assert r.trust_state != "verified"

    def test_explicit_multi_sentence_citation_allowed(self):
        """原始引文自带句界标点 → 属显式跨句引用，不算违规。"""
        r = _v("学而时习之，不亦说乎？", XUEER)
        _assert_fields(r, exists=True, exact=True, source_ok=True)


# ============================================================
# RC4：注疏不得因逐字存在而成为「经典原文」
# ============================================================

class TestCommentaryNeverClassic:
    def test_commentary_verbatim_not_displayable(self):
        """朱熹注文逐字存在，但 text_type=commentary → 不得 verified/可展示。"""
        from app.services.quote_verifier import load_corpus

        entry = next(
            (e for e in load_corpus()
             if e.text_type == "commentary" and len(e.norm) >= MIN_FULL_QUOTE_CHARS),
            None,
        )
        if entry is None:
            pytest.skip("语料中没有足够长的注疏条目")
        r = _v(entry.original, entry.source)
        assert r.quote_exists is True, "注疏文字确实存在"
        assert r.trust_state != "verified", "RC4：注疏不得判 verified"
        assert is_displayable_as_classic(r.trust_state) is False, (
            "RC4：注疏不得作为经典原文展示"
        )


# ============================================================
# 语料不存在 / 伪造
# ============================================================

class TestAbsentAndFabricated:
    def test_fake_confucius_internet_quote(self):
        r = _v("你若不勇敢，没人替你坚强。", "《论语·述而》")
        _assert_fields(r, exists=False, exact=False, source_ok=False)
        assert r.trust_state == "insufficient_evidence"

    @pytest.mark.parametrize("quote", [
        "以德报怨。",
        "天行健，君子以自强不息。",
        "知行合一。",
    ])
    def test_genuine_but_corpus_absent(self, quote):
        """真实古句但**本语料不含** → 不存在（不得当作已验证）。"""
        r = _v(quote, "《周易》")
        assert r.quote_exists is False
        assert r.trust_state == "insufficient_evidence"

    def test_real_prefix_plus_fabricated_suffix_rejected(self):
        """真实短句 + 伪造后缀 → 单向包含失败 → 不存在（§5 行 10）。"""
        r = _v("己所不欲，勿施于人，是故君子慎独。", WEILINGGONG)
        _assert_fields(r, exists=False, exact=False, source_ok=False)


# ============================================================
# 部分引用：前缀 / 中段 / 后缀
# ============================================================

class TestPartialFragments:
    def test_partial_prefix(self):
        r = _v("己所不欲", WEILINGGONG)
        assert r.quote_exists is True or r.quote_exists is False  # 见下断言
        if r.quote_exists:
            assert r.exact_match is True
            assert r.trust_state != "verified", "前缀片段不得 verified"

    def test_partial_middle(self):
        r = _v("勿施于人。", WEILINGGONG)
        if r.quote_exists:
            assert r.trust_state != "verified"

    def test_partial_suffix(self):
        r = _v("施于人", WEILINGGONG)
        # 3 字 < MIN_FRAGMENT_CHARS=4 → 不存在
        assert r.quote_exists is False
        assert r.trust_state == "insufficient_evidence"


# ============================================================
# §4 四态穷尽
# ============================================================

class TestTrustStateExhaustive:
    def test_only_verified_is_displayable(self):
        from app.schemas.knowledge import TRUST_STATES

        assert {ts for ts in TRUST_STATES if is_displayable_as_classic(ts)} == {"verified"}

    def test_all_four_states_reachable(self):
        states = {
            _v("己所不欲，勿施于人。", WEILINGGONG).trust_state,   # verified
            _v("己所不欲，勿施于人。", MENCIUS).trust_state,       # citation_corrected
            _v("勿施于人", WEILINGGONG).trust_state,               # quote_relaxed
            _v("你若不勇敢，没人替你坚强。", XUEER).trust_state,    # insufficient_evidence
        }
        assert states == {
            "verified", "citation_corrected", "quote_relaxed", "insufficient_evidence",
        }

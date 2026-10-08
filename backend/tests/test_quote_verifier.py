"""
悟典 - Quote Verifier 对抗测试（PHASE 5 / P5-01、P5-10）

覆盖 ``03-task-dag.md`` §7「P5-05 必含对抗用例」：

============  ==========================================================
A1            真古文 + 同书错篇 → ``quote_exists=True`` & ``source_correct=False``
A2            真古文 + 跨书错派（**修复前实测 FAIL**）→ 同上，且给 ``correct_source``
B1            2 字片段（``君子``）→ 不可验证
B2            3 字截断片段（``不亦说乎``）→ 不判 ``verified``
C1            纯假古文 → ``quote_exists=False`` / ``insufficient_evidence``
C2            繁体版本 → 归一化命中
C3            网络鸡汤冒充孔子 → ``quote_exists=False``
D1            ``candidates[]`` 不产生重复来源
============  ==========================================================

公平性要求（``03-task-dag.md`` §7 末段）：
C1/C3 在收紧**之前**已被正确拒绝，收紧后**必须继续拒绝**，不得因收紧而误伤。
本文件对这三类同时断言"修复后仍拒绝"。

断言强度：所有断言均针对**具体字段值与判定语义**，
不使用"对象可构造"式的弱断言。
"""
from __future__ import annotations

import pytest

from app.services.quote_verifier import (
    MIN_FRAGMENT_CHARS,
    MIN_FULL_QUOTE_CHARS,
    load_corpus,
    normalize_text,
    parse_source,
    to_simplified,
    verify_quote,
)
from app.services.trust_state import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    decide_trust_state,
    explain,
    is_displayable_as_classic,
    is_verifiable,
)

# 真实语料中的既定事实（已由 t4 审计 + 本次实测确认）
QUOTE_YI_SUO_BU_YU = "己所不欲，勿施于人。"
#: 《论语·卫灵公》15.24 与《论语·颜渊》12.2 均含此句
CORRECT_SOURCE_WEILINGGONG = "《论语·卫灵公》"
CORRECT_SOURCE_YANYUAN = "《论语·颜渊》"
WRONG_SOURCE_SAME_BOOK = "《论语·学而》"
WRONG_SOURCE_OTHER_SCHOOL = "《孟子·公孙丑上》"


@pytest.fixture(scope="module")
def corpus():
    """真实全库语料（只读）。"""
    entries = load_corpus()
    assert len(entries) >= 100, "语料加载异常：条目过少"
    return entries


# ============================================================
# 基础：两个指标必须独立
# ============================================================

class TestIndependentMetrics:
    """acceptance：``quote_exists`` 与 ``source_correct`` 是两个独立字段。"""

    def test_contract_has_both_independent_fields(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        # 两个字段同时出现在同一响应里
        dumped = result.model_dump()
        assert "quote_exists" in dumped
        assert "source_correct" in dumped

    def test_quote_exists_true_with_source_correct_false(self, corpus):
        """核心组合：文本真实存在，但出处错误（brief 第十一章要求）。"""
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert result.quote_exists is True
        assert result.source_correct is False
        assert result.trust_state == "citation_corrected"

    def test_quote_exists_false_with_source_correct_false(self, corpus):
        result = verify_quote("子贡问曰：同事抢功，当何以处之？", "《论语·子贡》", entries=corpus)
        assert result.quote_exists is False
        assert result.source_correct is False

    def test_both_true_yields_verified(self, corpus):
        result = verify_quote(
            "士不可以不弘毅，任重而道远。", "《论语·泰伯》", entries=corpus,
        )
        assert result.quote_exists is True
        assert result.source_correct is True
        assert result.trust_state == "verified"


# ============================================================
# A1 / A2：真古文 + 错误出处
# ============================================================

class TestA1SameBookWrongChapter:
    """A1：真古文 + **同书错篇**。"""

    def test_a1_quote_exists_true_source_correct_false(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_SAME_BOOK, entries=corpus)
        assert result.quote_exists is True, "该句真实存在于《论语》"
        assert result.source_correct is False, "《论语·学而》并非该句出处"

    def test_a1_trust_state_is_citation_corrected(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_SAME_BOOK, entries=corpus)
        assert result.trust_state == "citation_corrected"

    def test_a1_provides_correct_source_in_same_book(self, corpus):
        """correct_source 必须是**真实存在**的语料条目，且与声称出处同书。"""
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_SAME_BOOK, entries=corpus)
        assert result.correct_source is not None
        assert "论语" in result.correct_source, (
            f"correct_source 应指向《论语》真实篇章，实际为 {result.correct_source!r}"
        )
        # 必须能在语料中真的找到该出处
        assert any(e.source == result.correct_source for e in corpus)


class TestA2CrossBookWrongSchool:
    """A2：真古文 + **跨书错派**。

    这是 PROJECT-BRIEF 第十六章第一例，**修复前实测 FAIL**
    （``verifiable=True`` / ``status=all_verified``，错误出处原样保留）。
    """

    def test_a2_quote_exists_true(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert result.quote_exists is True

    def test_a2_source_correct_false(self, corpus):
        """**不得**因该句存在于《论语》就认可《孟子》为出处。"""
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert result.source_correct is False, (
            "『己所不欲，勿施于人』出自《论语》，不是《孟子·公孙丑上》"
        )

    def test_a2_trust_state_citation_corrected(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert result.trust_state == "citation_corrected"

    def test_a2_correct_source_is_lunyu(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert result.correct_source is not None
        assert "论语" in result.correct_source
        assert "孟子" not in result.correct_source
        assert any(e.source == result.correct_source for e in corpus), (
            "correct_source 必须是语料中真实存在的出处，不得编造"
        )

    def test_a2_not_reported_as_verifiable(self, corpus):
        """该例**不得**被判为可验证（修复前的核心缺陷）。"""
        result = verify_quote(QUOTE_YI_SUO_BU_YU, WRONG_SOURCE_OTHER_SCHOOL, entries=corpus)
        assert is_verifiable(result.trust_state) is False


# ============================================================
# B1 / B2：短片段必须被拒绝
# ============================================================

class TestB1TwoCharFragment:
    """B1：2 字片段 ``君子`` → 不可验证（修复前实测 FAIL）。"""

    def test_b1_two_char_fragment_not_exists(self, corpus):
        result = verify_quote("君子", "《论语·学而》", entries=corpus)
        assert result.quote_exists is False
        assert result.match_type == "none"

    def test_b1_trust_state_insufficient_evidence(self, corpus):
        result = verify_quote("君子", "《论语·学而》", entries=corpus)
        assert result.trust_state == "insufficient_evidence"

    def test_b1_not_verifiable(self, corpus):
        result = verify_quote("君子", "《论语·学而》", entries=corpus)
        assert is_verifiable(result.trust_state) is False

    def test_b1_below_threshold_is_rejected_generically(self, corpus):
        """任何低于长度下限的片段都不得通过（不只 ``君子`` 一例）。"""
        for fragment in ("君子", "仁义", "道德", "不亦"):
            result = verify_quote(fragment, "《论语·学而》", entries=corpus)
            assert result.quote_exists is False, f"{fragment!r} 不应被判为存在"

    def test_b1_threshold_is_meaningful(self):
        assert MIN_FRAGMENT_CHARS >= 3, "长度下限过低会放过无意义片段"


class TestB2ThreeCharFragment:
    """B2：3 字截断片段 → ``verifiable=False`` 或标 partial 且不计入 verified。"""

    def test_b2_short_fragment_never_verified(self, corpus):
        result = verify_quote("不亦说乎", "《论语·学而》", entries=corpus)
        assert result.trust_state != "verified", (
            "截断片段不得判为 verified"
        )

    def test_b2_fragment_not_counted_as_verifiable(self, corpus):
        result = verify_quote("不亦说乎", "《论语·学而》", entries=corpus)
        assert is_verifiable(result.trust_state, result.match_type) is False

    def test_b2_partial_fragments_excluded_from_verified(self, corpus):
        """介于两阈值之间的片段一律 partial，不计入 verified。"""
        for fragment in ("不亦说乎", "勿施于人", "任重道远"):
            result = verify_quote(fragment, "《论语·学而》", entries=corpus)
            if result.quote_exists:
                assert result.match_type == "partial", (
                    f"{fragment!r} 应标为 partial，实际 {result.match_type!r}"
                )
            assert is_verifiable(result.trust_state, result.match_type) is False


# ============================================================
# C1 / C2 / C3：公平性回归
# ============================================================

class TestC1FabricatedClassic:
    """C1：纯假古文（拼凑句）→ ``quote_exists=False``。

    修复前**已被正确拒绝**，修复后必须保持。
    """

    def test_c1_fabricated_quote_not_exists(self, corpus):
        result = verify_quote(
            "子贡问曰：同事抢功，当何以处之？", "《论语·子贡》", entries=corpus,
        )
        assert result.quote_exists is False
        assert result.source_correct is False

    def test_c1_trust_state_insufficient_evidence(self, corpus):
        result = verify_quote(
            "子贡问曰：同事抢功，当何以处之？", "《论语·子贡》", entries=corpus,
        )
        assert result.trust_state == "insufficient_evidence"

    def test_c1_message_is_the_refusal_text(self, corpus):
        """证据不足时必须给出 brief 第十二章的拒答文案，不得编造古文。"""
        result = verify_quote("孔子曰：职场如战场，先发制人。", "《论语》", entries=corpus)
        assert result.trust_state == "insufficient_evidence"
        assert explain(result.trust_state) == INSUFFICIENT_EVIDENCE_MESSAGE
        assert "没有检索到足够可靠的原典" in INSUFFICIENT_EVIDENCE_MESSAGE

    def test_c1_fabricated_long_text_with_embedded_real_quote(self, corpus):
        """**T-04 回归**：伪造长文内嵌真实短句，旧双向子串实现会放行。"""
        fabricated = (
            "网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。"
        )
        result = verify_quote(fabricated, "《论语·卫灵公》", entries=corpus)
        assert result.quote_exists is False, (
            "伪造长文包含真实短句，但整段并非原典，不得判为存在（单向匹配）"
        )
        assert result.trust_state == "insufficient_evidence"


class TestC2TraditionalChinese:
    """C2：繁体版本 → 归一化后应命中。"""

    def test_c2_traditional_normalizes_to_simplified(self):
        assert to_simplified("己所不欲，勿施於人。") == "己所不欲，勿施于人。"

    def test_c2_normalize_strips_punctuation(self):
        assert normalize_text("己所不欲，勿施於人。") == normalize_text(
            "己所不欲,勿施于人"
        )

    def test_c2_traditional_quote_is_found(self, corpus):
        """繁体版本必须能在知识库中命中（不得因收紧而误伤）。"""
        result = verify_quote("己所不欲，勿施於人。", CORRECT_SOURCE_WEILINGGONG, entries=corpus)
        assert result.quote_exists is True, "繁体版本应经归一化后命中"
        assert result.source_correct is True
        assert result.trust_state in ("quote_relaxed", "verified")

    def test_c2_traditional_not_verified_when_not_exact(self, corpus):
        """繁简差异属"归一化命中"，非逐字命中 → 不得判 verified。"""
        result = verify_quote("己所不欲，勿施於人。", CORRECT_SOURCE_WEILINGGONG, entries=corpus)
        assert result.exact_match is False
        assert result.trust_state == "quote_relaxed"


class TestC3ModernChickenSoup:
    """C3：网络鸡汤冒充孔子 → ``quote_exists=False``。

    修复前**已被正确拒绝**，修复后必须保持。
    """

    def test_c3_chicken_soup_not_exists(self, corpus):
        result = verify_quote(
            "你若不勇敢，没人替你坚强。", "《论语·述而》", entries=corpus,
        )
        assert result.quote_exists is False
        assert result.trust_state == "insufficient_evidence"

    def test_c3_multiple_chicken_soup_variants_rejected(self, corpus):
        variants = [
            "你若不勇敢，没人替你坚强。",
            "努力到无能为力，拼搏到感动自己。",
            "心若向阳，无谓悲伤。",
            "所有的失去，都会以另一种方式归来。",
        ]
        for text in variants:
            result = verify_quote(text, "《论语》", entries=corpus)
            assert result.quote_exists is False, f"鸡汤 {text!r} 不得被判为存在"

    def test_c3_no_candidates_for_fabricated(self, corpus):
        result = verify_quote("你若不勇敢，没人替你坚强。", "《论语·述而》", entries=corpus)
        assert result.candidates == []


# ============================================================
# D1：candidates 不产生重复来源
# ============================================================

class TestD1NoDuplicateSources:
    """D1：``candidates[]`` 不得出现同一文本的两个互不相干 ``passage_id``。"""

    def test_d1_quoted_fragment_has_unique_sources(self, corpus):
        result = verify_quote("士不可以不弘毅，任重而道远。", "《论语·泰伯》", entries=corpus)
        sources = [c.source for c in result.candidates]
        assert len(sources) == len(set(sources)), (
            f"candidates 出现重复来源: {sources}"
        )

    def test_d1_full_sentence_has_unique_sources(self, corpus):
        full = (
            "曾子曰：「士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？"
            "死而后已，不亦远乎？」"
        )
        result = verify_quote(full, "《论语·泰伯》", entries=corpus)
        sources = [c.source for c in result.candidates]
        assert len(sources) == len(set(sources))

    def test_d1_taibo_not_duplicated(self, corpus):
        """《论语·泰伯》在语料中有两条（全句 + 摘句），不得并列输出。"""
        result = verify_quote("士不可以不弘毅，任重而道远。", "《论语·泰伯》", entries=corpus)
        taibo = [c for c in result.candidates if "泰伯" in c.source]
        assert len(taibo) <= 1, f"《论语·泰伯》重复出现: {[c.passage_id for c in taibo]}"

    def test_d1_candidates_have_valid_text_types(self, corpus):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, CORRECT_SOURCE_WEILINGGONG, entries=corpus)
        assert result.candidates
        for candidate in result.candidates:
            assert candidate.text_type in {
                "original", "commentary", "translation", "modern_explanation",
            }


# ============================================================
# 出处缺失：不得放行
# ============================================================

class TestMissingSourceNotPassed:
    """acceptance：空出处不得放行（原 ``citation_validator.py:99-100`` 缺陷）。"""

    @pytest.mark.parametrize("missing", ["", "无", "未知", "   ", "none"])
    def test_missing_source_never_source_correct(self, corpus, missing):
        result = verify_quote(QUOTE_YI_SUO_BU_YU, missing, entries=corpus)
        assert result.source_correct is False, (
            f"出处 {missing!r} 不得被判为正确"
        )

    def test_missing_source_yields_citation_corrected(self, corpus):
        """文本存在但未给（有效）出处 → citation_corrected，并给出正确出处。"""
        result = verify_quote(QUOTE_YI_SUO_BU_YU, "", entries=corpus)
        assert result.quote_exists is True
        assert result.source_correct is False
        assert result.trust_state == "citation_corrected"
        assert result.correct_source is not None


# ============================================================
# Trust State 判定规则（P5-04）
# ============================================================

class TestTrustStateRules:
    """四态判定规则必须与 ``02-architecture.md`` §9.2 冻结表一致。"""

    def test_four_states_only(self):
        from app.schemas.knowledge import TRUST_STATES
        assert TRUST_STATES == {
            "verified", "citation_corrected", "quote_relaxed", "insufficient_evidence",
        }

    def test_not_exists_is_insufficient_evidence(self):
        assert decide_trust_state(
            quote_exists=False, source_correct=False, exact_match=False,
        ) == "insufficient_evidence"

    def test_exists_but_wrong_source_is_citation_corrected(self):
        assert decide_trust_state(
            quote_exists=True, source_correct=False, exact_match=True,
        ) == "citation_corrected"

    def test_exists_correct_and_exact_is_verified(self):
        assert decide_trust_state(
            quote_exists=True, source_correct=True, exact_match=True, match_type="exact",
        ) == "verified"

    def test_exists_correct_but_normalized_is_quote_relaxed(self):
        assert decide_trust_state(
            quote_exists=True, source_correct=True, exact_match=False,
            match_type="normalized",
        ) == "quote_relaxed"

    def test_partial_match_never_verified(self):
        """摘句即使文本存在且出处正确，也不得判 verified。"""
        assert decide_trust_state(
            quote_exists=True, source_correct=True, exact_match=True,
            match_type="partial",
        ) == "quote_relaxed"

    def test_wrong_source_beats_exact_match(self):
        """出处错误优先于逐字命中：不得因逐字存在就报 verified。"""
        assert decide_trust_state(
            quote_exists=True, source_correct=False, exact_match=True, match_type="exact",
        ) == "citation_corrected"

    def test_display_rules(self):
        assert is_displayable_as_classic("verified") is True
        assert is_displayable_as_classic("quote_relaxed") is True
        assert is_displayable_as_classic("citation_corrected") is False
        assert is_displayable_as_classic("insufficient_evidence") is False

    def test_citation_corrected_is_not_verifiable(self):
        """原声称出处错误 → 不算 verifiable。"""
        assert is_verifiable("citation_corrected") is False
        assert is_verifiable("verified") is True
        assert is_verifiable("quote_relaxed") is True
        assert is_verifiable("insufficient_evidence") is False

    def test_every_state_has_explanation(self):
        for state in ("verified", "citation_corrected", "quote_relaxed",
                      "insufficient_evidence"):
            assert explain(state).strip()


# ============================================================
# 辅助函数与语料完整性
# ============================================================

class TestHelpersAndCorpus:
    def test_parse_source_variants(self):
        assert parse_source("《论语·学而》") == ("论语", "学而")
        assert parse_source("《孟子·公孙丑上》") == ("孟子", "公孙丑上")
        assert parse_source("《将进酒》") == ("将进酒", "")
        assert parse_source("") == ("", "")

    def test_corpus_is_non_trivial(self, corpus):
        assert len(corpus) >= 100, f"语料仅 {len(corpus)} 条，与实测 143 条不符"

    def test_corpus_contains_original_and_commentary(self, corpus):
        types = {e.text_type for e in corpus}
        assert "original" in types
        assert "commentary" in types, "L2 注疏应进入可核验范围"

    def test_corpus_entries_have_real_sources(self, corpus):
        """每条语料必须有非空 source，且不得是编造占位。"""
        for entry in corpus:
            assert entry.source.strip()
            assert entry.source not in {"未知", "无", "unknown"}

    def test_verified_result_candidates_point_to_real_entries(self, corpus):
        result = verify_quote(
            "士不可以不弘毅，任重而道远。", "《论语·泰伯》", entries=corpus,
        )
        corpus_ids = {e.passage_id for e in corpus}
        for candidate in result.candidates:
            assert candidate.passage_id in corpus_ids, (
                f"candidate {candidate.passage_id!r} 不在真实语料中"
            )

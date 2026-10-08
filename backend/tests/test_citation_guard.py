"""
悟典 - Citation Guard 对抗测试（PHASE 5 / P5-02、P5-05、P5-10）

覆盖三组能力：

1. **Evidence Pack 白名单**：Pack 外的 source 一律 ``verifiable=False``。
2. **收紧后的匹配**：消除旧 ``citation_validator`` 的双向子串绕过（T-04）
   与空出处放行（T-05）。
3. **``citation_validator`` 兼容性**：``validate()`` 签名与 ``SAGE_CLASSICS``
   保持不变，且 A1/A2/B1/C1/C2/C3 在**不启用**白名单的旧调用路径下
   同样得到修复后的正确判定。

断言强度：针对具体字段值与判定语义，不使用"对象可构造"式弱断言。
"""
from __future__ import annotations

import asyncio

import pytest

from app.schemas.knowledge import EvidenceItem, EvidencePack
from app.services.citation_guard import (
    CitationWhitelist,
    guard_citations,
    quote_is_supported_by_refs,
    source_matches_quote,
)
from app.services.citation_validator import (
    SAGE_CLASSICS,
    CitationValidator,
    citation_validator,
)

# 真实检索结果样式（与 rag_service 返回结构一致）
REF_WEILINGGONG = {
    "original": "子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」",
    "source": "《论语·卫灵公》",
    "chapter": "卫灵公",
    "verse_id": "lunyu:15.24",
}
REF_YANYUAN = {
    "original": "仲弓问仁。子曰：「出门如见大宾，使民如承大祭。己所不欲，勿施于人。在邦无怨，在家无怨。」",
    "source": "《论语·颜渊》",
    "chapter": "颜渊",
    "verse_id": "lunyu:12.2",
}
REF_TAIBO = {
    "original": "曾子曰：「士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？死而后已，不亦远乎？」",
    "source": "《论语·泰伯》",
    "chapter": "泰伯",
    "verse_id": "lunyu:8.7",
}
QUOTE_YI_SUO_BU_YU = "己所不欲，勿施于人。"


# ============================================================
# 1. 白名单
# ============================================================

class TestCitationWhitelist:
    def _pack(self) -> EvidencePack:
        return EvidencePack(
            query="同事抢功怎么办",
            scenario="workplace_conflict",
            concepts=["义"],
            evidence=[
                EvidenceItem(
                    evidence_id="ev1", original=QUOTE_YI_SUO_BU_YU,
                    source="《论语·卫灵公》", school="儒家", text_type="original",
                    relevance=0.9,
                ),
                EvidenceItem(
                    evidence_id="ev2", original="法不阿贵，绳不挠曲。",
                    source="《韩非子·有度》", school="法家", text_type="original",
                    relevance=0.8,
                ),
            ],
        )

    def test_whitelist_built_from_pack(self):
        whitelist = CitationWhitelist.from_evidence_pack(self._pack())
        assert len(whitelist) == 2
        assert "《论语·卫灵公》" in whitelist.sources

    def test_allows_source_inside_pack(self):
        whitelist = CitationWhitelist.from_evidence_pack(self._pack())
        assert whitelist.allows_source("《论语·卫灵公》") is True

    def test_rejects_source_outside_pack(self):
        whitelist = CitationWhitelist.from_evidence_pack(self._pack())
        assert whitelist.allows_source("《孟子·公孙丑上》") is False

    @pytest.mark.parametrize("bad", ["", "无", "   ", None])
    def test_empty_source_never_allowed(self, bad):
        whitelist = CitationWhitelist.from_evidence_pack(self._pack())
        assert whitelist.allows_source(bad) is False

    def test_empty_pack_denies_everything(self):
        whitelist = CitationWhitelist.from_evidence_pack(
            EvidencePack(query="q", evidence=[])
        )
        assert len(whitelist) == 0
        assert whitelist.allows_source("《论语·卫灵公》") is False

    def test_blank_original_not_admitted(self):
        """正文归一化后为空的证据不得入白名单（不静默放行）。"""
        pack = EvidencePack(query="q", evidence=[EvidenceItem(
            evidence_id="ev_blank", original="。，！", source="《论语·学而》",
            text_type="original", relevance=0.5,
        )])
        assert len(CitationWhitelist.from_evidence_pack(pack)) == 0


class TestGuardCitationsWithWhitelist:
    def _whitelist(self) -> CitationWhitelist:
        return CitationWhitelist.from_items([EvidenceItem(
            evidence_id="ev1", original=REF_WEILINGGONG["original"],
            source="《论语·卫灵公》", text_type="original", relevance=0.9,
        )])

    def test_citation_inside_pack_verifies(self):
        guarded, status = guard_citations(
            [{"id": "引1", "出处": "《论语·卫灵公》", "原文": QUOTE_YI_SUO_BU_YU}],
            whitelist=self._whitelist(),
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].verifiable is True
        assert guarded[0].trust_state == "verified"
        assert status == "all_verified"

    def test_citation_outside_pack_rejected(self):
        """acceptance：Evidence Pack 外的 source 一律不可验证。"""
        guarded, status = guard_citations(
            [{"id": "引1", "出处": "《孟子·公孙丑上》", "原文": QUOTE_YI_SUO_BU_YU}],
            whitelist=self._whitelist(),
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].verifiable is False
        assert "白名单" in guarded[0].reason
        assert status == "unverified"

    def test_empty_whitelist_rejects_all(self):
        guarded, status = guard_citations(
            [{"id": "引1", "出处": "《论语·卫灵公》", "原文": QUOTE_YI_SUO_BU_YU}],
            whitelist=CitationWhitelist.from_items([]),
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].verifiable is False
        assert status == "unverified"

    def test_whitelist_hit_but_wrong_source_rejected(self):
        """在白名单内但出处与命中条目不一致 → 仍不可验证。"""
        guarded, _status = guard_citations(
            [{"id": "引1", "出处": "《论语·颜渊》", "原文": "法不阿贵，绳不挠曲。"}],
            whitelist=self._whitelist(),
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].verifiable is False


# ============================================================
# 2. 收紧后的匹配（T-04 / T-05 回归）
# ============================================================

class TestTightenedMatching:
    def test_single_direction_blocks_embedded_fabrication(self):
        """T-04：伪造长文内嵌真实短句 → 单向匹配必须拒绝。"""
        fabricated = "网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。"
        assert quote_is_supported_by_refs(fabricated, [REF_WEILINGGONG]) is False

    def test_reverse_containment_is_rejected(self):
        """反向包含（原典 ⊆ 引文）必须被拒绝。"""
        long_quote = REF_WEILINGGONG["original"] + "此外还有编造的后半句。"
        assert quote_is_supported_by_refs(long_quote, [REF_WEILINGGONG]) is False

    def test_forward_containment_accepted(self):
        """正向包含（引文 ⊆ 原典）应通过。"""
        assert quote_is_supported_by_refs(QUOTE_YI_SUO_BU_YU, [REF_WEILINGGONG]) is True

    @pytest.mark.parametrize("fragment", ["君子", "仁义", "道德", "不亦"])
    def test_short_fragments_rejected(self, fragment):
        """长度下限：过短片段不得通过。"""
        assert quote_is_supported_by_refs(fragment, [REF_WEILINGGONG]) is False

    def test_punctuation_normalization_allows_match(self):
        """标点差异不应阻止匹配（归一化）。"""
        assert quote_is_supported_by_refs("己所不欲 勿施于人", [REF_WEILINGGONG]) is True

    def test_traditional_allows_match(self):
        """繁体差异不应阻止匹配（归一化）。"""
        assert quote_is_supported_by_refs("己所不欲，勿施於人。", [REF_WEILINGGONG]) is True

    def test_no_refs_means_no_support(self):
        assert quote_is_supported_by_refs(QUOTE_YI_SUO_BU_YU, []) is False

    def test_refs_without_original_are_skipped(self):
        assert quote_is_supported_by_refs(
            QUOTE_YI_SUO_BU_YU, [{"source": "《论语·卫灵公》"}],
        ) is False


class TestSourceCorrectness:
    """出处正确性判定（T-03 / T-05 回归）。"""

    def test_correct_source_accepted(self):
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, "《论语·卫灵公》", [REF_WEILINGGONG],
        ) is True

    def test_same_book_wrong_chapter_rejected(self):
        """T-03：同书错篇必须被发现（旧实现只比书名关键词）。"""
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, "《论语·学而》", [REF_WEILINGGONG],
        ) is False

    def test_cross_book_wrong_school_rejected(self):
        """A2：跨书错派必须被发现。"""
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, "《孟子·公孙丑上》", [REF_WEILINGGONG],
        ) is False

    @pytest.mark.parametrize("missing", ["", "无", "未知", "   ", None])
    def test_missing_source_never_correct(self, missing):
        """T-05：空出处不得放行。"""
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, missing, [REF_WEILINGGONG],
        ) is False

    def test_chapter_suffix_ignored(self):
        """『卫灵公篇』与『卫灵公』应视为一致。"""
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, "《论语·卫灵公篇》", [REF_WEILINGGONG],
        ) is True

    def test_book_only_source_accepted(self):
        """只给书名且书名正确 → 视为出处正确（篇章未声明，不算错误）。"""
        assert source_matches_quote(
            QUOTE_YI_SUO_BU_YU, "《论语》", [REF_WEILINGGONG],
        ) is True

    def test_correct_source_reported_when_wrong(self):
        guarded, _status = guard_citations(
            [{"id": "引1", "出处": "《孟子·公孙丑上》", "原文": QUOTE_YI_SUO_BU_YU}],
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].source_correct is False
        assert guarded[0].correct_source == "《论语·卫灵公》"

    def test_correct_source_is_null_when_source_right(self):
        guarded, _status = guard_citations(
            [{"id": "引1", "出处": "《论语·卫灵公》", "原文": QUOTE_YI_SUO_BU_YU}],
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].source_correct is True
        assert guarded[0].correct_source is None


# ============================================================
# 3. citation_validator 兼容性 + 修复后行为
# ============================================================

class TestCitationValidatorCompatibility:
    """acceptance：不推翻 ``validate()`` 签名与 ``SAGE_CLASSICS``。"""

    def test_sage_classics_preserved(self):
        assert SAGE_CLASSICS["confucius"] == [
            "论语", "春秋", "诗经", "尚书", "礼记", "周易",
        ]
        assert SAGE_CLASSICS["mencius"] == ["孟子"]
        assert SAGE_CLASSICS["hanfeizi"] == ["韩非子", "韩非"]

    def test_validate_signature_unchanged(self):
        """``validate(sage_key, citations, rag_refs)`` 位置参数保持可用。"""
        validated, status = asyncio.run(
            citation_validator.validate(
                "confucius",
                [{"id": "引1", "出处": "《论语·卫灵公》", "原文": QUOTE_YI_SUO_BU_YU}],
                [REF_WEILINGGONG],
            )
        )
        assert isinstance(status, str)
        assert len(validated) == 1
        assert validated[0].id == "引1"

    def test_module_singleton_still_exists(self):
        assert isinstance(citation_validator, CitationValidator)

    def test_validator_has_rag_attribute(self):
        assert hasattr(citation_validator, "rag")


class TestCitationValidatorTightened:
    """修复后的判定（A1/A2/B1/C1/C2/C3 在旧调用路径下同样正确）。"""

    def _validate(self, quote, source, refs=None):
        return asyncio.run(citation_validator.validate(
            "confucius",
            [{"id": "引1", "出处": source, "原文": quote}],
            refs if refs is not None else [REF_WEILINGGONG],
        ))

    def test_a1_same_book_wrong_chapter_now_false(self):
        """A1：同书错篇 → 修复后必须为 False（修复前为 True）。"""
        validated, status = self._validate(QUOTE_YI_SUO_BU_YU, "《论语·学而》")
        assert validated[0].verifiable is False
        assert status == "unverified"

    def test_a2_cross_book_wrong_school_now_false(self):
        """A2：跨书错派 → 修复后必须为 False（**修复前实测 True**）。"""
        validated, status = self._validate(QUOTE_YI_SUO_BU_YU, "《孟子·公孙丑上》")
        assert validated[0].verifiable is False, (
            "brief 第十六章第一例：不得因该句存在于《论语》就认可《孟子》为出处"
        )
        assert status == "unverified"

    def test_a2_mencius_rag_refs_path(self):
        """brief 原始复现路径：以 mencius 身份 + 孟子 refs + 论语文本。"""
        mencius_ref = {
            "original": "人皆有不忍人之心。",
            "source": "《孟子·公孙丑上》",
            "chapter": "公孙丑上",
        }
        validated, status = asyncio.run(citation_validator.validate(
            "mencius",
            [{"id": "引1", "出处": "《孟子·公孙丑上》", "原文": QUOTE_YI_SUO_BU_YU}],
            [mencius_ref],
        ))
        assert validated[0].verifiable is False, (
            "论语文本不得被《孟子》refs 验证为可溯源"
        )
        assert status == "unverified"

    def test_b1_two_char_fragment_now_false(self):
        """B1：2 字片段 → 修复后必须为 False（修复前为 True）。"""
        validated, _status = self._validate("君子", "《论语·学而》")
        assert validated[0].verifiable is False

    def test_b1_fragment_rejected_even_with_matching_source(self):
        validated, _status = self._validate("君子", "《论语·卫灵公》")
        assert validated[0].verifiable is False

    def test_c1_fabricated_now_false(self):
        """C1 公平性：纯假古文修复前已拒绝，修复后必须保持。"""
        validated, _status = self._validate(
            "子贡问曰：同事抢功，当何以处之？", "《论语·子贡》",
        )
        assert validated[0].verifiable is False

    def test_c1_embedded_fabrication_now_false(self):
        """T-04：伪造长文内嵌真实短句 → 修复后必须为 False。"""
        fabricated = "网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。"
        validated, _status = self._validate(fabricated, "《论语·卫灵公》")
        assert validated[0].verifiable is False

    def test_c2_traditional_still_matches(self):
        """C2 公平性：繁体不得因收紧而误伤。"""
        validated, status = self._validate("己所不欲，勿施於人。", "《论语·卫灵公》")
        assert validated[0].verifiable is True
        assert status == "all_verified"

    def test_c3_chicken_soup_now_false(self):
        """C3 公平性：网络鸡汤修复前已拒绝，修复后必须保持。"""
        validated, _status = self._validate(
            "你若不勇敢，没人替你坚强。", "《论语·述而》",
        )
        assert validated[0].verifiable is False

    def test_empty_source_not_passed(self):
        """T-05：空出处不得放行（修复前 ``:99-100`` 直接 return True）。"""
        validated, status = self._validate(QUOTE_YI_SUO_BU_YU, "")
        assert validated[0].verifiable is False
        assert status == "unverified"

    def test_valid_citation_still_passes(self):
        """公平性：正确引用不得因收紧而误伤。"""
        validated, status = self._validate(QUOTE_YI_SUO_BU_YU, "《论语·卫灵公》")
        assert validated[0].verifiable is True
        assert status == "all_verified"

    def test_taibo_citation_still_passes(self):
        validated, status = self._validate(
            "士不可以不弘毅，任重而道远。", "《论语·泰伯》", [REF_TAIBO],
        )
        assert validated[0].verifiable is True
        assert status == "all_verified"

    def test_empty_citations_not_all_verified(self):
        """空引用集合不得报 ``all_verified``（修复前 all_verified 初值为 True）。"""
        validated, status = asyncio.run(
            citation_validator.validate("confucius", [], [])
        )
        assert validated == []
        assert status != "all_verified", (
            "空引用集合不得被判为『全部通过』"
        )


# ============================================================
# 4. guard_citations 状态语义
# ============================================================

class TestGuardStatusSemantics:
    def test_all_verified_only_when_every_citation_passes(self):
        guarded, status = guard_citations(
            [
                {"id": "引1", "出处": "《论语·卫灵公》", "原文": QUOTE_YI_SUO_BU_YU},
                {"id": "引2", "出处": "《论语·卫灵公》", "原文": "君子"},
            ],
            rag_refs=[REF_WEILINGGONG],
        )
        assert status == "partial_verified"
        assert guarded[0].verifiable is True
        assert guarded[1].verifiable is False

    def test_unverified_when_nothing_passes(self):
        guarded, status = guard_citations(
            [{"id": "引1", "出处": "《论语·学而》", "原文": "君子"}],
            rag_refs=[REF_WEILINGGONG],
        )
        assert status == "unverified"

    def test_empty_citations_is_unverified(self):
        guarded, status = guard_citations([], rag_refs=[REF_WEILINGGONG])
        assert guarded == []
        assert status == "unverified"

    def test_each_guarded_citation_carries_reason(self):
        guarded, _status = guard_citations(
            [{"id": "引1", "出处": "《论语·学而》", "原文": "君子"}],
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].reason.strip(), "失败必须给出可读原因"

    def test_trust_state_reflects_citation_corrected(self):
        guarded, _status = guard_citations(
            [{"id": "引1", "出处": "《孟子·公孙丑上》", "原文": QUOTE_YI_SUO_BU_YU}],
            rag_refs=[REF_WEILINGGONG],
        )
        assert guarded[0].quote_exists is True
        assert guarded[0].source_correct is False
        assert guarded[0].trust_state == "citation_corrected"

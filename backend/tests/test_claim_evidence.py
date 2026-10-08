"""
悟典 - Claim-Evidence 绑定单元测试（PHASE 5 / PROJECT-BRIEF 第十三章）

覆盖点：
1. claim 抽取是确定性的，且排除转场/免责句式；
2. **不得编造证据**：引用 Pack 之外的 evidence_id 必须 unsupported；
3. 逐字/归一化校验复用 quote_verifier：语料中不存在的引文必须 unsupported；
4. 「文本真但出处假」必须判 partially_supported（对应 citation_corrected），
   且不得被算作 fully supported；
5. 过短片段（如「君子」）不足以支撑思想结论 -> unsupported；
6. 覆盖率定义可自动化复现，且**没有核心 claim 时返回 0.0 而非 1.0**
   （避免空答案拿满分）；
7. 不修改任何 GATE 目标数字。
"""
from __future__ import annotations

import pytest

from app.schemas.knowledge import EvidenceItem, EvidencePack
from app.services.claim_evidence import (
    CLAIM_SUPPORT_STATES,
    Claim,
    bind_claims,
    coverage,
    extract_claims,
    verify_claim,
    verify_claims,
)
from app.services.trust_state import INSUFFICIENT_EVIDENCE_MESSAGE

# --- 真实语料中的条目（已由 quote_verifier 的语料加载器覆盖） ---
REAL_QUOTE = "己所不欲，勿施于人。"
REAL_QUOTE_SOURCE = "《论语·卫灵公》"
REAL_QUOTE_WRONG_SOURCE = "《孟子·公孙丑上》"
# 语料中不存在（论语仅收 107/512 章，此句所在章未收录）
ABSENT_QUOTE = "工欲善其事，必先利其器"


def _pack() -> EvidencePack:
    return EvidencePack(
        query="同事抢了我的功劳，我该不该跟他撕破脸？",
        scenario="workplace_conflict",
        concepts=["义", "礼"],
        evidence=[
            EvidenceItem(
                evidence_id="e1",
                original=REAL_QUOTE,
                source=REAL_QUOTE_SOURCE,
                text_type="original",
                relevance=0.9,
            ),
            EvidenceItem(
                evidence_id="e2",
                original="君子",
                source="《论语·学而》",
                text_type="original",
                relevance=0.5,
            ),
            EvidenceItem(
                evidence_id="e3",
                original=ABSENT_QUOTE,
                source="《论语·卫灵公》",
                text_type="original",
                relevance=0.7,
            ),
        ],
    )


# ============================================================
# 1. claim 抽取
# ============================================================


class TestExtractClaims:
    def test_extracts_sentences_deterministically(self):
        answer = "孔子并不主张无条件忍让。己所不欲勿施于人，是推己及人的底线。"
        claims = extract_claims(answer)
        assert [c.claim_id for c in claims] == ["c1", "c2"]
        # 确定性：同样输入两次结果一致
        assert [c.text for c in extract_claims(answer)] == [c.text for c in claims]

    def test_excludes_disclaimer_and_transition(self):
        answer = (
            "孔子并不主张无条件忍让。"
            "以上为基于经典思想的现代演绎，非历史人物原话。"
            "白话：先分清自己真正想守住的东西。"
        )
        texts = [c.text for c in extract_claims(answer)]
        assert len(texts) == 1
        assert "无条件忍让" in texts[0]

    def test_excludes_insufficient_evidence_notice(self):
        claims = extract_claims(INSUFFICIENT_EVIDENCE_MESSAGE + "。补充说明如下若干内容。")
        assert all(INSUFFICIENT_EVIDENCE_MESSAGE not in c.text for c in claims)

    def test_drops_too_short_sentences(self):
        assert extract_claims("好的。谢谢。") == []

    def test_empty_input(self):
        assert extract_claims("") == []


# ============================================================
# 2. 不得编造证据
# ============================================================


class TestNoFabricatedEvidence:
    def test_evidence_id_not_in_pack_is_unsupported(self):
        claim = Claim(claim_id="c1", text="孔子并不主张无条件忍让。", evidence_ids=("NOT_IN_PACK",))
        result = verify_claim(claim, _pack())
        assert result.support == "unsupported"
        assert result.has_evidence is False
        assert result.bindings[0].in_pack is False

    def test_claim_without_any_evidence_is_unsupported(self):
        claim = Claim(claim_id="c1", text="孔子并不主张无条件忍让。")
        result = verify_claim(claim, _pack())
        assert result.support == "unsupported"
        assert result.message == INSUFFICIENT_EVIDENCE_MESSAGE

    def test_mixed_pack_and_out_of_pack_is_not_supported_by_out_of_pack(self):
        """有一条真证据 + 一条 Pack 外引用 -> 以真证据为准，但不得因越界引用加分。"""
        claim = Claim(claim_id="c1", text="x", evidence_ids=("e1", "NOT_IN_PACK"))
        result = verify_claim(claim, _pack())
        assert result.support == "supported"
        assert any(b.in_pack is False for b in result.bindings)


# ============================================================
# 3. 逐字/归一化校验（复用 quote_verifier）
# ============================================================


class TestQuoteExistence:
    def test_real_quote_with_correct_source_is_supported(self):
        claim = Claim(claim_id="c1", text="x", evidence_ids=("e1",))
        result = verify_claim(claim, _pack())
        assert result.support == "supported"
        assert result.has_evidence is True
        b = result.bindings[0]
        assert b.quote_exists is True
        assert b.source_correct is True

    def test_absent_quote_is_unsupported(self):
        """e3 的引文在语料中不存在 -> 必须 unsupported（不得因"看起来像"放行）。"""
        claim = Claim(claim_id="c1", text="x", evidence_ids=("e3",))
        result = verify_claim(claim, _pack())
        assert result.support == "unsupported"
        assert result.has_evidence is False

    def test_too_short_fragment_is_unsupported(self):
        """「君子」2 字片段不足以支撑思想结论。"""
        claim = Claim(claim_id="c1", text="x", evidence_ids=("e2",))
        result = verify_claim(claim, _pack())
        assert result.support == "unsupported"
        assert result.has_evidence is False
        assert "过短" in result.bindings[0].reason


# ============================================================
# 4. 文本真 / 出处假 -> partially_supported（citation_corrected）
# ============================================================


class TestSourceMismatch:
    def test_real_quote_with_wrong_source_is_partially_supported(self):
        pack = EvidencePack(
            query="q",
            evidence=[
                EvidenceItem(
                    evidence_id="bad",
                    original=REAL_QUOTE,
                    source=REAL_QUOTE_WRONG_SOURCE,
                    text_type="original",
                    relevance=0.8,
                )
            ],
        )
        result = verify_claim(Claim(claim_id="c1", text="x", evidence_ids=("bad",)), pack)
        # 关键：不得算作 supported
        assert result.support == "partially_supported"
        b = result.bindings[0]
        assert b.quote_exists is True
        assert b.source_correct is False
        assert b.correct_source  # 必须给出正确出处
        assert b.trust_state == "citation_corrected"

    def test_partial_does_not_count_as_full_coverage_gap(self):
        """partially_supported 仍计为「有证据」，但不等于 fully supported。"""
        pack = EvidencePack(
            query="q",
            evidence=[
                EvidenceItem(
                    evidence_id="bad",
                    original=REAL_QUOTE,
                    source=REAL_QUOTE_WRONG_SOURCE,
                    text_type="original",
                    relevance=0.8,
                )
            ],
        )
        r = verify_claims([Claim(claim_id="c1", text="x", evidence_ids=("bad",))], pack)
        assert r.results[0].support == "partially_supported"
        assert r.results[0].has_evidence is True


# ============================================================
# 5. 覆盖率定义
# ============================================================


class TestCoverage:
    def test_all_supported_is_one(self):
        claims = [
            Claim(claim_id="c1", text="x", evidence_ids=("e1",)),
            Claim(claim_id="c2", text="y", evidence_ids=("e1",)),
        ]
        assert verify_claims(claims, _pack()).coverage() == pytest.approx(1.0)

    def test_half_supported(self):
        claims = [
            Claim(claim_id="c1", text="x", evidence_ids=("e1",)),
            Claim(claim_id="c2", text="y", evidence_ids=("e3",)),  # 引文不存在
        ]
        assert verify_claims(claims, _pack()).coverage() == pytest.approx(0.5)

    def test_no_core_claims_returns_zero_not_one(self):
        """空答案不得拿满分 —— 分母为 0 时返回 0.0。"""
        assert verify_claims([], _pack()).coverage() == 0.0

    def test_non_core_claims_excluded_from_denominator(self):
        claims = [
            Claim(claim_id="c1", text="x", evidence_ids=("e1",), is_core=True),
            Claim(claim_id="c2", text="y", evidence_ids=(), is_core=False),
        ]
        assert verify_claims(claims, _pack()).coverage() == pytest.approx(1.0)

    def test_bind_claims_without_map_is_conservative(self):
        """未提供结构化引用时，全部按 unsupported 处理（保守且诚实）。"""
        r = bind_claims("孔子并不主张无条件忍让。", _pack())
        assert all(x.support == "unsupported" for x in r.results)
        assert r.coverage() == 0.0

    def test_coverage_helper_matches_verify_claims(self):
        answer = "孔子并不主张无条件忍让。"
        pack = _pack()
        assert coverage(answer, pack, claim_evidence_map={"c1": ["e1"]}) == pytest.approx(
            verify_claims([Claim(claim_id="c1", text=answer, evidence_ids=("e1",))], pack).coverage()
        )


# ============================================================
# 6. 契约与纪律
# ============================================================


class TestContract:
    def test_support_states_are_exactly_three(self):
        assert CLAIM_SUPPORT_STATES == ("supported", "partially_supported", "unsupported")

    def test_unsupported_core_claims_exposed(self):
        r = bind_claims(
            "孔子并不主张无条件忍让。",
            _pack(),
            claim_evidence_map={"c1": ["e3"]},
        )
        assert [x.claim_id for x in r.unsupported_core_claims] == ["c1"]

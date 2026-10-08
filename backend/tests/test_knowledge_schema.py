"""
悟典 - 可信知识库 Schema 单元测试（PHASE 1 / P1-01、P1-06）

覆盖 GATE-1「schema test 全 PASS」。

断言强度要求（``03-task-dag.md`` P1-06）：
**必须覆盖字段缺失 / 非法枚举 / 无来源拒绝，不得仅断言对象可构造。**

测试分四组：
1. 29 字段覆盖（PROJECT-BRIEF 第六章）
2. 正例：合法 Passage / Commentary 可构造
3. 负例：非法输入**必须被拒绝**（本文件的主体）
4. 原典/注疏分离与来源注册表联动
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.knowledge import (
    PASSAGE_FIELDS_29,
    TEXT_TYPES,
    TRUST_STATES,
    VERIFICATION_LEVELS,
    Commentary,
    EvidenceItem,
    EvidencePack,
    Passage,
    QuoteCandidate,
    QuoteVerification,
    SourceRecord,
)
from app.services.source_registry import (
    LevelExceedsSourceError,
    MissingSourceError,
    SourceRegistry,
    SourceRegistryError,
    UnknownProvenanceError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "sources" / "source_registry.json"


# ============================================================
# fixtures：最小合法构造块
# ============================================================

def _provenance_unknown_level_c() -> dict:
    """当前语料唯一诚实的来源组合：显式 unknown 来源 + C 级。"""
    return {
        "source_id": "src_unknown",
        "source_provider": "unknown",
        "source_url": "unknown",
        "source_edition": "unknown",
        "license": "unknown",
        "verification_level": "C",
        "proofread_status": "unproofread",
    }


def make_passage(**overrides) -> dict:
    """构造一个合法的 L1 Passage 参数字典（显式给出全部 29 字段）。"""
    payload = {
        # 身份
        "passage_id": "lunyu:1.1",
        "book_id": "lunyu",
        "book_title": "论语",
        "chapter_id": 1,
        "chapter_title": "学而",
        "section": None,
        "line_no": None,
        # 正文
        "original": "子曰：「学而时习之，不亦说乎？」",
        "original_traditional": None,
        "original_simplified": None,
        # 作者/时代
        "author": "孔子弟子及再传弟子",
        "dynasty": "春秋",
        # 分层
        "text_type": "original",
        # 注疏元信息（L1 不适用，显式 None）
        "commentator": None,
        "commentary_dynasty": None,
        # 学派与概念
        "school": "儒家",
        "concepts": ["学"],
        "modern_topics": [],
        "modern_scenarios": [],
        "stance": None,
        # 来源与复核
        **_provenance_unknown_level_c(),
        # 索引与时间
        "embedding_version": None,
    }
    payload.update(overrides)
    return payload


def make_commentary(**overrides) -> dict:
    """构造一个合法的 L2 Commentary 参数字典（**不含**原典原文副本）。"""
    payload = {
        "commentary_id": "lunyu_zhuxi:1.1",
        "target_passage_id": "lunyu:1.1",
        "commentator": "朱熹",
        "commentary_dynasty": "南宋",
        "commentary_text": "学之为言效也。人性皆善，而觉有先后……",
        "text_type": "commentary",
        **_provenance_unknown_level_c(),
        "embedding_version": None,
    }
    payload.update(overrides)
    return payload


def make_source(**overrides) -> dict:
    payload = {
        "source_id": "src_test",
        "provider": "unknown",
        "url": "unknown",
        "edition": "unknown",
        "license": "unknown",
        "authorization_status": "unverified",
    }
    payload.update(overrides)
    return payload


# ============================================================
# 1. 29 字段覆盖（PROJECT-BRIEF 第六章）
# ============================================================

class TestPassageFieldCoverage:
    """acceptance：Passage 模型覆盖第六章全部 29 字段，缺一不可。"""

    def test_spec_has_exactly_29_fields(self):
        assert len(PASSAGE_FIELDS_29) == 29

    def test_every_brief_field_exists_on_model(self):
        missing = [f for f in PASSAGE_FIELDS_29 if f not in Passage.model_fields]
        assert missing == [], f"Passage 缺少第六章字段: {missing}"

    def test_model_adds_only_documented_extra_fields(self):
        """模型字段 = 29 字段 + 已文档化的额外字段（source_id 与 A 级证据字段）。"""
        extra = set(Passage.model_fields) - set(PASSAGE_FIELDS_29)
        assert extra == {"source_id", "verified_by", "verified_at"}, (
            f"出现未文档化的额外字段: {sorted(extra)}"
        )

    def test_text_type_enum_is_exactly_four_values(self):
        assert TEXT_TYPES == {
            "original", "commentary", "translation", "modern_explanation",
        }

    def test_verification_level_enum_is_exactly_abcd(self):
        assert VERIFICATION_LEVELS == {"A", "B", "C", "D"}

    def test_provenance_fields_are_required_no_defaults(self):
        """来源与复核字段**不允许静默缺省**：必须显式提供。"""
        for field in (
            "source_provider", "source_url", "source_edition", "license",
            "verification_level", "proofread_status", "source_id",
        ):
            assert Passage.model_fields[field].is_required(), (
                f"{field} 有默认值，违反『不允许静默缺省』"
            )
            assert Commentary.model_fields[field].is_required(), (
                f"Commentary.{field} 有默认值，违反『不允许静默缺省』"
            )

    @pytest.mark.parametrize(
        "field",
        ["section", "line_no", "original_traditional", "original_simplified",
         "author", "dynasty", "commentator", "commentary_dynasty", "school",
         "concepts", "modern_topics", "modern_scenarios", "stance",
         "embedding_version"],
    )
    def test_currently_unfillable_fields_require_explicit_value(self, field):
        """语料无法填充的字段必须**显式传 None/[]**，不得靠默认值静默缺省。

        这些字段今天无诚实数据来源（见 docs/kb-v1/audit/p1_01_field_fillability.py）；
        若给它们默认值，"忘记填"与"确实为空"就无法区分。
        """
        assert Passage.model_fields[field].is_required(), (
            f"{field} 不应有默认值：必须显式传 None/[] 以区别于遗漏"
        )
        payload = make_passage()
        del payload[field]
        with pytest.raises(ValidationError):
            Passage(**payload)


# ============================================================
# 2. 正例
# ============================================================

class TestPositiveCases:
    def test_valid_passage_constructs(self):
        passage = Passage(**make_passage())
        assert passage.passage_id == "lunyu:1.1"
        assert passage.text_type == "original"
        assert passage.verification_level == "C"
        assert passage.created_at.tzinfo is not None

    def test_valid_commentary_constructs(self):
        commentary = Commentary(**make_commentary())
        assert commentary.text_type == "commentary"
        assert commentary.target_passage_id == "lunyu:1.1"
        assert commentary.verification_level == "C"

    def test_level_d_allowed_for_ai_explanation(self):
        """D 级（AI 解释）是当前**可诚实赋值**的等级。"""
        passage = Passage(**make_passage(
            passage_id="lunyu:1.1:explain",
            text_type="modern_explanation",
            verification_level="D",
            proofread_status="machine_processed",
        ))
        assert passage.verification_level == "D"

    def test_level_b_allowed_with_known_provenance(self):
        """B 级要求 provider/url/edition 均为已知。"""
        passage = Passage(**make_passage(
            source_provider="example-provider",
            source_url="https://example.org/text",
            source_edition="测试底本",
            license="public-domain",
            verification_level="B",
            proofread_status="machine_processed",
        ))
        assert passage.verification_level == "B"

    def test_level_a_allowed_only_with_human_evidence(self):
        """A 级在**具备人工确认依据**时可构造（当前语料不具备，但模型规则须正确）。"""
        passage = Passage(**make_passage(
            source_provider="example-provider",
            source_url="https://example.org/text",
            source_edition="测试底本",
            license="public-domain",
            verification_level="A",
            proofread_status="human_verified",
            verified_by="human:reviewer-1",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        assert passage.verification_level == "A"


# ============================================================
# 3. 负例：非法输入必须被拒绝
# ============================================================

class TestNegativeMissingProvenance:
    """acceptance：缺 source_provider / 来源字段缺失必须被拒绝。"""

    @pytest.mark.parametrize(
        "field",
        ["source_provider", "source_url", "source_edition", "license",
         "verification_level", "proofread_status", "source_id"],
    )
    def test_passage_missing_provenance_field_rejected(self, field):
        payload = make_passage()
        del payload[field]
        with pytest.raises(ValidationError):
            Passage(**payload)

    @pytest.mark.parametrize(
        "field",
        ["source_provider", "source_url", "source_edition", "license",
         "verification_level", "proofread_status", "source_id"],
    )
    def test_commentary_missing_provenance_field_rejected(self, field):
        payload = make_commentary()
        del payload[field]
        with pytest.raises(ValidationError):
            Commentary(**payload)

    @pytest.mark.parametrize("field", ["source_provider", "source_url", "source_edition", "license"])
    def test_blank_string_rejected(self, field):
        """空白串等同静默缺省，必须拒绝（要求显式写 'unknown'）。"""
        with pytest.raises(ValidationError):
            Passage(**make_passage(**{field: "   "}))

    def test_empty_original_rejected(self):
        with pytest.raises(ValidationError):
            Passage(**make_passage(original=""))


class TestNegativeTextType:
    """acceptance：text_type 非法值必须被拒绝。"""

    @pytest.mark.parametrize(
        "bad", ["Original", "ORIGINAL", "verse", "commentaries", "", "原文", None],
    )
    def test_invalid_text_type_rejected(self, bad):
        with pytest.raises(ValidationError):
            Passage(**make_passage(text_type=bad))

    def test_commentary_text_type_not_allowed_in_passage(self):
        """注疏必须走 Commentary，不得塞进 L1 Passage。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(text_type="commentary"))
        assert "commentary" in str(exc.value)

    def test_commentary_model_rejects_other_text_type(self):
        with pytest.raises(ValidationError):
            Commentary(**make_commentary(text_type="original"))

    def test_all_four_text_types_are_accepted_by_some_model(self):
        """四值各自有合法归属：commentary 归 L2，其余归 L1。"""
        Commentary(**make_commentary(text_type="commentary"))
        for tt in ("original", "translation", "modern_explanation"):
            level = "D" if tt != "original" else "C"
            Passage(**make_passage(text_type=tt, verification_level=level))


class TestNegativeVerificationLevel:
    """acceptance：verification_level=A 无复核依据必须被拒绝。"""

    def test_invalid_level_rejected(self):
        for bad in ("a", "E", "AB", "", "1", None):
            with pytest.raises(ValidationError):
                Passage(**make_passage(verification_level=bad))

    def test_level_a_without_human_verified_rejected(self):
        """A 级但 proofread_status 非 human_verified → 拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(
                source_provider="p", source_url="https://e.org", source_edition="ed",
                license="public-domain",
                verification_level="A", proofread_status="unproofread",
            ))
        assert "human_verified" in str(exc.value)

    def test_level_a_without_verified_by_rejected(self):
        """A 级但无人工确认者 → 拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(
                source_provider="p", source_url="https://e.org", source_edition="ed",
                license="public-domain",
                verification_level="A", proofread_status="human_verified",
                verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ))
        assert "verified_by" in str(exc.value)

    def test_level_a_without_verified_at_rejected(self):
        """A 级但无人工确认时间 → 拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(
                source_provider="p", source_url="https://e.org", source_edition="ed",
                license="public-domain",
                verification_level="A", proofread_status="human_verified",
                verified_by="human:reviewer-1",
            ))
        assert "verified_at" in str(exc.value)

    def test_level_a_with_unknown_license_rejected(self):
        """A 级但授权未知 → 拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(
                source_provider="p", source_url="https://e.org", source_edition="ed",
                license="unknown",
                verification_level="A", proofread_status="human_verified",
                verified_by="human:reviewer-1",
                verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ))
        assert "license" in str(exc.value)

    def test_level_b_with_unknown_source_rejected(self):
        """B 级要求权威来源；来源字段为 unknown → 拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(
                source_provider="unknown", source_url="unknown", source_edition="unknown",
                verification_level="B", proofread_status="machine_processed",
            ))
        assert "B" in str(exc.value)

    def test_level_a_requires_evidence_on_commentary_too(self):
        with pytest.raises(ValidationError):
            Commentary(**make_commentary(
                source_provider="p", source_url="https://e.org", source_edition="ed",
                license="public-domain", verification_level="A",
                proofread_status="machine_processed",
            ))

    def test_current_corpus_cannot_be_marked_a(self):
        """回归：现有语料（unknown 来源 + 无复核）不得标 A。"""
        with pytest.raises(ValidationError):
            Passage(**make_passage(verification_level="A"))


class TestNegativeLayerSeparation:
    """acceptance：注疏不得内嵌原典原文副本。"""

    def test_commentary_rejects_embedded_original(self):
        """``original`` 是现状 13/15 重复存储的字段名 → 必须拒绝。"""
        with pytest.raises(ValidationError) as exc:
            Commentary(**make_commentary(original="子曰：「学而时习之……」"))
        assert "original" in str(exc.value)

    @pytest.mark.parametrize("field", ["original", "original_text", "original_traditional", "original_simplified"])
    def test_commentary_rejects_any_embedded_original_variant(self, field):
        with pytest.raises(ValidationError):
            Commentary(**make_commentary(**{field: "任何原文副本"}))

    def test_commentary_rejects_unknown_extra_fields(self):
        with pytest.raises(ValidationError):
            Commentary(**make_commentary(book_title="论语"))

    def test_passage_rejects_unknown_extra_fields(self):
        with pytest.raises(ValidationError):
            Passage(**make_passage(verse_no=1))

    def test_commentary_requires_target_passage_id(self):
        payload = make_commentary()
        del payload["target_passage_id"]
        with pytest.raises(ValidationError):
            Commentary(**payload)


class TestNegativeAiAsCanonical:
    """禁止把 AI 生成文本当作权威原典。"""

    def test_original_cannot_be_level_d(self):
        with pytest.raises(ValidationError) as exc:
            Passage(**make_passage(text_type="original", verification_level="D"))
        assert "AI" in str(exc.value) or "D" in str(exc.value)

    def test_level_d_only_for_derived_content(self):
        """D 级不得用于 original/commentary。"""
        with pytest.raises(ValidationError):
            Passage(**make_passage(
                text_type="original", verification_level="D",
            ))
        with pytest.raises(ValidationError):
            Commentary(**make_commentary(verification_level="D"))


# ============================================================
# 4. 来源注册表
# ============================================================

class TestSourceRecord:
    def test_valid_unknown_source(self):
        record = SourceRecord(**make_source())
        assert record.authorization_status == "unverified"
        assert record.has_known_provenance is False
        assert record.max_verification_level == "C"

    def test_blank_fields_rejected(self):
        for field in ("provider", "url", "edition", "license"):
            with pytest.raises(ValidationError):
                SourceRecord(**make_source(**{field: ""}))

    def test_authorized_without_evidence_rejected(self):
        """编造授权必须被拒绝：authorized 需附证据。"""
        with pytest.raises(ValidationError) as exc:
            SourceRecord(**make_source(
                provider="p", url="https://e.org", edition="ed", license="public-domain",
                authorization_status="authorized",
            ))
        assert "证据" in str(exc.value) or "authorized" in str(exc.value)

    def test_authorized_with_evidence_accepted(self):
        record = SourceRecord(**make_source(
            provider="p", url="https://e.org", edition="ed", license="public-domain",
            authorization_status="authorized",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            evidence_ref="docs/kb-v1/audit/classical-knowledge.md#3.5",
        ))
        assert record.max_verification_level == "A"

    def test_known_provenance_without_authorization_caps_at_b(self):
        record = SourceRecord(**make_source(
            provider="p", url="https://e.org", edition="ed", license="public-domain",
            authorization_status="unverified",
        ))
        assert record.max_verification_level == "B"


class TestSourceRegistry:
    @pytest.fixture(scope="class")
    @classmethod
    def registry(cls):
        return SourceRegistry.load(REGISTRY_PATH)

    def test_registry_file_exists_and_loads(self, registry):
        assert REGISTRY_PATH.exists()
        assert len(registry) >= 1
        assert "src_unknown" in registry

    def test_registry_declares_no_verified_sources_yet(self, registry):
        """诚实性断言：当前没有任何已核验授权的来源。"""
        assert registry.verified_source_count == 0

    def test_registry_lists_pending_verification(self, registry):
        """未核验项必须显式登记，不得隐藏。"""
        pending = registry.pending_verification
        assert len(pending) >= 1
        assert all(item.get("status") == "unverified" for item in pending)

    def test_registry_json_is_parseable_and_has_no_placeholder_fakes(self):
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for entry in raw["sources"]:
            assert entry["source_id"], "来源条目缺少 source_id"
            # 禁止空串占位（真实未知必须显式写 'unknown'）
            for field in ("provider", "url", "edition", "license"):
                assert entry[field].strip(), f"{entry['source_id']}.{field} 为空串"
            # 未授权条目不得声称已核验
            if entry["authorization_status"] != "authorized":
                assert entry["verified_at"] is None, (
                    f"{entry['source_id']} 未授权却有 verified_at，涉嫌编造核验"
                )

    def test_missing_source_id_raises(self, registry):
        with pytest.raises(MissingSourceError):
            registry.get("src_does_not_exist")

    def test_no_implicit_fallback_for_missing_source(self, registry):
        """禁止隐式兜底：未知 source_id 必须报错而非返回默认来源。"""
        assert registry.try_get("src_does_not_exist") is None
        with pytest.raises(MissingSourceError):
            registry.assert_source_usable("src_nope")

    def test_passage_with_unknown_source_level_c_passes(self, registry):
        passage = Passage(**make_passage())
        record = registry.assert_passage_source(passage)
        assert record.source_id == "src_unknown"

    def test_passage_claiming_b_on_unknown_source_rejected(self, registry):
        """模型层允许 B（有已知来源时），但注册表层发现来源未知 → 拒绝。"""
        passage = Passage(**make_passage(
            source_provider="p", source_url="https://e.org", source_edition="ed",
            verification_level="B", proofread_status="machine_processed",
        ))
        with pytest.raises(UnknownProvenanceError):
            registry.assert_passage_source(passage)

    def test_passage_claiming_a_without_authorized_source_rejected(self, registry):
        passage = Passage(**make_passage(
            source_provider="p", source_url="https://e.org", source_edition="ed",
            license="public-domain",
            verification_level="A", proofread_status="human_verified",
            verified_by="human:reviewer-1",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        with pytest.raises((UnknownProvenanceError, LevelExceedsSourceError)):
            registry.assert_passage_source(passage)

    def test_validate_batch_collects_all_problems(self, registry):
        """批量校验必须收集全部问题，不得静默丢弃。"""
        good = Passage(**make_passage())
        bad = Passage(**make_passage(
            passage_id="lunyu:9.9",
            source_provider="p", source_url="https://e.org", source_edition="ed",
            verification_level="B", proofread_status="machine_processed",
        ))
        problems = registry.validate_batch([good, bad])
        assert len(problems) == 1
        assert "lunyu:9.9" in problems[0]

    def test_registry_rejects_entry_with_blank_field(self, tmp_path):
        """注册表文件含空白字段 → 加载失败（拒绝静默跳过）。"""
        bad_file = tmp_path / "bad_registry.json"
        bad_file.write_text(json.dumps({
            "sources": [{
                "source_id": "src_bad", "provider": "", "url": "u",
                "edition": "e", "license": "l", "authorization_status": "unverified",
            }],
        }, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(SourceRegistryError):
            SourceRegistry.load(bad_file)

    def test_registry_rejects_duplicate_source_id(self, tmp_path):
        entry = make_source(source_id="src_dup")
        dup_file = tmp_path / "dup_registry.json"
        dup_file.write_text(json.dumps({"sources": [entry, dict(entry)]}, ensure_ascii=False),
                            encoding="utf-8")
        with pytest.raises(SourceRegistryError) as exc:
            SourceRegistry.load(dup_file)
        assert "重复" in str(exc.value)

    def test_registry_rejects_empty_sources_list(self, tmp_path):
        empty_file = tmp_path / "empty_registry.json"
        empty_file.write_text(json.dumps({"sources": []}), encoding="utf-8")
        with pytest.raises(SourceRegistryError):
            SourceRegistry.load(empty_file)

    def test_commentary_source_checked_too(self, registry):
        commentary = Commentary(**make_commentary())
        record = registry.assert_commentary_source(commentary)
        assert record.source_id == "src_unknown"


# ============================================================
# 5. EvidencePack / QuoteVerification（PHASE 4/5 契约冻结）
# ============================================================

class TestEvidenceAndQuoteContracts:
    def test_evidence_pack_constructs(self):
        pack = EvidencePack(
            query="同事抢功该怎么办",
            scenario="workplace_conflict",
            concepts=["义", "礼"],
            evidence=[EvidenceItem(
                evidence_id="ev1", original="己所不欲，勿施于人。",
                source="《论语·颜渊》", school="儒家", text_type="original",
                relevance=0.9,
            )],
        )
        assert pack.evidence[0].text_type == "original"

    def test_evidence_relevance_bounds_enforced(self):
        with pytest.raises(ValidationError):
            EvidenceItem(
                evidence_id="ev1", original="x", source="s", text_type="original",
                relevance=1.5,
            )

    def test_trust_states_are_exactly_four(self):
        assert TRUST_STATES == {
            "verified", "citation_corrected", "quote_relaxed", "insufficient_evidence",
        }

    def test_verified_requires_both_true(self):
        with pytest.raises(ValidationError):
            QuoteVerification(
                quote_exists=True, exact_match=True, normalized_match=True,
                source_correct=False, similarity=1.0, match_type="exact",
                trust_state="verified",
            )

    def test_citation_corrected_requires_correct_source(self):
        with pytest.raises(ValidationError) as exc:
            QuoteVerification(
                quote_exists=True, exact_match=True, normalized_match=True,
                source_correct=False, similarity=1.0, match_type="exact",
                trust_state="citation_corrected", correct_source=None,
            )
        assert "correct_source" in str(exc.value)

    def test_citation_corrected_accepted_with_correct_source(self):
        result = QuoteVerification(
            quote_exists=True, exact_match=True, normalized_match=True,
            source_correct=False, correct_source="《论语·颜渊》",
            similarity=1.0, match_type="exact", trust_state="citation_corrected",
            candidates=[QuoteCandidate(
                passage_id="lunyu:12.2", source="《论语·颜渊》",
                text_type="original", similarity=1.0,
            )],
        )
        assert result.trust_state == "citation_corrected"

    def test_insufficient_evidence_requires_quote_absent(self):
        with pytest.raises(ValidationError):
            QuoteVerification(
                quote_exists=True, exact_match=False, normalized_match=False,
                source_correct=False, similarity=0.0, match_type="none",
                trust_state="insufficient_evidence",
            )

    def test_insufficient_evidence_accepted_when_absent(self):
        result = QuoteVerification(
            quote_exists=False, exact_match=False, normalized_match=False,
            source_correct=False, similarity=0.0, match_type="none",
            trust_state="insufficient_evidence",
        )
        assert result.quote_exists is False

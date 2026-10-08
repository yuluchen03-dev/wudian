"""
悟典 - ingestion pipeline 单元测试（PHASE 1 / P1-03、P1-06）

覆盖 GATE-1「fixture 数据可 ingest」。

断言强度（``03-task-dag.md`` P1-06）：必须覆盖
**字段缺失 / 非法枚举 / 无来源拒绝**，不得仅断言对象可构造。

本测试**不使用 mock 代替真实入库**：每条正例都通过 SQLAlchemy 异步会话
真正写进表，再从表里读回来断言。使用临时 SQLite 文件，不触碰生产库。
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.knowledge import KnowledgeCommentary, KnowledgePassage
from app.services.ingestion import (
    IngestionError,
    IngestionReport,
    assert_no_high_level_ingested,
    ingest_bundle,
    ingest_commentaries,
    ingest_fixture_file,
    ingest_passages,
    level_distribution_is_within,
    load_fixture,
)
from app.services.source_registry import (
    MissingSourceError,
    SourceRegistry,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
FIXTURE_PATH = BACKEND_DIR / "data" / "knowledge" / "lunyu_fixture.json"
REGISTRY_PATH = REPO_ROOT / "data" / "sources" / "source_registry.json"


# ============================================================
# 测试基础设施：独立临时 SQLite（不碰 test_wudian.db / 生产库）
# ============================================================

def _make_engine(tmp_path: Path):
    db_file = tmp_path / "ingest_test.db"
    return create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}")


async def _create_tables(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(KnowledgePassage.metadata.create_all)


def _run(coro_fn, tmp_path: Path):
    """在独立事件循环里建库 -> 执行 -> 释放。"""

    async def _main():
        engine = _make_engine(tmp_path)
        try:
            await _create_tables(engine)
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                result = await coro_fn(session)
                await session.commit()
                return result
        finally:
            await engine.dispose()

    return asyncio.run(_main())


# ============================================================
# fixtures：最小合法/非法构造块（与 t18 契约一致）
# ============================================================

def provenance_c() -> dict:
    """当前唯一诚实的来源组合：显式 unknown + C 级。"""
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
    payload = {
        "passage_id": "lunyu:1.1",
        "book_id": "lunyu",
        "book_title": "论语",
        "chapter_id": 1,
        "chapter_title": "学而",
        "section": None,
        "line_no": None,
        "original": "子曰：「学而时习之，不亦说乎？」",
        "original_traditional": None,
        "original_simplified": None,
        "author": "孔子弟子及再传弟子",
        "dynasty": "春秋",
        "text_type": "original",
        "commentator": None,
        "commentary_dynasty": None,
        "school": "儒家",
        "concepts": ["学"],
        "modern_topics": [],
        "modern_scenarios": [],
        "stance": None,
        **provenance_c(),
        "embedding_version": None,
    }
    payload.update(overrides)
    return payload


def make_commentary(**overrides) -> dict:
    payload = {
        "commentary_id": "lunyu_zhuxi:1.1",
        "target_passage_id": "lunyu:1.1",
        "commentator": "朱熹",
        "commentary_dynasty": "南宋",
        "commentary_text": "学之为言效也。人性皆善，而觉有先后……",
        "text_type": "commentary",
        **provenance_c(),
        "embedding_version": None,
    }
    payload.update(overrides)
    return payload


# ============================================================
# 1. 正例：真实入库并可读回
# ============================================================

class TestPositiveIngestion:
    def test_passage_ingested_and_read_back(self, tmp_path):
        """正例：合法 passage 真正写库并可读回（非 mock）。"""
        async def _flow(session):
            report = await ingest_passages(session, [make_passage()])
            return report

        report = _run(_flow, tmp_path)
        assert report.passages_written == 1
        assert report.total_rejected == 0

        async def _read(session):
            return await session.get(KnowledgePassage, "lunyu:1.1")

        row = _run(_read, tmp_path)
        assert row is not None
        assert row.book_id == "lunyu"
        assert row.text_type == "original"
        assert row.verification_level == "C"
        assert row.source_id == "src_unknown"
        # chapter_id 在 DB 侧统一为字符串
        assert row.chapter_id == "1"

    def test_commentary_ingested_with_foreign_key(self, tmp_path):
        """正例：注疏经外键引用 L1，且不内嵌原文副本。"""
        async def _flow(session):
            return await ingest_bundle(
                session,
                passages=[make_passage()],
                commentaries=[make_commentary()],
            )

        report = _run(_flow, tmp_path)
        assert report.passages_written == 1
        assert report.commentaries_written == 1
        assert report.total_rejected == 0

        async def _read(session):
            return await session.get(KnowledgeCommentary, "lunyu_zhuxi:1.1")

        row = _run(_read, tmp_path)
        assert row is not None
        assert row.target_passage_id == "lunyu:1.1"
        assert row.commentator == "朱熹"
        assert row.verification_level == "C"
        # 表结构上不存在原文列
        assert not hasattr(row, "original")
        assert not hasattr(row, "original_text")

    def test_real_fixture_file_ingests_cleanly(self, tmp_path):
        """GATE-1 核心：仓库内 fixture 文件真实可 ingest。"""
        assert FIXTURE_PATH.exists(), f"fixture 缺失: {FIXTURE_PATH}"

        async def _flow(session):
            return await ingest_fixture_file(session, FIXTURE_PATH)

        report = _run(_flow, tmp_path)
        assert report.passages_written == 5
        assert report.commentaries_written == 5
        assert report.total_rejected == 0, report.rejected

        async def _count(session):
            p = await session.scalar(select(func.count()).select_from(KnowledgePassage))
            c = await session.scalar(select(func.count()).select_from(KnowledgeCommentary))
            return p, c

        passages, commentaries = _run(_count, tmp_path)
        assert passages == 5
        assert commentaries == 5

    def test_ingestion_is_idempotent_upsert(self, tmp_path):
        """重复 ingest 同一 passage 应更新而非重复插入。"""
        async def _flow(session):
            first = await ingest_passages(session, [make_passage()])
            second = await ingest_passages(
                session, [make_passage(original="子曰：「学而时习之。」")]
            )
            return first, second

        first, second = _run(_flow, tmp_path)
        assert first.passages_written == 1
        assert second.passages_updated == 1
        assert second.passages_written == 0

        async def _count(session):
            return await session.scalar(select(func.count()).select_from(KnowledgePassage))

        assert _run(_count, tmp_path) == 1

    def test_ai_explanation_allowed_as_level_d(self, tmp_path):
        """D 级（AI 解释）是当前可诚实赋值的等级之一。"""
        async def _flow(session):
            return await ingest_passages(session, [make_passage(
                passage_id="lunyu:1.1:explain",
                text_type="modern_explanation",
                verification_level="D",
                proofread_status="machine_processed",
            )])

        report = _run(_flow, tmp_path)
        assert report.passages_written == 1
        assert report.level_distribution.get("D") == 1


# ============================================================
# 2. 负例：来源缺失 / 未登记 → 必须被拒绝
# ============================================================

class TestNegativeSourceRejection:
    @pytest.mark.parametrize(
        "field",
        ["source_id", "source_provider", "source_url", "source_edition",
         "license", "verification_level", "proofread_status"],
    )
    def test_missing_source_field_rejected_not_silently_dropped(self, tmp_path, field):
        """缺任一来来源/复核字段 → 拒绝并**记入拒绝清单**，不得静默丢弃。"""
        payload = make_passage()
        del payload[field]

        async def _flow(session):
            return await ingest_passages(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.passages_written == 0
        assert report.total_rejected == 1
        assert field in report.rejected[0].reason or "schema" in report.rejected[0].reason
        assert report.rejected[0].identifier == "lunyu:1.1"

        async def _count(session):
            return await session.scalar(select(func.count()).select_from(KnowledgePassage))

        assert _run(_count, tmp_path) == 0

    def test_unregistered_source_id_rejected(self, tmp_path):
        """source_id 未在 registry 登记 → 拒绝，无隐式兜底。"""
        async def _flow(session):
            return await ingest_passages(
                session, [make_passage(source_id="src_does_not_exist")]
            )

        report = _run(_flow, tmp_path)
        assert report.passages_written == 0
        assert report.total_rejected == 1
        assert "来源校验失败" in report.rejected[0].reason

        async def _count(session):
            return await session.scalar(select(func.count()).select_from(KnowledgePassage))

        assert _run(_count, tmp_path) == 0

    def test_blank_source_field_rejected(self, tmp_path):
        """空白串等同静默缺省 → 拒绝（须显式写 'unknown'）。"""
        async def _flow(session):
            return await ingest_passages(session, [make_passage(source_provider="   ")])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1
        assert report.passages_written == 0

    def test_commentary_missing_source_rejected(self, tmp_path):
        payload = make_commentary()
        del payload["source_provider"]

        async def _flow(session):
            return await ingest_bundle(session, commentaries=[payload])

        report = _run(_flow, tmp_path)
        assert report.commentaries_written == 0
        assert report.total_rejected == 1

    def test_registry_rejects_unknown_source_id_directly(self):
        """SourceRegistry 本身不提供隐式兜底。"""
        registry = SourceRegistry.load(REGISTRY_PATH)
        with pytest.raises(MissingSourceError):
            registry.get("src_nope")


# ============================================================
# 3. 负例：注疏内嵌原文副本 → 必须被拒绝
# ============================================================

class TestNegativeEmbeddedOriginal:
    def test_commentary_with_embedded_original_rejected(self, tmp_path):
        """现状 13/15 重复存储的字段名 → ingestion 必须拒绝。"""
        payload = make_commentary()
        payload["original"] = "子曰：「学而时习之，不亦说乎？」"

        async def _flow(session):
            return await ingest_commentaries(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.commentaries_written == 0
        assert report.total_rejected == 1
        assert "original" in report.rejected[0].reason

        async def _count(session):
            return await session.scalar(select(func.count()).select_from(KnowledgeCommentary))

        assert _run(_count, tmp_path) == 0

    @pytest.mark.parametrize(
        "field", ["original", "original_text", "original_traditional", "original_simplified"],
    )
    def test_any_original_variant_rejected(self, tmp_path, field):
        payload = make_commentary()
        payload[field] = "任何原文副本"

        async def _flow(session):
            return await ingest_commentaries(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1
        assert report.commentaries_written == 0

    def test_l2_table_has_no_original_column(self):
        """DDL 层证据：L2 表结构上不存在原文列。"""
        cols = set(KnowledgeCommentary.__table__.columns.keys())
        assert "original" not in cols
        assert "original_text" not in cols
        assert "original_traditional" not in cols
        assert "original_simplified" not in cols
        assert "target_passage_id" in cols

    def test_l1_and_l2_are_separate_tables(self):
        """L1/L2 物理分离。"""
        assert KnowledgePassage.__tablename__ == "knowledge_passage"
        assert KnowledgeCommentary.__tablename__ == "knowledge_commentary"
        assert KnowledgePassage.__tablename__ != KnowledgeCommentary.__tablename__

    def test_commentary_referencing_missing_passage_rejected(self, tmp_path):
        """悬空注疏必须被拒（外键完整性）。"""
        async def _flow(session):
            return await ingest_commentaries(session, [make_commentary()])

        report = _run(_flow, tmp_path)
        assert report.commentaries_written == 0
        assert report.total_rejected == 1
        assert "不存在" in report.rejected[0].reason


# ============================================================
# 4. 负例：verification_level=A 无人工依据 → 必须被拒绝
# ============================================================

class TestNegativeLevelA:
    def test_level_a_without_human_evidence_rejected(self, tmp_path):
        """A 级无人工确认依据 → 拒绝（当前零人工复核）。"""
        payload = make_passage(verification_level="A")

        async def _flow(session):
            return await ingest_passages(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.passages_written == 0
        assert report.total_rejected == 1

        async def _count(session):
            return await session.scalar(select(func.count()).select_from(KnowledgePassage))

        assert _run(_count, tmp_path) == 0

    def test_level_a_with_partial_evidence_rejected(self, tmp_path):
        """A 级缺 verified_by/verified_at 之一 → 拒绝。"""
        payload = make_passage(
            source_provider="p", source_url="https://e.org", source_edition="ed",
            license="public-domain",
            verification_level="A", proofread_status="human_verified",
        )

        async def _flow(session):
            return await ingest_passages(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1

    def test_level_b_with_unknown_source_rejected(self, tmp_path):
        """B 级但来源为 unknown → 注册表上限 C，拒绝。"""
        payload = make_passage(
            source_provider="p", source_url="https://e.org", source_edition="ed",
            verification_level="B", proofread_status="machine_processed",
        )

        async def _flow(session):
            return await ingest_passages(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.passages_written == 0
        assert report.total_rejected == 1

    def test_commentary_level_a_without_evidence_rejected(self, tmp_path):
        payload = make_commentary(
            source_provider="p", source_url="https://e.org", source_edition="ed",
            license="public-domain", verification_level="A",
            proofread_status="machine_processed",
        )

        async def _flow(session):
            return await ingest_bundle(
                session, passages=[make_passage()], commentaries=[payload],
            )

        report = _run(_flow, tmp_path)
        assert report.commentaries_written == 0
        assert report.total_rejected == 1

    def test_commentary_level_d_rejected(self, tmp_path):
        """D 级 = AI 解释，不得冒充历代注疏。"""
        payload = make_commentary(
            verification_level="D", proofread_status="machine_processed",
        )

        async def _flow(session):
            return await ingest_bundle(
                session, passages=[make_passage()], commentaries=[payload],
            )

        report = _run(_flow, tmp_path)
        assert report.commentaries_written == 0
        assert report.total_rejected == 1


# ============================================================
# 5. 负例：分层与枚举
# ============================================================

class TestNegativeLayerAndEnum:
    def test_invalid_text_type_rejected(self, tmp_path):
        async def _flow(session):
            return await ingest_passages(session, [make_passage(text_type="verse")])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1
        assert report.passages_written == 0

    def test_commentary_text_type_in_l1_rejected(self, tmp_path):
        """注疏不得进 L1 表。"""
        async def _flow(session):
            return await ingest_passages(session, [make_passage(text_type="commentary")])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1

    def test_original_with_level_d_rejected(self, tmp_path):
        """禁止把 AI 生成文本当作权威原典。"""
        async def _flow(session):
            return await ingest_passages(session, [make_passage(verification_level="D")])

        report = _run(_flow, tmp_path)
        assert report.passages_written == 0
        assert report.total_rejected == 1

    def test_unknown_extra_field_rejected(self, tmp_path):
        payload = make_passage(verse_no=1)

        async def _flow(session):
            return await ingest_passages(session, [payload])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 1


# ============================================================
# 6. 等级分布：证明无 A/B
# ============================================================

class TestLevelDistribution:
    def test_ingested_levels_only_c_or_d(self, tmp_path):
        """GATE-1：入库条目等级只能是 C/D，不得出现 A/B。"""
        async def _flow(session):
            report = await ingest_bundle(
                session,
                passages=[
                    make_passage(),
                    make_passage(
                        passage_id="lunyu:1.1:explain",
                        text_type="modern_explanation",
                        verification_level="D",
                        proofread_status="machine_processed",
                    ),
                ],
                commentaries=[make_commentary()],
            )
            dist = await assert_no_high_level_ingested(session)
            return report, dist

        report, dist = _run(_flow, tmp_path)
        assert report.total_rejected == 0
        assert set(dist) <= {"C", "D"}, dist
        assert "A" not in dist and "B" not in dist
        assert dist.get("C") == 2
        assert dist.get("D") == 1

    def test_level_distribution_helper(self):
        assert level_distribution_is_within(["C", "D"]) is True
        assert level_distribution_is_within(["C"]) is True
        assert level_distribution_is_within(["C", "A"]) is False
        assert level_distribution_is_within(["B"]) is False

    def test_registry_has_no_verified_source_yet(self):
        """诚实性断言：当前零已核验来源，故 A/B 不可达。"""
        registry = SourceRegistry.load(REGISTRY_PATH)
        assert registry.verified_source_count == 0

    def test_assert_no_high_level_raises_when_violation_exists(self, tmp_path):
        """若库中出现 A/B，检查函数必须报错而非放行。

        注意：为了让本用例真正**到达** `assert_no_high_level_ingested`，
        写入的 A 级行必须**先满足**表上的 CHECK 约束
        `ck_kp_level_a_requires_human_evidence`（即 A 级要求
        proofread_status='human_verified' 且 verified_by/verified_at 均非空）。
        早期版本把 verified_at 设为 None，导致行在 flush 阶段就被 CHECK 拒绝，
        抛的是 IntegrityError 而非 IngestionError —— 那样测的是约束、不是审计函数。
        因此这里补齐 verified_at，使该行能合法落库，
        再验证审计函数确实会因「存在 A 级」而报错。
        """
        from datetime import datetime, timezone

        async def _flow(session):
            # 绕过 ingestion 直接写入一条 A 级（模拟数据被外部污染）
            session.add(KnowledgePassage(
                passage_id="bad:A",
                book_id="lunyu", book_title="论语", chapter_id="1", chapter_title="学而",
                section=None, line_no=None, original="x",
                original_traditional=None, original_simplified=None,
                author=None, dynasty=None, text_type="original",
                commentator=None, commentary_dynasty=None, school=None,
                concepts=[], modern_topics=[], modern_scenarios=[], stance=None,
                source_id="src_unknown", source_provider="unknown",
                source_url="unknown", source_edition="unknown", license="unknown",
                verification_level="A", proofread_status="human_verified",
                verified_by="human:someone",
                verified_at=datetime.now(timezone.utc),
                embedding_version=None,
            ))
            await session.flush()
            return await assert_no_high_level_ingested(session)

        with pytest.raises(IngestionError):
            _run(_flow, tmp_path)


# ============================================================
# 7. fixture 装载与安全性
# ============================================================

class TestFixtureLoading:
    def test_fixture_file_exists_and_parses(self):
        passages, commentaries = load_fixture(FIXTURE_PATH)
        assert len(passages) == 5
        assert len(commentaries) == 5

    def test_fixture_is_marked_as_fixture(self):
        """fixture 必须自述为 fixture，不得冒充权威原典。"""
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        notice = raw.get("_fixture_notice", "")
        assert notice, "fixture 缺少 _fixture_notice 标注"
        assert "FIXTURE" in notice
        assert "严禁" in notice

    def test_fixture_commentaries_have_no_embedded_original(self):
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for c in raw["commentaries"]:
            for key in c:
                assert not key.startswith("original"), (
                    f"fixture 注疏 {c.get('commentary_id')} 内嵌了原文副本字段 {key}"
                )

    def test_fixture_text_is_byte_identical_to_source_corpus(self):
        """fixture 文本必须逐字取自真实语料，不得改写或生成。"""
        lunyu = json.loads(
            (REPO_ROOT / "data" / "processed" / "lunyu.json").read_text(encoding="utf-8")
        )
        comm = json.loads(
            (BACKEND_DIR / "data" / "commentaries" / "lunyu_zhuxi.json")
            .read_text(encoding="utf-8")
        )
        src_v = {
            f"lunyu:{v['verse_id']}": v["original"]
            for ch in lunyu["chapters"] for v in ch["verses"]
        }
        src_c = {
            f"lunyu_zhuxi:{c['verse_id']}": c["commentary"]
            for c in comm["commentaries"]
        }
        passages, commentaries = load_fixture(FIXTURE_PATH)
        for p in passages:
            assert p["original"] == src_v[p["passage_id"]], p["passage_id"]
        for c in commentaries:
            assert c["commentary_text"] == src_c[c["commentary_id"]], c["commentary_id"]

    def test_fixture_levels_and_sources_are_conservative(self):
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for p in raw["passages"] + raw["commentaries"]:
            assert p["verification_level"] in ("C", "D"), p
            assert p["source_id"] == "src_unknown", p

    def test_missing_fixture_file_raises(self, tmp_path):
        with pytest.raises(IngestionError):
            load_fixture(tmp_path / "nope.json")

    def test_malformed_fixture_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with pytest.raises(IngestionError):
            load_fixture(bad)

    def test_fixture_with_wrong_shape_raises(self, tmp_path):
        bad = tmp_path / "wrong.json"
        bad.write_text(json.dumps({"passages": "not-a-list"}), encoding="utf-8")
        with pytest.raises(IngestionError):
            load_fixture(bad)


# ============================================================
# 8. 报告结构
# ============================================================

class TestReport:
    def test_report_collects_multiple_rejections(self, tmp_path):
        """多个非法条目 → 全部进拒绝清单（不因首个错误而中断）。"""
        bad1 = make_passage(passage_id="lunyu:9.1")
        del bad1["source_provider"]
        bad2 = make_passage(passage_id="lunyu:9.2", text_type="bogus")

        async def _flow(session):
            return await ingest_passages(session, [bad1, bad2])

        report = _run(_flow, tmp_path)
        assert report.total_rejected == 2
        assert report.passages_written == 0
        ids = {r.identifier for r in report.rejected}
        assert ids == {"lunyu:9.1", "lunyu:9.2"}

    def test_report_ok_flag(self):
        clean = IngestionReport(passages_written=1)
        assert clean.ok is True
        dirty = IngestionReport()
        dirty.reject(0, "passage", "x", "reason")
        assert dirty.ok is False

    def test_report_summary_is_informative(self):
        report = IngestionReport(passages_written=2)
        report.note_level("C")
        text = report.summary()
        assert "passages=2" in text
        assert "levels=" in text

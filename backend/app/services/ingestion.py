"""
悟典 - 校验式 ingestion pipeline（PHASE 1 / P1-03）

职责
----
把符合 ``schemas/knowledge.py`` 契约的 JSON 记录导入 L1 ``knowledge_passage``
与 L2 ``knowledge_commentary``。**强制来源校验**：任何无 ``source_id``、
``source_id`` 未在 registry 登记、或 ``verification_level`` 超出该来源允许上限
的条目都会被**拒绝并记入拒绝清单**，绝不静默入库。

设计依据
--------
- ``docs/kb-v1/02-architecture.md`` §3.1：ingestion 带 schema 校验与**拒绝清单**。
- ``03-task-dag.md`` P1-03：fixture 可 ingest；非法条目进拒绝清单且**不静默丢弃**。
- ``PROJECT-BRIEF`` 第十四章：当前语料零人工复核 → 入库条目只能 C/D。

纪律
----
1. **不编造来源**：本模块不提供任何"默认来源"兜底。来源缺失/未知即拒绝。
2. **不静默丢弃**：所有被拒条目连同原因进入 ``IngestionReport.rejected``。
3. **复用而非重写**：校验逻辑来自 t18 的 ``Passage`` / ``Commentary`` /
   ``SourceRegistry``，本模块不重新实现字段级规则。
4. **不碰向量索引**：本模块只写关系表，不调用 ``RAGService``。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeCommentary, KnowledgePassage
from app.schemas.knowledge import (
    UNKNOWN,
    Commentary,
    Passage,
    VerificationLevel,
)
from app.services.source_registry import (
    SourceRegistry,
    SourceRegistryError,
    get_source_registry,
)

logger = logging.getLogger(__name__)

#: 当前语料零人工复核、零已核验来源 → 允许入库的最高等级。
#: 依据 ``data/sources/source_registry.json`` 的 ``verified_source_count = 0``。
MAX_INGESTIBLE_LEVEL_WHEN_NO_VERIFIED_SOURCE: VerificationLevel = "C"


# ============================================================
# 报告结构
# ============================================================

@dataclass
class RejectedItem:
    """被拒绝的条目（含原因，供人工复核）。"""

    index: int
    kind: str  # "passage" | "commentary"
    identifier: str
    reason: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionReport:
    """ingest 结果报告。**拒绝项不被静默丢弃**。"""

    passages_written: int = 0
    commentaries_written: int = 0
    passages_updated: int = 0
    commentaries_updated: int = 0
    rejected: List[RejectedItem] = field(default_factory=list)
    #: 实际写入条目的 verification_level 分布（用于证明无 A/B）
    level_distribution: Dict[str, int] = field(default_factory=dict)

    @property
    def total_written(self) -> int:
        return self.passages_written + self.commentaries_written

    @property
    def total_rejected(self) -> int:
        return len(self.rejected)

    @property
    def ok(self) -> bool:
        """无拒绝项即视为干净导入。"""
        return not self.rejected

    def reject(self, index: int, kind: str, identifier: str, reason: str,
               raw: Optional[Dict[str, Any]] = None) -> None:
        self.rejected.append(RejectedItem(
            index=index, kind=kind, identifier=identifier, reason=reason,
            raw=raw or {},
        ))

    def note_level(self, level: str) -> None:
        self.level_distribution[level] = self.level_distribution.get(level, 0) + 1

    def summary(self) -> str:
        return (
            f"ingestion: passages={self.passages_written} "
            f"(updated={self.passages_updated}), "
            f"commentaries={self.commentaries_written} "
            f"(updated={self.commentaries_updated}), "
            f"rejected={self.total_rejected}, "
            f"levels={self.level_distribution}"
        )


class IngestionError(ValueError):
    """ingestion 结构性错误（如 fixture 文件不可读）。"""


# ============================================================
# 校验
# ============================================================

def _validate_passage(
    index: int, raw: Dict[str, Any], registry: SourceRegistry, report: IngestionReport,
) -> Optional[Passage]:
    """把原始 dict 校验为 Passage；失败记入拒绝清单并返回 None。"""
    identifier = str(raw.get("passage_id", f"<index {index}>"))

    # 1) 契约校验（含来源字段必填、text_type 枚举、A 级证据、分层规则）
    try:
        passage = Passage(**raw)
    except Exception as exc:  # pydantic ValidationError
        report.reject(index, "passage", identifier, f"schema 校验失败: {exc}", raw)
        return None

    # 2) 来源必须已登记，且等级不得超过该来源允许上限
    try:
        registry.assert_passage_source(passage)
    except SourceRegistryError as exc:
        report.reject(index, "passage", identifier, f"来源校验失败: {exc}", raw)
        return None

    return passage


def _validate_commentary(
    index: int, raw: Dict[str, Any], registry: SourceRegistry, report: IngestionReport,
) -> Optional[Commentary]:
    """把原始 dict 校验为 Commentary；失败记入拒绝清单并返回 None。

    注：``Commentary`` 使用 ``extra='forbid'``，因此内嵌 ``original``
    之类的原典副本字段会在此处**直接被拒**。
    """
    identifier = str(raw.get("commentary_id", f"<index {index}>"))

    try:
        commentary = Commentary(**raw)
    except Exception as exc:
        report.reject(index, "commentary", identifier, f"schema 校验失败: {exc}", raw)
        return None

    try:
        registry.assert_commentary_source(commentary)
    except SourceRegistryError as exc:
        report.reject(index, "commentary", identifier, f"来源校验失败: {exc}", raw)
        return None

    return commentary


# ============================================================
# ORM 映射
# ============================================================

_PASSAGE_COLUMNS = (
    "passage_id", "book_id", "book_title", "chapter_id", "chapter_title",
    "section", "line_no", "original", "original_traditional", "original_simplified",
    "author", "dynasty", "text_type", "commentator", "commentary_dynasty",
    "school", "concepts", "modern_topics", "modern_scenarios", "stance",
    "source_id", "source_provider", "source_url", "source_edition", "license",
    "verification_level", "proofread_status", "verified_by", "verified_at",
    "embedding_version",
)

_COMMENTARY_COLUMNS = (
    "commentary_id", "target_passage_id", "commentator", "commentary_dynasty",
    "commentary_text", "text_type", "source_id", "source_provider", "source_url",
    "source_edition", "license", "verification_level", "proofread_status",
    "verified_by", "verified_at", "embedding_version",
)


def _passage_to_orm(passage: Passage) -> Dict[str, Any]:
    data = passage.model_dump()
    row: Dict[str, Any] = {c: data[c] for c in _PASSAGE_COLUMNS}
    # chapter_id 在 Pydantic 侧允许 int|str，DB 统一存字符串
    row["chapter_id"] = str(row["chapter_id"])
    return row


def _commentary_to_orm(commentary: Commentary) -> Dict[str, Any]:
    data = commentary.model_dump()
    return {c: data[c] for c in _COMMENTARY_COLUMNS}


# ============================================================
# 主入口
# ============================================================

async def ingest_passages(
    session: AsyncSession,
    passages: Sequence[Dict[str, Any] | Passage],
    *,
    registry: Optional[SourceRegistry] = None,
    report: Optional[IngestionReport] = None,
) -> IngestionReport:
    """把 L1 原典条目 ingest 进 ``knowledge_passage``。

    Args:
        session: 异步 DB 会话（调用方负责 commit）。
        passages: 原始 dict 或已构造的 ``Passage``。
        registry: 来源注册表；默认加载仓库内的注册表。
        report: 复用既有报告（用于 passage + commentary 合并统计）。

    Returns:
        :class:`IngestionReport`，含写入数与**拒绝清单**。

    Raises:
        IngestionError: 结构性错误（如某条目的 dict 缺少 passage_id 等）。
    """
    registry = registry or get_source_registry()
    report = report or IngestionReport()

    for index, item in enumerate(passages):
        raw = item.model_dump() if isinstance(item, Passage) else dict(item)
        passage = _validate_passage(index, raw, registry, report)
        if passage is None:
            continue

        row = _passage_to_orm(passage)
        existing = await session.get(KnowledgePassage, row["passage_id"])
        if existing is None:
            session.add(KnowledgePassage(**row))
            report.passages_written += 1
        else:
            for key, value in row.items():
                setattr(existing, key, value)
            report.passages_updated += 1
        report.note_level(row["verification_level"])

    await session.flush()
    logger.info("ingest_passages: %s", report.summary())
    return report


async def ingest_commentaries(
    session: AsyncSession,
    commentaries: Sequence[Dict[str, Any] | Commentary],
    *,
    registry: Optional[SourceRegistry] = None,
    report: Optional[IngestionReport] = None,
    require_target_exists: bool = True,
) -> IngestionReport:
    """把 L2 注疏条目 ingest 进 ``knowledge_commentary``。

    Args:
        require_target_exists: 为 True 时，``target_passage_id`` 必须在 L1
            表中已存在，否则该条被拒（防止悬空注疏）。
    """
    registry = registry or get_source_registry()
    report = report or IngestionReport()

    for index, item in enumerate(commentaries):
        raw = item.model_dump() if isinstance(item, Commentary) else dict(item)
        commentary = _validate_commentary(index, raw, registry, report)
        if commentary is None:
            continue

        row = _commentary_to_orm(commentary)

        # 外键完整性：注疏必须指向已存在的 L1 passage
        if require_target_exists:
            target = await session.get(KnowledgePassage, row["target_passage_id"])
            if target is None:
                report.reject(
                    index, "commentary", row["commentary_id"],
                    f"target_passage_id={row['target_passage_id']!r} 在 L1 中不存在"
                    "（拒绝悬空注疏）",
                    raw,
                )
                continue

        existing = await session.get(KnowledgeCommentary, row["commentary_id"])
        if existing is None:
            session.add(KnowledgeCommentary(**row))
            report.commentaries_written += 1
        else:
            for key, value in row.items():
                setattr(existing, key, value)
            report.commentaries_updated += 1
        report.note_level(row["verification_level"])

    await session.flush()
    logger.info("ingest_commentaries: %s", report.summary())
    return report


async def ingest_bundle(
    session: AsyncSession,
    *,
    passages: Sequence[Dict[str, Any] | Passage] = (),
    commentaries: Sequence[Dict[str, Any] | Commentary] = (),
    registry: Optional[SourceRegistry] = None,
) -> IngestionReport:
    """一次 ingest L1 + L2（先原典后注疏，保证外键可解析）。"""
    report = IngestionReport()
    if passages:
        await ingest_passages(session, passages, registry=registry, report=report)
    if commentaries:
        await ingest_commentaries(session, commentaries, registry=registry, report=report)
    return report


# ============================================================
# JSON 文件装载
# ============================================================

def load_fixture(path: Path | str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """读取 fixture JSON，返回 ``(passages, commentaries)``。

    期望格式::

        {"passages": [...], "commentaries": [...]}

    任一键缺失视为空列表。文件不可读/JSON 非法抛 :class:`IngestionError`。
    """
    target = Path(path)
    if not target.exists():
        raise IngestionError(f"fixture 文件不存在: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestionError(f"fixture JSON 非法: {target}: {exc}") from exc

    if not isinstance(data, dict):
        raise IngestionError(f"fixture 顶层必须是对象: {target}")

    passages = data.get("passages") or []
    commentaries = data.get("commentaries") or []
    if not isinstance(passages, list) or not isinstance(commentaries, list):
        raise IngestionError("fixture 的 passages/commentaries 必须是数组")
    return passages, commentaries


async def ingest_fixture_file(
    session: AsyncSession, path: Path | str,
    *, registry: Optional[SourceRegistry] = None,
) -> IngestionReport:
    """从 fixture 文件 ingest。"""
    passages, commentaries = load_fixture(path)
    return await ingest_bundle(
        session, passages=passages, commentaries=commentaries, registry=registry,
    )


async def assert_no_high_level_ingested(
    session: AsyncSession, *, max_allowed: VerificationLevel = "C",
) -> Dict[str, int]:
    """只读检查：库中是否存在高于 ``max_allowed`` 的条目。

    用于 GATE-1 验收「入库条目的 verification_level 只能为 C/D」。
    返回 ``{level: count}`` 分布。
    """
    from sqlalchemy import func

    allowed = {"C", "D"} if max_allowed == "C" else {"A", "B", "C", "D"}
    dist: Dict[str, int] = {}

    for model in (KnowledgePassage, KnowledgeCommentary):
        rows = await session.execute(
            select(model.verification_level, func.count()).group_by(model.verification_level)
        )
        for level, count in rows.all():
            dist[level] = dist.get(level, 0) + count

    violations = {k: v for k, v in dist.items() if k not in allowed}
    if violations:
        raise IngestionError(
            f"存在超出允许范围的 verification_level: {violations}"
            f"（当前允许 {sorted(allowed)}；零人工复核与零已核验来源下不得标 A/B）"
        )
    return dist


def level_distribution_is_within(levels: Iterable[str], allowed=("C", "D")) -> bool:
    """纯函数：判断等级分布是否只落在允许集合内（便于单测）。"""
    return all(level in allowed for level in levels)


__all__ = [
    "MAX_INGESTIBLE_LEVEL_WHEN_NO_VERIFIED_SOURCE",
    "IngestionError",
    "IngestionReport",
    "RejectedItem",
    "ingest_passages",
    "ingest_commentaries",
    "ingest_bundle",
    "ingest_fixture_file",
    "load_fixture",
    "assert_no_high_level_ingested",
    "level_distribution_is_within",
]

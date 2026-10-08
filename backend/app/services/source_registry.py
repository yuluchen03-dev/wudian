"""
悟典 - 底本来源注册表（PHASE 1 / P1-02）

职责
----
1. 加载并校验 ``data/sources/source_registry.json``。
2. 提供 ``source_id → SourceRecord`` 查询。
3. **拒绝无来源条目入库**：``assert_passage_source`` / ``assert_commentary_source``
   在来源缺失、来源未知、或 ``verification_level`` 超出该来源允许上限时抛错。

硬约束（对应 PROJECT-BRIEF 第十/十一/十四章与 ``02-architecture.md`` §4.2）
--------------------------------------------------------------------------
- **严禁编造来源、版本或授权**：真实未知写哨兵 ``"unknown"``，
  不得留空、不得填占位假值。本模块不提供任何"默认来源"兜底。
- **来源未知 → 等级上限 C**：现有 11 个语料文件全部无来源字段，
  故一律登记 ``src_unknown``，``verification_level`` 只能 C/D。
- **A 级双重要求**：既需来源侧 ``authorization_status="authorized"``（附证据），
  也需 passage 侧人工确认依据（由 ``schemas.knowledge`` 的校验器强制）。

本模块**只读**注册表文件；不写入、不修改、不创建来源记录。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from app.schemas.knowledge import (
    LEVEL_RANK,
    UNKNOWN,
    Commentary,
    Passage,
    SourceRecord,
    VerificationLevel,
)

logger = logging.getLogger(__name__)

#: 仓库根下的注册表路径：<repo>/data/sources/source_registry.json
#: 本文件位于 <repo>/backend/app/services/source_registry.py
_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "sources" / "source_registry.json"
)

#: 显式未知来源 id（注册表内必须存在；不提供隐式兜底）
UNKNOWN_SOURCE_ID = "src_unknown"


class SourceRegistryError(ValueError):
    """来源注册表相关错误（加载失败 / 条目非法 / 来源缺失）。"""


class MissingSourceError(SourceRegistryError):
    """引用了注册表中不存在的 source_id。"""


class UnknownProvenanceError(SourceRegistryError):
    """来源字段为哨兵 unknown，不足以支撑所声明的质量等级。"""


class LevelExceedsSourceError(SourceRegistryError):
    """声明的 verification_level 超出该来源允许的最高等级。"""


class SourceRegistry:
    """来源注册表（进程内缓存，只读）。

    用法::

        registry = SourceRegistry.load()            # 从默认路径
        registry = SourceRegistry.load(path=...)    # 从指定路径
        record = registry.get("src_unknown")
        registry.assert_passage_source(passage)     # 不合规则抛错
    """

    def __init__(self, sources: Dict[str, SourceRecord], raw: Optional[dict] = None):
        self._sources = dict(sources)
        self._raw = raw or {}

    # ----------------------------------------------------------
    # 加载 / 校验
    # ----------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "SourceRegistry":
        """加载并校验注册表文件。

        Raises:
            SourceRegistryError: 文件缺失、JSON 非法、或任一条目校验失败。
        """
        target = Path(path) if path is not None else _DEFAULT_REGISTRY_PATH
        if not target.exists():
            raise SourceRegistryError(f"来源注册表不存在: {target}")

        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SourceRegistryError(f"来源注册表 JSON 非法: {target}: {exc}") from exc

        entries = data.get("sources")
        if not isinstance(entries, list):
            raise SourceRegistryError(
                "来源注册表缺少 'sources' 数组（不允许空注册表静默通过）"
            )

        sources: Dict[str, SourceRecord] = {}
        problems: List[str] = []
        for index, entry in enumerate(entries):
            try:
                record = SourceRecord(**entry)
            except Exception as exc:  # pydantic ValidationError
                problems.append(f"sources[{index}] ({entry.get('source_id', '?')}): {exc}")
                continue
            if record.source_id in sources:
                problems.append(f"sources[{index}]: source_id 重复: {record.source_id}")
                continue
            sources[record.source_id] = record

        if problems:
            raise SourceRegistryError(
                "来源注册表存在非法条目（拒绝静默跳过）:\n  " + "\n  ".join(problems)
            )
        if not sources:
            raise SourceRegistryError("来源注册表为空（拒绝无来源运行）")

        logger.info("来源注册表加载完成: %d 条", len(sources))
        return cls(sources, raw=data)

    # ----------------------------------------------------------
    # 查询
    # ----------------------------------------------------------
    def get(self, source_id: str) -> SourceRecord:
        """按 id 取来源记录。

        Raises:
            MissingSourceError: source_id 不在注册表中（**不做隐式兜底**）。
        """
        try:
            return self._sources[source_id]
        except KeyError:
            raise MissingSourceError(
                f"source_id={source_id!r} 不在来源注册表中。"
                "禁止引用未注册来源；如来源真实未知，请显式登记 src_unknown。"
            ) from None

    def try_get(self, source_id: str) -> Optional[SourceRecord]:
        """按 id 取来源记录，不存在返回 None（供只读探测使用）。"""
        return self._sources.get(source_id)

    def all_ids(self) -> List[str]:
        return sorted(self._sources)

    def all_records(self) -> Iterable[SourceRecord]:
        return tuple(self._sources.values())

    def __len__(self) -> int:
        return len(self._sources)

    def __contains__(self, source_id: object) -> bool:
        return source_id in self._sources

    @property
    def raw(self) -> dict:
        """原始 JSON（含 pending_verification 等待核验清单）。"""
        return self._raw

    @property
    def pending_verification(self) -> List[dict]:
        """待人工核验清单（来源授权、归属冲突等）。"""
        return list(self._raw.get("pending_verification", []))

    @property
    def verified_source_count(self) -> int:
        """已核验授权（authorization_status='authorized'）的来源数量。"""
        return sum(
            1 for r in self._sources.values() if r.authorization_status == "authorized"
        )

    # ----------------------------------------------------------
    # 拒绝无来源条目入库
    # ----------------------------------------------------------
    def assert_source_usable(self, source_id: str) -> SourceRecord:
        """确认 source_id 已注册。返回记录，否则抛 :class:`MissingSourceError`。"""
        return self.get(source_id)

    def assert_passage_source(self, passage: Passage) -> SourceRecord:
        """校验 passage 的来源与等级自洽；不合规抛错。

        检查项：
        1. ``passage.source_id`` 必须已注册；
        2. ``passage.verification_level`` 不得超过来源允许上限；
        3. 来源 provider/url/edition 全为 unknown 时，等级不得高于 C；
        4. 来源未授权（authorization_status != 'authorized'）时，等级不得为 A。
        """
        record = self.get(passage.source_id)
        self._assert_level_ceiling(
            level=passage.verification_level,
            record=record,
            subject=f"passage {passage.passage_id!r}",
        )
        return record

    def assert_commentary_source(self, commentary: Commentary) -> SourceRecord:
        """校验 commentary 的来源与等级自洽；不合规抛错（规则同 passage）。"""
        record = self.get(commentary.source_id)
        self._assert_level_ceiling(
            level=commentary.verification_level,
            record=record,
            subject=f"commentary {commentary.commentary_id!r}",
        )
        return record

    @staticmethod
    def _assert_level_ceiling(
        level: VerificationLevel, record: SourceRecord, subject: str,
    ) -> None:
        ceiling = record.max_verification_level

        # 来源字段全未知时，明确报 UnknownProvenanceError（更精确的诊断）
        if level in ("A", "B") and not record.has_known_provenance:
            unknown_fields = [
                name for name in ("provider", "url", "edition")
                if getattr(record, name).strip().lower() == UNKNOWN
            ]
            raise UnknownProvenanceError(
                f"{subject} 声明 verification_level={level!r}，但来源 "
                f"{record.source_id!r} 的 {unknown_fields} 为 'unknown'。"
                f"来源未核验时等级上限为 {ceiling!r}（当前语料只能 C/D）。"
                "禁止为无来源条目补造 provider/url/edition 以抬高等级。"
            )

        # 未授权不得为 A
        if level == "A" and record.authorization_status != "authorized":
            raise LevelExceedsSourceError(
                f"{subject} 声明 verification_level='A'，但来源 "
                f"{record.source_id!r} 的 authorization_status="
                f"{record.authorization_status!r}（非 'authorized'）。"
                "A 级要求权威文本 + 人工确认 + 已核验授权。"
            )

        if LEVEL_RANK[level] > LEVEL_RANK[ceiling]:
            raise LevelExceedsSourceError(
                f"{subject} 声明 verification_level={level!r}，超出来源 "
                f"{record.source_id!r} 允许的最高等级 {ceiling!r}。"
            )

    def validate_batch(
        self, passages: Iterable[Passage], commentaries: Iterable[Commentary] = (),
    ) -> List[str]:
        """批量校验，返回问题清单（**不静默丢弃**）。

        与 ``assert_*`` 的区别：本方法收集**全部**问题而不在首个错误处中断，
        供 ingestion 生成"拒绝清单"使用（P1-03）。
        """
        problems: List[str] = []
        for passage in passages:
            try:
                self.assert_passage_source(passage)
            except SourceRegistryError as exc:
                problems.append(f"passage {passage.passage_id!r}: {exc}")
        for commentary in commentaries:
            try:
                self.assert_commentary_source(commentary)
            except SourceRegistryError as exc:
                problems.append(f"commentary {commentary.commentary_id!r}: {exc}")
        return problems


# ============================================================
# 模块级单例（懒加载，供 ingestion / API 复用）
# ============================================================

_registry: Optional[SourceRegistry] = None


def get_source_registry(path: Optional[Path] = None, *, reload: bool = False) -> SourceRegistry:
    """获取来源注册表单例（懒加载）。

    Args:
        path: 自定义注册表路径（测试用）。
        reload: 强制重新加载（忽略缓存）。
    """
    global _registry
    if _registry is None or reload or path is not None:
        registry = SourceRegistry.load(path)
        if path is None:
            _registry = registry
        return registry
    return _registry


__all__ = [
    "UNKNOWN_SOURCE_ID",
    "SourceRegistry",
    "SourceRegistryError",
    "MissingSourceError",
    "UnknownProvenanceError",
    "LevelExceedsSourceError",
    "get_source_registry",
]

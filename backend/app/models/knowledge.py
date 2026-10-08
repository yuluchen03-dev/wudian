"""
悟典 - 可信知识库表模型（PHASE 1 / P1-04）

L1 权威原典与 L2 历代注疏**分离**存储，对应 PROJECT-BRIEF 第五章
「禁止把这些层混成普通 chunk」与第六章「原典和注疏必须分开储存」。

设计依据
--------
- ``docs/kb-v1/02-architecture.md`` §4.2：L1 表 ``knowledge_passage``；
  L2 表 ``knowledge_commentary``，经 ``target_passage_id`` 外键引用 L1，
  **不内嵌原文副本**（消除现状 ``lunyu_zhuxi.json`` 13/15 重复存储）。
- ``backend/app/schemas/knowledge.py``（t18 冻结的契约）：本模块的列定义
  与该 Pydantic 契约**逐字段对齐**，但表模型不重复实现校验逻辑——
  校验的单一真值来源是 Pydantic 模型 + ``SourceRegistry``。

与既有 ``verses`` 表的关系（02-architecture §4.2 决策 5 / §12 双真值风险）
------------------------------------------------------------------------
``knowledge_passage`` 是**检索与证据的唯一真值**；既有 ``verses`` 表保持
「学习进度用途」不变，两者并存、不迁移、不互相覆盖。

硬约束（在 DDL 层可验证的部分）
------------------------------
1. L2 **无** ``original`` / ``original_text`` 列 —— 原文副本在表结构上就不存在。
2. L2 ``target_passage_id`` 外键指向 ``knowledge_passage.passage_id``，
   带 ``ondelete="RESTRICT"``：不允许先删原典而留下悬空注疏。
3. L1 与 L2 各自独立表，不共用。
"""
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ============================================================
# 枚举取值（与 schemas/knowledge.py 保持一致，DDL 层加 CHECK 约束）
# ============================================================

TEXT_TYPES = ("original", "commentary", "translation", "modern_explanation")
VERIFICATION_LEVELS = ("A", "B", "C", "D")
PROOFREAD_STATUSES = ("unproofread", "machine_processed", "human_verified")


class KnowledgePassage(Base):
    """L1 权威原典表。

    列覆盖 PROJECT-BRIEF 第六章 29 字段（外加 ``source_id`` 外键，
    见 02-architecture §4.2）。可空性策略与 ``schemas/knowledge.py`` 一致：
    当前语料无诚实数据来源的字段**允许 NULL**，但写入时由 Pydantic 强制
    「必须显式传 None」，从而在数据层保留「确实为空」与「忘记填」的区别。
    """

    __tablename__ = "knowledge_passage"
    __table_args__ = (
        Index("idx_kp_book", "book_id", "chapter_id"),
        Index("idx_kp_text_type", "text_type"),
        Index("idx_kp_source", "source_id"),
        Index("idx_kp_school", "school"),
        Index("idx_kp_level", "verification_level"),
        CheckConstraint(
            "text_type IN ('original', 'commentary', 'translation', 'modern_explanation')",
            name="ck_kp_text_type",
        ),
        CheckConstraint(
            "verification_level IN ('A', 'B', 'C', 'D')",
            name="ck_kp_verification_level",
        ),
        CheckConstraint(
            "proofread_status IN ('unproofread', 'machine_processed', 'human_verified')",
            name="ck_kp_proofread_status",
        ),
        # 禁止把 AI 生成文本当作权威原典（与 schemas/knowledge.py 同规则，DDL 层再兜一层）
        CheckConstraint(
            "NOT (text_type = 'original' AND verification_level = 'D')",
            name="ck_kp_no_ai_as_original",
        ),
        # 注疏必须走 L2 表，L1 不得出现 text_type='commentary'
        CheckConstraint(
            "text_type <> 'commentary'",
            name="ck_kp_no_commentary_in_l1",
        ),
        # A 级必须有人工确认依据（DDL 层兜底；Pydantic 侧校验更细）
        CheckConstraint(
            "verification_level <> 'A' OR ("
            "proofread_status = 'human_verified' "
            "AND verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="ck_kp_level_a_requires_human_evidence",
        ),
        {"comment": "L1 权威原典表（检索与证据的唯一真值）"},
    )

    # --- 身份 ---
    passage_id: Mapped[str] = mapped_column(
        String(200), primary_key=True, comment="全局唯一 passage 主键"
    )
    book_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="书籍 slug"
    )
    book_title: Mapped[str] = mapped_column(String(200), nullable=False, comment="书名")
    chapter_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="篇章 id（int/str 统一存字符串）"
    )
    chapter_title: Mapped[str] = mapped_column(String(200), nullable=False, comment="篇章名")
    section: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="节/小节")
    line_no: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="行号")

    # --- 正文 ---
    original: Mapped[str] = mapped_column(Text, nullable=False, comment="原典正文")
    original_traditional: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="繁体原文"
    )
    original_simplified: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="简体原文"
    )

    # --- 作者 / 时代 ---
    author: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="作者")
    dynasty: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="朝代")

    # --- 分层 ---
    text_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="文本类型（L1 不应为 commentary）"
    )

    # --- 注疏元信息（L1 不适用，保留列以满足 29 字段）---
    commentator: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="注疏者（L1 不适用，应为 NULL）"
    )
    commentary_dynasty: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="注疏朝代（L1 不适用，应为 NULL）"
    )

    # --- 学派与概念 ---
    school: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="学派")
    concepts: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="思想概念标签（受控词表见 PHASE 3）"
    )
    modern_topics: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="现代议题标签"
    )
    modern_scenarios: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="现代情境标签"
    )
    stance: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="学派立场")

    # --- 来源与复核 ---
    source_id: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True,
        comment="指向 data/sources/source_registry.json 的 source_id",
    )
    source_provider: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="来源提供方（未知须显式 'unknown'）"
    )
    source_url: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="来源链接（未知须显式 'unknown'）"
    )
    source_edition: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="所据底本（未知须显式 'unknown'）"
    )
    license: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="授权状态（未知须显式 'unknown'）"
    )
    verification_level: Mapped[str] = mapped_column(
        String(1), nullable=False, comment="质量等级 A/B/C/D"
    )
    proofread_status: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="复核状态"
    )
    verified_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="人工确认者（A 级必需）"
    )
    verified_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="人工确认时间（A 级必需）"
    )

    # --- 索引与时间 ---
    embedding_version: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="向量索引版本（PHASE 4 写入）"
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间"
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False, comment="更新时间",
    )

    # --- 关系：一个 passage 可被多条注疏引用 ---
    commentaries = relationship(
        "KnowledgeCommentary",
        back_populates="target_passage",
        cascade="save-update, merge",
    )

    def __repr__(self) -> str:
        return f"<KnowledgePassage(passage_id='{self.passage_id}', level='{self.verification_level}')>"


class KnowledgeCommentary(Base):
    """L2 历代注疏表。

    **本表刻意不包含任何原文列**（无 ``original`` / ``original_text``）——
    这是「不内嵌原典原文副本」约束在 DDL 层的体现。注疏文本放在
    ``commentary_text``，对原典的引用一律通过 ``target_passage_id`` 外键。
    """

    __tablename__ = "knowledge_commentary"
    __table_args__ = (
        Index("idx_kc_target", "target_passage_id"),
        Index("idx_kc_source", "source_id"),
        Index("idx_kc_commentator", "commentator"),
        CheckConstraint("text_type = 'commentary'", name="ck_kc_text_type"),
        CheckConstraint(
            "verification_level IN ('A', 'B', 'C', 'D')",
            name="ck_kc_verification_level",
        ),
        CheckConstraint(
            "proofread_status IN ('unproofread', 'machine_processed', 'human_verified')",
            name="ck_kc_proofread_status",
        ),
        CheckConstraint(
            "verification_level <> 'A' OR ("
            "proofread_status = 'human_verified' "
            "AND verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="ck_kc_level_a_requires_human_evidence",
        ),
        # D 级 = AI 解释，不得冒充历代注疏
        CheckConstraint(
            "verification_level <> 'D'",
            name="ck_kc_no_ai_as_commentary",
        ),
        {"comment": "L2 历代注疏表（经 target_passage_id 引用 L1，不内嵌原文）"},
    )

    commentary_id: Mapped[str] = mapped_column(
        String(200), primary_key=True, comment="注疏条目主键"
    )
    target_passage_id: Mapped[str] = mapped_column(
        String(200),
        ForeignKey("knowledge_passage.passage_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="外键 → L1 passage_id（替代内嵌原文副本）",
    )
    commentator: Mapped[str] = mapped_column(String(200), nullable=False, comment="注疏者")
    commentary_dynasty: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="注疏者朝代"
    )
    commentary_text: Mapped[str] = mapped_column(Text, nullable=False, comment="注疏正文")
    text_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="commentary", comment="固定 'commentary'"
    )

    # --- 来源与复核 ---
    source_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source_provider: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_edition: Mapped[str] = mapped_column(String(300), nullable=False)
    license: Mapped[str] = mapped_column(String(200), nullable=False)
    verification_level: Mapped[str] = mapped_column(String(1), nullable=False)
    proofread_status: Mapped[str] = mapped_column(String(30), nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verified_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    embedding_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    target_passage = relationship("KnowledgePassage", back_populates="commentaries")

    def __repr__(self) -> str:
        return (
            f"<KnowledgeCommentary(commentary_id='{self.commentary_id}', "
            f"target='{self.target_passage_id}')>"
        )


__all__ = [
    "TEXT_TYPES",
    "VERIFICATION_LEVELS",
    "PROOFREAD_STATUSES",
    "KnowledgePassage",
    "KnowledgeCommentary",
]

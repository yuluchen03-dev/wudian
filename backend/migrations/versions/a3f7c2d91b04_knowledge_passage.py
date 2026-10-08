"""add knowledge_passage and knowledge_commentary (L1/L2 separation)

PHASE 1 / P1-04：建立可信知识库的 L1 原典表与 L2 注疏表。

设计依据 docs/kb-v1/02-architecture.md §4.2：
- L1 ``knowledge_passage``：权威原典，检索与证据的唯一真值。
- L2 ``knowledge_commentary``：历代注疏，经 ``target_passage_id`` 外键引用 L1，
  **不内嵌原典原文副本**（消除现状 lunyu_zhuxi.json 13/15 重复存储）。
- 既有 ``verses`` 表（``601e9ee0d57f``）**不动**，保持「学习进度用途」。

DDL 层硬约束（与 schemas/knowledge.py + SourceRegistry 的校验互补）：
- ``ck_kp_no_ai_as_original``：text_type='original' 不得配 verification_level='D'。
- ``ck_kp_no_commentary_in_l1``：注疏不得进 L1 表。
- ``ck_kc_no_ai_as_commentary``：L2 不得标 D（D = AI 解释，不是历代注疏）。
- ``ck_*_level_a_requires_human_evidence``：A 级必须有人工确认依据。

Revision ID: a3f7c2d91b04
Revises: 601e9ee0d57f
Create Date: 2026-10-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f7c2d91b04"
down_revision: Union[str, Sequence[str], None] = "601e9ee0d57f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: 建立 L1 原典表与 L2 注疏表。"""
    op.create_table(
        "knowledge_passage",
        # --- 身份 ---
        sa.Column("passage_id", sa.String(length=200), nullable=False),
        sa.Column("book_id", sa.String(length=100), nullable=False),
        sa.Column("book_title", sa.String(length=200), nullable=False),
        sa.Column("chapter_id", sa.String(length=100), nullable=False),
        sa.Column("chapter_title", sa.String(length=200), nullable=False),
        sa.Column("section", sa.String(length=200), nullable=True),
        sa.Column("line_no", sa.Integer(), nullable=True),
        # --- 正文 ---
        sa.Column("original", sa.Text(), nullable=False),
        sa.Column("original_traditional", sa.Text(), nullable=True),
        sa.Column("original_simplified", sa.Text(), nullable=True),
        # --- 作者/时代 ---
        sa.Column("author", sa.String(length=200), nullable=True),
        sa.Column("dynasty", sa.String(length=100), nullable=True),
        # --- 分层 ---
        sa.Column("text_type", sa.String(length=30), nullable=False),
        # --- 注疏元信息（L1 不适用）---
        sa.Column("commentator", sa.String(length=200), nullable=True),
        sa.Column("commentary_dynasty", sa.String(length=100), nullable=True),
        # --- 学派与概念 ---
        sa.Column("school", sa.String(length=100), nullable=True),
        sa.Column("concepts", sa.JSON(), nullable=False),
        sa.Column("modern_topics", sa.JSON(), nullable=False),
        sa.Column("modern_scenarios", sa.JSON(), nullable=False),
        sa.Column("stance", sa.String(length=200), nullable=True),
        # --- 来源与复核 ---
        sa.Column("source_id", sa.String(length=200), nullable=False),
        sa.Column("source_provider", sa.String(length=300), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("source_edition", sa.String(length=300), nullable=False),
        sa.Column("license", sa.String(length=200), nullable=False),
        sa.Column("verification_level", sa.String(length=1), nullable=False),
        sa.Column("proofread_status", sa.String(length=30), nullable=False),
        sa.Column("verified_by", sa.String(length=200), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        # --- 索引与时间 ---
        sa.Column("embedding_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("passage_id"),
        # 禁止 AI 生成文本冒充权威原典
        sa.CheckConstraint(
            "NOT (text_type = 'original' AND verification_level = 'D')",
            name="ck_kp_no_ai_as_original",
        ),
        # 注疏必须走 L2 表
        sa.CheckConstraint("text_type <> 'commentary'", name="ck_kp_no_commentary_in_l1"),
        sa.CheckConstraint(
            "text_type IN ('original', 'commentary', 'translation', 'modern_explanation')",
            name="ck_kp_text_type",
        ),
        sa.CheckConstraint(
            "verification_level IN ('A', 'B', 'C', 'D')",
            name="ck_kp_verification_level",
        ),
        sa.CheckConstraint(
            "proofread_status IN ('unproofread', 'machine_processed', 'human_verified')",
            name="ck_kp_proofread_status",
        ),
        # A 级必须有人工确认依据
        sa.CheckConstraint(
            "verification_level <> 'A' OR ("
            "proofread_status = 'human_verified' "
            "AND verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="ck_kp_level_a_requires_human_evidence",
        ),
        comment="L1 权威原典表（检索与证据的唯一真值）",
    )
    op.create_index("idx_kp_book", "knowledge_passage", ["book_id", "chapter_id"])
    op.create_index("idx_kp_text_type", "knowledge_passage", ["text_type"])
    op.create_index("idx_kp_source", "knowledge_passage", ["source_id"])
    op.create_index("idx_kp_school", "knowledge_passage", ["school"])
    op.create_index("idx_kp_level", "knowledge_passage", ["verification_level"])

    op.create_table(
        "knowledge_commentary",
        sa.Column("commentary_id", sa.String(length=200), nullable=False),
        sa.Column("target_passage_id", sa.String(length=200), nullable=False),
        sa.Column("commentator", sa.String(length=200), nullable=False),
        sa.Column("commentary_dynasty", sa.String(length=100), nullable=False),
        sa.Column("commentary_text", sa.Text(), nullable=False),
        sa.Column("text_type", sa.String(length=30), nullable=False),
        sa.Column("source_id", sa.String(length=200), nullable=False),
        sa.Column("source_provider", sa.String(length=300), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("source_edition", sa.String(length=300), nullable=False),
        sa.Column("license", sa.String(length=200), nullable=False),
        sa.Column("verification_level", sa.String(length=1), nullable=False),
        sa.Column("proofread_status", sa.String(length=30), nullable=False),
        sa.Column("verified_by", sa.String(length=200), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        # 外键：注疏引用原典，不复制原文。RESTRICT 防止删除原典后留下悬空注疏。
        sa.ForeignKeyConstraint(
            ["target_passage_id"], ["knowledge_passage.passage_id"],
            name="fk_kc_target_passage", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("commentary_id"),
        sa.CheckConstraint("text_type = 'commentary'", name="ck_kc_text_type"),
        sa.CheckConstraint(
            "verification_level IN ('A', 'B', 'C', 'D')",
            name="ck_kc_verification_level",
        ),
        sa.CheckConstraint(
            "proofread_status IN ('unproofread', 'machine_processed', 'human_verified')",
            name="ck_kc_proofread_status",
        ),
        # D 级 = AI 解释，不得冒充历代注疏
        sa.CheckConstraint("verification_level <> 'D'", name="ck_kc_no_ai_as_commentary"),
        sa.CheckConstraint(
            "verification_level <> 'A' OR ("
            "proofread_status = 'human_verified' "
            "AND verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="ck_kc_level_a_requires_human_evidence",
        ),
        comment="L2 历代注疏表（经 target_passage_id 引用 L1，不内嵌原文）",
    )
    op.create_index("idx_kc_target", "knowledge_commentary", ["target_passage_id"])
    op.create_index("idx_kc_source", "knowledge_commentary", ["source_id"])
    op.create_index("idx_kc_commentator", "knowledge_commentary", ["commentator"])


def downgrade() -> None:
    """Downgrade schema: 先删 L2 再删 L1（外键依赖顺序）。"""
    op.drop_index("idx_kc_commentator", table_name="knowledge_commentary")
    op.drop_index("idx_kc_source", table_name="knowledge_commentary")
    op.drop_index("idx_kc_target", table_name="knowledge_commentary")
    op.drop_table("knowledge_commentary")

    op.drop_index("idx_kp_level", table_name="knowledge_passage")
    op.drop_index("idx_kp_school", table_name="knowledge_passage")
    op.drop_index("idx_kp_source", table_name="knowledge_passage")
    op.drop_index("idx_kp_text_type", table_name="knowledge_passage")
    op.drop_index("idx_kp_book", table_name="knowledge_passage")
    op.drop_table("knowledge_passage")

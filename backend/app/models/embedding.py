"""
悟典 - 向量嵌入模型
用于 AI 智能问答的语义检索

兼容性说明：
- PostgreSQL + pgvector：使用 Vector(1536) 类型存储向量
- SQLite / 无 pgvector：使用 Text 类型存储向量的 JSON 字符串
通过 settings.is_sqlite 自动判断。
"""
from sqlalchemy import String, Integer, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base
from app.models.base import TimestampMixin

# 尝试导入 pgvector，如果不可用则使用 Text 占位
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


def _embedding_column():
    """根据数据库类型返回合适的 embedding 列定义"""
    # SQLite 或未安装 pgvector 时，使用 Text 存储 JSON 字符串
    if settings.is_sqlite or not HAS_PGVECTOR:
        return mapped_column(
            Text,
            nullable=False,
            comment="语义向量（JSON 字符串，SQLite/无pgvector模式）",
        )
    # PostgreSQL + pgvector
    return mapped_column(
        Vector(1536),
        nullable=False,
        comment="语义向量（1536维，pgvector）",
    )


class VerseEmbedding(Base, TimestampMixin):
    """经文向量嵌入表 - 存储经文的语义向量用于相似度检索"""

    __tablename__ = "verse_embeddings"
    __table_args__ = (
        Index("idx_embedding_verse", "verse_id"),
        {"comment": "经文向量嵌入表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=False, unique=True, comment="经文 ID"
    )
    # 向量维度 1536 (OpenAI text-embedding-3-small)
    embedding = _embedding_column()
    # 嵌入的文本内容（用于重建）
    source_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="嵌入源文本"
    )
    # 嵌入模型
    model_name: Mapped[str] = mapped_column(
        String(100), default="text-embedding-3-small", nullable=False, comment="嵌入模型"
    )

    # 关系
    verse = relationship("Verse")

    def __repr__(self):
        return f"<VerseEmbedding(verse_id={self.verse_id}, model='{self.model_name}')>"


class AiChatLog(Base, TimestampMixin):
    """AI 对话记录表 - 存储用户与 AI 的对话历史"""

    __tablename__ = "ai_chat_logs"
    __table_args__ = (
        Index("idx_chat_user", "user_id"),
        Index("idx_chat_user_verse", "user_id", "verse_id"),
        {"comment": "AI 对话记录表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    verse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True, comment="相关经文 ID"
    )
    # 角色: user / assistant
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="对话角色"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="对话内容"
    )
    # 对话会话 ID
    session_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="会话 ID"
    )
    # 检索到的相关经文 ID（JSON）
    context_verse_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="检索到的上下文经文ID（JSON）"
    )

    def __repr__(self):
        return f"<AiChatLog(user_id={self.user_id}, role='{self.role}')>"

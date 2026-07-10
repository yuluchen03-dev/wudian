"""
悟典 - 学习进度模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class Progress(Base, BaseModelMixin):
    """学习进度表 - 记录用户对每条经文的学习状态"""

    __tablename__ = "progress"
    __table_args__ = (
        UniqueConstraint("user_id", "verse_id", name="uq_progress_user_verse"),
        Index("idx_progress_user", "user_id"),
        Index("idx_progress_chapter", "chapter_id"),
        Index("idx_progress_status", "status"),
        {"comment": "学习进度表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="CASCADE"),
        nullable=False, comment="书籍 ID"
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False, comment="章节 ID"
    )
    verse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=False, comment="经文 ID"
    )

    # 学习状态: not_started / learning / reviewed / mastered
    status: Mapped[str] = mapped_column(
        String(20), default="not_started", nullable=False, comment="学习状态"
    )
    # 掌握程度: 0.0 - 1.0
    mastery_level: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="掌握程度 0-1"
    )
    # 学习次数
    study_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="学习次数"
    )
    # 学习时长（秒）
    study_duration: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="累计学习时长（秒）"
    )

    last_reviewed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后复习时间"
    )
    next_review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="下次复习日期"
    )

    # 关系
    user = relationship("User", back_populates="progress_records")
    verse = relationship("Verse", back_populates="progress_records")

    def __repr__(self):
        return f"<Progress(user_id={self.user_id}, verse_id={self.verse_id}, status='{self.status}')>"

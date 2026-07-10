"""
悟典 - SRS 间隔重复记忆调度模型
基于 SM-2 算法的改进版
"""
from datetime import date
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class SrsRecord(Base, BaseModelMixin):
    """SRS 记忆调度记录表 - 管理每条经文的间隔重复调度"""

    __tablename__ = "srs_records"
    __table_args__ = (
        UniqueConstraint("user_id", "verse_id", name="uq_srs_user_verse"),
        Index("idx_srs_user_next", "user_id", "next_review_date"),
        Index("idx_srs_next_review", "next_review_date"),
        {"comment": "SRS 间隔重复调度记录表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    verse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=False, comment="经文 ID"
    )

    # SM-2 算法参数
    ease_factor: Mapped[float] = mapped_column(
        Float, default=2.5, nullable=False, comment="容易度因子（初始2.5，最小1.3）"
    )
    interval_days: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="当前间隔天数"
    )
    repetitions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="成功复习次数"
    )

    # 调度日期
    last_review_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="上次复习日期"
    )
    next_review_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="下次复习日期"
    )

    # 上次评分 (0-5): 0=完全忘记, 5=完美记住
    last_rating: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="上次复习评分 0-5"
    )
    # 总复习次数
    total_reviews: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="总复习次数"
    )
    # 遗忘次数
    lapse_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="遗忘次数（评分<3）"
    )

    # 调度状态: new / learning / review / relearning / suspended
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False, comment="调度状态"
    )

    # 关系
    user = relationship("User", back_populates="srs_records")
    verse = relationship("Verse", back_populates="srs_records")

    def __repr__(self):
        return f"<SrsRecord(user_id={self.user_id}, verse_id={self.verse_id}, next={self.next_review_date})>"

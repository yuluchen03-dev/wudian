"""
悟典 - 成就系统模型
"""
from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Achievement(Base, TimestampMixin):
    """成就表 - 记录用户获得的成就徽章"""

    __tablename__ = "achievements"
    __table_args__ = (
        Index("idx_achievement_user", "user_id"),
        Index("idx_achievement_user_type", "user_id", "badge_type"),
        {"comment": "成就表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    badge_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="徽章类型"
    )
    badge_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="徽章名称"
    )
    badge_icon: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="徽章图标 URL"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="成就描述"
    )
    # 成就等级: bronze / silver / gold / platinum
    tier: Mapped[str] = mapped_column(
        String(20), default="bronze", nullable=False, comment="成就等级"
    )
    # 获得时的经验值奖励
    exp_reward: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="经验值奖励"
    )

    # 关系
    user = relationship("User", back_populates="achievements")

    def __repr__(self):
        return f"<Achievement(user_id={self.user_id}, badge='{self.badge_name}', tier='{self.tier}')>"

"""
悟典 - 每日打卡模型
记录用户每日学习打卡，用于 streak 连续天数计算
"""
from datetime import date
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Checkin(Base, BaseModelMixin):
    """每日打卡表 - 记录用户每日学习打卡"""

    __tablename__ = "checkins"
    __table_args__ = (
        Index("idx_checkin_user_date", "user_id", "checkin_date"),
        UniqueConstraint("user_id", "checkin_date", name="uq_checkin_user_date"),
        Index("idx_checkin_group", "group_id"),
        {"comment": "每日打卡表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="用户 ID"
    )
    checkin_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="打卡日期"
    )
    # 关联小组（可选，用于小组打卡统计）
    group_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("study_groups.id", ondelete="SET NULL"),
        nullable=True, comment="小组 ID"
    )
    # 当日学习经文数
    verses_learned: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="当日学习经文数"
    )
    # 当日学习时长(秒)
    study_duration: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="当日学习时长(秒)"
    )
    # 获得 XP
    exp_gained: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="当日获得经验值"
    )
    # 是否使用补签道具
    is_makeup: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否补签"
    )
    note: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="打卡心得"
    )

    def __repr__(self):
        return f"<Checkin(user_id={self.user_id}, date={self.checkin_date})>"

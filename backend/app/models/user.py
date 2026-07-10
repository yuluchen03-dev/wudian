"""
悟典 - 用户模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class User(Base, BaseModelMixin):
    """用户表 - 存储用户基本信息和学习状态"""

    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True, comment="邮箱"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="加密密码"
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像 URL"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="昵称"
    )
    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="个人简介"
    )

    # 学习状态
    level: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="用户等级"
    )
    exp_points: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="经验值"
    )
    streak_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="连续学习天数"
    )
    total_study_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="总学习天数"
    )
    total_verses_learned: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="已学经文数"
    )
    # PK 段位分（ELO rating）
    pk_rating: Mapped[int] = mapped_column(
        Integer, default=1000, nullable=False, comment="PK 段位分"
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否超级管理员"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )
    last_study_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后学习时间"
    )

    # 关系
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    srs_records = relationship("SrsRecord", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    quiz_records = relationship("QuizRecord", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', level={self.level})>"

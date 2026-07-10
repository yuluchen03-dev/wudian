"""
悟典 - 社区模型
学习小组、小组成员、PK 对战
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class StudyGroup(Base, BaseModelMixin):
    """学习小组表"""

    __tablename__ = "study_groups"
    __table_args__ = (
        Index("idx_group_category", "category"),
        Index("idx_group_owner", "owner_id"),
        {"comment": "学习小组表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="小组名称"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="小组简介"
    )
    # 小组分类: beginner / advanced / theme / free
    category: Mapped[str] = mapped_column(
        String(20), default="free", nullable=False, comment="小组分类"
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="创建者 ID"
    )
    # 当前学习书籍（字符串形式 bookId，兼容前端）
    book_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="当前学习书籍 ID"
    )
    current_book_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="SET NULL"),
        nullable=True, comment="当前学习书籍 ORM ID"
    )
    # 小组类型: public / private
    group_type: Mapped[str] = mapped_column(
        String(20), default="public", nullable=False, comment="小组类型"
    )
    is_private: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否私有"
    )
    max_members: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False, comment="最大成员数"
    )
    member_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="当前成员数"
    )
    # 邀请码
    invite_code: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, comment="邀请码"
    )

    # 关系
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<StudyGroup(id={self.id}, name='{self.name}')>"


class GroupMember(Base, BaseModelMixin):
    """小组成员表"""

    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
        Index("idx_group_member_user", "user_id"),
        {"comment": "小组成员表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_groups.id", ondelete="CASCADE"),
        nullable=False, comment="小组 ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    # 角色: owner / admin / member
    role: Mapped[str] = mapped_column(
        String(20), default="member", nullable=False, comment="成员角色"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="加入时间"
    )

    # 关系
    group = relationship("StudyGroup", back_populates="members")

    def __repr__(self):
        return f"<GroupMember(group_id={self.group_id}, user_id={self.user_id}, role='{self.role}')>"


class PkMatch(Base, BaseModelMixin):
    """PK 对战表 - 用户之间的知识竞赛"""

    __tablename__ = "pk_matches"
    __table_args__ = (
        Index("idx_pk_match_user1", "player1_id"),
        Index("idx_pk_match_user2", "player2_id"),
        Index("idx_pk_match_status", "status"),
        {"comment": "PK 对战表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="玩家1 ID"
    )
    player2_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, comment="玩家2 ID"
    )
    # 对战书籍范围
    book_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="SET NULL"),
        nullable=True, comment="对战书籍 ID"
    )
    # 题目数量
    question_count: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False, comment="题目数量"
    )
    # 状态: waiting / ongoing / completed / cancelled
    status: Mapped[str] = mapped_column(
        String(20), default="waiting", nullable=False, comment="对战状态"
    )
    # 分数
    player1_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="玩家1得分"
    )
    player2_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="玩家2得分"
    )
    # 胜者: 1 / 2 / 0(平局) / null(未结束)
    winner: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="胜者（1/2/0平局）"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开始时间"
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="结束时间"
    )

    def __repr__(self):
        return f"<PkMatch(id={self.id}, p1={self.player1_id}, p2={self.player2_id}, status='{self.status}')>"

"""
悟典 - 笔记模型
用户对经文的个人笔记与批注
"""
from sqlalchemy import String, Integer, Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class Note(Base, BaseModelMixin):
    """笔记表 - 用户对经文的个人笔记"""

    __tablename__ = "notes"
    __table_args__ = (
        Index("idx_note_user", "user_id"),
        Index("idx_note_verse", "verse_id"),
        Index("idx_note_user_verse", "user_id", "verse_id"),
        Index("idx_note_group", "group_id"),
        Index("idx_note_book", "book_id"),
        {"comment": "笔记表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    verse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True, comment="经文 ID"
    )
    title: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="笔记标题"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="笔记内容（Markdown）"
    )
    # 关联书籍/章节（字符串形式，兼容前端 bookId/chapterId）
    book_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="关联书籍 ID"
    )
    chapter_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="关联章节 ID"
    )
    verse_text: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="引用经文原文"
    )
    # 关联小组（可选）
    group_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("study_groups.id", ondelete="SET NULL"),
        nullable=True, comment="关联小组 ID"
    )
    # 标签（JSON 数组字符串存储）
    tags: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="标签（JSON 数组）"
    )
    # 是否公开
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否公开"
    )
    # 是否精选
    is_essence: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否精选"
    )
    # 点赞数（冗余计数，加速查询）
    likes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="点赞数"
    )
    # 评论数（冗余计数）
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="评论数"
    )
    # 收藏数
    favorites: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="收藏数"
    )

    # 关系
    user = relationship("User", back_populates="notes")
    verse = relationship("Verse", back_populates="notes")
    likes_records = relationship("NoteLike", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Note(id={self.id}, user_id={self.user_id}, verse_id={self.verse_id})>"


class NoteLike(Base, BaseModelMixin):
    """笔记点赞表"""

    __tablename__ = "note_likes"
    __table_args__ = (
        Index("idx_note_like_user", "user_id"),
        Index("idx_note_like_note", "note_id"),
        UniqueConstraint("user_id", "note_id", name="uq_note_like"),
        {"comment": "笔记点赞表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="点赞用户 ID"
    )
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False, comment="笔记 ID"
    )

    # 关系
    note = relationship("Note", back_populates="likes_records")

    def __repr__(self):
        return f"<NoteLike(user_id={self.user_id}, note_id={self.note_id})>"


class Comment(Base, BaseModelMixin):
    """笔记评论表 - 支持评论与回复（自关联）"""

    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_comment_note", "note_id"),
        Index("idx_comment_user", "user_id"),
        Index("idx_comment_parent", "parent_id"),
        {"comment": "笔记评论表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False, comment="笔记 ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="评论者 ID"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="评论内容"
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True, comment="父评论 ID（回复）"
    )
    like_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="点赞数"
    )

    # 关系
    note = relationship("Note", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Comment(id={self.id}, note_id={self.note_id}, user_id={self.user_id})>"

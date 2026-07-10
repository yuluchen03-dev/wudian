"""
悟典 - 题库与答题记录模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Dict, Any

from app.core.database import Base
from app.models.base import BaseModelMixin


class Quiz(Base, BaseModelMixin):
    """题库表 - 各类型练习题"""

    __tablename__ = "quizzes"
    __table_args__ = (
        Index("idx_quiz_verse", "verse_id"),
        Index("idx_quiz_type_difficulty", "quiz_type", "difficulty"),
        Index("idx_quiz_chapter", "chapter_id"),
        {"comment": "题库表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        comment="题型：choice/fill/match/translate/explain/order"
    )
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="CASCADE"),
        nullable=False, comment="书籍 ID"
    )
    chapter_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=True, comment="章节 ID"
    )
    verse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=True, comment="经文 ID"
    )

    question: Mapped[str] = mapped_column(
        Text, nullable=False, comment="题干"
    )
    # 选项使用 JSON 存储，适配各种题型
    options: Mapped[List[Dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, comment="选项（JSON 数组）"
    )
    answer: Mapped[str] = mapped_column(
        Text, nullable=False, comment="正确答案"
    )
    explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="答案解析"
    )
    difficulty: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="难度 1-5"
    )
    tags: Mapped[List[str] | None] = mapped_column(
        JSON, nullable=True, comment="标签（JSON 数组）"
    )

    # 关系
    verse = relationship("Verse", back_populates="quizzes")
    quiz_records = relationship("QuizRecord", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz(id={self.id}, type='{self.quiz_type}', difficulty={self.difficulty})>"


class QuizRecord(Base, BaseModelMixin):
    """答题记录表 - 记录用户每次答题情况"""

    __tablename__ = "quiz_records"
    __table_args__ = (
        Index("idx_quiz_record_user", "user_id"),
        Index("idx_quiz_record_user_quiz", "user_id", "quiz_id"),
        {"comment": "答题记录表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户 ID"
    )
    quiz_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False, comment="题目 ID"
    )

    user_answer: Mapped[str] = mapped_column(
        Text, nullable=False, comment="用户作答"
    )
    is_correct: Mapped[bool] = mapped_column(
        Integer, nullable=False, comment="是否正确（0/1）"
    )
    score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="得分"
    )
    time_spent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="耗时（秒）"
    )
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="答题时间"
    )

    # 关系
    user = relationship("User", back_populates="quiz_records")
    quiz = relationship("Quiz", back_populates="quiz_records")

    def __repr__(self):
        return f"<QuizRecord(user_id={self.user_id}, quiz_id={self.quiz_id}, correct={self.is_correct})>"

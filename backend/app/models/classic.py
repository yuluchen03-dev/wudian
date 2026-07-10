"""
悟典 - 经典文献模型
四书五经的结构化存储：书籍 -> 章节 -> 经文
"""
from sqlalchemy import String, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class ClassicBook(Base, BaseModelMixin):
    """经典书籍表 - 四书五经等典籍"""

    __tablename__ = "classic_books"
    __table_args__ = {"comment": "经典书籍表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="书名"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="分类：四书/五经"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="书籍简介"
    )
    author: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="作者/编者"
    )
    era: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="朝代"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序序号"
    )

    # 关系
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClassicBook(id={self.id}, title='{self.title}')>"


class Chapter(Base, BaseModelMixin):
    """章节表 - 书籍的章节"""

    __tablename__ = "chapters"
    __table_args__ = (
        Index("idx_chapter_book", "book_id", "chapter_number"),
        {"comment": "章节表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="书籍 ID"
    )
    chapter_number: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="章节序号"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="章节标题"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="章节简介"
    )

    # 关系
    book = relationship("ClassicBook", back_populates="chapters")
    verses = relationship("Verse", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter(id={self.id}, book_id={self.book_id}, ch={self.chapter_number})>"


class Verse(Base, BaseModelMixin):
    """经文表 - 最小学习单元"""

    __tablename__ = "verses"
    __table_args__ = (
        Index("idx_verse_chapter", "chapter_id", "verse_number"),
        Index("idx_verse_book", "book_id"),
        {"comment": "经文表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classic_books.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="书籍 ID"
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="章节 ID"
    )
    verse_number: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="经文序号"
    )
    original_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="原文"
    )
    translation: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="白话翻译"
    )
    annotation: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="注释"
    )
    interpretation: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="解读/义理"
    )
    pinyin: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="拼音标注"
    )
    audio_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="朗读音频 URL"
    )

    # 关系
    book = relationship("ClassicBook")
    chapter = relationship("Chapter", back_populates="verses")
    progress_records = relationship("Progress", back_populates="verse")
    srs_records = relationship("SrsRecord", back_populates="verse")
    notes = relationship("Note", back_populates="verse")
    quizzes = relationship("Quiz", back_populates="verse")

    def __repr__(self):
        return f"<Verse(id={self.id}, book_id={self.book_id}, ch={self.chapter_id}, v={self.verse_number})>"

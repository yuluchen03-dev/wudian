"""
悟典 - 数据模型模块
导出所有 ORM 模型，确保 SQLAlchemy 能正确建立关系映射
"""

from app.models.base import Base, BaseModelMixin, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.classic import ClassicBook, Chapter, Verse
from app.models.progress import Progress
from app.models.srs_record import SrsRecord
from app.models.quiz import Quiz, QuizRecord
from app.models.achievement import Achievement
from app.models.note import Note, NoteLike, Comment
from app.models.community import StudyGroup, GroupMember, PkMatch
from app.models.embedding import VerseEmbedding, AiChatLog
from app.models.checkin import Checkin

__all__ = [
    # Base
    "Base",
    "BaseModelMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # 用户
    "User",
    # 经典文献
    "ClassicBook",
    "Chapter",
    "Verse",
    # 学习进度
    "Progress",
    # SRS 调度
    "SrsRecord",
    # 题库
    "Quiz",
    "QuizRecord",
    # 成就
    "Achievement",
    # 笔记
    "Note",
    "NoteLike",
    "Comment",
    # 社区
    "StudyGroup",
    "GroupMember",
    "PkMatch",
    # AI 向量
    "VerseEmbedding",
    "AiChatLog",
    # 打卡
    "Checkin",
]

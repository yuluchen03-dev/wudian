"""
悟典 - 学习模块请求/响应模型 (Pydantic)
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, Field


# ---------- 通用 ----------

class APIResponse(BaseModel):
    """统一响应包装"""
    code: int = 0
    message: str = "ok"
    data: Optional[Any] = None


# ---------- 闯关课程树 ----------

class ChapterTreeNode(BaseModel):
    chapter_id: int
    chapter_number: int
    title: str
    description: Optional[str] = None
    verse_count: int
    completed_count: int
    is_unlocked: bool
    is_completed: bool
    progress_pct: float


class BookTreeNode(BaseModel):
    book_id: int
    title: str
    category: str
    description: Optional[str] = None
    chapters: list[ChapterTreeNode]


class ChapterTreeResponse(BaseModel):
    books: list[BookTreeNode]


# ---------- 完成学习 ----------

class CompleteVerseRequest(BaseModel):
    verse_id: int
    read_completed: bool = True
    study_duration: int = Field(default=0, ge=0, description="本次学习时长(秒)")


class CompleteVerseResponse(BaseModel):
    progress_id: int
    verse_id: int
    status: str
    read_completed: bool
    quiz_passed: bool
    completed: bool
    completed_at: Optional[str] = None
    exp_gained: int = 0
    new_achievements: list[dict] = Field(default_factory=list)


# ---------- 每日一句 ----------

class DailyQuoteResponse(BaseModel):
    verse_id: int
    book_title: str
    chapter_title: str
    original_text: str
    translation: Optional[str] = None
    interpretation: Optional[str] = None


# ---------- 打卡 ----------

class CheckinRequest(BaseModel):
    verses_learned: int = 0
    study_duration: int = 0
    exp_gained: int = Field(default=0, ge=0, le=100, description="经验值上限100")
    note: Optional[str] = None


class CheckinResponse(BaseModel):
    checkin_id: int
    checkin_date: str
    verses_learned: int
    study_duration: int
    exp_gained: int
    is_makeup: bool
    streak_days: int
    total_study_days: int
    new_achievements: list[dict] = Field(default_factory=list)


class MakeupCheckinRequest(BaseModel):
    target_date: date
    note: Optional[str] = None


class StreakResponse(BaseModel):
    streak_days: int
    total_study_days: int
    checked_in_today: bool
    at_risk: bool
    last_study_at: Optional[str] = None
    recent_7_days: list[dict]
    grace_hours: int


# ---------- SRS 复习 ----------

class DueReviewItem(BaseModel):
    record_id: int
    verse_id: int
    book_id: int
    chapter_id: int
    original_text: str
    translation: Optional[str] = None
    repetitions: int
    ease_factor: float
    interval_days: int
    next_review_at: Optional[str] = None
    last_review_at: Optional[str] = None


class DueReviewsResponse(BaseModel):
    due_count: int
    items: list[DueReviewItem]


class ReviewRequest(BaseModel):
    verse_id: int
    quality: int = Field(ge=0, le=5, description="答题质量 0-5")
    # 简化模式
    is_correct: Optional[bool] = None
    hesitation_seconds: float = 0.0


class ReviewResponse(BaseModel):
    verse_id: int
    repetitions: int
    ease_factor: float
    interval_days: int
    next_review_at: str
    is_relearn: bool
    exp_gained: int = 0


class ReviewStatsResponse(BaseModel):
    due_count: int
    mastered_count: int
    learning_count: int
    reviewed_today: int
    total_in_srs: int


# ---------- 测验 ----------

class QuizOption(BaseModel):
    index: int
    text: str


class QuizItem(BaseModel):
    quiz_id: int
    verse_id: int
    question_type: str
    difficulty: int
    question: str
    options: Optional[Any] = None


class QuizResponse(BaseModel):
    items: list[QuizItem]


class QuizAnswerItem(BaseModel):
    quiz_id: int
    user_answer: dict
    time_spent: int = 0


class QuizSubmitRequest(BaseModel):
    verse_id: Optional[int] = None
    answers: list[QuizAnswerItem]


class QuizFeedback(BaseModel):
    quiz_id: int
    is_correct: bool
    correct_answer: Optional[Any] = None
    explanation: str = ""
    in_wrong_book: bool = False


class QuizSubmitResponse(BaseModel):
    total: int
    correct_count: int
    wrong_count: int
    score: int
    passed: bool
    pass_threshold: int
    total_time: int
    results: list[QuizFeedback]
    wrong_list: list[QuizFeedback]
    exp_gained: int = 0
    verse_completed: bool = False


# ---------- 错题本 ----------

class WrongBookItem(BaseModel):
    record_id: int
    quiz_id: int
    verse_id: int
    question_type: str
    question: str
    options: Optional[Any] = None
    user_answer: Optional[Any] = None
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    created_at: Optional[str] = None


class WrongBookResponse(BaseModel):
    items: list[WrongBookItem]
    total: int
    limit: int
    offset: int


class ResolveWrongRequest(BaseModel):
    record_id: int


class RetryWrongRequest(BaseModel):
    record_id: int
    user_answer: dict


# ---------- 成就 ----------

class AchievementItem(BaseModel):
    code: str
    type: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    exp_reward: int
    unlocked: bool
    unlocked_at: Optional[str] = None


class AchievementsResponse(BaseModel):
    total: int
    unlocked_count: int
    achievements: list[AchievementItem]


class RankInfo(BaseModel):
    code: str
    name: str
    min_exp: int
    icon: str


class RankResponse(BaseModel):
    current_rank: RankInfo
    next_rank: Optional[RankInfo] = None
    exp: int
    exp_to_next: int
    progress_pct: float
    all_ranks: list[RankInfo]


# ---------- 排行榜 ----------

class LeaderboardItem(BaseModel):
    rank: int
    user_id: int
    username: str
    nickname: str
    avatar: Optional[str] = None
    exp: int
    streak_days: int
    verses_learned: int
    rank_name: str
    rank_icon: str


class LeaderboardResponse(BaseModel):
    scope: str
    items: list[LeaderboardItem]


# ---------- 进度概览 ----------

class OverallProgressResponse(BaseModel):
    verses_completed: int
    total_verses: int
    chapters_touched: int
    completion_pct: float


class DailyGoalResponse(BaseModel):
    date: str
    learned_today: int
    learn_target: int
    learn_achieved: bool

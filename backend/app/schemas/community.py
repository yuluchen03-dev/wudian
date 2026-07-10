"""
悟典 - 社区共学层数据模型
共读小组、笔记、评论、点赞、PK 竞技、排行榜
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
#  枚举
# ============================================================

class GroupCategory(str, Enum):
    """小组分类"""
    BEGINNER = "beginner"       # 入门共读
    ADVANCED = "advanced"       # 进阶研读
    THEME = "theme"             # 主题共读
    FREE = "free"               # 自由共读


class NoteSortBy(str, Enum):
    """笔记排序方式"""
    LATEST = "latest"           # 最新
    HOTTEST = "hottest"         # 最热（点赞数）
    ESSENCE = "essence"         # 精选


class PKStatus(str, Enum):
    """PK 状态"""
    MATCHING = "matching"       # 匹配中
    ONGOING = "ongoing"         # 进行中
    FINISHED = "finished"       # 已结束
    CANCELLED = "cancelled"     # 已取消


class PKResult(str, Enum):
    """PK 结算结果"""
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"


class LeaderboardScope(str, Enum):
    """排行榜范围"""
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


# ============================================================
#  共读小组
# ============================================================

class GroupCreate(BaseModel):
    """创建小组"""
    name: str = Field(..., min_length=2, max_length=50, description="小组名称")
    description: str = Field("", max_length=500, description="小组简介")
    category: GroupCategory = Field(GroupCategory.FREE, description="小组分类")
    book_id: Optional[str] = Field(None, description="共读书籍 ID")
    max_members: int = Field(50, ge=2, le=500, description="最大成员数")
    is_private: bool = Field(False, description="是否私有")


class GroupMemberBrief(BaseModel):
    """小组成员简要信息"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    level: int = 1
    joined_at: datetime
    is_owner: bool = False
    checkin_days: int = 0


class GroupBrief(BaseModel):
    """小组列表项"""
    id: int
    name: str
    description: str
    category: GroupCategory
    book_id: Optional[str] = None
    owner_name: str
    member_count: int
    max_members: int
    today_checkin_count: int
    is_private: bool
    created_at: datetime


class GroupDetail(GroupBrief):
    """小组详情"""
    members: List[GroupMemberBrief] = []
    total_checkin_days: int = 0


class GroupCheckinStat(BaseModel):
    """小组打卡统计"""
    group_id: int
    today_checkin_count: int
    today_checkin_members: List[GroupMemberBrief] = []
    week_checkin_rate: float = 0.0
    streak_days: int = 0


# ============================================================
#  笔记
# ============================================================

class NoteCreate(BaseModel):
    """发布笔记"""
    title: str = Field("", max_length=100, description="笔记标题")
    content: str = Field(..., min_length=1, max_length=5000, description="笔记内容")
    book_id: Optional[str] = Field(None, description="关联书籍")
    chapter_id: Optional[str] = Field(None, description="关联章节")
    verse_text: Optional[str] = Field(None, description="引用经文")
    group_id: Optional[int] = Field(None, description="关联小组")
    tags: List[str] = Field(default_factory=list, description="标签")
    is_public: bool = Field(True, description="是否公开")


class CommentCreate(BaseModel):
    """发表评论"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论 ID（回复）")


class AuthorBrief(BaseModel):
    """作者简要信息"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    level: int = 1


class CommentBrief(BaseModel):
    """评论"""
    id: int
    author: AuthorBrief
    content: str
    like_count: int = 0
    parent_id: Optional[int] = None
    created_at: datetime
    replies: List["CommentBrief"] = Field(default_factory=list)


class NoteBrief(BaseModel):
    """笔记列表项"""
    id: int
    title: str
    content: str
    excerpt: str = Field("", description="内容摘要")
    author: AuthorBrief
    book_id: Optional[str] = None
    chapter_id: Optional[str] = None
    verse_text: Optional[str] = None
    group_id: Optional[int] = None
    tags: List[str] = []
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    is_essence: bool = False
    created_at: datetime


class NoteDetail(NoteBrief):
    """笔记详情"""
    comments: List[CommentBrief] = []


class NoteListResponse(BaseModel):
    """笔记列表分页响应"""
    items: List[NoteBrief]
    total: int
    page: int
    page_size: int
    has_more: bool


class LikeResult(BaseModel):
    """点赞结果"""
    note_id: int
    liked: bool
    like_count: int


# ============================================================
#  PK 竞技
# ============================================================

class PKMatchRequest(BaseModel):
    """PK 匹配请求"""
    book_id: Optional[str] = Field(None, description="指定书籍范围，空为全库")
    question_count: int = Field(10, ge=5, le=20, description="题目数量")


class PKQuestion(BaseModel):
    """PK 题目"""
    index: int
    question: str
    options: List[str]
    verse_source: Optional[str] = None


class PKMatchResult(BaseModel):
    """PK 匹配结果"""
    pk_id: str
    opponent: AuthorBrief
    questions: List[PKQuestion]
    time_limit_seconds: int = 300
    status: PKStatus = PKStatus.ONGOING


class PKSubmitAnswer(BaseModel):
    """提交单题答案"""
    question_index: int
    selected_option: int


class PKSubmitRequest(BaseModel):
    """提交 PK 答案"""
    pk_id: str
    answers: List[PKSubmitAnswer]
    duration_seconds: int


class PKSettlement(BaseModel):
    """PK 结算"""
    pk_id: str
    my_score: int
    opponent_score: int
    result: PKResult
    correct_count: int
    total_count: int
    exp_gained: int
    rating_change: int
    new_rating: int


# ============================================================
#  排行榜
# ============================================================

class LeaderboardEntry(BaseModel):
    """排行榜条目"""
    rank: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    level: int = 1
    score: int
    score_label: str = Field("", description="分数含义，如'经验值'/'打卡天数'")
    extra: Optional[str] = Field(None, description="附加信息，如'连续30天'")


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    scope: LeaderboardScope
    metric: str
    my_rank: Optional[int] = None
    my_score: Optional[int] = None
    entries: List[LeaderboardEntry]


CommentBrief.model_rebuild()

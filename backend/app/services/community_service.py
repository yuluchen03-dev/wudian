"""
悟典 - 社区共学服务
共读小组、笔记互动、答题 PK、排行榜

设计说明：
- 本服务使用 SQLAlchemy 2.0 异步语法持久化到数据库。
- 接口签名与返回结构对齐 schemas/community.py，前端兼容。
- 所有方法接收 db: AsyncSession，由 API 层注入。
"""
import json
import random
import uuid
from datetime import datetime, timedelta, date, timezone
from typing import Dict, List, Optional

from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.community import StudyGroup, GroupMember, PkMatch
from app.models.note import Note, NoteLike, Comment
from app.models.checkin import Checkin
from app.schemas.community import (
    AuthorBrief,
    CommentBrief,
    GroupBrief,
    GroupCategory,
    GroupCheckinStat,
    GroupCreate,
    GroupDetail,
    GroupMemberBrief,
    LeaderboardEntry,
    LeaderboardResponse,
    LeaderboardScope,
    LikeResult,
    NoteBrief,
    NoteCreate,
    NoteDetail,
    NoteListResponse,
    NoteSortBy,
    PKMatchRequest,
    PKMatchResult,
    PKQuestion,
    PKResult,
    PKSettlement,
    PKStatus,
    PKSubmitRequest,
)


# ============================================================
#  辅助函数
# ============================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return date.today()


def _excerpt(content: str, length: int = 80) -> str:
    if not content:
        return ""
    if len(content) <= length:
        return content
    return content[:length] + "..."


def _author_from_user(user: User) -> AuthorBrief:
    """从 User ORM 对象构造 AuthorBrief"""
    return AuthorBrief(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar,
        level=user.level,
    )


def _parse_tags(tags_str: Optional[str]) -> List[str]:
    """解析 tags JSON 字符串为列表"""
    if not tags_str:
        return []
    try:
        result = json.loads(tags_str)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _serialize_tags(tags: List[str]) -> Optional[str]:
    """将 tags 列表序列化为 JSON 字符串"""
    if not tags:
        return None
    return json.dumps(tags, ensure_ascii=False)


# ============================================================
#  PK 题库（MVP 演示用，后续从 gamification 模块拉取）
# ============================================================

_PK_QUESTIONS = [
    PKQuestion(index=0, question='「有朋自远方来」的下一句是？',
               options=["不亦乐乎", "不亦说乎", "不亦君子乎", "不亦善乎"], verse_source="《论语·学而》"),
    PKQuestion(index=1, question='「温故而知新」出自哪部经典？',
               options=["《大学》", "《中庸》", "《论语》", "《孟子》"], verse_source="《论语·为政》"),
    PKQuestion(index=2, question='「三人行，必有我师焉」强调的是？',
               options=["谦虚好学", "尊师重道", "勤奋刻苦", "诚实守信"], verse_source="《论语·述而》"),
    PKQuestion(index=3, question='「学而不思则罔」的下一句是？',
               options=["思而不学则殆", "思而不学则罔", "学而不厌", "诲人不倦"], verse_source="《论语·为政》"),
    PKQuestion(index=4, question='「己所不欲，勿施于人」讲的是？',
               options=["恕道", "忠道", "孝道", "仁道"], verse_source="《论语·卫灵公》"),
    PKQuestion(index=5, question='「君子坦荡荡」的下一句是？',
               options=["小人长戚戚", "小人常戚戚", "小人常悲悲", "小人长悲悲"], verse_source="《论语·述而》"),
    PKQuestion(index=6, question='「朝闻道，夕死可矣」体现的是？',
               options=["对真理的追求", "对死亡的恐惧", "对时间的珍惜", "对人生的感慨"], verse_source="《论语·里仁》"),
    PKQuestion(index=7, question='「知之为知之，不知为不知」讲的是？',
               options=["求知的态度", "做人的原则", "交友的方法", "做事的智慧"], verse_source="《论语·为政》"),
    PKQuestion(index=8, question='「敏而好学，不耻下问」出自？',
               options=["《论语·公冶长》", "《论语·学而》", "《孟子》", "《大学》"], verse_source="《论语·公冶长》"),
    PKQuestion(index=9, question='「见贤思齐焉」的下一句是？',
               options=["见不贤而内自省也", "见不贤而远之也", "见不贤而改之也", "见不贤而叹之也"], verse_source="《论语·里仁》"),
    PKQuestion(index=10, question='「工欲善其事」的下一句是？',
               options=["必先利其器", "必先苦其心", "必先正其身", "必先诚其意"], verse_source="《论语·卫灵公》"),
    PKQuestion(index=11, question='「人无远虑」的下一句是？',
               options=["必有近忧", "必有远忧", "必无近忧", "必无远虑"], verse_source="《论语·卫灵公》"),
    PKQuestion(index=12, question='「君子和而不同」的下一句是？',
               options=["小人同而不和", "小人和而不同", "小人同而不同", "小人和而不和"], verse_source="《论语·子路》"),
    PKQuestion(index=13, question='「吾日三省吾身」出自？',
               options=["《论语·学而》（曾子）", "《论语·学而》（孔子）", "《大学》", "《中庸》"], verse_source="《论语·学而》"),
    PKQuestion(index=14, question='「士不可以不弘毅」是因为？',
               options=["任重而道远", "任重而道短", "任轻而道远", "任重而道近"], verse_source="《论语·泰伯》"),
]
_PK_ANSWERS = [0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def _rating_tier(rating: int) -> str:
    """PK 段位名称"""
    if rating >= 1600:
        return "圣人"
    elif rating >= 1400:
        return "贤人"
    elif rating >= 1200:
        return "君子"
    elif rating >= 1000:
        return "士人"
    else:
        return "童生"


# PK 内存会话（题目、答案暂存，PK 结束后写入 pk_matches 表）
# 由于 PK 进行中的临时数据（题目顺序、对手模拟答案）不必持久化，仍用内存。
_pk_sessions: Dict[str, dict] = {}


# ============================================================
#  社区共学服务
# ============================================================

class CommunityService:
    """社区共学服务 - 数据库持久化实现"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 共读小组 ----------

    async def create_group(
        self, user_id: int, username: str, level: int, data: GroupCreate
    ) -> GroupDetail:
        """创建共读小组"""
        group = StudyGroup(
            name=data.name,
            description=data.description,
            category=data.category.value,
            owner_id=user_id,
            book_id=data.book_id,
            group_type="private" if data.is_private else "public",
            is_private=data.is_private,
            max_members=data.max_members,
            member_count=1,
        )
        self.db.add(group)
        await self.db.flush()

        # 创建者自动成为组长
        member = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role="owner",
            joined_at=_utcnow(),
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(group)

        return await self.get_group(group.id, current_user_id=user_id)

    async def list_groups(
        self,
        category: Optional[GroupCategory] = None,
        book_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """小组列表"""
        conditions = [StudyGroup.is_deleted == False]
        if category:
            conditions.append(StudyGroup.category == category.value)
        if book_id:
            conditions.append(StudyGroup.book_id == str(book_id))

        # 总数
        count_stmt = select(func.count(StudyGroup.id)).where(and_(*conditions))
        total = int((await self.db.execute(count_stmt)).scalar() or 0)

        # 分页查询
        offset = (page - 1) * page_size
        stmt = (
            select(StudyGroup)
            .where(and_(*conditions))
            .order_by(StudyGroup.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        groups = (await self.db.execute(stmt)).scalars().all()

        briefs = [await self._to_group_brief(g) for g in groups]
        return {
            "items": briefs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + page_size < total,
        }

    async def get_group(self, group_id: int, current_user_id: Optional[int] = None) -> GroupDetail:
        """小组详情"""
        group = await self._get_group(group_id)
        if not group:
            raise ValueError(f"小组 {group_id} 不存在")

        # 查询成员（关联用户表）
        member_stmt = (
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.is_deleted == False,
                    User.is_deleted == False,
                )
            )
            .order_by(GroupMember.joined_at)
        )
        rows = (await self.db.execute(member_stmt)).all()

        today = _today()
        today_checkin_count = 0
        member_briefs = []
        total_checkin_days = 0

        for gm, user in rows:
            # 统计每个成员在该小组的累计打卡天数
            checkin_days = await self._get_user_group_checkin_days(user.id, group_id)
            total_checkin_days += checkin_days

            # 今日是否打卡
            checked_today = await self._is_user_checked_today(user.id, group_id, today)
            if checked_today:
                today_checkin_count += 1

            member_briefs.append(
                GroupMemberBrief(
                    user_id=user.id,
                    username=user.username,
                    nickname=user.nickname,
                    avatar=user.avatar,
                    level=user.level,
                    joined_at=gm.joined_at,
                    is_owner=(gm.role == "owner"),
                    checkin_days=checkin_days,
                )
            )

        brief = await self._to_group_brief(group, today_checkin_count=today_checkin_count)
        return GroupDetail(
            **brief.model_dump(),
            members=member_briefs,
            total_checkin_days=total_checkin_days,
        )

    async def join_group(self, group_id: int, user_id: int, username: str, level: int) -> GroupDetail:
        """加入小组"""
        group = await self._get_group(group_id)
        if not group:
            raise ValueError(f"小组 {group_id} 不存在")

        # 检查是否已在小组中
        existing_stmt = select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.is_deleted == False,
            )
        )
        existing = (await self.db.execute(existing_stmt)).scalars().first()
        if existing:
            raise ValueError("你已在该小组中")

        # 检查人数上限
        count_stmt = select(func.count(GroupMember.id)).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.is_deleted == False,
            )
        )
        current_count = int((await self.db.execute(count_stmt)).scalar() or 0)
        if current_count >= group.max_members:
            raise ValueError("小组已满员")

        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role="member",
            joined_at=_utcnow(),
        )
        self.db.add(member)

        # 更新小组成员计数
        group.member_count = current_count + 1
        await self.db.commit()
        await self.db.refresh(group)

        return await self.get_group(group_id, current_user_id=user_id)

    async def leave_group(self, group_id: int, user_id: int) -> None:
        """退出小组"""
        group = await self._get_group(group_id)
        if not group:
            raise ValueError(f"小组 {group_id} 不存在")

        if group.owner_id == user_id:
            raise ValueError("组长不能退出，请先转让或解散小组")

        # 查询成员记录
        member_stmt = select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.is_deleted == False,
            )
        )
        member = (await self.db.execute(member_stmt)).scalars().first()
        if not member:
            raise ValueError("你不在该小组中")

        # 软删除成员
        member.is_deleted = True
        # 更新小组成员计数
        if group.member_count > 0:
            group.member_count -= 1
        await self.db.commit()

    async def checkin(self, group_id: int, user_id: int) -> GroupCheckinStat:
        """小组打卡"""
        group = await self._get_group(group_id)
        if not group:
            raise ValueError(f"小组 {group_id} 不存在")

        # 检查是否是成员
        member_stmt = select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.is_deleted == False,
            )
        )
        member = (await self.db.execute(member_stmt)).scalars().first()
        if not member:
            raise ValueError("你不在该小组中，无法打卡")

        today = _today()
        # 检查今日是否已打卡（该用户+该小组）
        existing_stmt = select(Checkin).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.checkin_date == today,
                Checkin.group_id == group_id,
                Checkin.is_deleted == False,
            )
        )
        existing = (await self.db.execute(existing_stmt)).scalars().first()
        if existing:
            raise ValueError("今日已打卡")

        # 创建打卡记录
        checkin = Checkin(
            user_id=user_id,
            checkin_date=today,
            group_id=group_id,
            verses_learned=0,
            study_duration=0,
            exp_gained=5,
            note="小组打卡",
        )
        self.db.add(checkin)

        # 更新用户 streak（简化：调用 streak 逻辑会增加 streak_days）
        # 这里直接累加 streak_days 和 total_study_days
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        if user:
            # 检查昨天是否打卡（任意小组），决定是否连续
            yesterday = today - timedelta(days=1)
            yesterday_stmt = select(Checkin).where(
                and_(
                    Checkin.user_id == user_id,
                    Checkin.checkin_date == yesterday,
                    Checkin.is_deleted == False,
                )
            )
            yesterday_checkin = (await self.db.execute(yesterday_stmt)).scalars().first()
            if yesterday_checkin:
                user.streak_days = (user.streak_days or 0) + 1
            else:
                user.streak_days = 1
            user.total_study_days = (user.total_study_days or 0) + 1
            user.last_study_at = _utcnow()

        await self.db.commit()
        return await self.get_group_checkin_stat(group_id)

    async def get_group_checkin_stat(self, group_id: int) -> GroupCheckinStat:
        """小组打卡统计"""
        group = await self._get_group(group_id)
        if not group:
            raise ValueError(f"小组 {group_id} 不存在")

        # 查询成员
        member_stmt = (
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.is_deleted == False,
                    User.is_deleted == False,
                )
            )
        )
        rows = (await self.db.execute(member_stmt)).all()
        members = [(gm, u) for gm, u in rows]

        today = _today()

        # 今日打卡成员
        today_checkin_members = []
        today_count = 0
        for gm, user in members:
            checked = await self._is_user_checked_today(user.id, group_id, today)
            if checked:
                today_count += 1
                checkin_days = await self._get_user_group_checkin_days(user.id, group_id)
                today_checkin_members.append(
                    GroupMemberBrief(
                        user_id=user.id,
                        username=user.username,
                        nickname=user.nickname,
                        avatar=user.avatar,
                        level=user.level,
                        joined_at=gm.joined_at,
                        is_owner=(gm.role == "owner"),
                        checkin_days=checkin_days,
                    )
                )

        # 本周打卡率
        now = _utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_days = [week_start.date() + timedelta(days=i) for i in range(7)]
        possible = len(members) * len(week_days) if members else 1

        week_checkin_stmt = select(func.count(Checkin.id)).where(
            and_(
                Checkin.group_id == group_id,
                Checkin.checkin_date.in_(week_days),
                Checkin.is_deleted == False,
            )
        )
        actual = int((await self.db.execute(week_checkin_stmt)).scalar() or 0)
        week_rate = round(actual / possible, 2) if possible else 0.0

        # 连续打卡天数（小组整体，至少有1人打卡算连续）
        streak = 0
        check_date = today
        for _ in range(365):
            day_count_stmt = select(func.count(Checkin.id)).where(
                and_(
                    Checkin.group_id == group_id,
                    Checkin.checkin_date == check_date,
                    Checkin.is_deleted == False,
                )
            )
            day_count = int((await self.db.execute(day_count_stmt)).scalar() or 0)
            if day_count > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return GroupCheckinStat(
            group_id=group_id,
            today_checkin_count=today_count,
            today_checkin_members=today_checkin_members,
            week_checkin_rate=week_rate,
            streak_days=streak,
        )

    async def _to_group_brief(
        self, group: StudyGroup, today_checkin_count: Optional[int] = None
    ) -> GroupBrief:
        """将 ORM 对象转为 GroupBrief"""
        if today_checkin_count is None:
            today = _today()
            count_stmt = select(func.count(Checkin.id)).where(
                and_(
                    Checkin.group_id == group.id,
                    Checkin.checkin_date == today,
                    Checkin.is_deleted == False,
                )
            )
            today_checkin_count = int((await self.db.execute(count_stmt)).scalar() or 0)

        # 获取 owner_name
        owner_stmt = select(User).where(User.id == group.owner_id)
        owner = (await self.db.execute(owner_stmt)).scalars().first()
        owner_name = owner.username if owner else f"user_{group.owner_id}"

        return GroupBrief(
            id=group.id,
            name=group.name,
            description=group.description or "",
            category=GroupCategory(group.category),
            book_id=group.book_id,
            owner_name=owner_name,
            member_count=group.member_count,
            max_members=group.max_members,
            today_checkin_count=today_checkin_count,
            is_private=group.is_private,
            created_at=group.created_at,
        )

    async def _get_group(self, group_id: int) -> Optional[StudyGroup]:
        """查询小组（排除软删除）"""
        stmt = select(StudyGroup).where(
            and_(
                StudyGroup.id == group_id,
                StudyGroup.is_deleted == False,
            )
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def _is_user_checked_today(
        self, user_id: int, group_id: int, today: date
    ) -> bool:
        """检查用户今日是否在指定小组打卡"""
        stmt = select(Checkin.id).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.group_id == group_id,
                Checkin.checkin_date == today,
                Checkin.is_deleted == False,
            )
        )
        return (await self.db.execute(stmt)).first() is not None

    async def _get_user_group_checkin_days(
        self, user_id: int, group_id: int
    ) -> int:
        """获取用户在指定小组的累计打卡天数"""
        stmt = select(func.count(Checkin.id)).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.group_id == group_id,
                Checkin.is_deleted == False,
            )
        )
        return int((await self.db.execute(stmt)).scalar() or 0)

    # ---------- 笔记 ----------

    async def create_note(
        self, user_id: int, username: str, level: int, data: NoteCreate
    ) -> NoteDetail:
        """发布笔记"""
        note = Note(
            user_id=user_id,
            verse_id=None,
            title=data.title or None,
            content=data.content,
            book_id=data.book_id,
            chapter_id=data.chapter_id,
            verse_text=data.verse_text,
            group_id=data.group_id,
            tags=_serialize_tags(data.tags),
            is_public=data.is_public,
            is_essence=False,
            likes=0,
            comment_count=0,
            favorites=0,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return await self.get_note(note.id, current_user_id=user_id)

    async def list_notes(
        self,
        group_id: Optional[int] = None,
        book_id: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: NoteSortBy = NoteSortBy.LATEST,
        page: int = 1,
        page_size: int = 20,
        current_user_id: Optional[int] = None,
    ) -> NoteListResponse:
        """笔记流"""
        conditions = [Note.is_deleted == False, Note.is_public == True]
        if group_id is not None:
            conditions.append(Note.group_id == group_id)
        if book_id:
            conditions.append(Note.book_id == str(book_id))
        if tag:
            # tags 是 JSON 字符串，用 LIKE 模糊匹配
            conditions.append(Note.tags.like(f'%"{tag}"%'))

        if sort_by == NoteSortBy.ESSENCE:
            conditions.append(Note.is_essence == True)

        # 总数
        count_stmt = select(func.count(Note.id)).where(and_(*conditions))
        total = int((await self.db.execute(count_stmt)).scalar() or 0)

        # 排序
        if sort_by == NoteSortBy.HOTTEST:
            order = (Note.likes.desc(), Note.created_at.desc())
        else:
            order = (Note.created_at.desc(),)

        offset = (page - 1) * page_size
        stmt = (
            select(Note)
            .where(and_(*conditions))
            .order_by(*order)
            .offset(offset)
            .limit(page_size)
        )
        notes = (await self.db.execute(stmt)).scalars().all()

        briefs = [await self._to_note_brief(n, current_user_id) for n in notes]
        return NoteListResponse(
            items=briefs,
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + page_size < total,
        )

    async def get_note(self, note_id: int, current_user_id: Optional[int] = None) -> NoteDetail:
        """笔记详情"""
        note = await self._get_note(note_id)
        if not note:
            raise ValueError(f"笔记 {note_id} 不存在")

        brief = await self._to_note_brief(note, current_user_id)
        comments = await self._get_comments_for_note(note_id)
        return NoteDetail(**brief.model_dump(), comments=comments)

    async def like_note(self, note_id: int, user_id: int) -> LikeResult:
        """点赞 / 取消点赞（toggle）"""
        note = await self._get_note(note_id)
        if not note:
            raise ValueError(f"笔记 {note_id} 不存在")

        # 检查是否已点赞
        existing_stmt = select(NoteLike).where(
            and_(
                NoteLike.user_id == user_id,
                NoteLike.note_id == note_id,
                NoteLike.is_deleted == False,
            )
        )
        existing = (await self.db.execute(existing_stmt)).scalars().first()

        if existing:
            # 取消点赞
            existing.is_deleted = True
            note.likes = max(0, note.likes - 1)
            liked = False
        else:
            # 点赞
            like = NoteLike(user_id=user_id, note_id=note_id)
            self.db.add(like)
            note.likes = (note.likes or 0) + 1
            liked = True

        await self.db.commit()
        await self.db.refresh(note)
        return LikeResult(note_id=note_id, liked=liked, like_count=note.likes)

    async def comment_note(
        self,
        note_id: int,
        user_id: int,
        username: str,
        level: int,
        content: str,
        parent_id: Optional[int] = None,
    ) -> CommentBrief:
        """评论笔记"""
        note = await self._get_note(note_id)
        if not note:
            raise ValueError(f"笔记 {note_id} 不存在")

        # 如果有父评论，验证存在性
        if parent_id is not None:
            parent_stmt = select(Comment).where(
                and_(
                    Comment.id == parent_id,
                    Comment.note_id == note_id,
                    Comment.is_deleted == False,
                )
            )
            parent = (await self.db.execute(parent_stmt)).scalars().first()
            if not parent:
                raise ValueError(f"父评论 {parent_id} 不存在")

        comment = Comment(
            note_id=note_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
            like_count=0,
        )
        self.db.add(comment)
        note.comment_count = (note.comment_count or 0) + 1
        await self.db.commit()
        await self.db.refresh(comment)

        # 获取作者信息
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        author = _author_from_user(user) if user else AuthorBrief(
            user_id=user_id, username=username, level=level
        )

        return CommentBrief(
            id=comment.id,
            author=author,
            content=content,
            like_count=0,
            parent_id=parent_id,
            created_at=comment.created_at,
            replies=[],
        )

    async def _get_comments_for_note(self, note_id: int) -> List[CommentBrief]:
        """获取笔记的评论树（顶层 + 回复）"""
        # 查询所有评论
        stmt = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)
            .where(
                and_(
                    Comment.note_id == note_id,
                    Comment.is_deleted == False,
                    User.is_deleted == False,
                )
            )
            .order_by(Comment.created_at)
        )
        rows = (await self.db.execute(stmt)).all()

        # 构建评论映射
        comment_map: Dict[int, CommentBrief] = {}
        top_level: List[CommentBrief] = []

        for comment, user in rows:
            author = _author_from_user(user)
            brief = CommentBrief(
                id=comment.id,
                author=author,
                content=comment.content,
                like_count=comment.like_count,
                parent_id=comment.parent_id,
                created_at=comment.created_at,
                replies=[],
            )
            comment_map[comment.id] = brief

        # 组装树结构
        for comment, user in rows:
            brief = comment_map[comment.id]
            if comment.parent_id is not None and comment.parent_id in comment_map:
                comment_map[comment.parent_id].replies.append(brief)
            else:
                top_level.append(brief)

        return top_level

    async def _to_note_brief(
        self, note: Note, current_user_id: Optional[int] = None
    ) -> NoteBrief:
        """将 ORM 对象转为 NoteBrief"""
        # 获取作者
        user_stmt = select(User).where(User.id == note.user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        if user:
            author = _author_from_user(user)
        else:
            author = AuthorBrief(user_id=note.user_id, username=f"user_{note.user_id}")

        # 检查当前用户是否点赞
        is_liked = False
        if current_user_id is not None:
            like_stmt = select(NoteLike.id).where(
                and_(
                    NoteLike.user_id == current_user_id,
                    NoteLike.note_id == note.id,
                    NoteLike.is_deleted == False,
                )
            )
            is_liked = (await self.db.execute(like_stmt)).first() is not None

        return NoteBrief(
            id=note.id,
            title=note.title or "",
            content=note.content,
            excerpt=_excerpt(note.content),
            author=author,
            book_id=note.book_id,
            chapter_id=note.chapter_id,
            verse_text=note.verse_text,
            group_id=note.group_id,
            tags=_parse_tags(note.tags),
            like_count=note.likes,
            comment_count=note.comment_count,
            is_liked=is_liked,
            is_essence=note.is_essence,
            created_at=note.created_at,
        )

    async def _get_note(self, note_id: int) -> Optional[Note]:
        """查询笔记（排除软删除）"""
        stmt = select(Note).where(
            and_(
                Note.id == note_id,
                Note.is_deleted == False,
            )
        )
        return (await self.db.execute(stmt)).scalars().first()

    # ---------- 答题 PK ----------

    async def pk_match(
        self, user_id: int, username: str, level: int, req: PKMatchRequest
    ) -> PKMatchResult:
        """PK 匹配 - 按段位匹配对手"""
        # 获取当前用户 rating
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        my_rating = user.pk_rating if user and user.pk_rating else 1000

        # 从数据库中选一个 rating 接近的对手（排除自己）
        opponent_stmt = (
            select(User)
            .where(
                and_(
                    User.id != user_id,
                    User.is_active == True,
                    User.is_deleted == False,
                )
            )
            .order_by(func.abs(User.pk_rating - my_rating))
            .limit(1)
        )
        opponent = (await self.db.execute(opponent_stmt)).scalars().first()

        if not opponent:
            # 没有其他用户，创建一个虚拟对手
            opponent_name = "AI对手"
            opponent_id = 0
            opponent_level = max(1, my_rating // 100)
        else:
            opponent_name = opponent.username
            opponent_id = opponent.id
            opponent_level = opponent.level

        # 抽题
        pool = list(range(len(_PK_QUESTIONS)))
        random.shuffle(pool)
        selected = pool[: req.question_count]
        questions = []
        for new_idx, orig_idx in enumerate(selected):
            q = _PK_QUESTIONS[orig_idx]
            questions.append(PKQuestion(
                index=new_idx,
                question=q.question,
                options=q.options,
                verse_source=q.verse_source,
            ))

        pk_id = f"pk_{uuid.uuid4().hex[:12]}"

        # 在数据库中创建 PkMatch 记录
        pk_match_record = PkMatch(
            player1_id=user_id,
            player2_id=opponent_id if opponent_id > 0 else None,
            book_id=None,
            question_count=req.question_count,
            status="ongoing",
            player1_score=0,
            player2_score=0,
            winner=None,
            started_at=_utcnow(),
        )
        self.db.add(pk_match_record)
        await self.db.flush()

        # 内存会话暂存题目索引和对手模拟答案
        opponent_answers = self._simulate_opponent_answers(selected)
        _pk_sessions[pk_id] = {
            "pk_id": pk_id,
            "match_db_id": pk_match_record.id,
            "user_id": user_id,
            "opponent_id": opponent_id,
            "opponent_name": opponent_name,
            "opponent_level": opponent_level,
            "question_indices": selected,
            "questions": questions,
            "status": PKStatus.ONGOING,
            "created_at": _utcnow(),
            "opponent_answers": opponent_answers,
        }

        await self.db.commit()

        return PKMatchResult(
            pk_id=pk_id,
            opponent=AuthorBrief(
                user_id=opponent_id,
                username=opponent_name,
                level=opponent_level,
            ),
            questions=questions,
            time_limit_seconds=300,
            status=PKStatus.ONGOING,
        )

    def _simulate_opponent_answers(self, question_indices: List[int]) -> Dict[int, int]:
        """模拟对手答题（正确率约 70%）"""
        answers = {}
        for qi in question_indices:
            if random.random() < 0.7:
                answers[qi] = _PK_ANSWERS[qi]
            else:
                wrong = [i for i in range(4) if i != _PK_ANSWERS[qi]]
                answers[qi] = random.choice(wrong)
        return answers

    async def pk_submit(self, user_id: int, req: PKSubmitRequest) -> PKSettlement:
        """提交 PK 答案并结算"""
        session = _pk_sessions.get(req.pk_id)
        if not session:
            raise ValueError(f"PK 会话 {req.pk_id} 不存在")
        if session["user_id"] != user_id:
            raise ValueError("无权提交此 PK")
        if session["status"] != PKStatus.ONGOING:
            raise ValueError("此 PK 已结束")

        question_indices = session["question_indices"]
        opponent_answers = session["opponent_answers"]

        # 计算我的得分
        my_correct = 0
        for ans in req.answers:
            orig_idx = question_indices[ans.question_index]
            if ans.selected_option == _PK_ANSWERS[orig_idx]:
                my_correct += 1

        # 计算对手得分
        opponent_correct = 0
        for qi in question_indices:
            if opponent_answers.get(qi) == _PK_ANSWERS[qi]:
                opponent_correct += 1

        total = len(question_indices)

        # 时间加分
        time_bonus = max(0, (300 - req.duration_seconds) // 30)
        my_score = my_correct * 10 + time_bonus
        opponent_score = opponent_correct * 10

        if my_score > opponent_score:
            result = PKResult.WIN
        elif my_score < opponent_score:
            result = PKResult.LOSE
        else:
            result = PKResult.DRAW

        # 获取用户
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        my_rating = user.pk_rating if user and user.pk_rating else 1000

        # 对手 rating
        opponent_id = session["opponent_id"]
        if opponent_id > 0:
            opp_stmt = select(User).where(User.id == opponent_id)
            opp_user = (await self.db.execute(opp_stmt)).scalars().first()
            opp_rating = opp_user.pk_rating if opp_user and opp_user.pk_rating else 1000
        else:
            opp_rating = 1000

        # ELO rating 计算
        expected = 1 / (1 + 10 ** ((opp_rating - my_rating) / 400))
        actual = {"win": 1.0, "draw": 0.5, "lose": 0.0}[result.value]
        k = 32
        rating_change = round(k * (actual - expected))
        new_rating = max(0, my_rating + rating_change)

        # 经验奖励
        exp_map = {"win": 50, "draw": 20, "lose": 10}
        exp_gained = exp_map[result.value]

        # 更新用户数据
        if user:
            user.pk_rating = new_rating
            user.exp_points = (user.exp_points or 0) + exp_gained

        # 更新 PkMatch 记录
        match_db_id = session.get("match_db_id")
        if match_db_id:
            match_stmt = select(PkMatch).where(PkMatch.id == match_db_id)
            match = (await self.db.execute(match_stmt)).scalars().first()
            if match:
                match.player1_score = my_score
                match.player2_score = opponent_score
                match.winner = 1 if result == PKResult.WIN else (2 if result == PKResult.LOSE else 0)
                match.status = "completed"
                match.ended_at = _utcnow()

        await self.db.commit()

        # 标记会话结束
        session["status"] = PKStatus.FINISHED
        session["result"] = result
        session["my_score"] = my_score
        session["opponent_score"] = opponent_score

        # 清理会话（保留一段时间供查询，简单起见保留）
        # del _pk_sessions[req.pk_id]

        return PKSettlement(
            pk_id=req.pk_id,
            my_score=my_score,
            opponent_score=opponent_score,
            result=result,
            correct_count=my_correct,
            total_count=total,
            exp_gained=exp_gained,
            rating_change=rating_change,
            new_rating=new_rating,
        )

    # ---------- 排行榜 ----------

    async def get_leaderboard(
        self,
        scope: LeaderboardScope,
        metric: str = "exp",
        current_user_id: Optional[int] = None,
        limit: int = 50,
    ) -> LeaderboardResponse:
        """
        排行榜
        metric: exp（经验值）| checkin（打卡天数）| pk_rating（PK 段位）
        """
        # 基础查询：活跃且未删除的用户
        base_conditions = [
            User.is_active == True,
            User.is_deleted == False,
        ]

        if metric == "checkin":
            # 打卡天数排行（用 total_study_days 或 streak_days）
            # 这里用 total_study_days 作为累计打卡天数
            score_field = User.total_study_days
            score_label = "连续打卡天数"
        elif metric == "pk_rating":
            score_field = User.pk_rating
            score_label = "PK 段位分"
        else:
            score_field = User.exp_points
            score_label = "经验值"

        # 范围过滤（简化：week/month 用最近 checkin 时间近似）
        now = _utcnow()
        if scope == LeaderboardScope.WEEK:
            week_ago = now - timedelta(days=7)
            # 子查询：最近7天有打卡记录的用户
            recent_users_stmt = (
                select(Checkin.user_id)
                .where(
                    and_(
                        Checkin.checkin_date >= week_ago.date(),
                        Checkin.is_deleted == False,
                    )
                )
                .distinct()
            )
            base_conditions.append(User.id.in_(recent_users_stmt))
        elif scope == LeaderboardScope.MONTH:
            month_ago = now - timedelta(days=30)
            recent_users_stmt = (
                select(Checkin.user_id)
                .where(
                    and_(
                        Checkin.checkin_date >= month_ago.date(),
                        Checkin.is_deleted == False,
                    )
                )
                .distinct()
            )
            base_conditions.append(User.id.in_(recent_users_stmt))

        stmt = (
            select(User)
            .where(and_(*base_conditions))
            .order_by(score_field.desc())
            .limit(limit)
        )
        users = (await self.db.execute(stmt)).scalars().all()

        entries = []
        my_rank = None
        my_score = None

        for idx, u in enumerate(users):
            rank = idx + 1
            score = int(getattr(u, score_field.key) or 0)

            if u.id == current_user_id:
                my_rank = rank
                my_score = score

            extra = None
            if metric == "pk_rating":
                extra = _rating_tier(score)
            elif metric == "checkin":
                extra = f"连续{score}天"

            entries.append(LeaderboardEntry(
                rank=rank,
                user_id=u.id,
                username=u.username,
                nickname=u.nickname,
                avatar=u.avatar,
                level=u.level,
                score=score,
                score_label=score_label,
                extra=extra,
            ))

        # 如果当前用户不在榜单中，单独查询其排名
        if my_rank is None and current_user_id is not None:
            current_stmt = select(User).where(
                and_(
                    User.id == current_user_id,
                    User.is_deleted == False,
                )
            )
            current_user = (await self.db.execute(current_stmt)).scalars().first()
            if current_user:
                my_score = int(getattr(current_user, score_field.key) or 0)
                # 计算排名：分数高于当前用户的用户数 + 1
                rank_stmt = select(func.count(User.id)).where(
                    and_(
                        User.is_active == True,
                        User.is_deleted == False,
                        score_field > my_score,
                    )
                )
                higher_count = int((await self.db.execute(rank_stmt)).scalar() or 0)
                my_rank = higher_count + 1

        return LeaderboardResponse(
            scope=scope,
            metric=metric,
            my_rank=my_rank,
            my_score=my_score,
            entries=entries,
        )

"""
悟典 - 学习进度服务
闯关进度管理、关卡解锁逻辑、每日学习目标跟踪。

适配现有 Progress 模型字段:
  - status: not_started / learning / reviewed / mastered
  - mastery_level: 0.0 - 1.0
  - study_count, study_duration, last_reviewed, next_review_date

通关定义: status == "mastered" (mastery_level >= 1.0)
通关条件: 完成阅读 + 通过测验(正确率≥70%) -> mastery_level 累加至 1.0
"""
from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classic import ClassicBook, Chapter, Verse
from app.models.progress import Progress
from app.models.user import User


# mastery_level 阶段
MASTERY_READ = 0.5      # 完成阅读
MASTERY_QUIZ_PASS = 0.8  # 测验通过
MASTERY_COMPLETE = 1.0   # 完全通关


class ProgressService:
    """学习进度服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 闯关课程树 ----------

    async def get_chapter_tree(self, user_id: int, book_id: Optional[int] = None) -> list[dict]:
        """
        获取闯关课程树。
        结构: 书 -> 章(大关) -> 小节(小关，含经文数与用户完成状态)
        解锁逻辑: 前一章全部通关后，下一章解锁。
        """
        # 查询书籍
        book_stmt = select(ClassicBook).where(
            ClassicBook.is_deleted == False
        ).order_by(ClassicBook.sort_order, ClassicBook.id)
        if book_id is not None:
            book_stmt = book_stmt.where(ClassicBook.id == book_id)
        books = (await self.db.execute(book_stmt)).scalars().all()

        tree: list[dict] = []
        for book in books:
            # 章节
            ch_stmt = (
                select(Chapter)
                .where(
                    and_(
                        Chapter.book_id == book.id,
                        Chapter.is_deleted == False,
                    )
                )
                .order_by(Chapter.chapter_number)
            )
            chapters = (await self.db.execute(ch_stmt)).scalars().all()

            chapter_list: list[dict] = []
            prev_unlocked = True  # 第一章默认解锁
            for ch in chapters:
                # 统计该章经文总数
                verse_count_stmt = select(func.count(Verse.id)).where(
                    and_(
                        Verse.chapter_id == ch.id,
                        Verse.is_deleted == False,
                    )
                )
                verse_count = int((await self.db.execute(verse_count_stmt)).scalar() or 0)

                # 统计该章用户已通关数 (status == mastered)
                completed_stmt = select(func.count(Progress.id)).where(
                    and_(
                        Progress.user_id == user_id,
                        Progress.chapter_id == ch.id,
                        Progress.status == "mastered",
                        Progress.is_deleted == False,
                    )
                )
                completed_count = int((await self.db.execute(completed_stmt)).scalar() or 0)

                is_unlocked = prev_unlocked
                is_completed = verse_count > 0 and completed_count >= verse_count

                chapter_list.append({
                    "chapter_id": ch.id,
                    "chapter_number": ch.chapter_number,
                    "title": ch.title,
                    "description": ch.description,
                    "verse_count": verse_count,
                    "completed_count": completed_count,
                    "is_unlocked": is_unlocked,
                    "is_completed": is_completed,
                    "progress_pct": round(completed_count / verse_count * 100, 1) if verse_count else 0,
                })
                prev_unlocked = is_completed  # 下一章是否解锁取决于本章是否全部通关

            tree.append({
                "book_id": book.id,
                "title": book.title,
                "category": book.category,
                "description": book.description,
                "chapters": chapter_list,
            })
        return tree

    # ---------- 完成一章学习 ----------

    async def complete_verse(
        self,
        user_id: int,
        verse_id: int,
        *,
        read_completed: bool = True,
        study_duration: int = 0,
    ) -> Progress:
        """
        标记一条经文为"已完成阅读"。
        mastery_level: 完成阅读 -> 0.5；测验通过 -> 0.8；两者皆完成 -> 1.0 (mastered)
        """
        verse = await self._get_verse(verse_id)
        if verse is None:
            raise ValueError(f"经文 {verse_id} 不存在")

        progress = await self.get_or_create_progress(user_id, verse_id, verse.book_id, verse.chapter_id)

        progress.study_count += 1
        if study_duration > 0:
            progress.study_duration += study_duration
        progress.last_reviewed = datetime.now(timezone.utc)

        if read_completed:
            # 至少达到阅读完成水平
            if progress.mastery_level < MASTERY_READ:
                progress.mastery_level = MASTERY_READ
            if progress.status == "not_started":
                progress.status = "learning"
            elif progress.status == "learning":
                progress.status = "reviewed"

            # 若测验已通过 -> 通关
            if progress.mastery_level >= MASTERY_QUIZ_PASS:
                progress.mastery_level = MASTERY_COMPLETE
                progress.status = "mastered"
                progress.next_review_date = None
        else:
            if progress.status == "not_started":
                progress.status = "learning"

        await self.db.flush()
        await self._sync_user_stats(user_id)
        return progress

    async def mark_quiz_passed(self, user_id: int, verse_id: int, score: int) -> Progress:
        """标记测验通过(正确率≥70%)，更新通关状态。"""
        verse = await self._get_verse(verse_id)
        if verse is None:
            raise ValueError(f"经文 {verse_id} 不存在")

        progress = await self.get_or_create_progress(user_id, verse_id, verse.book_id, verse.chapter_id)

        if score >= 70:
            # 测验通过
            if progress.mastery_level < MASTERY_QUIZ_PASS:
                progress.mastery_level = MASTERY_QUIZ_PASS
            # 若阅读也完成 -> 通关
            if progress.mastery_level >= MASTERY_READ:
                progress.mastery_level = MASTERY_COMPLETE
                progress.status = "mastered"
                progress.next_review_date = None
            else:
                progress.status = "reviewed"
        else:
            # 测验未通过，保持学习状态
            if progress.status == "not_started":
                progress.status = "learning"

        await self.db.flush()
        await self._sync_user_stats(user_id)
        return progress

    async def get_or_create_progress(
        self, user_id: int, verse_id: int, book_id: int, chapter_id: int
    ) -> Progress:
        stmt = select(Progress).where(
            and_(
                Progress.user_id == user_id,
                Progress.verse_id == verse_id,
                Progress.is_deleted == False,
            )
        )
        progress = (await self.db.execute(stmt)).scalars().first()
        if progress is None:
            progress = Progress(
                user_id=user_id,
                book_id=book_id,
                chapter_id=chapter_id,
                verse_id=verse_id,
                status="not_started",
                mastery_level=0.0,
                study_count=0,
                study_duration=0,
            )
            self.db.add(progress)
            await self.db.flush()
        return progress

    # ---------- 每日学习目标 ----------

    async def get_daily_goal_status(self, user_id: int, target_date: date | None = None) -> dict:
        """获取当日学习目标完成状态。默认目标: 学习3条经文 / 复习10条。"""
        if target_date is None:
            target_date = date.today()

        start = datetime.combine(target_date, datetime.min.time()).astimezone(timezone.utc)
        end = start + timedelta(days=1)

        # 当日新学经文数 (当天 last_reviewed 落在今日 且 status != not_started)
        learned_stmt = select(func.count(Progress.id)).where(
            and_(
                Progress.user_id == user_id,
                Progress.is_deleted == False,
                Progress.last_reviewed.isnot(None),
                Progress.last_reviewed >= start,
                Progress.last_reviewed < end,
                Progress.status != "not_started",
            )
        )
        learned_today = int((await self.db.execute(learned_stmt)).scalar() or 0)

        return {
            "date": target_date.isoformat(),
            "learned_today": learned_today,
            "learn_target": 3,
            "learn_achieved": learned_today >= 3,
        }

    async def _sync_user_stats(self, user_id: int) -> None:
        """同步用户的 total_verses_learned 字段。"""
        count_stmt = select(func.count(Progress.id)).where(
            and_(
                Progress.user_id == user_id,
                Progress.status == "mastered",
                Progress.is_deleted == False,
            )
        )
        total = int((await self.db.execute(count_stmt)).scalar() or 0)
        await self.db.execute(
            update(User).where(User.id == user_id).values(
                total_verses_learned=total,
                last_study_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()

    async def get_overall_progress(self, user_id: int) -> dict:
        """获取用户总体学习进度概览。"""
        # 已通关经文数
        completed_stmt = select(func.count(Progress.id)).where(
            and_(
                Progress.user_id == user_id,
                Progress.status == "mastered",
                Progress.is_deleted == False,
            )
        )
        completed = int((await self.db.execute(completed_stmt)).scalar() or 0)

        # 全平台经文总数
        total_verses_stmt = select(func.count(Verse.id)).where(Verse.is_deleted == False)
        total_verses = int((await self.db.execute(total_verses_stmt)).scalar() or 0)

        # 已通关章节数 (该章所有经文都通关)
        chapters_stmt = (
            select(Progress.chapter_id)
            .where(
                and_(
                    Progress.user_id == user_id,
                    Progress.status == "mastered",
                    Progress.is_deleted == False,
                )
            )
            .distinct()
        )
        chapters_count = len((await self.db.execute(chapters_stmt)).scalars().all())

        return {
            "verses_completed": completed,
            "total_verses": total_verses,
            "chapters_touched": chapters_count,
            "completion_pct": round(completed / total_verses * 100, 2) if total_verses else 0,
        }

    async def _get_verse(self, verse_id: int) -> Optional[Verse]:
        stmt = select(Verse).where(Verse.id == verse_id)
        return (await self.db.execute(stmt)).scalars().first()

"""
悟典 - SRS 间隔复习服务
封装 SM-2 算法与数据库交互，提供到期复习查询、复习结果提交等能力。

适配现有 SrsRecord 模型字段:
  - ease_factor, interval_days, repetitions
  - last_review_date (Date), next_review_date (Date)
  - last_rating (0-5), total_reviews, lapse_count, status
"""
from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.srs_record import SrsRecord
from app.models.classic import Verse
from app.utils.srs_algorithm import sm2, SRSResult, quality_from_correctness
from app.core.config import settings


class SRSService:
    """SRS 间隔复习服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_next_review(
        self,
        quality: int,
        repetitions: int,
        ease_factor: float,
        interval: int,
        *,
        now: datetime | None = None,
    ) -> SRSResult:
        """根据用户答题质量(0-5)，计算下次复习参数。纯计算，不落库。"""
        return sm2(
            quality=quality,
            repetitions=repetitions,
            ease_factor=ease_factor,
            interval_days=interval,
            now=now,
        )

    async def get_due_reviews(
        self,
        user_id: int,
        *,
        limit: int = 50,
        today: date | None = None,
    ) -> list[SrsRecord]:
        """获取用户今日待复习的内容 (已到期或逾期)。"""
        if today is None:
            today = date.today()

        stmt = (
            select(SrsRecord)
            .where(
                and_(
                    SrsRecord.user_id == user_id,
                    SrsRecord.is_deleted == False,
                    SrsRecord.next_review_date <= today,
                )
            )
            .order_by(SrsRecord.next_review_date.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_due_count(self, user_id: int, *, today: date | None = None) -> int:
        """获取用户今日待复习数量。"""
        if today is None:
            today = date.today()
        stmt = (
            select(func.count(SrsRecord.id))
            .where(
                and_(
                    SrsRecord.user_id == user_id,
                    SrsRecord.is_deleted == False,
                    SrsRecord.next_review_date <= today,
                )
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)

    async def get_or_create_record(self, user_id: int, verse_id: int) -> SrsRecord:
        """获取或创建某条经文的 SRS 记录。新记录的 next_review_date 为今天(立即可复习)。"""
        stmt = select(SrsRecord).where(
            and_(
                SrsRecord.user_id == user_id,
                SrsRecord.verse_id == verse_id,
                SrsRecord.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if record is None:
            record = SrsRecord(
                user_id=user_id,
                verse_id=verse_id,
                repetitions=0,
                ease_factor=settings.SRS_INITIAL_EASE_FACTOR,
                interval_days=1,
                next_review_date=date.today(),
                last_review_date=None,
                total_reviews=0,
                last_rating=None,
                lapse_count=0,
                status="new",
            )
            self.db.add(record)
            await self.db.flush()
        return record

    async def submit_review(
        self,
        user_id: int,
        verse_id: int,
        quality: int,
    ) -> SRSResult:
        """
        提交一次复习结果，更新 SRS 记录。

        参数:
            quality: 答题质量 0-5 (前端可简化为 correct/incorrect)
        返回:
            SRSResult: 计算后的下次复习参数
        """
        record = await self.get_or_create_record(user_id, verse_id)

        result = self.calculate_next_review(
            quality=quality,
            repetitions=record.repetitions,
            ease_factor=record.ease_factor,
            interval=record.interval_days,
        )

        now = datetime.now(timezone.utc)

        # 落库更新
        record.repetitions = result.repetitions
        record.ease_factor = result.ease_factor
        record.interval_days = result.interval_days
        # next_review_date 是 Date 类型，取 datetime 的 date 部分
        record.next_review_date = result.next_review_at.date()
        record.last_review_date = now.date()
        record.total_reviews += 1
        record.last_rating = quality

        if result.is_relearn:
            record.lapse_count += 1
            record.status = "relearning"
        else:
            if result.repetitions >= 3 and result.interval_days >= 21:
                record.status = "review"
            else:
                record.status = "learning"

        await self.db.flush()
        return result

    async def submit_review_simple(
        self,
        user_id: int,
        verse_id: int,
        is_correct: bool,
        hesitation_seconds: float = 0.0,
    ) -> SRSResult:
        """简化版复习提交：前端只传对/错与犹豫时间，内部映射为 quality。"""
        quality = quality_from_correctness(is_correct, hesitation_seconds=hesitation_seconds)
        return await self.submit_review(user_id, verse_id, quality)

    async def get_review_stats(self, user_id: int) -> dict:
        """获取用户复习统计：待复习数、已掌握数、总复习数等。"""
        today = date.today()

        # 待复习
        due_count = await self.get_due_count(user_id, today=today)

        # 已掌握 (repetitions >= 3 且 interval >= 21 天)
        mastered_stmt = (
            select(func.count(SrsRecord.id))
            .where(
                and_(
                    SrsRecord.user_id == user_id,
                    SrsRecord.is_deleted == False,
                    SrsRecord.repetitions >= 3,
                    SrsRecord.interval_days >= 21,
                )
            )
        )
        mastered_result = await self.db.execute(mastered_stmt)
        mastered_count = int(mastered_result.scalar() or 0)

        # 学习中 (有 SRS 记录但未掌握)
        learning_stmt = (
            select(func.count(SrsRecord.id))
            .where(
                and_(
                    SrsRecord.user_id == user_id,
                    SrsRecord.is_deleted == False,
                )
            )
        )
        learning_result = await self.db.execute(learning_stmt)
        total_in_srs = int(learning_result.scalar() or 0)

        # 今日已复习
        reviewed_today_stmt = (
            select(func.count(SrsRecord.id))
            .where(
                and_(
                    SrsRecord.user_id == user_id,
                    SrsRecord.is_deleted == False,
                    SrsRecord.last_review_date == today,
                )
            )
        )
        reviewed_today_result = await self.db.execute(reviewed_today_stmt)
        reviewed_today = int(reviewed_today_result.scalar() or 0)

        return {
            "due_count": due_count,
            "mastered_count": mastered_count,
            "learning_count": max(0, total_in_srs - mastered_count),
            "reviewed_today": reviewed_today,
            "total_in_srs": total_in_srs,
        }

"""
悟典 - 连续打卡服务
streak 计算、断签处理、护级(补签)机制、每日推送时机管理。
"""
from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import Checkin
from app.models.user import User


# 断签宽限期(小时): 超过 24 小时未打卡则 streak 清零
STREAK_GRACE_HOURS = 24
# 补签道具: 每月最多补签次数
MONTHLY_MAKEUP_LIMIT = 3


class StreakService:
    """连续打卡服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def checkin(
        self,
        user_id: int,
        *,
        target_date: date | None = None,
        verses_learned: int = 0,
        study_duration: int = 0,
        exp_gained: int = 0,
        note: str | None = None,
        is_makeup: bool = False,
    ) -> Checkin:
        """
        执行打卡。若当日已打卡则更新记录。
        打卡后刷新用户的 streak_days。
        """
        if target_date is None:
            target_date = date.today()

        # 查询是否已打卡
        existing = await self._get_checkin(user_id, target_date)
        if existing:
            # 更新
            existing.verses_learned = max(existing.verses_learned, verses_learned)
            existing.study_duration = max(existing.study_duration, study_duration)
            existing.exp_gained = max(existing.exp_gained, exp_gained)
            if note:
                existing.note = note
            await self.db.flush()
            await self._update_user_streak(user_id, target_date)
            return existing

        checkin = Checkin(
            user_id=user_id,
            checkin_date=target_date,
            verses_learned=verses_learned,
            study_duration=study_duration,
            exp_gained=exp_gained,
            is_makeup=is_makeup,
            note=note,
        )
        self.db.add(checkin)
        await self.db.flush()

        await self._update_user_streak(user_id, target_date)
        return checkin

    async def makeup_checkin(self, user_id: int, target_date: date, note: str | None = None) -> Checkin:
        """
        补签(护级机制): 为过去某天补打卡。
        限制: 每月最多 MONTHLY_MAKEUP_LIMIT 次，且只能补过去 7 天内。
        """
        today = date.today()
        if target_date >= today:
            raise ValueError("补签日期必须是过去的日期")
        if (today - target_date).days > 7:
            raise ValueError("仅可补签最近 7 天内的打卡")

        # 当月已补签次数
        month_start = today.replace(day=1)
        makeup_count_stmt = select(func.count(Checkin.id)).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.is_makeup == True,
                Checkin.checkin_date >= month_start,
                Checkin.is_deleted == False,
            )
        )
        makeup_count = int((await self.db.execute(makeup_count_stmt)).scalar() or 0)
        if makeup_count >= MONTHLY_MAKEUP_LIMIT:
            raise ValueError(f"本月补签次数已达上限({MONTHLY_MAKEUP_LIMIT}次)")

        return await self.checkin(
            user_id,
            target_date=target_date,
            is_makeup=True,
            note=note or "补签",
        )

    async def get_streak(self, user_id: int) -> dict:
        """获取用户当前连续打卡天数与历史信息。"""
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        if user is None:
            raise ValueError(f"用户 {user_id} 不存在")

        streak = user.streak_days or 0
        total_days = user.total_study_days or 0

        # 今日是否已打卡
        today_checkin = await self._get_checkin(user_id, date.today())
        checked_in_today = today_checkin is not None

        # 计算是否处于断签风险 (距上次打卡 > 24 小时但 < 48 小时)
        at_risk = False
        last_study = user.last_study_at
        if last_study and not checked_in_today:
            now_utc = datetime.now(timezone.utc)
            hours_since = (now_utc - last_study).total_seconds() / 3600
            if STREAK_GRACE_HOURS <= hours_since < 48:
                at_risk = True

        # 最近 7 天打卡情况
        recent = await self.get_recent_checkins(user_id, days=7)

        return {
            "streak_days": streak,
            "total_study_days": total_days,
            "checked_in_today": checked_in_today,
            "at_risk": at_risk,
            "last_study_at": user.last_study_at.isoformat() if user.last_study_at else None,
            "recent_7_days": recent,
            "grace_hours": STREAK_GRACE_HOURS,
        }

    async def get_recent_checkins(self, user_id: int, days: int = 7) -> list[dict]:
        """获取最近 N 天的打卡记录。"""
        start_date = date.today() - timedelta(days=days - 1)
        stmt = (
            select(Checkin)
            .where(
                and_(
                    Checkin.user_id == user_id,
                    Checkin.is_deleted == False,
                    Checkin.checkin_date >= start_date,
                )
            )
            .order_by(Checkin.checkin_date.desc())
        )
        records = (await self.db.execute(stmt)).scalars().all()
        return [
            {
                "date": r.checkin_date.isoformat(),
                "verses_learned": r.verses_learned,
                "study_duration": r.study_duration,
                "exp_gained": r.exp_gained,
                "is_makeup": r.is_makeup,
            }
            for r in records
        ]

    async def _update_user_streak(self, user_id: int, checkin_date: date) -> int:
        """
        根据打卡日期更新用户的 streak_days。
        规则:
          - 若是连续的下一天 (昨天 streak + 1)
          - 若是同一天补打卡，不增加
          - 若中间断了一天且非补签 -> 若断签超过宽限期则重置为 1，否则补连
        """
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        if user is None:
            return 0

        yesterday = checkin_date - timedelta(days=1)

        # 查询昨天是否打卡
        yesterday_checkin = await self._get_checkin(user_id, yesterday)

        if yesterday_checkin:
            # 连续打卡
            new_streak = (user.streak_days or 0) + 1
        else:
            # 昨天没打卡
            any_checkin_stmt = select(func.count(Checkin.id)).where(
                and_(
                    Checkin.user_id == user_id,
                    Checkin.is_deleted == False,
                )
            )
            total_checkins = int((await self.db.execute(any_checkin_stmt)).scalar() or 0)
            if total_checkins <= 1:
                new_streak = 1
            else:
                # 断签: 检查是否在宽限期内 (有 last_study_at)
                new_streak = 1  # 默认重置
                if user.last_study_at:
                    now_utc = datetime.now(timezone.utc)
                    hours_since = (now_utc - user.last_study_at).total_seconds() / 3600
                    if hours_since <= STREAK_GRACE_HOURS:
                        # 宽限期内，继续 streak
                        new_streak = (user.streak_days or 0) + 1

        user.streak_days = new_streak
        # total_study_days 仅在该日期首次打卡时 +1
        already_counted = await self._already_counted_today(user_id, checkin_date)
        if not already_counted:
            user.total_study_days = (user.total_study_days or 0) + 1
        user.last_study_at = datetime.now(timezone.utc)
        await self.db.flush()
        return new_streak

    async def _already_counted_today(self, user_id: int, checkin_date: date) -> bool:
        """检查该日期是否已经计入 total_study_days (即之前已有打卡记录)。"""
        stmt = select(func.count(Checkin.id)).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.checkin_date == checkin_date,
                Checkin.is_deleted == False,
            )
        )
        count = int((await self.db.execute(stmt)).scalar() or 0)
        return count > 1  # 当前这次还没 flush，>1 表示之前已有

    async def _get_checkin(self, user_id: int, target_date: date) -> Optional[Checkin]:
        stmt = select(Checkin).where(
            and_(
                Checkin.user_id == user_id,
                Checkin.checkin_date == target_date,
                Checkin.is_deleted == False,
            )
        )
        return (await self.db.execute(stmt)).scalars().first()

    # ---------- 每日推送时机 ----------

    async def get_reminder_time(self, user_id: int) -> dict:
        """
        获取每日打卡提醒时机。
        策略:
          - 默认晚上 21:00 (学习黄金时段)
          - 若用户常在固定时段打卡，学习该时段
          - 若今日未打卡且接近断签，提前提醒
        """
        stmt = (
            select(Checkin)
            .where(
                and_(
                    Checkin.user_id == user_id,
                    Checkin.is_deleted == False,
                )
            )
            .order_by(Checkin.checkin_date.desc())
            .limit(30)
        )
        records = (await self.db.execute(stmt)).scalars().all()

        default_time = "21:00"
        if len(records) < 3:
            suggested_time = default_time
        else:
            hour_counts: dict[int, int] = {}
            for r in records:
                if r.created_at:
                    h = r.created_at.hour
                    hour_counts[h] = hour_counts.get(h, 0) + 1
            if hour_counts:
                best_hour = max(hour_counts, key=hour_counts.get)
                suggested_time = f"{best_hour:02d}:00"
            else:
                suggested_time = default_time

        today_checkin = await self._get_checkin(user_id, date.today())
        need_early_reminder = today_checkin is None

        return {
            "suggested_time": suggested_time,
            "default_time": default_time,
            "need_early_reminder": need_early_reminder,
        }

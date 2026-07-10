"""
悟典 - 成就体系服务
经验值计算、段位系统(童生→秀才→举人→进士→翰林)、徽章系统、成就触发检查。

适配现有 Achievement 模型字段:
  - badge_type (唯一标识), badge_name, badge_icon, description, tier, exp_reward
  - created_at 作为解锁时间 (TimestampMixin)

适配现有 QuizRecord 模型字段:
  - is_correct: Integer (0/1)
  - 无 verse_id 字段
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.achievement import Achievement
from app.models.checkin import Checkin
from app.models.quiz import QuizRecord
from app.models.progress import Progress
from app.models.user import User


# ---------- 段位系统 ----------
# 童生 → 秀才 → 举人 → 进士 → 翰林
RANKS = [
    {"code": "tongsheng", "name": "童生", "min_exp": 0,      "icon": "🎓"},
    {"code": "xiucai",    "name": "秀才", "min_exp": 500,    "icon": "📖"},
    {"code": "juren",     "name": "举人", "min_exp": 2000,   "icon": "📜"},
    {"code": "jinshi",    "name": "进士", "min_exp": 6000,   "icon": "🏛️"},
    {"code": "hanlin",    "name": "翰林", "min_exp": 15000,  "icon": "👑"},
]


# ---------- 成就定义 ----------
# badge_type 作为唯一标识；type 是分类用于前端分组
ACHIEVEMENT_DEFS = [
    # 学习类
    {"badge_type": "first_verse",    "type": "learning",   "badge_name": "初窥门径",   "description": "完成第一章经文学习",     "badge_icon": "🌱", "tier": "bronze",   "exp_reward": 50},
    {"badge_type": "ten_verses",     "type": "learning",   "badge_name": "渐入佳境",   "description": "完成 10 章经文学习",     "badge_icon": "🌿", "tier": "silver",   "exp_reward": 100},
    {"badge_type": "lunyu_complete", "type": "learning",   "badge_name": "通读论语",   "description": "完成《论语》全部 20 篇", "badge_icon": "📚", "tier": "platinum", "exp_reward": 1000},
    # 打卡类
    {"badge_type": "streak_1",       "type": "streak",     "badge_name": "初心不忘",   "description": "连续打卡 1 天",          "badge_icon": "🔥", "tier": "bronze",   "exp_reward": 10},
    {"badge_type": "streak_7",       "type": "streak",     "badge_name": "一周不辍",   "description": "连续打卡 7 天",          "badge_icon": "⚡", "tier": "silver",   "exp_reward": 100},
    {"badge_type": "streak_30",      "type": "streak",     "badge_name": "月度坚持",   "description": "连续打卡 30 天",         "badge_icon": "🌟", "tier": "gold",     "exp_reward": 500},
    {"badge_type": "streak_100",     "type": "streak",     "badge_name": "百日筑基",   "description": "连续打卡 100 天",        "badge_icon": "🏆", "tier": "platinum", "exp_reward": 2000},
    # 测验类
    {"badge_type": "first_perfect",  "type": "quiz",       "badge_name": "初露锋芒",   "description": "首次测验满分",          "badge_icon": "💯", "tier": "silver",   "exp_reward": 100},
    {"badge_type": "streak_perfect10","type": "quiz",      "badge_name": "连战连捷",   "description": "连续 10 次测验满分",     "badge_icon": "🗡️", "tier": "gold",     "exp_reward": 500},
    # 探索类
    {"badge_type": "dialogue_10",    "type": "exploration","badge_name": "与圣贤言",   "description": "与圣贤对话 10 次",       "badge_icon": "💬", "tier": "silver",   "exp_reward": 200},
    {"badge_type": "graph_browse",   "type": "exploration","badge_name": "博观约取",   "description": "浏览知识图谱全章",       "badge_icon": "🗺️", "tier": "silver",   "exp_reward": 150},
]

# 成就 type -> badge_type 前缀映射(用于查询分组)
TYPE_BY_BADGE = {d["badge_type"]: d["type"] for d in ACHIEVEMENT_DEFS}

# 经验值获取规则
EXP_RULES = {
    "complete_verse": 20,    # 完成一条经文
    "quiz_pass": 30,         # 测验通过
    "quiz_perfect": 50,      # 测验满分
    "checkin": 10,           # 每日打卡
    "streak_bonus_7": 100,   # 7天连续额外奖励
    "review": 5,             # 完成一次复习
    "dialogue": 20,          # 与圣贤对话
}


class AchievementService:
    """成就体系服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 经验值 ----------

    async def add_exp(self, user_id: int, amount: int, reason: str = "") -> int:
        """给用户增加经验值，返回新的总经验值。"""
        if amount <= 0:
            return await self._get_user_exp(user_id)
        await self.db.execute(
            update(User).where(User.id == user_id).values(
                exp_points=User.exp_points + amount
            )
        )
        await self.db.flush()
        new_exp = await self._get_user_exp(user_id)
        await self._update_level(user_id, new_exp)
        return new_exp

    async def _get_user_exp(self, user_id: int) -> int:
        stmt = select(User.exp_points).where(User.id == user_id)
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def _update_level(self, user_id: int, exp: int) -> None:
        """根据经验值更新用户 level 字段(对应段位序号)。"""
        level = 1
        for i, rank in enumerate(RANKS):
            if exp >= rank["min_exp"]:
                level = i + 1
        await self.db.execute(
            update(User).where(User.id == user_id).values(level=level)
        )
        await self.db.flush()

    # ---------- 段位 ----------

    async def get_rank(self, user_id: int) -> dict:
        """获取用户当前段位与晋升进度。"""
        exp = await self._get_user_exp(user_id)
        current_rank = RANKS[0]
        next_rank = None
        for i, rank in enumerate(RANKS):
            if exp >= rank["min_exp"]:
                current_rank = rank
                next_rank = RANKS[i + 1] if i + 1 < len(RANKS) else None

        progress_pct = 100.0
        exp_to_next = 0
        if next_rank:
            span = next_rank["min_exp"] - current_rank["min_exp"]
            gained = exp - current_rank["min_exp"]
            progress_pct = round(gained / span * 100, 1) if span > 0 else 100.0
            exp_to_next = next_rank["min_exp"] - exp

        return {
            "current_rank": current_rank,
            "next_rank": next_rank,
            "exp": exp,
            "exp_to_next": exp_to_next,
            "progress_pct": progress_pct,
            "all_ranks": RANKS,
        }

    # ---------- 成就解锁 ----------

    async def unlock(self, user_id: int, badge_type: str) -> Optional[Achievement]:
        """解锁某个成就(若已解锁则跳过)。返回解锁记录或 None。"""
        # 检查是否已解锁
        existing_stmt = select(Achievement).where(
            and_(
                Achievement.user_id == user_id,
                Achievement.badge_type == badge_type,
                Achievement.is_deleted == False,
            )
        )
        existing = (await self.db.execute(existing_stmt)).scalars().first()
        if existing:
            return None

        defn = next((a for a in ACHIEVEMENT_DEFS if a["badge_type"] == badge_type), None)
        if defn is None:
            return None

        achievement = Achievement(
            user_id=user_id,
            badge_type=defn["badge_type"],
            badge_name=defn["badge_name"],
            badge_icon=defn["badge_icon"],
            description=defn["description"],
            tier=defn["tier"],
            exp_reward=defn["exp_reward"],
        )
        self.db.add(achievement)
        await self.db.flush()

        if defn["exp_reward"] > 0:
            await self.add_exp(user_id, defn["exp_reward"], reason=f"成就:{defn['badge_name']}")

        return achievement

    async def get_user_achievements(self, user_id: int) -> dict:
        """获取用户成就列表(已解锁 + 未解锁)。"""
        unlocked_stmt = select(Achievement).where(
            and_(
                Achievement.user_id == user_id,
                Achievement.is_deleted == False,
            )
        ).order_by(Achievement.created_at.desc())
        unlocked = (await self.db.execute(unlocked_stmt)).scalars().all()
        unlocked_types = {a.badge_type for a in unlocked}

        all_defs = []
        for defn in ACHIEVEMENT_DEFS:
            unlocked_at = next(
                (a.created_at.isoformat() for a in unlocked if a.badge_type == defn["badge_type"]),
                None,
            )
            all_defs.append({
                "code": defn["badge_type"],
                "type": defn["type"],
                "name": defn["badge_name"],
                "description": defn["description"],
                "icon": defn["badge_icon"],
                "tier": defn["tier"],
                "exp_reward": defn["exp_reward"],
                "unlocked": defn["badge_type"] in unlocked_types,
                "unlocked_at": unlocked_at,
            })

        return {
            "total": len(ACHIEVEMENT_DEFS),
            "unlocked_count": len(unlocked),
            "achievements": all_defs,
        }

    # ---------- 成就触发检查 ----------

    async def check_achievements(self, user_id: int) -> list[dict]:
        """
        综合检查并触发所有成就。返回本次新解锁的成就列表。
        在关键事件(完成经文/打卡/测验)后调用。
        """
        newly_unlocked: list[dict] = []

        # ---- 学习类 ----
        completed_count = await self._count_completed_verses(user_id)
        if completed_count >= 1:
            a = await self.unlock(user_id, "first_verse")
            if a:
                newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})
        if completed_count >= 10:
            a = await self.unlock(user_id, "ten_verses")
            if a:
                newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})
        if await self._is_lunyu_complete(user_id):
            a = await self.unlock(user_id, "lunyu_complete")
            if a:
                newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})

        # ---- 打卡类 ----
        streak = await self._get_user_streak(user_id)
        for threshold, code in [(1, "streak_1"), (7, "streak_7"), (30, "streak_30"), (100, "streak_100")]:
            if streak >= threshold:
                a = await self.unlock(user_id, code)
                if a:
                    newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})

        # ---- 测验类 ----
        perfect_count = await self._count_perfect_quizzes(user_id)
        consecutive_perfect = await self._count_consecutive_perfect(user_id)
        if perfect_count >= 1:
            a = await self.unlock(user_id, "first_perfect")
            if a:
                newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})
        if consecutive_perfect >= 10:
            a = await self.unlock(user_id, "streak_perfect10")
            if a:
                newly_unlocked.append({"code": a.badge_type, "name": a.badge_name, "exp": a.exp_reward})

        return newly_unlocked

    async def _count_completed_verses(self, user_id: int) -> int:
        stmt = select(func.count(Progress.id)).where(
            and_(
                Progress.user_id == user_id,
                Progress.status == "mastered",
                Progress.is_deleted == False,
            )
        )
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def _is_lunyu_complete(self, user_id: int) -> bool:
        """检查《论语》是否全部通关。"""
        from app.models.classic import ClassicBook, Chapter, Verse
        book_stmt = select(ClassicBook).where(
            and_(ClassicBook.title.like("%论语%"), ClassicBook.is_deleted == False)
        )
        book = (await self.db.execute(book_stmt)).scalars().first()
        if book is None:
            return False
        total_stmt = select(func.count(Verse.id)).where(
            and_(Verse.book_id == book.id, Verse.is_deleted == False)
        )
        total = int((await self.db.execute(total_stmt)).scalar() or 0)
        if total == 0:
            return False
        done_stmt = select(func.count(Progress.id)).where(
            and_(
                Progress.user_id == user_id,
                Progress.book_id == book.id,
                Progress.status == "mastered",
                Progress.is_deleted == False,
            )
        )
        done = int((await self.db.execute(done_stmt)).scalar() or 0)
        return done >= total

    async def _get_user_streak(self, user_id: int) -> int:
        stmt = select(User.streak_days).where(User.id == user_id)
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def _count_perfect_quizzes(self, user_id: int) -> int:
        """统计满分测验次数(is_correct == 1)。"""
        stmt = select(func.count(QuizRecord.id)).where(
            and_(
                QuizRecord.user_id == user_id,
                QuizRecord.is_correct == 1,
                QuizRecord.is_deleted == False,
            )
        )
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def _count_consecutive_perfect(self, user_id: int) -> int:
        """统计连续满分测验次数(按时间倒序，遇到非满分停止)。"""
        stmt = (
            select(QuizRecord.is_correct)
            .where(
                and_(
                    QuizRecord.user_id == user_id,
                    QuizRecord.is_deleted == False,
                )
            )
            .order_by(QuizRecord.answered_at.desc())
            .limit(50)
        )
        results = (await self.db.execute(stmt)).scalars().all()
        count = 0
        for is_correct in results:
            if is_correct == 1:
                count += 1
            else:
                break
        return count

    # ---------- 排行榜 ----------

    async def get_leaderboard(self, *, limit: int = 50, scope: str = "exp") -> list[dict]:
        """
        获取排行榜。
        scope: exp(经验值) / streak(连续天数) / verses(通关数)
        """
        order_col = {
            "exp": User.exp_points,
            "streak": User.streak_days,
            "verses": User.total_verses_learned,
        }.get(scope, User.exp_points)

        stmt = (
            select(User)
            .where(User.is_deleted == False)
            .order_by(order_col.desc(), User.id.asc())
            .limit(limit)
        )
        users = (await self.db.execute(stmt)).scalars().all()

        board = []
        for rank, u in enumerate(users, 1):
            rank_info = RANKS[0]
            for r in RANKS:
                if u.exp_points >= r["min_exp"]:
                    rank_info = r
            board.append({
                "rank": rank,
                "user_id": u.id,
                "username": u.username,
                "nickname": u.nickname or u.username,
                "avatar": u.avatar,
                "exp": u.exp_points,
                "streak_days": u.streak_days,
                "verses_learned": u.total_verses_learned,
                "rank_name": rank_info["name"],
                "rank_icon": rank_info["icon"],
            })
        return board

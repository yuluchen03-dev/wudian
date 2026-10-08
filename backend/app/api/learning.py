"""
悟典 - 学习游戏化 API 路由

接口：
- GET  /api/learning/chapter-tree      获取闯关课程树
- POST /api/learning/complete-verse    完成一章学习
- GET  /api/learning/daily-quote       每日一句
- POST /api/learning/checkin           打卡
- GET  /api/learning/streak            获取连续打卡天数
- GET  /api/learning/due-reviews       获取今日待复习
- POST /api/learning/review            提交复习结果
- GET  /api/learning/quiz/{verse_id}   获取测验题
- POST /api/learning/quiz/submit       提交测验答案
- GET  /api/learning/achievements      获取成就
- GET  /api/learning/leaderboard       排行榜
- GET  /api/learning/progress          学习进度概览
- GET  /api/learning/rank              获取段位
- GET  /api/learning/wrong-book        错题本
- GET  /api/learning/review-stats      复习统计
- POST /api/learning/makeup-checkin    补签
"""
import logging
import random
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.classic import Verse, Chapter, ClassicBook
from app.models.srs_record import SrsRecord
from app.models.user import User
from app.schemas.learning import (
    APIResponse,
    ChapterTreeResponse,
    CompleteVerseRequest,
    CompleteVerseResponse,
    DailyQuoteResponse,
    CheckinRequest,
    CheckinResponse,
    MakeupCheckinRequest,
    StreakResponse,
    DueReviewsResponse,
    ReviewRequest,
    ReviewResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    WrongBookResponse,
    ResolveWrongRequest,
    RetryWrongRequest,
    AchievementsResponse,
    LeaderboardResponse,
    OverallProgressResponse,
    DailyGoalResponse,
)
from app.services.srs_service import SRSService
from app.services.progress_service import ProgressService
from app.services.streak_service import StreakService
from app.services.achievement_service import AchievementService, EXP_RULES, RANKS
from app.services.quiz_service import QuizService, PASS_THRESHOLD

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning", tags=["学习游戏化"])


# ============================================================
# 闯关课程树
# ============================================================

@router.get("/chapter-tree", summary="获取闯关课程树")
async def get_chapter_tree(
    book_id: Optional[int] = Query(None, description="书籍 ID，不传则返回全部"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取闯关课程树：书 -> 章(大关) -> 小节(小关)。前一章全部通关后下一章解锁。"""
    svc = ProgressService(db)
    tree = await svc.get_chapter_tree(current_user.id, book_id=book_id)
    return APIResponse(code=0, message="ok", data={"books": tree})


# ============================================================
# 完成一章学习
# ============================================================

@router.post("/complete-verse", summary="完成一章学习")
async def complete_verse(
    req: CompleteVerseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """标记一条经文为已完成阅读，返回更新后的进度与可能触发的新成就。"""
    progress_svc = ProgressService(db)
    ach_svc = AchievementService(db)

    progress = await progress_svc.complete_verse(
        current_user.id,
        req.verse_id,
        read_completed=req.read_completed,
        study_duration=req.study_duration,
    )

    # 发放经验
    exp_gained = 0
    new_achievements: list[dict] = []
    if progress.status == "mastered":
        exp_gained = EXP_RULES["complete_verse"]
        await ach_svc.add_exp(current_user.id, exp_gained, reason="complete_verse")
        new_achievements = await ach_svc.check_achievements(current_user.id)

    return APIResponse(code=0, message="ok", data={
        "progress_id": progress.id,
        "verse_id": progress.verse_id,
        "status": progress.status,
        "mastery_level": progress.mastery_level,
        "study_count": progress.study_count,
        "study_duration": progress.study_duration,
        "exp_gained": exp_gained,
        "new_achievements": new_achievements,
    })


# ============================================================
# 每日一句
# ============================================================

@router.get("/daily-quote", summary="每日一句")
async def get_daily_quote(db: AsyncSession = Depends(get_db)):
    """随机返回一条经文作为每日一句。"""
    # 统计经文总数
    count_stmt = select(func.count(Verse.id)).where(Verse.is_deleted == False)
    total = int((await db.execute(count_stmt)).scalar() or 0)
    if total == 0:
        raise HTTPException(status_code=404, detail="暂无经文数据")

    # 随机取一条 (用 offset)
    offset = random.randint(0, total - 1)
    stmt = (
        select(Verse, Chapter, ClassicBook)
        .join(Chapter, Verse.chapter_id == Chapter.id)
        .join(ClassicBook, Verse.book_id == ClassicBook.id)
        .where(Verse.is_deleted == False)
        .offset(offset)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="暂无经文数据")

    verse, chapter, book = row
    return APIResponse(code=0, message="ok", data={
        "verse_id": verse.id,
        "book_id": book.id,
        "book_title": book.title,
        "chapter_id": chapter.id,
        "chapter_title": chapter.title,
        "original_text": verse.original_text,
        "translation": verse.translation,
        "interpretation": verse.interpretation,
        "pinyin": verse.pinyin,
    })


# ============================================================
# 打卡
# ============================================================

@router.post("/checkin", summary="每日打卡")
async def checkin(
    req: CheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """执行每日打卡，刷新 streak，触发打卡成就。"""
    streak_svc = StreakService(db)
    ach_svc = AchievementService(db)

    checkin_record = await streak_svc.checkin(
        current_user.id,
        verses_learned=req.verses_learned,
        study_duration=req.study_duration,
        note=req.note,
    )

    # 服务端计算经验值：固定打卡奖励 + 客户端上报量级奖励 (最多100)
    exp_gained = EXP_RULES["checkin"]
    # 校验有效期：同一用户同一天只能贡献一次经验 (,streak_service 记录已存在)
    # 去重：若记录已存在，server 端只添加一次固定奖励
    await ach_svc.add_exp(current_user.id, exp_gained, reason="checkin")

    # 触发成就检查
    new_achievements = await ach_svc.check_achievements(current_user.id)

    # 获取最新 streak
    streak_info = await streak_svc.get_streak(current_user.id)

    return APIResponse(code=0, message="ok", data={
        "checkin_id": checkin_record.id,
        "checkin_date": checkin_record.checkin_date.isoformat(),
        "verses_learned": checkin_record.verses_learned,
        "study_duration": checkin_record.study_duration,
        "exp_gained": exp_gained,
        "is_makeup": checkin_record.is_makeup,
        "streak_days": streak_info["streak_days"],
        "total_study_days": streak_info["total_study_days"],
        "new_achievements": new_achievements,
    })


@router.post("/makeup-checkin", summary="补签打卡(护级机制)")
async def makeup_checkin(
    req: MakeupCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """为过去某天补签(最多7天内，每月3次)。"""
    streak_svc = StreakService(db)
    try:
        checkin_record = await streak_svc.makeup_checkin(
            current_user.id, req.target_date, req.note
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    streak_info = await streak_svc.get_streak(current_user.id)
    return APIResponse(code=0, message="ok", data={
        "checkin_id": checkin_record.id,
        "checkin_date": checkin_record.checkin_date.isoformat(),
        "is_makeup": True,
        "streak_days": streak_info["streak_days"],
    })


# ============================================================
# 连续打卡
# ============================================================

@router.get("/streak", summary="获取连续打卡天数")
async def get_streak(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前连续打卡天数、总学习天数、最近7天打卡记录、断签风险。"""
    svc = StreakService(db)
    info = await svc.get_streak(current_user.id)
    return APIResponse(code=0, message="ok", data=info)


# ============================================================
# SRS 复习
# ============================================================

@router.get("/due-reviews", summary="获取今日待复习")
async def get_due_reviews(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户今日待复习的经文列表。"""
    # 关联经文内容：一次性 JOIN 查询，避免 N+1
    stmt = (
        select(SrsRecord, Verse)
        .join(Verse, SrsRecord.verse_id == Verse.id)
        .where(
            and_(
                SrsRecord.user_id == current_user.id,
                SrsRecord.is_deleted == False,
                SrsRecord.next_review_date <= date.today(),
            )
        )
        .order_by(SrsRecord.next_review_date.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for r, verse in rows:
        items.append({
            "record_id": r.id,
            "verse_id": r.verse_id,
            "original_text": verse.original_text if verse else "",
            "translation": verse.translation if verse else None,
            "repetitions": r.repetitions,
            "ease_factor": r.ease_factor,
            "interval_days": r.interval_days,
            "next_review_date": r.next_review_date.isoformat() if r.next_review_date else None,
            "last_review_date": r.last_review_date.isoformat() if r.last_review_date else None,
            "status": r.status,
        })

    return APIResponse(code=0, message="ok", data={
        "due_count": len(items),
        "items": items,
    })


@router.post("/review", summary="提交复习结果")
async def submit_review(
    req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """提交一次复习结果(质量0-5或对/错)，更新SRS调度并发放经验。"""
    srs_svc = SRSService(db)
    ach_svc = AchievementService(db)

    if req.is_correct is not None:
        result = await srs_svc.submit_review_simple(
            current_user.id, req.verse_id, req.is_correct, req.hesitation_seconds
        )
    else:
        result = await srs_svc.submit_review(
            current_user.id, req.verse_id, req.quality
        )

    # 服务端计算经验：按固定规则发放，忽略客户端上报的 exp_gained
    exp_gained = EXP_RULES["review"]
    await ach_svc.add_exp(current_user.id, exp_gained, reason="review")

    return APIResponse(code=0, message="ok", data={
        "verse_id": req.verse_id,
        "repetitions": result.repetitions,
        "ease_factor": result.ease_factor,
        "interval_days": result.interval_days,
        "next_review_at": result.next_review_at.isoformat(),
        "is_relearn": result.is_relearn,
        "exp_gained": exp_gained,
    })


@router.get("/review-stats", summary="复习统计")
async def get_review_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取复习统计：待复习数、已掌握数、今日已复习数等。"""
    svc = SRSService(db)
    stats = await svc.get_review_stats(current_user.id)
    return APIResponse(code=0, message="ok", data=stats)


# ============================================================
# 测验
# ============================================================

@router.get("/quiz/{verse_id}", summary="获取测验题")
async def get_quiz(
    verse_id: int,
    count: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取某条经文的测验题(支持选择/填空/配对/连线)。"""
    svc = QuizService(db)
    items = await svc.get_quiz_for_verse(verse_id, count=count)
    return APIResponse(code=0, message="ok", data={"items": items})


@router.post("/quiz/submit", summary="提交测验答案")
async def submit_quiz(
    req: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量提交测验答案，返回得分、正确率、是否通关、逐题反馈。"""
    quiz_svc = QuizService(db)
    progress_svc = ProgressService(db)
    ach_svc = AchievementService(db)

    answers = [
        {"quiz_id": a.quiz_id, "user_answer": a.user_answer, "time_spent": a.time_spent}
        for a in req.answers
    ]
    result = await quiz_svc.submit_quiz_batch(current_user.id, answers)

    # 经验发放
    exp_gained = 0
    if result["passed"]:
        exp_gained += EXP_RULES["quiz_pass"]
    if result["score"] == 100:
        exp_gained += EXP_RULES["quiz_perfect"]
    if exp_gained > 0:
        await ach_svc.add_exp(current_user.id, exp_gained, reason="quiz")

    # 若指定了 verse_id 且测验通过，更新通关进度
    verse_completed = False
    if req.verse_id and result["passed"]:
        progress = await progress_svc.mark_quiz_passed(
            current_user.id, req.verse_id, result["score"]
        )
        verse_completed = progress.status == "mastered"
        if verse_completed:
            exp_gained += EXP_RULES["complete_verse"]
            await ach_svc.add_exp(current_user.id, EXP_RULES["complete_verse"], reason="complete_verse")

    # 触发成就检查
    new_achievements = await ach_svc.check_achievements(current_user.id)

    return APIResponse(code=0, message="ok", data={
        "total": result["total"],
        "correct_count": result["correct_count"],
        "wrong_count": result["wrong_count"],
        "score": result["score"],
        "passed": result["passed"],
        "pass_threshold": result["pass_threshold"],
        "total_time": result["total_time"],
        "results": result["results"],
        "wrong_list": result["wrong_list"],
        "exp_gained": exp_gained,
        "verse_completed": verse_completed,
        "new_achievements": new_achievements,
    })


# ============================================================
# 错题本
# ============================================================

@router.get("/wrong-book", summary="错题本")
async def get_wrong_book(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取错题本列表。"""
    svc = QuizService(db)
    result = await svc.get_wrong_book(current_user.id, limit=limit, offset=offset)
    return APIResponse(code=0, message="ok", data=result)


@router.post("/wrong-book/resolve", summary="攻克错题")
async def resolve_wrong(
    req: ResolveWrongRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """将错题从错题本移除。"""
    svc = QuizService(db)
    ok = await svc.resolve_wrong(current_user.id, req.record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    return APIResponse(code=0, message="ok", data={"resolved": True})


@router.post("/wrong-book/retry", summary="重做错题")
async def retry_wrong(
    req: RetryWrongRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """重做错题本中的某题。"""
    svc = QuizService(db)
    try:
        result = await svc.retry_wrong(current_user.id, req.record_id, req.user_answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(code=0, message="ok", data=result)


# ============================================================
# 成就
# ============================================================

@router.get("/achievements", summary="获取成就")
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户成就列表(已解锁 + 未解锁)。"""
    svc = AchievementService(db)
    result = await svc.get_user_achievements(current_user.id)
    return APIResponse(code=0, message="ok", data=result)


@router.get("/rank", summary="获取段位")
async def get_rank(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户当前段位(童生→秀才→举人→进士→翰林)与晋升进度。"""
    svc = AchievementService(db)
    result = await svc.get_rank(current_user.id)
    return APIResponse(code=0, message="ok", data=result)


# ============================================================
# 排行榜
# ============================================================

@router.get("/leaderboard", summary="排行榜")
async def get_leaderboard(
    scope: str = Query("exp", description="排序维度: exp/streak/verses"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取排行榜(按经验值/连续天数/通关数)。"""
    svc = AchievementService(db)
    items = await svc.get_leaderboard(limit=limit, scope=scope)
    return APIResponse(code=0, message="ok", data={"scope": scope, "items": items})


# ============================================================
# 学习进度概览
# ============================================================

@router.get("/progress", summary="学习进度概览")
async def get_overall_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户总体学习进度：已通关经文数、总经文数、完成百分比。"""
    svc = ProgressService(db)
    result = await svc.get_overall_progress(current_user.id)
    return APIResponse(code=0, message="ok", data=result)


@router.get("/daily-goal", summary="每日学习目标")
async def get_daily_goal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当日学习目标完成状态。"""
    svc = ProgressService(db)
    result = await svc.get_daily_goal_status(current_user.id)
    return APIResponse(code=0, message="ok", data=result)

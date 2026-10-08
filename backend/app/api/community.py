"""
悟典 - 社区共学 API 路由

接口：
- POST   /api/community/groups              创建小组
- GET    /api/community/groups              小组列表
- GET    /api/community/groups/{id}         小组详情
- POST   /api/community/groups/{id}/join    加入小组
- POST   /api/community/groups/{id}/leave   退出小组
- POST   /api/community/groups/{id}/checkin 小组打卡
- GET    /api/community/groups/{id}/stats   小组打卡统计
- POST   /api/community/notes               发布笔记
- GET    /api/community/notes               笔记流（分页、排序）
- GET    /api/community/notes/{id}          笔记详情
- POST   /api/community/notes/{id}/like     点赞
- POST   /api/community/notes/{id}/comment  评论
- POST   /api/community/pk/match            PK 匹配
- POST   /api/community/pk/submit           提交 PK 答案
- GET    /api/community/leaderboard         排行榜
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.community import (
    CommentCreate,
    GroupCategory,
    GroupCreate,
    LeaderboardScope,
    NoteCreate,
    NoteSortBy,
    PKMatchRequest,
    PKSubmitRequest,
)
from app.services.community_service import CommunityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/community", tags=["社区共学"])


def _get_service(db: AsyncSession = Depends(get_db)) -> CommunityService:
    """依赖注入：创建 CommunityService 实例"""
    return CommunityService(db)


# ============================================================
# 共读小组
# ============================================================

@router.post("/groups", summary="创建小组")
async def create_group(
    req: GroupCreate,
    service: CommunityService = Depends(_get_service),
    current_user: User = Depends(get_current_active_user),
):
    """创建共读小组，创建者自动成为组长"""
    try:
        group = await service.create_group(
            user_id=current_user.id,
            username=current_user.username,
            level=current_user.level,
            data=req,
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/groups", summary="小组列表")
async def list_groups(
    category: Optional[GroupCategory] = Query(None, description="小组分类"),
    book_id: Optional[str] = Query(None, description="书籍 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommunityService = Depends(_get_service),
):
    """获取小组列表，支持按分类、书籍筛选与分页"""
    return await service.list_groups(
        category=category, book_id=book_id, page=page, page_size=page_size
    )


@router.get("/groups/{group_id}", summary="小组详情")
async def get_group(group_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """获取小组详情，含成员列表"""
    try:
        return await service.get_group(group_id, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/groups/{group_id}/join", summary="加入小组")
async def join_group(group_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """加入指定小组"""
    try:
        return await service.join_group(
            group_id=group_id,
            user_id=current_user.id,
            username=current_user.username,
            level=current_user.level,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/groups/{group_id}/leave", summary="退出小组")
async def leave_group(group_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """退出指定小组"""
    try:
        await service.leave_group(group_id, current_user.id)
        return {"message": "已退出小组"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/groups/{group_id}/checkin", summary="小组打卡")
async def checkin(group_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """每日小组打卡"""
    try:
        return await service.checkin(group_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/groups/{group_id}/stats", summary="小组打卡统计")
async def group_stats(group_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """获取小组打卡统计：今日打卡人数、本周打卡率、连续天数"""
    try:
        return await service.get_group_checkin_stat(group_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 笔记
# ============================================================

@router.post("/notes", summary="发布笔记")
async def create_note(req: NoteCreate, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """发布学习笔记，可关联书籍、章节、经文、小组"""
    try:
        return await service.create_note(
            user_id=current_user.id,
            username=current_user.username,
            level=current_user.level,
            data=req,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notes", summary="笔记流")
async def list_notes(
    group_id: Optional[int] = Query(None, description="小组 ID"),
    book_id: Optional[str] = Query(None, description="书籍 ID"),
    tag: Optional[str] = Query(None, description="标签"),
    sort_by: NoteSortBy = Query(NoteSortBy.LATEST, description="排序：latest/hottest/essence"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommunityService = Depends(_get_service),
    current_user: User = Depends(get_current_active_user),
):
    """获取笔记流，支持分页、排序、按小组/书籍/标签筛选"""
    return await service.list_notes(
        group_id=group_id,
        book_id=book_id,
        tag=tag,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
    )


@router.get("/notes/{note_id}", summary="笔记详情")
async def get_note(note_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """获取笔记详情，含评论树"""
    try:
        return await service.get_note(note_id, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/notes/{note_id}/like", summary="点赞")
async def like_note(note_id: int, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """点赞 / 取消点赞（toggle）"""
    try:
        return await service.like_note(note_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/notes/{note_id}/comment", summary="评论")
async def comment_note(
    note_id: int, req: CommentCreate, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)
):
    """评论笔记，支持回复（parent_id）"""
    try:
        return await service.comment_note(
            note_id=note_id,
            user_id=current_user.id,
            username=current_user.username,
            level=current_user.level,
            content=req.content,
            parent_id=req.parent_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 答题 PK
# ============================================================

@router.post("/pk/match", summary="PK 匹配")
async def pk_match(req: PKMatchRequest, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """按段位匹配 PK 对手，返回题目"""
    try:
        return await service.pk_match(
            user_id=current_user.id,
            username=current_user.username,
            level=current_user.level,
            req=req,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pk/submit", summary="提交 PK 答案")
async def pk_submit(req: PKSubmitRequest, service: CommunityService = Depends(_get_service), current_user: User = Depends(get_current_active_user)):
    """提交 PK 答案并结算"""
    try:
        return await service.pk_submit(current_user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 排行榜
# ============================================================

@router.get("/leaderboard", summary="排行榜")
async def leaderboard(
    scope: LeaderboardScope = Query(LeaderboardScope.WEEK, description="范围：week/month/all"),
    metric: str = Query("exp", description="指标：exp/checkin/pk_rating"),
    limit: int = Query(50, ge=1, le=200),
    service: CommunityService = Depends(_get_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    排行榜
    - scope: week（周榜）/ month（月榜）/ all（总榜）
    - metric: exp（经验值）/ checkin（打卡天数）/ pk_rating（PK 段位分）
    """
    return await service.get_leaderboard(
        scope=scope, metric=metric, current_user_id=current_user.id, limit=limit
    )

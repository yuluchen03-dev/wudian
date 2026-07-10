"""
悟典 - 趣味内容 API 路由

接口：
- GET  /api/content/quote-cards          金句卡片列表
- GET  /api/content/quote-cards/{id}     金句卡片详情
- POST /api/content/quote-cards/{id}/like  点赞金句卡片
- POST /api/content/quote-cards/{id}/share 记录分享
- GET  /api/content/theater              情景小剧场列表
- GET  /api/content/theater/{id}         小剧场详情
- GET  /api/content/comics              漫画列表
- GET  /api/content/comics/{id}         漫画详情
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.content import CardStyle
from app.services.content_service import content_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["趣味内容"])


# ============================================================
# 金句卡片
# ============================================================

@router.get("/quote-cards", summary="金句卡片列表")
async def list_quote_cards(
    style: Optional[CardStyle] = Query(None, description="排版风格"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取金句卡片列表，支持按风格筛选与分页"""
    return await content_service.list_quote_cards(style=style, page=page, page_size=page_size)


@router.get("/quote-cards/{card_id}", summary="金句卡片详情")
async def get_quote_card(card_id: str):
    """获取单张金句卡片详情"""
    try:
        return await content_service.get_quote_card(card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quote-cards/{card_id}/like", summary="点赞金句卡片")
async def like_quote_card(
    card_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """点赞金句卡片（需要登录）"""
    logger.info("用户 %s 点赞金句卡片: %s", current_user.id, card_id)
    try:
        return await content_service.like_quote_card(card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quote-cards/{card_id}/share", summary="记录分享")
async def share_quote_card(
    card_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """记录金句卡片分享次数（需要登录）"""
    logger.info("用户 %s 分享金句卡片: %s", current_user.id, card_id)
    try:
        return await content_service.share_quote_card(card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 情景小剧场
# ============================================================

@router.get("/theater", summary="情景小剧场列表")
async def list_theaters(
    modern_setting: Optional[str] = Query(None, description="现代场景：职场/校园/家庭"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取情景小剧场列表"""
    return await content_service.list_theaters(
        modern_setting=modern_setting, page=page, page_size=page_size
    )


@router.get("/theater/{theater_id}", summary="小剧场详情")
async def get_theater(theater_id: str):
    """获取小剧场详情，含角色、场景、台词"""
    try:
        return await content_service.get_theater(theater_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 漫画解读
# ============================================================

@router.get("/comics", summary="漫画列表")
async def list_comics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取漫画解读列表"""
    return await content_service.list_comics(page=page, page_size=page_size)


@router.get("/comics/{comic_id}", summary="漫画详情")
async def get_comic(comic_id: str):
    """获取漫画详情，含分镜"""
    try:
        return await content_service.get_comic(comic_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

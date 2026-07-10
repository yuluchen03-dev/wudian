"""
悟典 - 经典内容 API 路由（层1 经典阅读层后端）

接口：
- GET /api/classics/books                  获取所有经典书目
- GET /api/classics/books/{book_id}        获取单本书信息
- GET /api/classics/books/{book_id}/chapters  获取章节列表
- GET /api/classics/chapters/{chapter_id}  获取章节内容（含句子、注释）
- GET /api/classics/verses/{verse_id}      获取单句详情
- GET /api/classics/entities/{entity_id}   获取实体百科
- GET /api/classics/daily-quote            每日一句

注：经典阅读为公开内容，无需登录即可访问。
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.classics import (
    Book,
    Chapter,
    ChapterBrief,
    DailyQuote,
    Entity,
    SentencePair,
)
from app.services import classics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/classics", tags=["经典文献"])


# ============================================================
# 书籍
# ============================================================

@router.get(
    "/books",
    response_model=List[Book],
    summary="获取所有经典书目",
)
async def get_books():
    """获取四书五经的书目列表"""
    return classics_service.get_books()


@router.get(
    "/books/{book_id}",
    response_model=Book,
    summary="获取单本书信息",
)
async def get_book(book_id: str):
    """获取指定书籍的元信息"""
    book = classics_service.get_book(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"书籍 {book_id} 不存在",
        )
    return book


@router.get(
    "/books/{book_id}/chapters",
    response_model=List[ChapterBrief],
    summary="获取章节列表",
)
async def get_chapters(book_id: str):
    """获取指定书籍的章节列表（简要信息，不含句子）"""
    book = classics_service.get_book(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"书籍 {book_id} 不存在",
        )
    return classics_service.get_chapters(book_id)


# ============================================================
# 章节 & 句子
# ============================================================

@router.get(
    "/chapters/{chapter_id}",
    response_model=Chapter,
    summary="获取章节内容",
)
async def get_chapter(chapter_id: str):
    """
    获取章节详情，包含所有句子（原文、译文、注释、关联实体）

    chapter_id 格式: "lunyu-1" 表示论语第1篇
    """
    chapter = classics_service.get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"章节 {chapter_id} 不存在",
        )
    return chapter


@router.get(
    "/verses/{verse_id}",
    response_model=SentencePair,
    summary="获取单句详情",
)
async def get_verse(verse_id: str):
    """
    获取单句详情（原文、译文、注释、关联实体）

    verse_id 格式: "1-1" 对应论语第1篇第1句
    """
    verse = classics_service.get_verse(verse_id)
    if verse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"句子 {verse_id} 不存在",
        )
    return verse


# ============================================================
# 实体百科
# ============================================================

@router.get(
    "/entities/{entity_id}",
    response_model=Entity,
    summary="获取实体百科",
)
async def get_entity(entity_id: str):
    """
    获取实体（人名/地名/概念等）的百科信息

    示例 entity_id: confucius(孔子), zengzi(曾子), junzi(君子), ren(仁)
    """
    entity = classics_service.get_entity(entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"实体 {entity_id} 不存在",
        )
    return entity


# ============================================================
# 每日一句
# ============================================================

@router.get(
    "/daily-quote",
    response_model=DailyQuote,
    summary="每日一句",
)
async def get_daily_quote():
    """
    获取今日推荐名句

    根据当天日期从名句库中选取，同一天访问返回相同结果。
    """
    quote = classics_service.get_daily_quote()
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无每日一句数据",
        )
    return quote

"""
悟典 - 经典内容数据模型
与前端 frontend/lib/types.ts 类型定义对齐

书籍(Book) -> 章节(Chapter) -> 句子(SentencePair) -> 注释(Annotation)
实体(Entity) | 每日一句(DailyQuote)
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# 注释 & 实体
# ============================================================

class Annotation(BaseModel):
    """句子中的注释（生僻字）"""
    char: str = Field(..., description="原文中的字")
    pinyin: str = Field(..., description="拼音")
    meaning: str = Field(..., description="释义")
    isTongjia: Optional[bool] = Field(None, description="是否为通假字")
    tongjiaOrigin: Optional[str] = Field(None, description="通假字本字")


class Entity(BaseModel):
    """实体（百科）"""
    id: str = Field(..., description="实体唯一标识")
    name: str = Field(..., description="名称")
    type: str = Field(..., description="类型: 人名 / 地名 / 官职 / 典故 / 概念")
    description: str = Field(..., description="描述")
    relatedText: Optional[str] = Field(None, description="关联的原文片段")


# ============================================================
# 句子 & 章节 & 书籍
# ============================================================

class SentencePair(BaseModel):
    """原文与译文逐句对应"""
    id: str = Field(..., description="句子唯一标识")
    original: str = Field(..., description="原文")
    translation: str = Field(..., description="白话翻译")
    annotations: List[Annotation] = Field(default_factory=list, description="注释列表")
    entityIds: List[str] = Field(default_factory=list, description="关联实体 ID")
    title: Optional[str] = Field(None, description="句子标题/主题")
    keywords: List[str] = Field(default_factory=list, description="关键词")


class Chapter(BaseModel):
    """章节"""
    id: str = Field(..., description="章节唯一标识")
    bookId: str = Field(..., description="所属书籍 ID")
    order: int = Field(..., description="章序号")
    title: str = Field(..., description="章节标题，如 '学而第一'")
    summary: Optional[str] = Field(None, description="章节摘要")
    sentences: List[SentencePair] = Field(default_factory=list, description="句子列表")


class ChapterBrief(BaseModel):
    """章节简要信息（列表用，不含句子）"""
    id: str = Field(..., description="章节唯一标识")
    bookId: str = Field(..., description="所属书籍 ID")
    order: int = Field(..., description="章序号")
    title: str = Field(..., description="章节标题")
    summary: Optional[str] = Field(None, description="章节摘要")
    sentenceCount: int = Field(0, description="句子数量")


class Book(BaseModel):
    """书籍元信息"""
    id: str = Field(..., description="书籍唯一标识")
    title: str = Field(..., description="书名")
    category: str = Field(..., description="四书五经分类: '四书' / '五经'")
    author: Optional[str] = Field(None, description="作者/编者")
    dynasty: Optional[str] = Field(None, description="朝代")
    description: str = Field(..., description="书籍简介")
    coverColor: str = Field("#b91c1c", description="封面颜色")
    totalChapters: int = Field(..., description="总章节数")


# ============================================================
# 每日一句
# ============================================================

class DailyQuote(BaseModel):
    """每日一句"""
    id: str = Field(..., description="唯一标识")
    text: str = Field(..., description="原文")
    translation: str = Field(..., description="白话翻译")
    source: str = Field(..., description="出处，如 '论语·学而第一'")
    chapterId: str = Field(..., description="章节 ID")

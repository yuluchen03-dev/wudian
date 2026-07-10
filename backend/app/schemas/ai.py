"""
悟典 - AI 服务 Pydantic 请求/响应模型
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, validator


# ============================================================
# 通用子模型
# ============================================================

class RAGReference(BaseModel):
    """RAG 检索到的原文引用"""
    text: str = Field(..., description="原文内容")
    source: str = Field(..., description="出处，如《论语·学而》")
    chapter: Optional[str] = Field(None, description="篇章")
    verse_no: Optional[int] = Field(None, description="章序号")
    similarity: float = Field(0.0, description="相关度分数 0-1")


# ============================================================
# 逐句精讲 explain
# ============================================================

class ExplainRequest(BaseModel):
    """逐句精讲请求"""
    verse_id: str = Field(..., description="经文 ID")
    text: Optional[str] = Field(None, description="原文，若 verse_id 未命中可手动传入")
    context: Optional[str] = Field(None, description="上下文（前后章节）")
    depth: Literal["brief", "standard", "deep"] = Field(
        "standard", description="讲解深度：简版/标准/深读"
    )


class VerseExplanation(BaseModel):
    """逐句精讲响应"""
    verse_id: str
    original_text: str = Field(..., description="原文")
    translation: str = Field(..., description="白话翻译")
    background: str = Field(..., description="背景故事")
    modern_analogy: str = Field(..., description="现代场景类比")
    reflection: str = Field(..., description="延伸思考")
    key_words: List[str] = Field(default_factory=list, description="核心字词解析")
    references: List[RAGReference] = Field(default_factory=list, description="RAG 引用出处")
    confidence: float = Field(1.0, description="置信度 0-1")
    disclaimer: Optional[str] = Field(None, description="低置信度时的提示")


# ============================================================
# 文白翻译 translate
# ============================================================

class TranslateRequest(BaseModel):
    """文白翻译请求"""
    text: str = Field(..., min_length=1, max_length=2000, description="待翻译文言文")
    direction: Literal["to_modern", "to_classical"] = Field(
        "to_modern", description="方向：译为白话 / 译为文言"
    )


class TranslateResponse(BaseModel):
    """文白翻译响应"""
    original: str
    translated: str
    notes: Optional[str] = Field(None, description="字词注释")


# ============================================================
# 与圣贤对话 chat-sage
# ============================================================

class ChatMessage(BaseModel):
    """对话历史单条"""
    role: Literal["user", "assistant"]
    content: str


SageId = Literal[
    "confucius",
    "mencius",
    "wang_yangming",
    "laozi",
    "mozi",
    "hanfeizi",
    "li_bai",
    "su_shi",
    "fan_zhongyan",
    "wang_anshi",
    "zhuge_liang",
]


class ChatSageRequest(BaseModel):
    """与圣贤对话请求"""
    sage: SageId = Field(
        ..., description="圣贤：confucius 孔子 / mencius 孟子 / wang_yangming 王阳明"
    )
    question: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, description="历史对话")
    stream: bool = Field(True, description="是否流式返回（SSE）")


class Citation(BaseModel):
    """引用条目"""
    id: str = Field(..., description="引用标记，如 引1")
    source: str = Field(..., alias="出处", description="出处，如 论语·学而篇")
    original: str = Field(..., alias="原文", description="经典原文")
    verifiable: bool = Field(True, description="是否可溯源")

    model_config = ConfigDict(populate_by_name=True)


class ChatSageResponse(BaseModel):
    """与圣贤对话响应（非流式）"""
    sage: str
    reply: str
    disclaimer: str = Field(..., description="免责声明")
    references: List[RAGReference] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list, description="结构化引用列表")
    modern_takeaway: Optional[str] = Field(None, description="现代白话点睛")
    confidence: Literal["high", "medium", "low"] = Field("medium", description="置信度")
    honest_note: Optional[str] = Field(None, description="诚实声明")


# ============================================================
# AI 生成测验题 generate-quiz
# ============================================================

class GenerateQuizRequest(BaseModel):
    """生成测验题请求"""
    verse_id: str = Field(..., description="经文 ID")
    quiz_type: Literal["choice", "fill", "judge", "explain"] = Field(
        "choice", description="题型：选择/填空/判断/简答"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field("medium")
    count: int = Field(3, ge=1, le=10, description="题目数量")


class QuizQuestion(BaseModel):
    """单道测验题"""
    question: str
    options: Optional[List[str]] = Field(None, description="选项（选择题）")
    answer: str
    explanation: str
    quiz_type: str
    difficulty: str


class GenerateQuizResponse(BaseModel):
    """生成测验题响应"""
    verse_id: str
    quiz_type: str
    questions: List[QuizQuestion]
    references: List[RAGReference] = Field(default_factory=list)


# ============================================================
# RAG 检索（内部/调试用）
# ============================================================

class RetrieveRequest(BaseModel):
    """RAG 检索请求"""
    query: str
    top_k: int = Field(5, ge=1, le=20)


class RetrieveResponse(BaseModel):
    """RAG 检索响应"""
    query: str
    results: List[RAGReference]

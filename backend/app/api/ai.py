"""
悟典 - AI 相关 API 路由

接口：
- POST /api/ai/explain       逐句精讲
- POST /api/ai/translate     文白翻译
- POST /api/ai/chat-sage     与圣贤对话（支持 SSE 流式）
- POST /api/ai/generate-quiz 生成测验题
- POST /api/ai/retrieve      RAG 检索（调试用）
"""
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user_or_demo
from app.models.user import User
from app.schemas.ai import (
    ExplainRequest,
    VerseExplanation,
    TranslateRequest,
    TranslateResponse,
    ChatSageRequest,
    ChatSageResponse,
    GenerateQuizRequest,
    GenerateQuizResponse,
    RetrieveRequest,
    RetrieveResponse,
    RAGReference,
    Citation,
)
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI 智能讲解"])


# ============================================================
# 逐句精讲
# ============================================================
@router.post("/explain", response_model=VerseExplanation, summary="逐句精讲")
async def explain_verse(
    req: ExplainRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """对指定经文进行逐句精讲：白话翻译 + 背景故事 + 现代场景类比 + 延伸思考"""
    logger.info("用户 %s 请求逐句精讲: verse_id=%s", current_user.id, req.verse_id)
    return await ai_service.explain_verse(
        verse_id=req.verse_id,
        text=req.text,
        context=req.context,
        depth=req.depth,
    )


# ============================================================
# 文白翻译
# ============================================================
@router.post("/translate", response_model=TranslateResponse, summary="文白翻译")
async def translate_text(
    req: TranslateRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """文言文 ↔ 现代汉语互译"""
    logger.info("用户 %s 请求文白翻译", current_user.id)
    result = await ai_service.translate_text(req.text, direction=req.direction)
    return TranslateResponse(
        original=req.text,
        translated=result,
        notes=None,
    )


# ============================================================
# 与圣贤对话（支持 SSE 流式）
# ============================================================
@router.post("/chat-sage", summary="与圣贤对话")
async def chat_with_sage(
    req: ChatSageRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """与孔子/孟子/王阳明对话，支持 SSE 流式响应"""
    logger.info(
        "用户 %s 与圣贤对话: sage=%s, stream=%s",
        current_user.id, req.sage, req.stream,
    )
    history = [{"role": h.role, "content": h.content} for h in req.history]

    if req.stream:
        # 流式：SSE
        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                # --- 检索可视化：先发送检索到的篇章信息 ---
                from app.services.rag_service import get_rag_service
                rag = get_rag_service()
                sage_result = await rag.retrieve_for_sage_chat(req.question, top_k=5)
                # 提取去重的篇章名
                seen_chapters: set = set()
                chapters_list: list = []
                for v in sage_result.get("verses", []):
                    ch = v.get("chapter", "")
                    src = v.get("source", "")
                    if ch and ch not in seen_chapters:
                        seen_chapters.add(ch)
                        chapters_list.append({"name": ch, "source": src})
                for c in sage_result.get("commentaries", []):
                    ch = c.get("chapter", "")
                    src = c.get("source", "")
                    if ch and ch not in seen_chapters:
                        seen_chapters.add(ch)
                        chapters_list.append({"name": ch, "source": src})
                # 发送 chapters 事件
                chapters_data = json.dumps(
                    {"type": "chapters", "chapters": chapters_list},
                    ensure_ascii=False,
                )
                yield f"data: {chapters_data}\n\n"

                response = await ai_service.chat_with_sage_stream_response(
                    sage=req.sage,
                    question=req.question,
                    history=history,
                )
                # Final response is only returned after the shared CitationGuard.
                for chunk in ai_service._response_text_chunks(response):
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                if response.citations:
                    citations = [citation.model_dump(by_alias=True) for citation in response.citations]
                    cit_data = json.dumps({"type": "citations", "citations": citations}, ensure_ascii=False)
                    yield f"data: {cit_data}\n\n"
                yield "data: [DONE]\n\n"
            except Exception:
                # Do not expose any citation if completion/verification was interrupted.
                # Avoid logging provider exception payloads which may contain headers.
                logger.error("chat-sage stream failed before citation validation completed")
                event = json.dumps(
                    {"type": "error", "code": "stream_incomplete",
                     "message": "本次回答未完成验证，请稍后重试。"},
                    ensure_ascii=False,
                )
                yield f"data: {event}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式：使用结构化版本，带 citations 和引用校验
        try:
            response = await ai_service.chat_with_sage_structured(
                sage=req.sage,
                question=req.question,
                history=history,
            )
            return response
        except Exception:
            # 兜底：缓存兜底，不报 500
            # 不记录异常负载：SDK 异常文本可能含 Authorization/Bearer（401/403）。
            logger.error("chat-sage 非流式 error，启用缓存兜底")
            from app.services import sage_cache
            from app.services.prompt_templates import DISCLAIMER_SAGE
            fallback = sage_cache.get_fallback_qa(req.question)
            content = fallback.get("content", "")
            vernacular = fallback.get("vernacular", "")
            quotes = fallback.get("original_quotes", [])
            sources = fallback.get("sources", [])
            quote_text = quotes[0] if quotes else "无"
            source_text = sources[0] if sources else "无"
            # 统一 <<<TAG>>> 格式
            reply = (
                f"<<<QUOTE>>>\n{quote_text}\n"
                f"<<<SOURCE>>>\n{source_text}\n"
                f"<<<CLASSICAL>>>\n{content}\n"
                f"<<<VERNACULAR>>>\n{vernacular}\n"
                f"<<<DISCLAIMER>>>\n{fallback.get('disclaimer', DISCLAIMER_SAGE)}"
            )
            # 构造 citations
            fallback_citations = []
            for idx, q in enumerate(quotes):
                src = sources[idx] if idx < len(sources) else ""
                fallback_citations.append(Citation(
                    id=f"引{idx + 1}",
                    source=src,
                    original=q,
                    verifiable=True,
                ))
            # references 仍从缓存的原文/出处构造
            refs = []
            for idx, q in enumerate(quotes):
                src = sources[idx] if idx < len(sources) else ""
                refs.append(RAGReference(text=q, source=src, similarity=1.0))
            
            return ChatSageResponse(
                sage=req.sage,
                reply=reply,
                disclaimer=fallback.get("disclaimer", DISCLAIMER_SAGE),
                references=refs,
                citations=fallback_citations,
                modern_takeaway=vernacular,
                confidence="low",
                honest_note="AI 服务暂时不可用，已返回预设回答。",
            )


# ============================================================
# AI 生成测验题
# ============================================================
@router.post("/generate-quiz", response_model=GenerateQuizResponse, summary="生成测验题")
async def generate_quiz(
    req: GenerateQuizRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """AI 根据经文生成测验题（选择/填空/判断/简答）"""
    logger.info("用户 %s 请求生成测验题: verse_id=%s", current_user.id, req.verse_id)
    questions = await ai_service.generate_quiz(
        verse_id=req.verse_id,
        quiz_type=req.quiz_type,
        difficulty=req.difficulty,
        count=req.count,
    )
    # 附带 RAG 引用
    from app.services.rag_service import get_rag_service
    rag = get_rag_service()
    # 用 verse_id 粗检索一次拿引用
    refs = await rag.retrieve(req.verse_id, top_k=3)
    return GenerateQuizResponse(
        verse_id=req.verse_id,
        quiz_type=req.quiz_type,
        questions=questions,
        references=refs,
    )


# ============================================================
# RAG 检索（调试用）
# ============================================================
@router.post("/retrieve", response_model=RetrieveResponse, summary="RAG 检索（调试）")
async def retrieve(
    req: RetrieveRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """检索与查询相关的原文，返回引用列表"""
    logger.info("用户 %s 请求 RAG 检索: query=%s", current_user.id, req.query)
    from app.services.rag_service import get_rag_service
    rag = get_rag_service()
    results = await rag.retrieve(req.query, top_k=req.top_k)
    return RetrieveResponse(query=req.query, results=results)

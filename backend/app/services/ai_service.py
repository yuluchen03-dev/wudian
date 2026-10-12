"""
悟典 - AI 核心服务

提供：
- explain_verse: 逐句精讲（白话翻译 + 背景 + 现代类比 + 延伸思考）
- translate_text: 文白翻译
- chat_with_sage: 与圣贤对话（角色扮演，支持流式）
- generate_quiz: AI 生成测验题

防幻觉设计：
- 所有回答基于 RAG 检索原文，强制引用出处
- 低置信度时明确告知"未找到确切出处"
- 圣贤对话标注免责声明

断网兜底：
- chat_with_sage 优先匹配 sage_cache 中的安全问答
- LLM 调用失败时 fallback 到缓存中最相似的问答
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, List, Optional

from app.core.config import settings
from app.schemas.ai import (
    VerseExplanation,
    RAGReference,
    QuizQuestion,
    Citation,
    ChatSageResponse,
)
from app.services.llm_client import llm_client
from app.services.rag_service import get_rag_service
from app.services import prompt_templates as pt
from app.services.sage_persona import (
    get_sage,
    build_sage_system_prompt,
    get_sage_name,
)
from app.services import sage_cache

logger = logging.getLogger(__name__)


def extract_stream_reply_text(raw: str) -> str:
    """Return displayable text from an LLM response that may be JSON-wrapped."""
    text = (raw or "").strip()
    if not text:
        return ""

    try:
        data = llm_client._parse_json(text)
    except Exception:
        return text

    if not isinstance(data, dict):
        return text

    reply = str(data.get("reply") or "").strip()
    takeaway = str(data.get("modern_takeaway") or "").strip()
    honest_note = data.get("honest_note")
    honest = str(honest_note).strip() if honest_note else ""

    parts = [part for part in (reply, takeaway, honest) if part and part.lower() != "null"]
    return "\n\n".join(parts) if parts else text


def _looks_like_llm_unavailable(text: str) -> bool:
    """Detect friendly LLM setup errors that should trigger cached demo fallback."""
    original = text or ""
    normalized = original.lower()
    return (
        ("api_key" in normalized and ("未配置" in original or "not configured" in normalized))
        or ("llm_provider" in normalized and "api_key" in normalized)
        or ("ai 讲解功能未启用" in normalized)
        or ("openai" in normalized and "未安装" in original)
        or ("llm" in normalized and ("unavailable" in normalized or "未初始化" in original))
    )


class AIService:
    """AI 核心服务"""

    # ----------------------------------------------------------
    # 1. 逐句精讲
    # ----------------------------------------------------------
    async def explain_verse(
        self,
        verse_id: str,
        text: Optional[str] = None,
        context: Optional[str] = None,
        depth: str = "standard",
    ) -> VerseExplanation:
        """逐句精讲：白话翻译 + 背景故事 + 现代场景类比 + 延伸思考"""
        verse_text = text or verse_id  # 若无 text，用 verse_id 兜底

        # 1. RAG 检索相关原文
        rag = get_rag_service()
        refs = await rag.retrieve(verse_text, top_k=settings.RAG_TOP_K)
        rag_context = rag.build_context_text(refs)
        low_conf = rag.is_low_confidence(refs)

        # 2. 构建 prompt
        depth_desc = pt.EXPLAIN_DEPTH.get(depth, pt.EXPLAIN_DEPTH["standard"])
        extra = f"【上下文】\n{context}" if context else ""
        user_msg = pt.EXPLAIN_USER.format(
            verse_text=verse_text,
            rag_context=rag_context,
            extra_context=extra,
            depth_desc=depth_desc,
        )
        messages = [
            {"role": "system", "content": pt.EXPLAIN_SYSTEM},
            {"role": "user", "content": user_msg},
        ]

        # 3. 调 LLM（JSON 模式）
        try:
            data = await llm_client.complete_json(messages, temperature=0.5)
        except Exception:
            # 不记录异常负载：SDK 异常文本可能含 Authorization/Bearer（401/403）。
            logger.error("explain_verse LLM 调用失败")
            # 兜底：返回带错误提示的结构
            return VerseExplanation(
                verse_id=verse_id,
                original_text=verse_text,
                translation="（讲解生成失败，请稍后重试）",
                background="",
                modern_analogy="",
                reflection="",
                references=refs,
                confidence=0.0,
                disclaimer="生成失败",
            )

        # 4. 组装响应
        confidence = float(data.get("confidence", 0.5))
        disclaimer = None
        if low_conf or confidence < settings.RAG_SIMILARITY_THRESHOLD:
            disclaimer = pt.DISCLAIMER_LOW_CONFIDENCE

        return VerseExplanation(
            verse_id=verse_id,
            original_text=verse_text,
            translation=data.get("translation", ""),
            background=data.get("background", ""),
            modern_analogy=data.get("modern_analogy", ""),
            reflection=data.get("reflection", ""),
            key_words=data.get("key_words", []),
            references=refs,
            confidence=confidence,
            disclaimer=disclaimer,
        )

    # ----------------------------------------------------------
    # 2. 文白翻译
    # ----------------------------------------------------------
    async def translate_text(self, text: str, direction: str = "to_modern") -> str:
        """文白翻译"""
        if direction == "to_classical":
            sys_prompt = pt.TRANSLATE_TO_CLASSICAL_SYSTEM
        else:
            sys_prompt = pt.TRANSLATE_TO_MODERN_SYSTEM

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": pt.TRANSLATE_USER.format(text=text)},
        ]
        return await llm_client.complete(messages, temperature=0.3)

    # ----------------------------------------------------------
    # 3. 与圣贤对话
    # ----------------------------------------------------------
    async def chat_with_sage(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Compatibility generator: yields display chunks from a verified final response."""
        response = await self.chat_with_sage_stream_response(sage, question, history)
        for chunk in self._response_text_chunks(response):
            yield chunk

    async def chat_with_sage_stream_response(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
    ) -> ChatSageResponse:
        """Generate/assemble a complete response, then validate citations before return."""
        history = history or []
        rag = get_rag_service()
        sage_result = await rag.retrieve_for_sage_chat(question, top_k=settings.RAG_TOP_K)

        # Local cache answers are not exempt from the citation validation path.
        cached = sage_cache.match_safe_qa(question)
        if cached is not None:
            logger.info("chat_with_sage 命中安全问答缓存: %s", cached.get("cache_key"))
            return self.build_stream_fallback_response(sage, cached, sage_result)

        if not llm_client.is_available:
            logger.info("chat_with_sage LLM 不可用，直接启用缓存兜底")
            fallback = sage_cache.get_fallback_qa(question)
            return self.build_stream_fallback_response(sage, fallback, sage_result)

        rag_context = rag.build_sage_chat_context(sage_result)
        sys_prompt = build_sage_system_prompt(sage, rag_context)
        sage_name = get_sage_name(sage)
        messages = [{"role": "system", "content": sys_prompt}]
        for item in history:
            messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        has_results = bool(sage_result.get("verses") or sage_result.get("commentaries"))
        messages.append({
            "role": "user",
            "content": pt.SAGE_CHAT_USER.format(
                question=question,
                persona_name=sage_name,
                has_results="有" if has_results else "无",
            ),
        })

        raw_chunks = []
        try:
            async for chunk in llm_client.stream(messages, temperature=0.8):
                raw_chunks.append(chunk)
        except Exception:
            # Provider exception strings may contain headers. Never log their payload.
            logger.error("chat_with_sage LLM 调用失败，启用缓存兜底")
            fallback = sage_cache.get_fallback_qa(question)
            return self.build_stream_fallback_response(sage, fallback, sage_result)

        raw_response = "".join(raw_chunks)
        if _looks_like_llm_unavailable(extract_stream_reply_text(raw_response)):
            logger.info("chat_with_sage 收到 LLM 不可用文本，启用缓存兜底")
            fallback = sage_cache.get_fallback_qa(question)
            raw_response = json.dumps(self._cached_structured_payload(fallback), ensure_ascii=False)

        # Stream and non-stream both return only after this shared final validator.
        data = llm_client._parse_json(raw_response)
        if not isinstance(data, dict):
            data = {}
        raw_citations = data.get("citations", []) or []
        refs = list(sage_result.get("verses", [])) + list(sage_result.get("commentaries", []))
        citations, all_verified = self._validate_citations(raw_citations, refs)
        if not all_verified:
            failed = [citation for citation in citations if not citation.verifiable]
            if failed:
                if data.get("confidence") == "high":
                    data["confidence"] = "medium"
                data["honest_note"] = data.get("honest_note") or "部分引用无法在经典原文中溯源，请谨慎参考。"
        return ChatSageResponse(
            sage=sage,
            reply=str(data.get("reply") or extract_stream_reply_text(raw_response)),
            disclaimer=pt.DISCLAIMER_SAGE,
            citations=citations,
            modern_takeaway=data.get("modern_takeaway"),
            confidence=data.get("confidence", "medium"),
            honest_note=data.get("honest_note"),
        )

    @staticmethod
    def _response_text_chunks(response: ChatSageResponse) -> List[str]:
        """Build display text from the validated completed response."""
        citations = [
            {"id": c.id, "出处": c.source, "原文": c.original, "verifiable": c.verifiable,
             "verification_status": c.verification_status}
            for c in response.citations
        ]
        payload = {
            "reply": response.reply,
            "citations": citations,
            "modern_takeaway": response.modern_takeaway,
            "confidence": response.confidence,
            "honest_note": response.honest_note,
        }
        rendered = extract_stream_reply_text(json.dumps(payload, ensure_ascii=False))
        chunk_size = 4
        return [rendered[i:i + chunk_size] for i in range(0, len(rendered), chunk_size)]

    @staticmethod
    def _cached_structured_payload(cached: dict) -> dict:
        """Adapt the approved local cache structure to the common validator input."""
        quotes = cached.get("original_quotes", []) or []
        sources = cached.get("sources", []) or []
        citations = []
        for index, quote in enumerate(quotes):
            citations.append({
                "id": f"引{index + 1}",
                "出处": sources[index] if index < len(sources) else "",
                "原文": quote,
            })
        return {
            "reply": cached.get("content", ""),
            "citations": citations,
            "modern_takeaway": cached.get("vernacular", ""),
            "confidence": "low",
            "honest_note": cached.get("disclaimer"),
        }

    async def _yield_cached_reply(
        self, cached: dict
    ) -> AsyncGenerator[str, None]:
        """
        把缓存的结构化回答拆成流式 chunks 输出，
        模拟打字机效果，统一使用 <<<TAG>>> 标记格式（与 LLM 输出一致）。

        输出结构：
          <<<QUOTE>>>
          （原文）
          <<<SOURCE>>>
          （出处）
          <<<CLASSICAL>>>
          （孔子口吻回应正文）
          <<<VERNACULAR>>>
          （白话点睛）
          <<<DISCLAIMER>>>
          （免责声明）
        """
        import asyncio

        content: str = cached.get("content", "")
        vernacular: str = cached.get("vernacular", "")
        disclaimer: str = cached.get("disclaimer", pt.DISCLAIMER_SAGE)
        quotes: list = cached.get("original_quotes", [])
        sources: list = cached.get("sources", [])

        # 拼接为统一的 <<<TAG>>> 格式
        quote_text = quotes[0] if quotes else "无"
        source_text = sources[0] if sources else "无"

        parts = [
            f"<<<QUOTE>>>\n{quote_text}",
            f"<<<SOURCE>>>\n{source_text}",
            f"<<<CLASSICAL>>>\n{content}",
            f"<<<VERNACULAR>>>\n{vernacular}",
            f"<<<DISCLAIMER>>>\n{disclaimer}",
        ]

        full = "\n".join(parts)
        chunk_size = 4
        for i in range(0, len(full), chunk_size):
            yield full[i : i + chunk_size]
            await asyncio.sleep(0.02)

    async def chat_with_sage_full(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
    ) -> tuple:
        """非流式版本，返回 (reply_text, references)"""
        chunks = []
        async for chunk in self.chat_with_sage(sage, question, history, stream=False):
            chunks.append(chunk)
        reply = "".join(chunks)

        # 若命中缓存，references 从缓存的原文/出处构造
        cached = sage_cache.match_safe_qa(question)
        if cached is not None:
            refs = []
            quotes = cached.get("original_quotes", [])
            sources = cached.get("sources", [])
            for idx, q in enumerate(quotes):
                src = sources[idx] if idx < len(sources) else ""
                refs.append(RAGReference(
                    text=q,
                    source=src,
                    similarity=1.0,
                ))
            return reply, refs

        # 未命中缓存：从 RAG 专用检索结果构造 references
        rag = get_rag_service()
        sage_result = await rag.retrieve_for_sage_chat(question, top_k=settings.RAG_TOP_K)
        refs = []
        for v in sage_result.get("verses", []):
            refs.append(RAGReference(
                text=v.get("original", ""),
                source=v.get("source", "未知"),
                chapter=v.get("chapter"),
                similarity=v.get("similarity", 0.0),
            ))
        for c in sage_result.get("commentaries", []):
            refs.append(RAGReference(
                text=f"{c.get('original','')}（{c.get('commentary','')}）",
                source=c.get("source", "朱熹《论语集注》"),
                chapter=c.get("chapter"),
                similarity=c.get("similarity", 0.0),
            ))
        return reply, refs

    # ----------------------------------------------------------
    # 引用校验机制
    # ----------------------------------------------------------
    def _validate_citations(
        self, citations: List[dict], rag_refs: List[dict]
    ) -> tuple[List[Citation], bool]:
        """Validate citations through the shared CitationGuard for both transports."""
        from app.services.citation_guard import guard_citations

        guarded, status = guard_citations(citations, rag_refs=rag_refs)
        validated: List[Citation] = []
        for item in guarded:
            source = item.correct_source if item.trust_state == "citation_corrected" and item.correct_source else item.source
            validated.append(Citation(
                id=item.citation_id,
                source=source,
                original=item.original,
                verifiable=item.verifiable,
                verification_status=item.trust_state,
            ))
        return validated, status == "all_verified"

    def _build_citations_from_cache(
        self, cached: dict, rag_refs: Optional[List[dict]] = None
    ) -> List[Citation]:
        """Validate cache citations only against independently retrieved refs."""
        quotes = cached.get("original_quotes", []) or []
        sources = cached.get("sources", []) or []
        candidates = [
            {"id": f"引{idx + 1}", "出处": sources[idx] if idx < len(sources) else "", "原文": quote}
            for idx, quote in enumerate(quotes)
        ]
        validated, _ = self._validate_citations(candidates, list(rag_refs or []))
        return validated

    def build_stream_fallback_response(
        self, sage: str, cached: dict, sage_result: Optional[dict] = None
    ) -> ChatSageResponse:
        """Construct a fallback response and validate citations against available RAG refs."""
        refs = list((sage_result or {}).get("verses", [])) + list((sage_result or {}).get("commentaries", []))
        citations = self._build_citations_from_cache(cached, refs)
        return ChatSageResponse(
            sage=sage,
            reply=cached.get("content", ""),
            disclaimer=cached.get("disclaimer", pt.DISCLAIMER_SAGE),
            citations=citations,
            modern_takeaway=cached.get("vernacular", ""),
            confidence="low",
            honest_note="AI 服务暂时不可用，已返回预设回答。",
        )

    # ----------------------------------------------------------
    # 3. 与圣贤对话（增强版：结构化 JSON 输出 + 引用校验）
    # ----------------------------------------------------------
    async def chat_with_sage_structured(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
    ) -> ChatSageResponse:
        """
        与圣贤对话的结构化版本，返回带 citations 的完整响应。
        
        流程：
        1. 优先检查安全问答缓存
        2. RAG 检索 → LLM 生成 JSON → 解析
        3. 引用校验：对 citations 逐条与 RAG 语料做精确匹配
        4. 若有不可溯源引用 → 触发诚实降级
        """
        history = history or []

        # ----- 0. 优先检查安全问答缓存 -----
        cached = sage_cache.match_safe_qa(question)
        if cached is not None:
            logger.info("chat_with_sage_structured 命中安全问答缓存: %s", cached.get("cache_key"))
            rag = get_rag_service()
            sage_result = await rag.retrieve_for_sage_chat(question, top_k=settings.RAG_TOP_K)
            return self.build_stream_fallback_response(sage, cached, sage_result)

        # ----- 1. RAG 检索 -----
        rag = get_rag_service()
        sage_result = await rag.retrieve_for_sage_chat(question, top_k=settings.RAG_TOP_K)
        rag_context = rag.build_sage_chat_context(sage_result)

        # 2. 构建 system prompt
        sys_prompt = build_sage_system_prompt(sage, rag_context)
        sage_name = get_sage_name(sage)

        # 3. 构建 messages（含历史）
        messages = [{"role": "system", "content": sys_prompt}]
        for h in history:
            role = h.get("role", "user")
            content = h.get("content", "")
            messages.append({"role": role, "content": content})

        # 检查是否有检索结果
        has_results = bool(sage_result.get("verses") or sage_result.get("commentaries"))
        user_msg = pt.SAGE_CHAT_USER.format(
            question=question,
            persona_name=sage_name,
            has_results="有" if has_results else "无",
        )
        messages.append({"role": "user", "content": user_msg})

        # Prepare retrieved evidence before provider invocation for safe fallback validation.
        rag_refs = list(sage_result.get("verses", [])) + list(sage_result.get("commentaries", []))
        # 4. 调 LLM（JSON 模式）
        try:
            data = await llm_client.complete_json(messages, temperature=0.8)
        except Exception:
            logger.error("chat_with_sage_structured LLM 调用失败；已使用缓存兜底")
            fallback = sage_cache.get_fallback_qa(question)
            citations = self._build_citations_from_cache(fallback, rag_refs)
            return ChatSageResponse(
                sage=sage,
                reply=fallback.get("content", ""),
                disclaimer=fallback.get("disclaimer", pt.DISCLAIMER_SAGE),
                citations=citations,
                modern_takeaway=fallback.get("vernacular", ""),
                confidence="low",
                honest_note="AI 服务暂时不可用，已返回预设回答。",
            )

        # 5. 解析 JSON 响应
        reply = data.get("reply", "")
        raw_citations = data.get("citations", [])
        modern_takeaway = data.get("modern_takeaway", "")
        confidence = data.get("confidence", "medium")
        honest_note = data.get("honest_note")

        # 6. 引用校验
        # 合并 RAG 原文用于校验
        rag_refs = []
        for v in sage_result.get("verses", []):
            rag_refs.append(v)
        for c in sage_result.get("commentaries", []):
            rag_refs.append(c)

        validated_citations, all_verified = self._validate_citations(raw_citations, rag_refs)

        # 7. 若有不可溯源引用，降级为诚实声明
        if not all_verified:
            unverified = [c for c in validated_citations if not c.verifiable and c.original != "无"]
            if unverified:
                logger.warning(
                    "发现 %d 条不可溯源引用，触发诚实降级", len(unverified)
                )
                # 将不可溯源的引用原文替换为提示
                for c in validated_citations:
                    if not c.verifiable and c.original != "无":
                        c.original = f"（该引用无法在语料库中溯源：{c.original[:20]}...）"
                # 降级置信度
                if confidence == "high":
                    confidence = "medium"
                honest_note = honest_note or "部分引用无法在经典原文中溯源，请谨慎参考。"

        return ChatSageResponse(
            sage=sage,
            reply=reply,
            disclaimer=pt.DISCLAIMER_SAGE,
            citations=validated_citations,
            modern_takeaway=modern_takeaway,
            confidence=confidence,
            honest_note=honest_note,
        )

    # ----------------------------------------------------------
    # 4. AI 生成测验题
    # ----------------------------------------------------------
    async def generate_quiz(
        self,
        verse_id: str,
        quiz_type: str = "choice",
        difficulty: str = "medium",
        count: int = 3,
        verse_text: Optional[str] = None,
    ) -> List[QuizQuestion]:
        """AI 生成测验题"""
        verse_text = verse_text or verse_id

        # 1. RAG 检索
        rag = get_rag_service()
        refs = await rag.retrieve(verse_text, top_k=settings.RAG_TOP_K)
        rag_context = rag.build_context_text(refs)

        # 2. 构建 prompt
        user_msg = pt.QUIZ_USER.format(
            verse_text=verse_text,
            rag_context=rag_context,
            count=count,
            quiz_type_desc=pt.QUIZ_TYPE_DESC.get(quiz_type, quiz_type),
            difficulty_desc=pt.QUIZ_DIFFICULTY_DESC.get(difficulty, difficulty),
        )
        messages = [
            {"role": "system", "content": pt.QUIZ_SYSTEM},
            {"role": "user", "content": user_msg},
        ]

        # 3. 调 LLM
        try:
            data = await llm_client.complete_json(messages, temperature=0.7)
        except Exception:
            # 不记录异常负载：SDK 异常文本可能含 Authorization/Bearer（401/403）。
            logger.error("generate_quiz LLM 调用失败")
            return []

        # 4. 解析题目列表
        if isinstance(data, dict):
            data = data.get("questions", [data])
        questions = []
        for item in data:
            questions.append(QuizQuestion(
                question=item.get("question", ""),
                options=item.get("options"),
                answer=item.get("answer", ""),
                explanation=item.get("explanation", ""),
                quiz_type=item.get("quiz_type", quiz_type),
                difficulty=item.get("difficulty", difficulty),
            ))
        return questions[:count]


# 全局单例
ai_service = AIService()

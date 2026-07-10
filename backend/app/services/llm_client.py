"""
悟典 - LLM 客户端封装

支持：
- OpenAI API 兼容协议（含 DeepSeek / Qwen / 本地 Ollama）
- 流式响应（streaming）
- 错误处理与指数退避重试
- Token 计数与成本控制
- JSON 模式输出
"""
import asyncio
import json
import time
from typing import AsyncGenerator, Optional, Dict, Any, List

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 可选依赖：openai 未安装时降级运行
try:
    from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None
    APIError = Exception
    APIConnectionError = Exception
    RateLimitError = Exception


class TokenCounter:
    """简易 token 计数器（粗略估计：中文按字算，英文按空格分词）"""

    @staticmethod
    def estimate(text: str) -> int:
        if not text:
            return 0
        # 粗略：中文字符数 + 英文单词数
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_text = "".join(c if not ("\u4e00" <= c <= "\u9fff") else " " for c in text)
        english_words = len(other_text.split())
        return chinese_chars + english_words


class LLMClient:
    """LLM 客户端单例，封装 OpenAI 兼容协议调用"""

    _instance: Optional["LLMClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        if not HAS_OPENAI:
            logger.warning(
                "openai 包未安装，LLMClient 降级运行。"
                "安装后可启用 AI 功能：pip install openai>=1.10.0"
            )
            self.client = None
            self.model = settings.llm_config.get("model", "unknown")
            self.provider = settings.LLM_PROVIDER
            self.api_key_configured = False
            self.today_tokens = 0
            self.today_date = time.strftime("%Y-%m-%d")
            self._initialized = True
            return
        cfg = settings.llm_config
        api_key = cfg.get("api_key", "")
        # 检查 API_KEY 是否已配置（非空、非占位符）
        self.api_key_configured = bool(api_key and not api_key.startswith("sk-placeholder"))
        if not self.api_key_configured:
            logger.warning(
                f"LLM API_KEY 未配置（provider={settings.LLM_PROVIDER}）。"
                f"请在 backend/.env 中设置对应的 API_KEY。"
                f"AI 接口将返回降级回复。"
            )
            self.client = None
            self.model = cfg.get("model", "unknown")
            self.provider = settings.LLM_PROVIDER
            self.today_tokens = 0
            self.today_date = time.strftime("%Y-%m-%d")
            self._initialized = True
            return
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=cfg["base_url"],
            timeout=settings.LLM_TIMEOUT,
        )
        self.model = cfg["model"]
        self.provider = settings.LLM_PROVIDER
        self.today_tokens = 0
        self.today_date = time.strftime("%Y-%m-%d")
        self._initialized = True
        logger.info(f"LLMClient 初始化: provider={settings.LLM_PROVIDER}, model={self.model}")

    @property
    def is_available(self) -> bool:
        """LLM 客户端是否可用（openai 已安装且 API_KEY 已配置）"""
        return self.client is not None

    def _unavailable_error(self) -> str:
        """返回友好的不可用错误信息"""
        if not HAS_OPENAI:
            return (
                "AI 讲解功能未启用：未安装 openai 包。"
                "请运行 pip install openai>=1.10.0 安装后使用。"
            )
        if not self.api_key_configured:
            return (
                f"AI 讲解功能未启用：LLM_PROVIDER={self.provider} 的 API_KEY 未配置。"
                f"请在 backend/.env 文件中设置对应的 API_KEY 后重启服务。"
            )
        return "LLM 客户端未初始化，请检查配置。"

    # ----------------------------------------------------------
    # 内部：token 配额检查 & 重置
    # ----------------------------------------------------------
    def _reset_if_new_day(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.today_date:
            self.today_tokens = 0
            self.today_date = today

    def _check_quota(self, est_tokens: int):
        self._reset_if_new_day()
        if self.today_tokens + est_tokens > settings.DAILY_TOKEN_LIMIT:
            raise RuntimeError(
                f"已达每日 token 上限 ({settings.DAILY_TOKEN_LIMIT})，请明日再试。"
            )
        if self.today_tokens + est_tokens > settings.DAILY_TOKEN_LIMIT * settings.TOKEN_COST_WARN_RATIO:
            logger.warning(
                f"Token 用量预警: {self.today_tokens}/{settings.DAILY_TOKEN_LIMIT}"
            )

    def _record_tokens(self, prompt_tokens: int, completion_tokens: int):
        self._reset_if_new_day()
        self.today_tokens += prompt_tokens + completion_tokens

    # ----------------------------------------------------------
    # 内部：带重试的请求
    # ----------------------------------------------------------
    async def _retry_async(self, func, *args, **kwargs):
        last_err = None
        for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_err = e
                wait = settings.LLM_RETRY_DELAY * (2 ** attempt)
                logger.warning(f"RateLimit, 第 {attempt} 次重试，等待 {wait}s")
                await asyncio.sleep(wait)
            except APIConnectionError as e:
                last_err = e
                wait = settings.LLM_RETRY_DELAY * (2 ** attempt)
                logger.warning(f"ConnectionError, 第 {attempt} 次重试，等待 {wait}s")
                await asyncio.sleep(wait)
            except APIError as e:
                last_err = e
                # 5xx 重试，4xx 不重试
                if getattr(e, "status_code", 500) >= 500:
                    wait = settings.LLM_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"APIError {e.status_code}, 第 {attempt} 次重试")
                    await asyncio.sleep(wait)
                else:
                    raise
        raise last_err

    # ----------------------------------------------------------
    # 公开：普通补全
    # ----------------------------------------------------------
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """同步获取完整回复"""
        if self.client is None:
            raise RuntimeError(self._unavailable_error())
        est_in = sum(TokenCounter.estimate(m["content"]) for m in messages)
        self._check_quota(est_in)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await self._retry_async(self.client.chat.completions.create, **kwargs)
        content = resp.choices[0].message.content or ""
        usage = resp.usage
        if usage:
            self._record_tokens(usage.prompt_tokens, usage.completion_tokens)
        logger.info(
            f"LLM complete: in={usage.prompt_tokens if usage else est_in}, "
            f"out={usage.completion_tokens if usage else TokenCounter.estimate(content)}, "
            f"today_total={self.today_tokens}"
        )
        return content

    # ----------------------------------------------------------
    # 公开：流式补全
    # ----------------------------------------------------------
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成，yield 每个 token chunk 的文本"""
        if self.client is None:
            # 降级：yield 友好错误提示而非抛异常（保持流式接口契约）
            yield self._unavailable_error()
            return
        est_in = sum(TokenCounter.estimate(m["content"]) for m in messages)
        self._check_quota(est_in)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        completion_text = ""
        usage = None
        try:
            stream = await self._retry_async(self.client.chat.completions.create, **kwargs)
            async for chunk in stream:
                if chunk.usage:
                    usage = chunk.usage
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    completion_text += text
                    yield text
        finally:
            if usage:
                self._record_tokens(usage.prompt_tokens, usage.completion_tokens)
            else:
                self._record_tokens(est_in, TokenCounter.estimate(completion_text))
            logger.info(
                f"LLM stream done: out={TokenCounter.estimate(completion_text)}, "
                f"today_total={self.today_tokens}"
            )

    # ----------------------------------------------------------
    # 公开：JSON 输出（自动修复常见格式问题）
    # ----------------------------------------------------------
    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> Any:
        """获取 JSON 格式回复并解析"""
        if self.client is None:
            raise RuntimeError(self._unavailable_error())
        raw = await self.complete(
            messages, temperature=temperature, json_mode=True
        )
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> Any:
        """容错 JSON 解析：去掉 ```json 包裹、截取首个 { 到末尾 }"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试截取
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
            # 数组
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
            raise


# 全局单例
llm_client = LLMClient()

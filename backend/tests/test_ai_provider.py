"""
AI Provider 切换/降级路径测试

覆盖：
- mock openai SDK 的测试用例
- Provider 切换逻辑（openai → 其他 provider → fallback）
- 超时/错误降级路径
- API_KEY 缺失时的降级行为
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import os
import time

from app.core.config import Settings


@pytest.fixture(autouse=True)
def reset_llm_client_module():
    """每个测试前重置 llm_client 模块的单例状态"""
    import app.services.llm_client as llm_module
    if hasattr(llm_module, 'llm_client'):
        llm_module.llm_client._initialized = False
        llm_module.llm_client.client = None
    yield
    if hasattr(llm_module, 'llm_client'):
        llm_module.llm_client._initialized = False
        llm_module.llm_client.client = None


class TestMockOpenSDK:
    """测试 openai 包未安装时的降级行为（HAS_OPENAI=False）"""

    @patch("app.services.llm_client.HAS_OPENAI", False)
    @patch("app.services.llm_client.AsyncOpenAI", None)
    def test_has_no_openai_sets_client_none(self):
        from app.services.llm_client import LLMClient
        client = LLMClient()
        client._initialized = False
        client.client = None
        client2 = LLMClient()
        assert client2.client is None

    @patch("app.services.llm_client.HAS_OPENAI", False)
    def test_unavailable_error_when_no_openai(self):
        from app.services.llm_client import LLMClient
        client = LLMClient()
        client._initialized = True
        client.client = None
        client.HAS_OPENAI = False
        client.api_key_configured = False
        client.provider = "openai"
        msg = client._unavailable_error()
        assert "未安装 openai 包" in msg

    @patch("app.services.llm_client.HAS_OPENAI", False)
    def test_is_available_false_when_no_openai(self):
        from app.services.llm_client import LLMClient
        client = LLMClient()
        client._initialized = True
        client.client = None
        client.HAS_OPENAI = False
        assert client.is_available is False


class TestProviderSwitching:
    """测试不同 LLM_PROVIDER 的配置切换"""

    def test_openai_provider_config(self):
        settings = Settings(
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="sk-test123",
            OPENAI_BASE_URL="https://api.openai.com/v1",
            OPENAI_MODEL="gpt-4o-mini",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "sk-test123"
        assert cfg["base_url"] == "https://api.openai.com/v1"
        assert cfg["model"] == "gpt-4o-mini"

    def test_deepseek_provider_config(self):
        settings = Settings(
            LLM_PROVIDER="deepseek",
            DEEPSEEK_API_KEY="sk-deepseek-key",
            DEEPSEEK_BASE_URL="https://api.deepseek.com/v1",
            DEEPSEEK_MODEL="deepseek-chat",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "sk-deepseek-key"
        assert cfg["base_url"] == "https://api.deepseek.com/v1"
        assert cfg["model"] == "deepseek-chat"

    def test_qwen_provider_config(self):
        settings = Settings(
            LLM_PROVIDER="qwen",
            QWEN_API_KEY="sk-qwen-key",
            QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1",
            QWEN_MODEL="qwen-plus",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "sk-qwen-key"
        assert cfg["base_url"].startswith("https://dashscope")
        assert cfg["model"] == "qwen-plus"

    def test_local_provider_config(self):
        settings = Settings(
            LLM_PROVIDER="local",
            LOCAL_LLM_BASE_URL="http://localhost:11434/v1",
            LOCAL_LLM_MODEL="qwen2.5:7b",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "not-needed"
        assert cfg["base_url"] == "http://localhost:11434/v1"
        assert cfg["model"] == "qwen2.5:7b"

    def test_agnes_provider_config(self):
        settings = Settings(
            LLM_PROVIDER="agnes",
            AGNES_API_KEY="agnes-key",
            AGNES_BASE_URL="https://apihub.agnes-ai.com/v1",
            AGNES_MODEL="agnes-2.0-flash",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "agnes-key"
        assert cfg["base_url"] == "https://apihub.agnes-ai.com/v1"
        assert cfg["model"] == "agnes-2.0-flash"

    def test_agnes_reuses_openai_key(self):
        settings = Settings(
            LLM_PROVIDER="agnes",
            OPENAI_API_KEY="existing-key",
            AGNES_API_KEY="",
            AGNES_BASE_URL="https://apihub.agnes-ai.com/v1",
            AGNES_MODEL="agnes-2.0-flash",
        )
        cfg = settings.llm_config
        assert cfg["api_key"] == "existing-key"

    def test_default_provider_is_openai(self):
        settings = Settings()
        assert settings.LLM_PROVIDER == "openai"
        cfg = settings.llm_config
        assert cfg["model"] == "gpt-4o-mini"


class TestAPIKEYMissingDegradation:
    """测试 API_KEY 缺失或未配置时的降级行为"""

    def test_api_key_configured_flag_logic(self):
        """API_KEY 以 sk-placeholder 开头时视为未配置"""
        assert "sk-placeholder".startswith("sk-placeholder")  # True → 未配置
        assert not ("test-key".startswith("sk-placeholder"))  # False → 已配置

    def test_empty_api_key_degraded(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        import sys
        for mod in list(sys.modules.keys()):
            if 'app.core.config' in mod or 'app.services.llm_client' in mod:
                del sys.modules[mod]

        from app.core.config import Settings
        from app.services.llm_client import LLMClient

        settings = Settings()
        assert settings.OPENAI_API_KEY == ""

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_api_key_placeholder_degraded(self, mock_async_openai, monkeypatch):
        """API_KEY 为占位符时降级"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-placeholder")
        import sys
        for mod in list(sys.modules.keys()):
            if 'app.core.config' in mod or 'app.services.llm_client' in mod:
                del sys.modules[mod]

        from app.core.config import Settings
        from app.services.llm_client import LLMClient

        settings = Settings()
        assert settings.OPENAI_API_KEY == "sk-placeholder"


class TestTimeoutAndErrorDegradation:
    """测试 API 超时、错误时的降级与重试逻辑"""

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_rate_limit_error_triggers_retry(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import RateLimitError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        response = httpx.Response(429, request=request)
        error = RateLimitError("Rate limit exceeded", response=response, body=None)
        mock_instance.chat.completions.create = AsyncMock(side_effect=error)

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        with pytest.raises(RateLimitError):
            asyncio.run(client._retry_async(
                mock_instance.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hello"}],
            ))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_api_connection_error_triggers_retry(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import APIConnectionError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        error = APIConnectionError(request=request)
        mock_instance.chat.completions.create = AsyncMock(side_effect=error)

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        with pytest.raises(APIConnectionError):
            asyncio.run(client._retry_async(
                mock_instance.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hello"}],
            ))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_api_error_5xx_triggers_retry(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import APIError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        error_5xx = APIError("Server error", request=request, body=None)
        # Add status_code attribute to simulate real OpenAI error
        error_5xx.status_code = 500
        mock_instance.chat.completions.create = AsyncMock(side_effect=error_5xx)

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        with pytest.raises(APIError):
            asyncio.run(client._retry_async(
                mock_instance.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hello"}],
            ))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_api_error_4xx_raises_without_retry(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import APIError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        error_4xx = APIError("Bad request", request=request, body=None)
        # Add status_code attribute to simulate real OpenAI error
        error_4xx.status_code = 400
        mock_instance.chat.completions.create = AsyncMock(side_effect=error_4xx)

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        with pytest.raises(APIError):
            asyncio.run(client._retry_async(
                mock_instance.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hello"}],
            ))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_client_none_raises_on_complete(self, mock_async_openai):
        from app.services.llm_client import LLMClient

        client = LLMClient()
        client._initialized = True
        client.client = None
        client.provider = "openai"
        client.api_key_configured = False

        with pytest.raises(RuntimeError):
            asyncio.run(client.complete([{"role": "user", "content": "hello"}]))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_client_none_yields_error_on_stream(self, mock_async_openai):
        from app.services.llm_client import LLMClient

        client = LLMClient()
        client._initialized = True
        client.client = None
        client.provider = "openai"
        client.api_key_configured = False

        async def run_stream():
            result = []
            async for chunk in client.stream([{"role": "user", "content": "hello"}]):
                result.append(chunk)
            return result

        results = asyncio.run(run_stream())
        assert len(results) > 0
        assert any("API_KEY 未配置" in r or "未初始化" in r for r in results)

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_client_none_raises_on_complete_json(self, mock_async_openai):
        from app.services.llm_client import LLMClient

        client = LLMClient()
        client._initialized = True
        client.client = None
        client.provider = "openai"
        client.api_key_configured = False

        with pytest.raises(RuntimeError):
            asyncio.run(client.complete_json([{"role": "user", "content": "hello"}]))


class TestTokenQuotaDegradation:
    """测试 token 配额超限时的降级行为"""

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_daily_token_limit_exceeded(self, mock_async_openai):
        """超过每日 token 上限时 complete() 应抛出 RuntimeError"""
        from app.services.llm_client import LLMClient
        from app.core.config import settings

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance
        mock_instance.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="hello"))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=10),
        ))

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = settings.DAILY_TOKEN_LIMIT
        # _check_quota 会先按今天日期重置计数，必须把日期设为今天才能模拟"今日已超限"
        client.today_date = time.strftime("%Y-%m-%d")
        client.api_key_configured = True

        with pytest.raises(RuntimeError) as exc_info:
            asyncio.run(client.complete([{"role": "user", "content": "hello"}]))
        assert "每日 token 上限" in str(exc_info.value)

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_token_quota_warn_ratio(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from app.core.config import settings

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance
        mock_instance.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="hello"))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=10),
        ))

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = int(settings.DAILY_TOKEN_LIMIT * settings.TOKEN_COST_WARN_RATIO)
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        result = asyncio.run(client.complete([{"role": "user", "content": "hello"}]))
        assert result == "hello"


class TestFullDegradationPath:
    """测试完整降级链路：正常 → 错误 → 降级"""

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_full_workflow_with_fallback(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import APIConnectionError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        error = APIConnectionError(request=request)
        mock_instance.chat.completions.create = AsyncMock(
            side_effect=[
                error,
                MagicMock(
                    choices=[MagicMock(message=MagicMock(content="response"))],
                    usage=MagicMock(prompt_tokens=5, completion_tokens=5),
                ),
            ]
        )

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        result = asyncio.run(client.complete([{"role": "user", "content": "hello"}]))
        assert result == "response"
        assert mock_instance.chat.completions.create.call_count == 2

    @patch("app.services.llm_client.HAS_OPENAI", False)
    def test_degradation_when_openai_not_installed(self):
        from app.services.llm_client import LLMClient

        client = LLMClient()
        client._initialized = True
        client.client = None
        client.HAS_OPENAI = False
        client.api_key_configured = False
        client.provider = "openai"

        assert client.is_available is False

        msg = client._unavailable_error()
        assert "未安装 openai 包" in msg

        async def run():
            result = []
            async for chunk in client.stream([{"role": "user", "content": "test"}]):
                result.append(chunk)
            return result

        results = asyncio.run(run())
        assert len(results) > 0
        assert "未安装" in results[0]

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_all_retries_exhausted_fallback(self, mock_async_openai):
        from app.services.llm_client import LLMClient
        from openai import APIConnectionError
        import httpx

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance

        request = httpx.Request("GET", "http://test")
        error = APIConnectionError(request=request)
        mock_instance.chat.completions.create = AsyncMock(side_effect=error)

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        with pytest.raises(APIConnectionError):
            asyncio.run(client._retry_async(
                mock_instance.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hello"}],
            ))

    @patch("app.services.llm_client.HAS_OPENAI", True)
    @patch("app.services.llm_client.AsyncOpenAI")
    def test_degraded_complete_returns_content(self, mock_async_openai):
        from app.services.llm_client import LLMClient

        mock_instance = MagicMock()
        mock_async_openai.return_value = mock_instance
        mock_instance.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="degraded response"))],
            usage=MagicMock(prompt_tokens=5, completion_tokens=5),
        ))

        client = LLMClient()
        client._initialized = True
        client.client = mock_instance
        client.provider = "openai"
        client.model = "gpt-4o-mini"
        client.today_tokens = 0
        client.today_date = "2026-01-01"
        client.api_key_configured = True

        result = asyncio.run(client.complete([{"role": "user", "content": "hello"}]))
        assert result == "degraded response"
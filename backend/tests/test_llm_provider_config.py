from app.core.config import Settings


def test_agnes_provider_uses_openai_compatible_endpoint():
    settings = Settings(
        LLM_PROVIDER="agnes",
        AGNES_API_KEY="agnes-key",
        AGNES_BASE_URL="https://apihub.agnes-ai.com/v1",
        AGNES_MODEL="agnes-2.0-flash",
    )

    assert settings.llm_config == {
        "api_key": "agnes-key",
        "base_url": "https://apihub.agnes-ai.com/v1",
        "model": "agnes-2.0-flash",
    }


def test_agnes_provider_can_reuse_existing_openai_key_for_local_migration():
    settings = Settings(
        LLM_PROVIDER="agnes",
        OPENAI_API_KEY="existing-key",
        AGNES_API_KEY="",
        AGNES_BASE_URL="https://apihub.agnes-ai.com/v1",
        AGNES_MODEL="agnes-2.0-flash",
    )

    assert settings.llm_config["api_key"] == "existing-key"

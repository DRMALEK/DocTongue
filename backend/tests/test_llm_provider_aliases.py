from app.core.config import Settings
from app.services.llm import _normalize_model_name, _resolve_api_key, _uses_litellm_provider


def test_uses_litellm_provider_accepts_common_aliases() -> None:
    assert _uses_litellm_provider("litellm") is True
    assert _uses_litellm_provider("openai") is True
    assert _uses_litellm_provider("anthropic") is True
    assert _uses_litellm_provider("gemini") is True


def test_normalize_model_name_prefixes_provider_when_needed() -> None:
    assert _normalize_model_name("openai", "gpt-4o-mini") == "openai/gpt-4o-mini"
    assert _normalize_model_name("anthropic", "claude-3-5-sonnet") == "anthropic/claude-3-5-sonnet"
    assert _normalize_model_name("litellm", "gpt-4o-mini") == "gpt-4o-mini"
    assert _normalize_model_name("openai", "openai/gpt-4o-mini") == "openai/gpt-4o-mini"


def test_resolve_api_key_uses_provider_specific_fallback() -> None:
    settings = Settings(openai_api_key="dummy-openai-key")
    assert _resolve_api_key("openai", None, settings) == "dummy-openai-key"
    assert _resolve_api_key("litellm", None, settings) == "dummy-openai-key"
"""Tests for the FastAPI application and ProviderFactory."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.llm.provider_factory import ProviderFactory
from backend.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """GET /api/health returns 200 and ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_provider_factory_defaults_to_groq() -> None:
    """ProviderFactory uses groq when no override is given."""
    factory = ProviderFactory()
    assert factory.provider == "groq"


def test_provider_factory_rejects_unknown() -> None:
    """ProviderFactory raises ValueError for unknown providers."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        ProviderFactory(provider="foobar")


def test_provider_factory_resolve_model() -> None:
    """_resolve_model returns a model string with correct prefix."""
    factory = ProviderFactory(provider="groq")
    model = factory._resolve_model()
    assert model.startswith("groq/")


def test_provider_factory_resolve_model_explicit() -> None:
    """Explicit model string is returned as-is."""
    factory = ProviderFactory(provider="openai")
    model = factory._resolve_model("my-custom-model")
    assert model == "my-custom-model"


def test_provider_factory_missing_api_key() -> None:
    """_resolve_api_key raises when the key env var is empty."""
    factory = ProviderFactory(provider="openai")
    with pytest.raises(ValueError, match="API key"):
        factory._resolve_api_key()


@pytest.mark.asyncio
async def test_provider_factory_completion_calls_litellm() -> None:
    """completion() delegates to litellm.acompletion."""
    mock_usage = AsyncMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30

    mock_choice = AsyncMock()
    mock_choice.message.content = "mocked response"

    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    with (
        patch("backend.llm.provider_factory.litellm.acompletion", return_value=mock_response) as mock_acompletion,
        patch.object(ProviderFactory, "_resolve_api_key", return_value="fake-key"),
    ):
        factory = ProviderFactory(provider="groq")
        result = await factory.completion(messages=[{"role": "user", "content": "hi"}])

    mock_acompletion.assert_awaited_once()
    assert result.content == "mocked response"
    assert result.provider == "groq"
    assert result.usage["total_tokens"] == 30

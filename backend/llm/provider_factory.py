"""Multi-LLM Adapter using LiteLLM with dynamic provider switching."""

from typing import Any

import litellm
from pydantic import BaseModel

from backend.core.config import settings


class LLMResponse(BaseModel):
    """Structured response from the LLM layer."""

    content: str
    model: str
    provider: str
    usage: dict[str, int]


class ProviderFactory:
    """Factory that routes LLM calls through LiteLLM.

    Supports dynamic switching between Groq, Claude (Anthropic),
    and OpenAI via the ``LLM_PROVIDER`` environment variable.
    """

    PROVIDER_MAP: dict[str, dict[str, str]] = {
        "groq": {
            "model_prefix": "groq/",
            "env_key": "GROQ_API_KEY",
        },
        "openai": {
            "model_prefix": "",
            "env_key": "OPENAI_API_KEY",
        },
        "anthropic": {
            "model_prefix": "",
            "env_key": "ANTHROPIC_API_KEY",
        },
    }

    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or settings.llm_provider).lower()
        if self.provider not in self.PROVIDER_MAP:
            raise ValueError(
                f"Unsupported provider '{self.provider}'. "
                f"Choose from: {', '.join(self.PROVIDER_MAP)}"
            )

    def _resolve_model(self, model: str | None = None) -> str:
        """Return the fully-qualified model string for LiteLLM."""
        if model:
            return model

        model_name: str
        if self.provider == "groq":
            model_name = settings.groq_model
        elif self.provider == "anthropic":
            model_name = settings.anthropic_model
        elif self.provider == "openai":
            model_name = settings.openai_model
        else:
            raise ValueError(f"No default model for provider '{self.provider}'")

        prefix = self.PROVIDER_MAP[self.provider]["model_prefix"]
        return f"{prefix}{model_name}"

    def _resolve_api_key(self) -> str:
        """Return the API key for the active provider."""
        env_key = self.PROVIDER_MAP[self.provider]["env_key"]
        api_key: str = getattr(settings, env_key.lower(), "")
        if not api_key:
            raise ValueError(
                f"API key for provider '{self.provider}' is not set. "
                f"Please set the {env_key} environment variable."
            )
        return api_key

    async def completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send an async chat-completion request via LiteLLM."""
        resolved_model = self._resolve_model(model)
        api_key = self._resolve_api_key()

        response = await litellm.acompletion(
            model=resolved_model,
            messages=messages,
            api_key=api_key,
            **kwargs,
        )

        usage = response.usage  # type: ignore[union-attr]
        return LLMResponse(
            content=response.choices[0].message.content,  # type: ignore[union-attr, index]
            model=resolved_model,
            provider=self.provider,
            usage={
                "prompt_tokens": usage.prompt_tokens,  # type: ignore[union-attr]
                "completion_tokens": usage.completion_tokens,  # type: ignore[union-attr]
                "total_tokens": usage.total_tokens,  # type: ignore[union-attr]
            },
        )

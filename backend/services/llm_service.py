"""LLM service wrappers using the ProviderFactory."""

from backend.llm.provider_factory import LLMResponse, ProviderFactory


async def summarize_text(text: str, provider: str | None = None) -> LLMResponse:
    """Summarize the given text using the active LLM provider."""
    factory = ProviderFactory(provider=provider)
    messages = [
        {"role": "system", "content": "You are a concise summarizer. Return a brief summary."},
        {"role": "user", "content": text},
    ]
    return await factory.completion(messages=messages)

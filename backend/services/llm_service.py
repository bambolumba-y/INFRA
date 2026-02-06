"""LLM service wrappers using the ProviderFactory."""

from backend.llm.provider_factory import LLMResponse, ProviderFactory

SUMMARIZE_SYSTEM = (
    "You are a concise news summarizer for an intelligence terminal. "
    "Return a brief 2-3 sentence summary capturing the key facts."
)


async def summarize_text(text: str, provider: str | None = None) -> LLMResponse:
    """Summarize the given text using the active LLM provider."""
    factory = ProviderFactory(provider=provider)
    messages = [
        {"role": "system", "content": SUMMARIZE_SYSTEM},
        {"role": "user", "content": text[:4000]},
    ]
    return await factory.completion(messages=messages)


async def summarize_news_item(
    title: str, body: str, source: str, provider: str | None = None
) -> str:
    """Summarize a scraped news item, returning just the summary string."""
    prompt = f"Source: {source}\nTitle: {title}\n\n{body}"
    result = await summarize_text(prompt, provider=provider)
    return result.content

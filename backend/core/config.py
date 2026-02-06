"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from .env / environment."""

    app_env: str = "development"
    app_debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://infra:infra@localhost:5432/infra"

    # LLM
    llm_provider: str = "groq"
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Telegram
    telegram_bot_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

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

    # Admin
    admin_ids: list[int] = []  # Telegram user IDs allowed to access /admin

    # Encryption key for storing sensitive data (Fernet key, base64-encoded)
    encryption_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_channels: str = ""  # comma-separated list of channels
    telegram_session_string: str = ""  # Telethon StringSession
    telegram_phone: str = ""  # phone number for user session login

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "INFRA/0.1 (intelligence terminal)"
    reddit_subreddits: str = "programming,cscareerquestions,localllama"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_host: str = "localhost"
    chroma_port: int = 8100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

"""Database models defined with SQLModel (Pydantic v2 + SQLAlchemy)."""

from datetime import UTC, datetime

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Telegram user stored in PostgreSQL."""

    __tablename__ = "users"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(unique=True, index=True)
    preferences: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    sub_tier: str = Field(default="free")
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Content(SQLModel, table=True):
    """Scraped/aggregated content item."""

    __tablename__ = "content"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    source_type: str = Field(index=True)
    raw_text: str = Field(sa_column=Column(Text, nullable=False))
    summary: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    vector_id: str | None = None
    sentiment_score: float | None = None
    url: str | None = None
    title: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserResume(SQLModel, table=True):
    """Uploaded and parsed resume."""

    __tablename__ = "user_resumes"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    extracted_data: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    s3_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Job(SQLModel, table=True):
    """Job listing scraped from various sources."""

    __tablename__ = "jobs"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    company: str
    salary_min: float | None = None
    salary_max: float | None = None
    requirements_vector: str | None = None
    url: str | None = None
    source: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapingSource(SQLModel, table=True):
    """Configurable scraping source stored in the database."""

    __tablename__ = "scraping_sources"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    source_type: str = Field(index=True)  # telegram, reddit, rss
    name: str  # channel/subreddit/feed name
    enabled: bool = Field(default=True)
    interval_minutes: int = Field(default=15)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

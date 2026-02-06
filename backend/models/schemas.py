"""Database models defined with SQLModel (Pydantic v2 + SQLAlchemy)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Telegram user stored in PostgreSQL."""

    __tablename__ = "users"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(unique=True, index=True)
    preferences: dict | None = Field(default=None, sa_type_kwargs={"astext_type": None})
    sub_tier: str = Field(default="free")
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Content(SQLModel, table=True):
    """Scraped/aggregated content item."""

    __tablename__ = "content"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    source_type: str
    raw_text: str
    summary: str | None = None
    vector_id: str | None = None
    sentiment_score: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserResume(SQLModel, table=True):
    """Uploaded and parsed resume."""

    __tablename__ = "user_resumes"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    extracted_data: dict | None = None
    s3_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Job(SQLModel, table=True):
    """Job listing scraped from various sources."""

    __tablename__ = "jobs"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    title: str
    company: str
    salary_min: float | None = None
    salary_max: float | None = None
    requirements_vector: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

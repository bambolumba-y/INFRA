"""API routes for the INFRA Intelligence Terminal."""

from __future__ import annotations

import base64
import logging

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import require_tma_auth
from backend.core.config import settings
from backend.core.database import get_session
from backend.models.schemas import Content, Job, User, UserResume
from backend.services.career_service import (
    extract_resume_data,
    match_resume_to_job,
    parse_resume_pdf,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return application health status."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------


class NewsFilters(BaseModel):
    source_type: str | None = None
    min_score: float | None = None
    limit: int = 50


@router.get("/news")
async def list_news(
    source_type: str | None = None,
    min_score: float | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Filtered and summarized news feed."""
    stmt = select(Content).order_by(Content.created_at.desc()).limit(limit)  # type: ignore[union-attr]
    if source_type:
        stmt = stmt.where(Content.source_type == source_type)
    if min_score is not None:
        stmt = stmt.where(Content.sentiment_score >= min_score)  # type: ignore[operator]

    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "source_type": r.source_type,
            "title": r.title,
            "summary": r.summary,
            "sentiment_score": r.sentiment_score,
            "url": r.url,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Resume upload
# ---------------------------------------------------------------------------


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = 1,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Upload and process a CV (PDF)."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    text = await parse_resume_pdf(file_bytes)
    extracted = await extract_resume_data(text)

    resume = UserResume(
        user_id=user_id,
        extracted_data=extracted,
        s3_path=None,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)

    return {
        "id": resume.id,
        "extracted_data": resume.extracted_data,
    }


# ---------------------------------------------------------------------------
# Job matches
# ---------------------------------------------------------------------------


@router.get("/jobs/matches")
async def job_matches(
    user_id: int = 1,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Return high-percentage job matches for a user's latest resume."""
    # Fetch latest resume
    stmt = (
        select(UserResume)
        .where(UserResume.user_id == user_id)
        .order_by(UserResume.created_at.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if not resume or not resume.extracted_data:
        return []

    # Fetch jobs
    jobs_result = await session.execute(select(Job).limit(50))
    jobs = jobs_result.scalars().all()

    matches: list[dict] = []
    for job in jobs:
        description = f"{job.title} at {job.company}"
        if job.salary_min:
            description += f" (${job.salary_min}-${job.salary_max})"
        try:
            match = await match_resume_to_job(resume.extracted_data, description)
            if match.get("match_percentage", 0) >= 30:
                matches.append(
                    {
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        **match,
                    }
                )
        except Exception:
            logger.exception("Match scoring failed for job %s", job.id)

    matches.sort(key=lambda m: m.get("match_percentage", 0), reverse=True)
    return matches


# ---------------------------------------------------------------------------
# Settings / API keys
# ---------------------------------------------------------------------------


class APIKeysPayload(BaseModel):
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


def _get_fernet() -> Fernet:
    """Return a Fernet instance from the configured encryption key."""
    key = settings.encryption_key
    if not key:
        raise HTTPException(
            status_code=500, detail="Encryption key not configured"
        )
    return Fernet(key.encode())


def _encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    return _get_fernet().encrypt(value.encode()).decode()


@router.post("/settings/keys")
async def save_api_keys(
    payload: APIKeysPayload,
    user: dict = Depends(require_tma_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Store user-provided API keys in their preferences (encrypted)."""
    user_id = user.get("id", 1)
    result = await session.execute(select(User).where(User.tg_id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        db_user = User(tg_id=user_id, preferences={})
        session.add(db_user)

    prefs = db_user.preferences or {}
    if payload.groq_api_key is not None:
        prefs["groq_api_key"] = _encrypt_value(payload.groq_api_key)
    if payload.openai_api_key is not None:
        prefs["openai_api_key"] = _encrypt_value(payload.openai_api_key)
    if payload.anthropic_api_key is not None:
        prefs["anthropic_api_key"] = _encrypt_value(payload.anthropic_api_key)
    db_user.preferences = prefs

    await session.commit()
    return {"status": "saved"}

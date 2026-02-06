"""Admin API routes for managing scraping sources and system settings."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import require_tma_auth
from backend.core.config import settings
from backend.core.database import get_session
from backend.models.schemas import ScrapingSource
from backend.services.scheduler import scheduler

admin_router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(user: dict = Depends(require_tma_auth)) -> dict:
    """Verify authenticated user is in the ADMIN_IDS list.

    Fail-closed: if ADMIN_IDS is empty, no one gets admin access.
    """
    if not settings.admin_ids:
        raise HTTPException(status_code=403, detail="Admin access denied — no admins configured")
    if user.get("id") not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Admin access denied")
    return user


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SourceCreate(BaseModel):
    source_type: str  # telegram, reddit, rss
    name: str
    enabled: bool = True
    interval_minutes: int = 15


class SourceUpdate(BaseModel):
    enabled: bool | None = None
    interval_minutes: int | None = None


class SourceResponse(BaseModel):
    id: int
    source_type: str
    name: str
    enabled: bool
    interval_minutes: int
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Source management
# ---------------------------------------------------------------------------


@admin_router.get("/sources", response_model=list[SourceResponse])
async def list_sources(
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(require_admin),
) -> list[SourceResponse]:
    """List all configured scraping sources."""
    result = await session.execute(
        select(ScrapingSource).order_by(ScrapingSource.created_at.desc())
    )
    sources = result.scalars().all()
    return [
        SourceResponse(
            id=s.id,  # type: ignore[arg-type]
            source_type=s.source_type,
            name=s.name,
            enabled=s.enabled,
            interval_minutes=s.interval_minutes,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sources
    ]


@admin_router.post("/sources", response_model=SourceResponse, status_code=201)
async def create_source(
    payload: SourceCreate,
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(require_admin),
) -> SourceResponse:
    """Add a new scraping source."""
    if payload.source_type not in ("telegram", "reddit", "rss"):
        raise HTTPException(status_code=400, detail="Invalid source_type")

    source = ScrapingSource(
        source_type=payload.source_type,
        name=payload.name,
        enabled=payload.enabled,
        interval_minutes=payload.interval_minutes,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return SourceResponse(
        id=source.id,  # type: ignore[arg-type]
        source_type=source.source_type,
        name=source.name,
        enabled=source.enabled,
        interval_minutes=source.interval_minutes,
        created_at=source.created_at.isoformat(),
        updated_at=source.updated_at.isoformat(),
    )


@admin_router.patch("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    payload: SourceUpdate,
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(require_admin),
) -> SourceResponse:
    """Update an existing scraping source."""
    result = await session.execute(
        select(ScrapingSource).where(ScrapingSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if payload.enabled is not None:
        source.enabled = payload.enabled
    if payload.interval_minutes is not None:
        source.interval_minutes = payload.interval_minutes
    source.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(source)
    return SourceResponse(
        id=source.id,  # type: ignore[arg-type]
        source_type=source.source_type,
        name=source.name,
        enabled=source.enabled,
        interval_minutes=source.interval_minutes,
        created_at=source.created_at.isoformat(),
        updated_at=source.updated_at.isoformat(),
    )


@admin_router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(require_admin),
) -> None:
    """Remove a scraping source."""
    result = await session.execute(
        select(ScrapingSource).where(ScrapingSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await session.delete(source)
    await session.commit()


# ---------------------------------------------------------------------------
# System health
# ---------------------------------------------------------------------------


@admin_router.get("/health")
async def admin_health(
    _user: dict = Depends(require_admin),
) -> dict:
    """Return system health and scheduler status."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs,
    }

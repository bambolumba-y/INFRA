"""Health-check and core API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return application health status."""
    return {"status": "ok"}

"""Tests for Phase 3.5: admin access control, scraper rate limiting."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.admin import require_admin
from backend.core.auth import require_tma_auth
from backend.main import app


# ---------------------------------------------------------------------------
# Admin access control — ADMIN_IDS check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_admin_allows_listed_user() -> None:
    """require_admin passes when user ID is in ADMIN_IDS."""
    with patch("backend.api.admin.settings") as mock_settings:
        mock_settings.admin_ids = [42, 99]
        result = await require_admin(user={"id": 42, "first_name": "Admin"})
        assert result["id"] == 42


@pytest.mark.asyncio
async def test_require_admin_rejects_unlisted_user() -> None:
    """require_admin raises 403 when user ID is not in ADMIN_IDS."""
    from fastapi import HTTPException

    with patch("backend.api.admin.settings") as mock_settings:
        mock_settings.admin_ids = [42, 99]
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user={"id": 1, "first_name": "Intruder"})
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_rejects_when_empty() -> None:
    """require_admin denies access when ADMIN_IDS is empty (fail-closed)."""
    from fastapi import HTTPException

    with patch("backend.api.admin.settings") as mock_settings:
        mock_settings.admin_ids = []
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user={"id": 1, "first_name": "Anyone"})
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_health_blocked_for_non_admin() -> None:
    """GET /api/admin/health returns 403 for non-admin users."""
    with patch("backend.api.admin.settings") as mock_settings:
        mock_settings.admin_ids = [999]

        # Override TMA auth to return a non-admin user
        async def override_auth():
            return {"id": 1, "first_name": "NonAdmin"}

        app.dependency_overrides[require_tma_auth] = override_auth
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/admin/health")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Scraper rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_all_channels_applies_delay() -> None:
    """scrape_all_channels waits between channels to avoid bans."""
    scraper = MagicMock()
    scraper.scrape_channel = AsyncMock(return_value=[])

    with (
        patch("backend.scrapers.telegram_scraper.settings") as mock_settings,
        patch("backend.scrapers.telegram_scraper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_settings.telegram_channels = "chan1,chan2,chan3"
        mock_settings.telegram_api_id = 123
        mock_settings.telegram_api_hash = "abc"
        mock_settings.telegram_session_string = "session"

        from backend.scrapers.telegram_scraper import TelegramScraper

        real_scraper = TelegramScraper(api_id=123, api_hash="abc", session_string="s")
        # Mock scrape_channel to avoid real Telegram calls
        real_scraper.scrape_channel = AsyncMock(return_value=[])

        result = await real_scraper.scrape_all_channels(limit_per_channel=10)

        # Sleep should be called for channels after the first one (2 times for 3 channels)
        assert mock_sleep.await_count == 2
        # Verify delay is in range [2, 5]
        for call in mock_sleep.await_args_list:
            delay = call[0][0]
            assert 2.0 <= delay <= 5.0

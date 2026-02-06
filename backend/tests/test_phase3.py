"""Tests for Phase 3 features: auth, admin API, scheduler, scraper refactor."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from backend.core.auth import validate_init_data
from backend.main import app
from backend.models.schemas import ScrapingSource
from backend.scrapers.telegram_scraper import TelegramScraper
from backend.services.scheduler import scheduler


# ---------------------------------------------------------------------------
# Auth — initData validation
# ---------------------------------------------------------------------------


def _build_init_data(bot_token: str, user: dict) -> str:
    """Build a valid Telegram initData string for testing."""
    user_json = json.dumps(user)
    params = {
        "user": user_json,
        "auth_date": str(int(time.time())),
        "query_id": "test_query",
    }
    # Build data-check-string
    data_pairs = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_pairs)

    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    params["hash"] = computed_hash
    return urlencode(params)


def test_validate_init_data_valid() -> None:
    """validate_init_data returns user data for valid signature."""
    bot_token = "123456:ABC-DEF"
    user = {"id": 42, "first_name": "Test"}
    init_data = _build_init_data(bot_token, user)
    result = validate_init_data(init_data, bot_token)
    assert result["id"] == 42
    assert result["first_name"] == "Test"


def test_validate_init_data_invalid_hash() -> None:
    """validate_init_data raises for tampered hash."""
    bot_token = "123456:ABC-DEF"
    user = {"id": 42, "first_name": "Test"}
    init_data = _build_init_data(bot_token, user)
    # Tamper with the hash
    init_data = init_data.replace(init_data[-8:], "00000000")
    with pytest.raises(ValueError, match="Invalid initData"):
        validate_init_data(init_data, bot_token)


def test_validate_init_data_missing_hash() -> None:
    """validate_init_data raises when hash is missing."""
    with pytest.raises(ValueError, match="Missing hash"):
        validate_init_data("user=%7B%22id%22%3A1%7D&auth_date=123", "token")


# ---------------------------------------------------------------------------
# Telegram scraper — StringSession
# ---------------------------------------------------------------------------


def test_telegram_scraper_init_session_string() -> None:
    """TelegramScraper accepts a session_string parameter."""
    scraper = TelegramScraper(
        api_id=12345, api_hash="abc", session_string="test_session"
    )
    assert scraper.api_id == 12345
    assert scraper.api_hash == "abc"
    assert scraper.session_string == "test_session"


def test_telegram_scraper_defaults() -> None:
    """TelegramScraper uses settings defaults when no args provided."""
    scraper = TelegramScraper()
    assert scraper.api_id is not None
    assert scraper.session_string is not None


# ---------------------------------------------------------------------------
# ScrapingSource model
# ---------------------------------------------------------------------------


def test_scraping_source_model() -> None:
    """ScrapingSource model can be instantiated."""
    source = ScrapingSource(
        source_type="telegram",
        name="test_channel",
        enabled=True,
        interval_minutes=30,
    )
    assert source.source_type == "telegram"
    assert source.name == "test_channel"
    assert source.interval_minutes == 30
    assert source.enabled is True


# ---------------------------------------------------------------------------
# Admin API routes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_health_endpoint() -> None:
    """GET /api/admin/health returns scheduler status."""
    from backend.api.admin import require_admin
    from backend.core.auth import require_tma_auth

    async def override_admin():
        return {"id": 42, "first_name": "Admin"}

    app.dependency_overrides[require_admin] = override_admin
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert "scheduler_running" in data
        assert "jobs" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_sources_list() -> None:
    """GET /api/admin/sources returns a list."""
    from backend.api.admin import require_admin

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_session():
        yield mock_session

    async def override_admin():
        return {"id": 42, "first_name": "Admin"}

    from backend.core.database import get_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[require_admin] = override_admin
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/admin/sources")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_create_source_invalid_type() -> None:
    """POST /api/admin/sources rejects invalid source_type."""
    from backend.api.admin import require_admin

    mock_session = AsyncMock()

    async def override_session():
        yield mock_session

    async def override_admin():
        return {"id": 42, "first_name": "Admin"}

    from backend.core.database import get_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[require_admin] = override_admin
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/sources",
                json={"source_type": "invalid", "name": "test"},
            )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()

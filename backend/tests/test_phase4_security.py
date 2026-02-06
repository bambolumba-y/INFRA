"""Tests for Phase 4 security fixes: auth_date validation, fail-closed admin,
encrypted key storage, scraper timeouts, and FloodWait handling."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.core.auth import validate_init_data
from backend.main import app


# ---------------------------------------------------------------------------
# Helper — build valid initData
# ---------------------------------------------------------------------------


def _build_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    """Build a valid Telegram initData string for testing."""
    from urllib.parse import urlencode

    user_json = json.dumps(user)
    params = {
        "user": user_json,
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "test_query",
    }
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


# ---------------------------------------------------------------------------
# auth_date replay protection
# ---------------------------------------------------------------------------


def test_validate_init_data_rejects_stale_payload() -> None:
    """validate_init_data raises for auth_date older than max_age."""
    bot_token = "123456:ABC-DEF"
    user = {"id": 42, "first_name": "Test"}
    stale_ts = int(time.time()) - 700  # 700s ago (> 600s default)
    init_data = _build_init_data(bot_token, user, auth_date=stale_ts)
    with pytest.raises(ValueError, match="too old"):
        validate_init_data(init_data, bot_token)


def test_validate_init_data_accepts_fresh_payload() -> None:
    """validate_init_data succeeds for fresh auth_date."""
    bot_token = "123456:ABC-DEF"
    user = {"id": 42, "first_name": "Test"}
    init_data = _build_init_data(bot_token, user, auth_date=int(time.time()))
    result = validate_init_data(init_data, bot_token)
    assert result["id"] == 42


def test_validate_init_data_missing_auth_date() -> None:
    """validate_init_data raises when auth_date is missing."""
    bot_token = "123456:ABC-DEF"
    # Build initData without auth_date
    from urllib.parse import urlencode

    user_json = json.dumps({"id": 1})
    params = {"user": user_json, "query_id": "test"}
    data_pairs = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_pairs)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    params["hash"] = computed_hash
    init_data = urlencode(params)

    with pytest.raises(ValueError, match="Missing auth_date"):
        validate_init_data(init_data, bot_token)


def test_validate_init_data_custom_max_age() -> None:
    """validate_init_data respects a custom max_age parameter."""
    bot_token = "123456:ABC-DEF"
    user = {"id": 42, "first_name": "Test"}
    # 90 seconds old
    init_data = _build_init_data(bot_token, user, auth_date=int(time.time()) - 90)
    # 60s max_age should reject it
    with pytest.raises(ValueError, match="too old"):
        validate_init_data(init_data, bot_token, max_age=60)
    # 120s max_age should accept it
    result = validate_init_data(init_data, bot_token, max_age=120)
    assert result["id"] == 42


# ---------------------------------------------------------------------------
# /settings/keys requires auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_keys_requires_auth() -> None:
    """POST /api/settings/keys returns 401 without auth header in production mode."""
    with patch("backend.core.auth.settings") as mock_settings:
        mock_settings.app_env = "production"
        mock_settings.telegram_bot_token = "fake-token"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/settings/keys",
                json={"groq_api_key": "test-key"},
            )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# RSS scraper timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rss_scraper_timeout() -> None:
    """RSSScraper._parse_feed returns empty list on timeout."""
    import asyncio
    from backend.scrapers.rss_scraper import RSSScraper

    async def slow_parse(*_args, **_kwargs):
        await asyncio.sleep(10)

    scraper = RSSScraper(feed_urls=["http://example.com/feed"])
    with patch("backend.scrapers.rss_scraper.FEED_TIMEOUT_SECONDS", 0.1):
        with patch("backend.scrapers.rss_scraper.asyncio.get_running_loop") as mock_loop:
            loop = asyncio.get_running_loop()
            mock_loop.return_value = loop
            # Make run_in_executor return a slow coroutine
            async def slow_executor(_exec, _fn):
                await asyncio.sleep(10)
            loop_orig = loop.run_in_executor
            with patch.object(loop, "run_in_executor", side_effect=slow_executor):
                items = await scraper._parse_feed("http://example.com/feed")
    assert items == []


# ---------------------------------------------------------------------------
# Telegram scraper FloodWait handling
# ---------------------------------------------------------------------------


def test_telegram_scraper_has_retry_constants() -> None:
    """Verify retry constants exist in the telegram_scraper module."""
    from backend.scrapers.telegram_scraper import MAX_RETRIES, BASE_BACKOFF_SECONDS
    assert MAX_RETRIES >= 1
    assert BASE_BACKOFF_SECONDS > 0

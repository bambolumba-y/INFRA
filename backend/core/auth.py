"""Telegram Mini App initData validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs, unquote

from fastapi import Header, HTTPException

from backend.core.config import settings

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData and return parsed user data.

    Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    parsed = parse_qs(init_data, keep_blank_values=True)

    # Extract hash from the data
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        raise ValueError("Missing hash in initData")

    # Build the data-check-string: sort key=value pairs alphabetically
    data_pairs = []
    for key in sorted(parsed.keys()):
        val = parsed[key][0]
        data_pairs.append(f"{key}={val}")
    data_check_string = "\n".join(data_pairs)

    # Compute HMAC-SHA256
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid initData signature")

    # Parse user data
    user_raw = parsed.get("user", [None])[0]
    if user_raw:
        return json.loads(unquote(user_raw))
    return {}


async def require_tma_auth(
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    """FastAPI dependency that validates Telegram initData from header.

    In development mode with no bot token, auth is bypassed.
    """
    if settings.app_env == "development" and not settings.telegram_bot_token:
        logger.warning("TMA auth bypassed — development mode with no bot token")
        return {"id": 1, "first_name": "Dev"}

    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram initData")

    try:
        user = validate_init_data(x_telegram_init_data, settings.telegram_bot_token)
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

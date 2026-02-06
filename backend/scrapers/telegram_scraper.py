"""Telegram channel scraper using Telethon (async)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from telethon import TelegramClient
from telethon.tl.types import Message

from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramPost:
    """Represents a single scraped Telegram message."""

    channel: str
    text: str
    message_id: int
    date: str
    url: str | None = None
    media_urls: list[str] = field(default_factory=list)


class TelegramScraper:
    """Async service that monitors Telegram channels via Telethon."""

    def __init__(
        self,
        api_id: int | None = None,
        api_hash: str | None = None,
        session_name: str = "infra_scraper",
    ) -> None:
        self.api_id = api_id or settings.telegram_api_id
        self.api_hash = api_hash or settings.telegram_api_hash
        self.session_name = session_name
        self._client: TelegramClient | None = None

    async def _get_client(self) -> TelegramClient:
        """Return (and lazily start) the Telethon client."""
        if self._client is None:
            self._client = TelegramClient(
                self.session_name, self.api_id, self.api_hash
            )
            await self._client.start(bot_token=settings.telegram_bot_token)
        return self._client

    async def scrape_channel(
        self, channel: str, limit: int = 50
    ) -> list[TelegramPost]:
        """Fetch the latest *limit* messages from a public channel."""
        client = await self._get_client()
        posts: list[TelegramPost] = []

        async for message in client.iter_messages(channel, limit=limit):
            if not isinstance(message, Message) or not message.text:
                continue

            post = TelegramPost(
                channel=channel,
                text=message.text,
                message_id=message.id,
                date=message.date.isoformat() if message.date else "",
            )
            posts.append(post)

        logger.info("Scraped %d messages from %s", len(posts), channel)
        return posts

    async def scrape_all_channels(
        self, limit_per_channel: int = 50
    ) -> list[TelegramPost]:
        """Scrape every channel listed in ``settings.telegram_channels``."""
        channels = [
            ch.strip()
            for ch in settings.telegram_channels.split(",")
            if ch.strip()
        ]
        all_posts: list[TelegramPost] = []
        for channel in channels:
            try:
                posts = await self.scrape_channel(channel, limit=limit_per_channel)
                all_posts.extend(posts)
            except Exception:
                logger.exception("Failed to scrape channel %s", channel)
        return all_posts

    async def close(self) -> None:
        """Disconnect the Telethon client."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

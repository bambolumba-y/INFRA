"""Telegram channel scraper using Telethon User Session (StringSession)."""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field

from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession
from telethon.tl.types import Message

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Retry budget for FloodWait / transient errors
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 5


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
    """Async service that monitors Telegram channels via Telethon User Session."""

    def __init__(
        self,
        api_id: int | None = None,
        api_hash: str | None = None,
        session_string: str | None = None,
    ) -> None:
        self.api_id = api_id or settings.telegram_api_id
        self.api_hash = api_hash or settings.telegram_api_hash
        self.session_string = session_string or settings.telegram_session_string
        self._client: TelegramClient | None = None

    async def _get_client(self) -> TelegramClient:
        """Return (and lazily start) the Telethon client using StringSession."""
        if self._client is None:
            session = StringSession(self.session_string)
            self._client = TelegramClient(session, self.api_id, self.api_hash)
            await self._client.start()
        return self._client

    async def join_channel(self, channel: str) -> bool:
        """Join a public channel if not already a member."""
        client = await self._get_client()
        try:
            entity = await client.get_entity(channel)
            await client(functions.channels.JoinChannelRequest(entity))
            logger.info("Joined channel %s", channel)
            return True
        except FloodWaitError as e:
            logger.warning("FloodWait while joining %s — waiting %ds", channel, e.seconds)
            await asyncio.sleep(e.seconds)
            return False
        except Exception:
            logger.exception("Failed to join channel %s", channel)
            return False

    async def _iter_posts(
        self, channel: str, limit: int
    ) -> list[TelegramPost]:
        """Iterate messages from a channel and return TelegramPost list."""
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
        return posts

    async def scrape_channel(
        self, channel: str, limit: int = 50
    ) -> list[TelegramPost]:
        """Fetch the latest *limit* messages from a public channel.

        Handles FloodWaitError with exponential backoff.
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                posts = await self._iter_posts(channel, limit)
                logger.info("Scraped %d messages from %s", len(posts), channel)
                return posts
            except FloodWaitError as e:
                wait = e.seconds + 1
                logger.warning(
                    "FloodWait on %s — waiting %ds (attempt %d/%d)",
                    channel, wait, attempt + 1, MAX_RETRIES + 1,
                )
                await asyncio.sleep(wait)
            except Exception:
                if attempt == 0:
                    logger.warning("Cannot read %s, attempting to join...", channel)
                    joined = await self.join_channel(channel)
                    if not joined:
                        return []
                else:
                    backoff = BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Retry %d/%d for %s — backoff %.1fs",
                        attempt + 1, MAX_RETRIES + 1, channel, backoff,
                    )
                    await asyncio.sleep(backoff)

        logger.error("Exhausted retries for channel %s", channel)
        return []

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
        for i, channel in enumerate(channels):
            if i > 0:
                delay = random.uniform(2, 5)
                logger.debug("Rate-limit delay: %.1fs before scraping %s", delay, channel)
                await asyncio.sleep(delay)
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

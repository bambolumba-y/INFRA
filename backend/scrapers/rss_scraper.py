"""RSS / Atom feed scraper using feedparser."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from functools import partial

import feedparser  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    "https://hnrss.org/newest?points=50",
    "https://feeds.feedburner.com/TechCrunch/",
]

# Timeout (seconds) for fetching a single feed
FEED_TIMEOUT_SECONDS = 30


@dataclass
class RSSItem:
    """Represents a single RSS feed entry."""

    feed_url: str
    title: str
    link: str
    summary: str
    published: str


class RSSScraper:
    """Async-friendly RSS scraper backed by feedparser."""

    def __init__(self, feed_urls: list[str] | None = None) -> None:
        self.feed_urls = feed_urls or DEFAULT_FEEDS

    async def _parse_feed(self, url: str) -> list[RSSItem]:
        """Parse a single feed URL in a thread-pool (feedparser is sync) with timeout."""
        loop = asyncio.get_running_loop()
        try:
            feed = await asyncio.wait_for(
                loop.run_in_executor(None, partial(feedparser.parse, url)),
                timeout=FEED_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error("Timeout fetching feed %s after %ds", url, FEED_TIMEOUT_SECONDS)
            return []

        items: list[RSSItem] = []
        for entry in feed.entries:
            item = RSSItem(
                feed_url=url,
                title=getattr(entry, "title", ""),
                link=getattr(entry, "link", ""),
                summary=getattr(entry, "summary", ""),
                published=getattr(entry, "published", ""),
            )
            items.append(item)

        logger.info("Parsed %d entries from %s", len(items), url)
        return items

    async def scrape_all(self) -> list[RSSItem]:
        """Fetch and parse every configured feed concurrently."""
        tasks = [self._parse_feed(url) for url in self.feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[RSSItem] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.error("Feed scraping failed: %s", result)
            else:
                all_items.extend(result)
        return all_items

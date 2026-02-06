"""Reddit scraper using AsyncPRAW."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import asyncpraw  # type: ignore[import-untyped]

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Timeout (seconds) for scraping a single subreddit
SUBREDDIT_TIMEOUT_SECONDS = 60


@dataclass
class RedditPost:
    """Represents a single scraped Reddit submission."""

    subreddit: str
    title: str
    selftext: str
    author: str
    url: str
    score: int
    created_utc: float
    permalink: str


class RedditScraper:
    """Async service that fetches posts from configured subreddits via AsyncPRAW."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.client_id = client_id or settings.reddit_client_id
        self.client_secret = client_secret or settings.reddit_client_secret
        self.user_agent = user_agent or settings.reddit_user_agent
        self._reddit: asyncpraw.Reddit | None = None

    async def _get_reddit(self) -> asyncpraw.Reddit:
        """Return (and lazily create) the AsyncPRAW Reddit instance."""
        if self._reddit is None:
            self._reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
        return self._reddit

    async def _collect_posts(
        self,
        subreddit: asyncpraw.reddit.Subreddit,
        subreddit_name: str,
        limit: int,
        posts: list[RedditPost],
    ) -> None:
        """Collect posts from a subreddit into the provided list."""
        async for submission in subreddit.hot(limit=limit):
            post = RedditPost(
                subreddit=subreddit_name,
                title=submission.title,
                selftext=submission.selftext or "",
                author=str(submission.author) if submission.author else "[deleted]",
                url=submission.url,
                score=submission.score,
                created_utc=submission.created_utc,
                permalink=f"https://reddit.com{submission.permalink}",
            )
            posts.append(post)

    async def scrape_subreddit(
        self, subreddit_name: str, limit: int = 25
    ) -> list[RedditPost]:
        """Fetch the latest *limit* hot posts from a subreddit with timeout."""
        reddit = await self._get_reddit()
        subreddit = await reddit.subreddit(subreddit_name)

        posts: list[RedditPost] = []
        try:
            await asyncio.wait_for(
                self._collect_posts(subreddit, subreddit_name, limit, posts),
                timeout=SUBREDDIT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout scraping r/%s after %ds — returning %d posts collected so far",
                subreddit_name, SUBREDDIT_TIMEOUT_SECONDS, len(posts),
            )

        logger.info("Scraped %d posts from r/%s", len(posts), subreddit_name)
        return posts

    async def scrape_all_subreddits(
        self, limit_per_sub: int = 25
    ) -> list[RedditPost]:
        """Scrape every subreddit listed in ``settings.reddit_subreddits``."""
        subreddits = [
            s.strip()
            for s in settings.reddit_subreddits.split(",")
            if s.strip()
        ]
        all_posts: list[RedditPost] = []
        for sub in subreddits:
            try:
                posts = await self.scrape_subreddit(sub, limit=limit_per_sub)
                all_posts.extend(posts)
            except Exception:
                logger.exception("Failed to scrape r/%s", sub)
        return all_posts

    async def close(self) -> None:
        """Close the AsyncPRAW session."""
        if self._reddit is not None:
            await self._reddit.close()
            self._reddit = None

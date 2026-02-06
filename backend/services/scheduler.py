"""Task scheduler using APScheduler for periodic scraping and processing."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session
from backend.models.schemas import ScrapingSource

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _get_sources() -> list[ScrapingSource]:
    """Fetch all enabled scraping sources from the database."""
    async with async_session() as session:
        result = await session.execute(
            select(ScrapingSource).where(ScrapingSource.enabled == True)  # noqa: E712
        )
        return list(result.scalars().all())


async def run_scraping_cycle() -> None:
    """Execute a full scraping cycle for all enabled sources."""
    try:
        sources = await _get_sources()
        logger.info("Running scraping cycle for %d sources", len(sources))

        telegram_channels = [s.name for s in sources if s.source_type == "telegram"]
        reddit_subs = [s.name for s in sources if s.source_type == "reddit"]
        rss_feeds = [s.name for s in sources if s.source_type == "rss"]

        if telegram_channels:
            try:
                from backend.scrapers.telegram_scraper import TelegramScraper

                scraper = TelegramScraper()
                for ch in telegram_channels:
                    try:
                        posts = await scraper.scrape_channel(ch)
                        logger.info("Scraped %d posts from TG channel %s", len(posts), ch)
                    except Exception:
                        logger.exception("Failed to scrape TG channel %s", ch)
                await scraper.close()
            except Exception:
                logger.exception("Telegram scraper initialization failed")

        if reddit_subs:
            try:
                from backend.scrapers.reddit_scraper import RedditScraper

                scraper = RedditScraper()
                for sub in reddit_subs:
                    try:
                        posts = await scraper.scrape_subreddit(sub)
                        logger.info("Scraped %d posts from r/%s", len(posts), sub)
                    except Exception:
                        logger.exception("Failed to scrape r/%s", sub)
                await scraper.close()
            except Exception:
                logger.exception("Reddit scraper initialization failed")

        if rss_feeds:
            try:
                from backend.scrapers.rss_scraper import RSSScraper

                scraper = RSSScraper(feed_urls=rss_feeds)
                items = await scraper.scrape_all()
                logger.info("Scraped %d RSS items", len(items))
            except Exception:
                logger.exception("RSS scraper failed")

    except Exception:
        logger.exception("Scraping cycle failed")


def start_scheduler() -> None:
    """Start the APScheduler with a default 15-minute scraping interval."""
    scheduler.add_job(
        run_scraping_cycle,
        trigger=IntervalTrigger(minutes=15),
        id="scraping_cycle",
        name="Periodic scraping cycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with 15-minute scraping interval")


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

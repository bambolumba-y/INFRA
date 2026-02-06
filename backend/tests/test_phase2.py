"""Tests for scrapers, sentinel, career service, and new API routes."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.scrapers.rss_scraper import RSSScraper, RSSItem
from backend.scrapers.telegram_scraper import TelegramScraper, TelegramPost
from backend.scrapers.reddit_scraper import RedditScraper, RedditPost
from backend.services.sentinel import SentinelService
from backend.services.career_service import parse_resume_pdf, extract_resume_data
from backend.services.llm_service import summarize_news_item


# ---------------------------------------------------------------------------
# Telegram scraper
# ---------------------------------------------------------------------------


def test_telegram_scraper_init() -> None:
    """TelegramScraper initializes with settings values."""
    scraper = TelegramScraper(api_id=12345, api_hash="abc")
    assert scraper.api_id == 12345
    assert scraper.api_hash == "abc"


# ---------------------------------------------------------------------------
# Reddit scraper
# ---------------------------------------------------------------------------


def test_reddit_scraper_init() -> None:
    """RedditScraper stores credential overrides."""
    scraper = RedditScraper(
        client_id="cid", client_secret="csec", user_agent="test/1"
    )
    assert scraper.client_id == "cid"
    assert scraper.client_secret == "csec"


# ---------------------------------------------------------------------------
# RSS scraper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rss_scraper_parse_feed() -> None:
    """RSSScraper._parse_feed converts feedparser output to RSSItem list."""
    mock_feed = MagicMock()
    entry = MagicMock()
    entry.title = "Test Title"
    entry.link = "https://example.com"
    entry.summary = "A summary"
    entry.published = "Mon, 01 Jan 2024 00:00:00 GMT"
    mock_feed.entries = [entry]

    with patch("backend.scrapers.rss_scraper.feedparser.parse", return_value=mock_feed):
        scraper = RSSScraper(feed_urls=["https://example.com/feed"])
        items = await scraper._parse_feed("https://example.com/feed")

    assert len(items) == 1
    assert items[0].title == "Test Title"
    assert isinstance(items[0], RSSItem)


# ---------------------------------------------------------------------------
# Sentinel
# ---------------------------------------------------------------------------


def test_sentinel_add_and_dedup() -> None:
    """SentinelService add_document and is_duplicate work correctly."""
    with patch.object(SentinelService, "__init__", lambda self, **kw: None):
        sentinel = SentinelService.__new__(SentinelService)

    mock_collection = MagicMock()
    sentinel._collection = mock_collection
    sentinel._llm = MagicMock()

    # add_document should call collection.add
    doc_id = sentinel.add_document("Breaking news: Python 4 released")
    assert doc_id  # non-empty UUID string
    mock_collection.add.assert_called_once()

    # is_duplicate should detect close match
    mock_collection.query.return_value = {
        "distances": [[0.01]],
        "ids": [[doc_id]],
    }
    is_dup, matched = sentinel.is_duplicate("Breaking news: Python 4 released")
    assert is_dup is True
    assert matched == doc_id

    # is_duplicate should return False for distant content
    mock_collection.query.return_value = {
        "distances": [[1.8]],
        "ids": [["other-id"]],
    }
    is_dup, matched = sentinel.is_duplicate("Completely different text")
    assert is_dup is False
    assert matched is None


@pytest.mark.asyncio
async def test_sentinel_score_content() -> None:
    """score_content delegates to ProviderFactory and parses JSON."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps({"score": 8, "reason": "Looks legit"})

    with patch.object(SentinelService, "__init__", lambda self, **kw: None):
        sentinel = SentinelService.__new__(SentinelService)

    sentinel._llm = MagicMock()
    sentinel._llm.completion = AsyncMock(return_value=mock_llm_response)

    result = await sentinel.score_content("Some news text")
    assert result["score"] == 8
    assert "legit" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Career service
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_resume_pdf_returns_string() -> None:
    """parse_resume_pdf returns extracted text from a minimal PDF."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "John Doe — Senior Engineer")
    pdf_bytes = doc.tobytes()
    doc.close()

    text = await parse_resume_pdf(pdf_bytes)
    assert "John Doe" in text


@pytest.mark.asyncio
async def test_extract_resume_data_calls_llm() -> None:
    """extract_resume_data invokes the LLM and parses JSON."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "name": "Jane",
        "skills": ["Python"],
        "experience_years": 5,
        "stack": ["FastAPI"],
        "summary": "Experienced engineer",
    })

    with patch(
        "backend.services.career_service.ProviderFactory"
    ) as MockFactory:
        instance = MockFactory.return_value
        instance.completion = AsyncMock(return_value=mock_response)
        result = await extract_resume_data("Jane Doe resume text")

    assert result["name"] == "Jane"
    assert "Python" in result["skills"]


# ---------------------------------------------------------------------------
# LLM service — summarize_news_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summarize_news_item() -> None:
    """summarize_news_item returns the LLM content string."""
    mock_response = MagicMock()
    mock_response.content = "A quick summary."

    with patch(
        "backend.services.llm_service.ProviderFactory"
    ) as MockFactory:
        instance = MockFactory.return_value
        instance.completion = AsyncMock(return_value=mock_response)
        summary = await summarize_news_item("Title", "Body text", "reddit")

    assert summary == "A quick summary."


# ---------------------------------------------------------------------------
# API: /api/news (returns empty when no DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_news_endpoint_returns_list() -> None:
    """GET /api/news returns 200 with a list (mocked session)."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_session():
        yield mock_session

    from backend.core.database import get_session

    app.dependency_overrides[get_session] = override_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/news")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.clear()

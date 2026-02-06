# INFRA — Intelligence & News Filtering, Research & Analysis

> A Telegram Mini App that aggregates tech news from multiple sources, applies AI-powered credibility scoring, de-duplicates content via vector similarity, and delivers a curated intelligence feed — all inside Telegram.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [The Sentinel System](#the-sentinel-system)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Obtain Telegram Credentials](#2-obtain-telegram-credentials)
  - [3. Generate a Telethon Session](#3-generate-a-telethon-session)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
- [Running the Project](#running-the-project)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Development](#local-development)
- [Environment Variables Reference](#environment-variables-reference)
- [Admin Guide](#admin-guide)
- [Project Structure](#project-structure)
- [License](#license)

---

## Overview

**INFRA** is a full-stack intelligence terminal built as a Telegram Mini App (TMA). It continuously scrapes Telegram channels, Reddit, and RSS feeds for tech news and job postings, then runs every item through an AI-powered **Sentinel** pipeline that scores credibility and eliminates duplicates. The result is a clean, high-signal feed delivered straight to Telegram.

Key capabilities:

- **Multi-source scraping** — Telegram channels, Reddit subreddits, RSS/Atom feeds.
- **AI credibility scoring** — Every article is rated 1–10 by an LLM for factual reliability.
- **Vector de-duplication** — ChromaDB embeddings prevent near-duplicate content from cluttering the feed.
- **Multi-LLM support** — Groq, OpenAI, and Anthropic via LiteLLM with automatic provider switching.
- **Admin dashboard** — Configure scraping sources, intervals, and monitor system health.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│              Telegram Mini App               │
│        React 19 · Vite · Tailwind 4          │
└────────────────────┬─────────────────────────┘
                     │  HTTP + TMA initData auth
┌────────────────────▼─────────────────────────┐
│              FastAPI Backend                  │
│   ┌─────────┐  ┌──────────┐  ┌───────────┐  │
│   │ Scrapers │  │ Sentinel │  │ Admin API │  │
│   │ TG/Reddit│  │ AI+Dedup │  │ Sources   │  │
│   └─────────┘  └──────────┘  └───────────┘  │
│        │            │  │                     │
│   ┌────▼────┐  ┌────▼──▼────┐               │
│   │Scheduler│  │  LiteLLM   │               │
│   │APSched  │  │Groq/OAI/CL │               │
│   └─────────┘  └────────────┘               │
└───────┬──────────────┬───────────────────────┘
        │              │
   ┌────▼────┐    ┌────▼────┐
   │PostgreSQL│    │ChromaDB │
   │  Data    │    │ Vectors │
   └─────────┘    └─────────┘
```

---

## The Sentinel System

The **Sentinel** is INFRA's content quality pipeline located in `backend/services/sentinel.py`. Every scraped article passes through two stages:

### 1. Vector De-duplication

When new content arrives, Sentinel generates a vector embedding and queries ChromaDB for similar existing documents. If the L2 distance indicates similarity ≥ 0.9 (approximate cosine), the article is flagged as a duplicate and discarded. This prevents the feed from showing multiple versions of the same story.

### 2. AI Credibility Scoring

Non-duplicate content is sent to the configured LLM with a system prompt that asks: *"Is this news factual or marketing hype? Rate 1–10."* The LLM returns a JSON response with a numeric score and a short explanation. Articles scoring below the configured threshold can be filtered out.

**Combined pipeline flow:**

```
Incoming article
       │
       ▼
  Is duplicate? ──yes──▶ Discard (return existing vector ID)
       │ no
       ▼
  AI Score (1-10)
       │
       ▼
  Store embedding in ChromaDB
       │
       ▼
  Return { is_duplicate, vector_id, score, reason }
```

---

## Prerequisites

| Tool       | Version   | Purpose                     |
| ---------- | --------- | --------------------------- |
| Python     | 3.13+     | Backend runtime             |
| Node.js    | 20+       | Frontend build toolchain    |
| Docker     | 24+       | Container orchestration     |
| Compose    | v2+       | Multi-container management  |

---

## Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/bambolumba-y/INFRA.git
cd INFRA
```

### 2. Obtain Telegram Credentials

1. **Bot Token** — Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. **API ID & Hash** — Go to [my.telegram.org](https://my.telegram.org), sign in, and create an application to obtain your `API_ID` and `API_HASH`.

### 3. Generate a Telethon Session

The Telegram scraper requires a user session (StringSession) to read channel history. Use the included generator script:

```bash
pip install telethon
python scripts/generate_session.py
```

The script will:
1. Ask for your API ID and API Hash.
2. Send a login code to your Telegram account.
3. Print a `TELEGRAM_SESSION_STRING` value to add to your `.env`.

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values. See the [Environment Variables Reference](#environment-variables-reference) below for details on each variable.

---

## Running the Project

### Docker (Recommended)

The easiest way to run INFRA with all dependencies (PostgreSQL, ChromaDB):

```bash
docker compose up --build
```

This starts four services:

| Service      | Port  | Description                |
| ------------ | ----- | -------------------------- |
| `db`         | 5432  | PostgreSQL 17              |
| `vector-db`  | 8100  | ChromaDB                   |
| `backend`    | 8000  | FastAPI + Alembic migrations |
| `frontend`   | 5173  | Vite dev server            |

Data is persisted across restarts via named Docker volumes (`pgdata`, `chromadata`).

To stop:

```bash
docker compose down
```

To stop **and remove volumes** (⚠️ deletes all data):

```bash
docker compose down -v
```

### Local Development

#### Backend

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

> **Note:** For local development you need PostgreSQL and ChromaDB running separately, or use `docker compose up db vector-db` to start just the databases.

---

## Environment Variables Reference

| Variable                  | Required | Default                            | Description                                                           |
| ------------------------- | -------- | ---------------------------------- | --------------------------------------------------------------------- |
| `APP_ENV`                 | No       | `development`                      | Environment mode (`development` / `production`)                       |
| `APP_DEBUG`               | No       | `true`                             | Enable debug logging                                                  |
| `ADMIN_IDS`               | No       | `[]`                               | JSON list of Telegram user IDs allowed to access admin endpoints      |
| `DATABASE_URL`            | Yes      | `postgresql+asyncpg://…`           | PostgreSQL connection string                                          |
| `LLM_PROVIDER`            | No       | `groq`                             | Active LLM provider: `groq`, `openai`, or `anthropic`                 |
| `GROQ_API_KEY`            | *        |                                    | API key for Groq (required if `LLM_PROVIDER=groq`)                    |
| `OPENAI_API_KEY`          | *        |                                    | API key for OpenAI (required if `LLM_PROVIDER=openai`)                |
| `ANTHROPIC_API_KEY`       | *        |                                    | API key for Anthropic (required if `LLM_PROVIDER=anthropic`)          |
| `GROQ_MODEL`              | No       | `llama-3.1-70b-versatile`          | Groq model name                                                      |
| `OPENAI_MODEL`            | No       | `gpt-4o`                           | OpenAI model name                                                     |
| `ANTHROPIC_MODEL`         | No       | `claude-sonnet-4-20250514`              | Anthropic model name                                                  |
| `TELEGRAM_BOT_TOKEN`      | Yes      |                                    | Bot token from @BotFather (used for TMA auth)                         |
| `TELEGRAM_API_ID`         | Yes      | `0`                                | Telegram API ID from my.telegram.org                                  |
| `TELEGRAM_API_HASH`       | Yes      |                                    | Telegram API Hash from my.telegram.org                                |
| `TELEGRAM_CHANNELS`       | No       |                                    | Comma-separated list of Telegram channels to scrape                   |
| `TELEGRAM_SESSION_STRING` | Yes      |                                    | Telethon StringSession (generate via `scripts/generate_session.py`)   |
| `TELEGRAM_PHONE`          | No       |                                    | Phone number for Telethon login fallback                              |
| `REDDIT_CLIENT_ID`        | No       |                                    | Reddit app client ID                                                  |
| `REDDIT_CLIENT_SECRET`    | No       |                                    | Reddit app client secret                                              |
| `REDDIT_USER_AGENT`       | No       | `INFRA/0.1 (intelligence terminal)`| Reddit API user agent string                                          |
| `REDDIT_SUBREDDITS`       | No       | `programming,cscareerquestions,…`  | Comma-separated list of subreddits to scrape                          |
| `CHROMA_PERSIST_DIR`      | No       | `./chroma_data`                    | ChromaDB local persistence directory                                  |
| `CHROMA_HOST`             | No       | `localhost`                        | ChromaDB server host                                                  |
| `CHROMA_PORT`             | No       | `8100`                             | ChromaDB server port                                                  |

---

## Admin Guide

Admin endpoints are protected by two layers:

1. **TMA Auth** — Every request must include a valid Telegram `initData` header (HMAC-SHA256 validated).
2. **Admin ID Check** — The authenticated user's Telegram ID must be in the `ADMIN_IDS` list.

### Accessing the Admin Dashboard

1. Set your Telegram user ID in `ADMIN_IDS` in `.env` (e.g., `ADMIN_IDS=[123456789]`).
2. Open the Mini App in Telegram.
3. Navigate to the admin/settings section.

### Admin API Endpoints

| Method   | Endpoint                       | Description                    |
| -------- | ------------------------------ | ------------------------------ |
| `GET`    | `/api/admin/health`            | System health & scheduler jobs |
| `GET`    | `/api/admin/sources`           | List scraping sources          |
| `POST`   | `/api/admin/sources`           | Add a new source               |
| `PATCH`  | `/api/admin/sources/{id}`      | Update a source                |
| `DELETE` | `/api/admin/sources/{id}`      | Remove a source                |

---

## Project Structure

```
INFRA/
├── backend/
│   ├── api/            # FastAPI route handlers
│   ├── core/           # Config, auth, database session
│   ├── llm/            # Multi-LLM adapter (LiteLLM)
│   ├── models/         # SQLAlchemy schemas
│   ├── scrapers/       # Telegram, Reddit scrapers
│   ├── services/       # Sentinel, scheduler
│   ├── tests/          # Pytest test suite
│   ├── alembic/        # Database migrations
│   └── main.py         # FastAPI entry point
├── frontend/
│   └── src/
│       ├── components/ # React UI components
│       ├── hooks/      # Custom React hooks
│       ├── store/      # Zustand state management
│       └── api/        # TanStack Query clients
├── scripts/
│   └── generate_session.py  # Telethon session generator
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## License

This project is private and proprietary.

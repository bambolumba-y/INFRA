# DEVELOPMENT PHASE 3: AUTOMATION, SECURITY & ADMIN INTERFACE

## 1. TELEGRAM SCRAPER UPGRADE (USER SESSION)
- **Refactor `backend/scrapers/telegram_scraper.py`**:
    - Replace `bot_token` authorization with **User Session** (StringSession for stateless/Docker compatibility).
    - Implement a login flow that can handle `API_ID`, `API_HASH`, and `PHONE_NUMBER`.
    - Allow the scraper to join public channels automatically if it's not a member.
    - Reference: https://docs.telethon.dev/en/stable/concepts/sessions.html

## 2. TASK SCHEDULING (THE HEARTBEAT)
- **Implement `APScheduler` or `Arq`** for background tasks (simpler for this stage than full Celery).
- Create a `backend/services/scheduler.py` to manage:
    - Interval-based scraping (e.g., every 15 mins).
    - Interval-based AI processing (Sentinel scoring).
- **Flexibility:** Task intervals must be configurable via the database (not hardcoded in .env).

## 3. ADMIN PANEL & CONFIGURATION
- **Admin UI:** Create a protected route `/admin` in the React frontend.
- **Features:**
    - **Source Management:** Add/Remove Telegram channels, Subreddits, and RSS feeds.
    - **Interval Controls:** Set global or per-source scraping frequency.
    - **System Health:** View logs and current scraper status (Active/Idle/Error).
    - **AI Settings:** Configure the "Sentinel" threshold (0.9 by default).
- **Backend:** Create `api/admin.py` routes with strict Auth.

## 4. DATABASE & MIGRATIONS (PERSISTENCE)
- **Migrations:** Set up `Alembic`. Create initial migration scripts to ensure the database schema matches `models/schemas.py`.
- **ChromaDB Upgrade:** Switch from `chromadb.Client` (Local) to `chromadb.HttpClient` to allow multiple backend workers to access the vector DB without file locking.

## 5. SECURITY & DEPLOYMENT
- **TMA Validation:** Implement `backend/core/auth.py` to validate `initData` on every request.
- **Docker-Compose:** 
    - Add a `db` service (PostgreSQL).
    - Add a `vector-db` service (ChromaDB standalone).
    - Configure `Nginx` as a reverse proxy with a placeholder for SSL.

## 6. KNOWN ISSUES TO SOLVE
- **ChromaDB Locking:** Fixed by switching to `HttpClient`.
- **TG Bot Limits:** Fixed by switching to `UserSession`.
- **Frontend Persistence:** Add `persist` middleware to the Zustand `appStore`.

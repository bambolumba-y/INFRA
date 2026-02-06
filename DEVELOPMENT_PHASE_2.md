# DEVELOPMENT PHASE 2: CORE FUNCTIONALITY IMPLEMENTATION

## 1. SCOUTING ENGINE (PRIMARY TASK)
Implement asynchronous scrapers in `backend/scrapers/`:
- **Telegram:** Use `Telethon`. Create a service that monitors a list of channels from the database.
- **Reddit:** Use `AsyncPRAW`. Implement a scraper for specific subreddits (IT/Career).
- **RSS:** Basic `feedparser` integration for technical blogs.
- **Sentinel System:**
    - Create `services/sentinel.py`.
    - Implement a de-duplication logic using `ChromaDB` embeddings.
    - Implement an AI-rating system: use `ProviderFactory` to score news validity (1-10).

## 2. DATABASE & MODELS
- Finalize `backend/models/schemas.py`: Add `User`, `Article`, `Job`, and `UserResume` tables.
- Implement `backend/core/database.py`: Set up SQLAlchemy async engine and session management.
- Create initial migrations or an auto-init script for PostgreSQL.

## 3. FRONTEND (TWA INTERFACE)
- **UI Architecture:** Implement the "Intelligence Dashboard" using `shadcn/ui`.
- **Key Components:**
    - `NewsCard`: Summarized info, Impact Score, Source.
    - `FilterBar`: Toggle between News, Jobs, and Market Intel.
    - `ProfileSection`: Resume upload (PDF).
- **State Management:** Set up `Zustand` for global state and `TanStack Query` for API calls.
- **Telegram Integration:** Connect `@telegram-apps/sdk` to handle `initData` and Haptic Feedback.

## 4. CV-MATCHING ENGINE
- Create `services/career_service.py`.
- Implement PDF parsing using `PyMuPDF`.
- Create a matching algorithm: AI compares Resume (Vector) vs Job Openings (Vector).

## 5. API ROUTES
Implement the following controllers:
- `GET /api/news`: Filtered and summarized news feed.
- `POST /api/resume/upload`: Upload and process CV.
- `GET /api/jobs/matches`: List of high-percentage job matches.
- `POST /api/settings/keys`: User-provided API keys storage.

## 6. ADMIN PANEL
- Simple dashboard at `/admin` (can use `fastapi-admin` or a custom React route) to manage news sources and view system logs.

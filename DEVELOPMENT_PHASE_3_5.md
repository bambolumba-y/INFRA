# PHASE 3.5: REFINEMENT & DOCUMENTATION

## 1. SECURITY FIXES
- **Admin Access Control:**
    - In `backend/api/admin.py`, implement a check against a `settings.admin_ids` list (integers).
    - Ensure that even if someone accesses the `/admin` route on the frontend, the backend rejects unauthorized `user_id`s extracted from `initData`.
- **TMA Auth Hardening:** 
    - Verify that the `auth.py` validation correctly handles all fields of `initData` as per official Telegram documentation.

## 2. RELIABILITY & PERFORMANCE
- **Scraper Rate Limiting:**
    - In `telegram_scraper.py`, add a randomized delay (e.g., `asyncio.sleep(random.uniform(2, 5))`) between scraping different channels to avoid Telethon flood waits.
- **Docker Data Persistence:**
    - Ensure `docker-compose.yml` has named volumes for both `postgres_data` and `chroma_data` to prevent data loss during container restarts.
- **Zustand Persistence:**
    - Ensure `frontend/src/store/appStore.ts` uses the `persist` middleware from Zustand so the user's state isn't lost on page refresh within Telegram.

## 3. UTILITIES
- **Session Generator:** 
    - Create a standalone script `scripts/generate_session.py`. It should guide the user through the Telethon login process and print the `STRING_SESSION` to be used in `.env`.

## 4. DOCUMENTATION (README.md)
Create a comprehensive `README.md` in the root directory covering:
- **Project Concept:** What is INFRA?
- **Setup Guide:**
    - Prerequisites (Python 3.13, Docker, Node.js).
    - How to get Telegram API ID/Hash.
    - How to use the `generate_session.py` script.
    - Environment variables explanation (`.env.example`).
- **Deployment:**
    - Local run (`uvicorn`, `npm run dev`).
    - Docker run (`docker-compose up`).
- **Admin Guide:** How to access the dashboard and configure scrapers.

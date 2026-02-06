# INFRA Repository Audit (2026-02-06)

## Executive Summary

**Vulnerability Score (1-10): 3/10**  
Current state is prototype-grade. Critical security gaps (admin access control defaults, unauthenticated key storage, missing replay protection for Telegram initData) and production hardening gaps (Dockerfiles, non-root execution, health checks, observability) need to be addressed before release.

## Architecture & API Contract Review

- **Frontend → Backend contract mismatch:** The backend requires `X-Telegram-Init-Data` for protected endpoints (`require_tma_auth`), but the frontend API client does not attach initData to requests. Admin calls will fail in production or be bypassed in development with `APP_ENV=development`.  
  **Recommendation:** Add an Axios interceptor that attaches `X-Telegram-Init-Data` from the Telegram SDK and ensure SDK initialization happens before API calls.
- **Hard-coded `user_id=1` in backend endpoints (`/resume/upload`, `/jobs/matches`, `/settings/keys`):** Leads to mixed-user data and implicit privilege access.  
  **Recommendation:** Derive user id from Telegram auth payload, not query params/defaults.
- **CORS is fully open with credentials enabled:** `allow_origins=["*"]` with `allow_credentials=True` is unsafe.  
  **Recommendation:** restrict to known frontend origins and disable credentials if not required.

## Docker & Deployment Readiness

- **Missing Dockerfiles** in repo while `docker-compose.yml` references build contexts (`backend`, `frontend`).  
  **Recommendation:** add multi-stage Dockerfiles for both services.
- **Backend runs in dev mode:** `uvicorn --reload` and `settings.app_debug=True` in compose → unsafe for production.  
  **Recommendation:** use `--workers`, disable reload, and set `APP_ENV=production`.
- **No non-root user, resource limits, or restart policies** in compose.  
  **Recommendation:** run as non-root, pin images, add resource limits and restart policy.
- **`vector-db` uses `latest` tag:** risk of breaking upgrades.  
  **Recommendation:** pin a specific ChromaDB version.

## Deep Security Audit (Highest Priority)

### Telegram initData (backend/core/auth.py)

- **No replay protection / age check:** `auth_date` is not validated. initData can be replayed indefinitely.  
  **Fix:** reject payloads with `auth_date` older than X minutes (typically 5–10 mins).
- **No required field enforcement:** `auth_date` / `query_id` / `user` presence not validated.  
  **Fix:** validate required keys and enforce consistent parsing rules per Telegram spec.
- **Bot token empty in production:** If `telegram_bot_token` missing, auth is impossible; if `APP_ENV=development`, auth is bypassed.  
  **Fix:** fail startup when `APP_ENV=production` and token is missing.

### Admin access control (backend/api/admin.py & config)

- **Default `admin_ids=[]` grants admin to any authenticated user.**  
  **Fix:** fail closed by requiring explicit admin IDs; block access when list is empty.
- **No audit logging for admin actions.**  
  **Fix:** add structured audit logs for create/update/delete operations.

### API keys storage (backend/api/routes.py)

- **`/settings/keys` unauthenticated and stores raw keys in DB.**  
  **Fix:** require Telegram auth, store keys encrypted (KMS or envelope encryption), and scope to authenticated user.

## External APIs & Scraping Logic

### Telethon (backend/scrapers/telegram_scraper.py)

- **No FloodWait handling or backoff**; exceptions are swallowed.  
  **Fix:** handle `FloodWaitError`, exponential backoff, and retry budget.
- **StringSession stored in env, no rotation** → high-value secret.  
  **Fix:** store in a secrets manager; rotate and lock down logs.
- **No reconnection strategy** beyond first error; `_client` remains active.  
  **Fix:** reinitialize client on disconnect and enforce clean shutdown.

### AsyncPRAW (backend/scrapers/reddit_scraper.py)

- **No rate-limit/backoff handling** and no timeout configuration.  
  **Fix:** add retries with jitter; cap concurrency; configure timeouts.
- **No pagination/continuation strategy** for large subreddits.

### RSS (backend/scrapers/rss_scraper.py)

- **No fetch timeout or per-feed error isolation beyond logging.**  
  **Fix:** add per-feed timeout + circuit breaker; limit max feed size.

## Data Integrity & AI Logic

### De-duplication (backend/services/sentinel.py)

- **Similarity uses L2-derived approximation with static threshold (0.9).**  
  This can be overly strict or lenient depending on embedding scale.  
  **Fix:** normalize embeddings, store similarity metrics, and calibrate threshold per source.
- **No metadata-based filtering or TTL cleanup**, so vectors can grow unbounded.  
  **Fix:** partition collections by source or add TTL/retention policy.

### LLM Orchestration (backend/llm/provider_factory.py)

- **No provider fallback or retry strategy.**  
  **Fix:** implement automatic failover (e.g., Groq → OpenAI → Anthropic), timeouts, and error categorization.

## Frontend & UX

- **Telegram SDK usage does not propagate auth to API calls.**  
  **Fix:** store initData and add it to request headers.
- **Persisted user data stored in localStorage** without expiry or encryption.  
  **Fix:** limit persisted data to non-sensitive fields and add expiry.
- **Potential memory leak:** `initDataUser()` signal is read once; no unsubscribe or handling for updates.  
  **Fix:** subscribe/unsubscribe to SDK signals if persistent updates are used.

## Critical Fixes (Immediate)

1. Enforce admin allowlist (fail closed if `ADMIN_IDS` empty).
2. Require Telegram auth + replay protection (validate `auth_date`).
3. Secure `/settings/keys` endpoint and encrypt stored secrets.
4. Add API auth headers from frontend (Telegram initData).
5. Lock down CORS to known origins.

## Efficiency Improvements

- Add connection pooling and request timeouts for external APIs.
- Batch embed + dedup in ChromaDB to reduce query overhead.
- Cache RSS results; skip unchanged feeds using `etag`/`last-modified`.
- Reduce DB round-trips in admin endpoints (bulk operations).

## Scalability Roadmap (100× Growth)

1. **Security & Auth:** Centralized identity (JWT/TMA), secrets manager, audit logs.
2. **Infrastructure:** Add Dockerfiles, non-root images, health checks, and autoscaling.
3. **Data Layer:** Introduce vector retention, partitioned collections, and read replicas.
4. **Scrapers:** Queue-based ingestion (Celery/Redis/RQ), rate-limiters, and per-source workers.
5. **LLM Layer:** Provider fallback, caching, async queues, and budget-aware routing.
6. **Observability:** OpenTelemetry traces, structured logs, SLOs, and alerting.

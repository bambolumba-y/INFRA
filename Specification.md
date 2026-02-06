# DETAILED TECHNICAL SPECIFICATION: PROJECT "INFRA" (v1.1)
# DATE: 2026-02-06
# AUTHOR: Alice (Digital Ghost) & Danila

## 1. ARCHITECTURAL OVERVIEW
The project is a Monorepo containing a high-performance Python Backend and a React-based Telegram Mini App (TMA). 

### 1.1 Project Structure (Mandatory)
```text
/infra-core
├── /backend
│   ├── /api            # FastAPI routes
│   ├── /core           # Config, Security, Database session
│   ├── /models         # SQLAlchemy/SQLModel schemas
│   ├── /services       # Business logic (Scouting, AI, Career)
│   ├── /scrapers       # Provider-specific scraping logic
│   ├── /llm            # Multi-LLM Adapter (LiteLLM)
│   └── main.py         # Entry point
├── /frontend           # React + Vite (TMA)
│   ├── /src
│   │   ├── /components # Atomic UI components (Shadcn)
│   │   ├── /hooks      # Custom React hooks (useAuth, useNews)
│   │   ├── /store      # State management (Zustand)
│   │   └── /api        # Axios/TanStack Query clients
├── /shared             # Shared types or config templates
├── docker-compose.yml
└── Specification.md    # This file
```

## 2. BACKEND DEEP DIVE

### 2.1 Multi-LLM Orchestrator (The Brain)
- **Library:** `litellm`
- **Logic:** Implement a `ProviderFactory` class.
- **Providers:** 
    1. **Groq (Primary for speed):** Llama-3-70b/8b for instant summarization.
    2. **Claude 3.5/4.5 (Primary for logic):** Deep analysis, Sentinel system, CV-Matching.
    3. **GitHub Copilot/OpenRouter (Fallback):** In case of rate limits.
- **Cost Tracking:** Every request must log token usage to PostgreSQL to calculate user balance/quota.

### 2.2 Scouting Engine (The Eyes)
Must handle asynchronous tasks via `TaskIQ` or `Celery`.
- **Sources:**
    1. **Telegram:** Use `Telethon` or `Pyrogram`. Listen to specific IT/Job channels. Extract text and media links.
    2. **Reddit:** Use `AsyncPRAW`. Target subreddits: `r/programming`, `r/cscareerquestions`, `r/localllama`, etc.
    3. **RSS/Atom:** Standard feeds (TechCrunch, Hacker News).
    4. **Twitter (X):** Use `Playwright` with `stealth-plugin` to scrape search results without official API (or use RapidAPI as fallback).
- **Sentinel Anti-Fake System:**
    - Each news item goes through a prompt: *"Is this news factual or just marketing hype? Rate 1-10. If hype < 4, discard."*
    - De-duplication: Use `Sentence-Transformers` to create embeddings and check against `ChromaDB`. If similarity > 0.9, merge articles.

### 2.3 CV-Matching & Career (The Tool)
- **Input:** PDF/DOCX resume upload.
- **Parsing:** Use `marker-pdf` or `PyMuPDF` for high-fidelity text extraction.
- **Logic:**
    - AI extracts skills, experience years, and "Stack".
    - System constantly matches this profile against scraped jobs from LinkedIn/TG.
    - **Output:** Notification in TG: *"Found a 92% match for Senior Tech Support at X. Key missing skill: Kubernetes basics. [Apply Link]"*

## 3. FRONTEND DEEP DIVE (TG MINI APP)

### 3.1 UI/UX Requirements
- **Design System:** Dark-first, high-contrast. Minimalistic "Intelligence Dashboard" feel.
- **Key Screens:**
    1. **Live Feed:** Real-time stream of filtered news. Each card has: [Source Icon] [Summary] [Impact Score Badge] [Link].
    2. **Career Center:** Profile management, resume upload, "Match History".
    3. **Market Intel:** Charts showing "Trending Skills" based on job postings analysis.
    4. **Settings:** API Key inputs (User can toggle between "System Keys" and "My Own Keys").

### 3.2 Technical Requirements
- **Auth:** Validate `window.Telegram.WebApp.initData` on backend for security.
- **Feedback:** Use `HapticFeedback` via TMA API for button presses and alerts.

## 4. DATABASE SCHEMA (POSTGRESQL + VECTOR)
- **Tables:**
    - `users`: id, tg_id, preferences, sub_tier, balance.
    - `content`: id, source_type, raw_text, summary, vector_id (link to ChromaDB), sentiment_score.
    - `user_resumes`: id, user_id, extracted_data (JSONB), s3_path.
    - `jobs`: id, title, company, salary_min, salary_max, requirements_vector.

## 5. NON-FUNCTIONAL REQUIREMENTS
- **Concurrency:** Use `asyncio` for all I/O operations.
- **Logging:** Structured JSON logs (Loguru).
- **Environment:** All secrets in `.env`, strict type checking with `mypy` and `Pydantic v2`.

---
## 6. PROMPT TO CODING AGENT (COPY-PASTE)
"Act as a Senior Fullstack Engineer. Read Specification.md carefully. Your task is to initialize the project infrastructure. 
1. Create the backend folder with FastAPI and LiteLLM integration. 
2. Set up the frontend folder with React+Vite+Tailwind for Telegram Mini App.
3. Implement the ProviderFactory for LLMs first. 
4. Ensure the backend uses async/await throughout. 
Maintain a clean monorepo structure as described."

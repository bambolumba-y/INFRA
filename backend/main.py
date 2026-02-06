"""FastAPI application entry-point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.admin import admin_router
from backend.api.routes import router
from backend.core.config import settings
from backend.core.database import init_db
from backend.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Run database init and scheduler on startup."""
    try:
        await init_db()
    except Exception:
        pass  # DB may not be available in dev/test without Postgres
    try:
        start_scheduler()
    except Exception:
        pass  # Scheduler may fail in test environments
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    app = FastAPI(
        title="INFRA — Intelligence Terminal",
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")
    app.include_router(admin_router, prefix="/api")

    return app


app = create_app()

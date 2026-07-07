"""Application entry point.

Creates the FastAPI app, attaches metadata (which drives the OpenAPI/Swagger
docs), registers the domain exception handlers, and mounts all routers.

Run locally with:
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db
from app.core.logging_config import configure_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter
from app.exceptions import (
    DuplicateEmailError,
    EmployeeNotFoundError,
    duplicate_email_handler,
    employee_not_found_handler,
)
from app.routers import employees_router
from app.routers.auth import router as auth_router
from app.routers.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup (creates tables + seeds departments)
    init_db()
    yield


configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    contact={"name": "Madhav"},
    lifespan=lifespan,
)

# --- Week 6: rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Week 6: request logging middleware ---
app.add_middleware(RequestLoggingMiddleware)

# Translate domain exceptions into clean HTTP responses.
app.add_exception_handler(EmployeeNotFoundError, employee_not_found_handler)
app.add_exception_handler(DuplicateEmailError, duplicate_email_handler)

# Mount routes.
app.include_router(employees_router)
app.include_router(auth_router)
app.include_router(analytics_router)


@app.get("/", tags=["Meta"], summary="API root")
def root() -> dict:
    """Basic API metadata and useful links."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health", tags=["Meta"], summary="Health check")
def health() -> dict:
    """Liveness probe used by monitoring/uptime checks."""
    return {"status": "ok"}
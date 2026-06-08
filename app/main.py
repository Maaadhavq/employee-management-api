"""Application entry point.

Creates the FastAPI app, attaches metadata (which drives the OpenAPI/Swagger
docs), registers the domain exception handlers, and mounts the employee router.

Run locally with:
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.
"""

from fastapi import FastAPI

from app.config import settings
from app.exceptions import (
    DuplicateEmailError,
    EmployeeNotFoundError,
    duplicate_email_handler,
    employee_not_found_handler,
)
from app.routers import employees_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    contact={"name": "Madhav"},
)

# Translate domain exceptions into clean HTTP responses.
app.add_exception_handler(EmployeeNotFoundError, employee_not_found_handler)
app.add_exception_handler(DuplicateEmailError, duplicate_email_handler)

# Mount routes.
app.include_router(employees_router)


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

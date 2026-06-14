"""Application configuration.

Centralises settings so they are not scattered as magic values across the
codebase.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Project root: .../employee-management-api
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Runtime settings, overridable via environment variables."""

    APP_NAME: str = "Employee Management API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A REST API to manage employee records with full CRUD support, "
        "validation and OpenAPI documentation."
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:madhav@localhost:5432/employee_db"
    )
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:madhav@localhost:5432/employee_test_db"
    )
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False").lower() in ("true", "1", "yes")

    # Default pagination size for list endpoints.
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()

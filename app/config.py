"""Application configuration.

Centralises settings so they are not scattered as magic values across the
codebase. In later weeks (e.g. when a real database is introduced) this is the
natural place for connection strings, secrets loaded from the environment, etc.
"""

import os
from pathlib import Path

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

    # Path to the JSON file used as a simple persistence layer for Week 2.
    # The repository layer hides this detail, so it can be swapped for a real
    # database (Week 3) without touching the rest of the application.
    DATA_FILE: Path = Path(
        os.getenv("EMPLOYEE_DATA_FILE", BASE_DIR / "data" / "employees.json")
    )

    # Default pagination size for list endpoints.
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()

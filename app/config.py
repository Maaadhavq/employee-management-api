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

    # Deployment environment: "development" locally, "production" on AWS.
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # AWS / S3 settings (used by the employee-export feature in Week 4).
    # On EC2 these credentials are supplied automatically by the attached IAM
    # role, so AWS keys are deliberately NOT read from the environment here.
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    # How long (seconds) a generated export download link stays valid.
    S3_PRESIGNED_URL_TTL: int = int(os.getenv("S3_PRESIGNED_URL_TTL", "3600"))
    # JWT authentication settings (Week 6)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))



    # Default pagination size for list endpoints.
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()

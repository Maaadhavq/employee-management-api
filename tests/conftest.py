"""Shared test fixtures: one in-memory SQLite engine, one dependency
override, one TestClient — used by both test_auth.py and
test_employees.py so they don't fight over app.dependency_overrides.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db

# Explicitly import every ORM model module so their tables are
# registered on Base.metadata BEFORE create_all() runs below.
# Relying on this happening indirectly via app.main's import chain
# is fragile — this makes it explicit and guaranteed.
import app.models.employee_orm  # noqa: F401
import app.models.user  # noqa: F401

from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
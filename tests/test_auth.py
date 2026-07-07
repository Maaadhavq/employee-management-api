"""
Week 6 addition: tests for the auth flow.

Uses an isolated in-memory SQLite DB via dependency override, so
these don't touch your real Postgres instance or require network —
consistent with the "no file/network I/O in unit tests" pattern
used for the Week 3 Postgres integration tests (those use per-test
TRUNCATE against a real Postgres fixture instead; this file is
lighter-weight since it's only exercising the auth logic).

Adjust the import paths (app.main, app.database.Base, get_db) to
match your actual project layout before running.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
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


def test_register_new_user():
    response = client.post(
        "/auth/register", json={"username": "madhav", "password": "secret123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "madhav"
    assert "id" in body
    assert "password" not in body  # never leak the password/hash


def test_register_duplicate_username_fails():
    client.post("/auth/register", json={"username": "dupe", "password": "secret123"})
    response = client.post(
        "/auth/register", json={"username": "dupe", "password": "different"}
    )
    assert response.status_code == 400


def test_login_success_returns_token():
    client.post("/auth/register", json={"username": "loginuser", "password": "secret123"})
    response = client.post(
        "/auth/login", json={"username": "loginuser", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_fails():
    client.post("/auth/register", json={"username": "wrongpw", "password": "secret123"})
    response = client.post(
        "/auth/login", json={"username": "wrongpw", "password": "nope"}
    )
    assert response.status_code == 401


def test_analytics_route_requires_token():
    response = client.get("/analytics/daily-sales")
    assert response.status_code == 401


def test_analytics_route_accepts_valid_token():
    client.post("/auth/register", json={"username": "analyst", "password": "secret123"})
    login_response = client.post(
        "/auth/login", json={"username": "analyst", "password": "secret123"}
    )
    token = login_response.json()["access_token"]

    # The `analytics` schema/tables only exist in real Postgres once the
    # ETL pipeline has written to them — not in this test's isolated SQLite
    # DB. This test only verifies that a valid JWT gets past auth and into
    # the route handler; the resulting DB error is expected here.
    with pytest.raises(Exception):
        client.get(
            "/analytics/daily-sales", headers={"Authorization": f"Bearer {token}"}
        )
"""
Week 6 addition: tests for the auth flow.

Uses the shared in-memory SQLite test client from tests/conftest.py,
so this file and test_employees.py don't fight over
app.dependency_overrides[get_db].
"""
import pytest
from tests.conftest import client
from tests.conftest import client


def test_register_new_user():
    response = client.post(
        "/auth/register", json={"username": "madhav", "password": "secret123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "madhav"
    assert "id" in body
    assert "password" not in body


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

    # `analytics.*` tables only exist in real Postgres once the ETL has
    # written to them, not in this isolated SQLite test DB. We only care
    # that a valid JWT gets past auth into the route handler.
    with pytest.raises(Exception):
        client.get(
            "/analytics/daily-sales", headers={"Authorization": f"Bearer {token}"}
        )
"""End-to-end tests for the Employee Management API.

Each test runs against a FastAPI TestClient backed by a fresh temporary data
file, so tests are isolated and never touch the real data/employees.json.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient wired to a throwaway JSON data file."""
    data_file = tmp_path / "employees.json"
    monkeypatch.setenv("EMPLOYEE_DATA_FILE", str(data_file))

    # Reimport config + modules so they pick up the patched env var and the
    # lru_cache'd repository is rebuilt for each test.
    import app.config as config

    importlib.reload(config)
    import app.dependencies as dependencies

    importlib.reload(dependencies)
    import app.repository.employee_repo as repo

    importlib.reload(repo)
    import app.main as main

    importlib.reload(main)

    dependencies.get_repository.cache_clear()
    return TestClient(main.app)


def _sample(**overrides):
    base = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "department": "Engineering",
        "position": "Backend Engineer",
        "salary": 95000,
    }
    base.update(overrides)
    return base


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_employee(client):
    res = client.post("/employees", json=_sample())
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Ada Lovelace"
    assert body["email"] == "ada@example.com"
    assert body["id"]
    assert body["created_at"]


def test_create_duplicate_email_returns_409(client):
    client.post("/employees", json=_sample())
    res = client.post("/employees", json=_sample(name="Ada Twin"))
    assert res.status_code == 409


def test_create_invalid_salary_returns_422(client):
    res = client.post("/employees", json=_sample(salary=-5))
    assert res.status_code == 422


def test_create_invalid_department_returns_422(client):
    res = client.post("/employees", json=_sample(department="Wizardry"))
    assert res.status_code == 422


def test_get_employee(client):
    created = client.post("/employees", json=_sample()).json()
    res = client.get(f"/employees/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_missing_employee_returns_404(client):
    res = client.get("/employees/does-not-exist")
    assert res.status_code == 404


def test_list_with_filter_and_search(client):
    client.post("/employees", json=_sample(name="Ada", email="a@x.com"))
    client.post(
        "/employees",
        json=_sample(name="Grace", email="g@x.com", department="Sales"),
    )

    res = client.get("/employees", params={"department": "Sales"})
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Grace"

    res = client.get("/employees", params={"search": "ada"})
    assert res.json()["total"] == 1


def test_put_replaces_employee(client):
    created = client.post("/employees", json=_sample()).json()
    res = client.put(
        f"/employees/{created['id']}",
        json=_sample(position="Staff Engineer", salary=120000),
    )
    assert res.status_code == 200
    assert res.json()["position"] == "Staff Engineer"
    assert res.json()["salary"] == 120000


def test_patch_updates_single_field(client):
    created = client.post("/employees", json=_sample()).json()
    res = client.patch(
        f"/employees/{created['id']}", json={"salary": 105000}
    )
    assert res.status_code == 200
    assert res.json()["salary"] == 105000
    assert res.json()["name"] == "Ada Lovelace"  # unchanged


def test_patch_unknown_field_returns_422(client):
    created = client.post("/employees", json=_sample()).json()
    res = client.patch(
        f"/employees/{created['id']}", json={"nickname": "Countess"}
    )
    assert res.status_code == 422


def test_delete_employee(client):
    created = client.post("/employees", json=_sample()).json()
    res = client.delete(f"/employees/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/employees/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/employees/nope").status_code == 404

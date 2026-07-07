"""End-to-end tests for the Employee Management API.

Rewritten for the Week 3 PostgreSQL migration. The original 13 tests
(from Week 2) were written against JSON-file storage and monkeypatched
EMPLOYEE_DATA_FILE; that fixture no longer applies now that the
repository is SQLAlchemy/Postgres-backed (app/database.py, get_db).

Uses the shared in-memory SQLite test client from tests/conftest.py,
so this file and test_auth.py don't fight over
app.dependency_overrides[get_db].
"""

from tests.conftest import client


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


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_employee():
    res = client.post("/employees", json=_sample())
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Ada Lovelace"
    assert body["email"] == "ada@example.com"
    assert body["id"]
    assert body["created_at"]


def test_create_duplicate_email_returns_409():
    client.post("/employees", json=_sample())
    res = client.post("/employees", json=_sample(name="Ada Twin"))
    assert res.status_code == 409


def test_create_invalid_salary_returns_422():
    res = client.post("/employees", json=_sample(salary=-5))
    assert res.status_code == 422


def test_create_invalid_department_returns_422():
    res = client.post("/employees", json=_sample(department="Wizardry"))
    assert res.status_code == 422


def test_get_employee():
    created = client.post("/employees", json=_sample()).json()
    res = client.get(f"/employees/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_missing_employee_returns_404():
    res = client.get("/employees/does-not-exist")
    assert res.status_code == 404


def test_list_with_filter_and_search():
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


def test_put_replaces_employee():
    created = client.post("/employees", json=_sample()).json()
    res = client.put(
        f"/employees/{created['id']}",
        json=_sample(position="Staff Engineer", salary=120000),
    )
    assert res.status_code == 200
    assert res.json()["position"] == "Staff Engineer"
    assert res.json()["salary"] == 120000


def test_patch_updates_single_field():
    created = client.post("/employees", json=_sample()).json()
    res = client.patch(
        f"/employees/{created['id']}", json={"salary": 105000}
    )
    assert res.status_code == 200
    assert res.json()["salary"] == 105000
    assert res.json()["name"] == "Ada Lovelace"  # unchanged


def test_patch_unknown_field_returns_422():
    created = client.post("/employees", json=_sample()).json()
    res = client.patch(
        f"/employees/{created['id']}", json={"nickname": "Countess"}
    )
    assert res.status_code == 422


def test_delete_employee():
    created = client.post("/employees", json=_sample()).json()
    res = client.delete(f"/employees/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/employees/{created['id']}").status_code == 404


def test_delete_missing_returns_404():
    assert client.delete("/employees/nope").status_code == 404
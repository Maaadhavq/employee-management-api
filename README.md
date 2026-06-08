# Employee Management REST API

> **Week 2 deliverable — Backend Development Fundamentals**
> A CRUD REST API for managing employee records, built with **FastAPI** and
> **Pydantic**. Demonstrates REST/HTTP fundamentals, request validation,
> automatic OpenAPI/Swagger docs, and a clean layered (MVC-style) architecture.

---

## Table of contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Architecture](#architecture)
5. [Setup & running](#setup--running)
6. [API reference](#api-reference)
7. [Validation rules](#validation-rules)
8. [Error handling](#error-handling)
9. [Testing](#testing)
10. [Postman collection](#postman-collection)
11. [What's next](#whats-next)

---

## Features

- Full **CRUD** for employees: create, read, update (full + partial), delete
- **Listing** with filtering (department, active status), free-text **search**, and **pagination**
- Strong **request validation** with Pydantic (email format, salary bounds, enum departments)
- Correct, meaningful **HTTP status codes** (`201`, `204`, `404`, `409`, `422`)
- Auto-generated **interactive API docs** (Swagger UI + ReDoc)
- **Layered architecture** (router → service → repository → model) that cleanly
  separates HTTP, business logic, and storage
- Domain-level **exception handling** mapped to clean JSON error responses
- A pytest **test suite** (13 tests) covering happy paths and edge cases

---

## Tech stack

| Concern        | Choice                          |
| -------------- | ------------------------------- |
| Language       | Python 3.10+                    |
| Web framework  | FastAPI                         |
| Validation     | Pydantic v2 (+ email-validator) |
| ASGI server    | Uvicorn                         |
| Persistence    | JSON file (swappable for a DB)  |
| Testing        | pytest + Starlette TestClient   |

---

## Project structure

```
employee-management-api/
├── app/
│   ├── main.py                 # App entry: metadata, routers, exception handlers
│   ├── config.py               # Settings (env-overridable)
│   ├── dependencies.py         # Dependency-injection providers
│   ├── exceptions.py           # Domain exceptions + HTTP handlers
│   ├── models/
│   │   └── employee.py         # Domain model (dataclass + Department enum)
│   ├── schemas/
│   │   └── employee.py         # Pydantic request/response schemas
│   ├── repository/
│   │   └── employee_repo.py    # Data access (JSON persistence)
│   ├── services/
│   │   └── employee_service.py # Business logic
│   └── routers/
│       └── employees.py        # API routes (controllers)
├── data/
│   └── employees.json          # Seed data (3 sample employees)
├── tests/
│   └── test_employees.py       # pytest suite
├── postman_collection.json     # Importable Postman collection
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Architecture

The app follows a layered design. Each layer has one job and only talks to the
layer directly beneath it, which keeps HTTP concerns, business rules, and
storage cleanly separated.

```
            HTTP request
                 │
                 ▼
   ┌──────────────────────────┐
   │  Router  (controller)    │  routers/employees.py
   │  - reads path/query/body │  HTTP only — no business logic
   └────────────┬─────────────┘
                │  validated Pydantic schema
                ▼
   ┌──────────────────────────┐
   │  Service (business logic)│  services/employee_service.py
   │  - uniqueness rules      │  raises domain exceptions
   │  - filtering/pagination  │
   └────────────┬─────────────┘
                │  domain Employee objects
                ▼
   ┌──────────────────────────┐
   │  Repository (data access)│  repository/employee_repo.py
   │  - read/write storage    │  the ONLY layer that knows storage
   └────────────┬─────────────┘
                │
                ▼
            employees.json
```

**Why it's built this way:** because storage is hidden behind the repository
interface, the JSON file can be replaced with PostgreSQL + SQLAlchemy in Week 3
without touching the router, service, or schemas. The Pydantic **schemas**
(API contract) are kept separate from the domain **model** (`Employee`
dataclass) for the same reason.

---

## Setup & running

**Prerequisites:** Python 3.10+

```bash
# 1. Clone and enter the project
git clone https://github.com/Maaadhavq/employee-management-api.git
cd employee-management-api

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn app.main:app --reload
```

The API is now at **http://127.0.0.1:8000**.

| Resource          | URL                              |
| ----------------- | -------------------------------- |
| Swagger UI (docs) | http://127.0.0.1:8000/docs       |
| ReDoc             | http://127.0.0.1:8000/redoc      |
| OpenAPI JSON      | http://127.0.0.1:8000/openapi.json |
| Health check      | http://127.0.0.1:8000/health     |

---

## API reference

Base path: `/employees`

| Method   | Path               | Description                  | Success |
| -------- | ------------------ | ---------------------------- | ------- |
| `POST`   | `/employees`       | Create an employee           | `201`   |
| `GET`    | `/employees`       | List (filter/search/page)    | `200`   |
| `GET`    | `/employees/{id}`  | Get one by id                | `200`   |
| `PUT`    | `/employees/{id}`  | Replace (full update)        | `200`   |
| `PATCH`  | `/employees/{id}`  | Partial update               | `200`   |
| `DELETE` | `/employees/{id}`  | Delete                       | `204`   |

### List query parameters

| Param        | Type   | Default | Notes                                   |
| ------------ | ------ | ------- | --------------------------------------- |
| `department` | enum   | —       | Filter by department                    |
| `is_active`  | bool   | —       | Filter by active status                 |
| `search`     | string | —       | Case-insensitive match on name + email  |
| `page`       | int    | `1`     | 1-indexed, `>= 1`                        |
| `page_size`  | int    | `20`    | `1`–`100`                               |

### Example: create an employee

**Request**

```http
POST /employees
Content-Type: application/json

{
  "name": "Katherine Johnson",
  "email": "katherine.johnson@example.com",
  "department": "Finance",
  "position": "Financial Analyst",
  "salary": 92000
}
```

**Response — `201 Created`**

```json
{
  "name": "Katherine Johnson",
  "email": "katherine.johnson@example.com",
  "department": "Finance",
  "position": "Financial Analyst",
  "salary": 92000.0,
  "id": "9f1c2e8a-4b6d-4c2a-9f0e-3a1b2c3d4e5f",
  "is_active": true,
  "created_at": "2026-06-07T10:15:00+00:00",
  "updated_at": "2026-06-07T10:15:00+00:00"
}
```

### Example: list response shape

```json
{
  "total": 3,
  "count": 3,
  "page": 1,
  "page_size": 20,
  "items": [ /* EmployeeResponse objects */ ]
}
```

---

## Validation rules

Enforced by the Pydantic schemas; violations return **`422 Unprocessable Entity`**
with a detailed body describing which field failed and why.

| Field        | Rule                                                            |
| ------------ | -------------------------------------------------------------- |
| `name`       | string, 2–100 characters                                       |
| `email`      | valid email format, **unique** across employees                |
| `department` | one of: `Engineering`, `Sales`, `Marketing`, `Human Resources`, `Finance`, `Operations` |
| `position`   | string, 2–100 characters                                       |
| `salary`     | number, `> 0` and `<= 10,000,000`                              |
| `is_active`  | boolean (defaults to `true`)                                   |

> **PUT vs PATCH:** `PUT` requires the full set of fields (it replaces the
> resource). `PATCH` accepts any subset; unknown fields are rejected with `422`.

---

## Error handling

| Status | Meaning              | When                                       |
| ------ | -------------------- | ------------------------------------------ |
| `404`  | Not Found            | No employee with the given id              |
| `409`  | Conflict             | Email already belongs to another employee  |
| `422`  | Unprocessable Entity | Request body fails validation              |

Example `404` body:

```json
{
  "detail": "Employee with id 'abc' was not found.",
  "employee_id": "abc"
}
```

---

## Testing

```bash
pytest -q
```

The suite covers create, read, list (with filter + search), full/partial
update, delete, and the `404` / `409` / `422` edge cases — using an isolated
temporary data file so tests never touch `data/employees.json`.

---

## Postman collection

Import **`postman_collection.json`** into Postman.

- Set the `base_url` collection variable (defaults to `http://127.0.0.1:8000`).
- Running **Create Employee** automatically captures the new `id` into the
  `employee_id` variable, so the Get / PUT / PATCH / DELETE requests work
  against it immediately.

---

## What's next

This API is intentionally storage-agnostic to set up later weeks:

- **Week 3 (Databases):** swap the JSON repository for PostgreSQL + SQLAlchemy —
  only `repository/employee_repo.py` changes.
- **Week 4 (AWS):** containerise and deploy behind a public endpoint.
- **Week 6 (Advanced backend):** add JWT authentication, middleware, logging,
  and rate limiting.

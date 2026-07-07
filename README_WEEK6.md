# Week 6 — Employee Management API Additions

Additive files to merge into `github.com/Maaadhavq/employee-management-api`,
building on the layered architecture (router → service → repository → model)
from Week 2/3. Nothing here replaces your existing employee/department code —
it sits alongside it.

## What's in this package

| File | Purpose |
|---|---|
| `app/core/security.py` | JWT creation/decoding + password hashing |
| `app/core/config_additions.py` | Reference for merging JWT settings into your existing `Settings` class |
| `app/core/logging_config.py` | Central logging setup |
| `app/models/user.py` | `users` table (SQLAlchemy 2.0 style, matches Week 3) |
| `app/schemas/auth.py` | Pydantic request/response models |
| `app/repositories/user_repository.py` | Data access for users |
| `app/services/auth_service.py` | Register/login business logic |
| `app/routers/auth.py` | `POST /auth/register`, `POST /auth/login` |
| `app/api/deps.py` | `get_current_user` dependency — protects any route |
| `app/routers/analytics.py` | JWT-protected routes reading the ETL's output tables (integration point with the Sales ETL pipeline) |
| `app/middleware/logging_middleware.py` | Request/response logging with request IDs |
| `app/middleware/rate_limit.py` | Rate limiting via slowapi |
| `app/routers/background_jobs_example.py` | `BackgroundTasks` example (async S3 export) |
| `main_reference.py` | Shows how everything wires into `main.py` |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Containerization |
| `requirements_additions.txt` | New dependencies to append |
| `tests/test_auth.py` | Auth flow tests (isolated SQLite, no network) |
| `postman_week6_additions.json` | Import alongside your Week 2 collection |

## Integration steps

1. **Copy files in** — drop each `app/...` file into the matching path in
   your existing repo. Nothing here overwrites your Week 2/3 employee or
   department code.

2. **Merge config** — add the `jwt_secret_key`, `jwt_algorithm`,
   `jwt_expire_minutes` fields into your existing `Settings` class (see
   `app/core/config_additions.py` for the exact snippet). Add matching
   values to your `.env`. Generate a real secret with:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Create the `users` table.** Since you're not using Alembic yet, either:
   - Let `Base.metadata.create_all(bind=engine)` pick it up automatically
     (if that's how Week 3 created tables), or
   - Run the equivalent `CREATE TABLE` manually via psql/pgAdmin.

4. **Merge `main.py`** using `main_reference.py` as a guide — add the
   logging middleware, rate limiter, and the two new routers
   (`auth`, `analytics`). Decide how much of your existing employee router
   you want behind `Depends(get_current_user)` — usually all of it except
   maybe a health check.

5. **Install new dependencies**:
   ```
   .venv\Scripts\python.exe -m pip install -r requirements_additions.txt
   ```
   (or append `requirements_additions.txt` into your main `requirements.txt`
   and reinstall).

6. **Run tests**:
   ```
   .venv\Scripts\python.exe -m pytest tests/test_auth.py -v
   ```
   Your existing 13 tests from Week 2/3 should be untouched and still pass.

7. **Rename analytics table names** in `app/routers/analytics.py` to match
   your actual four Week 5 aggregation table names once the ETL's
   `PostgresDataSink` (see the `sales-etl-additions` package) has written
   them into the `analytics` schema.

8. **Docker** — build and run locally first:
   ```
   docker compose up --build
   ```
   Then deploy the same image on EC2 (replaces the manual
   nginx → Gunicorn/Uvicorn process setup from Week 4, or run alongside it
   during the transition — your call).

## Week 6 deliverable checklist

- [x] **Authentication flow** — JWT register/login, protecting existing
      and new routes
- [x] **Dockerized application** — `Dockerfile` + `docker-compose.yml`
- [x] **Cloud deployment** — same EC2/RDS from Week 4, now serving the
      containerized + JWT-protected API
- [x] Middleware (request logging)
- [x] Logging
- [x] Rate limiting
- [x] Background jobs (BackgroundTasks example)
- [ ] AWS Lambda / API Gateway / DynamoDB — intentionally out of scope
      this week per your planned scope; these fit naturally into Week 7/8
      if you want to revisit them

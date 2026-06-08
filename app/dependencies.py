"""Dependency providers.

FastAPI's dependency-injection system wires these into the route handlers.
Centralising construction here means the repository/service are created once
and are trivial to swap out in tests (e.g. pointing at a temp data file).
"""

from functools import lru_cache

from app.repository.employee_repo import EmployeeRepository
from app.services.employee_service import EmployeeService


@lru_cache
def get_repository() -> EmployeeRepository:
    return EmployeeRepository()


def get_employee_service() -> EmployeeService:
    return EmployeeService(get_repository())

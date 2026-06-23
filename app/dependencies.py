"""Dependency providers.

FastAPI's dependency-injection system wires these into the route handlers.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository.employee_repo import EmployeeRepository
from app.services.employee_service import EmployeeService
from app.services.s3_service import S3Service


def get_repository(db: Session = Depends(get_db)) -> EmployeeRepository:
    return EmployeeRepository(db)


def get_employee_service(
    repo: EmployeeRepository = Depends(get_repository),
) -> EmployeeService:
    return EmployeeService(repo)


def get_s3_service() -> S3Service:
    return S3Service()

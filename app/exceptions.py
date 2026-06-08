"""Domain-specific exceptions and their HTTP exception handlers.

Keeping business-rule errors as plain Python exceptions means the service layer
stays framework-agnostic (it does not import FastAPI). The handlers registered
in `main.py` translate these into clean JSON HTTP responses with the right
status codes. This is the same separation-of-concerns idea behind the layered
architecture as a whole.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class EmployeeError(Exception):
    """Base class for all employee-related domain errors."""


class EmployeeNotFoundError(EmployeeError):
    """Raised when an employee with the given id does not exist."""

    def __init__(self, employee_id: str) -> None:
        self.employee_id = employee_id
        super().__init__(f"Employee with id '{employee_id}' was not found.")


class DuplicateEmailError(EmployeeError):
    """Raised when attempting to create/update an employee with an email
    address that already belongs to another employee."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"An employee with email '{email}' already exists.")


async def employee_not_found_handler(
    request: Request, exc: EmployeeNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "employee_id": exc.employee_id},
    )


async def duplicate_email_handler(
    request: Request, exc: DuplicateEmailError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc), "email": exc.email},
    )

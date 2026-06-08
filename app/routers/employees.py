"""Employee API routes -- the 'controller' in the MVC sense.

These handlers do only HTTP-level work: read path/query params and the
validated request body, delegate to the service, and shape the response. No
business logic lives here. The rich `responses=` metadata and docstrings feed
directly into the Swagger UI at /docs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_employee_service
from app.models.employee import Department, Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeePatch,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Employees"])


def _to_response(employee: Employee) -> EmployeeResponse:
    """Map a domain Employee to its API response schema."""
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        department=employee.department,
        position=employee.position,
        salary=employee.salary,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee",
    responses={409: {"description": "Email already exists"}},
)
def create_employee(
    payload: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Create a new employee. Emails must be unique."""
    employee = service.create_employee(payload)
    return _to_response(employee)


@router.get(
    "",
    response_model=EmployeeListResponse,
    summary="List employees",
)
def list_employees(
    department: Optional[Department] = Query(
        default=None, description="Filter by department."
    ),
    is_active: Optional[bool] = Query(
        default=None, description="Filter by active status."
    ),
    search: Optional[str] = Query(
        default=None, description="Case-insensitive search on name and email."
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Items per page (max 100)."
    ),
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeListResponse:
    """List employees with optional filtering, search and pagination."""
    employees, total = service.list_employees(
        department=department,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    items = [_to_response(e) for e in employees]
    return EmployeeListResponse(
        total=total,
        count=len(items),
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get an employee by id",
    responses={404: {"description": "Employee not found"}},
)
def get_employee(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Retrieve a single employee by id."""
    return _to_response(service.get_employee(employee_id))


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Replace an employee (full update)",
    responses={
        404: {"description": "Employee not found"},
        409: {"description": "Email already exists"},
    },
)
def replace_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Replace all editable fields of an employee (PUT semantics)."""
    return _to_response(service.replace_employee(employee_id, payload))


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Partially update an employee",
    responses={
        404: {"description": "Employee not found"},
        409: {"description": "Email already exists"},
    },
)
def patch_employee(
    employee_id: str,
    payload: EmployeePatch,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    """Update only the supplied fields of an employee (PATCH semantics)."""
    return _to_response(service.patch_employee(employee_id, payload))


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an employee",
    responses={404: {"description": "Employee not found"}},
)
def delete_employee(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Delete an employee by id. Returns 204 with no body on success."""
    service.delete_employee(employee_id)

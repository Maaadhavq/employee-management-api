"""Employee API routes -- the 'controller' in the MVC sense.

These handlers do only HTTP-level work: read path/query params and the
validated request body, delegate to the service, and shape the response. No
business logic lives here. The rich `responses=` metadata and docstrings feed
directly into the Swagger UI at /docs.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_employee_service, get_s3_service
from app.models.employee import Department, Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeePatch,
    EmployeeResponse,
    EmployeeUpdate,
    ExportResponse,
)
from app.services.employee_service import EmployeeService
from app.services.s3_service import (
    S3NotConfiguredError,
    S3Service,
    S3UploadError,
)

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
    "/export",
    response_model=ExportResponse,
    summary="Export all employees to a CSV stored in S3",
    responses={
        503: {"description": "S3 is not configured on this deployment"},
        502: {"description": "Upload to S3 failed"},
    },
)
def export_employees(
    service: EmployeeService = Depends(get_employee_service),
    s3: S3Service = Depends(get_s3_service),
) -> ExportResponse:
    """Generate a CSV of every employee, store it in S3, and return a
    time-limited download link.

    This exercises the full Week 4 cloud stack in one request: the EC2-hosted
    API reads from RDS, writes an object to S3 using the instance's IAM role,
    and hands back a presigned URL the client can use to download it directly.
    Declared before `/{employee_id}` so the path is not captured as an id.
    """
    csv_content = service.build_employees_csv()
    record_count = max(len(csv_content.strip().splitlines()) - 1, 0)
    generated_at = datetime.now(timezone.utc)
    key = f"exports/employees-{generated_at:%Y%m%dT%H%M%SZ}.csv"

    try:
        download_url = s3.upload_text(
            content=csv_content, key=key, content_type="text/csv"
        )
    except S3NotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except S3UploadError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ExportResponse(
        bucket=s3.bucket,
        key=key,
        record_count=record_count,
        generated_at=generated_at.isoformat(),
        download_url=download_url,
        expires_in_seconds=s3.ttl,
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

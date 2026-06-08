"""Pydantic schemas: the API's request and response contracts.

These define what the API accepts and returns, and they are where input
validation lives. FastAPI uses them to validate incoming JSON, to serialise
responses, and to auto-generate the OpenAPI/Swagger documentation.

Three input shapes are intentionally distinct:
  * EmployeeCreate  -> POST   (all business fields required)
  * EmployeeUpdate  -> PUT    (full replacement, all fields required)
  * EmployeePatch   -> PATCH  (partial update, every field optional)
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.employee import Department


class EmployeeBase(BaseModel):
    """Fields shared by the create/update request schemas, with validation."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the employee.",
        examples=["Ada Lovelace"],
    )
    email: EmailStr = Field(
        ...,
        description="Unique work email address.",
        examples=["ada.lovelace@example.com"],
    )
    department: Department = Field(
        ..., description="Department the employee belongs to."
    )
    position: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Job title / role.",
        examples=["Senior Backend Engineer"],
    )
    salary: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Annual salary; must be greater than 0.",
        examples=[95000.0],
    )


class EmployeeCreate(EmployeeBase):
    """Payload for creating a new employee (POST /employees)."""

    is_active: bool = Field(
        default=True, description="Whether the employee is currently active."
    )


class EmployeeUpdate(EmployeeBase):
    """Payload for a full update (PUT /employees/{id}).

    All business fields are required because PUT replaces the resource.
    """

    is_active: bool = Field(default=True)


class EmployeePatch(BaseModel):
    """Payload for a partial update (PATCH /employees/{id}).

    Every field is optional; only the provided fields are changed.
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    department: Optional[Department] = Field(default=None)
    position: Optional[str] = Field(default=None, min_length=2, max_length=100)
    salary: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    is_active: Optional[bool] = Field(default=None)


class EmployeeResponse(EmployeeBase):
    """Representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: str
    updated_at: str


class EmployeeListResponse(BaseModel):
    """Paginated list response wrapper."""

    total: int = Field(description="Total number of employees matching the query.")
    count: int = Field(description="Number of employees in this page.")
    page: int = Field(description="Current page number (1-indexed).")
    page_size: int = Field(description="Requested page size.")
    items: list[EmployeeResponse]

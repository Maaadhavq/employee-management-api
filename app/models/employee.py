"""The Employee domain model.

This is the *domain* representation of an employee, deliberately kept separate
from the Pydantic API schemas (`app/schemas`). The schemas describe what comes
in and goes out over HTTP; this dataclass is what the application stores and
reasons about internally. This is the OOP modelling from Week 1 carried forward
into a backend service, and it is the layer that maps most directly onto a
database table in Week 3.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Department(str, Enum):
    """Allowed departments. Inheriting from `str` makes the values
    JSON-serialisable and usable directly in Pydantic schemas."""

    ENGINEERING = "Engineering"
    SALES = "Sales"
    MARKETING = "Marketing"
    HR = "Human Resources"
    FINANCE = "Finance"
    OPERATIONS = "Operations"


def _now_iso() -> str:
    """Current UTC time as an ISO-8601 string (timezone-aware)."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Employee:
    """An employee record.

    `id`, `created_at` and `updated_at` are managed by the application and are
    never accepted from the client.
    """

    name: str
    email: str
    department: Department
    position: str
    salary: float
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def touch(self) -> None:
        """Update the `updated_at` timestamp after a modification."""
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        """Serialise to a plain dict suitable for JSON storage."""
        data = asdict(self)
        # Enum -> its string value for clean JSON.
        data["department"] = self.department.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        """Rebuild an Employee from stored JSON data."""
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            department=Department(data["department"]),
            position=data["position"],
            salary=data["salary"],
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
        )

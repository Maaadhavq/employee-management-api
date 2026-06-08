"""Service layer: the business logic.

The router (controller) handles HTTP concerns; the repository handles storage.
Everything in between -- enforcing rules like "emails must be unique", building
a new Employee from a validated request, applying a partial update, filtering
and paginating -- lives here. The service raises domain exceptions
(`EmployeeNotFoundError`, `DuplicateEmailError`) rather than HTTP errors, so it
remains independent of the web framework.
"""

from __future__ import annotations

from typing import Optional

from app.exceptions import DuplicateEmailError, EmployeeNotFoundError
from app.models.employee import Department, Employee
from app.repository.employee_repo import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeePatch, EmployeeUpdate


class EmployeeService:
    def __init__(self, repository: EmployeeRepository) -> None:
        self._repo = repository

    # ----- queries ----------------------------------------------------------

    def get_employee(self, employee_id: str) -> Employee:
        employee = self._repo.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(employee_id)
        return employee

    def list_employees(
        self,
        *,
        department: Optional[Department] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        """Return a (page_of_employees, total_matching) tuple.

        Filtering by department / active status / a free-text search on name and
        email is applied before pagination.
        """
        employees = self._repo.list_all()

        if department is not None:
            employees = [e for e in employees if e.department == department]
        if is_active is not None:
            employees = [e for e in employees if e.is_active == is_active]
        if search:
            needle = search.lower()
            employees = [
                e
                for e in employees
                if needle in e.name.lower() or needle in e.email.lower()
            ]

        # Stable, predictable ordering.
        employees.sort(key=lambda e: e.name.lower())

        total = len(employees)
        start = (page - 1) * page_size
        end = start + page_size
        return employees[start:end], total

    # ----- commands ---------------------------------------------------------

    def create_employee(self, payload: EmployeeCreate) -> Employee:
        if self._repo.get_by_email(payload.email) is not None:
            raise DuplicateEmailError(payload.email)

        employee = Employee(
            name=payload.name.strip(),
            email=str(payload.email).lower(),
            department=payload.department,
            position=payload.position.strip(),
            salary=payload.salary,
            is_active=payload.is_active,
        )
        return self._repo.add(employee)

    def replace_employee(
        self, employee_id: str, payload: EmployeeUpdate
    ) -> Employee:
        existing = self.get_employee(employee_id)  # raises if missing

        # If the email is changing, make sure it does not collide with someone
        # else's email.
        new_email = str(payload.email).lower()
        clash = self._repo.get_by_email(new_email)
        if clash is not None and clash.id != existing.id:
            raise DuplicateEmailError(new_email)

        existing.name = payload.name.strip()
        existing.email = new_email
        existing.department = payload.department
        existing.position = payload.position.strip()
        existing.salary = payload.salary
        existing.is_active = payload.is_active
        existing.touch()
        return self._repo.update(existing)

    def patch_employee(
        self, employee_id: str, payload: EmployeePatch
    ) -> Employee:
        existing = self.get_employee(employee_id)  # raises if missing

        # Only the fields the client actually sent.
        changes = payload.model_dump(exclude_unset=True)

        if "email" in changes:
            new_email = str(changes["email"]).lower()
            clash = self._repo.get_by_email(new_email)
            if clash is not None and clash.id != existing.id:
                raise DuplicateEmailError(new_email)
            changes["email"] = new_email

        if "name" in changes and changes["name"] is not None:
            changes["name"] = changes["name"].strip()
        if "position" in changes and changes["position"] is not None:
            changes["position"] = changes["position"].strip()

        for key, value in changes.items():
            setattr(existing, key, value)

        existing.touch()
        return self._repo.update(existing)

    def delete_employee(self, employee_id: str) -> None:
        if not self._repo.delete(employee_id):
            raise EmployeeNotFoundError(employee_id)

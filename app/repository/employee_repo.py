"""Data access layer (the 'repository').

This is the only part of the application that knows *how* employees are stored.
It uses SQLAlchemy to persist data to a PostgreSQL database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.employee import Employee, Department
from app.models.employee_orm import EmployeeORM


def orm_to_domain(orm: EmployeeORM) -> Employee:
    """Map a database EmployeeORM model to a domain Employee dataclass."""
    return Employee(
        id=orm.id,
        name=orm.name,
        email=orm.email,
        department=Department(orm.department),
        position=orm.position,
        salary=orm.salary,
        is_active=orm.is_active,
        created_at=orm.created_at.isoformat(),
        updated_at=orm.updated_at.isoformat(),
    )


def domain_to_orm(emp: Employee) -> EmployeeORM:
    """Map a domain Employee dataclass to a database EmployeeORM model."""
    return EmployeeORM(
        id=emp.id,
        name=emp.name,
        email=emp.email.lower(),
        department=emp.department.value,
        position=emp.position,
        salary=emp.salary,
        is_active=emp.is_active,
        created_at=datetime.fromisoformat(emp.created_at),
        updated_at=datetime.fromisoformat(emp.updated_at),
    )


class EmployeeRepository:
    """CRUD persistence for Employee records, backed by PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Employee]:
        orms = self._db.query(EmployeeORM).all()
        return [orm_to_domain(o) for o in orms]

    def get_by_id(self, employee_id: str) -> Optional[Employee]:
        orm = self._db.query(EmployeeORM).filter(EmployeeORM.id == employee_id).first()
        return orm_to_domain(orm) if orm else None

    def get_by_email(self, email: str) -> Optional[Employee]:
        orm = (
            self._db.query(EmployeeORM)
            .filter(EmployeeORM.email == email.lower())
            .first()
        )
        return orm_to_domain(orm) if orm else None

    def add(self, employee: Employee) -> Employee:
        orm = domain_to_orm(employee)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return orm_to_domain(orm)

    def update(self, employee: Employee) -> Employee:
        orm = self._db.query(EmployeeORM).filter(EmployeeORM.id == employee.id).first()
        if orm:
            orm.name = employee.name
            orm.email = employee.email.lower()
            orm.department = employee.department.value
            orm.position = employee.position
            orm.salary = employee.salary
            orm.is_active = employee.is_active
            orm.updated_at = datetime.fromisoformat(employee.updated_at)
            self._db.commit()
            self._db.refresh(orm)
            return orm_to_domain(orm)
        else:
            orm = domain_to_orm(employee)
            self._db.add(orm)
            self._db.commit()
            return employee

    def delete(self, employee_id: str) -> bool:
        orm = self._db.query(EmployeeORM).filter(EmployeeORM.id == employee_id).first()
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True

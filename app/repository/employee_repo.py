"""Data access layer (the 'repository').

This is the only part of the application that knows *how* employees are stored.
For Week 2 that storage is a JSON file (carrying forward the JSON persistence
from Week 1). Because every caller goes through this interface, the JSON file
can later be replaced with PostgreSQL + SQLAlchemy (Week 3) without changing the
service, router or schema layers.

A threading.Lock guards file reads/writes so concurrent requests cannot corrupt
the file.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.employee import Employee


class EmployeeRepository:
    """CRUD persistence for Employee records, backed by a JSON file."""

    def __init__(self, data_file: Optional[Path] = None) -> None:
        self._data_file = Path(data_file) if data_file else settings.DATA_FILE
        self._lock = threading.Lock()
        self._ensure_file()

    # ----- internal helpers -------------------------------------------------

    def _ensure_file(self) -> None:
        """Create the data file (and parent dir) with an empty list if absent."""
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._data_file.exists():
            self._data_file.write_text("[]", encoding="utf-8")

    def _read_all(self) -> list[Employee]:
        try:
            raw = self._data_file.read_text(encoding="utf-8").strip() or "[]"
            records = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable file -> treat as empty rather than crashing.
            records = []
        return [Employee.from_dict(r) for r in records]

    def _write_all(self, employees: list[Employee]) -> None:
        payload = [e.to_dict() for e in employees]
        # Write to a temp file then replace, so a crash mid-write cannot leave
        # the data file half-written.
        tmp = self._data_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self._data_file)

    # ----- public CRUD interface -------------------------------------------

    def list_all(self) -> list[Employee]:
        with self._lock:
            return self._read_all()

    def get_by_id(self, employee_id: str) -> Optional[Employee]:
        with self._lock:
            return next(
                (e for e in self._read_all() if e.id == employee_id), None
            )

    def get_by_email(self, email: str) -> Optional[Employee]:
        with self._lock:
            email = email.lower()
            return next(
                (e for e in self._read_all() if e.email.lower() == email), None
            )

    def add(self, employee: Employee) -> Employee:
        with self._lock:
            employees = self._read_all()
            employees.append(employee)
            self._write_all(employees)
            return employee

    def update(self, employee: Employee) -> Employee:
        with self._lock:
            employees = self._read_all()
            for i, existing in enumerate(employees):
                if existing.id == employee.id:
                    employees[i] = employee
                    self._write_all(employees)
                    return employee
            # Should not happen: callers check existence first.
            employees.append(employee)
            self._write_all(employees)
            return employee

    def delete(self, employee_id: str) -> bool:
        with self._lock:
            employees = self._read_all()
            remaining = [e for e in employees if e.id != employee_id]
            if len(remaining) == len(employees):
                return False
            self._write_all(remaining)
            return True

from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, CheckConstraint
from app.database import Base

class DepartmentORM(Base):
    __tablename__ = "departments"

    name = Column(String(50), primary_key=True)
    description = Column(String(255), nullable=True)
    cost_center = Column(String(20), nullable=True)

class EmployeeORM(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(50), ForeignKey("departments.name"), nullable=False)
    position = Column(String(100), nullable=False)
    salary = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("salary > 0", name="check_positive_salary"),
    )

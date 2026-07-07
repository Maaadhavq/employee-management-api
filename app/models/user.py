"""
Week 6 addition: users table for JWT authentication.

Matches the SQLAlchemy 2.0 declarative style used in the Week 3
Postgres migration (Mapped / mapped_column).
"""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

# Adjust this import to match wherever your existing Base lives
# (Week 3 repo: app/database.py or app/models/base.py)
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

"""
Week 6 addition: service layer for authentication logic.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.repository import user_repository


def register_user(db: Session, username: str, password: str) -> User:
    existing = user_repository.get_by_username(db, username)
    if existing:
        raise ValueError("Username already registered")
    return user_repository.create_user(db, username, password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = user_repository.get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def login(db: Session, username: str, password: str) -> Optional[str]:
    user = authenticate_user(db, username, password)
    if not user:
        return None
    return create_access_token(subject=user.username)

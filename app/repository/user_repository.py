"""
Repository layer for users, following the same
router -> service -> repository -> model pattern used across the app.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password


def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

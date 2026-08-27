"""
Placeholder auth dependency. Replace with real JWT/session validation
before shipping -- this currently just fetches the first user in the DB
so routes are testable without a full auth flow wired up yet.
"""

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.database import get_db
from app.models.user import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    # TODO: replace with real JWT-based auth (see app/core/security.py)
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

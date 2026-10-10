from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import User
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.auth import UserOut
from app.services.activity import log_activity

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _count(db: Session, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    return {
        "total_users": _count(db),
        "active_accounts": _count(db, User.is_active.is_(True)),
        "admins": _count(db, User.role == "admin"),
        "new_last_7_days": _count(db, User.created_at >= week_ago),
        "active_last_7_days": _count(db, User.last_login_at >= week_ago),
    }


@router.get("/users")
def list_users(
    search: str = Query(""),
    role: Literal["user", "admin"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(User)
    if search.strip():
        like = f"%{search.strip().lower()}%"
        query = query.where(or_(func.lower(User.email).like(like), func.lower(User.name).like(like)))
    if role:
        query = query.where(User.role == role)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [UserOut.model_validate(u) for u in rows], "total": total, "page": page, "page_size": page_size}


class UserUpdate(BaseModel):
    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, body: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User not found.")
    if user.id == admin.id and (body.role == "user" or body.is_active is False):
        raise AppError(409, "SELF_LOCKOUT", "You cannot remove your own admin access or deactivate yourself.")
    if body.role is not None:
        if body.role != user.role:
            log_activity(db, admin.id, "role_changed", "user", user.id, {"to": body.role})
        user.role = body.role
    if body.is_active is not None:
        if body.is_active != user.is_active:
            log_activity(db, admin.id, "account_activated" if body.is_active else "account_deactivated",
                         "user", user.id)
        user.is_active = body.is_active
    db.commit()
    return user
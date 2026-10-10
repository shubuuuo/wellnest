# import uuid

# from fastapi import Depends, Request
# from sqlalchemy.orm import Session

# from app.core.errors import AppError
# from app.core.security import decode_access_token
# from app.db.models import User
# from app.db.session import get_db

# COOKIE_NAME = "wellnest_session"


# def api_error(status_code: int, code: str, message: str, details=None, headers=None) -> AppError:
#     """Builds our {code, message, details} error. `headers` is accepted but unused."""
#     return AppError(status_code, code, message, details)


# def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
#     token = request.cookies.get(COOKIE_NAME)
#     if not token:
#         return None
#     sub = decode_access_token(token)
#     if not sub:
#         return None
#     try:
#         user_id = uuid.UUID(sub)
#     except ValueError:
#         return None
#     user = db.get(User, user_id)
#     if user is None or not user.is_active:
#         return None
#     return user


# def current_user(user: User | None = Depends(get_optional_user)) -> User:
#     if user is None:
#         raise api_error(401, "NOT_AUTHENTICATED", "Please log in to continue.")
#     return user

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(get_settings().cookie_name)
    user_id = decode_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise AppError(401, "NOT_AUTHENTICATED", "Please log in.")
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "This account has been deactivated.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise AppError(403, "FORBIDDEN", "Administrator access is required.")
    return user
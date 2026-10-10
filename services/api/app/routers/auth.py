import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.deps import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services.activity import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])

# A small brake on password guessing: 5 failures per 5 minutes per (ip, email).
_failures: dict[tuple[str, str], deque[float]] = defaultdict(deque)
WINDOW_SECONDS, MAX_FAILURES = 300, 5


def _start_session(response: Response, user: User) -> None:
    s = get_settings()
    response.set_cookie(
        key=s.cookie_name,
        value=create_token(user.id),
        max_age=s.jwt_expire_minutes * 60,
        httponly=True,      # JavaScript cannot read it
        samesite="lax",
        secure=s.cookie_secure,
        path="/",
    )


# @router.post("/register", response_model=UserOut, status_code=201)
# def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
#     if not body.consent:
#         raise AppError(422, "CONSENT_REQUIRED", "Please accept the data notice to create an account.")
#     email = body.email.strip().lower()
#     if db.scalar(select(User.id).where(User.email == email)):
#         raise AppError(409, "EMAIL_TAKEN", "An account with this email already exists.")

#     now = datetime.now(timezone.utc)
#     user = User(email=email, name=body.name, password_hash=hash_password(body.password),
#                 role="user", consented_at=now, last_login_at=now)
#     db.add(user)
#     try:
#         db.flush()  # assigns user.id and catches a duplicate email
#         log_activity(db, user.id, "register", "user", user.id)
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise AppError(409, "EMAIL_TAKEN", "An account with this email already exists.")

@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not body.consent:
        raise AppError(422, "CONSENT_REQUIRED", "Please accept the data notice to create an account.")
    email = body.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise AppError(409, "EMAIL_TAKEN", "An account with this email already exists.")

    now = datetime.now(timezone.utc)
    user = User(email=email, name=body.name, password_hash=hash_password(body.password),
                role="user", consented_at=now, last_login_at=now, training_consent=body.training_consent)
    db.add(user)
    try:
        db.flush()  # assigns user.id and catches a duplicate email
        log_activity(db, user.id, "register", "user", user.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "EMAIL_TAKEN", "An account with this email already exists.")
    _start_session(response, user)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    attempts = _failures[(request.client.host if request.client else "?", email)]
    now = time.time()
    while attempts and now - attempts[0] > WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= MAX_FAILURES:
        raise AppError(429, "TOO_MANY_ATTEMPTS", "Too many failed attempts. Please wait a few minutes.")

    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        attempts.append(now)
        raise AppError(401, "INVALID_CREDENTIALS", "Incorrect email or password.")
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "This account has been deactivated.")

    attempts.clear()
    user.last_login_at = datetime.now(timezone.utc)
    log_activity(db, user.id, "login", "user", user.id)
    db.commit()
    _start_session(response, user)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(get_settings().cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
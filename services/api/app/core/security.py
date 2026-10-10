# from datetime import datetime, timedelta, timezone

# import jwt
# from argon2 import PasswordHasher
# from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

# from app.core.config import settings

# _ph = PasswordHasher()
# # Used to burn the same time when the email doesn't exist (prevents timing leaks)
# DUMMY_HASH = _ph.hash("not-a-real-password")

# JWT_ALGORITHM = "HS256"


# def hash_password(password: str) -> str:
#     return _ph.hash(password)


# def verify_password(password: str, password_hash: str) -> bool:
#     try:
#         return _ph.verify(password_hash, password)
#     except (VerifyMismatchError, VerificationError, InvalidHash):
#         return False


# def password_needs_rehash(password_hash: str) -> bool:
#     return _ph.check_needs_rehash(password_hash)


# def _secret() -> str:
#     secret = settings.jwt_secret
#     if len(secret) < 32:
#         raise RuntimeError("JWT_SECRET must be set in .env and be at least 32 characters.")
#     return secret

# def create_access_token(user_id) -> str:
#     now = datetime.now(timezone.utc)
#     payload = {
#         "sub": str(user_id),
#         "iat": now,
#         "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
#     }
#     return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


# def decode_access_token(token: str) -> str | None:
#     """Returns the user id string, or None if the token is invalid/expired."""
#     try:
#         payload = jwt.decode(
#             token,
#             _secret(),
#             algorithms=[JWT_ALGORITHM],
#             options={"require": ["exp", "sub"]},
#         )
#     except jwt.PyJWTError:
#         return None
#     return payload.get("sub")

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def _secret() -> str:
    secret = get_settings().jwt_secret
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters. Set it in the root .env")
    return secret


def create_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=get_settings().jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": expires}, _secret(), algorithm="HS256")


def decode_token(token: str) -> UUID | None:
    try:
        return UUID(jwt.decode(token, _secret(), algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
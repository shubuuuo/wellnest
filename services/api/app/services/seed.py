import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import User
from app.db.session import get_session_factory

logger = logging.getLogger("wellnest")


def ensure_admin() -> None:
    s = get_settings()
    if not (s.database_url and s.admin_email and s.admin_password):
        logger.warning("DATABASE_URL / ADMIN_EMAIL / ADMIN_PASSWORD not set: no admin account created")
        return
    email = s.admin_email.strip().lower()
    try:
        with get_session_factory()() as db:
            if db.scalar(select(User.id).where(User.email == email)):
                return
            db.add(User(email=email, name=s.admin_name, password_hash=hash_password(s.admin_password),
                        role="admin", consented_at=datetime.now(timezone.utc)))
            db.commit()
            logger.warning("Admin account created: %s", email)
    except Exception:
        logger.exception("Could not create the admin account (is the database migrated?)")
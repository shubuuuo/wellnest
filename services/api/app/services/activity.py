from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import ActivityLog


def log_activity(
    db: Session,
    actor_id: UUID | None,
    action: str,
    entity: str | None = None,
    entity_id: UUID | None = None,
    details: dict | None = None,
) -> None:
    """Adds one row to the session. The caller commits, so the log and the change succeed or fail together."""
    db.add(ActivityLog(actor_user_id=actor_id, action=action, entity=entity, entity_id=entity_id, details=details or {}))
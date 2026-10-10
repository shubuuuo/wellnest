# from datetime import datetime

# from sqlalchemy import Boolean, CheckConstraint, DateTime, String, true
# from sqlalchemy.orm import Mapped, mapped_column

# from app.db.base import Base, CreatedAtMixin, IdMixin


# class User(IdMixin, CreatedAtMixin, Base):
#     __tablename__ = "users"
#     __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="role_valid"),)

#     email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
#     password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
#     name: Mapped[str] = mapped_column(String(120), nullable=False)
#     role: Mapped[str] = mapped_column(String(16), nullable=False, default="user", server_default="user")
#     is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
#     consented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
#     last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Text,
    UniqueConstraint, Uuid, false, func, text, true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="role_valid"),)

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user", server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    consented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    training_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

class Review(IdMixin, CreatedAtMixin, Base):
    """One editable review per user."""

    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ActivityLog(IdMixin, CreatedAtMixin, Base):
    """Who did what, and when. Never stores health values or emails in `details`."""

    __tablename__ = "activity_log"
    __table_args__ = (
        Index("ix_activity_log_created", "created_at"),
        Index("ix_activity_log_action_created", "action", "created_at"),
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    entity: Mapped[str | None] = mapped_column(String(48))
    entity_id: Mapped[UUID | None] = mapped_column(Uuid)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

class Prediction(IdMixin, CreatedAtMixin, Base):
    """One saved risk check: what the user entered and what the model answered."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("risk_band IN ('low', 'moderate', 'high')", name="risk_band_valid"),
        CheckConstraint("probability >= 0 AND probability <= 1", name="probability_range"),
        Index("ix_predictions_user_created", "user_id", "created_at"),
        Index("ix_predictions_dataset_created", "dataset", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(16), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)  # the exact values used, one key per column

class Outcome(IdMixin, CreatedAtMixin, Base):
    """The real result of one saved check, confirmed by an administrator (simulated doctor verification)."""

    __tablename__ = "outcomes"

    prediction_id: Mapped[UUID] = mapped_column(ForeignKey("predictions.id", ondelete="CASCADE"), unique=True, nullable=False)
    confirmed_cancer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    entered_pool: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())


class LearningEvent(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        CheckConstraint("kind IN ('online_update', 'batch_retrain', 'rollback', 'reset')", name="kind_valid"),
        CheckConstraint("status IN ('applied', 'rolled_back', 'info')", name="status_valid"),
        Index("ix_learning_events_dataset_created", "dataset", "created_at"),
    )

    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="applied", server_default="applied")
    n_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class TrainingPoolRow(IdMixin, CreatedAtMixin, Base):
    """A confirmed, consented record. Holds NO user id. event_id is set once an update has used it."""

    __tablename__ = "training_pool"
    __table_args__ = (
        CheckConstraint("label IN (0, 1)", name="label_binary"),
        Index("ix_training_pool_dataset_event", "dataset", "event_id"),
    )

    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    label: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("learning_events.id", ondelete="SET NULL"))


class ModelVersion(IdMixin, CreatedAtMixin, Base):
    """One saved version of an online model. Exactly one version per (dataset, model) is current."""

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("dataset", "model_name", "version", name="uq_model_versions_dataset_model_version"),
        Index("uq_model_versions_one_current", "dataset", "model_name", unique=True, postgresql_where=text("is_current")),
    )

    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    file: Mapped[str] = mapped_column(String(500), nullable=False)  # relative to MODEL_STORE_PATH
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # scores on the frozen test set
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("model_versions.id", ondelete="SET NULL"))
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("learning_events.id", ondelete="SET NULL"))
"""Administrator tools for the live-learning loop: confirm outcomes, update, roll back, batch-retrain."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import LearningEvent, Outcome, Prediction, TrainingPoolRow, User
from app.db.session import get_db
from app.deps import require_admin
from app.services import online
from app.services.activity import log_activity
from app.services.history import paginate, prediction_dict

router = APIRouter(prefix="/admin", tags=["live learning"])


class OutcomeIn(BaseModel):
    confirmed_cancer: bool


class BatchIn(BaseModel):
    name: str


@router.get("/outcomes")
def outcome_queue(
    dataset: str | None = None,
    state: Literal["pending", "confirmed", "all"] = "pending",
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Prediction, User.email, User.name, User.training_consent,
               Outcome.confirmed_cancer, Outcome.entered_pool, Outcome.created_at.label("outcome_at"))
        .join(User, User.id == Prediction.user_id)
        .outerjoin(Outcome, Outcome.prediction_id == Prediction.id)
    )
    if dataset:
        stmt = stmt.where(Prediction.dataset == dataset)
    if state == "pending":
        stmt = stmt.where(Outcome.id.is_(None))
    elif state == "confirmed":
        stmt = stmt.where(Outcome.id.is_not(None))
    total, rows = paginate(db, stmt.order_by(Prediction.created_at.desc(), Prediction.id), page, page_size)
    labels: dict[str, str] = {}
    items = []
    for p, email, name, consent, confirmed, entered, at in rows:
        items.append({
            **prediction_dict(p, labels), "user_id": str(p.user_id), "user_email": email, "user_name": name,
            "training_consent": consent,
            "outcome": None if confirmed is None else {"confirmed_cancer": confirmed, "entered_pool": entered, "at": at},
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/predictions/{prediction_id}/outcome")
def confirm_outcome(
    prediction_id: UUID, body: OutcomeIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    found = db.execute(select(Prediction, User).join(User, User.id == Prediction.user_id).where(Prediction.id == prediction_id)).first()
    if found is None:
        raise AppError(404, "PREDICTION_NOT_FOUND", "That result was not found.")
    p, owner = found
    if db.scalar(select(Outcome.id).where(Outcome.prediction_id == p.id)):
        raise AppError(409, "OUTCOME_EXISTS", "This outcome is already confirmed. Confirmed outcomes cannot be changed.")

    entered = bool(owner.training_consent)  # the consent gate: no consent, no learning
    db.add(Outcome(prediction_id=p.id, confirmed_cancer=body.confirmed_cancer, confirmed_by=admin.id, entered_pool=entered))
    if entered:
        db.add(TrainingPoolRow(dataset=p.dataset, features=p.inputs, label=int(body.confirmed_cancer)))
    # the log never records the health outcome itself
    log_activity(db, admin.id, "outcome_confirmed", "prediction", p.id, {"dataset": p.dataset, "entered_pool": entered})
    db.commit()

    result: dict = {"confirmed_cancer": body.confirmed_cancer, "entered_pool": entered}
    s = get_settings()
    if entered and s.online_learning_enabled and online.waiting_count(db, p.dataset) >= s.online_batch_size:
        try:
            event = online.apply_online_update(db, p.dataset, admin.id)
            models = event.details.get("models", [])
            result["update"] = {"event_id": str(event.id), "accepted": sum(1 for m in models if m["accepted"]), "total": len(models)}
        except AppError as exc:  # the record stays in the pool and joins the next update
            result["update_skipped"] = exc.message
    return result


@router.get("/learning/status")
def learning_status(dataset: str = Query(...), db: Session = Depends(get_db)):
    return online.status(db, dataset)


@router.get("/learning/events")
def learning_events(
    dataset: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)
):
    stmt = (select(LearningEvent, User.name).outerjoin(User, User.id == LearningEvent.created_by)
            .where(LearningEvent.dataset == dataset).order_by(LearningEvent.created_at.desc(), LearningEvent.id))
    total, rows = paginate(db, stmt, page, page_size)
    return {"items": [online.event_dict(e, name) for e, name in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/learning/update")
def learning_update(dataset: str = Query(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return online.event_dict(online.apply_online_update(db, dataset, admin.id), admin.name)


@router.post("/learning/rollback")
def learning_rollback(dataset: str = Query(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return online.event_dict(online.rollback_last(db, dataset, admin.id), admin.name)


@router.post("/learning/batch-retrain")
def learning_batch_retrain(body: BatchIn, dataset: str = Query(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return online.event_dict(online.batch_retrain(db, dataset, body.name, admin.id), admin.name)
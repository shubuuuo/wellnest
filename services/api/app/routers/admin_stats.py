"""Usage analytics, activity log and review moderation for administrators."""
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import ActivityLog, Prediction, Review, User
from app.db.session import get_db
from app.deps import require_admin
from app.services.activity import log_activity
from app.services.history import dataset_label, paginate

router = APIRouter(prefix="/admin", tags=["admin analytics"])


def _per_day(db: Session, column, since: datetime, *where, distinct_of=None) -> dict[date, int]:
    day = func.date(func.timezone("UTC", column)).label("d")
    counted = func.count(func.distinct(distinct_of)) if distinct_of is not None else func.count()
    rows = db.execute(select(day, counted).where(column >= since, *where).group_by(day)).all()
    return {d: n for d, n in rows}


def _rating_summary(db: Session) -> dict:
    avg, count = db.execute(select(func.avg(Review.rating), func.count())).one()
    counts = dict(db.execute(select(Review.rating, func.count()).group_by(Review.rating)).all())
    return {
        "average": round(float(avg), 2) if avg is not None else None,
        "count": count,
        "distribution": {str(n): counts.get(n, 0) for n in range(1, 6)},
    }


@router.get("/analytics")
def analytics(days: int = Query(30, ge=7, le=365), db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    since = datetime.combine(start, time.min, tzinfo=timezone.utc)

    new_users = _per_day(db, User.created_at, since)
    checks = _per_day(db, Prediction.created_at, since)
    active = _per_day(db, ActivityLog.created_at, since,
                      ActivityLog.actor_user_id.is_not(None), distinct_of=ActivityLog.actor_user_id)

    series = []
    for i in range(days):
        d = start + timedelta(days=i)
        series.append({"date": d.isoformat(), "new_users": new_users.get(d, 0),
                       "predictions": checks.get(d, 0), "active_users": active.get(d, 0)})

    repeat = select(Prediction.user_id).group_by(Prediction.user_id).having(func.count() >= 2).subquery()
    by_dataset = db.execute(
        select(Prediction.dataset, func.count()).group_by(Prediction.dataset).order_by(func.count().desc())
    ).all()
    bands = dict(db.execute(select(Prediction.risk_band, func.count()).group_by(Prediction.risk_band)).all())

    return {
        "days": days,
        "totals": {
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "predictions": db.scalar(select(func.count()).select_from(Prediction)) or 0,
            "users_with_checks": db.scalar(select(func.count(func.distinct(Prediction.user_id)))) or 0,
            "returning_users": db.scalar(select(func.count()).select_from(repeat)) or 0,
            "active_users_period": db.scalar(
                select(func.count(func.distinct(ActivityLog.actor_user_id))).where(ActivityLog.created_at >= since)
            ) or 0,
            "predictions_period": sum(s["predictions"] for s in series),
        },
        "series": series,
        "by_dataset": [{"dataset": d, "label": dataset_label(d), "count": n} for d, n in by_dataset],
        "by_band": {b: bands.get(b, 0) for b in ("low", "moderate", "high")},
        "ratings": _rating_summary(db),
    }


@router.get("/activity")
def activity(
    action: str | None = None,
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(ActivityLog, User.email, User.name).outerjoin(User, User.id == ActivityLog.actor_user_id)
    if action:
        stmt = stmt.where(ActivityLog.action == action)
    if search.strip():
        like = f"%{search.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.name).like(like)))
    total, rows = paginate(db, stmt.order_by(ActivityLog.created_at.desc(), ActivityLog.id), page, page_size)
    return {
        "items": [
            {"id": str(a.id), "created_at": a.created_at, "action": a.action, "entity": a.entity,
             "entity_id": str(a.entity_id) if a.entity_id else None, "details": a.details,
             "actor_id": str(a.actor_user_id) if a.actor_user_id else None, "actor_name": name, "actor_email": email}
            for a, email, name in rows
        ],
        "total": total, "page": page, "page_size": page_size,
        "actions": list(db.scalars(select(ActivityLog.action).distinct().order_by(ActivityLog.action))),
    }


@router.get("/reviews")
def reviews(
    rating: int | None = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Review, User.email, User.name).join(User, User.id == Review.user_id)
    if rating:
        stmt = stmt.where(Review.rating == rating)
    total, rows = paginate(db, stmt.order_by(Review.updated_at.desc(), Review.id), page, page_size)
    return {
        "items": [
            {"id": str(r.id), "rating": r.rating, "comment": r.comment, "created_at": r.created_at,
             "updated_at": r.updated_at, "user_name": name, "user_email": email}
            for r, email, name in rows
        ],
        "total": total, "page": page, "page_size": page_size,
        "summary": _rating_summary(db),
    }


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: UUID, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if review is None:
        raise AppError(404, "REVIEW_NOT_FOUND", "Review not found.")
    log_activity(db, admin.id, "review_deleted", "review", review.id, {"rating": review.rating})
    db.delete(review)
    db.commit()
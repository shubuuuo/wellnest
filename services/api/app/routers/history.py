"""What a signed-in user can see about themselves: history, health profile and reports."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Prediction, User
from app.db.session import get_db
from app.deps import get_current_user
from app.services.history import build_summary, model_metrics, paginate, prediction_dict
from app.services.activity import log_activity
from app.services.reports import health_report_pdf, pdf_response, prediction_report_pdf

router = APIRouter(prefix="/me", tags=["my data"])


@router.get("/predictions")
def my_predictions(
    dataset: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Prediction).where(Prediction.user_id == user.id)
    if dataset:
        stmt = stmt.where(Prediction.dataset == dataset)
    total, rows = paginate(db, stmt.order_by(Prediction.created_at.desc(), Prediction.id), page, page_size)
    labels: dict[str, str] = {}
    return {"items": [prediction_dict(r[0], labels) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/summary")
def my_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_summary(db, user.id)


# @router.get("/predictions/{prediction_id}/report.pdf")
# def my_prediction_report(prediction_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     # the user_id condition is the access rule: nobody can fetch somebody else's check by guessing an id
#     p = db.scalar(select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == user.id))
#     if p is None:
#         raise AppError(404, "PREDICTION_NOT_FOUND", "That result was not found.")
#     data = prediction_dict(p, {})
#     pdf = prediction_report_pdf(user.name, user.email, data, model_metrics(p.dataset, p.model_name))
#         # in my_prediction_report
#     log_activity(db, user.id, "report_downloaded", "prediction", p.id)
#     db.commit()

#     # in my_full_report
#     log_activity(db, user.id, "report_downloaded", "health_report", user.id)
#     db.commit()
#     return pdf_response(pdf, f"wellnest-risk-report-{str(p.id)[:8]}.pdf")


# @router.get("/report.pdf")
# def my_full_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     summary = build_summary(db, user.id)
#     rows = db.scalars(
#         select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.created_at.desc(), Prediction.id).limit(500)
#     ).all()
#     labels: dict[str, str] = {}
#     pdf = health_report_pdf(user.name, user.email, summary, [prediction_dict(p, labels) for p in rows])
#         # in my_prediction_report
#     log_activity(db, user.id, "report_downloaded", "prediction", p.id)
#     db.commit()

#     # in my_full_report
#     log_activity(db, user.id, "report_downloaded", "health_report", user.id)
#     db.commit()
#     return pdf_response(pdf, f"wellnest-health-report-{datetime.now(timezone.utc):%Y%m%d}.pdf")

@router.get("/predictions/{prediction_id}/report.pdf")
def my_prediction_report(prediction_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # the user_id condition is the access rule: nobody can fetch somebody else's check by guessing an id
    p = db.scalar(select(Prediction).where(Prediction.id == prediction_id, Prediction.user_id == user.id))
    if p is None:
        raise AppError(404, "PREDICTION_NOT_FOUND", "That result was not found.")
    data = prediction_dict(p, {})
    pdf = prediction_report_pdf(user.name, user.email, data, model_metrics(p.dataset, p.model_name))
    log_activity(db, user.id, "report_downloaded", "prediction", p.id)
    db.commit()
    return pdf_response(pdf, f"wellnest-risk-report-{str(p.id)[:8]}.pdf")


@router.get("/report.pdf")
def my_full_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    summary = build_summary(db, user.id)
    rows = db.scalars(
        select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.created_at.desc(), Prediction.id).limit(500)
    ).all()
    labels: dict[str, str] = {}
    pdf = health_report_pdf(user.name, user.email, summary, [prediction_dict(p, labels) for p in rows])
    log_activity(db, user.id, "report_downloaded", "health_report", user.id)
    db.commit()
    return pdf_response(pdf, f"wellnest-health-report-{datetime.now(timezone.utc):%Y%m%d}.pdf")
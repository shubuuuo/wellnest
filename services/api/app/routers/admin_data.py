"""Administrator view of everybody's saved checks: browse, filter, export and download reports."""
import csv
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from io import StringIO
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Prediction, User
from app.db.session import get_db
from app.services.history import build_summary, model_metrics, paginate, prediction_dict
from app.services.reports import health_report_pdf, pdf_response, prediction_report_pdf

router = APIRouter(prefix="/admin", tags=["admin"])

EXPORT_LIMIT = 50_000
BASE_COLUMNS = ["prediction_id", "created_at", "user_email", "user_name", "dataset", "model_name", "probability", "risk_band", "label"]


class Filters:
    """Query-string filters shared by the table and the CSV export."""

    def __init__(
        self,
        search: str = "",
        dataset: str | None = None,
        band: Literal["low", "moderate", "high"] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        self.search, self.dataset, self.band, self.date_from, self.date_to = search, dataset, band, date_from, date_to


def _statement(f: Filters):
    stmt = select(Prediction, User.email, User.name).join(User, User.id == Prediction.user_id)
    if f.search.strip():
        like = f"%{f.search.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.name).like(like)))
    if f.dataset:
        stmt = stmt.where(Prediction.dataset == f.dataset)
    if f.band:
        stmt = stmt.where(Prediction.risk_band == f.band)
    if f.date_from:
        stmt = stmt.where(Prediction.created_at >= datetime.combine(f.date_from, time.min, tzinfo=timezone.utc))
    if f.date_to:  # inclusive: everything up to the end of that day
        stmt = stmt.where(Prediction.created_at < datetime.combine(f.date_to + timedelta(days=1), time.min, tzinfo=timezone.utc))
    return stmt.order_by(Prediction.created_at.desc(), Prediction.id)


def _row(p: Prediction, email: str, name: str, labels: dict[str, str]) -> dict:
    return {**prediction_dict(p, labels), "user_id": str(p.user_id), "user_email": email, "user_name": name}


def _page(db: Session, stmt, page: int, page_size: int) -> dict:
    total, rows = paginate(db, stmt, page, page_size)
    labels: dict[str, str] = {}
    return {"items": [_row(p, email, name, labels) for p, email, name in rows], "total": total, "page": page, "page_size": page_size}


def _safe(value):
    """Stop spreadsheet programs from running text that starts like a formula (=, +, -, @)."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


@router.get("/predictions")
def all_predictions(
    f: Filters = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _page(db, _statement(f), page, page_size)


@router.get("/predictions/export.csv")
def export_predictions(f: Filters = Depends(), db: Session = Depends(get_db)):
    rows = db.execute(_statement(f).limit(EXPORT_LIMIT)).all()
    # with a dataset chosen every answer has the same fields, so they become columns; otherwise one JSON column
    input_keys: list[str] = []
    if f.dataset:
        for p, _, _ in rows:
            input_keys += [k for k in p.inputs if k not in input_keys]
    header = BASE_COLUMNS + (input_keys if f.dataset else ["inputs_json"])

    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(header)
    for p, email, name in rows:
        line = [str(p.id), p.created_at.isoformat(), email, name, p.dataset, p.model_name, p.probability, p.risk_band, p.label]
        if f.dataset:
            line += [p.inputs.get(k, "") for k in input_keys]
        else:
            line.append(json.dumps(p.inputs))
        writer.writerow([_safe(v) for v in line])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return Response(
        content="\ufeff" + out.getvalue(),  # the byte-order mark lets Excel read UTF-8 names correctly
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="wellnest-predictions-{stamp}.csv"'},
    )


@router.get("/predictions/{prediction_id}/report.pdf")
def prediction_report(prediction_id: UUID, db: Session = Depends(get_db)):
    found = db.execute(
        select(Prediction, User).join(User, User.id == Prediction.user_id).where(Prediction.id == prediction_id)
    ).first()
    if found is None:
        raise AppError(404, "PREDICTION_NOT_FOUND", "That result was not found.")
    p, owner = found
    pdf = prediction_report_pdf(owner.name, owner.email, prediction_dict(p, {}), model_metrics(p.dataset, p.model_name))
    return pdf_response(pdf, f"wellnest-risk-report-{str(p.id)[:8]}.pdf")


def _user_or_404(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User not found.")
    return user


@router.get("/users/{user_id}/summary")
def user_summary(user_id: UUID, db: Session = Depends(get_db)):
    _user_or_404(db, user_id)
    return build_summary(db, user_id)


@router.get("/users/{user_id}/predictions")
def user_predictions(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    _user_or_404(db, user_id)
    return _page(db, _statement(Filters()).where(Prediction.user_id == user_id), page, page_size)


@router.get("/users/{user_id}/report.pdf")
def user_report(user_id: UUID, db: Session = Depends(get_db)):
    user = _user_or_404(db, user_id)
    rows = db.scalars(
        select(Prediction).where(Prediction.user_id == user_id).order_by(Prediction.created_at.desc(), Prediction.id).limit(500)
    ).all()
    labels: dict[str, str] = {}
    pdf = health_report_pdf(user.name, user.email, build_summary(db, user_id), [prediction_dict(p, labels) for p in rows])
    # header values must be plain ASCII, so a name such as "Ravi" is kept and anything else is dropped
    who = re.sub(r"[^a-z0-9]+", "-", user.name.lower()).strip("-") or "user"
    return pdf_response(pdf, f"wellnest-health-report-{who}-{datetime.now(timezone.utc):%Y%m%d}.pdf")

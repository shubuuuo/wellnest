"""Helpers shared by the user routes (/me/...) and the admin routes (/admin/...)."""
from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Prediction
from app.services.store import read_json

MAX_POINTS = 500  # the profile and the full report look at the newest 500 checks of a user
TREND_STEP = 0.02  # a change of 2 percentage points or less counts as "no change"


def dataset_label(dataset: str) -> str:
    try:
        return str(read_json(dataset, "meta.json").get("label", dataset))
    except AppError:  # dataset folder was removed after the check was saved
        return dataset


def model_metrics(dataset: str, model_name: str) -> dict | None:
    """Current held-out test scores of a model, for the 'about the model' part of a report."""
    try:
        results = read_json(dataset, "results.json")
    except AppError:
        return None
    entry = next((m for m in results["models"] if m["name"] == model_name), None)
    if entry is None:
        return None
    final = entry["final"]
    return {
        "accuracy": final["accuracy"],
        "precision": final["precision"],
        "recall": final["recall"],
        "f1": final["f1"],
        "roc_auc": final["roc_auc"],
        "test_rows": results.get("test_rows"),
    }


def prediction_dict(p: Prediction, labels: dict[str, str]) -> dict:
    """labels is a small per-request cache so each dataset label is read from disk once."""
    if p.dataset not in labels:
        labels[p.dataset] = dataset_label(p.dataset)
    return {
        "id": str(p.id),
        "created_at": p.created_at,
        "dataset": p.dataset,
        "dataset_label": labels[p.dataset],
        "model_name": p.model_name,
        "model_trained_at": p.model_trained_at,
        "probability": p.probability,
        "label": p.label,
        "risk_band": p.risk_band,
        "inputs": p.inputs,
    }


def paginate(db: Session, stmt, page: int, page_size: int) -> tuple[int, list]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return total, rows


def build_summary(db: Session, user_id: UUID) -> dict:
    """The 'health profile': counts, latest result per dataset and a timeline of every check."""
    total = db.scalar(select(func.count()).select_from(Prediction).where(Prediction.user_id == user_id)) or 0
    newest_first = db.scalars(
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc(), Prediction.id)
        .limit(MAX_POINTS)
    ).all()
    rows = list(reversed(newest_first))  # oldest first, so the timeline reads left to right

    labels: dict[str, str] = {}
    band_counts = {"low": 0, "moderate": 0, "high": 0}
    by_dataset: dict[str, list[Prediction]] = defaultdict(list)
    for p in rows:
        band_counts[p.risk_band] += 1
        by_dataset[p.dataset].append(p)

    datasets = []
    for dataset, items in by_dataset.items():
        latest = items[-1]
        change = round(latest.probability - items[-2].probability, 4) if len(items) > 1 else None
        if change is None:
            trend = "first"
        elif change > TREND_STEP:
            trend = "up"
        elif change < -TREND_STEP:
            trend = "down"
        else:
            trend = "flat"
        datasets.append({
            "dataset": dataset,
            "label": labels.setdefault(dataset, dataset_label(dataset)),
            "checks": len(items),
            "latest": prediction_dict(latest, labels),
            "change": change,
            "trend": trend,
            "points": [
                {"id": str(p.id), "created_at": p.created_at, "probability": p.probability, "risk_band": p.risk_band}
                for p in items
            ],
        })
    datasets.sort(key=lambda d: d["latest"]["created_at"], reverse=True)

    return {
        "total_checks": total,
        "first_check_at": rows[0].created_at if rows else None,
        "last_check_at": rows[-1].created_at if rows else None,
        "band_counts": band_counts,
        "datasets": datasets,
    }
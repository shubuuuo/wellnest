"""The live-learning loop: confirmed outcomes -> anonymous pool -> guarded, versioned online updates."""
import copy
import hashlib
import shutil
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import ROOT_DIR, get_settings
from app.core.errors import AppError
from app.db.models import LearningEvent, ModelVersion, TrainingPoolRow, User
from app.services.activity import log_activity
from app.services.store import dataset_dir, get_preprocessor, get_stream_data, read_json

sys.path.insert(0, str(ROOT_DIR / "ml"))  # lets the API import ml/model_catalog.py
from model_catalog import SPECS, evaluate, make_model  # noqa: E402

_lock = threading.RLock()
MAX_BATCH = 500
CORE = ("accuracy", "precision", "recall", "f1", "roc_auc")


# ---------- files, fingerprint, loading ----------

def _store() -> Path:
    return get_settings().model_store_path


def _root(dataset: str) -> Path:
    return _store() / dataset / "versions"


def _online_entries(dataset: str) -> list[dict]:
    results = read_json(dataset, "results.json")
    return [m for m in results["models"] if m["mode"] == "online" and m.get("has_proba") and m.get("file")]


def _stem(entry: dict) -> str:
    return Path(entry["file"]).stem.removeprefix("final_")


@lru_cache(maxsize=16)
def _fp_cached(dataset: str, pre_mtime: int, npz_mtime: int) -> str:
    data = get_stream_data(dataset)
    h = hashlib.sha256()
    h.update((dataset_dir(dataset) / "preprocessor.joblib").read_bytes())
    h.update(data["X_test"].tobytes())
    h.update(data["y_test"].tobytes())
    return h.hexdigest()


def fingerprint(dataset: str) -> str:
    """Hash of the frozen test set plus the frozen preprocessor. Changes only if train.py is re-run."""
    folder = dataset_dir(dataset)
    return _fp_cached(dataset, (folder / "preprocessor.joblib").stat().st_mtime_ns, (folder / "stream.npz").stat().st_mtime_ns)


@lru_cache(maxsize=64)
def _load(path: str, mtime_ns: int):
    return joblib.load(path)


def _load_file(rel: str):
    path = _store() / rel
    return _load(str(path), path.stat().st_mtime_ns)


def _core(metrics: dict) -> dict:
    return {k: metrics[k] for k in CORE if k in metrics}


def _rank(v: ModelVersion) -> tuple[float, float]:
    return (v.metrics.get("f1", 0.0), v.metrics.get("recall", 0.0))


# ---------- versions ----------

def ensure_baseline(db: Session, dataset: str) -> None:
    """Version 0 of every online model is the model train.py produced.
    If train.py was re-run (fingerprint changed) the old versions no longer match the preprocessor, so they are reset."""
    marker = _root(dataset) / "fingerprint.txt"
    fp = fingerprint(dataset)

    def state() -> tuple[int, bool]:
        have = db.scalar(select(func.count()).select_from(ModelVersion).where(ModelVersion.dataset == dataset)) or 0
        stale = (have > 0 and not marker.exists()) or (marker.exists() and marker.read_text().strip() != fp)
        return have, stale

    have, stale = state()
    if have and not stale:
        return
    with _lock:
        have, stale = state()
        if have and not stale:
            return
        if stale:
            if have:
                db.execute(delete(ModelVersion).where(ModelVersion.dataset == dataset))
                db.add(LearningEvent(dataset=dataset, kind="reset", status="info",
                                     details={"reason": "train.py was re-run or the model store was missing; online versions were reset to the new base models."}))
            shutil.rmtree(_root(dataset), ignore_errors=True)
        _root(dataset).mkdir(parents=True, exist_ok=True)
        marker.write_text(fp)
        for entry in _online_entries(dataset):
            target = _root(dataset) / _stem(entry) / "v0.joblib"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dataset_dir(dataset) / entry["file"], target)
            db.add(ModelVersion(dataset=dataset, model_name=entry["name"], version=0,
                                file=target.relative_to(_store()).as_posix(),
                                metrics=_core(entry["final"]), is_current=True))
        db.commit()


def current_versions(db: Session, dataset: str) -> list[ModelVersion]:
    ensure_baseline(db, dataset)
    return list(db.scalars(
        select(ModelVersion).where(ModelVersion.dataset == dataset, ModelVersion.is_current.is_(True)).order_by(ModelVersion.model_name)
    ))


@dataclass
class LiveModel:
    name: str
    version: int
    trained_at: datetime
    model: object


def live_model(db: Session, dataset: str) -> LiveModel:
    """The model users are answered by: the online model whose current version scores best on the frozen test set."""
    versions = current_versions(db, dataset)
    if not versions:
        raise AppError(503, "NO_ONLINE_MODEL", f"No online model found. Run: python ml/train.py {dataset}")
    best = max(versions, key=_rank)
    return LiveModel(best.model_name, best.version, best.created_at, _load_file(best.file))


# ---------- the pool ----------

def _matrix(dataset: str, rows: list[TrainingPoolRow]):
    columns = read_json(dataset, "columns.json")
    frame = pd.DataFrame([r.features for r in rows])[columns]
    X = get_preprocessor(dataset).transform(frame).astype(np.float32)  # the frozen preprocessor, never refitted
    return X, np.array([r.label for r in rows])


def waiting_count(db: Session, dataset: str) -> int:
    return db.scalar(select(func.count()).select_from(TrainingPoolRow).where(
        TrainingPoolRow.dataset == dataset, TrainingPoolRow.event_id.is_(None))) or 0


# ---------- the three actions ----------

def apply_online_update(db: Session, dataset: str, actor_id: UUID | None) -> LearningEvent:
    s = get_settings()
    if not s.online_learning_enabled:
        raise AppError(409, "ONLINE_LEARNING_OFF", "Online learning is switched off (ONLINE_LEARNING_ENABLED=false).")
    if not _lock.acquire(blocking=False):
        raise AppError(409, "BUSY", "Another learning action is running. Please wait a moment.")
    try:
        ensure_baseline(db, dataset)
        rows = list(db.scalars(
            select(TrainingPoolRow).where(TrainingPoolRow.dataset == dataset, TrainingPoolRow.event_id.is_(None))
            .order_by(TrainingPoolRow.created_at).limit(MAX_BATCH)
        ))
        if not rows:
            raise AppError(409, "POOL_EMPTY", "No confirmed records are waiting.")
        X, y = _matrix(dataset, rows)
        test = get_stream_data(dataset)
        X_test, y_test = test["X_test"], test["y_test"]
        tolerance = s.auto_promote_guard_tolerance
        entries = {m["name"]: m for m in _online_entries(dataset)}

        event = LearningEvent(dataset=dataset, kind="online_update", status="info", n_records=len(rows), created_by=actor_id, details={})
        db.add(event)
        db.flush()

        outcomes = []
        for cur in current_versions(db, dataset):
            model = copy.deepcopy(_load_file(cur.file))  # never touch the cached copy
            before = _core(cur.metrics)
            try:
                model.partial_fit(X, y)  # ONLINE LEARNING: update with the new records only
            except Exception as exc:  # one model that cannot take this batch must not stop the others
                outcomes.append({"model": cur.model_name, "accepted": False, "before": before, "after": None,
                                 "reason": f"update failed ({type(exc).__name__})"})
                continue
            after = _core(evaluate(model, X_test, y_test))
            ok = after["f1"] >= before["f1"] - tolerance and after["recall"] >= before["recall"] - tolerance
            item = {"model": cur.model_name, "accepted": ok, "before": before, "after": after}
            if ok:
                number = (db.scalar(select(func.max(ModelVersion.version)).where(
                    ModelVersion.dataset == dataset, ModelVersion.model_name == cur.model_name)) or 0) + 1
                target = _root(dataset) / _stem(entries[cur.model_name]) / f"v{number}.joblib"
                joblib.dump(model, target)
                cur.is_current = False
                db.flush()  # free the "one current version" slot before adding the new one
                db.add(ModelVersion(dataset=dataset, model_name=cur.model_name, version=number,
                                    file=target.relative_to(_store()).as_posix(), metrics=after,
                                    is_current=True, parent_id=cur.id, event_id=event.id))
                item["version"] = number
            else:
                item["reason"] = (f"Rejected by the safety guard: F1 {before['f1']:.3f}→{after['f1']:.3f}, "
                                  f"recall {before['recall']:.3f}→{after['recall']:.3f} (allowed drop {tolerance}).")
            outcomes.append(item)

        for r in rows:
            r.event_id = event.id
        accepted = sum(1 for o in outcomes if o["accepted"])
        event.status = "applied" if accepted else "info"
        event.details = {"models": outcomes, "tolerance": tolerance, "fingerprint": fingerprint(dataset)[:12],
                         "positives": int(y.sum()), "negatives": int(len(y) - y.sum())}
        log_activity(db, actor_id, "online_update", "learning_event", event.id,
                     {"dataset": dataset, "records": len(rows), "accepted_models": accepted})
        db.commit()
        return event
    finally:
        _lock.release()


def rollback_last(db: Session, dataset: str, actor_id: UUID | None) -> LearningEvent:
    if not _lock.acquire(blocking=False):
        raise AppError(409, "BUSY", "Another learning action is running. Please wait a moment.")
    try:
        target = db.scalar(select(LearningEvent).where(
            LearningEvent.dataset == dataset, LearningEvent.kind == "online_update", LearningEvent.status == "applied"
        ).order_by(LearningEvent.created_at.desc(), LearningEvent.id).limit(1))
        if target is None:
            raise AppError(409, "NOTHING_TO_ROLL_BACK", "There is no applied update to roll back.")
        reverted = []
        for v in db.scalars(select(ModelVersion).where(ModelVersion.event_id == target.id, ModelVersion.is_current.is_(True))):
            parent = db.get(ModelVersion, v.parent_id) if v.parent_id else None
            if parent is None:
                continue
            v.is_current = False
            db.flush()
            parent.is_current = True
            reverted.append({"model": v.model_name, "from_version": v.version, "to_version": parent.version})
        target.status = "rolled_back"
        event = LearningEvent(dataset=dataset, kind="rollback", status="info", n_records=target.n_records, created_by=actor_id,
                              details={"reverted_event_id": str(target.id), "reverted": reverted})
        db.add(event)
        db.flush()
        log_activity(db, actor_id, "online_rollback", "learning_event", event.id, {"dataset": dataset, "models": len(reverted)})
        db.commit()
        return event
    finally:
        _lock.release()


def batch_retrain(db: Session, dataset: str, name: str, actor_id: UUID | None) -> LearningEvent:
    """Batch-only models cannot learn online. We retrain from scratch on base data + every pool record and
    record the scores for comparison. The result is NOT deployed."""
    results = read_json(dataset, "results.json")
    entry = next((m for m in results["models"] if m["name"] == name), None)
    if entry is None or name not in SPECS:
        raise AppError(404, "UNKNOWN_MODEL", f"Unknown model '{name}'.")
    if entry["mode"] != "batch":
        raise AppError(422, "NOT_A_BATCH_MODEL", f"'{name}' learns online, use the online update instead.")
    data = get_stream_data(dataset)
    if "X_train" not in data or "class_weight" not in results:
        raise AppError(409, "RETRAIN_NEEDS_TRAINING", f"Run once more: python ml/train.py {dataset}")
    rows = list(db.scalars(select(TrainingPoolRow).where(TrainingPoolRow.dataset == dataset)))
    if not rows:
        raise AppError(409, "POOL_EMPTY", "No confirmed records in the pool yet.")
    if not _lock.acquire(blocking=False):
        raise AppError(409, "BUSY", "Another learning action is running. Please wait a moment.")
    try:
        spec = SPECS[name]
        value = entry["param"]["value"]
        value = int(value) if spec["int"] else value
        cw = {int(k): v for k, v in results["class_weight"].items()}
        X_new, y_new = _matrix(dataset, rows)
        model = make_model(name, cw, value)
        started = time.time()
        model.fit(np.vstack([data["X_train"], X_new]), np.concatenate([data["y_train"], y_new]))
        seconds = round(time.time() - started, 1)
        after = _core(evaluate(model, data["X_test"], data["y_test"]))
        event = LearningEvent(dataset=dataset, kind="batch_retrain", status="info", n_records=len(rows), created_by=actor_id,
                              details={"model": name, "before": _core(entry["final"]), "after": after,
                                       "fit_seconds": seconds, "deployed": False,
                                       "note": "Online update is not possible for this model. It was retrained from scratch on all data; the scores are shown for comparison only."})
        db.add(event)
        db.flush()
        log_activity(db, actor_id, "batch_retrain", "learning_event", event.id, {"dataset": dataset, "model": name, "records": len(rows)})
        db.commit()
        return event
    finally:
        _lock.release()


# ---------- read models for the API ----------

def event_dict(e: LearningEvent, actor_name: str | None = None) -> dict:
    return {"id": str(e.id), "created_at": e.created_at, "kind": e.kind, "status": e.status,
            "n_records": e.n_records, "details": e.details, "actor_name": actor_name}


def status(db: Session, dataset: str) -> dict:
    s = get_settings()
    versions = current_versions(db, dataset)
    best = max(versions, key=_rank) if versions else None
    results = read_json(dataset, "results.json")
    labels = dict(db.execute(select(TrainingPoolRow.label, func.count()).where(TrainingPoolRow.dataset == dataset)
                             .group_by(TrainingPoolRow.label)).all())
    batch_events = list(db.scalars(select(LearningEvent).where(
        LearningEvent.dataset == dataset, LearningEvent.kind == "batch_retrain").order_by(LearningEvent.created_at.desc())))
    batch = []
    for m in results["models"]:
        if m["mode"] != "batch":
            continue
        last = next((e for e in batch_events if e.details.get("model") == m["name"]), None)
        batch.append({"name": m["name"], "baseline": _core(m["final"]),
                      "latest": last.details if last else None, "latest_at": last.created_at if last else None,
                      "latest_records": last.n_records if last else None})
    applied = db.scalar(select(func.count()).select_from(LearningEvent).where(
        LearningEvent.dataset == dataset, LearningEvent.kind == "online_update", LearningEvent.status == "applied")) or 0
    return {
        "dataset": dataset,
        "online_enabled": s.online_learning_enabled,
        "batch_size": s.online_batch_size,
        "tolerance": s.auto_promote_guard_tolerance,
        "fingerprint": fingerprint(dataset)[:12],
        "pool": {"total": sum(labels.values()), "waiting": waiting_count(db, dataset),
                 "positive": labels.get(1, 0), "negative": labels.get(0, 0)},
        "live": {"name": best.model_name, "version": best.version} if best else None,
        "online_models": [{"name": v.model_name, "version": v.version, "is_live": v is best,
                           "metrics": _core(v.metrics), "created_at": v.created_at} for v in versions],
        "batch_models": batch,
        "can_roll_back": applied > 0,
    }
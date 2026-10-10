import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.config import ROOT_DIR
from app.core.errors import AppError

ART = ROOT_DIR / "ml" / "artifacts"


def list_datasets() -> list[dict]:
    """Every folder under ml/artifacts that has been trained."""
    found = []
    if ART.exists():
        for folder in sorted(ART.iterdir()):
            if folder.is_dir() and (folder / "meta.json").exists() and (folder / "results.json").exists():
                found.append(json.loads((folder / "meta.json").read_text()))
    return found


def _dir(dataset: str) -> Path:
    if dataset not in {d["id"] for d in list_datasets()}:
        raise AppError(404, "UNKNOWN_DATASET", f"Dataset '{dataset}' is not trained. Run: python ml/train.py {dataset}")
    return ART / dataset


@lru_cache
def _cached_load(path: str, mtime_ns: int, kind: str) -> Any:
    # mtime_ns is part of the cache key, so retraining refreshes the cache automatically
    p = Path(path)
    if kind == "json":
        return json.loads(p.read_text())
    if kind == "joblib":
        return joblib.load(p)
    data = np.load(p)
    return {key: data[key] for key in data.files}


def _load(folder: Path, filename: str, kind: str) -> Any:
    path = folder / filename
    if not path.exists():
        raise AppError(503, "ARTIFACTS_MISSING", "Model files not found. Run: python ml/train.py <dataset>")
    return _cached_load(str(path), path.stat().st_mtime_ns, kind)


def read_json(dataset: str, filename: str) -> Any:
    return _load(_dir(dataset), filename, "json")


def get_preprocessor(dataset: str):
    return _load(_dir(dataset), "preprocessor.joblib", "joblib")

def dataset_dir(dataset: str) -> Path:
    return _dir(dataset)

def get_best_model(dataset: str):
    folder = _dir(dataset)
    results = _load(folder, "results.json", "json")
    best = next(m for m in results["models"] if m["name"] == results["best_model"])
    return best["name"], _load(folder, best["file"], "joblib")


def get_stream_data(dataset: str) -> dict[str, np.ndarray]:
    return _load(_dir(dataset), "stream.npz", "npz")


def load_warm_models(dataset: str) -> dict[str, Any]:
    """Fresh copies every call (not cached), so each demo run starts from the same small base."""
    folder = _dir(dataset)
    results = _load(folder, "results.json", "json")
    return {m["name"]: joblib.load(folder / m["warm_file"]) for m in results["models"] if m["mode"] == "online"}
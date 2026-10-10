import copy
import json
import sys
import threading
import time

import joblib

from app.core.config import ROOT_DIR
from app.core.errors import AppError
from app.services.store import dataset_dir, get_stream_data, read_json

sys.path.insert(0, str(ROOT_DIR / "ml"))  # lets the API import ml/model_catalog.py
from model_catalog import SPECS, evaluate, make_model, roc_points  # noqa: E402

_lock = threading.Lock()


def retrain(dataset: str, name: str, value: float | None) -> dict:
    folder = dataset_dir(dataset)
    results = copy.deepcopy(read_json(dataset, "results.json"))  # never edit the cached copy
    entry = next((m for m in results["models"] if m["name"] == name), None)
    if entry is None or name not in SPECS:
        raise AppError(404, "UNKNOWN_MODEL", f"Unknown model '{name}'.")

    spec = SPECS[name]
    value = entry["param"]["value"] if value is None else value
    if not spec["min"] <= value <= spec["max"]:
        raise AppError(422, "PARAM_OUT_OF_RANGE", f"{spec['label']} must be between {spec['min']} and {spec['max']}.")
    if spec["int"]:
        value = int(value)

    data = get_stream_data(dataset)
    if "X_train" not in data or "class_weight" not in results:
        raise AppError(409, "RETRAIN_NEEDS_TRAINING", f"Run once more: python ml/train.py {dataset}")

    if not _lock.acquire(blocking=False):
        raise AppError(409, "BUSY", "Another retrain is running. Please wait for it to finish.")
    try:
        cw = {int(k): v for k, v in results["class_weight"].items()}
        model = make_model(name, cw, value)
        started = time.time()
        model.fit(data["X_train"], data["y_train"])
        seconds = round(time.time() - started, 1)

        entry["previous"] = {"metrics": entry["final"], "param_value": entry["param"]["value"],
                             "fit_seconds": entry["fit_seconds"]}
        entry["final"] = evaluate(model, data["X_test"], data["y_test"])
        entry["roc"] = roc_points(model, data["X_test"], data["y_test"])
        entry["param"]["value"] = value
        entry["fit_seconds"] = seconds

        usable = [m for m in results["models"] if m["has_proba"]]
        results["best_model"] = max(usable, key=lambda m: (m["final"]["f1"], m["final"]["recall"]))["name"]

        joblib.dump(model, folder / entry["file"])
        (folder / "results.json").write_text(json.dumps(results, indent=2))
        return results
    finally:
        _lock.release()
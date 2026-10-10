import json
import time
from collections.abc import Iterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sklearn.metrics import accuracy_score, f1_score, recall_score

from app.services.store import get_stream_data, load_warm_models, read_json

router = APIRouter(prefix="/learning", tags=["learning"])


def _scores(model, X, y) -> dict[str, float]:
    pred = model.predict(X)
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
    }


def _event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.get("/stream")
def stream(dataset: str = Query(...), chunk: int = Query(250, ge=50, le=2000), delay: float = Query(0.4, ge=0, le=3)):
    results = read_json(dataset, "results.json")
    data = get_stream_data(dataset)
    models = load_warm_models(dataset)
    X_stream, y_stream, X_test, y_test = data["X_stream"], data["y_stream"], data["X_test"], data["y_test"]
    batch = {m["name"]: {"warm": m["warm"], "final": m["final"]} for m in results["models"] if m["mode"] == "batch"}

    def generate() -> Iterator[str]:
        yield _event({"type": "start", "total_rows": int(len(y_stream)), "chunk": chunk, "batch": batch})
        # step 0: the models before they have seen any streamed row
        yield _event({"type": "step", "rows_seen": 0,
                      "models": {n: _scores(m, X_test, y_test) for n, m in models.items()}})
        for start in range(0, len(y_stream), chunk):
            Xc, yc = X_stream[start:start + chunk], y_stream[start:start + chunk]
            for model in models.values():
                model.partial_fit(Xc, yc)  # ONLINE LEARNING: update with the new rows only
            seen = min(start + chunk, len(y_stream))
            yield _event({"type": "step", "rows_seen": seen,
                          "models": {n: _scores(m, X_test, y_test) for n, m in models.items()}})
            time.sleep(delay)
        yield _event({"type": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

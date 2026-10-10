import json
import re
from collections.abc import Iterator
from functools import lru_cache

import httpx
import numpy as np

from app.core.config import ROOT_DIR, get_settings
from app.core.errors import AppError
from app.services.store import ART, list_datasets, read_json

KNOWLEDGE_DIR = ROOT_DIR / "ml" / "knowledge"

SYSTEM_PROMPT = """You are the WellNest Assistant inside a student machine-learning demo about cancer risk prediction.

Rules:
- For anything about this app, its dataset, its models or its scores, answer from the CONTEXT below and quote numbers exactly as written there.
- If the context does not contain the answer, say you don't know instead of guessing. You may explain general machine-learning ideas in simple words.
- You are not a doctor. Never diagnose, never interpret a person's own symptoms or test results, and never recommend treatment. For health worries, tell the user to see a qualified clinician.
- Keep answers short (under 120 words) and plain.

CONTEXT:
{context}"""


def _knowledge_chunks() -> list[dict]:
    """One chunk per paragraph of every .md file, prefixed with its heading."""
    chunks = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        heading = ""
        for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            block = block.strip()
            if not block:
                continue
            if block.startswith("#") and "\n" not in block:
                heading = block.lstrip("# ").strip()
                continue
            chunks.append({"source": path.name, "text": f"{heading}: {block}" if heading else block})
    return chunks


def _dataset_chunks(dataset: str) -> list[dict]:
    """Facts written from your real results, so the numbers the bot quotes are correct."""
    summary = read_json(dataset, "dataset_summary.json")
    results = read_json(dataset, "results.json")
    label = next((d["label"] for d in list_datasets() if d["id"] == dataset), dataset)
    counts = summary["class_counts"]

    chunks = [{
        "source": "dataset",
        "text": (
            f"The '{label}' dataset in this app has {summary['rows']:,} rows and {summary['columns']} input columns. "
            f"The target column is '{summary['target']}'. {counts['cancer']:,} rows are cancer cases "
            f"({summary['positive_rate']:.1%}) and {counts['no_cancer']:,} are not. Always guessing 'no cancer' "
            f"would reach {results['baseline_accuracy']:.1%} accuracy. The test set has {results['test_rows']:,} rows, "
            f"the small starting set {results['base_rows']:,} rows and the stream {results['stream_rows']:,} rows."
        ),
    }]

    numeric = [h["name"] for h in summary["numeric"]][:40]
    categorical = [h["name"] for h in summary["categorical"]][:40]
    chunks.append({
        "source": "dataset",
        "text": f"Input features of '{label}'. Numeric: {', '.join(numeric) or 'none'}. "
                f"Categorical: {', '.join(categorical) or 'none'}.",
    })

    for m in results["models"]:
        f, w = m["final"], m["warm"]
        kind = ("an online model: it can keep learning from new rows" if m["mode"] == "online"
                else "a batch-only model: it cannot learn online and must be retrained on all data")
        chunks.append({
            "source": "results",
            "text": (
                f"On the '{label}' dataset, {m['name']} is {kind}. Trained on all training rows it scored "
                f"accuracy {f['accuracy']:.3f}, precision {f['precision']:.3f}, recall {f['recall']:.3f}, "
                f"F1 {f['f1']:.3f}, ROC-AUC {f['roc_auc']:.3f} on the test set. Trained only on the small starting "
                f"set it scored accuracy {w['accuracy']:.3f}, recall {w['recall']:.3f}, F1 {w['f1']:.3f}. "
                f"Training took {m['fit_seconds']} seconds. Confusion matrix: {f['tp']} true cancers found, "
                f"{f['fn']} cancers missed, {f['fp']} false alarms, {f['tn']} true negatives."
            ),
        })

    chunks.append({
        "source": "results",
        "text": f"On '{label}', the best model used by the Predict tab is {results['best_model']}. It is chosen by "
                f"highest F1 among the models that output probabilities.",
    })
    return chunks


def _embed(texts: list[str]) -> np.ndarray:
    s = get_settings()
    try:
        response = httpx.post(
            f"{s.ollama_url}/api/embed",
            json={"model": s.embed_model, "input": texts},
            timeout=120,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AppError(
            503, "OLLAMA_UNAVAILABLE",
            f"Cannot use Ollama. Start it (ollama serve) and check that '{s.embed_model}' is installed.",
        ) from exc
    vectors = np.array(response.json()["embeddings"], dtype=np.float32)
    return vectors / np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9, None)


@lru_cache(maxsize=8)
def _build_index(dataset: str, signature: tuple) -> tuple[list[dict], np.ndarray]:
    # signature changes when you retrain or edit a knowledge file, which rebuilds the index
    chunks = _knowledge_chunks() + _dataset_chunks(dataset)
    return chunks, _embed([c["text"] for c in chunks])


def retrieve(dataset: str, question: str, k: int = 4) -> list[dict]:
    read_json(dataset, "results.json")  # also validates the dataset name
    signature = (
        (ART / dataset / "results.json").stat().st_mtime_ns,
        tuple((p.name, p.stat().st_mtime_ns) for p in sorted(KNOWLEDGE_DIR.glob("*.md"))),
    )
    chunks, vectors = _build_index(dataset, signature)
    scores = vectors @ _embed([question])[0]
    return [chunks[i] for i in np.argsort(-scores)[:k]]


def stream_answer(messages: list[dict], context_chunks: list[dict]) -> Iterator[str]:
    s = get_settings()
    context = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(context_chunks))
    payload = {
        "model": s.chat_model,
        "stream": True,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}, *messages[-8:]],
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    try:
        with httpx.stream("POST", f"{s.ollama_url}/api/chat", json=payload,
                          timeout=httpx.Timeout(300.0, connect=10.0)) as response:
            if response.status_code != 200:
                yield f"[The assistant could not answer: Ollama returned {response.status_code}. Is '{s.chat_model}' installed?]"
                return
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                piece = data.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if data.get("done"):
                    break
    except httpx.HTTPError:
        yield "[The assistant lost its connection to Ollama.]"
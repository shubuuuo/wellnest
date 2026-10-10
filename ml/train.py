# """Train every model, evaluate it, and write the files the API and UI use.

# Run from the repo root with the venv active:   python ml/train.py
# """
# import json
# import time
# import warnings
# from pathlib import Path
# import argparse

# import joblib
# import numpy as np
# import pandas as pd
# from sklearn.base import clone
# from sklearn.compose import ColumnTransformer
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.impute import SimpleImputer
# from sklearn.linear_model import SGDClassifier
# from sklearn.metrics import (
#     accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
# )
# from sklearn.model_selection import train_test_split
# from sklearn.naive_bayes import GaussianNB
# from sklearn.neural_network import MLPClassifier
# from sklearn.pipeline import make_pipeline
# from sklearn.preprocessing import OneHotEncoder, StandardScaler
# from sklearn.svm import SVC

# warnings.filterwarnings("ignore")  

# from dataset_configs import DATASETS

# parser = argparse.ArgumentParser()
# parser.add_argument("dataset", choices=list(DATASETS), help="which dataset to train")
# ARGS = parser.parse_args()
# CFG = DATASETS[ARGS.dataset]

# CSV_PATH = Path(__file__).parent / "data" / CFG["csv"]
# TARGET = CFG["target"]
# DROP_COLS = CFG["drop_cols"]
# POSITIVE_VALUES = CFG["positive_values"]
# N_ROWS = CFG["n_rows"]

# SEED = 42
# OUT = Path(__file__).parent / "artifacts" / ARGS.dataset              



# def slug(name: str) -> str:
#     return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


# def load_data() -> tuple[pd.DataFrame, pd.Series]:
#     df = pd.read_csv(CSV_PATH)
#     print(f"Loaded {len(df):,} rows and {df.shape[1]} columns")
#     df = df.drop(columns=DROP_COLS, errors="ignore").drop_duplicates()
#     if TARGET not in df.columns:
#         raise SystemExit(f"TARGET '{TARGET}' is not a column. Columns are: {list(df.columns)}")

#     # id-like columns: integer or text columns where every value is different
#     id_like = [
#         c for c in df.columns
#         if c != TARGET and df[c].nunique() == len(df)
#         and (df[c].dtype == object or pd.api.types.is_integer_dtype(df[c]))
#     ]
#     if id_like:
#         print("Dropping id-like columns:", id_like)
#         df = df.drop(columns=id_like)

#     df = df.dropna(subset=[TARGET])
#     if len(df) > N_ROWS:
#         df = df.sample(n=N_ROWS, random_state=SEED)
#     df = df.reset_index(drop=True)

#     y = df[TARGET].astype(str).str.strip().str.lower().isin(POSITIVE_VALUES).astype(int)
#     X = df.drop(columns=[TARGET])
#     for c in X.columns:  # text and True/False columns become plain strings
#         if pd.api.types.is_bool_dtype(X[c]) or not pd.api.types.is_numeric_dtype(X[c]):
#             X[c] = X[c].astype(str)

#     print(f"Using {len(X):,} rows. Cancer cases: {int(y.sum()):,} ({y.mean():.1%})")
#     if y.nunique() < 2:
#         raise SystemExit("Only one class found. Fix TARGET / POSITIVE_VALUES at the top of train.py")
#     return X, y


# def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
#     return ColumnTransformer([
#         ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
#         ("cat", make_pipeline(
#             SimpleImputer(strategy="most_frequent"),
#             OneHotEncoder(handle_unknown="ignore", sparse_output=False),
#         ), categorical),
#     ])


# def make_models(cw: dict) -> dict:
#     """name -> (learning mode, untrained model)"""
#     return {
#         # ONLINE: these can keep learning with partial_fit
#         "SGD Logistic Regression": ("online", SGDClassifier(loss="log_loss", class_weight=cw, random_state=SEED)),
#         "SGD Linear SVM": ("online", SGDClassifier(loss="modified_huber", class_weight=cw, random_state=SEED)),
#         "Gaussian Naive Bayes": ("online", GaussianNB()),
#         "Neural Network (MLP)": ("online", MLPClassifier(hidden_layer_sizes=(32,), random_state=SEED)),
#         # BATCH ONLY: these must be retrained from scratch on all the data
#         "Random Forest": ("batch", RandomForestClassifier(
#             n_estimators=150, max_depth=14, min_samples_leaf=3, class_weight=cw, n_jobs=-1, random_state=SEED)),
#         "SVM (RBF kernel)": ("batch", SVC(kernel="rbf", class_weight=cw, random_state=SEED)),
#     }


# def scores(model, X):
#     if hasattr(model, "predict_proba"):
#         return model.predict_proba(X)[:, 1]
#     return model.decision_function(X)


# def evaluate(model, X, y) -> dict:
#     pred = model.predict(X)
#     tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
#     return {
#         "accuracy": round(float(accuracy_score(y, pred)), 4),
#         "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
#         "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
#         "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
#         "roc_auc": round(float(roc_auc_score(y, scores(model, X))), 4),
#         "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
#     }


# def build_summary(X: pd.DataFrame, y: pd.Series, numeric: list[str], categorical: list[str]) -> dict:
#     out = {
#         "rows": int(len(X)), "columns": int(X.shape[1]), "target": TARGET,
#         "positive_rate": round(float(y.mean()), 4),
#         "class_counts": {"no_cancer": int((y == 0).sum()), "cancer": int((y == 1).sum())},
#         "numeric": [], "categorical": [],
#     }
#     for c in numeric:
#         values = X[c].dropna().to_numpy()
#         if len(values) == 0:
#             continue
#         edges = np.histogram_bin_edges(values, bins=15)
#         neg, _ = np.histogram(X.loc[y == 0, c].dropna(), bins=edges)
#         pos, _ = np.histogram(X.loc[y == 1, c].dropna(), bins=edges)
#         out["numeric"].append({
#             "name": c, "edges": [round(float(e), 3) for e in edges],
#             "no_cancer": neg.tolist(), "cancer": pos.tolist(),
#         })
#     for c in categorical:
#         table = pd.crosstab(X[c], y).reindex(columns=[0, 1], fill_value=0)
#         table = table.loc[table.sum(axis=1).sort_values(ascending=False).index].head(12)
#         out["categorical"].append({
#             "name": c, "categories": [str(i) for i in table.index],
#             "no_cancer": table[0].tolist(), "cancer": table[1].tolist(),
#         })
#     return out


# def build_schema(X: pd.DataFrame, numeric: list[str], categorical: list[str]) -> list[dict]:
#     fields = []
#     for c in numeric:
#         fields.append({"name": c, "kind": "number", "min": round(float(X[c].min()), 3),
#                        "max": round(float(X[c].max()), 3), "default": round(float(X[c].median()), 3)})
#     for c in categorical:
#         options = [str(v) for v in X[c].value_counts().index]
#         fields.append({"name": c, "kind": "category", "options": options, "default": options[0]})
#     return fields


# def main() -> None:
#     OUT.mkdir(parents=True, exist_ok=True)
#     X, y = load_data()
#     numeric = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
#     categorical = [c for c in X.columns if c not in numeric]
#     print(f"{len(numeric)} number columns, {len(categorical)} text columns")

#     # 20% test. The other 80% is split again: a small BASE (the starting point of the
#     # online demo) and a large STREAM (the rows that arrive later, one chunk at a time).
#     X_all, X_test, y_all, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=SEED)
#     X_base, X_stream, y_base, y_stream = train_test_split(
#         X_all, y_all, train_size=0.125, stratify=y_all, random_state=SEED)

#     pre = build_preprocessor(numeric, categorical).fit(X_base)  # frozen: learned from BASE only
#     Xa, Xb, Xs, Xt = (pre.transform(f).astype(np.float32) for f in (X_all, X_base, X_stream, X_test))
#     ya, yb, ys, yt = (s.to_numpy() for s in (y_all, y_base, y_stream, y_test))
#     print(f"train {len(ya):,} (base {len(yb):,} + stream {len(ys):,}) | test {len(yt):,}")

#     neg, pos = int((yb == 0).sum()), int((yb == 1).sum())
#     cw = {0: 1.0, 1: round(neg / max(pos, 1), 2)}

#     rows = []
#     for name, (mode, model) in make_models(cw).items():
#         print(f"Training {name} ({mode}) ...", flush=True)
#         t0 = time.time()
#         final = clone(model).fit(Xa, ya)           # learned from ALL training rows
#         seconds = round(time.time() - t0, 1)
#         warm = clone(model).fit(Xb, yb)            # learned from the small BASE only
#         entry = {
#             "name": name, "mode": mode, "fit_seconds": seconds,
#             "has_proba": hasattr(final, "predict_proba"),
#             "final": evaluate(final, Xt, yt), "warm": evaluate(warm, Xt, yt),
#             "file": f"final_{slug(name)}.joblib", "warm_file": None,
#         }
#         joblib.dump(final, OUT / entry["file"])
#         if mode == "online":
#             entry["warm_file"] = f"warm_{slug(name)}.joblib"
#             joblib.dump(warm, OUT / entry["warm_file"])
#         rows.append(entry)
#         f = entry["final"]
#         print(f"   accuracy {f['accuracy']:.3f} | recall {f['recall']:.3f} | f1 {f['f1']:.3f} | {seconds}s")

#     usable = [r for r in rows if r["has_proba"]]  # the Predict tab needs probabilities
#     best = max(usable, key=lambda r: (r["final"]["f1"], r["final"]["recall"]))

#     results = {
#         "rows_total": int(len(X)), "base_rows": int(len(yb)), "stream_rows": int(len(ys)),
#         "test_rows": int(len(yt)), "baseline_accuracy": round(float(max(yt.mean(), 1 - yt.mean())), 4),
#         "best_model": best["name"], "models": rows,
#     }
#     (OUT / "results.json").write_text(json.dumps(results, indent=2))
#     (OUT / "dataset_summary.json").write_text(json.dumps(build_summary(X, y, numeric, categorical)))
#     (OUT / "feature_schema.json").write_text(json.dumps(build_schema(X, numeric, categorical)))
#     (OUT / "columns.json").write_text(json.dumps(list(X.columns)))
#     joblib.dump(pre, OUT / "preprocessor.joblib")
#     np.savez_compressed(OUT / "stream.npz", X_stream=Xs, y_stream=ys, X_test=Xt, y_test=yt)
#     (OUT / "meta.json").write_text(json.dumps({"id": ARGS.dataset, "label": CFG["label"], "target": TARGET}))

#     print(f"\nBest model for the Predict tab: {best['name']}")
#     print(f"Always guessing the majority class scores {results['baseline_accuracy']:.1%} accuracy.")
#     print(f"Files written to {OUT}")


# if __name__ == "__main__":
#     main()

"""Train every model, evaluate it, and write the files the API and UI use.

Run from the repo root with the venv active:   python ml/train.py lung
"""
import argparse
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from dataset_configs import DATASETS
from model_catalog import evaluate, make_models, param_info, roc_points

warnings.filterwarnings("ignore")  # hides noisy convergence warnings

parser = argparse.ArgumentParser()
parser.add_argument("dataset", choices=list(DATASETS), help="which dataset to train")
ARGS = parser.parse_args()
CFG = DATASETS[ARGS.dataset]

CSV_PATH = Path(__file__).parent / "data" / CFG["csv"]
TARGET = CFG["target"]
DROP_COLS = CFG["drop_cols"]
POSITIVE_VALUES = CFG["positive_values"]
N_ROWS = CFG["n_rows"]

SEED = 42
OUT = Path(__file__).parent / "artifacts" / ARGS.dataset


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df):,} rows and {df.shape[1]} columns")
    df = df.drop(columns=DROP_COLS, errors="ignore").drop_duplicates()
    if TARGET not in df.columns:
        raise SystemExit(f"TARGET '{TARGET}' is not a column. Columns are: {list(df.columns)}")

    id_like = [
        c for c in df.columns
        if c != TARGET and df[c].nunique() == len(df)
        and (df[c].dtype == object or pd.api.types.is_integer_dtype(df[c]))
    ]
    if id_like:
        print("Dropping id-like columns:", id_like)
        df = df.drop(columns=id_like)

    df = df.dropna(subset=[TARGET])
    if len(df) > N_ROWS:
        df = df.sample(n=N_ROWS, random_state=SEED)
    df = df.reset_index(drop=True)

    y = df[TARGET].astype(str).str.strip().str.lower().isin(POSITIVE_VALUES).astype(int)
    X = df.drop(columns=[TARGET])
    for c in X.columns:
        if pd.api.types.is_bool_dtype(X[c]) or not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype(str)

    print(f"Using {len(X):,} rows. Cancer cases: {int(y.sum()):,} ({y.mean():.1%})")
    if y.nunique() < 2:
        raise SystemExit("Only one class found. Fix target / positive_values in dataset_configs.py")
    return X, y


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        ("cat", make_pipeline(
            SimpleImputer(strategy="most_frequent"),
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        ), categorical),
    ])


def build_summary(X: pd.DataFrame, y: pd.Series, numeric: list[str], categorical: list[str]) -> dict:
    out = {
        "rows": int(len(X)), "columns": int(X.shape[1]), "target": TARGET,
        "positive_rate": round(float(y.mean()), 4),
        "class_counts": {"no_cancer": int((y == 0).sum()), "cancer": int((y == 1).sum())},
        "numeric": [], "categorical": [],
    }
    for c in numeric:
        values = X[c].dropna().to_numpy()
        if len(values) == 0:
            continue
        edges = np.histogram_bin_edges(values, bins=15)
        neg, _ = np.histogram(X.loc[y == 0, c].dropna(), bins=edges)
        pos, _ = np.histogram(X.loc[y == 1, c].dropna(), bins=edges)
        out["numeric"].append({
            "name": c, "edges": [round(float(e), 3) for e in edges],
            "no_cancer": neg.tolist(), "cancer": pos.tolist(),
        })
    for c in categorical:
        table = pd.crosstab(X[c], y).reindex(columns=[0, 1], fill_value=0)
        table = table.loc[table.sum(axis=1).sort_values(ascending=False).index].head(12)
        out["categorical"].append({
            "name": c, "categories": [str(i) for i in table.index],
            "no_cancer": table[0].tolist(), "cancer": table[1].tolist(),
        })
    return out


def build_schema(X: pd.DataFrame, numeric: list[str], categorical: list[str]) -> list[dict]:
    fields = []
    for c in numeric:
        fields.append({"name": c, "kind": "number", "min": round(float(X[c].min()), 3),
                       "max": round(float(X[c].max()), 3), "default": round(float(X[c].median()), 3)})
    for c in categorical:
        options = [str(v) for v in X[c].value_counts().index]
        fields.append({"name": c, "kind": "category", "options": options, "default": options[0]})
    return fields


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    X, y = load_data()
    numeric = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical = [c for c in X.columns if c not in numeric]
    print(f"{len(numeric)} number columns, {len(categorical)} text columns")

    # 20% test. The other 80% is split again: a small BASE (the starting point of the
    # online demo) and a large STREAM (the rows that arrive later, one chunk at a time).
    X_all, X_test, y_all, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=SEED)
    X_base, X_stream, y_base, y_stream = train_test_split(
        X_all, y_all, train_size=0.125, stratify=y_all, random_state=SEED)

    pre = build_preprocessor(numeric, categorical).fit(X_base)  # frozen: learned from BASE only
    Xa, Xb, Xs, Xt = (pre.transform(f).astype(np.float32) for f in (X_all, X_base, X_stream, X_test))
    ya, yb, ys, yt = (s.to_numpy() for s in (y_all, y_base, y_stream, y_test))
    print(f"train {len(ya):,} (base {len(yb):,} + stream {len(ys):,}) | test {len(yt):,}")

    neg, pos = int((yb == 0).sum()), int((yb == 1).sum())
    cw = {0: 1.0, 1: round(neg / max(pos, 1), 2)}

    rows = []
    for name, (mode, model) in make_models(cw).items():
        print(f"Training {name} ({mode}) ...", flush=True)
        t0 = time.time()
        final = clone(model).fit(Xa, ya)           # learned from ALL training rows
        seconds = round(time.time() - t0, 1)
        warm = clone(model).fit(Xb, yb)            # learned from the small BASE only
        entry = {
            "name": name, "mode": mode, "fit_seconds": seconds,
            "has_proba": hasattr(final, "predict_proba"),
            "final": evaluate(final, Xt, yt), "warm": evaluate(warm, Xt, yt),
            "roc": roc_points(final, Xt, yt), "param": param_info(name),
            "file": f"final_{slug(name)}.joblib", "warm_file": None,
        }
        joblib.dump(final, OUT / entry["file"])
        if mode == "online":
            entry["warm_file"] = f"warm_{slug(name)}.joblib"
            joblib.dump(warm, OUT / entry["warm_file"])
        rows.append(entry)
        f = entry["final"]
        print(f"   accuracy {f['accuracy']:.3f} | recall {f['recall']:.3f} | f1 {f['f1']:.3f} | {seconds}s")

    usable = [r for r in rows if r["has_proba"]]  # the Predict tab needs probabilities
    best = max(usable, key=lambda r: (r["final"]["f1"], r["final"]["recall"]))

    results = {
        "rows_total": int(len(X)), "base_rows": int(len(yb)), "stream_rows": int(len(ys)),
        "test_rows": int(len(yt)), "baseline_accuracy": round(float(max(yt.mean(), 1 - yt.mean())), 4),
        "best_model": best["name"], "class_weight": cw, "models": rows,
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    (OUT / "dataset_summary.json").write_text(json.dumps(build_summary(X, y, numeric, categorical)))
    (OUT / "feature_schema.json").write_text(json.dumps(build_schema(X, numeric, categorical)))
    (OUT / "columns.json").write_text(json.dumps(list(X.columns)))
    (OUT / "meta.json").write_text(json.dumps({"id": ARGS.dataset, "label": CFG["label"], "target": TARGET}))
    joblib.dump(pre, OUT / "preprocessor.joblib")
    np.savez_compressed(OUT / "stream.npz", X_stream=Xs, y_stream=ys, X_test=Xt, y_test=yt,
                        X_train=Xa, y_train=ya)  # X_train/y_train power the retrain buttons

    print(f"\nBest model for the Predict tab: {best['name']}")
    print(f"Always guessing the majority class scores {results['baseline_accuracy']:.1%} accuracy.")
    print(f"Files written to {OUT}")


if __name__ == "__main__":
    main()
"""Model definitions shared by train.py and the API's retrain endpoint."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score, roc_curve,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

SEED = 42

# One tunable setting per model. The UI builds its input box from this.
SPECS = {
    "SGD Logistic Regression": {"mode": "online", "param": "alpha", "label": "alpha (regularization)",
                                "default": 0.0001, "min": 0.000001, "max": 0.1, "int": False},
    "SGD Linear SVM": {"mode": "online", "param": "alpha", "label": "alpha (regularization)",
                       "default": 0.0001, "min": 0.000001, "max": 0.1, "int": False},
    "Gaussian Naive Bayes": {"mode": "online", "param": "var_smoothing", "label": "var_smoothing",
                             "default": 1e-9, "min": 1e-12, "max": 0.001, "int": False},
    "Neural Network (MLP)": {"mode": "online", "param": "hidden_neurons", "label": "hidden neurons",
                             "default": 32, "min": 4, "max": 128, "int": True},
    "Random Forest": {"mode": "batch", "param": "max_depth", "label": "tree depth",
                      "default": 14, "min": 3, "max": 30, "int": True},
    "SVM (RBF kernel)": {"mode": "batch", "param": "C", "label": "C (penalty)",
                         "default": 1.0, "min": 0.1, "max": 20.0, "int": False},
}


def make_model(name: str, cw: dict, value: float | None = None):
    spec = SPECS[name]
    v = spec["default"] if value is None else value
    if spec["int"]:
        v = int(v)
    if name == "SGD Logistic Regression":
        return SGDClassifier(loss="log_loss", alpha=v, class_weight=cw, random_state=SEED)
    if name == "SGD Linear SVM":
        return SGDClassifier(loss="modified_huber", alpha=v, class_weight=cw, random_state=SEED)
    if name == "Gaussian Naive Bayes":
        return GaussianNB(var_smoothing=v)
    if name == "Neural Network (MLP)":
        return MLPClassifier(hidden_layer_sizes=(v,), random_state=SEED)
    if name == "Random Forest":
        return RandomForestClassifier(n_estimators=150, max_depth=v, min_samples_leaf=3,
                                      class_weight=cw, n_jobs=-1, random_state=SEED)
    if name == "SVM (RBF kernel)":
        return SVC(kernel="rbf", C=v, class_weight=cw, random_state=SEED)
    raise KeyError(name)


def make_models(cw: dict) -> dict:
    """name -> (learning mode, untrained model with default settings)"""
    return {name: (spec["mode"], make_model(name, cw)) for name, spec in SPECS.items()}


def param_info(name: str, value: float | None = None) -> dict:
    spec = SPECS[name]
    return {"name": spec["param"], "label": spec["label"],
            "value": spec["default"] if value is None else value,
            "default": spec["default"], "min": spec["min"], "max": spec["max"], "int": spec["int"]}


def scores(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)


def evaluate(model, X, y) -> dict:
    pred = model.predict(X)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y, scores(model, X))), 4),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def roc_points(model, X, y, n: int = 40) -> dict:
    fpr, tpr, _ = roc_curve(y, scores(model, X))
    idx = np.unique(np.linspace(0, len(fpr) - 1, n).astype(int))
    return {"fpr": [round(float(fpr[i]), 4) for i in idx], "tpr": [round(float(tpr[i]), 4) for i in idx]}
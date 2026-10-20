# 🩺 WellNest — Cancer Risk Prediction

WellNest is a full-stack machine-learning web application that demonstrates how cancer-risk models are built, evaluated, used for inference, and **kept up to date via online (incremental) learning** — all in a single, dataset-agnostic interface.

Built as a college PBL (Project-Based Learning) submission for the **Data Warehousing & Mining** course.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📊 **Dataset Explorer** | Row count, class-balance pie chart, per-column histograms and statistics |
| 🤖 **Model Comparison** | Six algorithms benchmarked side-by-side — accuracy, precision, recall, F1, ROC-AUC, confusion matrix |
| 🔮 **Risk Prediction** | Auto-generated patient form → probability, risk band (Low / Moderate / High) and best-model name |
| 🔄 **Online Learning Demo** | Live chart showing incremental models improving as "new patients arrive" in chunks |
| ➕ **Plug-in Datasets** | Add a new CSV via one config entry + one training command — zero UI changes needed |

---

## 🏗️ Architecture

```
ml/train.py  ──writes──►  ml/artifacts/<dataset>/*  ◄──reads──  FastAPI  ◄──HTTP──  Next.js UI
 (offline)                 (JSON, joblib, npz)                   (services/api)      (apps/web)
```

Three decoupled layers talk through files and HTTP:

1. **ML (offline, Python)** — reads a CSV, preprocesses, trains all six models, evaluates them on a frozen test set, and writes every artifact the API needs.
2. **API (FastAPI)** — serves artifacts, runs predictions, and streams the online-learning replay via SSE.
3. **Web (Next.js)** — renders five tabs from API responses; no column names or model names are hard-coded.

---

## 🗂️ Repository Layout

```
tinywellnest/
├── apps/web/                   # Next.js 16 + Tailwind CSS + Recharts
│   └── src/
│       ├── app/page.tsx        # Header, dataset dropdown, five tabs
│       ├── components/         # DatasetTab · ModelsTab · PredictTab · OnlineTab · NotesTab
│       └── lib/                # api.ts · types.ts · useApi hook
├── services/api/               # FastAPI 0.2.0 backend
│   └── app/
│       ├── main.py             # App factory, CORS, lifespan, /api/v1 prefix
│       ├── core/               # config.py (pydantic-settings) · errors.py
│       ├── routers/            # health · dataset · models · predict · learning
│       └── services/store.py  # Artifact cache (refresh-on-mtime)
├── ml/
│   ├── data/                   # CSV datasets (git-ignored)
│   ├── dataset_configs.py      # One entry per supported dataset
│   ├── model_catalog.py        # Six model definitions + evaluation helpers
│   ├── train.py                # Offline training script
│   └── artifacts/<dataset>/   # Generated JSON, .joblib and .npz files
├── docs/                       # Design docs, prompts, PDF risk reports
└── research/                   # PBL report and research paper (.docx)
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **ML** | Python 3.12, pandas, NumPy, scikit-learn, joblib |
| **API** | FastAPI, Uvicorn, pydantic-settings, SQLAlchemy, Alembic, ReportLab, PyJWT, Argon2 |
| **Web** | Next.js 16 (App Router, TypeScript), React 19, Tailwind CSS v4, Recharts, pnpm |
| **Testing** | pytest, httpx |

---

## 🤖 Models

Six classifiers are trained per dataset:

| Model | Learning Mode | Supports `partial_fit` |
|---|---|---|
| SGD Logistic Regression | **Online** | ✅ |
| SGD Linear SVM | **Online** | ✅ |
| Gaussian Naive Bayes | **Online** | ✅ |
| Neural Network (MLP) | **Online** | ✅ |
| Random Forest | Batch | ❌ |
| SVM (RBF kernel) | Batch | ❌ |

**Online models** update incrementally with each chunk of arriving patients (`partial_fit`), never re-reading old data.  
**Batch-only models** must be retrained from scratch; the UI shows their "small-start" vs "after full retrain" comparison so the trade-off is immediately visible.

---

## 📈 Sample Results (Breast Cancer — Wisconsin, 569 rows)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Neural Network (MLP) ⭐ | 98.25% | 100% | 95.24% | 97.56% | 99.57% |
| SVM (RBF kernel) | 97.37% | 97.56% | 95.24% | 96.39% | 99.57% |
| Random Forest | 96.49% | 97.50% | 92.86% | 95.12% | 99.57% |
| SGD Logistic Regression | 95.61% | 93.02% | 95.24% | 94.12% | 98.02% |
| SGD Linear SVM | 93.86% | 88.89% | 95.24% | 91.95% | 94.15% |
| Gaussian Naive Bayes | 92.11% | 92.31% | 85.71% | 88.89% | 98.91% |

> Recall is the primary metric for cancer screening — missing a real case is more harmful than a false alarm.

---

## 🌐 Supported Datasets

| Dataset | Rows | Target | Source |
|---|---|---|---|
| Lung Cancer Risk | ~30 000 | `lung_cancer` (Yes/No) | Kaggle |
| Breast Cancer (Wisconsin) | 569 | Malignant/Benign | Kaggle / scikit-learn |
| Prostate Cancer | — | Malignant/Benign | Kaggle |
| Thyroid Cancer Risk | — | Cancer risk | Kaggle |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ and pnpm
- PostgreSQL *(optional — only needed for auth/user features)*

### 1 · Set up the Python environment

```bash
cd services/api
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2 · Train the models

```bash
# From the repo root (with the .venv active)
python ml/train.py lung
python ml/train.py breast
python ml/train.py prostate
python ml/train.py thyroid
```

### 3 · Start the API

```bash
cd services/api
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/api/v1/health
```

### 4 · Start the web app

```bash
cd apps/web
pnpm install
pnpm dev
# → http://localhost:3000
```

### 5 · Run tests

```bash
cd services/api
pytest
```

---

## 🔌 API Reference

Base path: `/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check → `{"status":"ok"}` |
| `GET` | `/dataset` | List trained datasets (dropdown source) |
| `GET` | `/dataset/summary?dataset=<id>` | Row count, class balance, histograms |
| `GET` | `/models/results?dataset=<id>` | All model metrics + best model |
| `GET` | `/predict/schema?dataset=<id>` | Auto-generated form definition |
| `POST` | `/predict?dataset=<id>` | `{"values":{...}}` → probability, label, risk band |
| `GET` | `/learning/stream?dataset=<id>` | SSE online-learning replay |

**Risk bands:** `< 0.30` → Low · `0.30–0.70` → Moderate · `≥ 0.70` → High

---

## ➕ Adding a New Dataset

1. Drop the CSV into `ml/data/`
2. Inspect it: `python ml/inspect_data.py <file.csv>`
3. Add one entry to [`ml/dataset_configs.py`](ml/dataset_configs.py)
4. Train: `python ml/train.py <your-id>`
5. Refresh the browser — the dropdown updates automatically, no restart needed.

---

## ⚠️ Limitations

- **Educational demo only** — not clinically validated or approved as a medical device.
- The online-learning stream replays *known* historical labels, not live clinical data.
- One binary (yes/no) target per dataset — multi-class targets need additional code.
- No user accounts or persistent database in the base version.
- Public Kaggle datasets may be synthetic; reported scores do not reflect real-world performance.

---

## 🔭 Future Work

- User accounts, consent management, and a prediction history database
- Simulated or real clinician feedback loop feeding a verified training pool
- Guard-checked online updates (accept a new model only if recall does not drop) with snapshot + rollback
- Feature-contribution explanations (SHAP) per prediction
- Multi-class targets and image-based cancer detection

---

## 📄 License

This project is an academic submission. The code is available for educational reference.  
**Do not use this software for clinical decision-making.**

---

<p align="center">Made with ❤️ for the Data Warehousing &amp; Mining PBL — 2025–26</p>

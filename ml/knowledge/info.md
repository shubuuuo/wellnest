# WellNest : Cancer Risk Model Training and Online Learning Demo

## 1. One-paragraph summary

WellNest  is a full-stack web application that shows how a machine-learning model for cancer risk is built, compared, used and kept up to date. A user picks a dataset (lung cancer risk or breast cancer or any other dataset), and the app shows the data, trains and compares several models, gives a risk estimate for a patient's values, and, most importantly, replays "new patients arriving over time" to show how some models can learn continuously (online learning) while others must be retrained from scratch (batch learning).

## 2. Problem and motivation

- Medical prediction models are usually trained once and frozen. In reality, new verified patient outcomes keep arriving, so a model that can keep learning is attractive.
- Not every algorithm can learn incrementally. Random Forest and kernel SVM must be retrained on all data. Others (SGD-based models, Naive Bayes, small neural networks) can update with `partial_fit`.
- Goal: make this difference visible and measurable in one interface, for any yes/no cancer dataset, with no new chart or form code per dataset.

## 3. Objectives

1. Load a tabular dataset and summarise it (rows, columns, class balance, distributions).
2. Train and compare several classification models with the same preprocessing.
3. Let a user enter values and get a risk probability, risk band and disclaimer.
4. Demonstrate online learning with a live chart of model quality versus patients learned.
5. Show honestly that batch-only models cannot update incrementally, with their retrain results.
6. Make adding a new dataset a configuration change, not a coding task.

## 4. What the user sees (the interface)

A header with the title and a **Dataset dropdown** (for example "Lung cancer risk", "Breast cancer (Wisconsin)"). Switching the dropdown reloads every tab. Five tabs:

| Tab | Purpose |
|---|---|
| **Dataset** | Summary of the chosen dataset: size, target column, class balance, per-column histograms/statistics. |
| **Models** | Table and charts comparing all trained models (metrics, which is "best", learning mode online/batch). |
| **Predict** | A form built automatically from the dataset's columns. Submit values to get a probability, label, risk band and the best model's name, plus a disclaimer. |
| **Online Learning** | Press Start to stream held-back patients in chunks; a line chart adds one dot per model per chunk. A table below shows Random Forest/SVM "small start" versus "after batch retrain". Chunk size and delay are adjustable. |
| **Notes** | Static explanation text. |

The UI builds itself from files written by training, so it contains no hard-coded column names.

## 5. System architecture

Three parts, connected by files and HTTP:

```
ml/train.py  ──writes──►  ml/artifacts/<dataset>/*  ◄──reads──  FastAPI  ◄──HTTP──  Next.js UI
 (offline)                 (JSON, joblib, npz)                   (services/api)      (apps/web)
```

1. **ML side (offline, Python):** reads a CSV, preprocesses, trains models, evaluates them, and writes everything the app needs into one folder per dataset.
2. **API side (FastAPI):** serves those files and runs predictions and the online-learning stream. It has no database in this version.
3. **Web side (Next.js + Tailwind + Recharts):** renders tabs and charts from API responses.

### Repository layout

```
wellnest/
├─ ml/
│  ├─ data/                      # CSV datasets (git-ignored in the full project)
│  ├─ dataset_configs.py         # one entry per dataset
│  ├─ inspect_data.py            # prints columns, types, target values
│  ├─ train.py                   # python ml/train.py <dataset>
│  └─ artifacts/<dataset>/       # outputs for each dataset
├─ services/api/
│  ├─ app/
│  │  ├─ main.py                 # app factory, CORS, error handlers, /api/v1 prefix
│  │  ├─ core/ (config.py, errors.py)
│  │  ├─ routers/ (health, dataset, models, predict, learning)
│  │  └─ services/store.py       # loads and caches artifacts
│  ├─ tests/                     # pytest (health tests etc.)
│  ├─ pytest.ini
│  └─ requirements.txt
└─ apps/web/src/
   ├─ app/page.tsx               # header, dropdown, tabs
   ├─ components/                # DatasetTab, ModelsTab, PredictTab, OnlineTab, NotesTab
   └─ lib/                       # api.ts (fetch wrapper), types.ts, useApi hook
```

### Technology stack

| Layer | Technology |
|---|---|
| ML | Python, pandas, numpy, scikit-learn, joblib |
| API | FastAPI, Uvicorn, pydantic-settings, pytest, httpx |
| Web | Next.js (App Router, TypeScript), Tailwind CSS, Recharts, pnpm |

## 6. Datasets

Each dataset is one entry in `ml/dataset_configs.py`:

| Setting | Meaning |
|---|---|
| `label` | Name shown in the dropdown |
| `csv` | File inside `ml/data/` |
| `target` | The yes/no column to predict |
| `drop_cols` | Columns to ignore (ids, leakage) |
| `positive_values` | Raw values that mean "has cancer" |
| `n_rows` | Row cap for training |

- **Lung cancer risk:** `lung_cancer_risk.csv`, target `lung_cancer`, about 30,000 rows with a mix of numeric and yes/no/categorical risk-factor columns. [confirm column list from the Dataset tab]
- **Breast cancer (Wisconsin):** from scikit-learn, 569 rows, 30 numeric measurements. In that copy 0 means malignant, so `positive_values` is `{"0"}` to make "1 = cancer" consistent. Only 569 rows, so it is a demo second dataset.
- **Limits:** needs one yes/no target (multi-class such as stage 1-4 needs extra code). Very wide datasets (40+ columns) produce 40+ histograms.

## 7. Machine-learning pipeline (`train.py`)

1. **Load and clean:** read the CSV, drop `drop_cols`, convert the target to 0/1 using `positive_values`.
2. **Split** (for the 30,000-row lung data):
   - 20% **frozen test set** (about 6,000), never trained on, used only to score.
   - 80% **training pool** (about 24,000), further split into a **starter set** (12.5%, about 3,000) and a **stream** (about 21,000) held back to imitate new patients arriving later.
3. **Preprocess:** a scikit-learn `ColumnTransformer` pipeline (missing-value imputation with `SimpleImputer`, plus scaling/encoding of columns) fitted only on training data, then frozen. Saved as `preprocessor.joblib`. [confirm scaler/encoder choices]
4. **Train models** (about [N] total):
   - **Online-capable (4 models):** learn from the starter set, then update with `partial_fit`. A warm copy is saved so each demo run starts from the same small base. [list the 4 names from the Models tab; typically SGD logistic regression, SGD linear SVM, Gaussian Naive Bayes, small MLP]
   - **Batch-only:** Random Forest and SVM. They cannot learn incrementally; the app shows "small start" and "after batch retrain" scores instead.
5. **Evaluate** on the frozen test set. [list metrics from the Models tab, e.g. recall, precision, F1, ROC-AUC, accuracy]
6. **Choose the best model** (`best_model` in `results.json`) used by the Predict tab.
7. **Write artifacts** to `ml/artifacts/<dataset>/`.

### Files written per dataset

| File | Used for |
|---|---|
| `meta.json` | id, label, target (feeds the dropdown) |
| `dataset_summary.json` | Dataset tab |
| `results.json` | Models tab and online-learning setup (models, metrics, best model, mode online/batch, file names) |
| `feature_schema.json` | Predict form: each column's name, kind (number or category), choices, default |
| `columns.json` | Exact column order for the model |
| `preprocessor.joblib` | Frozen preprocessing |
| `<model>.joblib` (+ warm copies) | Trained models |
| `stream.npz` | Held-back patients for the replay |

## 8. Backend (FastAPI)

Base path `/api/v1`. Every data endpoint takes `?dataset=<id>`.

| Method and path | Purpose |
|---|---|
| `GET /health` | Liveness check, returns `{"status":"ok"}` |
| `GET /dataset` | Lists trained datasets (dropdown) |
| `GET /dataset/summary` | Dataset summary |
| `GET /models/results` | Models, metrics, best model |
| `GET /predict/schema` | Form definition |
| `POST /predict` | Body `{"values": {...}}`; returns `probability`, `label` (1 if probability >= 0.5), `risk_band`, `model`, `disclaimer` |
| `GET /learning/stream` | Streams the online-learning replay; parameters `chunk` (50-2000, default 250) and `delay` (0-3 s, default 0.4) |

**Risk bands:** probability below 0.30 is low, 0.30 to 0.70 is moderate, 0.70 and above is high.

**Disclaimer returned with every prediction:** "This is an estimate for education only and is not a medical diagnosis. Please consult a qualified clinician about any health concern."

**Design decisions**
- **Artifact store with automatic refresh:** `store.py` caches loaded files keyed by file modification time, so retraining refreshes data without restarting the API. Warm models are loaded fresh on every demo run so each run starts identically.
- **Unified error shape:** every error is `{code, message, details}` (examples: `UNKNOWN_DATASET`, `ARTIFACTS_MISSING`, `INVALID_VALUE`, `VALIDATION_ERROR`).
- **CORS** allows the web origin (default `http://localhost:3000`).
- **Input handling:** `/predict` fills missing fields with schema defaults, converts numbers, rejects non-numbers with a clear error, and reorders columns to the training order.
- **Config:** pydantic-settings reading `.env`, with a repo-root path helper.

## 9. Frontend

- `page.tsx` holds the active tab and the chosen dataset. It fetches the dataset list, picks the first by default, and re-keys every tab by dataset so charts and forms reset on switch. Inactive tabs are hidden, not unmounted, so the Online Learning chart keeps its state.
- Every tab takes a `dataset` prop and builds its API paths from it.
- `lib/api.ts` is one fetch wrapper that converts server errors into a single error type with a friendly message (for example "We can't reach the server. Is the API running?").
- Charts use Recharts. Styling uses Tailwind with a small token palette (brand, ink, muted, line, surface).

## 10. Online learning explained from scratch

Think of a student who studied from a small set of notes, then receives a few new pages at a time and updates their knowledge after each batch.

1. Before Start, the 4 online models know only the starter set (about 3,000 patients).
2. About 21,000 other patients are held back as the stream.
3. **Each step:** the server sends one chunk (default 250 patients). Each model learns only from that chunk using `partial_fit`, adjusting its numbers slightly without re-reading old data.
4. **Exam:** right after learning, each model is scored on the frozen test set it has never trained on.
5. **One dot per model** is added to the chart, then after a short pause (default 0.4 s, only so you can watch) the next chunk is sent.

Chart axes: x = patients learned so far, y = test score.

How to read it: a rising line means the model improves with more data; a flat line means nothing more to gain; small wiggles are normal; the final value should land near that model's score in the Models tab.

**Batch-only models (Random Forest, SVM)** must discard everything and retrain on all data to use new patients. The table under the chart shows their "small start" and "after batch retrain" scores. This is the key contrast: online models reach similar quality without ever retraining from scratch.

**Important honesty note:** this is a replay. The "arriving patients" are existing rows whose answers are already known. In a real system outcomes would arrive only when confirmed. If lines are flat from the start, the starter set was already large enough or the signal is weak; reducing `train_size` from 0.125 to 0.03 (about 750 starter patients) makes learning more visible.

## 11. Results

[Fill from the running app: for each dataset, a table of model, learning mode (online/batch), recall, precision, F1, ROC-AUC, accuracy; the best model; and a screenshot of the online-learning chart showing start versus end score for each online model. Add the batch retrain comparison for Random Forest and SVM.]

## 12. Adding a new dataset (extensibility)

1. Put the CSV in `ml/data/`.
2. Run `python ml/inspect_data.py <file.csv>` to see columns, target and values.
3. Add one entry to `ml/dataset_configs.py`.
4. Run `python ml/train.py <id>`.
5. Refresh the browser. The dropdown shows it, with no restart and no UI code changes.

## 13. How to run it

```bash
# 1. API environment (once)
cd services/api
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash
pip install -r requirements.txt

# 2. Train (repo root, same venv active)
cd ../..
python ml/train.py lung
python ml/train.py breast

# 3. Start API (from services/api)
cd services/api
uvicorn app.main:app --reload --port 8000

# 4. Start web (new terminal)
cd apps/web
pnpm install
pnpm dev                              # http://localhost:3000

# 5. Tests
cd services/api && pytest
```

## 14. Testing

- `pytest` (with `httpx`) in `services/api/tests`, starting with health-endpoint tests; `pytest.ini` sets `pythonpath = .`.
- Manual checks: `/api/v1/health`, `/api/v1/dataset`, then each tab for each dataset.

## 15. Problems met and lessons learned (good material for a "challenges" slide)

| Problem | Cause | Lesson |
|---|---|---|
| `SimpleImputer has no attribute '_fill_dtype'` on `/predict` | Models were trained with a different scikit-learn version than the API used (training ran outside the project virtual environment). | Pickled/joblib models are tied to library versions. Train and serve in the same environment and pin versions. |
| `No module named 'app'` | Uvicorn started from the repo root instead of `services/api`. | Run commands from the folder that contains the package. |
| Browser showed CORS errors | The real cause was server crashes (HTTP 500). Responses from the catch-all error handler sit outside the CORS middleware and lack CORS headers. | Read the server log first; browser CORS messages can hide server errors. |
| `read_json() missing argument` | One router still used the old single-dataset function signature after the multi-dataset refactor. | Search for every call site when changing a function signature. |
| Recharts "width(0) height(0)" warning | Charts mounted inside hidden (display: none) tabs. | Give chart containers a minimum size or mount charts only when visible. |
| Pasted code failed | A `...` placeholder from instructions was copied into the file. | Placeholders mean "keep your existing code" and never go into a file. |

## 16. Limitations (state these honestly)

- Educational demo only. Not a diagnostic tool and not clinically validated.
- The online-learning stream is a replay of known labels, not live clinical data.
- Online learning on real patient data is risky (noisy or wrong labels, deliberate poisoning, data drift) and is not recommended for clinical deployment.
- Lung data is a risk-factor dataset, not clinical measurements. The breast dataset has only 569 rows.
- One yes/no target only. No users, login or database in this  version. Models cached in memory per process.

## 17. Future work

- Accounts, consent and a database of predictions (as in the full WellNest design).
- Simulated or real clinician verification feeding a training pool.
- Safe online updates with guard checks (accept a new model only if recall does not drop), snapshots and one-click rollback.
- Model explanations (feature contributions) for each prediction.
- Probability calibration review and tuned risk-band cutoffs.
- More datasets, multi-class targets, image-based cancer detection.

## 18. Key terms

| Term | Meaning |
|---|---|
| Online learning | A model updates itself from small batches of new data (`partial_fit`). |
| Batch learning | A model must be retrained from scratch on all data. |
| Stream | Held-back records replayed to imitate new data arriving. |
| Frozen test set | Records used only for scoring, never trained on. |
| Starter set | The small initial training set before streaming starts. |
| Recall (sensitivity) | Share of real cancer cases the model catches. Missing a case is worse than a false alarm. |
| Precision | Share of positive predictions that were correct. |
| Artifacts | Files produced by training and read by the API. |
| Risk band | Low, moderate or high, from the predicted probability. |

## 19. Likely questions from an examiner

1. **Why can't Random Forest learn online?** It builds fixed trees from the whole dataset; adding data means rebuilding them.
2. **Why score on a frozen test set?** To measure improvement fairly on data no model has trained on.
3. **Why is recall the key metric?** A missed cancer case is more harmful than a false alarm.
4. **Why a separate stream set?** So the demo shows learning from data the model has never seen, without leaking test data.
5. **How does the UI work for any dataset?** It reads the feature schema and results written by training, so nothing is hard-coded.
6. **Is it safe for real patients?** No. It is an educational demo, and online learning has known risks listed above.
7. **Why train outside the API?** Training is slow and offline; the API only loads finished files, which keeps it fast and simple.
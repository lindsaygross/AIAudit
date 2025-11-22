# AIAudit Lite

**AIAudit Lite is a decision-support prototype that evaluates textual technical documentation of AI systems against EU AI Act risk signals and returns a prioritized remediation plan. Target users: product teams, AI-governance, and legal/compliance. The tool provides heuristic, auditable guidance — not legal advice.**

---

## Table of Contents

- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Dataset](#dataset)
- [Training Pipeline](#training-pipeline)
- [MLflow Tracking](#mlflow-tracking)
- [API & Frontend](#api--frontend)
- [Docker & Cloud Run](#docker--cloud-run)
- [Ethics & Limitations](#ethics--limitations)
- [Reproducibility Checklist](#reproducibility-checklist)

---

## Quickstart

### One-Command Start (Local)

```bash
# Clone the repo and run everything
git clone https://github.com/YOUR_ORG/AIAudit.git
cd AIAudit
chmod +x dev_start.sh
bash dev_start.sh
```

This single command will:
1. Create a virtual environment and install dependencies
2. Clone/pull the AIReg-Bench dataset repository
3. Build the supervised CSV from annotations
4. Train a risk classification model with MLflow logging
5. Start the FastAPI server on http://127.0.0.1:8000
6. (Optional) Run Streamlit frontend via `streamlit run app/app.py`

### Manual Steps

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build dataset (clones AIReg-Bench automatically)
python src/data/build_dataset.py

# 4. Train model
python -m src.models.train --config config.yaml

# 5. Start API
uvicorn src.api.main:app --reload

# 6. (In another terminal) Start Streamlit UI
streamlit run app/app.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AIAudit Lite                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  AIReg-Bench │───▶│ build_dataset│───▶│ Supervised   │                  │
│  │  (git clone) │    │     .py      │    │    CSV       │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   MLflow     │◀───│   train.py   │◀───│ TF-IDF +     │                  │
│  │   Tracking   │    │              │    │ LogisticReg  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Streamlit   │◀──▶│   FastAPI    │◀───│ Remediation  │                  │
│  │  Frontend    │    │   /predict   │    │  Generator   │                  │
│  └──────────────┘    │   /assess    │    │  (Templates) │                  │
│                      └──────────────┘    └──────────────┘                  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────┐    ┌──────────────┐                                      │
│  │   Docker     │───▶│  Cloud Run   │                                      │
│  │   Container  │    │  Deployment  │                                      │
│  └──────────────┘    └──────────────┘                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Dataset

### AIReg-Bench Dataset Pull

The dataset is sourced from [AIReg-Bench](https://github.com/camlsys/aireg-bench), a benchmark for evaluating AI system documentation against regulatory requirements.

**Automatic Dataset Construction:**

```bash
python src/data/build_dataset.py
```

This script:
1. Clones (or pulls) the AIReg-Bench repository to `data/raw/aireg-bench/`
2. Reads technical documents and human annotations
3. Computes median compliance scores across annotators
4. Buckets into risk labels: `high` (score ≤2), `medium` (score=3), `low` (score ≥4)
5. Saves `data/aireg_supervised.csv` with columns:
   - `doc_id`, `article`, `intended_use`, `system_type`
   - `text`, `compliance_score_median`, `risk_label`

**No cloud credentials required** — the dataset is pulled locally via git.

---

## Training Pipeline

```bash
python -m src.models.train --config config.yaml
```

**Pipeline:**
- TF-IDF Vectorizer (max_features=10000, ngram_range=(1,2))
- Logistic Regression (multi-class, balanced class weights)

**Outputs:**
- `artifacts/model.joblib` — trained sklearn pipeline
- `artifacts/label_encoder.json` — label mappings
- `artifacts/metrics.json` — accuracy, macro F1
- `artifacts/confusion_matrix.png` — visualization

---

## MLflow Tracking

When `logging.use_mlflow: true` in `config.yaml`:

```bash
# View experiments
mlflow ui
# Navigate to http://127.0.0.1:5000
```

Logged items:
- Hyperparameters (C, max_features, ngram_range)
- Metrics (accuracy, macro_f1)
- Artifacts (model, confusion matrix)
- Dataset source commit SHA

---

## API & Frontend

### FastAPI Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict` | POST | Risk classification |
| `/assess_and_remediate` | POST | Full assessment with remediation plan |

**Start the API:**
```bash
uvicorn src.api.main:app --reload --port 8000
```

### Streamlit Frontend

```bash
streamlit run app/app.py
```

Features:
- Paste AI system documentation
- One-click "Assess & Remediate"
- Risk badge with probability scores
- Article-specific remediation checklist
- "Create GitHub Issue" button for tracking

---

## Docker & Cloud Run

### Build and Run Locally

```bash
docker build -t aiaudit-lite .
docker run -p 8080:8080 aiaudit-lite
```

### Deploy to Cloud Run

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiaudit-lite

# Deploy
gcloud run deploy aiaudit-lite \
  --image gcr.io/YOUR_PROJECT_ID/aiaudit-lite \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

**Environment Variables for Cloud Run:**
- `GCS_BUCKET`: (optional) GCS bucket for data
- `MLFLOW_TRACKING_URI`: (optional) MLflow server URL

---

## Ethics & Limitations

### Important Disclaimers

1. **Not Legal Advice**: This tool provides heuristic guidance based on pattern matching and ML classification. It does not constitute legal advice and should not replace consultation with qualified legal professionals.

2. **Model Limitations**:
   - Trained on limited annotated data from AIReg-Bench
   - May not generalize to all AI system types
   - Classification confidence should not be interpreted as legal certainty

3. **Bias Considerations**:
   - Training data reflects annotator perspectives
   - Keyword-based rules may have blind spots
   - Regular auditing of model outputs recommended

4. **Intended Use**:
   - Internal compliance triage and prioritization
   - Identifying areas requiring deeper legal review
   - Tracking remediation progress

5. **Not Intended For**:
   - Final compliance certification
   - Regulatory submission without human review
   - Automated decision-making without oversight

---

## Reproducibility Checklist

| Item | Status | Notes |
|------|--------|-------|
| Dataset source documented | ✅ | AIReg-Bench via git clone |
| Random seeds fixed | ✅ | `config.yaml: random_state: 42` |
| Dependencies pinned | ✅ | `requirements.txt` |
| Training logged | ✅ | MLflow tracking |
| Model artifacts versioned | ✅ | `artifacts/` directory |
| Docker reproducible | ✅ | `Dockerfile` with fixed base image |
| One-command start | ✅ | `bash dev_start.sh` |
| Unit tests included | ✅ | `tests/` directory |
| Config externalized | ✅ | `config.yaml` |

---

## Project Structure

```
AIAudit/
├── README.md
├── requirements.txt
├── config.yaml
├── Dockerfile
├── dev_start.sh
├── .gitignore
├── artifacts/                 # Model outputs (gitignored contents)
├── data/
│   ├── raw/aireg-bench/      # Cloned dataset (gitignored)
│   └── aireg_supervised.csv  # Built supervised dataset
├── mlruns/                    # MLflow tracking (gitignored)
├── src/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── build_dataset.py
│   │   └── ingest.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py
│   │   └── predict.py
│   ├── remediation/
│   │   ├── __init__.py
│   │   ├── mapping.py
│   │   └── generator.py
│   └── api/
│       ├── __init__.py
│       ├── schemas.py
│       └── main.py
├── templates/
│   └── article_remediations.yml
├── app/
│   └── app.py
└── tests/
    ├── __init__.py
    ├── test_remediation.py
    └── test_api.py
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*Built with scikit-learn, FastAPI, Streamlit, and MLflow*

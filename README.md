# AIAudit Lite

**AIAudit Lite is a decision-support prototype that evaluates textual technical documentation of AI systems against EU AI Act risk signals and returns a prioritized remediation plan. Target users: product teams, AI-governance, and legal/compliance. The tool provides heuristic, auditable guidance — not legal advice.**

## Overview

This project implements a full-stack ML system for EU AI Act compliance assessment. It combines:
- **Machine Learning**: TF-IDF + Logistic Regression for risk classification
- **Rule-Based Engine**: Multi-article compliance evaluation (Articles 5, 6, 9, 10, 14)
- **Remediation Planning**: Automated action items based on Articles 9-15, 52, 69
- **Cloud Deployment**: FastAPI backend on Google Cloud Run, Streamlit frontend
- **MLOps**: MLflow tracking, Docker containerization, reproducible pipelines

### EU AI Act Articles Evaluated

The assessment engine (`src/scoring/risk_engine.py`) evaluates AI systems against multiple EU AI Act articles:

**Classification Articles:**
- **Article 5**: Prohibited AI practices (manipulative systems, social scoring)
- **Article 6**: High-risk AI system classification criteria

**Compliance Evaluation Articles:**
- **Article 9**: Risk management systems
- **Article 10**: Data and data governance
- **Article 14**: Human oversight requirements

**Remediation Obligations:**
Generated from Articles 9-15 (technical requirements), Article 52 (transparency), and Article 69 (codes of conduct).

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

### AIReg-Bench: EU AI Act Compliance Benchmark

**Source:** [AIReg-Bench GitHub Repository](https://github.com/camlsys/aireg-bench)
**Research Paper:** [AIReg-Bench: Benchmarking Language Models That Assess AI Regulation Compliance](https://arxiv.org/abs/2510.01474)

AIReg-Bench is a comprehensive benchmark dataset for evaluating AI system documentation against EU AI Act requirements. It contains:
- **300 synthetic documentation files** across 5 EU AI Act articles
- **Human compliance annotations** (1-5 scale) from expert evaluators
- **Multiple scenario types**: Compliance (A), Violation_1 (B), Violation_2 (C)
- **10 intended use cases**: From critical infrastructure to judicial systems
- **Coverage**: Articles 9, 10, 12, 14, 15 of the EU AI Act

### Dataset Construction

**Automatic Build Process:**

```bash
python src/data/build_dataset.py
```

This script:
1. Clones (or pulls) the AIReg-Bench repository to `data/raw/aireg-bench/`
2. Reads technical documents and human annotations from Excel
3. Computes compliance scores from annotator ratings
4. Buckets into risk labels: `high` (score ≤2), `medium` (score ≤3), `low` (score >3)
5. Saves `data/aireg_supervised.csv` with 300 labeled documents

**Output Dataset Columns:**
- `doc_id`, `article`, `scenario`, `use_case`, `system`
- `intended_use`, `text`, `compliance_score`, `risk_label`

**Cloud Storage:**
The processed dataset is also available in Google Cloud Storage for cloud deployments (see [Cloud Services](#cloud-services-used)).

---

## Training Pipeline

### Model Architecture

**Task:** Multi-class text classification (high/medium/low risk)
**Algorithm:** TF-IDF + Logistic Regression

```bash
python -m src.models.train --config config.yaml
```

**Pipeline Components:**
1. **TF-IDF Vectorizer**
   - `max_features=10000`
   - `ngram_range=(1,2)` (unigrams and bigrams)
   - Captures keyword patterns from EU AI Act language

2. **Logistic Regression Classifier**
   - Multi-class classification (one-vs-rest)
   - Balanced class weights for imbalanced data
   - L2 regularization (C=1.0)

**Training Process:**
- 80/20 train/test split (stratified)
- Random state fixed at 42 for reproducibility
- Evaluation metrics: accuracy, macro F1-score, confusion matrix

**Outputs:**
- `artifacts/model.joblib` — trained sklearn pipeline
- `artifacts/label_encoder.json` — label mappings (high/medium/low → 0/1/2)
- `artifacts/metrics.json` — accuracy, macro F1
- `artifacts/confusion_matrix.png` — visualization

**Note:** This is a baseline model for demonstration. The primary compliance logic resides in `src/scoring/risk_engine.py` which combines ML predictions with rule-based article evaluation.

---

## MLflow Tracking

### Experiment Tracking with MLflow

This project uses MLflow to track all training experiments, ensuring full reproducibility and experiment comparison.

**Configuration** (`config.yaml`):
```yaml
logging:
  use_mlflow: true
  experiment_name: aireg_risk
```

**Launch MLflow UI**:
```bash
mlflow ui
# Navigate to http://127.0.0.1:5000
```

**Logged Information:**
- **Hyperparameters**: C, max_features, ngram_range, class_weight, test_size
- **Metrics**: accuracy, macro_f1, per-class precision/recall/f1-score
- **Artifacts**: trained model, label encoder, confusion matrix, metrics JSON
- **Dataset Version**: Git commit SHA of AIReg-Bench dataset

### MLflow Screenshots

**Experiments Overview:**
![MLflow Experiments List](SCREENSHOTS/Screenshot%202025-11-22%20at%2010.29.26%20PM.png)

**Run Parameters:**
![MLflow Parameters](SCREENSHOTS/Screenshot%202025-11-22%20at%2010.29.43%20PM.png)

**Run Metrics:**
![MLflow Metrics](SCREENSHOTS/Screenshot%202025-11-22%20at%2010.29.53%20PM.png)

**Run Artifacts:**
![MLflow Artifacts](SCREENSHOTS/Screenshot%202025-11-22%20at%2010.30.11%20PM.png)

**Model Details:**
![MLflow Model Details](SCREENSHOTS/Screenshot%202025-11-22%20at%2010.31.03%20PM.png)

---

## API & Frontend

### 🌐 Live Deployment

- **API Endpoint:** https://aiaudit-api-fbohlm36ca-uc.a.run.app
- **Frontend App:** [REPLACE_WITH_STREAMLIT_URL_AFTER_DEPLOYMENT]
- **Cloud Data Storage:** Google Cloud Storage bucket (configured in deployment)

### FastAPI Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict` | POST | Risk classification |
| `/assess_and_remediate` | POST | Full assessment with remediation plan |
| `/assess_intake` | POST | Structured intake form assessment |

**Test the Live API:**
```bash
curl https://aiaudit-api-fbohlm36ca-uc.a.run.app/health
```

**Run Locally (Optional):**
```bash
uvicorn src.api.main:app --reload --port 8000
```

### Streamlit Frontend

**Use the Live App:** [REPLACE_WITH_STREAMLIT_URL_AFTER_DEPLOYMENT]

**Run Locally (Optional):**
```bash
# Set API URL to cloud endpoint
export API_URL="https://aiaudit-api-fbohlm36ca-uc.a.run.app"
streamlit run app/app1.py
```

**Features:**
- **Structured Intake Form**: Comprehensive AI system questionnaire
  - System details (name, version, team)
  - Intended use case and deployment context
  - Risk classification (intended purpose, deployment sector)
  - Data governance and human oversight configuration
  - Optional technical documentation upload

- **Real-Time Assessment**: Evaluates against multiple EU AI Act articles
  - Article 5: Prohibited practices detection
  - Article 6: High-risk classification
  - Article 9: Risk management requirements
  - Article 10: Data governance compliance
  - Article 14: Human oversight adequacy

- **Risk Scoring**: Combined ML + rule-based evaluation
  - Overall risk score (0-100%)
  - Risk category (Unacceptable/High/Limited/Minimal)
  - Key risk factors breakdown
  - Article-specific compliance scores

- **Remediation Planning**: Actionable recommendations
  - Prioritized action items based on Articles 9-15, 52, 69
  - Compliance obligations mapped to specific articles
  - Documentation gap identification
  - Implementation guidance

---

## Cloud Services Used

This project uses the following Google Cloud Platform services:

1. **Google Cloud Storage (GCS)**
   - Stores the processed dataset (`aireg_supervised.csv`)
   - Bucket: [ADD_YOUR_BUCKET_NAME]
   - Access: Public read or authenticated based on bucket policy

2. **Google Cloud Run**
   - Hosts the FastAPI backend API
   - Service: `aiaudit-api`
   - URL: https://aiaudit-api-fbohlm36ca-uc.a.run.app
   - Region: us-central1
   - Configuration: 2Gi memory, 2 CPU cores, max 10 instances

3. **Google Cloud Build**
   - Automated Docker container builds
   - Triggered by deployment script

4. **Streamlit Cloud**
   - Hosts the frontend application
   - Auto-deploys from GitHub main branch
   - URL: [REPLACE_WITH_STREAMLIT_URL_AFTER_DEPLOYMENT]

**Cost:** All services operate within free tier limits for this demo application.

---

## Docker & Cloud Deployment

### Local Development with Docker

```bash
# Build Docker image
docker build -t aiaudit-lite .

# Run container locally
docker run -p 8080:8080 aiaudit-lite

# Test the containerized API
curl http://localhost:8080/health
```

### Deploy to Google Cloud Run

**Quick Deployment:**
```bash
# Run the automated deployment script
./deploy_cloudrun.sh
```

**Manual Deployment Steps:**
```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs and set permissions
./setup_gcp_permissions.sh

# 3. Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiaudit-api
gcloud run deploy aiaudit-api \
  --image gcr.io/YOUR_PROJECT_ID/aiaudit-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

**Deployment Documentation:**
See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide including:
- GCP project setup and permissions
- Cloud Run configuration
- Streamlit Cloud deployment
- Environment variable configuration
- Troubleshooting and monitoring

---

## Ethics & Limitations

### Important Disclaimers

1. **Not Legal Advice**: This tool provides heuristic guidance based on pattern matching and ML classification. It does not constitute legal advice and should not replace consultation with qualified legal professionals specializing in EU AI Act compliance.

2. **Model Limitations**:
   - **Training Data Scope**: Trained on 300 synthetic documents from AIReg-Bench covering only 5 articles (9, 10, 12, 14, 15)
   - **Generalization**: May not generalize to all AI system types, domains, or novel use cases
   - **Confidence Calibration**: Classification probabilities should not be interpreted as legal certainty
   - **Baseline Model**: TF-IDF + Logistic Regression is intentionally simple for educational purposes, not production-grade
   - **Synthetic Data**: Training data consists of generated compliance/violation scenarios, not real-world documentation

3. **Bias and Fairness Considerations**:
   - **Annotator Bias**: Training data reflects perspectives of AIReg-Bench annotators
   - **Keyword Dependence**: Rule-based components may miss novel phrasings or domain-specific terminology
   - **Coverage Gaps**: Does not cover all 85 articles of the EU AI Act
   - **Language Limitation**: English-only; may not work for multilingual documentation
   - **Regular Auditing**: Human review of outputs is essential to catch errors and biases

4. **Technical Limitations**:
   - **No Real-Time Updates**: Does not reflect amendments or guidance updates to the EU AI Act
   - **Context Dependency**: Cannot evaluate organizational policies, processes, or implementation quality
   - **Documentation Only**: Assesses written documentation, not actual system behavior or technical implementation
   - **No Code Analysis**: Cannot evaluate source code, model architectures, or data processing pipelines

5. **Intended Use Cases**:
   - Internal compliance triage and prioritization
   - Identifying areas requiring deeper legal/technical review
   - Tracking remediation progress across teams
   - Educational tool for understanding EU AI Act requirements
   - Rapid initial assessment for portfolio management

6. **Explicitly Not Intended For**:
   - Final compliance certification or attestation
   - Regulatory submission without expert human review
   - Automated decision-making without human oversight
   - Legal defense or liability protection
   - Replacing compliance officers, legal counsel, or technical auditors

7. **Data Privacy and Security**:
   - **No Data Retention**: API does not store submitted documentation (stateless)
   - **Public Deployment**: Current deployment allows unauthenticated access (demo only)
   - **Production Requirements**: For production use, implement authentication, encryption, and audit logging
   - **Sensitive Data**: Do not submit confidential business information or personal data to public demo

8. **Ethical Considerations for Automated Compliance Tools**:
   - **Automation Bias**: Users may over-rely on automated outputs without critical evaluation
   - **False Confidence**: High confidence scores may create false sense of security
   - **Regulatory Arbitrage**: Tool should not be used to game compliance requirements
   - **Accountability**: Organizations remain fully responsible for compliance regardless of tool outputs
   - **Transparency**: Limitations and uncertainties must be clearly communicated to stakeholders

### Responsible Use Guidelines

**DO:**
- Use as a first-pass screening tool to identify potential issues
- Combine outputs with expert legal and technical review
- Document all assessments and review decisions
- Regularly validate outputs against official EU AI Act guidance
- Update assessments as regulations evolve

**DON'T:**
- Rely solely on automated outputs for compliance decisions
- Submit to regulators without comprehensive human review
- Use for systems where errors could cause harm
- Assume coverage of all regulatory requirements
- Deploy in production without proper security controls

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

## References and Resources

### Dataset and Benchmark
- **AIReg-Bench Paper**: [AIReg-Bench: Benchmarking Language Models That Assess AI Regulation Compliance](https://arxiv.org/abs/2510.01474)
- **AIReg-Bench Repository**: [https://github.com/camlsys/aireg-bench](https://github.com/camlsys/aireg-bench)
- **Authors**: Cambridge Machine Learning Systems Lab

### EU AI Act Resources
- **Official EU AI Act Text**: [EUR-Lex - Artificial Intelligence Act](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206)
- **European Commission AI Hub**: [https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)

### Technical Stack
- **Scikit-learn**: Machine learning pipeline and TF-IDF vectorization
- **FastAPI**: REST API framework
- **Streamlit**: Interactive web application framework
- **MLflow**: Experiment tracking and model versioning
- **Google Cloud Run**: Serverless container deployment
- **Google Cloud Storage**: Cloud data storage

### Related Work
- EU AI Act compliance frameworks and tools
- Regulatory technology (RegTech) for AI governance
- Automated compliance assessment systems

---

## Acknowledgments

This project was developed as part of the AIPI 510 course at Duke University. It builds upon:
- The AIReg-Bench dataset and benchmark developed by Cambridge Machine Learning Systems Lab
- Open-source ML and cloud infrastructure tools
- EU AI Act regulatory framework research

**Development Tools:**
- This project was developed with assistance from Claude (Anthropic's AI assistant) for code implementation, debugging, and documentation

**Disclaimer**: This is an educational project. It is not affiliated with, endorsed by, or representative of any official regulatory body.

---

*Built with scikit-learn, FastAPI, Streamlit, MLflow, and Google Cloud Platform*

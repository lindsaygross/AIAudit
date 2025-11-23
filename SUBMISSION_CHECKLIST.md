# Module Project 3 - Submission Checklist

## ✅ Completed Items

### 1. Dataset and Problem ✅
- [x] Selected AIReg-Bench public dataset
- [x] Defined supervised task: EU AI Act risk classification (high/medium/low)
- [x] Target variable: `risk_label`
- [x] Evaluation metrics: accuracy, macro F1-score

### 2. Reproducible ML Pipeline ✅
- [x] Simple model: TF-IDF + Logistic Regression
- [x] Data ingestion from local clone (to be migrated to GCS)
- [x] Preprocessing and feature engineering
- [x] Train/validation/test split
- [x] Model training and evaluation
- [x] `config.yaml` for all parameters

### 3. Experiment Tracking ✅
- [x] MLflow configured and working
- [x] Tracks parameters, metrics, and artifacts
- [x] Logs model, confusion matrix, dataset info

### 4. Containerization ✅
- [x] Dockerfile created
- [x] Includes training and serving entry points
- [x] Tested locally (builds successfully)

### 5. API Deployment ✅
- [x] FastAPI with `/health`, `/predict`, `/assess_and_remediate` endpoints
- [x] Deployed to Google Cloud Run
- [x] Public endpoint: https://aiaudit-api-fbohlm36ca-uc.a.run.app
- [x] Tested and working

### 6. GitHub Best Practices ✅
- [x] Clear project structure
- [x] requirements.txt
- [x] Good commit history
- [x] At least 1 pull request merged (PR #1)

---

## ❌ To-Do Before Submission

### 1. Cloud Data Storage ⚠️ REQUIRED
**Status:** Data currently only on local disk

**Action Items:**
```bash
# Upload dataset to Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name ./upload_data_to_gcs.sh
```

**After Upload:**
- [ ] Update README with bucket name
- [ ] Verify data is accessible at `gs://your-bucket-name/data/aireg_supervised.csv`

---

### 2. Deploy Frontend to Streamlit Cloud ⚠️ REQUIRED
**Status:** Frontend only runs locally

**Action Items:**
1. [ ] Push latest code to GitHub
   ```bash
   git add .
   git commit -m "Add cloud deployment configuration"
   git push origin main
   ```

2. [ ] Deploy on Streamlit Cloud
   - Go to https://share.streamlit.io
   - Click "New app"
   - Repository: your-github-username/AIAudit
   - Branch: main
   - Main file: `app/app1.py`

3. [ ] Set environment variable in Streamlit Cloud
   - Advanced Settings → Secrets
   - Add:
     ```toml
     API_URL = "https://aiaudit-api-fbohlm36ca-uc.a.run.app"
     ```

4. [ ] Update README.md
   - Replace `[REPLACE_WITH_STREAMLIT_URL_AFTER_DEPLOYMENT]` with actual Streamlit URL

**Expected URL format:** `https://your-app-name.streamlit.app`

---

### 3. Add One More Pull Request (Optional but Recommended)
**Status:** Have 1 PR, but 2+ is better for collaboration demonstration

**Action Items:**
1. [ ] Create a feature branch
   ```bash
   git checkout -b feature/cloud-deployment-docs
   ```

2. [ ] Make a small improvement (e.g., update docs, add deployment script)

3. [ ] Commit and push
   ```bash
   git add .
   git commit -m "Add cloud deployment documentation"
   git push origin feature/cloud-deployment-docs
   ```

4. [ ] Create pull request on GitHub
5. [ ] Merge PR

---

### 4. Final README Updates ⚠️ REQUIRED
**Status:** README has placeholders

**Action Items:**
- [ ] Replace `[ADD_YOUR_BUCKET_NAME]` with actual GCS bucket name
- [ ] Replace `[REPLACE_WITH_STREAMLIT_URL_AFTER_DEPLOYMENT]` with Streamlit URL (2 places)
- [ ] Verify all deployment links work
- [ ] Add partner names if applicable
- [ ] Add any additional ethical considerations discovered during development

---

### 5. Test Everything End-to-End ⚠️ REQUIRED

**Action Items:**
1. [ ] Test API health check
   ```bash
   curl https://aiaudit-api-fbohlm36ca-uc.a.run.app/health
   ```
   Expected: `{"status":"healthy","model_loaded":true,...}`

2. [ ] Test API prediction
   ```bash
   curl -X POST https://aiaudit-api-fbohlm36ca-uc.a.run.app/predict \
     -H "Content-Type: application/json" \
     -d '{"text":"AI system for credit scoring without human oversight"}'
   ```

3. [ ] Test Streamlit app
   - Open deployed Streamlit URL
   - Check "Online" status indicator (green)
   - Submit a test assessment
   - Verify results display correctly

4. [ ] Clone repo fresh and test locally
   ```bash
   git clone YOUR_REPO_URL test-clone
   cd test-clone
   bash dev_start.sh
   ```

---

## 📋 Submission Requirements Checklist

### Required Files in Repository
- [x] All source code (src/, app/, etc.)
- [x] config.yaml
- [x] requirements.txt
- [x] Dockerfile
- [x] .dockerignore
- [x] README.md with:
  - [x] Project overview
  - [x] Dataset description
  - [x] Model architecture
  - [ ] Cloud services used (needs bucket name)
  - [ ] Deployed API link ✅
  - [ ] Deployed frontend link ⚠️
  - [x] Setup instructions
  - [x] Ethics & Limitations section
- [x] MLflow configuration
- [x] Clear project structure

### GitHub Collaboration
- [x] Use of branches
- [x] At least 1 pull request per team member
- [x] Clear commit history

### Deployments
- [x] API deployed to cloud (Google Cloud Run) ✅
- [ ] Frontend deployed to cloud (Streamlit Cloud) ⚠️
- [ ] Data in cloud storage (GCS) ⚠️

### Documentation
- [x] How to train model
- [x] How to test API locally
- [x] How to deploy to cloud
- [x] Ethical considerations
- [x] Limitations discussed

---

## 🎯 Quick Action Plan

**Priority 1 (30 minutes):**
1. Upload data to GCS
2. Deploy Streamlit to Streamlit Cloud
3. Update README with URLs

**Priority 2 (15 minutes):**
4. Test everything end-to-end
5. Fix any broken links or instructions

**Priority 3 (10 minutes):**
6. Optional: Create second PR for better collaboration demonstration
7. Final review of README

**Total Time: ~1 hour**

---

## 📝 Before You Submit

Final sanity checks:
- [ ] README has no placeholder text
- [ ] All deployment URLs work
- [ ] API responds to health check
- [ ] Streamlit app shows "Online" and can submit assessments
- [ ] Repository is public or instructor has access
- [ ] No API keys or secrets committed to repo
- [ ] requirements.txt is up to date

---

## 🚀 Submission Instructions

1. Ensure all items above are complete
2. Submit on Canvas:
   - GitHub repository URL
   - Deployed frontend URL
3. Verify instructor can access:
   - GitHub repo
   - Live API endpoint
   - Live Streamlit app

---

**Your Deployment URLs:**
- API: https://aiaudit-api-fbohlm36ca-uc.a.run.app ✅
- Frontend: [TO BE ADDED AFTER STREAMLIT DEPLOYMENT]
- Data: gs://[YOUR_BUCKET_NAME]/data/aireg_supervised.csv

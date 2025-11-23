# AIAudit Cloud Deployment Guide

This guide covers deploying both the FastAPI backend to Google Cloud Run and the Streamlit frontend to Streamlit Cloud.

## Prerequisites

1. **Google Cloud Platform Account**
   - Create a GCP project at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable billing for your project

2. **Install Google Cloud SDK**
   ```bash
   # macOS (using Homebrew)
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

3. **GitHub Account** (for Streamlit Cloud deployment)

---

## Part 1: Deploy API to Google Cloud Run

### Step 1: Configure gcloud CLI

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Deploy the API

Run the deployment script:

```bash
./deploy_cloudrun.sh
```

This script will:
1. Build your Docker container using Cloud Build
2. Deploy it to Cloud Run
3. Return your API URL

**Expected output:**
```
================================
Deployment Complete!
================================
API URL: https://aiaudit-api-xxxxx-uc.a.run.app

Test the API:
  curl https://aiaudit-api-xxxxx-uc.a.run.app/health
================================
```

### Step 3: Test Your Deployed API

```bash
# Health check
curl https://YOUR-API-URL/health

# Example response:
# {"status":"healthy","model_loaded":true,"templates_loaded":true,"version":"1.0.0"}
```

### Step 4: Save Your API URL

**IMPORTANT:** Copy your API URL! You'll need it for the Streamlit deployment.

Example: `https://aiaudit-api-xxxxx-uc.a.run.app`

---

## Part 2: Deploy Streamlit App to Streamlit Cloud

### Step 1: Push Code to GitHub

```bash
# Commit your changes
git add .
git commit -m "Add Cloud Run deployment configuration"
git push origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Fill in the form:
   - **Repository:** `YOUR_USERNAME/YOUR_REPO_NAME`
   - **Branch:** `main`
   - **Main file path:** `app/app1.py`

### Step 3: Configure Environment Variables

**CRITICAL STEP:** Set the API URL as an environment variable.

1. In the Streamlit Cloud deployment settings, click "Advanced settings"
2. Under "Secrets", add:
   ```toml
   API_URL = "https://aiaudit-api-xxxxx-uc.a.run.app"
   ```
   Replace with your actual Cloud Run API URL from Part 1, Step 4.

3. Click "Deploy"

### Step 4: Verify Connection

Once deployed:
1. Open your Streamlit app URL (e.g., `https://your-app.streamlit.app`)
2. Check the status indicator in the top-right corner
3. It should show "Online" with a green dot ✅

**If it shows "Offline":**
- Verify the `API_URL` environment variable is set correctly
- Test your Cloud Run API URL directly in a browser
- Check Cloud Run logs: `gcloud run logs read aiaudit-api --region us-central1`

---

## Troubleshooting

### API Deployment Issues

**Problem:** Build fails with "permission denied"
```bash
# Solution: Authenticate with application-default credentials
gcloud auth application-default login
```

**Problem:** Service times out during startup
```bash
# Solution: Check Cloud Run logs
gcloud run logs read aiaudit-api --region us-central1 --limit 50

# Common issue: Model training takes too long
# Fix: Pre-train model locally and commit artifacts/ folder
python -m src.models.train --config config.yaml
git add artifacts/
git commit -m "Add pre-trained model artifacts"
```

**Problem:** "Service Unavailable" errors
```bash
# Check if model loaded successfully
curl https://YOUR-API-URL/health

# If model_loaded: false, the model didn't load
# Solution: Run training locally, commit artifacts, redeploy
```

### Streamlit Deployment Issues

**Problem:** App shows "Offline" status

**Solutions:**
1. Verify environment variable:
   - Go to Streamlit Cloud dashboard
   - Click your app → Settings → Secrets
   - Ensure `API_URL` is set to your Cloud Run URL (not localhost!)

2. Test API directly:
   ```bash
   curl https://YOUR-CLOUD-RUN-URL/health
   ```

3. Check browser console:
   - Open browser DevTools (F12)
   - Look for CORS or network errors

**Problem:** CORS errors in browser console

**Solution:** The API already has CORS enabled. If you still see CORS errors:
- Ensure you're using HTTPS for the API URL (not HTTP)
- Check that Cloud Run service allows unauthenticated requests

---

## Cost Optimization

### Cloud Run Pricing

Free tier includes:
- 2 million requests/month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**To minimize costs:**

```bash
# Deploy with minimal resources for low-traffic apps
gcloud run deploy aiaudit-api \
    --image gcr.io/YOUR_PROJECT/aiaudit-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5
```

### Streamlit Cloud Pricing

- **Free tier:** 1 private app OR unlimited public apps
- Your app will be public by default (fine for demo/portfolio)

---

## Security Considerations

### Current Setup (Development/Demo)
- ✅ API is public (allows unauthenticated requests)
- ✅ Streamlit app is public
- ✅ CORS allows all origins

### Production Hardening

For production use:

1. **Enable API Authentication:**
   ```bash
   # Remove --allow-unauthenticated flag
   gcloud run deploy aiaudit-api \
       --image gcr.io/YOUR_PROJECT/aiaudit-api \
       --platform managed \
       --region us-central1
   ```

2. **Restrict CORS in `src/api/main.py`:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-app.streamlit.app"],  # Specific domain
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **Add Rate Limiting:**
   - Use Cloud Armor or API Gateway
   - Prevents abuse and controls costs

---

## Continuous Deployment

### Auto-deploy on Git Push

1. **Cloud Run:** Use Cloud Build triggers
   ```bash
   gcloud builds triggers create github \
       --repo-name=YOUR_REPO \
       --repo-owner=YOUR_USERNAME \
       --branch-pattern="^main$" \
       --build-config=cloudbuild.yaml
   ```

2. **Streamlit Cloud:** Automatically deploys on git push to main branch

---

## Monitoring

### Cloud Run Metrics

```bash
# View recent logs
gcloud run logs read aiaudit-api --region us-central1 --limit 100

# Monitor in console
open "https://console.cloud.google.com/run/detail/us-central1/aiaudit-api/metrics"
```

### Streamlit Cloud Metrics

- View logs in Streamlit Cloud dashboard
- Monitor app health and usage statistics

---

## Quick Reference

### Update API After Code Changes

```bash
# 1. Commit changes
git add .
git commit -m "Update API logic"
git push

# 2. Redeploy
./deploy_cloudrun.sh

# 3. New API URL will be displayed (usually stays the same)
```

### Update Streamlit App

```bash
# Just push to GitHub - auto-deploys
git add .
git commit -m "Update Streamlit UI"
git push origin main

# Streamlit Cloud will rebuild automatically
```

### Rollback Deployment

```bash
# Cloud Run: View revisions
gcloud run revisions list --service aiaudit-api --region us-central1

# Rollback to previous revision
gcloud run services update-traffic aiaudit-api \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

---

## Summary Checklist

### Initial Setup
- [ ] Install gcloud CLI
- [ ] Login: `gcloud auth login`
- [ ] Set project: `gcloud config set project YOUR_PROJECT_ID`
- [ ] Enable APIs (Cloud Run, Cloud Build)

### API Deployment
- [ ] Run `./deploy_cloudrun.sh`
- [ ] Test: `curl YOUR-API-URL/health`
- [ ] Save API URL

### Streamlit Deployment
- [ ] Push code to GitHub
- [ ] Deploy on share.streamlit.io
- [ ] Set `API_URL` environment variable
- [ ] Verify "Online" status

### Validation
- [ ] API returns `{"status":"healthy"}`
- [ ] Streamlit shows green "Online" indicator
- [ ] Can submit test assessment successfully
- [ ] Results display correctly

---

## Getting Help

- **Cloud Run Issues:** [cloud.google.com/run/docs](https://cloud.google.com/run/docs)
- **Streamlit Issues:** [docs.streamlit.io](https://docs.streamlit.io)
- **Project Issues:** Check logs with commands above

**Your deployment URLs:**
- API: `https://aiaudit-api-xxxxx-uc.a.run.app` (replace after deployment)
- Streamlit: `https://your-app.streamlit.app` (replace after deployment)

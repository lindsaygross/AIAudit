#!/bin/bash
# Deploy AIAudit API to Google Cloud Run
#
# Prerequisites:
# 1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Login: gcloud auth login
# 3. Set project: gcloud config set project YOUR_PROJECT_ID
# 4. Enable APIs:
#    gcloud services enable run.googleapis.com
#    gcloud services enable cloudbuild.googleapis.com

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="aiaudit-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=================================="
echo "AIAudit API - Cloud Run Deployment"
echo "=================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo "=================================="

# Verify gcloud is configured
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No GCP project configured."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# Build the container image using Cloud Build
echo ""
echo "Step 1: Building container image..."
gcloud builds submit --tag "$IMAGE_NAME" --project "$PROJECT_ID"

# Deploy to Cloud Run
echo ""
echo "Step 2: Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --port 8080 \
    --project "$PROJECT_ID"

# Get the service URL
echo ""
echo "Step 3: Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --format 'value(status.url)' \
    --project "$PROJECT_ID")

echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo "API URL: $SERVICE_URL"
echo ""
echo "Test the API:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "Next steps:"
echo "1. Update your Streamlit app with this API URL"
echo "2. Set environment variable in Streamlit Cloud:"
echo "   API_URL=$SERVICE_URL"
echo "=================================="

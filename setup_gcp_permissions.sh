#!/bin/bash
# Setup GCP permissions for Cloud Run deployment
# Developed with assistance from Claude (Anthropic AI)
#
# Run this script to configure the necessary permissions

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
USER_EMAIL=$(gcloud config get-value account)

echo "=================================="
echo "GCP Permissions Setup"
echo "=================================="
echo "Project ID: $PROJECT_ID"
echo "User Email: $USER_EMAIL"
echo "=================================="

if [ -z "$PROJECT_ID" ]; then
    echo "Error: No GCP project configured."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo ""
echo "Step 1: Enabling required APIs..."
echo "This may take 1-2 minutes..."
gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID"
gcloud services enable run.googleapis.com --project="$PROJECT_ID"
gcloud services enable containerregistry.googleapis.com --project="$PROJECT_ID"
gcloud services enable artifactregistry.googleapis.com --project="$PROJECT_ID"

echo ""
echo "Step 2: Granting IAM roles to your account..."
echo "Adding Cloud Build Editor role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$USER_EMAIL" \
    --role="roles/cloudbuild.builds.editor" \
    --condition=None

echo "Adding Cloud Run Admin role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$USER_EMAIL" \
    --role="roles/run.admin" \
    --condition=None

echo "Adding Service Account User role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$USER_EMAIL" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None

echo "Adding Storage Admin role (for Container Registry)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$USER_EMAIL" \
    --role="roles/storage.admin" \
    --condition=None

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Permissions granted:"
echo "  ✓ Cloud Build Editor"
echo "  ✓ Cloud Run Admin"
echo "  ✓ Service Account User"
echo "  ✓ Storage Admin"
echo ""
echo "APIs enabled:"
echo "  ✓ Cloud Build API"
echo "  ✓ Cloud Run API"
echo "  ✓ Container Registry API"
echo "  ✓ Artifact Registry API"
echo ""
echo "Wait 1-2 minutes for permissions to propagate, then run:"
echo "  ./deploy_cloudrun.sh"
echo "=================================="

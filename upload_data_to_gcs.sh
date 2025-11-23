#!/bin/bash
# Upload dataset to Google Cloud Storage
# Developed with assistance from Claude (Anthropic AI)

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
BUCKET_NAME="${GCS_BUCKET_NAME}"

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: GCS_BUCKET_NAME not set"
    echo "Usage: GCS_BUCKET_NAME=your-bucket-name ./upload_data_to_gcs.sh"
    exit 1
fi

echo "=================================="
echo "Uploading Data to GCS"
echo "=================================="
echo "Project: $PROJECT_ID"
echo "Bucket: gs://$BUCKET_NAME"
echo "=================================="

# Upload the supervised dataset
echo ""
echo "Uploading aireg_supervised.csv..."
gsutil cp data/aireg_supervised.csv "gs://$BUCKET_NAME/data/aireg_supervised.csv"

echo ""
echo "✅ Upload complete!"
echo ""
echo "Data URL: gs://$BUCKET_NAME/data/aireg_supervised.csv"
echo ""
echo "Add this to your README.md under 'Cloud Services Used'"

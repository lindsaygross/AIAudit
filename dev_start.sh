#!/bin/bash
# =============================================================================
# AIAudit Lite - Development Startup Script
# =============================================================================
#
# PRODUCT PURPOSE:
# AIAudit Lite is a decision-support prototype that evaluates textual technical
# documentation of AI systems against EU AI Act risk signals and returns a
# prioritized remediation plan. Target users: product teams, AI-governance, and
# legal/compliance. The tool provides heuristic, auditable guidance — not legal
# advice.
#
# This script runs the full pipeline locally end-to-end:
# 1. Creates/activates virtual environment
# 2. Installs dependencies
# 3. Clones/pulls AIReg-Bench dataset
# 4. Builds supervised CSV
# 5. Trains risk classification model
# 6. Starts FastAPI server
#
# Usage:
#   chmod +x dev_start.sh
#   bash dev_start.sh
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "============================================================================="
echo "                        AIAudit Lite - Development Setup                     "
echo "============================================================================="
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Working directory: $SCRIPT_DIR${NC}"
echo ""

# =============================================================================
# Step 1: Virtual Environment
# =============================================================================
echo -e "${BLUE}Step 1: Setting up virtual environment...${NC}"

if [ -d ".venv" ]; then
    echo -e "${GREEN}Virtual environment exists. Activating...${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.11 -m venv .venv 2>/dev/null || python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo -e "${GREEN}Virtual environment activated: $(which python)${NC}"
echo ""

# =============================================================================
# Step 2: Install Dependencies
# =============================================================================
echo -e "${BLUE}Step 2: Installing dependencies...${NC}"

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo -e "${GREEN}Dependencies installed successfully.${NC}"
echo ""

# =============================================================================
# Step 3: Build Dataset
# =============================================================================
echo -e "${BLUE}Step 3: Building dataset from AIReg-Bench...${NC}"

# Create data directories if they don't exist
mkdir -p data/raw

# Run dataset builder (this will clone/pull AIReg-Bench)
python src/data/build_dataset.py

echo -e "${GREEN}Dataset build complete.${NC}"
echo ""

# =============================================================================
# Step 4: Train Model
# =============================================================================
echo -e "${BLUE}Step 4: Training risk classification model...${NC}"

# Create artifacts directory if it doesn't exist
mkdir -p artifacts

# Train the model
python -m src.models.train --config config.yaml

echo -e "${GREEN}Model training complete.${NC}"
echo ""

# =============================================================================
# Step 5: Run Tests (Optional)
# =============================================================================
echo -e "${BLUE}Step 5: Running tests...${NC}"

pytest tests/ -v --tb=short || {
    echo -e "${YELLOW}Some tests failed. Continuing anyway...${NC}"
}

echo ""

# =============================================================================
# Step 6: Start API Server
# =============================================================================
echo -e "${BLUE}Step 6: Starting FastAPI server...${NC}"

echo -e "${GREEN}"
echo "============================================================================="
echo "                           AIAudit Lite Ready!                              "
echo "============================================================================="
echo ""
echo "  API Server:    http://127.0.0.1:8000"
echo "  API Docs:      http://127.0.0.1:8000/docs"
echo "  Health Check:  http://127.0.0.1:8000/health"
echo ""
echo "  To start Streamlit UI (in another terminal):"
echo "    source .venv/bin/activate"
echo "    streamlit run app/app.py"
echo ""
echo "  To view MLflow experiments:"
echo "    source .venv/bin/activate"
echo "    mlflow ui"
echo ""
echo "  Press Ctrl+C to stop the server."
echo "============================================================================="
echo -e "${NC}"

# Start uvicorn (this will block)
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

"""
FastAPI application for AIAudit.

This module provides the REST API for EU AI Act compliance assessment
and remediation planning. It loads the trained model and templates on
startup and exposes endpoints for prediction and assessment.

Usage:
    uvicorn src.api.main:app --reload --port 8000

Endpoints:
    GET  /health              - Health check
    POST /predict             - Risk classification
    POST /assess_and_remediate - Full assessment with remediation plan
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src import __version__
from src.api.schemas import (
    ErrorResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    RemediationRequest,
    RemediationResponse,
)
from src.models.predict import load_model, predict_text
from src.remediation.generator import generate_remediation_plan, load_templates
from src.utils.config import load_config, get_project_root


# Global state for loaded resources
class AppState:
    """Container for application state."""
    config: Optional[Dict[str, Any]] = None
    pipeline: Optional[Any] = None
    templates: Optional[Dict[str, Any]] = None
    model_version: str = "not_loaded"
    template_version: str = "1.0.0"
    startup_time: Optional[datetime] = None


state = AppState()


def ensure_dataset_exists():
    """
    Ensure the training dataset exists, building it if necessary.

    This function checks for data/aireg_supervised.csv and runs
    build_dataset.py if it doesn't exist.
    """
    project_root = get_project_root()
    dataset_path = project_root / "data" / "aireg_supervised.csv"

    if not dataset_path.exists():
        print("Dataset not found. Building from AIReg-Bench...")
        try:
            from src.data.build_dataset import main as build_dataset_main
            build_dataset_main()
        except Exception as e:
            print(f"Warning: Could not build dataset: {e}")
            print("The API will run but training/prediction may fail.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup/shutdown.

    On startup:
    - Load configuration
    - Ensure dataset exists
    - Load trained model (if available)
    - Load remediation templates
    """
    print("=" * 50)
    print("AIAudit API Starting...")
    print("=" * 50)

    # Load configuration
    try:
        state.config = load_config()
        print("Configuration loaded.")
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        state.config = {}

    # Ensure dataset exists
    ensure_dataset_exists()

    # Load model
    project_root = get_project_root()
    model_path = project_root / "artifacts" / "model.joblib"

    try:
        state.pipeline = load_model(str(model_path))
        state.model_version = f"1.0.0-{model_path.stat().st_mtime:.0f}"
        print(f"Model loaded from: {model_path}")
    except FileNotFoundError:
        print("Warning: Model not found. Run 'python -m src.models.train' to train.")
        print("The /predict and /assess_and_remediate endpoints will return errors.")
        state.pipeline = None

    # Load templates
    template_path = project_root / "templates" / "article_remediations.yml"

    try:
        state.templates = load_templates(str(template_path))
        print(f"Templates loaded from: {template_path}")
    except FileNotFoundError:
        print(f"Warning: Templates not found at {template_path}")
        state.templates = {}

    state.startup_time = datetime.utcnow()
    print("=" * 50)
    print("AIAudit API Ready!")
    print("=" * 50)

    yield

    # Cleanup on shutdown
    print("AIAudit API Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="AIAudit Lite API",
    description=(
        "EU AI Act compliance triage and remediation planning API. "
        "Provides risk classification and actionable remediation guidance "
        "for AI system documentation."
    ),
    version=__version__,
    lifespan=lifespan,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check API health status.

    Returns the current status of the API, including whether the model
    and templates are loaded.
    """
    status = "healthy" if state.pipeline is not None else "degraded"

    return HealthResponse(
        status=status,
        model_loaded=state.pipeline is not None,
        templates_loaded=state.templates is not None and len(state.templates) > 0,
        version=__version__
    )


@app.post(
    "/predict",
    response_model=PredictResponse,
    tags=["Prediction"],
    summary="Classify risk level of AI documentation",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "Model not loaded"}
    }
)
async def predict(request: PredictRequest):
    """
    Predict the EU AI Act risk level for AI system documentation.

    Classifies the input text as high, medium, or low risk based on
    the trained ML model.

    Args:
        request: PredictRequest with text to classify.

    Returns:
        PredictResponse with predicted label and probabilities.

    Raises:
        HTTPException 503: If model is not loaded.
    """
    if state.pipeline is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ServiceUnavailable",
                "message": "Model not loaded. Please run training first.",
                "detail": "Execute: python -m src.models.train --config config.yaml"
            }
        )

    try:
        project_root = get_project_root()
        encoder_path = project_root / "artifacts" / "label_encoder.json"

        label, probs = predict_text(
            state.pipeline,
            request.text,
            label_encoder_path=str(encoder_path)
        )

        return PredictResponse(
            predicted_label=label,
            probabilities=probs,
            model_version=state.model_version
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PredictionError",
                "message": str(e),
                "detail": None
            }
        )


@app.post(
    "/assess_and_remediate",
    response_model=RemediationResponse,
    tags=["Assessment"],
    summary="Full compliance assessment with remediation plan",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "Model or templates not loaded"}
    }
)
async def assess_and_remediate(request: RemediationRequest):
    """
    Perform full EU AI Act compliance assessment and generate remediation plan.

    This endpoint:
    1. Classifies the risk level using the ML model
    2. Extracts relevant keywords
    3. Fuses ML and rule-based signals
    4. Generates prioritized remediation actions from templates

    Args:
        request: RemediationRequest with text and optional parameters.

    Returns:
        RemediationResponse with full assessment and remediation plan.

    Raises:
        HTTPException 503: If model or templates are not loaded.
    """
    if state.pipeline is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ServiceUnavailable",
                "message": "Model not loaded. Please run training first.",
                "detail": "Execute: python -m src.models.train --config config.yaml"
            }
        )

    if not state.templates:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ServiceUnavailable",
                "message": "Remediation templates not loaded.",
                "detail": "Ensure templates/article_remediations.yml exists."
            }
        )

    try:
        project_root = get_project_root()
        encoder_path = project_root / "artifacts" / "label_encoder.json"

        # Get model predictions
        label, probs = predict_text(
            state.pipeline,
            request.text,
            label_encoder_path=str(encoder_path)
        )

        # Override top_k in config if provided
        config = state.config.copy() if state.config else {}
        if request.top_k:
            config.setdefault("remediation", {})["top_k_remediations"] = request.top_k

        # Generate remediation plan
        plan = generate_remediation_plan(
            text=request.text,
            model_probs=probs,
            templates=state.templates,
            config=config
        )

        return RemediationResponse(
            summary=plan["summary"],
            risk_level=plan["risk_level"],
            confidence=plan["confidence"],
            matched_keywords=plan["matched_keywords"],
            article_scores=plan["article_scores"],
            items=plan["items"],
            disclaimer=plan["disclaimer"],
            model_version=state.model_version,
            template_version=state.template_version
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AssessmentError",
                "message": str(e),
                "detail": None
            }
        )


@app.get(
    "/",
    tags=["System"],
    summary="API root",
    include_in_schema=False
)
async def root():
    """Redirect to API documentation."""
    return {
        "name": "AIAudit Lite API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

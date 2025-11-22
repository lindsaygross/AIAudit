"""
Pydantic schemas for AIAudit API.

This module defines request and response models for the FastAPI endpoints.
All models include validation and documentation for OpenAPI spec generation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================

class PredictRequest(BaseModel):
    """Request model for /predict endpoint."""

    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="AI system documentation text to classify"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This AI system uses facial recognition for access control..."
            }
        }


class RemediationRequest(BaseModel):
    """Request model for /assess_and_remediate endpoint."""

    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="AI system documentation text to assess"
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of top remediation items per article"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This AI system uses biometric identification for real-time surveillance...",
                "top_k": 3
            }
        }


# ============================================================================
# Response Models
# ============================================================================

class PredictResponse(BaseModel):
    """Response model for /predict endpoint."""

    predicted_label: str = Field(
        ...,
        description="Predicted risk level: high, medium, or low"
    )
    probabilities: Dict[str, float] = Field(
        ...,
        description="Probability distribution over risk levels"
    )
    model_version: str = Field(
        ...,
        description="Version identifier of the prediction model"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "predicted_label": "high",
                "probabilities": {
                    "high": 0.75,
                    "medium": 0.20,
                    "low": 0.05
                },
                "model_version": "1.0.0"
            }
        }


class RemediationItem(BaseModel):
    """Single remediation action item."""

    article: str = Field(..., description="EU AI Act article reference")
    article_name: str = Field(..., description="Human-readable article name")
    article_score: float = Field(..., description="Relevance score for this article")
    remediation_id: str = Field(..., description="Unique remediation identifier")
    title: str = Field(..., description="Remediation action title")
    description: str = Field(..., description="Detailed remediation guidance")
    urgency: str = Field(..., description="Urgency level: high, medium, or low")
    estimated_effort: str = Field(..., description="Estimated implementation effort")
    priority: int = Field(..., description="Priority ranking (1 = highest)")


class RemediationResponse(BaseModel):
    """Response model for /assess_and_remediate endpoint."""

    summary: str = Field(
        ...,
        description="Human-readable summary of the assessment"
    )
    risk_level: str = Field(
        ...,
        description="Overall risk level: high, medium, or low"
    )
    confidence: float = Field(
        ...,
        description="Confidence score for the risk prediction"
    )
    matched_keywords: List[str] = Field(
        ...,
        description="Keywords matched from the input text"
    )
    article_scores: Dict[str, float] = Field(
        ...,
        description="Relevance scores per EU AI Act article"
    )
    items: List[RemediationItem] = Field(
        ...,
        description="Prioritized list of remediation actions"
    )
    disclaimer: str = Field(
        ...,
        description="Legal disclaimer about the assessment"
    )
    model_version: str = Field(
        ...,
        description="Version identifier of the prediction model"
    )
    template_version: str = Field(
        ...,
        description="Version identifier of the remediation templates"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Assessment indicates HIGH risk level (confidence: 80%)...",
                "risk_level": "high",
                "confidence": 0.80,
                "matched_keywords": ["biometric", "surveillance"],
                "article_scores": {
                    "Article_9": 0.85,
                    "Article_10": 0.65,
                    "Article_12": 0.45,
                    "Article_14": 0.55,
                    "Article_15": 0.40
                },
                "items": [
                    {
                        "article": "Article_9",
                        "article_name": "Risk Management System",
                        "article_score": 0.85,
                        "remediation_id": "A9-R1",
                        "title": "Implement Continuous Risk Monitoring Pipeline",
                        "description": "Deploy automated monitoring infrastructure...",
                        "urgency": "high",
                        "estimated_effort": "2-3 weeks",
                        "priority": 1
                    }
                ],
                "disclaimer": "This remediation plan provides heuristic guidance...",
                "model_version": "1.0.0",
                "template_version": "1.0.0"
            }
        }


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""

    status: str = Field(..., description="Health status: healthy or degraded")
    model_loaded: bool = Field(..., description="Whether the ML model is loaded")
    templates_loaded: bool = Field(..., description="Whether templates are loaded")
    version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "templates_loaded": True,
                "version": "0.1.0"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Text must be at least 10 characters",
                "detail": None
            }
        }

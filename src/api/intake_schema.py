"""
Structured intake form schema for AI system assessment.

This module defines the intake form structure that companies use to describe
their AI systems for compliance assessment. It follows a standardized format
that maps to EU AI Act risk categories.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Sector(str, Enum):
    """Industry sectors for AI deployment."""
    HIRING = "hiring"
    CREDIT_SCORING = "credit_scoring"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    LAW_ENFORCEMENT = "law_enforcement"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    INSURANCE = "insurance"
    SOCIAL_SERVICES = "social_services"
    RECOMMENDER = "recommender"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"
    OTHER = "other"


class UserType(str, Enum):
    """Types of users affected by the AI system."""
    GENERAL_PUBLIC = "general_public"
    EMPLOYEES = "employees"
    CHILDREN = "children"
    ELDERLY = "elderly"
    VULNERABLE_GROUPS = "vulnerable_groups"
    PROFESSIONALS = "professionals"
    CONSUMERS = "consumers"
    PATIENTS = "patients"
    STUDENTS = "students"


class DataType(str, Enum):
    """Types of data processed by the AI system."""
    BIOMETRICS = "biometrics"
    HEALTH_DATA = "health_data"
    FINANCIAL_DATA = "financial_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    POLITICAL_OPINIONS = "political_opinions"
    RELIGIOUS_BELIEFS = "religious_beliefs"
    ETHNIC_ORIGIN = "ethnic_origin"
    SEXUAL_ORIENTATION = "sexual_orientation"
    CRIMINAL_RECORDS = "criminal_records"
    EMPLOYMENT_DATA = "employment_data"
    EDUCATIONAL_RECORDS = "educational_records"
    GENERIC_PII = "generic_pii"
    ANONYMOUS_DATA = "anonymous_data"


class DecisionImpact(str, Enum):
    """Types of decisions influenced by the AI system."""
    ACCESS_TO_SERVICES = "access_to_services"
    SAFETY_CRITICAL = "safety_critical"
    CONTENT_RANKING = "content_ranking"
    EMPLOYMENT_DECISIONS = "employment_decisions"
    CREDIT_DECISIONS = "credit_decisions"
    LEGAL_DECISIONS = "legal_decisions"
    EDUCATIONAL_OUTCOMES = "educational_outcomes"
    HEALTH_TREATMENT = "health_treatment"
    LAW_ENFORCEMENT_ACTIONS = "law_enforcement_actions"
    MIGRATION_DECISIONS = "migration_decisions"
    RECOMMENDATIONS = "recommendations"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"


class OversightLevel(str, Enum):
    """Level of human oversight in the AI system."""
    FULLY_AUTOMATED = "fully_automated"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    HUMAN_ON_THE_LOOP = "human_on_the_loop"
    HUMAN_OVERRIDE_POSSIBLE = "human_override_possible"
    HUMAN_FINAL_DECISION = "human_final_decision"


class DocumentationStatus(str, Enum):
    """Status of documentation artifacts."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    NEEDS_UPDATE = "needs_update"


class DocumentationArtifacts(BaseModel):
    """Documentation status for various compliance artifacts."""
    data_sheet: DocumentationStatus = DocumentationStatus.NOT_STARTED
    model_card: DocumentationStatus = DocumentationStatus.NOT_STARTED
    system_logs: DocumentationStatus = DocumentationStatus.NOT_STARTED
    monitoring_dashboard: DocumentationStatus = DocumentationStatus.NOT_STARTED
    risk_assessment: DocumentationStatus = DocumentationStatus.NOT_STARTED
    bias_audit: DocumentationStatus = DocumentationStatus.NOT_STARTED
    technical_documentation: DocumentationStatus = DocumentationStatus.NOT_STARTED
    user_instructions: DocumentationStatus = DocumentationStatus.NOT_STARTED


class AISystemIntake(BaseModel):
    """
    Structured intake form for AI system assessment.

    This is the primary input format for company-scale AI governance workflows.
    """
    # System identification
    system_name: str = Field(..., min_length=3, max_length=200, description="Name of the AI system")
    system_version: str = Field(default="1.0.0", description="Version identifier")
    team_name: str = Field(..., description="Responsible team or department")
    project_owner: str = Field(..., description="Project owner email or name")

    # Use case description
    sector: Sector = Field(..., description="Primary industry sector")
    use_case_description: str = Field(..., min_length=20, description="Detailed description of the AI use case")

    # User and data characteristics
    user_types: List[UserType] = Field(..., min_length=1, description="Types of users affected")
    data_types: List[DataType] = Field(..., min_length=1, description="Types of data processed")

    # Decision impact
    decision_impacts: List[DecisionImpact] = Field(..., min_length=1, description="Types of decisions influenced")

    # Oversight and control
    oversight_level: OversightLevel = Field(..., description="Level of human oversight")
    can_users_opt_out: bool = Field(default=False, description="Can users opt out of AI processing?")
    appeal_mechanism: bool = Field(default=False, description="Is there an appeal mechanism for decisions?")

    # Documentation status
    documentation: DocumentationArtifacts = Field(default_factory=DocumentationArtifacts)

    # Technical details (optional)
    model_type: Optional[str] = Field(None, description="Type of ML model used")
    training_data_size: Optional[int] = Field(None, description="Approximate training data size")
    deployment_environment: Optional[str] = Field(None, description="Where the system is deployed")

    # Free-form documentation text (for ML classification)
    additional_documentation: Optional[str] = Field(None, description="Additional technical documentation")

    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "Resume Screening Assistant",
                "system_version": "2.1.0",
                "team_name": "HR Technology",
                "project_owner": "hr-tech@company.com",
                "sector": "hiring",
                "use_case_description": "AI-powered resume screening tool that ranks candidates based on job requirements and historical hiring patterns.",
                "user_types": ["employees", "general_public"],
                "data_types": ["employment_data", "educational_records", "generic_pii"],
                "decision_impacts": ["employment_decisions", "access_to_services"],
                "oversight_level": "human_final_decision",
                "can_users_opt_out": True,
                "appeal_mechanism": True,
                "documentation": {
                    "data_sheet": "complete",
                    "model_card": "in_progress",
                    "bias_audit": "complete"
                }
            }
        }


class RiskFactor(BaseModel):
    """Individual risk factor identified in the assessment."""
    factor: str
    weight: float
    description: str
    article_reference: Optional[str] = None


class ComplianceObligation(BaseModel):
    """Specific compliance obligation identified."""
    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    status: str  # required, recommended, optional
    article_reference: str


class IntakeAssessmentResponse(BaseModel):
    """Response from the intake form assessment."""
    # Risk scoring
    risk_score: float = Field(..., ge=0, le=1, description="Overall risk score 0-1")
    risk_category: str = Field(..., description="high_risk, medium_risk, low_risk")
    risk_label: str = Field(..., description="Human-readable risk label")

    # Risk factors breakdown
    risk_factors: List[RiskFactor] = Field(..., description="Factors contributing to risk score")

    # Compliance obligations
    obligations: List[ComplianceObligation] = Field(..., description="Required compliance actions")

    # Documentation gaps
    documentation_gaps: List[str] = Field(..., description="Missing or incomplete documentation")

    # Key recommendations
    key_recommendations: List[str] = Field(..., description="Top priority actions")

    # Remediation items (from template system)
    remediation_items: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    assessment_id: str
    assessment_timestamp: str
    model_version: str

    # Summary for executives
    executive_summary: str


class SnapshotRecord(BaseModel):
    """Historical snapshot of an assessment."""
    snapshot_id: str
    system_name: str
    system_version: str
    assessment_timestamp: str
    risk_score: float
    risk_category: str
    key_changes: Optional[List[str]] = None

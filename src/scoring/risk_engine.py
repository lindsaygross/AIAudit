"""
Rule-based risk scoring engine for AI system assessment.
Developed with assistance from Claude (Anthropic AI).

This module implements the compliance readiness scoring logic that combines
ML predictions with rule-based heuristics based on EU AI Act categories.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Tuple

from src.api.intake_schema import (
    AISystemIntake,
    ComplianceObligation,
    DataType,
    DecisionImpact,
    DocumentationStatus,
    IntakeAssessmentResponse,
    OversightLevel,
    RiskFactor,
    Sector,
    UserType,
)


# Risk weights for different factors
SECTOR_RISK_WEIGHTS = {
    Sector.LAW_ENFORCEMENT: 0.95,
    Sector.CRITICAL_INFRASTRUCTURE: 0.90,
    Sector.HEALTHCARE: 0.85,
    Sector.CREDIT_SCORING: 0.80,
    Sector.HIRING: 0.75,
    Sector.EDUCATION: 0.70,
    Sector.INSURANCE: 0.70,
    Sector.SOCIAL_SERVICES: 0.75,
    Sector.RECOMMENDER: 0.40,
    Sector.MARKETING: 0.30,
    Sector.CUSTOMER_SERVICE: 0.25,
    Sector.MANUFACTURING: 0.35,
    Sector.LOGISTICS: 0.30,
    Sector.OTHER: 0.50,
}

USER_TYPE_RISK_WEIGHTS = {
    UserType.CHILDREN: 0.90,
    UserType.VULNERABLE_GROUPS: 0.85,
    UserType.ELDERLY: 0.75,
    UserType.PATIENTS: 0.80,
    UserType.STUDENTS: 0.65,
    UserType.GENERAL_PUBLIC: 0.50,
    UserType.EMPLOYEES: 0.45,
    UserType.CONSUMERS: 0.40,
    UserType.PROFESSIONALS: 0.30,
}

DATA_TYPE_RISK_WEIGHTS = {
    DataType.BIOMETRICS: 0.95,
    DataType.HEALTH_DATA: 0.90,
    DataType.CRIMINAL_RECORDS: 0.90,
    DataType.POLITICAL_OPINIONS: 0.85,
    DataType.RELIGIOUS_BELIEFS: 0.85,
    DataType.ETHNIC_ORIGIN: 0.85,
    DataType.SEXUAL_ORIENTATION: 0.85,
    DataType.FINANCIAL_DATA: 0.70,
    DataType.LOCATION_DATA: 0.60,
    DataType.BEHAVIORAL_DATA: 0.55,
    DataType.EMPLOYMENT_DATA: 0.50,
    DataType.EDUCATIONAL_RECORDS: 0.45,
    DataType.GENERIC_PII: 0.40,
    DataType.ANONYMOUS_DATA: 0.10,
}

DECISION_IMPACT_WEIGHTS = {
    DecisionImpact.LAW_ENFORCEMENT_ACTIONS: 0.95,
    DecisionImpact.LEGAL_DECISIONS: 0.90,
    DecisionImpact.MIGRATION_DECISIONS: 0.90,
    DecisionImpact.SAFETY_CRITICAL: 0.90,
    DecisionImpact.HEALTH_TREATMENT: 0.85,
    DecisionImpact.CREDIT_DECISIONS: 0.80,
    DecisionImpact.EMPLOYMENT_DECISIONS: 0.75,
    DecisionImpact.EDUCATIONAL_OUTCOMES: 0.70,
    DecisionImpact.ACCESS_TO_SERVICES: 0.65,
    DecisionImpact.CONTENT_RANKING: 0.40,
    DecisionImpact.RECOMMENDATIONS: 0.30,
    DecisionImpact.OPERATIONAL_EFFICIENCY: 0.20,
}

OVERSIGHT_RISK_MODIFIERS = {
    OversightLevel.FULLY_AUTOMATED: 1.0,  # Highest risk
    OversightLevel.HUMAN_ON_THE_LOOP: 0.85,
    OversightLevel.HUMAN_IN_THE_LOOP: 0.70,
    OversightLevel.HUMAN_OVERRIDE_POSSIBLE: 0.60,
    OversightLevel.HUMAN_FINAL_DECISION: 0.40,  # Lowest risk
}


def compute_base_risk_score(intake: AISystemIntake) -> Tuple[float, List[RiskFactor]]:
    """
    Compute the base risk score from intake form data.

    Returns:
        Tuple of (risk_score, list of contributing factors)
    """
    factors = []

    # 1. Sector risk
    sector_weight = SECTOR_RISK_WEIGHTS.get(intake.sector, 0.5)
    factors.append(RiskFactor(
        factor="sector",
        weight=sector_weight,
        description=f"Sector '{intake.sector.value}' risk level",
        article_reference="Article 6 - High-risk classification"
    ))

    # 2. User type risk (max of all user types)
    user_weights = [USER_TYPE_RISK_WEIGHTS.get(ut, 0.5) for ut in intake.user_types]
    max_user_weight = max(user_weights) if user_weights else 0.5
    vulnerable_users = [ut for ut in intake.user_types if ut in [UserType.CHILDREN, UserType.VULNERABLE_GROUPS, UserType.ELDERLY]]

    factors.append(RiskFactor(
        factor="user_types",
        weight=max_user_weight,
        description=f"Affects {', '.join([ut.value for ut in intake.user_types])}",
        article_reference="Article 9 - Risk management for vulnerable groups"
    ))

    # 3. Data type risk (max of all data types)
    data_weights = [DATA_TYPE_RISK_WEIGHTS.get(dt, 0.5) for dt in intake.data_types]
    max_data_weight = max(data_weights) if data_weights else 0.5
    sensitive_data = [dt for dt in intake.data_types if DATA_TYPE_RISK_WEIGHTS.get(dt, 0) >= 0.85]

    factors.append(RiskFactor(
        factor="data_types",
        weight=max_data_weight,
        description=f"Processes {', '.join([dt.value for dt in intake.data_types])}",
        article_reference="Article 10 - Data governance requirements"
    ))

    # 4. Decision impact risk (max of all impacts)
    impact_weights = [DECISION_IMPACT_WEIGHTS.get(di, 0.5) for di in intake.decision_impacts]
    max_impact_weight = max(impact_weights) if impact_weights else 0.5

    factors.append(RiskFactor(
        factor="decision_impact",
        weight=max_impact_weight,
        description=f"Influences {', '.join([di.value for di in intake.decision_impacts])}",
        article_reference="Article 6 - Annex III high-risk categories"
    ))

    # 5. Oversight modifier
    oversight_modifier = OVERSIGHT_RISK_MODIFIERS.get(intake.oversight_level, 0.7)
    factors.append(RiskFactor(
        factor="oversight_level",
        weight=oversight_modifier,
        description=f"Human oversight: {intake.oversight_level.value}",
        article_reference="Article 14 - Human oversight"
    ))

    # 6. Safeguards (reduce risk)
    safeguard_reduction = 0.0
    if intake.can_users_opt_out:
        safeguard_reduction += 0.05
    if intake.appeal_mechanism:
        safeguard_reduction += 0.05

    if safeguard_reduction > 0:
        factors.append(RiskFactor(
            factor="safeguards",
            weight=-safeguard_reduction,
            description=f"Risk reduction from opt-out/appeal mechanisms",
            article_reference="Article 14 - Human oversight safeguards"
        ))

    # Calculate weighted score
    # Formula: weighted average of top factors, adjusted by oversight
    base_weights = [sector_weight, max_user_weight, max_data_weight, max_impact_weight]
    avg_base = sum(base_weights) / len(base_weights)

    # Apply oversight as additive reduction rather than multiplicative
    # This prevents high-risk systems from being incorrectly classified as low-risk
    # just because they have human oversight
    oversight_reduction = (1.0 - oversight_modifier) * 0.2  # Max 20% reduction
    risk_score = avg_base - oversight_reduction

    # Apply safeguard reduction
    risk_score = max(0.0, risk_score - safeguard_reduction)

    # Boost for special high-risk combinations
    if DataType.BIOMETRICS in intake.data_types and intake.sector == Sector.LAW_ENFORCEMENT:
        risk_score = min(1.0, risk_score + 0.15)
        factors.append(RiskFactor(
            factor="prohibited_combination",
            weight=0.15,
            description="Biometric identification in law enforcement context",
            article_reference="Article 5 - Prohibited AI practices"
        ))

    return min(1.0, max(0.0, risk_score)), factors


def compute_documentation_gaps(intake: AISystemIntake) -> List[str]:
    """Identify documentation gaps based on intake form."""
    gaps = []
    doc = intake.documentation

    required_docs = [
        ("data_sheet", "Data Sheet / Data Governance Documentation"),
        ("model_card", "Model Card / Technical Documentation"),
        ("risk_assessment", "Risk Assessment Documentation"),
        ("technical_documentation", "Technical System Documentation"),
    ]

    for field, name in required_docs:
        status = getattr(doc, field)
        if status in [DocumentationStatus.NOT_STARTED, DocumentationStatus.NEEDS_UPDATE]:
            gaps.append(name)

    # Additional gaps based on risk level
    if any(dt in intake.data_types for dt in [DataType.BIOMETRICS, DataType.HEALTH_DATA]):
        if doc.bias_audit != DocumentationStatus.COMPLETE:
            gaps.append("Bias Audit (required for sensitive data)")

    if intake.oversight_level == OversightLevel.FULLY_AUTOMATED:
        if doc.monitoring_dashboard != DocumentationStatus.COMPLETE:
            gaps.append("Monitoring Dashboard (required for automated systems)")

    return gaps


def generate_obligations(risk_score: float, intake: AISystemIntake) -> List[ComplianceObligation]:
    """Generate compliance obligations based on risk assessment."""
    obligations = []

    # High-risk obligations (score >= 0.6)
    if risk_score >= 0.6:
        obligations.extend([
            ComplianceObligation(
                id="OB-001",
                title="Risk Management System",
                description="Establish and maintain a risk management system throughout the AI system lifecycle",
                priority="high",
                status="required",
                article_reference="Article 9"
            ),
            ComplianceObligation(
                id="OB-002",
                title="Data Governance",
                description="Implement data governance practices for training, validation, and testing data",
                priority="high",
                status="required",
                article_reference="Article 10"
            ),
            ComplianceObligation(
                id="OB-003",
                title="Technical Documentation",
                description="Maintain comprehensive technical documentation demonstrating compliance",
                priority="high",
                status="required",
                article_reference="Article 11"
            ),
            ComplianceObligation(
                id="OB-004",
                title="Record-Keeping",
                description="Implement automatic logging of events for traceability",
                priority="high",
                status="required",
                article_reference="Article 12"
            ),
            ComplianceObligation(
                id="OB-005",
                title="Transparency",
                description="Ensure transparent operation and provide clear information to users",
                priority="high",
                status="required",
                article_reference="Article 13"
            ),
            ComplianceObligation(
                id="OB-006",
                title="Human Oversight",
                description="Design system to allow effective human oversight",
                priority="high",
                status="required",
                article_reference="Article 14"
            ),
            ComplianceObligation(
                id="OB-007",
                title="Accuracy & Robustness",
                description="Ensure appropriate levels of accuracy, robustness, and cybersecurity",
                priority="high",
                status="required",
                article_reference="Article 15"
            ),
        ])

    # Medium-risk obligations (score >= 0.4)
    if 0.4 <= risk_score < 0.6:
        obligations.extend([
            ComplianceObligation(
                id="OB-101",
                title="Transparency Obligations",
                description="Ensure users are informed when interacting with AI system",
                priority="medium",
                status="required",
                article_reference="Article 52"
            ),
            ComplianceObligation(
                id="OB-102",
                title="Documentation Best Practices",
                description="Maintain model cards and data sheets as best practice",
                priority="medium",
                status="recommended",
                article_reference="Best Practice"
            ),
        ])

    # Low-risk recommendations (score < 0.4)
    if risk_score < 0.4:
        obligations.append(ComplianceObligation(
            id="OB-201",
            title="Voluntary Code of Conduct",
            description="Consider adopting voluntary codes of conduct for trustworthy AI",
            priority="low",
            status="optional",
            article_reference="Article 69"
        ))

    # Specific obligations based on data types
    if DataType.BIOMETRICS in intake.data_types:
        obligations.append(ComplianceObligation(
            id="OB-BIO-001",
            title="Biometric Data Protection",
            description="Implement enhanced protections for biometric data processing",
            priority="high",
            status="required",
            article_reference="Article 6 - Annex III"
        ))

    if any(ut in intake.user_types for ut in [UserType.CHILDREN, UserType.VULNERABLE_GROUPS]):
        obligations.append(ComplianceObligation(
            id="OB-VUL-001",
            title="Vulnerable Population Safeguards",
            description="Implement additional safeguards for vulnerable user populations",
            priority="high",
            status="required",
            article_reference="Article 9(9)"
        ))

    return obligations


def generate_key_recommendations(risk_score: float, factors: List[RiskFactor], gaps: List[str]) -> List[str]:
    """Generate top priority recommendations."""
    recommendations = []

    # Based on risk score
    if risk_score >= 0.8:
        recommendations.append("URGENT: This system likely falls into high-risk category. Initiate full compliance assessment immediately.")
    elif risk_score >= 0.6:
        recommendations.append("HIGH PRIORITY: System requires comprehensive compliance documentation and risk management procedures.")
    elif risk_score >= 0.4:
        recommendations.append("MODERATE: Review transparency requirements and consider implementing best practices.")

    # Based on documentation gaps
    if gaps:
        recommendations.append(f"Complete missing documentation: {', '.join(gaps[:3])}")

    # Based on top risk factors
    top_factors = sorted(factors, key=lambda x: x.weight, reverse=True)[:2]
    for factor in top_factors:
        if factor.weight >= 0.7:
            recommendations.append(f"Address high-risk factor: {factor.description}")

    return recommendations[:5]  # Limit to top 5


def generate_executive_summary(
    intake: AISystemIntake,
    risk_score: float,
    risk_category: str,
    obligations: List[ComplianceObligation],
    recommendations: List[str] = None
) -> str:
    """Generate executive summary for leadership."""
    high_priority_count = len([o for o in obligations if o.priority == "high"])
    medium_priority_count = len([o for o in obligations if o.priority == "medium"])
    total_obligations = len(obligations)
    recommendation_count = len(recommendations) if recommendations else 0

    if risk_category == "high_risk":
        summary = (
            f"**{intake.system_name}** has been assessed as HIGH RISK under EU AI Act criteria. "
            f"The system's use of {intake.sector.value} applications affecting {', '.join([ut.value for ut in intake.user_types[:2]])} "
            f"triggers mandatory compliance requirements. "
            f"There are {high_priority_count} high-priority obligations requiring immediate attention. "
            f"Recommend initiating formal compliance review and engaging legal counsel."
        )
    elif risk_category == "medium_risk":
        summary = (
            f"**{intake.system_name}** has been assessed as MEDIUM RISK. "
            f"While not classified as high-risk under Annex III, the system should implement "
            f"transparency measures and documentation best practices. "
            f"There are {total_obligations} compliance obligations and {recommendation_count} recommended actions to improve compliance posture."
        )
    else:
        summary = (
            f"**{intake.system_name}** has been assessed as LOW RISK. "
            f"Minimal regulatory obligations apply, but consider adopting voluntary "
            f"codes of conduct and maintaining basic documentation for good governance. "
            f"There are {recommendation_count} suggested improvements."
        )

    return summary


def assess_intake_form(
    intake: AISystemIntake,
    ml_risk_score: float = None,
    remediation_items: List[Dict[str, Any]] = None
) -> IntakeAssessmentResponse:
    """
    Perform full assessment of an AI system intake form.

    Combines rule-based scoring with optional ML predictions.

    Args:
        intake: Structured intake form data
        ml_risk_score: Optional ML model prediction (0-1)
        remediation_items: Optional remediation items from template system

    Returns:
        Complete assessment response
    """
    # Compute rule-based risk score
    rule_score, factors = compute_base_risk_score(intake)

    # Combine with ML score if available (weighted average)
    if ml_risk_score is not None:
        # ML contributes 40%, rules contribute 60%
        final_score = 0.4 * ml_risk_score + 0.6 * rule_score
    else:
        final_score = rule_score

    # Determine risk category
    if final_score >= 0.6:
        risk_category = "high_risk"
        risk_label = "High Risk - Mandatory Compliance Required"
    elif final_score >= 0.4:
        risk_category = "medium_risk"
        risk_label = "Medium Risk - Compliance Recommended"
    else:
        risk_category = "low_risk"
        risk_label = "Low Risk - Minimal Obligations"

    # Generate assessments
    documentation_gaps = compute_documentation_gaps(intake)
    obligations = generate_obligations(final_score, intake)
    recommendations = generate_key_recommendations(final_score, factors, documentation_gaps)
    executive_summary = generate_executive_summary(intake, final_score, risk_category, obligations, recommendations)

    # Generate assessment ID
    assessment_id = hashlib.sha256(
        f"{intake.system_name}{intake.system_version}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:12]

    return IntakeAssessmentResponse(
        risk_score=round(final_score, 3),
        risk_category=risk_category,
        risk_label=risk_label,
        risk_factors=factors,
        obligations=obligations,
        documentation_gaps=documentation_gaps,
        key_recommendations=recommendations,
        remediation_items=remediation_items or [],
        assessment_id=assessment_id,
        assessment_timestamp=datetime.utcnow().isoformat(),
        model_version="1.0.0",
        executive_summary=executive_summary
    )

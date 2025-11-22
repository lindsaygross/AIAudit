"""
AIAudit - EU AI Act Compliance Assessment Tool

A clean, professional interface for assessing AI systems against EU AI Act requirements.
Design inspired by lovable.dev's minimal, sophisticated aesthetic.

Usage:
    streamlit run app/app.py
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, Optional

import requests
import streamlit as st

# Configuration
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

# EU AI Act Article Reference
EU_AI_ACT_ARTICLES = {
    "Article 5": "Prohibited AI Practices",
    "Article 6": "High-Risk Classification",
    "Article 9": "Risk Management System",
    "Article 10": "Data Governance",
    "Article 11": "Technical Documentation",
    "Article 12": "Record-Keeping",
    "Article 13": "Transparency",
    "Article 14": "Human Oversight",
    "Article 15": "Accuracy & Robustness"
}

# Page config
st.set_page_config(
    page_title="AIAudit",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, clean CSS inspired by lovable.dev
st.markdown("""
<style>
    /* Import clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Reset and base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main app background - clean white */
    .stApp {
        background-color: #FAFAFA;
    }

    /* Main container */
    .main .block-container {
        max-width: 900px;
        padding: 2rem 1rem 4rem 1rem;
        margin: 0 auto;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Typography */
    h1 {
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        margin-bottom: 0.25rem !important;
    }

    h2 {
        color: #111827 !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    p, span, label, .stMarkdown {
        color: #374151 !important;
    }

    /* Subtitle styling */
    .subtitle {
        color: #6B7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Card component */
    .card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .card-header {
        font-weight: 600;
        color: #111827;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
    }

    /* Score display */
    .score-container {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0;
    }

    .score-value {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .score-high { color: #DC2626; }
    .score-medium { color: #D97706; }
    .score-low { color: #059669; }

    .score-label {
        display: inline-block;
        padding: 0.375rem 1rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .label-high {
        background: #FEE2E2;
        color: #DC2626;
    }

    .label-medium {
        background: #FEF3C7;
        color: #D97706;
    }

    .label-low {
        background: #D1FAE5;
        color: #059669;
    }

    /* Article violation cards */
    .violation-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }

    .violation-card.high {
        border-left: 4px solid #DC2626;
    }

    .violation-card.medium {
        border-left: 4px solid #D97706;
    }

    .violation-card.low {
        border-left: 4px solid #059669;
    }

    .violation-content {
        flex: 1;
    }

    .violation-title {
        font-weight: 600;
        color: #111827;
        font-size: 0.9375rem;
        margin-bottom: 0.25rem;
    }

    .violation-description {
        color: #6B7280;
        font-size: 0.8125rem;
        line-height: 1.5;
    }

    .violation-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.625rem;
        border-radius: 4px;
        white-space: nowrap;
    }

    .badge-high {
        background: #FEE2E2;
        color: #DC2626;
    }

    .badge-medium {
        background: #FEF3C7;
        color: #D97706;
    }

    .badge-low {
        background: #D1FAE5;
        color: #059669;
    }

    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        color: #111827 !important;
        font-size: 0.9375rem !important;
        padding: 0.75rem 1rem !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9CA3AF !important;
    }

    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stMultiSelect > label,
    .stRadio > label {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.375rem !important;
    }

    /* Select boxes */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }

    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        color: #111827 !important;
    }

    /* Radio buttons */
    .stRadio > div {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stRadio > div > label {
        color: #374151 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 6px !important;
        margin: 0.25rem 0 !important;
    }

    .stRadio > div > label:hover {
        background: #F9FAFB !important;
    }

    .stRadio > div > label[data-checked="true"] {
        background: #EEF2FF !important;
    }

    /* Checkboxes */
    .stCheckbox > label {
        color: #374151 !important;
    }

    /* Primary button */
    .stButton > button {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    .stButton > button:hover {
        background: #4338CA !important;
        box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2) !important;
        transform: translateY(-1px);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Download button */
    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    .stDownloadButton > button:hover {
        background: #F9FAFB !important;
        border-color: #9CA3AF !important;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 2rem 0;
    }

    /* Status indicator */
    .status-online {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        color: #059669;
        font-size: 0.8125rem;
        font-weight: 500;
    }

    .status-online::before {
        content: '';
        width: 8px;
        height: 8px;
        background: #059669;
        border-radius: 50%;
    }

    .status-offline {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        color: #DC2626;
        font-size: 0.8125rem;
        font-weight: 500;
    }

    .status-offline::before {
        content: '';
        width: 8px;
        height: 8px;
        background: #DC2626;
        border-radius: 50%;
    }

    /* Summary box */
    .summary-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1.25rem;
        color: #374151;
        font-size: 0.9375rem;
        line-height: 1.6;
    }

    /* List styling */
    .action-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #F3F4F6;
        color: #374151;
        font-size: 0.9375rem;
    }

    .action-item:last-child {
        border-bottom: none;
    }

    .action-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 1.5rem;
        height: 1.5rem;
        background: #EEF2FF;
        color: #4F46E5;
        border-radius: 50%;
        font-size: 0.75rem;
        font-weight: 600;
        flex-shrink: 0;
    }

    /* Section spacing */
    .section {
        margin-top: 2rem;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #4F46E5 !important;
    }

    /* Form container */
    [data-testid="stForm"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def assess_intake(intake_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Submit intake form for assessment."""
    try:
        response = requests.post(
            f"{API_URL}/assess_intake",
            json=intake_data,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


def render_header():
    """Render the application header."""
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown("# AIAudit")
        st.markdown('<p class="subtitle">EU AI Act Compliance Assessment</p>', unsafe_allow_html=True)

    with col2:
        api_online = check_api_health()
        if api_online:
            st.markdown('<span class="status-online">System Online</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-offline">System Offline</span>', unsafe_allow_html=True)


def render_intake_form() -> Optional[Dict[str, Any]]:
    """Render the intake assessment form."""

    with st.form("assessment_form", clear_on_submit=False):
        # System Information Section
        st.markdown("## System Information")

        col1, col2 = st.columns(2)
        with col1:
            system_name = st.text_input(
                "AI System Name",
                placeholder="e.g., Resume Screening Tool"
            )
        with col2:
            team_name = st.text_input(
                "Team / Department",
                placeholder="e.g., HR Technology"
            )

        # Scope Section
        st.markdown("## Scope")

        sector = st.selectbox(
            "What sector does this AI system operate in?",
            options=[
                "hiring",
                "credit_scoring",
                "healthcare",
                "education",
                "law_enforcement",
                "critical_infrastructure",
                "insurance",
                "social_services",
                "recommender",
                "customer_service",
                "manufacturing",
                "logistics",
                "other"
            ],
            format_func=lambda x: {
                "hiring": "Hiring / Recruitment",
                "credit_scoring": "Credit Scoring / Financial",
                "healthcare": "Healthcare / Medical",
                "education": "Education",
                "law_enforcement": "Law Enforcement / Security",
                "critical_infrastructure": "Critical Infrastructure",
                "insurance": "Insurance",
                "social_services": "Social Services / Benefits",
                "recommender": "Recommendations / Content",
                "customer_service": "Customer Service",
                "manufacturing": "Manufacturing / Industrial",
                "logistics": "Logistics / Supply Chain",
                "other": "Other"
            }.get(x, x)
        )

        use_case = st.text_area(
            "Describe what your AI system does",
            placeholder="Briefly describe the purpose, functionality, and how decisions are made...",
            height=100
        )

        # Data Section
        st.markdown("## Data Collection")

        data_types = st.multiselect(
            "What types of data does the system process?",
            options=[
                "biometrics",
                "health_data",
                "financial_data",
                "criminal_records",
                "political_opinions",
                "religious_beliefs",
                "ethnic_origin",
                "location_data",
                "behavioral_data",
                "employment_data",
                "educational_records",
                "generic_pii",
                "anonymous_data"
            ],
            default=["generic_pii"],
            format_func=lambda x: {
                "biometrics": "Biometric Data (face, fingerprint, voice)",
                "health_data": "Health / Medical Data",
                "financial_data": "Financial Data",
                "criminal_records": "Criminal Records",
                "political_opinions": "Political Opinions",
                "religious_beliefs": "Religious Beliefs",
                "ethnic_origin": "Ethnic Origin",
                "location_data": "Location Data",
                "behavioral_data": "Behavioral / Usage Data",
                "employment_data": "Employment Data",
                "educational_records": "Educational Records",
                "generic_pii": "Generic Personal Information",
                "anonymous_data": "Anonymous / Aggregated Data Only"
            }.get(x, x)
        )

        # Impact Section
        st.markdown("## Impact Assessment")

        col1, col2 = st.columns(2)

        with col1:
            user_types = st.multiselect(
                "Who are the affected users?",
                options=[
                    "general_public",
                    "employees",
                    "children",
                    "elderly",
                    "vulnerable_groups",
                    "patients",
                    "students",
                    "consumers"
                ],
                default=["general_public"],
                format_func=lambda x: {
                    "general_public": "General Public",
                    "employees": "Employees",
                    "children": "Children (under 18)",
                    "elderly": "Elderly",
                    "vulnerable_groups": "Vulnerable Groups",
                    "patients": "Patients",
                    "students": "Students",
                    "consumers": "Consumers"
                }.get(x, x)
            )

        with col2:
            decision_impacts = st.multiselect(
                "What decisions does the system influence?",
                options=[
                    "employment_decisions",
                    "credit_decisions",
                    "access_to_services",
                    "educational_outcomes",
                    "health_treatment",
                    "legal_decisions",
                    "law_enforcement_actions",
                    "safety_critical",
                    "recommendations",
                    "operational_efficiency"
                ],
                default=["recommendations"],
                format_func=lambda x: {
                    "employment_decisions": "Employment Decisions",
                    "credit_decisions": "Credit / Loan Decisions",
                    "access_to_services": "Access to Services",
                    "educational_outcomes": "Educational Outcomes",
                    "health_treatment": "Health Treatment",
                    "legal_decisions": "Legal / Court Decisions",
                    "law_enforcement_actions": "Law Enforcement Actions",
                    "safety_critical": "Safety-Critical Operations",
                    "recommendations": "Recommendations Only",
                    "operational_efficiency": "Internal Operations Only"
                }.get(x, x)
            )

        # Oversight Section
        st.markdown("## Human Oversight")

        oversight_level = st.radio(
            "What level of human oversight exists?",
            options=[
                "fully_automated",
                "human_on_the_loop",
                "human_in_the_loop",
                "human_override_possible",
                "human_final_decision"
            ],
            index=2,
            format_func=lambda x: {
                "fully_automated": "Fully Automated - No human review",
                "human_on_the_loop": "Human monitors but system acts autonomously",
                "human_in_the_loop": "Human reviews before each decision",
                "human_override_possible": "Human can override any decision",
                "human_final_decision": "Human makes all final decisions"
            }.get(x, x)
        )

        col1, col2 = st.columns(2)
        with col1:
            can_opt_out = st.checkbox("Users can opt out of AI processing")
        with col2:
            has_appeal = st.checkbox("Appeal mechanism exists for decisions")

        # Submit
        st.markdown("")  # Spacing
        submitted = st.form_submit_button("Assess Compliance", use_container_width=True)

        if submitted:
            if not system_name:
                st.error("Please provide a system name")
                return None
            if not use_case or len(use_case) < 20:
                st.error("Please provide a detailed use case description (at least 20 characters)")
                return None

            return {
                "system_name": system_name,
                "system_version": "1.0.0",
                "team_name": team_name or "Not specified",
                "project_owner": "assessment@company.com",
                "sector": sector,
                "use_case_description": use_case,
                "user_types": user_types,
                "data_types": data_types,
                "decision_impacts": decision_impacts,
                "oversight_level": oversight_level,
                "can_users_opt_out": can_opt_out,
                "appeal_mechanism": has_appeal,
                "documentation": {
                    "data_sheet": "not_started",
                    "model_card": "not_started",
                    "system_logs": "not_started",
                    "monitoring_dashboard": "not_started",
                    "risk_assessment": "not_started",
                    "bias_audit": "not_started",
                    "technical_documentation": "not_started",
                    "user_instructions": "not_started"
                }
            }

    return None


def render_results(result: Dict[str, Any]):
    """Render the assessment results."""

    st.markdown("---")

    # Score Section
    risk_score = result.get("risk_score", 0.5)
    risk_category = result.get("risk_category", "medium_risk")
    risk_percentage = int(risk_score * 100)

    if risk_category == "high_risk":
        score_class = "score-high"
        label_class = "label-high"
        label_text = "HIGH RISK"
    elif risk_category == "medium_risk":
        score_class = "score-medium"
        label_class = "label-medium"
        label_text = "MEDIUM RISK"
    else:
        score_class = "score-low"
        label_class = "label-low"
        label_text = "LOW RISK"

    st.markdown(f"""
    <div class="score-container">
        <div class="score-value {score_class}">{risk_percentage}%</div>
        <span class="score-label {label_class}">{label_text}</span>
    </div>
    """, unsafe_allow_html=True)

    # Summary
    st.markdown("## Summary")
    summary = result.get("executive_summary", "Assessment complete.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    # Article Violations
    st.markdown("## EU AI Act Article Analysis")

    risk_factors = result.get("risk_factors", [])
    obligations = result.get("obligations", [])

    # Collect all article-related findings
    findings = []

    for factor in risk_factors:
        weight = factor.get("weight", 0)
        if weight < 0:  # Skip negative weights (safeguards)
            continue
        article_ref = factor.get("article_reference", "")
        description = factor.get("description", "")

        if weight >= 0.7:
            severity = "high"
        elif weight >= 0.4:
            severity = "medium"
        else:
            severity = "low"

        findings.append({
            "article": article_ref,
            "description": description,
            "severity": severity,
            "score": int(weight * 100)
        })

    for ob in obligations:
        if ob.get("priority") == "high":
            findings.append({
                "article": ob.get("article_reference", ""),
                "description": f"{ob.get('title', '')}: {ob.get('description', '')}",
                "severity": "high",
                "score": 80
            })

    # Sort by severity then score
    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda x: (severity_order.get(x["severity"], 2), -x["score"]))

    # Display findings
    if findings:
        for finding in findings[:8]:  # Limit to top 8
            severity = finding["severity"]
            st.markdown(f"""
            <div class="violation-card {severity}">
                <div class="violation-content">
                    <div class="violation-title">{finding["article"]}</div>
                    <div class="violation-description">{finding["description"]}</div>
                </div>
                <span class="violation-badge badge-{severity}">{finding["score"]}%</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific article violations identified.")

    # Required Actions
    recommendations = result.get("key_recommendations", [])
    if recommendations:
        st.markdown("## Required Actions")

        actions_html = '<div class="action-list">'
        for i, rec in enumerate(recommendations, 1):
            actions_html += f'''
            <div class="action-item">
                <span class="action-number">{i}</span>
                <span>{rec}</span>
            </div>
            '''
        actions_html += '</div>'

        st.markdown(actions_html, unsafe_allow_html=True)

    # Documentation Gaps
    gaps = result.get("documentation_gaps", [])
    if gaps:
        st.markdown("## Missing Documentation")
        for gap in gaps:
            st.markdown(f"- {gap}")

    # Actions
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.download_button(
            "Download Report",
            json.dumps(result, indent=2),
            f"ai_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )

    with col3:
        if st.button("New Assessment", use_container_width=True):
            st.rerun()


def main():
    """Main application."""
    render_header()
    st.markdown("---")

    intake_data = render_intake_form()

    if intake_data:
        with st.spinner("Analyzing compliance..."):
            result = assess_intake(intake_data)
            if result:
                render_results(result)


if __name__ == "__main__":
    main()

"""
AIAudit - EU AI Act Compliance Assessment Tool

A clean, professional interface for assessing AI systems against EU AI Act requirements.
Modern white design inspired by Linear, Vercel, and Stripe dashboards.

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

# Page config
st.set_page_config(
    page_title="AIAudit - EU AI Act Compliance",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, clean CSS - White background with floating cards
st.markdown("""
<style>
    /* Import clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Reset and base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Main app background - Clean white */
    .stApp {
        background: #FFFFFF;
    }

    /* Main container */
    .main .block-container {
        max-width: 900px;
        padding: 2rem 2rem;
        margin: 0 auto;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}

    /* Typography */
    h1 {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
        margin-bottom: 0.25rem !important;
        letter-spacing: -0.02em !important;
    }

    h2 {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    h3 {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Subtitle styling */
    .subtitle {
        color: #666666 !important;
        font-size: 0.9375rem !important;
        font-weight: 400 !important;
        margin-bottom: 1.5rem !important;
    }

    /* Top nav bar */
    .nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 2rem;
    }

    .nav-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #1a1a1a;
    }

    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #FFFFFF;
        color: #666666;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid #e5e5e5;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        background: #22c55e;
        border-radius: 50%;
    }

    .status-offline .status-dot {
        background: #ef4444;
    }

    /* Floating card styles */
    .card {
        background: #FFFFFF;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .card-header {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f0f0f0;
    }

    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: #FFFFFF !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 8px !important;
        color: #1a1a1a !important;
        font-size: 0.875rem !important;
        padding: 0.625rem 0.875rem !important;
        transition: all 0.15s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9ca3af !important;
    }

    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stMultiSelect > label,
    .stRadio > label,
    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.8125rem !important;
        margin-bottom: 0.375rem !important;
    }

    /* Radio buttons */
    .stRadio > div {
        gap: 0.375rem;
    }

    .stRadio > div > label {
        background: #FFFFFF !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 8px !important;
        padding: 0.625rem 0.875rem !important;
        margin: 0.125rem 0 !important;
        color: #374151 !important;
        font-size: 0.8125rem !important;
        transition: all 0.15s ease !important;
    }

    .stRadio > div > label:hover {
        background: #f9fafb !important;
        border-color: #3b82f6 !important;
    }

    /* Checkboxes */
    .stCheckbox {
        margin-top: 0.375rem;
    }

    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 400 !important;
        font-size: 0.8125rem !important;
    }

    /* Primary button */
    .stButton > button {
        background: #3b82f6 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    .stButton > button:hover {
        background: #2563eb !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2) !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 8px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
    }

    .stDownloadButton > button:hover {
        background: #f9fafb !important;
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
    }

    /* Score display */
    .score-container {
        background: #FFFFFF;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 2rem 1.5rem;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .score-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.75rem;
        color: #3b82f6;
    }

    .score-value.high-risk {
        color: #ef4444;
    }

    .score-value.medium-risk {
        color: #f59e0b;
    }

    .score-value.low-risk {
        color: #22c55e;
    }

    .score-label {
        display: inline-block;
        padding: 0.375rem 1rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .label-high {
        background: #fef2f2;
        color: #dc2626;
    }

    .label-medium {
        background: #fffbeb;
        color: #d97706;
    }

    .label-low {
        background: #f0fdf4;
        color: #16a34a;
    }

    /* Summary box */
    .summary-box {
        background: #f9fafb;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        color: #374151;
        font-size: 0.875rem;
        line-height: 1.6;
        margin: 1rem 0;
    }

    /* Violation cards */
    .violation-card {
        background: #FFFFFF;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        transition: all 0.15s ease;
    }

    .violation-card:hover {
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }

    .violation-card.high {
        border-left: 3px solid #ef4444;
    }

    .violation-card.medium {
        border-left: 3px solid #f59e0b;
    }

    .violation-card.low {
        border-left: 3px solid #22c55e;
    }

    .violation-content {
        flex: 1;
    }

    .violation-title {
        font-weight: 600;
        color: #1a1a1a;
        font-size: 0.875rem;
        margin-bottom: 0.25rem;
    }

    .violation-description {
        color: #666666;
        font-size: 0.8125rem;
        line-height: 1.5;
    }

    .violation-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.375rem 0.625rem;
        border-radius: 6px;
        white-space: nowrap;
        min-width: 48px;
        text-align: center;
    }

    .badge-high {
        background: #fef2f2;
        color: #dc2626;
    }

    .badge-medium {
        background: #fffbeb;
        color: #d97706;
    }

    .badge-low {
        background: #f0fdf4;
        color: #16a34a;
    }

    /* Action list */
    .action-list {
        list-style: none;
        padding: 0;
        margin: 0.75rem 0;
    }

    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f0f0f0;
        color: #374151;
        font-size: 0.8125rem;
        line-height: 1.5;
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
        background: #3b82f6;
        color: #FFFFFF;
        border-radius: 50%;
        font-size: 0.75rem;
        font-weight: 600;
        flex-shrink: 0;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #e5e5e5;
        margin: 1.5rem 0;
    }

    /* Form container */
    [data-testid="stForm"] {
        background: transparent;
        border: none;
        padding: 0;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }

    /* Info cards */
    .info-card {
        background: #f9fafb;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #374151;
        font-size: 0.8125rem;
        line-height: 1.5;
        margin: 0.5rem 0;
    }

    /* Select dropdown text */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] div {
        color: #1a1a1a !important;
    }

    /* Multi-select tags */
    [data-baseweb="tag"] {
        background-color: #eff6ff !important;
        color: #1d4ed8 !important;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1.5rem 1rem;
        }

        h1 {
            font-size: 1.5rem !important;
        }

        .score-value {
            font-size: 2.5rem;
        }

        .card {
            padding: 1.25rem;
        }
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
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("# AIAudit")
        st.markdown('<p class="subtitle">EU AI Act Compliance Assessment</p>', unsafe_allow_html=True)

    with col2:
        api_online = check_api_health()
        status_class = "status-badge" if api_online else "status-badge status-offline"
        status_text = "Online" if api_online else "Offline"
        st.markdown(f'''
        <div class="{status_class}">
            <span class="status-dot"></span>
            <span>{status_text}</span>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")


def render_intake_form() -> Optional[Dict[str, Any]]:
    """Render the intake assessment form."""

    with st.form("assessment_form", clear_on_submit=False):
        # System Information Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## System Information")

        col1, col2 = st.columns(2)
        with col1:
            system_name = st.text_input(
                "AI System Name",
                value="",
                placeholder="Enter system name",
                help="The name of your AI system"
            )
        with col2:
            team_name = st.text_input(
                "Team / Department",
                value="Engineering",
                placeholder="e.g., HR Technology",
                help="The team responsible for this system"
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Scope Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
            index=0,
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
            value="",
            placeholder="Briefly describe the purpose and functionality...",
            height=100,
            help="Provide details about the system's purpose and decision-making process"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Data Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
                "biometrics": "Biometric Data",
                "health_data": "Health / Medical Data",
                "financial_data": "Financial Data",
                "criminal_records": "Criminal Records",
                "political_opinions": "Political Opinions",
                "religious_beliefs": "Religious Beliefs",
                "ethnic_origin": "Ethnic Origin",
                "location_data": "Location Data",
                "behavioral_data": "Behavioral Data",
                "employment_data": "Employment Data",
                "educational_records": "Educational Records",
                "generic_pii": "Generic Personal Information",
                "anonymous_data": "Anonymous Data Only"
            }.get(x, x),
            help="Select all data types that apply"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Impact Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
                default=["employees"],
                format_func=lambda x: {
                    "general_public": "General Public",
                    "employees": "Employees",
                    "children": "Children",
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
                default=["employment_decisions"],
                format_func=lambda x: {
                    "employment_decisions": "Employment Decisions",
                    "credit_decisions": "Credit / Loan Decisions",
                    "access_to_services": "Access to Services",
                    "educational_outcomes": "Educational Outcomes",
                    "health_treatment": "Health Treatment",
                    "legal_decisions": "Legal Decisions",
                    "law_enforcement_actions": "Law Enforcement",
                    "safety_critical": "Safety-Critical",
                    "recommendations": "Recommendations Only",
                    "operational_efficiency": "Internal Operations"
                }.get(x, x)
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Oversight Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
            }.get(x, x),
            help="Select the level of human involvement in decisions"
        )

        col1, col2 = st.columns(2)
        with col1:
            can_opt_out = st.checkbox("Users can opt out of AI processing", value=True)
        with col2:
            has_appeal = st.checkbox("Appeal mechanism exists for decisions", value=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Submit
        st.markdown("")
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

    # Score Section
    risk_score = result.get("risk_score", 0.5)
    risk_category = result.get("risk_category", "medium_risk")
    risk_percentage = int(risk_score * 100)

    if risk_category == "high_risk":
        score_class = "high-risk"
        label_class = "label-high"
        label_text = "HIGH RISK"
    elif risk_category == "medium_risk":
        score_class = "medium-risk"
        label_class = "label-medium"
        label_text = "MEDIUM RISK"
    else:
        score_class = "low-risk"
        label_class = "label-low"
        label_text = "LOW RISK"

    st.markdown(f"""
    <div class="score-container">
        <div class="score-value {score_class}">{risk_percentage}</div>
        <span class="score-label {label_class}">{label_text}</span>
    </div>
    """, unsafe_allow_html=True)

    # Summary
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## Executive Summary")
    summary = result.get("executive_summary", "Assessment complete.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Article Violations
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## EU AI Act Article Analysis")

    risk_factors = result.get("risk_factors", [])
    obligations = result.get("obligations", [])

    findings = []

    for factor in risk_factors:
        weight = factor.get("weight", 0)
        if weight < 0:
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

    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda x: (severity_order.get(x["severity"], 2), -x["score"]))

    if findings:
        for finding in findings[:8]:
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
        st.markdown('<div class="info-card">No specific article violations identified.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Required Actions
    recommendations = result.get("key_recommendations", [])
    if recommendations:
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

    # Documentation Gaps
    gaps = result.get("documentation_gaps", [])
    if gaps:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## Missing Documentation")
        for gap in gaps:
            st.markdown(f'<div class="info-card">{gap}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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

    intake_data = render_intake_form()

    if intake_data:
        with st.spinner("Analyzing compliance..."):
            result = assess_intake(intake_data)
            if result:
                render_results(result)


if __name__ == "__main__":
    main()

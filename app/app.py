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

# Page config
st.set_page_config(
    page_title="AIAudit - EU AI Act Compliance",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, clean CSS inspired by lovable.dev
st.markdown("""
<style>
    /* Import clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Reset and base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Main container */
    .main .block-container {
        max-width: 1200px;
        padding: 3rem 2rem;
        margin: 0 auto;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}

    /* Typography - Light text on dark gradient background */
    h1 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em !important;
    }

    h2 {
        color: #1F2937 !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    /* Subtitle styling - Light text for header area */
    .subtitle {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1.125rem !important;
        font-weight: 400 !important;
        margin-bottom: 2rem !important;
    }

    /* Status badge in header */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        color: #FFFFFF;
        padding: 0.5rem 1rem;
        border-radius: 24px;
        font-size: 0.875rem;
        font-weight: 500;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .status-offline .status-dot {
        background: #EF4444;
    }

    /* Main content card */
    .content-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 2.5rem;
        margin-top: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    }

    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: #F9FAFB !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 10px !important;
        color: #111827 !important;
        font-size: 0.9375rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        background: #FFFFFF !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9CA3AF !important;
    }

    /* Labels - Dark text on white background */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stMultiSelect > label,
    .stRadio > label,
    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.9375rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Radio buttons */
    .stRadio > div {
        gap: 0.5rem;
    }

    .stRadio > div > label {
        background: #F9FAFB !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 10px !important;
        padding: 0.875rem 1rem !important;
        margin: 0.25rem 0 !important;
        color: #374151 !important;
        transition: all 0.2s ease !important;
    }

    .stRadio > div > label:hover {
        background: #F3F4F6 !important;
        border-color: #667eea !important;
    }

    .stRadio > div > label[data-checked="true"] {
        background: #EEF2FF !important;
        border-color: #667eea !important;
        color: #4338CA !important;
    }

    /* Checkboxes */
    .stCheckbox {
        margin-top: 0.5rem;
    }

    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 400 !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"],
    .stButton > button:not([kind]) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind]):hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }

    .stButton > button[kind="primary"]:active,
    .stButton > button:not([kind]):active {
        transform: translateY(0);
    }

    /* Download button */
    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #374151 !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 10px !important;
        padding: 0.875rem 2rem !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stDownloadButton > button:hover {
        background: #F9FAFB !important;
        border-color: #667eea !important;
        color: #667eea !important;
    }

    /* Score display */
    .score-container {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border: 2px solid #E5E7EB;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }

    .score-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

    .score-value {
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-value.high-risk {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-value.medium-risk {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-value.low-risk {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-label {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 24px;
        font-size: 0.875rem;
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

    /* Summary box */
    .summary-box {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border: 1.5px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        color: #374151;
        font-size: 1rem;
        line-height: 1.7;
        margin: 1.5rem 0;
    }

    /* Article violation cards */
    .violation-card {
        background: #FFFFFF;
        border: 1.5px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        transition: all 0.2s ease;
    }

    .violation-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }

    .violation-card.high {
        border-left: 4px solid #EF4444;
        background: linear-gradient(90deg, #FEF2F2 0%, #FFFFFF 100%);
    }

    .violation-card.medium {
        border-left: 4px solid #F59E0B;
        background: linear-gradient(90deg, #FFFBEB 0%, #FFFFFF 100%);
    }

    .violation-card.low {
        border-left: 4px solid #10B981;
        background: linear-gradient(90deg, #ECFDF5 0%, #FFFFFF 100%);
    }

    .violation-content {
        flex: 1;
    }

    .violation-title {
        font-weight: 600;
        color: #111827;
        font-size: 1rem;
        margin-bottom: 0.375rem;
    }

    .violation-description {
        color: #6B7280;
        font-size: 0.875rem;
        line-height: 1.6;
    }

    .violation-badge {
        font-size: 0.875rem;
        font-weight: 700;
        padding: 0.5rem 0.875rem;
        border-radius: 8px;
        white-space: nowrap;
        min-width: 60px;
        text-align: center;
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

    /* Action list */
    .action-list {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }

    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem;
        border-bottom: 1px solid #F3F4F6;
        color: #374151;
        font-size: 0.9375rem;
        line-height: 1.6;
    }

    .action-item:last-child {
        border-bottom: none;
    }

    .action-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #FFFFFF;
        border-radius: 50%;
        font-size: 0.875rem;
        font-weight: 600;
        flex-shrink: 0;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1.5px solid rgba(255, 255, 255, 0.3);
        margin: 2rem 0;
    }

    .content-card hr {
        border-top: 1.5px solid #E5E7EB;
    }

    /* Form container */
    [data-testid="stForm"] {
        background: transparent;
        border: none;
        padding: 0;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
    }

    .section-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.125rem;
    }

    /* Info cards */
    .info-card {
        background: #F9FAFB;
        border: 1.5px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        color: #374151;
        font-size: 0.875rem;
        line-height: 1.6;
        margin: 1rem 0;
    }

    .info-card strong {
        color: #111827;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 2rem 1rem;
        }

        h1 {
            font-size: 2rem !important;
        }

        .score-value {
            font-size: 3rem;
        }

        .content-card {
            padding: 1.5rem;
        }
    }

    /* Select dropdown text - ensure dark text */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] div {
        color: #111827 !important;
    }

    /* Multi-select tags */
    [data-baseweb="tag"] {
        background-color: #EEF2FF !important;
        color: #4338CA !important;
    }

    /* Ensure all text in white cards is dark */
    .content-card p,
    .content-card span,
    .content-card div {
        color: #374151;
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
        status_text = "System Online" if api_online else "System Offline"
        st.markdown(f'''
        <div class="{status_class}">
            <span class="status-dot"></span>
            <span>{status_text}</span>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")


def render_intake_form() -> Optional[Dict[str, Any]]:
    """Render the intake assessment form."""

    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    with st.form("assessment_form", clear_on_submit=False):
        # System Information Section
        st.markdown("## 📋 System Information")

        col1, col2 = st.columns(2)
        with col1:
            system_name = st.text_input(
                "AI System Name",
                placeholder="e.g., Resume Screening Tool",
                help="The name of your AI system"
            )
        with col2:
            team_name = st.text_input(
                "Team / Department",
                placeholder="e.g., HR Technology",
                help="The team responsible for this system"
            )

        # Scope Section
        st.markdown("## 🎯 Scope")

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
            height=120,
            help="Provide details about the system's purpose and decision-making process"
        )

        # Data Section
        st.markdown("## 🔒 Data Collection")

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
            }.get(x, x),
            help="Select all data types that apply"
        )

        # Impact Section
        st.markdown("## 👥 Impact Assessment")

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
        st.markdown("## 👤 Human Oversight")

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
            can_opt_out = st.checkbox("Users can opt out of AI processing")
        with col2:
            has_appeal = st.checkbox("Appeal mechanism exists for decisions")

        # Submit
        st.markdown("")  # Spacing
        submitted = st.form_submit_button("🔍 Assess Compliance", use_container_width=True)

        if submitted:
            if not system_name:
                st.error("⚠️ Please provide a system name")
                return None
            if not use_case or len(use_case) < 20:
                st.error("⚠️ Please provide a detailed use case description (at least 20 characters)")
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

    st.markdown('</div>', unsafe_allow_html=True)
    return None


def render_results(result: Dict[str, Any]):
    """Render the assessment results."""

    st.markdown('<div class="content-card">', unsafe_allow_html=True)

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
    st.markdown("## 📊 Executive Summary")
    summary = result.get("executive_summary", "Assessment complete.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    # Article Violations
    st.markdown("## ⚖️ EU AI Act Article Analysis")

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
        st.markdown('<div class="info-card">✅ No specific article violations identified.</div>', unsafe_allow_html=True)

    # Required Actions
    recommendations = result.get("key_recommendations", [])
    if recommendations:
        st.markdown("## ✅ Required Actions")

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
        st.markdown("## 📄 Missing Documentation")
        for gap in gaps:
            st.markdown(f'<div class="info-card">⚠️ {gap}</div>', unsafe_allow_html=True)

    # Actions
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.download_button(
            "📥 Download Report",
            json.dumps(result, indent=2),
            f"ai_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )

    with col3:
        if st.button("🔄 New Assessment", use_container_width=True):
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application."""
    render_header()

    intake_data = render_intake_form()

    if intake_data:
        with st.spinner("🔍 Analyzing compliance..."):
            result = assess_intake(intake_data)
            if result:
                render_results(result)


if __name__ == "__main__":
    main()

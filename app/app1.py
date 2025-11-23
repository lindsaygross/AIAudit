"""
AIAudit - EU AI Act Compliance Assessment Tool
Beautiful, modern interface with polished design.
Developed with assistance from Claude (Anthropic AI).
"""

import os
import json
import random
from datetime import datetime
from typing import Any, Dict, Optional

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AIAudit - EU AI Act Compliance",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional gradient backgrounds (blues, greens, teals - no pink/yellow)
GRADIENTS = [
    "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 30%, #ffffff 100%)",  # Green
    "linear-gradient(135deg, #eff6ff 0%, #dbeafe 30%, #ffffff 100%)",  # Blue
    "linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 30%, #ffffff 100%)",  # Teal
    "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 30%, #ffffff 100%)",  # Subtle purple
    "linear-gradient(135deg, #ecfeff 0%, #cffafe 30%, #ffffff 100%)",  # Cyan
]

if 'gradient' not in st.session_state:
    st.session_state.gradient = random.choice(GRADIENTS)

gradient = st.session_state.gradient

# Beautiful CSS with animations and polish
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800;900&display=swap');

/* Global styles */
*, *::before, *::after {{
    font-family: 'Barlow', -apple-system, BlinkMacSystemFont, sans-serif !important;
    box-sizing: border-box;
}}

html, body, [class*="css"] {{
    font-family: 'Barlow', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Gradient background */
.stApp {{
    background: {gradient} !important;
    min-height: 100vh;
}}

.main .block-container {{
    max-width: 920px;
    padding: 48px 24px 100px 24px;
    margin: 0 auto;
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {{
    display: none !important;
}}

/* Typography */
h1, .stMarkdown h1 {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 48px !important;
    font-weight: 800 !important;
    color: #1a1a1a !important;
    letter-spacing: -1.5px !important;
    line-height: 1.1 !important;
}}

h2, .stMarkdown h2 {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
    letter-spacing: -0.5px !important;
    margin: 28px 0 14px 0 !important;
}}

h3, .stMarkdown h3 {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
    margin: 20px 0 10px 0 !important;
}}

p, .stMarkdown p {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 16px !important;
    color: #4b5563 !important;
    line-height: 1.6 !important;
}}

/* Form labels */
.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stMultiSelect > label,
.stRadio > label {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #374151 !important;
    margin-bottom: 6px !important;
}}

/* Input fields with nice focus states */
.stTextInput input {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 15px !important;
    background: white !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    color: #1a1a1a !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}}

.stTextInput input:focus {{
    border-color: #22c55e !important;
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12), 0 1px 2px rgba(0,0,0,0.04) !important;
    outline: none !important;
}}

.stTextInput input::placeholder {{
    color: #9ca3af !important;
}}

/* Text area */
.stTextArea textarea {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 15px !important;
    background: white !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    color: #1a1a1a !important;
    min-height: 120px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}}

.stTextArea textarea:focus {{
    border-color: #22c55e !important;
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12), 0 1px 2px rgba(0,0,0,0.04) !important;
}}

/* Select boxes */
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    font-family: 'Barlow', sans-serif !important;
    background: white !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}}

.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div,
.stMultiSelect [data-baseweb="select"] span {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 15px !important;
    color: #1a1a1a !important;
}}

/* Multi-select tags */
.stMultiSelect [data-baseweb="tag"] {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    background: #dcfce7 !important;
    color: #166534 !important;
    border-radius: 8px !important;
    padding: 4px 10px !important;
}}

/* Radio buttons - card style */
.stRadio > div {{
    gap: 10px !important;
}}

.stRadio > div > label {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    background: white !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    margin: 0 !important;
    color: #374151 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    cursor: pointer !important;
}}

.stRadio > div > label:hover {{
    border-color: #22c55e !important;
    background: #f0fdf4 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.1) !important;
}}

/* Checkboxes */
.stCheckbox > label {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #374151 !important;
}}

.stCheckbox > label span {{
    font-family: 'Barlow', sans-serif !important;
    color: #374151 !important;
}}

/* Primary button - beautiful green */
.stButton > button {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px 32px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35) !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4) !important;
}}

.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* Download button */
.stDownloadButton > button {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    background: white !important;
    color: #374151 !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 14px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}}

.stDownloadButton > button:hover {{
    border-color: #22c55e !important;
    color: #22c55e !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}}

/* Form container */
[data-testid="stForm"] {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}}

/* Divider */
hr, .stMarkdown hr {{
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, #e5e7eb, transparent) !important;
    margin: 32px 0 !important;
}}

/* Info/warning boxes */
.stAlert {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 15px !important;
    border-radius: 12px !important;
    border: none !important;
}}

/* Caption text */
.stCaption, [data-testid="stCaptionContainer"] {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 13px !important;
    color: #6b7280 !important;
}}

/* Spinner */
.stSpinner > div {{
    border-top-color: #22c55e !important;
}}

/* Animation keyframes */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
}}

/* Smooth scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: #f1f1f1;
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb {{
    background: #c1c1c1;
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: #a1a1a1;
}}
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def assess_intake(intake_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = requests.post(f"{API_URL}/assess_intake", json=intake_data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


def render_header():
    """Render beautiful header with centered logo and status."""
    api_online = check_api_health()

    # Status indicator in top right
    if api_online:
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 8px; padding: 10px 18px; background: white; border-radius: 24px; border: 1.5px solid #dcfce7; box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1);">
                <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite;"></span>
                <span style="font-family: 'Barlow', sans-serif; font-size: 13px; color: #166534; font-weight: 600;">Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 8px; padding: 10px 18px; background: white; border-radius: 24px; border: 1.5px solid #fecaca; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);">
                <span style="width: 8px; height: 8px; background: #ef4444; border-radius: 50%;"></span>
                <span style="font-family: 'Barlow', sans-serif; font-size: 13px; color: #dc2626; font-weight: 600;">Offline</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Centered title
    st.markdown("""
    <div style="text-align: center; animation: fadeInUp 0.6s ease-out;">
        <div style="margin-bottom: 8px;">
            <span style="font-family: 'Barlow', sans-serif; font-size: 52px; font-weight: 800; color: #22c55e; letter-spacing: -2px;">AIAudit</span>
        </div>
        <p style="font-family: 'Barlow', sans-serif; font-size: 20px; color: #6b7280; margin: 0; font-weight: 400;">
            EU AI Act Compliance Assessment
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)


# SVG icons for section cards (no emojis)
SECTION_ICONS = {
    "system": '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>''',
    "scope": '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>''',
    "data": '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>''',
    "impact": '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>''',
    "oversight": '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>''',
}


def render_section_card(title: str, icon_key: str, color: str):
    """Render a beautiful section card header with SVG icon."""
    icon_svg = SECTION_ICONS.get(icon_key, SECTION_ICONS["system"])

    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 20px 24px;
        margin: 28px 0 18px 0;
        border: 1px solid #f0f0f0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        display: flex;
        align-items: center;
        gap: 14px;
        animation: fadeInUp 0.4s ease-out;
    ">
        <div style="
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, {color}15 0%, {color}25 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {color};
        ">{icon_svg}</div>
        <span style="font-family: 'Barlow', sans-serif; font-size: 18px; font-weight: 700; color: #1a1a1a; letter-spacing: -0.3px;">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def render_intake_form() -> Optional[Dict[str, Any]]:
    with st.form("assessment_form"):

        render_section_card("System Information", "📋", "#8b5cf6")
        col1, col2 = st.columns(2)
        with col1:
            system_name = st.text_input("AI System Name", placeholder="e.g., RecruitAI Pro")
        with col2:
            team_name = st.text_input("Team / Department", value="Engineering", placeholder="e.g., HR Technology")

        render_section_card("Scope & Purpose", "🎯", "#22c55e")
        sector = st.selectbox(
            "Sector",
            options=["hiring", "credit_scoring", "healthcare", "education", "law_enforcement",
                    "critical_infrastructure", "insurance", "social_services", "recommender",
                    "customer_service", "manufacturing", "logistics", "other"],
            format_func=lambda x: {
                "hiring": "Hiring / Recruitment", "credit_scoring": "Credit Scoring / Financial",
                "healthcare": "Healthcare / Medical", "education": "Education",
                "law_enforcement": "Law Enforcement / Security", "critical_infrastructure": "Critical Infrastructure",
                "insurance": "Insurance", "social_services": "Social Services / Benefits",
                "recommender": "Recommendations / Content", "customer_service": "Customer Service",
                "manufacturing": "Manufacturing / Industrial", "logistics": "Logistics / Supply Chain",
                "other": "Other"
            }.get(x, x)
        )
        use_case = st.text_area("Use Case Description", placeholder="Describe what your AI system does, its main purpose, and how decisions are made...", height=120)

        render_section_card("Data Processing", "🔐", "#3b82f6")
        data_types = st.multiselect(
            "Data Types Processed",
            options=["biometrics", "health_data", "financial_data", "criminal_records",
                    "political_opinions", "religious_beliefs", "ethnic_origin", "location_data",
                    "behavioral_data", "employment_data", "educational_records", "generic_pii", "anonymous_data"],
            default=["generic_pii"],
            format_func=lambda x: x.replace("_", " ").title()
        )

        render_section_card("Impact Assessment", "⚡", "#f59e0b")
        col1, col2 = st.columns(2)
        with col1:
            user_types = st.multiselect(
                "Affected Users",
                options=["general_public", "employees", "children", "elderly", "vulnerable_groups", "patients", "students", "consumers"],
                default=["employees"],
                format_func=lambda x: x.replace("_", " ").title()
            )
        with col2:
            decision_impacts = st.multiselect(
                "Decision Types",
                options=["employment_decisions", "credit_decisions", "access_to_services", "educational_outcomes",
                        "health_treatment", "legal_decisions", "law_enforcement_actions", "safety_critical",
                        "recommendations", "operational_efficiency"],
                default=["employment_decisions"],
                format_func=lambda x: x.replace("_", " ").title()
            )

        render_section_card("Human Oversight", "👁️", "#ec4899")
        oversight_level = st.radio(
            "Oversight Level",
            options=["fully_automated", "human_on_the_loop", "human_in_the_loop", "human_override_possible", "human_final_decision"],
            index=2,
            format_func=lambda x: {
                "fully_automated": "Fully Automated — No human review",
                "human_on_the_loop": "Human Monitoring — System acts autonomously",
                "human_in_the_loop": "Human Review — Each decision reviewed",
                "human_override_possible": "Human Override — Can intervene anytime",
                "human_final_decision": "Human Final — All decisions by humans"
            }.get(x, x)
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            can_opt_out = st.checkbox("Users can opt out of AI processing", value=True)
        with col2:
            has_appeal = st.checkbox("Appeal mechanism exists for decisions", value=True)

        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Assess Compliance", use_container_width=True)

        if submitted:
            if not system_name:
                st.error("Please provide a system name")
                return None
            if not use_case or len(use_case) < 20:
                st.error("Please provide a detailed use case description (min 20 characters)")
                return None

            return {
                "system_name": system_name, "system_version": "1.0.0",
                "team_name": team_name or "Not specified", "project_owner": "assessment@company.com",
                "sector": sector, "use_case_description": use_case, "user_types": user_types,
                "data_types": data_types, "decision_impacts": decision_impacts,
                "oversight_level": oversight_level, "can_users_opt_out": can_opt_out,
                "appeal_mechanism": has_appeal,
                "documentation": {k: "not_started" for k in ["data_sheet", "model_card", "system_logs",
                    "monitoring_dashboard", "risk_assessment", "bias_audit", "technical_documentation", "user_instructions"]}
            }
    return None


def render_results(result: Dict[str, Any]):
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    risk_score = result.get("risk_score", 0.5)
    risk_category = result.get("risk_category", "medium_risk")
    risk_pct = int(risk_score * 100)

    # Color schemes for different risk levels
    if risk_category == "high_risk":
        color = "#dc2626"
        bg = "#fef2f2"
        gradient_bg = "linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)"
        label = "HIGH RISK"
        ring_color = "rgba(220, 38, 38, 0.2)"
    elif risk_category == "medium_risk":
        color = "#d97706"
        bg = "#fffbeb"
        gradient_bg = "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)"
        label = "MEDIUM RISK"
        ring_color = "rgba(217, 119, 6, 0.2)"
    else:
        color = "#16a34a"
        bg = "#f0fdf4"
        gradient_bg = "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)"
        label = "LOW RISK"
        ring_color = "rgba(22, 163, 74, 0.2)"

    # Beautiful score display card
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 24px;
        padding: 48px 40px;
        text-align: center;
        margin-bottom: 32px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 8px 40px rgba(0,0,0,0.06);
        animation: fadeInUp 0.5s ease-out;
    ">
        <div style="
            width: 160px;
            height: 160px;
            margin: 0 auto 24px auto;
            border-radius: 50%;
            background: {gradient_bg};
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 0 8px {ring_color};
        ">
            <span style="font-family: 'Barlow', sans-serif; font-size: 64px; font-weight: 800; color: {color}; letter-spacing: -3px;">{risk_pct}</span>
        </div>
        <div style="
            display: inline-block;
            padding: 12px 28px;
            background: {bg};
            color: {color};
            border-radius: 24px;
            font-family: 'Barlow', sans-serif;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)

    # Executive Summary in a nice card
    summary = result.get("executive_summary", "Assessment complete.")
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    ">
        <div style="font-family: 'Barlow', sans-serif; font-size: 16px; font-weight: 700; color: #1a1a1a; margin-bottom: 12px;">Executive Summary</div>
        <div style="font-family: 'Barlow', sans-serif; font-size: 15px; color: #4b5563; line-height: 1.7;">{summary}</div>
    </div>
    """, unsafe_allow_html=True)

    # Risk Factors / Article Analysis
    risk_factors = result.get("risk_factors", [])
    obligations = result.get("obligations", [])

    findings = []
    for f in risk_factors:
        w = f.get("weight", 0)
        if w >= 0:
            findings.append({
                "article": f.get("article_reference", ""),
                "desc": f.get("description", ""),
                "severity": "high" if w >= 0.7 else "medium" if w >= 0.4 else "low",
                "score": int(w * 100)
            })

    for ob in obligations:
        if ob.get("priority") == "high":
            findings.append({
                "article": ob.get("article_reference", ""),
                "desc": f"{ob.get('title', '')}: {ob.get('description', '')}",
                "severity": "high",
                "score": 80
            })

    if findings:
        findings.sort(key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x["severity"], 2), -x["score"]))

        st.markdown("""
        <div style="font-family: 'Barlow', sans-serif; font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 28px 0 16px 0;">
            EU AI Act Article Analysis
        </div>
        """, unsafe_allow_html=True)

        for f in findings[:8]:
            sev = f["severity"]
            if sev == "high":
                border_col, badge_bg, badge_col = "#dc2626", "#fef2f2", "#dc2626"
            elif sev == "medium":
                border_col, badge_bg, badge_col = "#d97706", "#fffbeb", "#d97706"
            else:
                border_col, badge_bg, badge_col = "#16a34a", "#f0fdf4", "#16a34a"

            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 18px 22px;
                margin-bottom: 12px;
                border: 1px solid #f0f0f0;
                border-left: 4px solid {border_col};
                box-shadow: 0 2px 8px rgba(0,0,0,0.03);
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 16px;
            ">
                <div style="flex: 1;">
                    <div style="font-family: 'Barlow', sans-serif; font-size: 15px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px;">{f['article']}</div>
                    <div style="font-family: 'Barlow', sans-serif; font-size: 14px; color: #6b7280; line-height: 1.5;">{f['desc']}</div>
                </div>
                <div style="
                    background: {badge_bg};
                    color: {badge_col};
                    padding: 6px 14px;
                    border-radius: 8px;
                    font-family: 'Barlow', sans-serif;
                    font-size: 13px;
                    font-weight: 700;
                    white-space: nowrap;
                ">{f['score']}%</div>
            </div>
            """, unsafe_allow_html=True)

    # Recommendations
    recs = result.get("key_recommendations", [])
    if recs:
        st.markdown("""
        <div style="font-family: 'Barlow', sans-serif; font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 28px 0 16px 0;">
            Required Actions
        </div>
        """, unsafe_allow_html=True)

        for i, rec in enumerate(recs, 1):
            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 10px;
                border: 1px solid #f0f0f0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.03);
                display: flex;
                align-items: flex-start;
                gap: 14px;
            ">
                <div style="
                    width: 28px;
                    height: 28px;
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-family: 'Barlow', sans-serif;
                    font-size: 14px;
                    font-weight: 700;
                    flex-shrink: 0;
                ">{i}</div>
                <div style="font-family: 'Barlow', sans-serif; font-size: 14px; color: #374151; line-height: 1.6; padding-top: 4px;">{rec}</div>
            </div>
            """, unsafe_allow_html=True)

    # Documentation gaps
    gaps = result.get("documentation_gaps", [])
    if gaps:
        st.markdown("""
        <div style="font-family: 'Barlow', sans-serif; font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 28px 0 16px 0;">
            Missing Documentation
        </div>
        """, unsafe_allow_html=True)

        for gap in gaps:
            st.markdown(f"""
            <div style="
                background: #fffbeb;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 10px;
                border: 1px solid #fde68a;
                font-family: 'Barlow', sans-serif;
                font-size: 14px;
                color: #92400e;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="font-size: 16px;">⚠️</span>
                {gap}
            </div>
            """, unsafe_allow_html=True)

    # Action buttons
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
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
            st.session_state.gradient = random.choice(GRADIENTS)
            st.rerun()


def main():
    render_header()
    intake_data = render_intake_form()
    if intake_data:
        with st.spinner("Analyzing compliance..."):
            result = assess_intake(intake_data)
            if result:
                render_results(result)


if __name__ == "__main__":
    main()

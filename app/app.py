"""
Streamlit frontend for AIAudit.

This application provides a user-friendly interface for EU AI Act
compliance assessment and remediation planning. Users can paste
their AI system documentation and receive risk classification
with actionable remediation guidance.

Usage:
    streamlit run app/app.py

Environment Variables:
    API_URL: Base URL of the FastAPI backend (default: http://127.0.0.1:8000)
"""

import os
import urllib.parse
from typing import Any, Dict, Optional

import requests
import streamlit as st

# Configuration
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


def check_api_health() -> Dict[str, Any]:
    """
    Check if the API is healthy and responsive.

    Returns:
        Health status dictionary or error info.
    """
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Status code: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "message": "Cannot connect to API"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def assess_and_remediate(text: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
    """
    Call the assessment and remediation endpoint.

    Args:
        text: AI system documentation to assess.
        top_k: Maximum remediation items per article.

    Returns:
        Remediation response or None on error.
    """
    try:
        response = requests.post(
            f"{API_URL}/assess_and_remediate",
            json={"text": text, "top_k": top_k},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Is the server running?")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def render_risk_badge(risk_level: str, confidence: float):
    """Render a colored risk badge based on risk level."""
    colors = {
        "high": "#ff4b4b",
        "medium": "#ffa500",
        "low": "#00cc00"
    }
    color = colors.get(risk_level, "#808080")

    st.markdown(
        f"""
        <div style="
            background-color: {color};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            font-size: 1.2em;
            font-weight: bold;
            margin: 10px 0;
        ">
            Risk Level: {risk_level.upper()} ({confidence:.0%} confidence)
        </div>
        """,
        unsafe_allow_html=True
    )


def render_article_scores(article_scores: Dict[str, float]):
    """Render article relevance scores as progress bars."""
    st.subheader("Article Relevance Scores")

    article_names = {
        "Article_9": "Risk Management System",
        "Article_10": "Data and Data Governance",
        "Article_12": "Record-Keeping",
        "Article_14": "Human Oversight",
        "Article_15": "Accuracy, Robustness, Cybersecurity"
    }

    # Sort by score descending
    sorted_articles = sorted(article_scores.items(), key=lambda x: x[1], reverse=True)

    for article, score in sorted_articles:
        name = article_names.get(article, article)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(score)
        with col2:
            st.write(f"{article}: {score:.0%}")
        st.caption(name)


def render_remediation_checklist(items: list):
    """Render remediation items as an interactive checklist."""
    st.subheader("Remediation Checklist")

    # Initialize checkbox states in session state
    if "checkbox_states" not in st.session_state:
        st.session_state.checkbox_states = {}

    for item in items:
        item_id = item["remediation_id"]

        # Urgency indicator
        urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["urgency"], "⚪")

        # Create checkbox with persistent state
        checkbox_key = f"check_{item_id}"
        checked = st.checkbox(
            f"{urgency_emoji} **{item['priority']}. {item['title']}**",
            key=checkbox_key,
            value=st.session_state.checkbox_states.get(checkbox_key, False)
        )
        st.session_state.checkbox_states[checkbox_key] = checked

        # Show details in an expander
        with st.expander(f"Details - {item['article']} | Effort: {item['estimated_effort']}"):
            st.markdown(f"**Article:** {item['article']} - {item['article_name']}")
            st.markdown(f"**Urgency:** {item['urgency'].capitalize()}")
            st.markdown(f"**Estimated Effort:** {item['estimated_effort']}")
            st.markdown("---")
            st.markdown(item['description'])


def create_github_issue_url(result: Dict[str, Any]) -> str:
    """
    Create a pre-filled GitHub issue URL.

    Args:
        result: Remediation response dictionary.

    Returns:
        GitHub new issue URL with pre-filled title and body.
    """
    # Build issue title
    title = f"[AI Compliance] {result['risk_level'].upper()} Risk - {len(result['items'])} Remediations Required"

    # Build issue body
    body_lines = [
        "## AI Act Compliance Assessment Results",
        "",
        result["summary"],
        "",
        "## Remediation Checklist",
        ""
    ]

    for item in result.get("items", []):
        urgency_tag = {"high": "P0", "medium": "P1", "low": "P2"}.get(item["urgency"], "P2")
        body_lines.append(
            f"- [ ] **[{urgency_tag}]** {item['title']} ({item['article']}) - {item['estimated_effort']}"
        )

    body_lines.extend([
        "",
        "---",
        f"_Generated by AIAudit Lite_"
    ])

    body = "\n".join(body_lines)

    # Encode for URL
    encoded_title = urllib.parse.quote(title)
    encoded_body = urllib.parse.quote(body)

    # GitHub new issue URL (user needs to specify their repo)
    return f"https://github.com/YOUR_ORG/YOUR_REPO/issues/new?title={encoded_title}&body={encoded_body}"


def main():
    """Main Streamlit application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="AIAudit Lite",
        page_icon="🔍",
        layout="wide"
    )

    # Header
    st.title("🔍 AIAudit Lite")
    st.markdown(
        """
        **EU AI Act Compliance Triage & Remediation Tool**

        Paste your AI system documentation below to receive a risk assessment
        and prioritized remediation plan.

        *This tool provides heuristic guidance — not legal advice.*
        """
    )

    # Sidebar with API status
    with st.sidebar:
        st.header("System Status")

        health = check_api_health()
        if health.get("status") == "healthy":
            st.success("✅ API Connected")
            st.caption(f"Model: {'✓' if health.get('model_loaded') else '✗'}")
            st.caption(f"Templates: {'✓' if health.get('templates_loaded') else '✗'}")
        elif health.get("status") == "degraded":
            st.warning("⚠️ API Degraded")
            st.caption(health.get("message", "Model may not be loaded"))
        else:
            st.error("❌ API Offline")
            st.caption("Start the API with: uvicorn src.api.main:app --reload")

        st.markdown("---")

        st.header("Settings")
        top_k = st.slider(
            "Max remediations per article",
            min_value=1,
            max_value=5,
            value=3
        )

        st.markdown("---")

        st.header("About")
        st.markdown(
            """
            AIAudit Lite evaluates AI system documentation against
            EU AI Act risk signals and generates actionable
            remediation plans.

            **Target Users:**
            - Product Teams
            - AI Governance
            - Legal/Compliance

            [View Documentation](https://github.com/YOUR_ORG/AIAudit)
            """
        )

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Input Documentation")

        # Text input
        text_input = st.text_area(
            "Paste your AI system documentation here:",
            height=400,
            placeholder=(
                "Enter a description of your AI system, including:\n"
                "- System purpose and intended use\n"
                "- Data processing activities\n"
                "- Risk management procedures\n"
                "- Human oversight mechanisms\n"
                "- Logging and monitoring capabilities\n"
                "- Security measures\n\n"
                "Example:\n"
                "This AI system uses facial recognition for access control "
                "in corporate facilities. The system processes biometric data "
                "from employees and visitors..."
            )
        )

        # Assess button
        assess_button = st.button(
            "🔍 Assess & Remediate",
            type="primary",
            use_container_width=True
        )

    with col2:
        st.subheader("📊 Assessment Results")

        if assess_button and text_input:
            if len(text_input) < 10:
                st.warning("Please enter at least 10 characters of documentation.")
            else:
                with st.spinner("Analyzing documentation..."):
                    result = assess_and_remediate(text_input, top_k)

                if result:
                    # Store result in session state
                    st.session_state.last_result = result

                    # Render results
                    render_risk_badge(result["risk_level"], result["confidence"])

                    st.markdown(f"**Summary:** {result['summary']}")

                    if result.get("matched_keywords"):
                        st.markdown(f"**Keywords:** {', '.join(result['matched_keywords'])}")

                    # Article scores
                    render_article_scores(result["article_scores"])

                    st.markdown("---")

                    # Remediation checklist
                    render_remediation_checklist(result["items"])

                    st.markdown("---")

                    # GitHub issue button
                    issue_url = create_github_issue_url(result)
                    st.markdown(
                        f"""
                        <a href="{issue_url}" target="_blank">
                            <button style="
                                background-color: #24292e;
                                color: white;
                                padding: 10px 20px;
                                border: none;
                                border-radius: 5px;
                                cursor: pointer;
                                font-size: 1em;
                            ">
                                📋 Create GitHub Issue
                            </button>
                        </a>
                        """,
                        unsafe_allow_html=True
                    )
                    st.caption("Opens GitHub with pre-filled issue content")

                    st.markdown("---")

                    # Disclaimer
                    st.info(f"**Disclaimer:** {result['disclaimer']}")

        elif assess_button:
            st.warning("Please enter documentation text to assess.")

        elif "last_result" in st.session_state:
            # Show previous result
            result = st.session_state.last_result
            render_risk_badge(result["risk_level"], result["confidence"])
            st.markdown(f"**Summary:** {result['summary']}")
            render_article_scores(result["article_scores"])
            st.markdown("---")
            render_remediation_checklist(result["items"])

        else:
            st.info(
                "Enter your AI system documentation in the left panel "
                "and click 'Assess & Remediate' to begin."
            )


if __name__ == "__main__":
    main()

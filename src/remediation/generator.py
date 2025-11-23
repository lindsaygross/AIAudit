"""
Remediation plan generator for AIAudit.

This module generates deterministic, template-driven remediation plans
based on fused article relevance scores. It uses the article_remediations.yml
templates to provide actionable engineering guidance.

Usage:
    from src.remediation.generator import generate_remediation_plan

    plan = generate_remediation_plan(
        text="AI system documentation...",
        model_probs={'high': 0.8, 'medium': 0.15, 'low': 0.05},
        templates=loaded_templates,
        config=config
    )
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.remediation.mapping import (
    ARTICLES,
    extract_keywords,
    fuse_model_and_rules,
    get_top_articles,
    rule_signal,
)


def load_templates(path: str = "templates/article_remediations.yml") -> Dict[str, Any]:
    """
    Load remediation templates from YAML file.

    Args:
        path: Path to the templates YAML file.

    Returns:
        Dictionary with article templates.

    Raises:
        FileNotFoundError: If template file doesn't exist.
    """
    template_path = Path(path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    with open(template_path, "r", encoding="utf-8") as f:
        templates = yaml.safe_load(f)

    return templates


def generate_remediation_plan(
    text: str,
    model_probs: Dict[str, float],
    templates: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a deterministic remediation plan based on text analysis.

    The plan includes:
    - Summary of risk assessment
    - Prioritized list of remediation items from templates
    - Confidence scores per article
    - Standard disclaimer

    Args:
        text: Input AI system documentation text.
        model_probs: ML model risk probabilities (high/medium/low).
        templates: Loaded remediation templates.
        config: Configuration dictionary with remediation settings.

    Returns:
        Remediation plan dictionary with structure:
        {
            "summary": str,
            "risk_level": str,
            "confidence": float,
            "matched_keywords": list,
            "items": [
                {
                    "article": str,
                    "article_name": str,
                    "article_score": float,
                    "remediation_id": str,
                    "title": str,
                    "description": str,
                    "urgency": str,
                    "estimated_effort": str,
                    "priority": int
                },
                ...
            ],
            "disclaimer": str
        }

    Example:
        >>> plan = generate_remediation_plan(text, model_probs, templates, config)
        >>> print(plan["summary"])
        "High-risk assessment with 3 priority remediation actions..."
    """
    remediation_config = config.get("remediation", {})
    alpha = remediation_config.get("alpha", 0.6)
    top_k = remediation_config.get("top_k_remediations", 3)

    # Extract keywords and compute rule signals
    keywords = extract_keywords(text)
    rule_scores = rule_signal(text)

    # Fuse model and rule signals
    fused_scores = fuse_model_and_rules(model_probs, rule_scores, alpha)

    # Get top relevant articles
    top_articles = get_top_articles(fused_scores, top_k=len(ARTICLES), threshold=0.05)

    # Determine overall risk level
    risk_level = max(model_probs, key=model_probs.get)
    confidence = model_probs[risk_level]

    # Build remediation items
    items = []
    priority = 1

    for article, score in top_articles:
        article_templates = templates.get(article, {})
        article_name = article_templates.get("name", article)
        remediations = article_templates.get("remediations", [])

        # Select top remediations for this article based on urgency
        # Sort by urgency: high > medium > low
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        sorted_remediations = sorted(
            remediations,
            key=lambda x: urgency_order.get(x.get("urgency", "low"), 2)
        )

        # Take top K remediations per article, weighted by article score
        n_remediations = max(1, int(score * top_k))
        for rem in sorted_remediations[:n_remediations]:
            items.append({
                "article": article,
                "article_name": article_name,
                "article_score": round(score, 3),
                "remediation_id": rem.get("id", ""),
                "title": rem.get("title", ""),
                "description": rem.get("description", "").strip(),
                "urgency": rem.get("urgency", "medium"),
                "estimated_effort": rem.get("estimated_effort", "Unknown"),
                "priority": priority
            })
            priority += 1

            # Limit total items
            if priority > top_k * 3:
                break

        if priority > top_k * 3:
            break

    # Sort items by priority (which incorporates article relevance and urgency)
    items = items[:top_k * 3]

    # Generate summary
    summary = _generate_summary(risk_level, confidence, len(items), keywords)

    # Standard disclaimer
    disclaimer = (
        "This remediation plan provides heuristic guidance based on automated "
        "analysis. It does not constitute legal advice and should not replace "
        "consultation with qualified legal and compliance professionals. "
        "The EU AI Act requirements may vary based on specific use case details "
        "not captured in this assessment."
    )

    return {
        "summary": summary,
        "risk_level": risk_level,
        "confidence": round(confidence, 3),
        "matched_keywords": list(keywords),
        "article_scores": {art: round(score, 3) for art, score in fused_scores.items()},
        "items": items,
        "disclaimer": disclaimer
    }


def _generate_summary(
    risk_level: str,
    confidence: float,
    n_items: int,
    keywords: set
) -> str:
    """
    Generate a human-readable summary of the assessment.

    Args:
        risk_level: Predicted risk level (high/medium/low).
        confidence: Confidence score for the prediction.
        n_items: Number of remediation items.
        keywords: Set of matched keywords.

    Returns:
        Summary string.
    """
    risk_descriptions = {
        "high": "significant compliance gaps requiring immediate attention",
        "medium": "moderate compliance considerations requiring review",
        "low": "generally aligned with requirements, with minor improvements suggested"
    }

    risk_desc = risk_descriptions.get(risk_level, "compliance considerations")

    summary = (
        f"Assessment indicates {risk_level.upper()} risk level "
        f"(confidence: {confidence:.0%}) with {risk_desc}. "
        f"Generated {n_items} prioritized remediation actions."
    )

    if keywords:
        top_keywords = list(keywords)[:5]
        summary += f" Key areas identified: {', '.join(top_keywords)}."

    return summary


def format_remediation_as_markdown(plan: Dict[str, Any]) -> str:
    """
    Format remediation plan as Markdown for display.

    Args:
        plan: Remediation plan dictionary.

    Returns:
        Markdown-formatted string.
    """
    md_lines = [
        f"# EU AI Act Compliance Assessment",
        "",
        f"## Summary",
        "",
        f"{plan['summary']}",
        "",
        f"**Risk Level:** {plan['risk_level'].upper()}",
        f"**Confidence:** {plan['confidence']:.0%}",
        "",
        f"## Remediation Actions",
        ""
    ]

    for item in plan.get("items", []):
        urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["urgency"], "⚪")

        md_lines.extend([
            f"### {item['priority']}. {item['title']}",
            "",
            f"**Article:** {item['article']} - {item['article_name']}",
            f"**Urgency:** {urgency_emoji} {item['urgency'].capitalize()}",
            f"**Estimated Effort:** {item['estimated_effort']}",
            "",
            f"{item['description']}",
            "",
            "---",
            ""
        ])

    md_lines.extend([
        "",
        f"## Disclaimer",
        "",
        f"_{plan['disclaimer']}_"
    ])

    return "\n".join(md_lines)


def format_remediation_as_github_issue(plan: Dict[str, Any]) -> Dict[str, str]:
    """
    Format remediation plan for GitHub issue creation.

    Args:
        plan: Remediation plan dictionary.

    Returns:
        Dict with 'title' and 'body' for GitHub issue.
    """
    title = f"[AI Compliance] {plan['risk_level'].upper()} Risk - {len(plan['items'])} Remediations Required"

    body_lines = [
        "## AI Act Compliance Assessment Results",
        "",
        plan["summary"],
        "",
        "## Remediation Checklist",
        ""
    ]

    for item in plan.get("items", []):
        urgency_tag = {"high": "P0", "medium": "P1", "low": "P2"}.get(item["urgency"], "P2")
        body_lines.append(
            f"- [ ] **[{urgency_tag}]** {item['title']} ({item['article']}) - {item['estimated_effort']}"
        )

    body_lines.extend([
        "",
        "## Details",
        ""
    ])

    for item in plan.get("items", []):
        body_lines.extend([
            f"### {item['title']}",
            f"**Article:** {item['article']} | **Urgency:** {item['urgency']} | **Effort:** {item['estimated_effort']}",
            "",
            item['description'],
            ""
        ])

    body_lines.extend([
        "---",
        f"_Generated by AIAudit Lite. {plan['disclaimer']}_"
    ])

    return {
        "title": title,
        "body": "\n".join(body_lines)
    }

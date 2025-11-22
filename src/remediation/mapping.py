"""
Rule-based signal mapping for AIAudit.

This module provides keyword-to-article mapping and rule-based signal
extraction to complement ML-based classification. The signals are fused
with model probabilities to produce final article relevance scores.

Usage:
    from src.remediation.mapping import extract_keywords, rule_signal, fuse_model_and_rules

    keywords = extract_keywords("AI system for biometric identification...")
    signals = rule_signal("AI system for biometric identification...")
    fused = fuse_model_and_rules(model_probs, signals, alpha=0.6)
"""

import re
from typing import Dict, List, Set, Tuple


# Keyword mapping from terms to EU AI Act articles
# Each keyword maps to a list of (article, weight) tuples
KEYWORD_MAP: Dict[str, List[Tuple[str, float]]] = {
    # Article 9 - Risk Management
    "risk management": [("Article_9", 1.0)],
    "risk assessment": [("Article_9", 0.9)],
    "risk mitigation": [("Article_9", 0.9)],
    "residual risk": [("Article_9", 0.8)],
    "risk monitoring": [("Article_9", 0.8)],
    "hazard": [("Article_9", 0.6)],
    "safety": [("Article_9", 0.5)],

    # Article 10 - Data Governance
    "training data": [("Article_10", 1.0)],
    "data governance": [("Article_10", 1.0)],
    "data quality": [("Article_10", 0.9)],
    "bias": [("Article_10", 0.9), ("Article_9", 0.5)],
    "fairness": [("Article_10", 0.8), ("Article_9", 0.4)],
    "representative": [("Article_10", 0.8)],
    "dataset": [("Article_10", 0.7)],
    "annotation": [("Article_10", 0.6)],
    "labeling": [("Article_10", 0.6)],
    "data collection": [("Article_10", 0.7)],
    "consent": [("Article_10", 0.5)],

    # Article 12 - Record Keeping
    "logging": [("Article_12", 1.0)],
    "audit trail": [("Article_12", 1.0)],
    "traceability": [("Article_12", 0.9)],
    "record keeping": [("Article_12", 1.0)],
    "log retention": [("Article_12", 0.9)],
    "audit": [("Article_12", 0.7)],
    "documentation": [("Article_12", 0.6)],
    "versioning": [("Article_12", 0.5)],

    # Article 14 - Human Oversight
    "human oversight": [("Article_14", 1.0)],
    "human-in-the-loop": [("Article_14", 1.0)],
    "human review": [("Article_14", 0.9)],
    "manual review": [("Article_14", 0.8)],
    "override": [("Article_14", 0.8)],
    "intervention": [("Article_14", 0.7)],
    "supervision": [("Article_14", 0.7)],
    "escalation": [("Article_14", 0.6)],
    "approval": [("Article_14", 0.5)],
    "operator": [("Article_14", 0.4)],

    # Article 15 - Accuracy, Robustness, Cybersecurity
    "accuracy": [("Article_15", 0.9)],
    "robustness": [("Article_15", 1.0)],
    "cybersecurity": [("Article_15", 1.0)],
    "security": [("Article_15", 0.8)],
    "adversarial": [("Article_15", 0.9)],
    "attack": [("Article_15", 0.7)],
    "vulnerability": [("Article_15", 0.8)],
    "encryption": [("Article_15", 0.6)],
    "integrity": [("Article_15", 0.7)],
    "availability": [("Article_15", 0.5)],
    "reliability": [("Article_15", 0.6)],
    "testing": [("Article_15", 0.5), ("Article_9", 0.4)],

    # High-risk indicators (boost Article 9)
    "biometric": [("Article_9", 0.8), ("Article_10", 0.6)],
    "facial recognition": [("Article_9", 0.9), ("Article_10", 0.7)],
    "law enforcement": [("Article_9", 0.9)],
    "critical infrastructure": [("Article_9", 0.8)],
    "employment": [("Article_9", 0.7), ("Article_10", 0.6)],
    "credit scoring": [("Article_9", 0.8), ("Article_10", 0.6)],
    "healthcare": [("Article_9", 0.7), ("Article_15", 0.6)],
    "education": [("Article_9", 0.6), ("Article_10", 0.5)],
    "migration": [("Article_9", 0.7)],
    "autonomous": [("Article_14", 0.7), ("Article_15", 0.6)],
}

# List of all known articles
ARTICLES = ["Article_9", "Article_10", "Article_12", "Article_14", "Article_15"]


def extract_keywords(text: str) -> Set[str]:
    """
    Extract relevant keywords from text that match the keyword map.

    Args:
        text: Input text to search for keywords.

    Returns:
        Set of matched keywords (lowercase).

    Example:
        >>> keywords = extract_keywords("The system has human oversight mechanisms")
        >>> print(keywords)
        {'human oversight', 'oversight'}
    """
    text_lower = text.lower()
    matched_keywords = set()

    for keyword in KEYWORD_MAP.keys():
        # Use word boundary matching for multi-word keywords
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            matched_keywords.add(keyword)

    return matched_keywords


def rule_signal(text: str) -> Dict[str, float]:
    """
    Compute rule-based signal scores for each article.

    Scores range from 0.0 to 1.0, with higher scores indicating
    stronger relevance to the article based on keyword matches.

    Args:
        text: Input text to analyze.

    Returns:
        Dictionary mapping article names to signal scores.

    Example:
        >>> signals = rule_signal("Risk management with human oversight")
        >>> print(signals)
        {'Article_9': 0.5, 'Article_10': 0.0, 'Article_12': 0.0,
         'Article_14': 0.5, 'Article_15': 0.0}
    """
    keywords = extract_keywords(text)

    # Accumulate weighted scores per article
    article_scores: Dict[str, float] = {article: 0.0 for article in ARTICLES}
    article_counts: Dict[str, int] = {article: 0 for article in ARTICLES}

    for keyword in keywords:
        mappings = KEYWORD_MAP.get(keyword, [])
        for article, weight in mappings:
            article_scores[article] += weight
            article_counts[article] += 1

    # Normalize scores to 0-1 range using sigmoid-like scaling
    normalized_scores = {}
    for article in ARTICLES:
        raw_score = article_scores[article]
        # Apply tanh scaling for smooth normalization
        # Scale factor adjusts sensitivity
        normalized_scores[article] = min(1.0, raw_score / 3.0)

    return normalized_scores


def get_article_keywords(article: str) -> List[str]:
    """
    Get all keywords associated with a specific article.

    Args:
        article: Article name (e.g., "Article_9").

    Returns:
        List of keywords that map to this article.
    """
    keywords = []
    for keyword, mappings in KEYWORD_MAP.items():
        for art, weight in mappings:
            if art == article:
                keywords.append(keyword)
                break
    return keywords


def fuse_model_and_rules(
    model_probs: Dict[str, float],
    rule_scores: Dict[str, float],
    alpha: float = 0.6
) -> Dict[str, float]:
    """
    Fuse ML model probabilities with rule-based signals.

    Uses weighted average: fused = alpha * model + (1-alpha) * rules

    The model probabilities are for risk levels (high/medium/low),
    while rule scores are per-article. This function maps risk to
    article relevance and combines with rule signals.

    Args:
        model_probs: Dict with risk probabilities (e.g., {'high': 0.7, ...}).
        rule_scores: Dict with per-article rule signals.
        alpha: Weight for model vs rules (0-1). Default 0.6 for model.

    Returns:
        Dict mapping articles to fused relevance scores.

    Example:
        >>> model_probs = {'high': 0.8, 'medium': 0.15, 'low': 0.05}
        >>> rule_scores = {'Article_9': 0.5, 'Article_10': 0.3, ...}
        >>> fused = fuse_model_and_rules(model_probs, rule_scores, alpha=0.6)
    """
    # Convert risk probabilities to article relevance
    # High risk -> higher relevance for compliance articles
    risk_multiplier = model_probs.get("high", 0.5) + 0.5 * model_probs.get("medium", 0.0)

    fused_scores = {}
    for article in ARTICLES:
        rule_score = rule_scores.get(article, 0.0)

        # Model contribution: base relevance scaled by risk
        model_contribution = risk_multiplier * (0.5 + 0.5 * rule_score)

        # Weighted fusion
        fused_scores[article] = alpha * model_contribution + (1 - alpha) * rule_score

    # Normalize so max is 1.0
    max_score = max(fused_scores.values()) if fused_scores else 1.0
    if max_score > 0:
        fused_scores = {k: v / max_score for k, v in fused_scores.items()}

    return fused_scores


def get_top_articles(
    fused_scores: Dict[str, float],
    top_k: int = 3,
    threshold: float = 0.1
) -> List[Tuple[str, float]]:
    """
    Get the top K most relevant articles based on fused scores.

    Args:
        fused_scores: Dict mapping articles to scores.
        top_k: Maximum number of articles to return.
        threshold: Minimum score to be included.

    Returns:
        List of (article, score) tuples, sorted by score descending.
    """
    # Filter by threshold and sort
    filtered = [(art, score) for art, score in fused_scores.items() if score >= threshold]
    sorted_articles = sorted(filtered, key=lambda x: x[1], reverse=True)

    return sorted_articles[:top_k]

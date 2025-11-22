"""
Unit tests for the remediation module.

Tests cover keyword extraction, rule-based signals, and remediation
plan generation.

Run tests:
    pytest tests/test_remediation.py -v
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.remediation.mapping import (
    ARTICLES,
    extract_keywords,
    fuse_model_and_rules,
    get_top_articles,
    rule_signal,
)
from src.remediation.generator import (
    generate_remediation_plan,
    _generate_summary,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_high_risk_text():
    """Sample text indicating high risk AI system."""
    return """
    This AI system uses biometric identification for real-time remote
    surveillance in public spaces. The facial recognition system processes
    personal data of individuals without explicit consent. The system is
    deployed for law enforcement purposes and critical infrastructure
    protection. Limited human oversight mechanisms are in place.
    """


@pytest.fixture
def sample_low_risk_text():
    """Sample text indicating low risk AI system."""
    return """
    This AI system optimizes inventory management in warehouse logistics.
    It uses historical sales data to predict demand patterns. The system
    has comprehensive logging, human oversight with manual override
    capabilities, and regular accuracy testing. All data processing
    activities are well-documented with complete audit trails.
    """


@pytest.fixture
def sample_templates():
    """Minimal remediation templates for testing."""
    return {
        "Article_9": {
            "name": "Risk Management System",
            "remediations": [
                {
                    "id": "A9-R1",
                    "title": "Implement Risk Monitoring",
                    "description": "Deploy monitoring infrastructure",
                    "urgency": "high",
                    "estimated_effort": "2-3 weeks"
                }
            ]
        },
        "Article_10": {
            "name": "Data Governance",
            "remediations": [
                {
                    "id": "A10-R1",
                    "title": "Data Lineage Tracking",
                    "description": "Track data provenance",
                    "urgency": "high",
                    "estimated_effort": "2-3 weeks"
                }
            ]
        },
        "Article_12": {
            "name": "Record-Keeping",
            "remediations": [
                {
                    "id": "A12-R1",
                    "title": "Implement Logging",
                    "description": "Deploy logging system",
                    "urgency": "medium",
                    "estimated_effort": "1-2 weeks"
                }
            ]
        },
        "Article_14": {
            "name": "Human Oversight",
            "remediations": [
                {
                    "id": "A14-R1",
                    "title": "Human-in-the-Loop Workflow",
                    "description": "Implement approval workflows",
                    "urgency": "high",
                    "estimated_effort": "3-4 weeks"
                }
            ]
        },
        "Article_15": {
            "name": "Accuracy and Robustness",
            "remediations": [
                {
                    "id": "A15-R1",
                    "title": "Accuracy Benchmarking",
                    "description": "Establish accuracy metrics",
                    "urgency": "medium",
                    "estimated_effort": "2-3 weeks"
                }
            ]
        }
    }


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "remediation": {
            "alpha": 0.6,
            "beta": 0.4,
            "top_k_remediations": 3
        }
    }


# ============================================================================
# Tests for mapping.py
# ============================================================================

class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_extracts_single_keyword(self):
        """Test extraction of a single known keyword."""
        text = "The system implements risk management procedures."
        keywords = extract_keywords(text)
        assert "risk management" in keywords

    def test_extracts_multiple_keywords(self):
        """Test extraction of multiple keywords."""
        text = "Human oversight with audit trail and data governance."
        keywords = extract_keywords(text)
        assert "human oversight" in keywords
        assert "audit trail" in keywords
        assert "data governance" in keywords

    def test_case_insensitive(self):
        """Test that extraction is case-insensitive."""
        text = "BIOMETRIC identification and CYBERSECURITY measures."
        keywords = extract_keywords(text)
        assert "biometric" in keywords
        assert "cybersecurity" in keywords

    def test_no_keywords_found(self):
        """Test with text containing no known keywords."""
        text = "The weather is nice today."
        keywords = extract_keywords(text)
        assert len(keywords) == 0

    def test_empty_text(self):
        """Test with empty text."""
        keywords = extract_keywords("")
        assert len(keywords) == 0


class TestRuleSignal:
    """Tests for rule_signal function."""

    def test_returns_all_articles(self):
        """Test that all articles are present in output."""
        text = "Some AI system documentation."
        signals = rule_signal(text)
        for article in ARTICLES:
            assert article in signals

    def test_scores_in_valid_range(self):
        """Test that all scores are between 0 and 1."""
        text = "Biometric facial recognition with human oversight logging."
        signals = rule_signal(text)
        for score in signals.values():
            assert 0 <= score <= 1

    def test_high_risk_text_signals(self, sample_high_risk_text):
        """Test that high-risk keywords produce non-zero signals."""
        signals = rule_signal(sample_high_risk_text)
        # Biometric and law enforcement should trigger Article 9
        assert signals["Article_9"] > 0

    def test_empty_text_signals(self):
        """Test signals for empty text are all zero."""
        signals = rule_signal("")
        for score in signals.values():
            assert score == 0


class TestFuseModelAndRules:
    """Tests for fuse_model_and_rules function."""

    def test_returns_all_articles(self):
        """Test that fused scores include all articles."""
        model_probs = {"high": 0.5, "medium": 0.3, "low": 0.2}
        rule_scores = {art: 0.5 for art in ARTICLES}
        fused = fuse_model_and_rules(model_probs, rule_scores, alpha=0.6)
        for article in ARTICLES:
            assert article in fused

    def test_scores_normalized(self):
        """Test that at least one fused score equals 1.0 (max normalized)."""
        model_probs = {"high": 0.8, "medium": 0.15, "low": 0.05}
        rule_scores = {"Article_9": 0.9, "Article_10": 0.5,
                       "Article_12": 0.3, "Article_14": 0.4, "Article_15": 0.2}
        fused = fuse_model_and_rules(model_probs, rule_scores, alpha=0.6)
        assert max(fused.values()) == 1.0

    def test_alpha_weighting(self):
        """Test that alpha affects the fusion balance."""
        model_probs = {"high": 1.0, "medium": 0.0, "low": 0.0}
        rule_scores = {"Article_9": 1.0, "Article_10": 0.0,
                       "Article_12": 0.0, "Article_14": 0.0, "Article_15": 0.0}

        # With alpha=1.0, only model contributes
        fused_alpha1 = fuse_model_and_rules(model_probs, rule_scores, alpha=1.0)

        # With alpha=0.0, only rules contribute
        fused_alpha0 = fuse_model_and_rules(model_probs, rule_scores, alpha=0.0)

        # Results should differ (unless edge case)
        assert fused_alpha1 != fused_alpha0 or all(v == 0 for v in rule_scores.values())


class TestGetTopArticles:
    """Tests for get_top_articles function."""

    def test_returns_top_k(self):
        """Test that at most K articles are returned."""
        scores = {"Article_9": 0.9, "Article_10": 0.7, "Article_12": 0.5,
                  "Article_14": 0.3, "Article_15": 0.1}
        top = get_top_articles(scores, top_k=3)
        assert len(top) <= 3

    def test_sorted_by_score(self):
        """Test that articles are sorted by score descending."""
        scores = {"Article_9": 0.5, "Article_10": 0.9, "Article_12": 0.3,
                  "Article_14": 0.7, "Article_15": 0.1}
        top = get_top_articles(scores, top_k=5)
        sorted_scores = [score for _, score in top]
        assert sorted_scores == sorted(sorted_scores, reverse=True)

    def test_threshold_filtering(self):
        """Test that scores below threshold are excluded."""
        scores = {"Article_9": 0.9, "Article_10": 0.05, "Article_12": 0.5,
                  "Article_14": 0.03, "Article_15": 0.1}
        top = get_top_articles(scores, top_k=5, threshold=0.1)
        for _, score in top:
            assert score >= 0.1


# ============================================================================
# Tests for generator.py
# ============================================================================

class TestGenerateRemediationPlan:
    """Tests for generate_remediation_plan function."""

    def test_returns_required_fields(self, sample_high_risk_text, sample_templates, sample_config):
        """Test that plan contains all required fields."""
        model_probs = {"high": 0.8, "medium": 0.15, "low": 0.05}
        plan = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )

        assert "summary" in plan
        assert "risk_level" in plan
        assert "confidence" in plan
        assert "matched_keywords" in plan
        assert "article_scores" in plan
        assert "items" in plan
        assert "disclaimer" in plan

    def test_risk_level_from_model(self, sample_high_risk_text, sample_templates, sample_config):
        """Test that risk level matches highest model probability."""
        model_probs = {"high": 0.1, "medium": 0.7, "low": 0.2}
        plan = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )
        assert plan["risk_level"] == "medium"

    def test_items_have_required_fields(self, sample_low_risk_text, sample_templates, sample_config):
        """Test that remediation items have all required fields."""
        model_probs = {"high": 0.1, "medium": 0.2, "low": 0.7}
        plan = generate_remediation_plan(
            sample_low_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )

        for item in plan["items"]:
            assert "article" in item
            assert "article_name" in item
            assert "article_score" in item
            assert "remediation_id" in item
            assert "title" in item
            assert "description" in item
            assert "urgency" in item
            assert "estimated_effort" in item
            assert "priority" in item

    def test_disclaimer_present(self, sample_high_risk_text, sample_templates, sample_config):
        """Test that disclaimer is included."""
        model_probs = {"high": 0.8, "medium": 0.15, "low": 0.05}
        plan = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )
        assert len(plan["disclaimer"]) > 0
        assert "legal advice" in plan["disclaimer"].lower()

    def test_deterministic_output(self, sample_high_risk_text, sample_templates, sample_config):
        """Test that the same input produces the same output."""
        model_probs = {"high": 0.8, "medium": 0.15, "low": 0.05}

        plan1 = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )
        plan2 = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )

        assert plan1["risk_level"] == plan2["risk_level"]
        assert plan1["confidence"] == plan2["confidence"]
        assert len(plan1["items"]) == len(plan2["items"])


class TestGenerateSummary:
    """Tests for _generate_summary helper function."""

    def test_includes_risk_level(self):
        """Test that summary includes the risk level."""
        summary = _generate_summary("high", 0.85, 5, set())
        assert "HIGH" in summary

    def test_includes_confidence(self):
        """Test that summary includes confidence percentage."""
        summary = _generate_summary("medium", 0.75, 3, set())
        assert "75%" in summary

    def test_includes_item_count(self):
        """Test that summary includes remediation count."""
        summary = _generate_summary("low", 0.90, 7, set())
        assert "7" in summary

    def test_includes_keywords(self):
        """Test that summary includes matched keywords."""
        keywords = {"biometric", "surveillance"}
        summary = _generate_summary("high", 0.80, 5, keywords)
        assert "biometric" in summary.lower() or "surveillance" in summary.lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the remediation pipeline."""

    def test_full_pipeline_high_risk(self, sample_high_risk_text, sample_templates, sample_config):
        """Test full pipeline with high-risk input."""
        # Extract keywords
        keywords = extract_keywords(sample_high_risk_text)
        assert len(keywords) > 0

        # Compute signals
        signals = rule_signal(sample_high_risk_text)
        assert signals["Article_9"] > 0  # Biometric should trigger Article 9

        # Fuse with model
        model_probs = {"high": 0.85, "medium": 0.10, "low": 0.05}
        fused = fuse_model_and_rules(model_probs, signals, alpha=0.6)
        assert max(fused.values()) > 0

        # Generate plan
        plan = generate_remediation_plan(
            sample_high_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )
        assert plan["risk_level"] == "high"
        assert len(plan["items"]) > 0

    def test_full_pipeline_low_risk(self, sample_low_risk_text, sample_templates, sample_config):
        """Test full pipeline with low-risk input."""
        model_probs = {"high": 0.05, "medium": 0.15, "low": 0.80}

        plan = generate_remediation_plan(
            sample_low_risk_text,
            model_probs,
            sample_templates,
            sample_config
        )

        assert plan["risk_level"] == "low"
        assert plan["confidence"] == 0.80


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

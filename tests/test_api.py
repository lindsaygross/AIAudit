"""
Unit tests for the FastAPI application.

Tests cover health endpoint and mocked prediction/remediation endpoints.

Run tests:
    pytest tests/test_api.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_pipeline():
    """Create a mock ML pipeline."""
    mock = MagicMock()
    mock.predict.return_value = [0]  # Return encoded label
    mock.predict_proba.return_value = [[0.8, 0.15, 0.05]]
    return mock


@pytest.fixture
def mock_templates():
    """Create mock remediation templates."""
    return {
        "Article_9": {
            "name": "Risk Management System",
            "remediations": [
                {
                    "id": "A9-R1",
                    "title": "Test Remediation",
                    "description": "Test description",
                    "urgency": "high",
                    "estimated_effort": "1 week"
                }
            ]
        }
    }


@pytest.fixture
def mock_label_encoder():
    """Create mock label encoder data."""
    return {
        "classes": ["high", "low", "medium"],
        "mapping": {"high": 0, "low": 1, "medium": 2}
    }


@pytest.fixture
def client_with_mocks(mock_pipeline, mock_templates, mock_label_encoder):
    """Create test client with mocked dependencies."""
    # Patch the loading functions before importing the app
    with patch('src.api.main.load_model') as mock_load_model, \
         patch('src.api.main.load_templates') as mock_load_templates, \
         patch('src.api.main.load_config') as mock_load_config, \
         patch('src.api.main.ensure_dataset_exists'):

        mock_load_model.return_value = mock_pipeline
        mock_load_templates.return_value = mock_templates
        mock_load_config.return_value = {
            "remediation": {"alpha": 0.6, "top_k_remediations": 3}
        }

        # Import app after patching
        from src.api.main import app, state

        # Set state directly
        state.pipeline = mock_pipeline
        state.templates = mock_templates
        state.model_version = "test-1.0.0"
        state.template_version = "1.0.0"
        state.config = {"remediation": {"alpha": 0.6, "top_k_remediations": 3}}

        client = TestClient(app)
        yield client


@pytest.fixture
def client_without_model():
    """Create test client without model loaded."""
    with patch('src.api.main.load_model') as mock_load_model, \
         patch('src.api.main.load_templates') as mock_load_templates, \
         patch('src.api.main.load_config') as mock_load_config, \
         patch('src.api.main.ensure_dataset_exists'):

        mock_load_model.side_effect = FileNotFoundError("Model not found")
        mock_load_templates.return_value = {}
        mock_load_config.return_value = {}

        from src.api.main import app, state

        # Set state to indicate no model
        state.pipeline = None
        state.templates = {}
        state.model_version = "not_loaded"

        client = TestClient(app)
        yield client


# ============================================================================
# Health Endpoint Tests
# ============================================================================

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self, client_with_mocks):
        """Test that health endpoint returns 200."""
        response = client_with_mocks.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client_with_mocks):
        """Test that health response includes status."""
        response = client_with_mocks.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_indicates_model_loaded(self, client_with_mocks):
        """Test that health indicates model is loaded."""
        response = client_with_mocks.get("/health")
        data = response.json()
        assert data["model_loaded"] is True

    def test_health_degraded_without_model(self, client_without_model):
        """Test that health shows degraded when model missing."""
        response = client_without_model.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["model_loaded"] is False


# ============================================================================
# Predict Endpoint Tests
# ============================================================================

class TestPredictEndpoint:
    """Tests for /predict endpoint."""

    def test_predict_returns_200(self, client_with_mocks):
        """Test that predict returns 200 with valid input."""
        with patch('src.api.main.predict_text') as mock_predict:
            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})

            response = client_with_mocks.post(
                "/predict",
                json={"text": "This is a test AI system documentation."}
            )
            assert response.status_code == 200

    def test_predict_returns_label(self, client_with_mocks):
        """Test that predict returns predicted label."""
        with patch('src.api.main.predict_text') as mock_predict:
            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})

            response = client_with_mocks.post(
                "/predict",
                json={"text": "This is a test AI system documentation."}
            )
            data = response.json()
            assert "predicted_label" in data
            assert data["predicted_label"] == "high"

    def test_predict_returns_probabilities(self, client_with_mocks):
        """Test that predict returns probabilities."""
        with patch('src.api.main.predict_text') as mock_predict:
            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})

            response = client_with_mocks.post(
                "/predict",
                json={"text": "This is a test AI system documentation."}
            )
            data = response.json()
            assert "probabilities" in data
            assert isinstance(data["probabilities"], dict)

    def test_predict_validates_text_length(self, client_with_mocks):
        """Test that predict validates minimum text length."""
        response = client_with_mocks.post(
            "/predict",
            json={"text": "short"}
        )
        assert response.status_code == 422  # Validation error

    def test_predict_503_without_model(self, client_without_model):
        """Test that predict returns 503 when model not loaded."""
        response = client_without_model.post(
            "/predict",
            json={"text": "This is a test AI system documentation."}
        )
        assert response.status_code == 503


# ============================================================================
# Assess and Remediate Endpoint Tests
# ============================================================================

class TestAssessAndRemediateEndpoint:
    """Tests for /assess_and_remediate endpoint."""

    def test_assess_returns_200(self, client_with_mocks):
        """Test that assess returns 200 with valid input."""
        with patch('src.api.main.predict_text') as mock_predict, \
             patch('src.api.main.generate_remediation_plan') as mock_generate:

            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})
            mock_generate.return_value = {
                "summary": "Test summary",
                "risk_level": "high",
                "confidence": 0.8,
                "matched_keywords": ["test"],
                "article_scores": {"Article_9": 0.8},
                "items": [],
                "disclaimer": "Test disclaimer"
            }

            response = client_with_mocks.post(
                "/assess_and_remediate",
                json={"text": "This is a test AI system documentation."}
            )
            assert response.status_code == 200

    def test_assess_returns_summary(self, client_with_mocks):
        """Test that assess returns summary."""
        with patch('src.api.main.predict_text') as mock_predict, \
             patch('src.api.main.generate_remediation_plan') as mock_generate:

            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})
            mock_generate.return_value = {
                "summary": "Test summary",
                "risk_level": "high",
                "confidence": 0.8,
                "matched_keywords": ["test"],
                "article_scores": {"Article_9": 0.8},
                "items": [],
                "disclaimer": "Test disclaimer"
            }

            response = client_with_mocks.post(
                "/assess_and_remediate",
                json={"text": "This is a test AI system documentation."}
            )
            data = response.json()
            assert "summary" in data

    def test_assess_returns_remediation_items(self, client_with_mocks):
        """Test that assess returns remediation items."""
        with patch('src.api.main.predict_text') as mock_predict, \
             patch('src.api.main.generate_remediation_plan') as mock_generate:

            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})
            mock_generate.return_value = {
                "summary": "Test summary",
                "risk_level": "high",
                "confidence": 0.8,
                "matched_keywords": ["test"],
                "article_scores": {"Article_9": 0.8},
                "items": [
                    {
                        "article": "Article_9",
                        "article_name": "Risk Management",
                        "article_score": 0.8,
                        "remediation_id": "A9-R1",
                        "title": "Test",
                        "description": "Test desc",
                        "urgency": "high",
                        "estimated_effort": "1 week",
                        "priority": 1
                    }
                ],
                "disclaimer": "Test disclaimer"
            }

            response = client_with_mocks.post(
                "/assess_and_remediate",
                json={"text": "This is a test AI system documentation."}
            )
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)

    def test_assess_503_without_model(self, client_without_model):
        """Test that assess returns 503 when model not loaded."""
        response = client_without_model.post(
            "/assess_and_remediate",
            json={"text": "This is a test AI system documentation."}
        )
        assert response.status_code == 503

    def test_assess_accepts_top_k_parameter(self, client_with_mocks):
        """Test that assess accepts top_k parameter."""
        with patch('src.api.main.predict_text') as mock_predict, \
             patch('src.api.main.generate_remediation_plan') as mock_generate:

            mock_predict.return_value = ("high", {"high": 0.8, "medium": 0.15, "low": 0.05})
            mock_generate.return_value = {
                "summary": "Test summary",
                "risk_level": "high",
                "confidence": 0.8,
                "matched_keywords": [],
                "article_scores": {},
                "items": [],
                "disclaimer": "Test disclaimer"
            }

            response = client_with_mocks.post(
                "/assess_and_remediate",
                json={"text": "This is a test AI system documentation.", "top_k": 5}
            )
            assert response.status_code == 200


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Tests for / endpoint."""

    def test_root_returns_200(self, client_with_mocks):
        """Test that root returns 200."""
        response = client_with_mocks.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self, client_with_mocks):
        """Test that root returns API info."""
        response = client_with_mocks.get("/")
        data = response.json()
        assert "name" in data
        assert "docs" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

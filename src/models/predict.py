"""
Prediction module for AIAudit.

This module provides functions to load trained models and make
predictions on new text documents.

Usage:
    from src.models.predict import load_model, predict_text

    pipeline = load_model("artifacts/model.joblib")
    label, probs = predict_text(pipeline, "Your AI system documentation...")
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
from sklearn.pipeline import Pipeline


def load_model(path: str = "artifacts/model.joblib") -> Pipeline:
    """
    Load a trained sklearn pipeline from disk.

    Args:
        path: Path to the joblib model file.

    Returns:
        Trained sklearn Pipeline.

    Raises:
        FileNotFoundError: If the model file does not exist.

    Example:
        >>> pipeline = load_model("artifacts/model.joblib")
        >>> print(type(pipeline))
        <class 'sklearn.pipeline.Pipeline'>
    """
    model_path = Path(path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path}. "
            "Please run 'python -m src.models.train --config config.yaml' first."
        )

    pipeline = joblib.load(model_path)
    return pipeline


def load_label_encoder(path: str = "artifacts/label_encoder.json") -> Dict[str, Any]:
    """
    Load label encoder mapping from disk.

    Args:
        path: Path to the label encoder JSON file.

    Returns:
        Dictionary with 'classes' list and 'mapping' dict.

    Raises:
        FileNotFoundError: If the encoder file does not exist.
    """
    encoder_path = Path(path)

    if not encoder_path.exists():
        raise FileNotFoundError(
            f"Label encoder file not found: {path}. "
            "Please run 'python -m src.models.train --config config.yaml' first."
        )

    with open(encoder_path, "r") as f:
        encoder_data = json.load(f)

    return encoder_data


def predict_text(
    pipeline: Pipeline,
    text: str,
    label_encoder_path: str = "artifacts/label_encoder.json"
) -> Tuple[str, Dict[str, float]]:
    """
    Predict risk label and probabilities for a text document.

    Args:
        pipeline: Trained sklearn pipeline with predict and predict_proba.
        text: Input text document to classify.
        label_encoder_path: Path to label encoder JSON for class names.

    Returns:
        Tuple of (predicted_label, class_probabilities_dict).

    Example:
        >>> pipeline = load_model()
        >>> label, probs = predict_text(pipeline, "This AI system uses biometric data...")
        >>> print(label)
        'high'
        >>> print(probs)
        {'high': 0.75, 'medium': 0.20, 'low': 0.05}
    """
    # Load label encoder to get class names
    try:
        encoder_data = load_label_encoder(label_encoder_path)
        class_names = encoder_data["classes"]
    except FileNotFoundError:
        # Fallback to default class names
        class_names = ["high", "low", "medium"]

    # Predict
    X = [text]
    y_pred = pipeline.predict(X)[0]

    # Get probabilities
    if hasattr(pipeline, "predict_proba"):
        probas = pipeline.predict_proba(X)[0]
        class_probs = {
            class_names[i]: float(probas[i])
            for i in range(len(class_names))
        }
    else:
        # No probabilities available, use 1.0 for predicted class
        class_probs = {name: 0.0 for name in class_names}
        class_probs[class_names[y_pred]] = 1.0

    # Get predicted label name
    predicted_label = class_names[y_pred]

    return predicted_label, class_probs


def predict_batch(
    pipeline: Pipeline,
    texts: list,
    label_encoder_path: str = "artifacts/label_encoder.json"
) -> list:
    """
    Predict risk labels and probabilities for multiple documents.

    Args:
        pipeline: Trained sklearn pipeline.
        texts: List of text documents to classify.
        label_encoder_path: Path to label encoder JSON.

    Returns:
        List of dicts, each with 'label' and 'probabilities' keys.

    Example:
        >>> results = predict_batch(pipeline, ["doc1...", "doc2..."])
        >>> print(results[0])
        {'label': 'high', 'probabilities': {'high': 0.8, 'medium': 0.15, 'low': 0.05}}
    """
    try:
        encoder_data = load_label_encoder(label_encoder_path)
        class_names = encoder_data["classes"]
    except FileNotFoundError:
        class_names = ["high", "low", "medium"]

    # Predict all at once for efficiency
    y_pred = pipeline.predict(texts)

    if hasattr(pipeline, "predict_proba"):
        probas = pipeline.predict_proba(texts)
    else:
        # Create one-hot probabilities
        n_classes = len(class_names)
        probas = np.zeros((len(texts), n_classes))
        for i, pred in enumerate(y_pred):
            probas[i, pred] = 1.0

    results = []
    for i in range(len(texts)):
        class_probs = {
            class_names[j]: float(probas[i, j])
            for j in range(len(class_names))
        }
        results.append({
            "label": class_names[y_pred[i]],
            "probabilities": class_probs
        })

    return results


def get_model_info(model_path: str = "artifacts/model.joblib") -> Dict[str, Any]:
    """
    Get information about a trained model.

    Args:
        model_path: Path to the model file.

    Returns:
        Dictionary with model metadata.
    """
    path = Path(model_path)

    if not path.exists():
        return {"status": "not_found", "path": str(path)}

    pipeline = load_model(model_path)

    # Extract pipeline info
    info = {
        "status": "loaded",
        "path": str(path),
        "steps": [step[0] for step in pipeline.steps],
    }

    # Get vectorizer info
    if hasattr(pipeline, "named_steps") and "tfidf" in pipeline.named_steps:
        tfidf = pipeline.named_steps["tfidf"]
        info["tfidf"] = {
            "max_features": tfidf.max_features,
            "ngram_range": tfidf.ngram_range,
            "vocabulary_size": len(tfidf.vocabulary_) if hasattr(tfidf, "vocabulary_") else None
        }

    # Get classifier info
    if hasattr(pipeline, "named_steps") and "classifier" in pipeline.named_steps:
        clf = pipeline.named_steps["classifier"]
        info["classifier"] = {
            "type": type(clf).__name__,
            "n_classes": clf.classes_.shape[0] if hasattr(clf, "classes_") else None
        }

    return info

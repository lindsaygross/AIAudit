"""
Model training module for AIAudit.

This script trains a TF-IDF + Logistic Regression classifier for
EU AI Act risk classification. It supports MLflow tracking and
saves all artifacts to the artifacts/ directory.

Usage:
    python -m src.models.train --config config.yaml

Outputs:
    - artifacts/model.joblib: Trained sklearn pipeline
    - artifacts/label_encoder.json: Label mappings
    - artifacts/metrics.json: Evaluation metrics
    - artifacts/confusion_matrix.png: Confusion matrix visualization
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import load_config, get_project_root
from src.data.ingest import get_data


def get_dataset_commit_sha(config: Dict[str, Any]) -> str:
    """
    Get the git commit SHA of the AIReg-Bench dataset.

    Args:
        config: Configuration dictionary.

    Returns:
        Commit SHA string, or 'unknown' if not available.
    """
    project_root = get_project_root()
    repo_path = project_root / config.get("data", {}).get("aireg_local_path", "data/raw/aireg-bench")

    if not repo_path.exists():
        return "unknown"

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def create_pipeline(config: Dict[str, Any]) -> Pipeline:
    """
    Create the sklearn training pipeline.

    Pipeline:
    1. TF-IDF Vectorizer with configurable features and n-gram range
    2. Logistic Regression with multinomial classification

    Args:
        config: Configuration dictionary with model settings.

    Returns:
        sklearn Pipeline object.
    """
    model_config = config.get("model", {})

    # TF-IDF settings
    max_features = model_config.get("max_features", 10000)
    ngram_range = tuple(model_config.get("ngram_range", [1, 2]))

    # Logistic Regression settings
    C = model_config.get("C", 1.0)
    class_weight = model_config.get("class_weight", "balanced")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words="english",
            lowercase=True,
            strip_accents="unicode"
        )),
        ("classifier", LogisticRegression(
            C=C,
            class_weight=class_weight,
            multi_class="multinomial",
            solver="lbfgs",
            max_iter=1000,
            random_state=config.get("data", {}).get("random_state", 42)
        ))
    ])

    return pipeline


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    config: Dict[str, Any]
) -> Pipeline:
    """
    Train the classification model.

    Args:
        X_train: Training text data.
        y_train: Training labels (encoded).
        config: Configuration dictionary.

    Returns:
        Trained sklearn Pipeline.
    """
    print("Creating pipeline...")
    pipeline = create_pipeline(config)

    print("Training model...")
    pipeline.fit(X_train, y_train)

    return pipeline


def evaluate_model(
    pipeline: Pipeline,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder: LabelEncoder
) -> Dict[str, Any]:
    """
    Evaluate the trained model.

    Args:
        pipeline: Trained sklearn pipeline.
        X_test: Test text data.
        y_test: Test labels (encoded).
        label_encoder: LabelEncoder for decoding predictions.

    Returns:
        Dictionary with evaluation metrics.
    """
    print("Evaluating model...")

    y_pred = pipeline.predict(X_test)

    # Compute metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    # Get unique labels present in test set for classification report
    labels_in_test = sorted(set(y_test) | set(y_pred))
    target_names_in_test = [label_encoder.classes_[i] for i in labels_in_test]

    class_report = classification_report(
        y_test, y_pred,
        labels=labels_in_test,
        target_names=target_names_in_test,
        output_dict=True,
        zero_division=0
    )

    metrics = {
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "classification_report": class_report
    }

    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Macro F1: {macro_f1:.4f}")

    return metrics


def save_confusion_matrix(
    pipeline: Pipeline,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder: LabelEncoder,
    output_path: Path
) -> None:
    """
    Generate and save confusion matrix visualization.

    Args:
        pipeline: Trained sklearn pipeline.
        X_test: Test text data.
        y_test: Test labels (encoded).
        label_encoder: LabelEncoder for class names.
        output_path: Path to save the PNG file.
    """
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns

    y_pred = pipeline.predict(X_test)

    # Get labels present in test/pred for confusion matrix
    labels_in_test = sorted(set(y_test) | set(y_pred))
    label_names = [label_encoder.classes_[i] for i in labels_in_test]

    cm = confusion_matrix(y_test, y_pred, labels=labels_in_test)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=label_names,
        yticklabels=label_names
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix - Risk Classification")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Confusion matrix saved to: {output_path}")


def save_artifacts(
    pipeline: Pipeline,
    label_encoder: LabelEncoder,
    metrics: Dict[str, Any],
    artifacts_dir: Path
) -> Dict[str, str]:
    """
    Save all training artifacts.

    Args:
        pipeline: Trained sklearn pipeline.
        label_encoder: Fitted LabelEncoder.
        metrics: Evaluation metrics dictionary.
        artifacts_dir: Directory to save artifacts.

    Returns:
        Dictionary mapping artifact names to file paths.
    """
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = {}

    # Save model
    model_path = artifacts_dir / "model.joblib"
    joblib.dump(pipeline, model_path)
    artifact_paths["model"] = str(model_path)
    print(f"Model saved to: {model_path}")

    # Save label encoder
    encoder_path = artifacts_dir / "label_encoder.json"
    encoder_data = {
        "classes": label_encoder.classes_.tolist(),
        "mapping": {label: int(idx) for idx, label in enumerate(label_encoder.classes_)}
    }
    with open(encoder_path, "w") as f:
        json.dump(encoder_data, f, indent=2)
    artifact_paths["label_encoder"] = str(encoder_path)
    print(f"Label encoder saved to: {encoder_path}")

    # Save metrics
    metrics_path = artifacts_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    artifact_paths["metrics"] = str(metrics_path)
    print(f"Metrics saved to: {metrics_path}")

    return artifact_paths


def log_to_mlflow(
    config: Dict[str, Any],
    pipeline: Pipeline,
    metrics: Dict[str, Any],
    artifact_paths: Dict[str, str],
    dataset_sha: str
) -> str:
    """
    Log training run to MLflow.

    Args:
        config: Configuration dictionary.
        pipeline: Trained sklearn pipeline.
        metrics: Evaluation metrics.
        artifact_paths: Paths to saved artifacts.
        dataset_sha: Git commit SHA of the dataset.

    Returns:
        MLflow run ID.
    """
    import mlflow

    logging_config = config.get("logging", {})
    experiment_name = logging_config.get("experiment_name", "aireg_risk")

    # Set experiment
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:
        # Log parameters
        model_config = config.get("model", {})
        mlflow.log_param("model_type", model_config.get("type", "logistic_regression"))
        mlflow.log_param("max_features", model_config.get("max_features", 10000))
        mlflow.log_param("ngram_range", str(model_config.get("ngram_range", [1, 2])))
        mlflow.log_param("C", model_config.get("C", 1.0))
        mlflow.log_param("class_weight", model_config.get("class_weight", "balanced"))
        mlflow.log_param("test_size", config.get("data", {}).get("test_size", 0.2))
        mlflow.log_param("dataset_commit_sha", dataset_sha)

        # Log metrics
        mlflow.log_metric("accuracy", metrics["accuracy"])
        mlflow.log_metric("macro_f1", metrics["macro_f1"])

        # Log per-class metrics
        for class_name, class_metrics in metrics.get("classification_report", {}).items():
            if isinstance(class_metrics, dict):
                for metric_name, value in class_metrics.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(f"{class_name}_{metric_name}", value)

        # Log artifacts
        for artifact_name, artifact_path in artifact_paths.items():
            if Path(artifact_path).exists():
                mlflow.log_artifact(artifact_path)

        run_id = run.info.run_id
        print(f"MLflow run ID: {run_id}")

        return run_id


def main():
    """
    Main training entry point.

    Parses command-line arguments, loads data, trains model,
    evaluates, saves artifacts, and optionally logs to MLflow.
    """
    parser = argparse.ArgumentParser(description="Train AIAudit risk classifier")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AIAudit Model Training")
    print("=" * 60)

    # Load configuration
    config = load_config(args.config)
    project_root = get_project_root()

    # Get dataset commit SHA
    dataset_sha = get_dataset_commit_sha(config)
    print(f"Dataset commit SHA: {dataset_sha[:8]}..." if dataset_sha != "unknown" else "Dataset SHA: unknown")

    # Load data
    print("\nLoading data...")
    df = get_data(config)
    print(f"Loaded {len(df)} samples")

    # Get column names from config
    data_config = config.get("data", {})
    text_col = data_config.get("text_column", "text")
    label_col = data_config.get("label_column", "risk_label")

    # Encode labels
    label_encoder = LabelEncoder()
    df["label_encoded"] = label_encoder.fit_transform(df[label_col])
    print(f"Classes: {label_encoder.classes_.tolist()}")

    # Split data
    test_size = data_config.get("test_size", 0.2)
    random_state = data_config.get("random_state", 42)

    X_train, X_test, y_train, y_test = train_test_split(
        df[text_col].values,
        df["label_encoded"].values,
        test_size=test_size,
        random_state=random_state,
        stratify=df["label_encoded"].values
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Train model
    print("\n" + "-" * 40)
    pipeline = train_model(X_train, y_train, config)

    # Evaluate model
    print("\n" + "-" * 40)
    metrics = evaluate_model(pipeline, X_test, y_test, label_encoder)

    # Save artifacts
    print("\n" + "-" * 40)
    print("Saving artifacts...")
    artifacts_dir = project_root / "artifacts"
    artifact_paths = save_artifacts(pipeline, label_encoder, metrics, artifacts_dir)

    # Save confusion matrix
    cm_path = artifacts_dir / "confusion_matrix.png"
    save_confusion_matrix(pipeline, X_test, y_test, label_encoder, cm_path)
    artifact_paths["confusion_matrix"] = str(cm_path)

    # Log to MLflow if enabled
    logging_config = config.get("logging", {})
    if logging_config.get("use_mlflow", False):
        print("\n" + "-" * 40)
        print("Logging to MLflow...")
        try:
            run_id = log_to_mlflow(config, pipeline, metrics, artifact_paths, dataset_sha)
        except Exception as e:
            print(f"Warning: MLflow logging failed: {e}")
            run_id = None
    else:
        run_id = None

    # Print summary
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Model path: {artifact_paths['model']}")
    if run_id:
        print(f"MLflow run ID: {run_id}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    main()

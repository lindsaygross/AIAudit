"""
Configuration loader for AIAudit.

This module provides utilities to load and validate configuration from YAML files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file. Defaults to 'config.yaml'.

    Returns:
        Dictionary containing configuration values.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML is malformed.

    Example:
        >>> config = load_config("config.yaml")
        >>> print(config["data"]["text_column"])
        'text'
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Apply environment variable overrides
    config = _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.

    Environment variables follow the pattern: AIAUDIT_<SECTION>_<KEY>
    For example: AIAUDIT_DATA_GCS_BUCKET overrides config['data']['gcs_bucket']

    Args:
        config: The base configuration dictionary.

    Returns:
        Configuration with environment overrides applied.
    """
    # Override GCS bucket if set
    if os.environ.get("AIAUDIT_DATA_GCS_BUCKET"):
        config.setdefault("data", {})["gcs_bucket"] = os.environ["AIAUDIT_DATA_GCS_BUCKET"]

    # Override MLflow experiment name if set
    if os.environ.get("AIAUDIT_LOGGING_EXPERIMENT_NAME"):
        config.setdefault("logging", {})["experiment_name"] = os.environ["AIAUDIT_LOGGING_EXPERIMENT_NAME"]

    # Override MLflow enabled flag if set
    if os.environ.get("AIAUDIT_LOGGING_USE_MLFLOW"):
        config.setdefault("logging", {})["use_mlflow"] = os.environ["AIAUDIT_LOGGING_USE_MLFLOW"].lower() == "true"

    return config


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root (directory containing config.yaml).
    """
    current = Path(__file__).resolve()

    # Walk up until we find config.yaml or hit the filesystem root
    for parent in [current] + list(current.parents):
        if (parent / "config.yaml").exists():
            return parent

    # Fallback to current working directory
    return Path.cwd()

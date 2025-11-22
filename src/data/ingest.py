"""
Data ingestion module for AIAudit.

This module provides functions to load training data from local files
or cloud storage (GCS). Local files take precedence to ensure the
system works without cloud credentials.

Usage:
    from src.data.ingest import get_data
    config = load_config()
    df = get_data(config)
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# Import project utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_project_root


def get_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the supervised dataset for training.

    Priority order:
    1. Local file (data/aireg_supervised.csv)
    2. GCS (if cloud_provider == 'gcs' and credentials available)

    Args:
        config: Configuration dictionary with data settings.

    Returns:
        pandas DataFrame with training data.

    Raises:
        FileNotFoundError: If no data source is available.

    Example:
        >>> config = load_config()
        >>> df = get_data(config)
        >>> print(df.columns.tolist())
        ['doc_id', 'article', 'intended_use', 'system_type', 'text',
         'compliance_score_median', 'risk_label']
    """
    project_root = get_project_root()
    local_path = project_root / "data" / "aireg_supervised.csv"

    # Try local file first
    if local_path.exists():
        print(f"Loading data from local file: {local_path}")
        df = pd.read_csv(local_path)
        _validate_dataframe(df, config)
        return df

    # Try GCS if configured and credentials available
    data_config = config.get("data", {})
    if data_config.get("cloud_provider") == "gcs":
        df = _try_load_from_gcs(data_config)
        if df is not None:
            _validate_dataframe(df, config)
            return df

    # No data available
    raise FileNotFoundError(
        "No data source available. Please run 'python src/data/build_dataset.py' "
        "to build the dataset from AIReg-Bench, or provide cloud credentials."
    )


def _try_load_from_gcs(data_config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Attempt to load data from Google Cloud Storage.

    This function gracefully handles missing credentials by returning None
    instead of raising an exception.

    Args:
        data_config: Data configuration with GCS settings.

    Returns:
        DataFrame if successful, None if GCS is unavailable.
    """
    bucket_name = data_config.get("gcs_bucket")
    blob_name = data_config.get("gcs_blob")

    if not bucket_name or not blob_name:
        print("GCS bucket/blob not configured. Skipping GCS.")
        return None

    try:
        # Import GCS client (may fail if not installed or configured)
        from google.cloud import storage
        from google.auth.exceptions import DefaultCredentialsError

        try:
            # Attempt to initialize client (will fail without credentials)
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                blob.download_to_filename(tmp.name)
                print(f"Downloaded data from gs://{bucket_name}/{blob_name}")
                df = pd.read_csv(tmp.name)
                os.unlink(tmp.name)  # Clean up temp file
                return df

        except DefaultCredentialsError:
            print("GCS credentials not configured. Skipping GCS.")
            return None
        except Exception as e:
            print(f"Could not load from GCS: {e}")
            return None

    except ImportError:
        print("google-cloud-storage not installed. Skipping GCS.")
        return None


def _validate_dataframe(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """
    Validate that the DataFrame has required columns.

    Args:
        df: DataFrame to validate.
        config: Configuration with column names.

    Raises:
        ValueError: If required columns are missing.
    """
    data_config = config.get("data", {})
    text_col = data_config.get("text_column", "text")
    label_col = data_config.get("label_column", "risk_label")

    required_cols = [text_col, label_col]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"DataFrame missing required columns: {missing_cols}. "
            f"Available columns: {df.columns.tolist()}"
        )

    # Check for empty data
    if len(df) == 0:
        raise ValueError("DataFrame is empty.")

    # Check for null values in required columns
    for col in required_cols:
        null_count = df[col].isna().sum()
        if null_count > 0:
            print(f"Warning: {null_count} null values in column '{col}'")

    # Ensure text column is string type (required for TfidfVectorizer)
    df[text_col] = df[text_col].fillna("").astype(str)


def get_train_test_split(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> tuple:
    """
    Split data into training and test sets.

    Args:
        df: Full dataset DataFrame.
        config: Configuration with split settings.

    Returns:
        Tuple of (train_df, test_df).
    """
    from sklearn.model_selection import train_test_split

    data_config = config.get("data", {})
    test_size = data_config.get("test_size", 0.2)
    random_state = data_config.get("random_state", 42)
    label_col = data_config.get("label_column", "risk_label")

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[label_col] if len(df[label_col].unique()) > 1 else None
    )

    print(f"Train set: {len(train_df)} samples")
    print(f"Test set: {len(test_df)} samples")

    return train_df, test_df

"""
Dataset builder for AIAudit.

This script automatically clones or pulls the AIReg-Bench dataset repository
and constructs a supervised CSV file for training the risk classification model.

Usage:
    python src/data/build_dataset.py

The script:
1. Clones (or pulls) AIReg-Bench from GitHub
2. Reads technical documents and human annotations
3. Computes median compliance scores
4. Buckets into risk labels: high (≤2), medium (=3), low (≥4)
5. Saves data/aireg_supervised.csv

No cloud credentials required - runs entirely locally via git.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import load_config, get_project_root


def clone_or_pull_repo(repo_url: str, local_path: str) -> str:
    """
    Clone the AIReg-Bench repository if not present, or pull updates if it exists.

    Args:
        repo_url: Git URL of the repository to clone.
        local_path: Local path where the repository should be cloned.

    Returns:
        The commit SHA of the current HEAD after clone/pull.

    Raises:
        subprocess.CalledProcessError: If git commands fail.
    """
    local_path = Path(local_path)
    project_root = get_project_root()
    full_path = project_root / local_path

    # Ensure parent directories exist
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if not full_path.exists():
        print(f"Cloning AIReg-Bench repository to {full_path}...")
        subprocess.run(
            ["git", "clone", repo_url, str(full_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Clone complete.")
    else:
        print(f"AIReg-Bench repository exists at {full_path}. Pulling updates...")
        try:
            subprocess.run(
                ["git", "-C", str(full_path), "pull"],
                check=True,
                capture_output=True,
                text=True
            )
            print("Pull complete.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not pull updates: {e.stderr}")
            print("Continuing with existing local copy...")

    # Get current commit SHA
    result = subprocess.run(
        ["git", "-C", str(full_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True
    )
    commit_sha = result.stdout.strip() if result.returncode == 0 else "unknown"

    return commit_sha


def load_annotations(repo_path: Path) -> Optional[pd.DataFrame]:
    """
    Load human annotations from the AIReg-Bench repository.

    Searches for annotation files in common locations within the repository.

    Args:
        repo_path: Path to the cloned AIReg-Bench repository.

    Returns:
        DataFrame with annotations, or None if not found.
    """
    # Possible annotation file locations
    annotation_paths = [
        repo_path / "human_annotations.xlsx",
        repo_path / "data" / "human_annotations.xlsx",
        repo_path / "annotations" / "human_annotations.xlsx",
        repo_path / "human_annotations.csv",
        repo_path / "data" / "annotations.xlsx",
        repo_path / "data" / "annotations.csv",
    ]

    for path in annotation_paths:
        if path.exists():
            print(f"Found annotations at: {path}")
            if path.suffix == ".xlsx":
                return pd.read_excel(path)
            else:
                return pd.read_csv(path)

    print("Warning: No annotation file found. Will attempt to construct from available data.")
    return None


def load_documents(repo_path: Path) -> Dict[str, Dict]:
    """
    Load technical documentation from the AIReg-Bench repository.

    Searches for document files (JSON, TXT, MD) in the repository.

    Args:
        repo_path: Path to the cloned AIReg-Bench repository.

    Returns:
        Dictionary mapping document IDs to document metadata and content.
    """
    documents = {}

    # Search for documents in common locations
    doc_dirs = [
        repo_path / "documents",
        repo_path / "data" / "documents",
        repo_path / "docs",
        repo_path / "data",
        repo_path,
    ]

    for doc_dir in doc_dirs:
        if not doc_dir.exists():
            continue

        # Look for JSON files with document data
        for json_file in doc_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle various JSON structures
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "doc_id" in item:
                            documents[item["doc_id"]] = item
                        elif isinstance(item, dict) and "id" in item:
                            documents[item["id"]] = item
                elif isinstance(data, dict):
                    if "documents" in data:
                        for doc in data["documents"]:
                            doc_id = doc.get("doc_id") or doc.get("id", str(len(documents)))
                            documents[doc_id] = doc
                    elif "doc_id" in data or "id" in data:
                        doc_id = data.get("doc_id") or data.get("id")
                        documents[doc_id] = data

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not parse {json_file}: {e}")
                continue

        # Also look for markdown/text files as documents
        for text_file in list(doc_dir.glob("*.md")) + list(doc_dir.glob("*.txt")):
            doc_id = text_file.stem
            if doc_id not in documents:
                with open(text_file, "r", encoding="utf-8") as f:
                    content = f.read()
                documents[doc_id] = {
                    "doc_id": doc_id,
                    "text": content,
                    "source_file": str(text_file)
                }

    return documents


def compute_risk_label(median_score: float) -> str:
    """
    Compute risk label from median compliance score.

    Thresholds:
    - median ≤ 2: high risk (poor compliance)
    - median = 3: medium risk
    - median ≥ 4: low risk (good compliance)

    Args:
        median_score: Median compliance score across annotators.

    Returns:
        Risk label: 'high', 'medium', or 'low'.
    """
    if median_score <= 2:
        return "high"
    elif median_score == 3:
        return "medium"
    else:
        return "low"


def build_supervised_dataset(
    documents: Dict[str, Dict],
    annotations: Optional[pd.DataFrame],
    repo_path: Path
) -> pd.DataFrame:
    """
    Build the supervised dataset from documents and annotations.

    Args:
        documents: Dictionary of document metadata and content.
        annotations: DataFrame with human annotations (optional).
        repo_path: Path to the repository for finding additional data.

    Returns:
        DataFrame with columns: doc_id, article, intended_use, system_type,
        text, compliance_score_median, risk_label.
    """
    records = []

    if annotations is not None and not annotations.empty:
        # Process AIReg-Bench annotation format
        # Format: First column is "Art X / Scenario Y", "Use N" columns contain scores
        # Row 0 is header row with column descriptions
        print(f"Processing {len(annotations)} annotation records...")

        # Skip header row (row 0) if it contains metadata
        data_start = 1 if 'Compliance [1-5]' in str(annotations.iloc[0].values) else 0

        # Find "Use N" columns which contain compliance scores
        use_cols = [col for col in annotations.columns if str(col).startswith('Use ')]

        for idx in range(data_start, len(annotations)):
            row = annotations.iloc[idx]

            # First column contains Article/Scenario info
            first_col = annotations.columns[0]
            article_scenario = str(row[first_col]) if pd.notna(row[first_col]) else ""

            if not article_scenario or article_scenario == 'nan':
                continue

            # Parse article from "Art X / Scenario Y" format
            article = ""
            if "Art" in article_scenario:
                parts = article_scenario.split("/")
                article_part = parts[0].strip()
                # Convert "Art 9" to "Article_9"
                article = article_part.replace("Art ", "Article_").replace(" ", "")

            # Collect compliance scores from "Use N" columns
            scores = []
            for use_col in use_cols:
                try:
                    score = row[use_col]
                    if pd.notna(score) and isinstance(score, (int, float)):
                        score_val = float(score)
                        if 1 <= score_val <= 5:
                            scores.append(score_val)
                except (ValueError, TypeError):
                    continue

            if not scores:
                continue

            # Compute median score
            sorted_scores = sorted(scores)
            median_score = sorted_scores[len(sorted_scores) // 2]

            # Get text from the "Compliance [Text]" columns (Unnamed columns after Use N)
            text_parts = []
            for col in annotations.columns:
                col_str = str(col)
                if 'Unnamed' in col_str:
                    # Check if this might be a text column (after a Use column)
                    val = row[col]
                    if pd.notna(val) and isinstance(val, str) and len(val) > 50:
                        text_parts.append(val)

            # Combine text parts or use article description
            if text_parts:
                text = " ".join(text_parts[:2])  # Take first 2 text explanations
            else:
                text = f"AI system documentation for {article_scenario}. Compliance assessment scenario."

            doc_id = f"aireg_{idx:03d}_{article}"

            records.append({
                "doc_id": doc_id,
                "article": article,
                "intended_use": article_scenario,
                "system_type": "High-risk AI system",
                "text": text,
                "compliance_score_median": median_score,
                "risk_label": compute_risk_label(median_score)
            })

    else:
        # No annotations - create synthetic dataset from documents
        print("No annotations found. Creating dataset from documents...")

        for doc_id, doc_data in documents.items():
            text = doc_data.get("text", doc_data.get("content", ""))

            if not text:
                continue

            # Assign synthetic scores based on document characteristics
            # This is a heuristic for demonstration purposes
            text_lower = text.lower()

            # Simple heuristics for risk assessment
            risk_keywords = {
                "high": ["biometric", "criminal", "social scoring", "manipulation",
                         "exploit", "subliminal", "real-time", "law enforcement"],
                "medium": ["employment", "education", "credit", "essential services",
                           "migration", "asylum", "justice"],
                "low": ["spam", "video games", "inventory", "scheduling"]
            }

            assigned_risk = "medium"  # Default
            for risk_level, keywords in risk_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    assigned_risk = risk_level
                    break

            # Map risk to median score
            score_map = {"high": 2.0, "medium": 3.0, "low": 4.0}

            records.append({
                "doc_id": doc_id,
                "article": doc_data.get("article", ""),
                "intended_use": doc_data.get("intended_use", ""),
                "system_type": doc_data.get("system_type", ""),
                "text": text,
                "compliance_score_median": score_map[assigned_risk],
                "risk_label": assigned_risk
            })

    # If still no records, create minimal synthetic dataset for testing
    if not records:
        print("Warning: No documents found. Creating minimal synthetic dataset for testing...")
        synthetic_docs = [
            {
                "doc_id": "synthetic_001",
                "article": "Article_9",
                "intended_use": "Risk management demonstration",
                "system_type": "High-risk AI system",
                "text": "This AI system uses biometric identification for real-time remote surveillance in public spaces. The system processes facial recognition data without adequate transparency measures.",
                "compliance_score_median": 1.5,
                "risk_label": "high"
            },
            {
                "doc_id": "synthetic_002",
                "article": "Article_10",
                "intended_use": "Employment screening",
                "system_type": "HR AI tool",
                "text": "This AI tool assists in employment screening by analyzing candidate resumes and predicting job performance. Training data governance and bias testing procedures are partially documented.",
                "compliance_score_median": 3.0,
                "risk_label": "medium"
            },
            {
                "doc_id": "synthetic_003",
                "article": "Article_12",
                "intended_use": "Inventory management",
                "system_type": "Logistics AI",
                "text": "This AI system optimizes warehouse inventory levels using demand forecasting. Complete documentation of logging practices and human oversight mechanisms is provided.",
                "compliance_score_median": 4.5,
                "risk_label": "low"
            },
            {
                "doc_id": "synthetic_004",
                "article": "Article_14",
                "intended_use": "Credit scoring",
                "system_type": "Financial AI",
                "text": "AI system for credit worthiness assessment. Partial human oversight documentation available. Some transparency gaps identified in decision explanation mechanisms.",
                "compliance_score_median": 2.5,
                "risk_label": "medium"
            },
            {
                "doc_id": "synthetic_005",
                "article": "Article_15",
                "intended_use": "Healthcare diagnosis support",
                "system_type": "Medical AI",
                "text": "AI diagnostic support tool for medical imaging analysis. Extensive accuracy testing and robustness validation documented. Cybersecurity measures well-defined.",
                "compliance_score_median": 4.0,
                "risk_label": "low"
            }
        ]
        records = synthetic_docs

    df = pd.DataFrame(records)

    # Ensure required columns exist
    required_cols = ["doc_id", "article", "intended_use", "system_type",
                     "text", "compliance_score_median", "risk_label"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    # Ensure text column contains only strings (fix for sklearn TfidfVectorizer)
    df["text"] = df["text"].fillna("").astype(str)

    # Remove rows with empty text
    df = df[df["text"].str.strip().str.len() > 0]

    return df[required_cols]


def main():
    """
    Main entry point for building the supervised dataset.

    Loads configuration, clones/pulls the AIReg-Bench repository,
    processes documents and annotations, and saves the supervised CSV.
    """
    print("=" * 60)
    print("AIAudit Dataset Builder")
    print("=" * 60)

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        config = {
            "data": {
                "aireg_repo_url": "https://github.com/camlsys/aireg-bench.git",
                "aireg_local_path": "data/raw/aireg-bench"
            }
        }

    project_root = get_project_root()
    repo_url = config["data"]["aireg_repo_url"]
    local_path = config["data"]["aireg_local_path"]

    # Clone or pull the repository
    print(f"\nRepository URL: {repo_url}")
    print(f"Local path: {local_path}")

    try:
        commit_sha = clone_or_pull_repo(repo_url, local_path)
        print(f"Current commit: {commit_sha[:8]}...")
    except subprocess.CalledProcessError as e:
        print(f"Error with git operations: {e}")
        print("Continuing with synthetic dataset...")
        commit_sha = "synthetic"

    # Load documents and annotations
    repo_full_path = project_root / local_path

    if repo_full_path.exists():
        documents = load_documents(repo_full_path)
        annotations = load_annotations(repo_full_path)
        print(f"\nLoaded {len(documents)} documents")
    else:
        print("\nRepository not available. Using synthetic data.")
        documents = {}
        annotations = None

    # Build supervised dataset
    df = build_supervised_dataset(documents, annotations, repo_full_path)

    # Save to CSV
    output_path = project_root / "data" / "aireg_supervised.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("Dataset Summary")
    print("=" * 60)
    print(f"Output file: {output_path}")
    print(f"Total records: {len(df)}")
    print(f"\nClass distribution:")
    for label, count in df["risk_label"].value_counts().items():
        print(f"  {label}: {count} ({100 * count / len(df):.1f}%)")

    print("\n" + "=" * 60)
    print("Dataset build complete!")
    print("=" * 60)

    return str(output_path)


if __name__ == "__main__":
    main()

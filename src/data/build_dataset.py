"""
Dataset builder for AIAudit using AIReg-Bench.
Developed with assistance from Claude (Anthropic AI).

This script parses the full AIReg-Bench dataset which contains:
- 5 EU AI Act Articles (9, 10, 12, 14, 15)
- 3 Scenarios per article (A=Compliance, B=Violation_1, C=Violation_2)
- 10 Intended Use Cases
- 2 AI Systems per use case
- Human compliance annotations (1-5 scale)

Total: 300 documentation files with compliance scores.

Based on the paper: "AIReg-Bench: Benchmarking Language Models That Assess AI Regulation Compliance"

Usage:
    python src/data/build_dataset.py
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import load_config, get_project_root


# Map scenario letters to documentation file types
SCENARIO_TO_FILE = {
    "A": "Compliance.txt",
    "B": "Violation_1.txt",
    "C": "Violation_2.txt"
}

# Article numbers in the dataset
ARTICLES = ["Article9", "Article10", "Article12", "Article14", "Article15"]

# 10 intended uses from the paper
INTENDED_USES = {
    1: "AI system for road traffic safety management",
    2: "AI system for gas supply infrastructure safety",
    3: "AI system for evaluating learning outcomes in education",
    4: "AI system for monitoring student behavior during tests",
    5: "AI system for recruitment and job application filtering",
    6: "AI system for employment termination decisions",
    7: "AI system for credit scoring and creditworthiness",
    8: "AI system for emergency response dispatching",
    9: "AI system for judicial research and law application",
    10: "AI system for election influence and voting behavior"
}


def clone_or_pull_repo(repo_url: str, local_path: str) -> str:
    """Clone or pull the AIReg-Bench repository."""
    local_path = Path(local_path)
    project_root = get_project_root()
    full_path = project_root / local_path

    full_path.parent.mkdir(parents=True, exist_ok=True)

    if not full_path.exists():
        print(f"Cloning AIReg-Bench repository to {full_path}...")
        subprocess.run(
            ["git", "clone", repo_url, str(full_path)],
            check=True, capture_output=True, text=True
        )
        print("Clone complete.")
    else:
        print(f"AIReg-Bench repository exists at {full_path}. Pulling updates...")
        try:
            subprocess.run(
                ["git", "-C", str(full_path), "pull"],
                check=True, capture_output=True, text=True
            )
            print("Pull complete.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not pull updates: {e.stderr}")

    result = subprocess.run(
        ["git", "-C", str(full_path), "rev-parse", "HEAD"],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def load_human_annotations(repo_path: Path) -> Dict[str, Dict[int, float]]:
    """
    Load human annotations from Excel file.

    Returns:
        Dict mapping "Art{N}/Scenario{X}" to {use_num: compliance_score}
    """
    excel_path = repo_path / "human_annotations.xlsx"
    if not excel_path.exists():
        print(f"Warning: Annotations file not found at {excel_path}")
        return {}

    df = pd.read_excel(excel_path)
    annotations = {}

    # Row 0 is header describing columns
    # Rows 1-15 contain: Art N / Scenario X and compliance scores for each Use
    for idx in range(1, len(df)):
        row = df.iloc[idx]
        first_col = df.columns[0]
        article_scenario = str(row[first_col]).strip()

        if not article_scenario or article_scenario == 'nan':
            continue

        # Parse "Art 9 / Scenario A" format
        if "Art" not in article_scenario:
            continue

        use_scores = {}

        # Find Use columns and extract compliance scores
        for col_idx, col in enumerate(df.columns):
            col_str = str(col)
            if col_str.startswith("Use "):
                try:
                    use_num = int(col_str.replace("Use ", ""))
                    score = row[col]
                    if pd.notna(score) and isinstance(score, (int, float)):
                        use_scores[use_num] = float(score)
                except (ValueError, TypeError):
                    continue

        if use_scores:
            annotations[article_scenario] = use_scores

    return annotations


def compute_risk_label(compliance_score: float) -> str:
    """
    Compute risk label from compliance score.

    Lower compliance = higher risk:
    - score <= 2: high risk (non-compliant)
    - score <= 3: medium risk (partial compliance)
    - score > 3: low risk (compliant)
    """
    if compliance_score <= 2:
        return "high"
    elif compliance_score <= 3:
        return "medium"
    else:
        return "low"


def read_documentation_file(repo_path: Path, article: str, use: int, system: int, scenario: str) -> Optional[str]:
    """Read a documentation text file from the AIReg-Bench structure."""
    file_name = SCENARIO_TO_FILE.get(scenario)
    if not file_name:
        return None

    file_path = repo_path / "documentation" / article / f"Use{use}" / f"System{system}" / file_name

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")

    return None


def build_supervised_dataset(repo_path: Path, annotations: Dict) -> pd.DataFrame:
    """
    Build supervised dataset from all 300 AIReg-Bench documents.

    Structure: 5 articles x 3 scenarios x 10 uses x 2 systems = 300 records
    """
    records = []

    # Map article folder names to annotation format
    article_map = {
        "Article9": "Art 9",
        "Article10": "Art 10",
        "Article12": "Art 12",
        "Article14": "Art 14",
        "Article15": "Art 15"
    }

    scenario_map = {
        "A": "Scenario A",
        "B": "Scenario B",
        "C": "Scenario C"
    }

    print(f"\nBuilding dataset from {repo_path / 'documentation'}...")

    for article_folder in ARTICLES:
        article_display = article_map[article_folder]

        for scenario_letter, scenario_name in scenario_map.items():
            # Build annotation key like "Art 9 / Scenario A"
            annotation_key = f"{article_display} / {scenario_name}"
            use_scores = annotations.get(annotation_key, {})

            for use_num in range(1, 11):
                for system_num in [1, 2]:
                    text = read_documentation_file(
                        repo_path, article_folder, use_num, system_num, scenario_letter
                    )

                    if not text:
                        continue

                    # Get compliance score for this use case
                    # If we have annotation, use it; otherwise infer from scenario
                    if use_num in use_scores:
                        compliance_score = use_scores[use_num]
                    else:
                        # Infer from scenario type
                        if scenario_letter == "A":  # Compliance scenario
                            compliance_score = 4.5
                        elif scenario_letter == "B":  # Violation 1
                            compliance_score = 2.0
                        else:  # Violation 2
                            compliance_score = 1.5

                    risk_label = compute_risk_label(compliance_score)

                    # Create unique document ID
                    doc_id = f"{article_folder}_Use{use_num}_Sys{system_num}_{scenario_letter}"

                    intended_use = INTENDED_USES.get(use_num, f"Use case {use_num}")

                    records.append({
                        "doc_id": doc_id,
                        "article": article_folder,
                        "article_number": article_folder.replace("Article", ""),
                        "scenario": scenario_letter,
                        "scenario_type": "compliance" if scenario_letter == "A" else "violation",
                        "use_case": use_num,
                        "system": system_num,
                        "intended_use": intended_use,
                        "text": text,
                        "compliance_score": compliance_score,
                        "risk_label": risk_label
                    })

    df = pd.DataFrame(records)

    # Ensure text is string type
    df["text"] = df["text"].fillna("").astype(str)

    # Remove empty records
    df = df[df["text"].str.strip().str.len() > 0]

    return df


def main():
    """Build the supervised dataset from AIReg-Bench."""
    print("=" * 60)
    print("AIAudit Dataset Builder - AIReg-Bench Parser")
    print("=" * 60)

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

    print(f"\nRepository URL: {repo_url}")
    print(f"Local path: {local_path}")

    try:
        commit_sha = clone_or_pull_repo(repo_url, local_path)
        print(f"Current commit: {commit_sha[:8]}...")
    except subprocess.CalledProcessError as e:
        print(f"Error with git operations: {e}")
        return None

    repo_full_path = project_root / local_path

    if not repo_full_path.exists():
        print("Error: Repository not cloned properly.")
        return None

    # Load human annotations
    annotations = load_human_annotations(repo_full_path)
    print(f"\nLoaded annotations for {len(annotations)} article/scenario combinations")

    # Build supervised dataset
    df = build_supervised_dataset(repo_full_path, annotations)

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
    print(f"\nRecords by article:")
    for article in ARTICLES:
        count = len(df[df["article"] == article])
        print(f"  {article}: {count}")
    print(f"\nRecords by scenario type:")
    print(f"  Compliance (A): {len(df[df['scenario'] == 'A'])}")
    print(f"  Violation 1 (B): {len(df[df['scenario'] == 'B'])}")
    print(f"  Violation 2 (C): {len(df[df['scenario'] == 'C'])}")
    print(f"\nRisk label distribution:")
    for label, count in df["risk_label"].value_counts().items():
        print(f"  {label}: {count} ({100 * count / len(df):.1f}%)")

    print("\n" + "=" * 60)
    print("Dataset build complete!")
    print("=" * 60)

    return str(output_path)


if __name__ == "__main__":
    main()

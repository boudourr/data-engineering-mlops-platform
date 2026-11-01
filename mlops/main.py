"""
main.py
-------

CLI entry point for the generic MLOps pipeline.

Usage (from the project root):

    python -m mlops.main --csv path/to/dataset.csv --target column_name

The pipeline will automatically detect the target type (regression or
classification) and train an appropriate model.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Allow running as 'python -m mlops.main' from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mlops.pipeline import MLOpsPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic MLOps pipeline — train on any CSV dataset."
    )
    parser.add_argument("--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument("--target", required=True, help="Name of the target column.")
    parser.add_argument(
        "--name",
        default=None,
        help="Human-readable dataset name (defaults to CSV filename).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    dataset_name = args.name or csv_path.stem

    pipeline = MLOpsPipeline()
    result = pipeline.run(
        dataframe=df,
        target_column=args.target,
        dataset_name=dataset_name,
    )

    print()
    print(f"Status          : {result['status']}")
    print(f"Target type     : {result['target_type']}")
    print(f"Model type      : {result['model_type']}")
    print(f"Training samples: {result['training_samples']}")
    print(f"Testing samples : {result['testing_samples']}")
    print(f"Metrics         : {result['metrics']}")


if __name__ == "__main__":
    main()
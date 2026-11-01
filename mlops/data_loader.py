"""
data_loader.py
--------------

Generic dataset loader and validator for the MLOps pipeline.

Accepts any pandas DataFrame — no assumptions about column names,
Gold-layer joins, or dataset-specific schemas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


class DataLoader:
    """Load and validate any tabular dataset for ML training."""

    MIN_ROWS = 10  # Minimum usable rows after cleaning
    # A classifier creates a probability slot for every class.  Very
    # high-cardinality targets are almost always record identifiers rather
    # than meaningful labels, and can otherwise require hundreds of GB.
    MAX_CLASSIFICATION_CLASSES = 100
    MAX_CLASSIFICATION_UNIQUE_RATIO = 0.50

    # ==================================================
    # Load from File
    # ==================================================

    def load_from_path(self, path: Path) -> pd.DataFrame:
        """Load a CSV, Parquet, or Excel file into a DataFrame."""
        path = Path(path)
        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        if ext == ".parquet":
            return pd.read_parquet(path)
        if ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        raise ValueError(f"Unsupported file type: {ext}")

    # ==================================================
    # Validate Target Column
    # ==================================================

    def validate_target(
        self,
        df: pd.DataFrame,
        target_column: str,
    ) -> Tuple[bool, str]:
        """
        Check that the target column is usable for ML.

        Returns (is_valid, error_message).
        """
        if target_column not in df.columns:
            return False, f"Column '{target_column}' not found in dataset."

        series = df[target_column]

        non_null = series.dropna()
        if len(non_null) == 0:
            return False, f"Column '{target_column}' contains only missing values."

        if len(non_null) < self.MIN_ROWS:
            return (
                False,
                f"Column '{target_column}' has only {len(non_null)} "
                f"non-null values (minimum required: {self.MIN_ROWS}).",
            )

        if non_null.nunique() < 2:
            return (
                False,
                f"Column '{target_column}' has fewer than 2 unique values "
                "and cannot be used as a target.",
            )

        # Text/category targets with mostly unique values are identifiers or
        # free text, not a viable classification label.  Validate this before
        # fitting so scikit-learn never attempts an enormous class matrix.
        if not pd.api.types.is_numeric_dtype(non_null):
            unique_count = non_null.nunique()
            unique_ratio = unique_count / len(non_null)
            if (
                unique_count > self.MAX_CLASSIFICATION_CLASSES
                or unique_ratio > self.MAX_CLASSIFICATION_UNIQUE_RATIO
            ):
                return (
                    False,
                    f"Column '{target_column}' has {unique_count:,} distinct values "
                    f"across {len(non_null):,} rows. It looks like an identifier or "
                    "free-text field and cannot be used as a classification target. "
                    "Choose a categorical column with at most "
                    f"{self.MAX_CLASSIFICATION_CLASSES} classes or a numeric target.",
                )

        return True, ""

    # ==================================================
    # Prepare Dataset
    # ==================================================

    def prepare_dataset(
        self,
        df: pd.DataFrame,
        target_column: str,
    ) -> pd.DataFrame:
        """
        Clean and validate a DataFrame for ML training.

        Steps
        -----
        1. Validate target column.
        2. Drop completely empty columns (all NaN).
        3. Drop duplicate rows.
        4. Drop rows where the target is missing.

        Returns a clean copy ready for feature engineering.
        """
        if target_column not in df.columns:
            raise ValueError(f"Column '{target_column}' not found in dataset.")

        result = df.copy()

        # Drop columns that are entirely null
        all_null_cols = result.columns[result.isna().all()].tolist()
        if all_null_cols:
            result = result.drop(columns=all_null_cols)
            print(f"Dropped {len(all_null_cols)} fully-null column(s): {all_null_cols}")

        # Drop duplicate rows
        before = len(result)
        result = result.drop_duplicates()
        dropped = before - len(result)
        if dropped:
            print(f"Dropped {dropped} duplicate row(s).")

        # Drop rows where target is missing
        before = len(result)
        result = result.dropna(subset=[target_column])
        dropped = before - len(result)
        if dropped:
            print(f"Dropped {dropped} row(s) with missing target '{target_column}'.")

        # Validation must run after cleaning: duplicate rows and missing target
        # values can otherwise make a target appear usable when it is not.
        valid, error = self.validate_target(result, target_column)
        if not valid:
            raise ValueError(error)

        print()
        print("=" * 60)
        print("DATASET PREPARED")
        print("=" * 60)
        print(f"Rows    : {len(result)}")
        print(f"Columns : {len(result.columns)}")
        print()

        return result


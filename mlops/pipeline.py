"""
pipeline.py
-----------

Generic end-to-end MLOps pipeline.

API
---
    pipeline = MLOpsPipeline()
    result = pipeline.run(dataframe=df, target_column="revenue")

The pipeline accepts any pandas DataFrame and a user-selected target column.
It automatically validates, preprocesses, trains, evaluates, and generates
predictions for any tabular dataset.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd

from mlops.config import (
    CLASSIFICATION_UNIQUE_THRESHOLD,
    get_run_paths,
    FEATURES_PATH,
    METADATA_PATH,
    MODEL_PATH,
    PREDICTIONS_PATH,
    PREPROCESSOR_PATH,
)
from mlops.data_loader import DataLoader
from mlops.evaluator import ModelEvaluator
from mlops.predictor import Predictor
from mlops.trainer import ModelTrainer


def infer_target_type(series: pd.Series) -> str:
    """
    Infer whether a target series is regression or classification.

    Rules
    -----
    - Non-numeric dtype (object, category, bool) -> classification
    - Numeric with <= CLASSIFICATION_UNIQUE_THRESHOLD unique values -> classification
    - Otherwise -> regression
    """
    clean = series.dropna()
    if not pd.api.types.is_numeric_dtype(clean):
        return "classification"
    if clean.nunique() <= CLASSIFICATION_UNIQUE_THRESHOLD:
        return "classification"
    return "regression"


class MLOpsPipeline:
    """Generic ML pipeline — dataset-driven, configured entirely at runtime."""

    def __init__(self) -> None:
        self.loader = DataLoader()
        self.trainer = ModelTrainer()
        self.evaluator = ModelEvaluator()
        self.predictor = Predictor()

    # =====================================================
    # Run Pipeline
    # =====================================================

    def run(
        self,
        dataframe: pd.DataFrame,
        target_column: str,
        dataset_name: str = "dataset",
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute the full generic MLOps pipeline.

        Parameters
        ----------
        dataframe:
            Raw uploaded dataset as a pandas DataFrame.
        target_column:
            Name of the column to predict.
        dataset_name:
            Human-readable name used in metadata output.

        Returns
        -------
        Structured result dict with status, metrics, predictions DataFrame,
        and artifact paths.
        """
        print("=" * 70)
        print("STARTING GENERIC MLOPS PIPELINE")
        print(f"Dataset : {dataset_name}")
        print(f"Target  : {target_column}")
        print("=" * 70)

        # -----------------------------------------------
        # Step 1: Validate and clean data
        # -----------------------------------------------

        df = self.loader.prepare_dataset(dataframe, target_column)

        print(f"Dataset loaded: {len(df)} rows x {len(df.columns)} columns")

        # -----------------------------------------------
        # Step 2: Infer target type
        # -----------------------------------------------

        target_type = infer_target_type(df[target_column])
        print(f"Target type inferred: {target_type}")

        # -----------------------------------------------
        # Steps 3-4: Train model
        # (feature detection + preprocessing + split + fit)
        # -----------------------------------------------
        
        save_paths = get_run_paths(run_id) if run_id else None
        m_path = save_paths["model"] if save_paths else MODEL_PATH
        p_path = save_paths["preprocessor"] if save_paths else PREPROCESSOR_PATH
        f_path = save_paths["features"] if save_paths else FEATURES_PATH
        meta_path = save_paths["metadata"] if save_paths else METADATA_PATH
        pred_path = save_paths["predictions"] if save_paths else PREDICTIONS_PATH

        train_result = self.trainer.train(df, target_column, target_type, save_paths=save_paths)

        # -----------------------------------------------
        # Step 5: Evaluate model
        # -----------------------------------------------

        metrics = self.evaluator.evaluate(
            model=train_result.model,
            preprocessor=train_result.preprocessor,
            X_test=train_result.X_test,
            y_test=train_result.y_test,
            target_type=target_type,
        )

        # -----------------------------------------------
        # Step 6: Generate predictions
        # -----------------------------------------------

        predictions_df = self.predictor.predict(
            model=train_result.model,
            preprocessor=train_result.preprocessor,
            df=df,
            target_column=target_column,
            feature_columns=train_result.feature_columns,
            target_type=target_type,
            predictions_path=pred_path,
        )

        # -----------------------------------------------
        # Step 7: Write metadata.json
        # -----------------------------------------------
        
        metadata = {
            "dataset": dataset_name,
            "target_column": target_column,
            "target_type": target_type,
            "model_type": train_result.model_type,
            "features": train_result.feature_columns,
            "numerical_features": train_result.numerical_features,
            "categorical_features": train_result.categorical_features,
            "training_samples": train_result.training_samples,
            "testing_samples": train_result.testing_samples,
            "metrics": metrics,
            "prediction_column": f"predicted_{target_column}",
            "predictions_path": str(pred_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(metadata, indent=2, default=str),
            encoding="utf-8",
        )

        print()
        print("=" * 70)
        print("MLOPS PIPELINE FINISHED SUCCESSFULLY")
        print("=" * 70)
        print("v Dataset loaded")
        print("v Target validated")
        print("v Features detected")
        print("v Data preprocessing completed")
        print("v Train/test split completed")
        print("v Model trained")
        print("v Model evaluated")
        print("v Predictions generated")
        print("v Metadata saved")

        return {
            "status": "SUCCESS",
            "dataset_name": dataset_name,
            "target_column": target_column,
            "target_type": target_type,
            "model_type": train_result.model_type,
            "features": train_result.feature_columns,
            "numerical_features": train_result.numerical_features,
            "categorical_features": train_result.categorical_features,
            "training_samples": train_result.training_samples,
            "testing_samples": train_result.testing_samples,
            "metrics": metrics,
            "predictions": predictions_df,
            "artifacts": {
                "model": m_path,
                "preprocessor": p_path,
                "feature_columns": f_path,
                "metadata": meta_path,
                "predictions": pred_path,
            },
        }

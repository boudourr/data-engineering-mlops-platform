"""Regression tests for MLOps validation and prediction safeguards."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

from mlops.data_loader import DataLoader
from mlops.predictor import Predictor
from mlops.trainer import ModelTrainer


class _PassthroughPreprocessor:
    def transform(self, dataframe: pd.DataFrame) -> np.ndarray:
        return dataframe.to_numpy()


class _ConstantModel:
    def predict(self, features: np.ndarray) -> np.ndarray:
        return np.full(len(features), 2.5)


class MLOpsReliabilityTests(unittest.TestCase):
    def test_validation_runs_after_target_nulls_are_removed(self) -> None:
        dataframe = pd.DataFrame(
            {"feature": range(10), "target": [None] * 9 + ["only-value"]}
        )

        with self.assertRaisesRegex(ValueError, "only 1 non-null values"):
            DataLoader().prepare_dataset(dataframe, "target")

    def test_high_cardinality_text_target_is_rejected(self) -> None:
        dataframe = pd.DataFrame(
            {"feature": range(101), "target": [f"id-{index}" for index in range(101)]}
        )

        with self.assertRaisesRegex(ValueError, "cannot be used as a classification target"):
            DataLoader().prepare_dataset(dataframe, "target")

    def test_feature_limit_is_enforced(self) -> None:
        dataframe = pd.DataFrame({f"feature_{index}": [0, 1, 0] for index in range(2005)})
        dataframe["target"] = [1, 2, 3]

        numerical, categorical = ModelTrainer().detect_features(dataframe, "target")

        self.assertEqual(len(numerical) + len(categorical), ModelTrainer.MAX_TOTAL_FEATURES)

    def test_only_regression_outputs_a_prediction_error(self) -> None:
        dataframe = pd.DataFrame({"feature": [1.0, 2.0], "target": [2.0, 3.0]})
        predictor = Predictor()

        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "predictions.csv"
            regression_output = predictor.predict(
                _ConstantModel(),
                _PassthroughPreprocessor(),
                dataframe,
                "target",
                ["feature"],
                "regression",
                output_path,
            )
            classification_output = predictor.predict(
                _ConstantModel(),
                _PassthroughPreprocessor(),
                dataframe,
                "target",
                ["feature"],
                "classification",
            )

            self.assertTrue(output_path.exists())
            self.assertIn("prediction_error", regression_output.columns)
            self.assertNotIn("prediction_error", classification_output.columns)


if __name__ == "__main__":
    unittest.main()

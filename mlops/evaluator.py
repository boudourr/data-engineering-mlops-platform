"""
evaluator.py
------------

Generic model evaluator.

Computes regression metrics (MAE, RMSE, R²) or classification metrics
(Accuracy, Precision, Recall, F1) depending on the target type.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


class ModelEvaluator:
    """Evaluate a trained model on a held-out test set."""

    # ==================================================
    # Evaluate
    # ==================================================

    def evaluate(
        self,
        model,
        preprocessor,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        target_type: str,
    ) -> dict:
        """
        Generate evaluation metrics for the given model and test set.

        Parameters
        ----------
        model:
            Fitted sklearn estimator.
        preprocessor:
            Fitted ColumnTransformer used during training.
        X_test:
            Raw (un-transformed) test features as a DataFrame.
        y_test:
            Ground-truth target values.
        target_type:
            'regression' or 'classification'.

        Returns
        -------
        dict with metric keys and float values.
        """
        X_test_transformed = preprocessor.transform(X_test)
        predictions = model.predict(X_test_transformed)

        if target_type == "regression":
            return self._regression_metrics(y_test, predictions)
        return self._classification_metrics(y_test, predictions)

    # ==================================================
    # Regression Metrics
    # ==================================================

    def _regression_metrics(self, y_true, y_pred) -> dict:
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))

        print()
        print("=" * 60)
        print("MODEL EVALUATION — REGRESSION")
        print("=" * 60)
        print(f"MAE  : {mae:.4f}")
        print(f"RMSE : {rmse:.4f}")
        print(f"R²   : {r2:.4f}")
        print()

        return {
            "target_type": "regression",
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
        }

    # ==================================================
    # Classification Metrics
    # ==================================================

    def _classification_metrics(self, y_true, y_pred) -> dict:
        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        )
        recall = float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        )
        f1 = float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        )
        report = classification_report(y_true, y_pred, zero_division=0)

        print()
        print("=" * 60)
        print("MODEL EVALUATION — CLASSIFICATION")
        print("=" * 60)
        print(f"Accuracy  : {accuracy:.4f}")
        print(f"Precision : {precision:.4f}")
        print(f"Recall    : {recall:.4f}")
        print(f"F1        : {f1:.4f}")
        print()
        print(report)

        return {
            "target_type": "classification",
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "classification_report": report,
        }
"""
predictor.py
------------

Generic prediction generator.

Works with any dataset and any target column. The prediction column is
named dynamically as 'predicted_{target_column}'.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

class Predictor:
    """Generate predictions using a trained model and preprocessor."""

    # ==================================================
    # Predict
    # ==================================================

    def predict(
        self,
        model,
        preprocessor,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: List[str],
        target_type: str,
        predictions_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        """
        Generate predictions for the full dataset.

        Parameters
        ----------
        model:
            Fitted sklearn estimator.
        preprocessor:
            Fitted ColumnTransformer (same as used during training).
        df:
            Clean DataFrame (same schema as training data).
        target_column:
            The column that was used as the prediction target.
        feature_columns:
            List of original feature column names (before preprocessing).
        target_type:
            ``regression`` or ``classification``. Error values are only
            meaningful for regression targets.
        predictions_path:
            Optional destination for the resulting CSV. The caller owns
            persistence so each pipeline run writes exactly one artifact.

        Returns
        -------
        DataFrame with original columns plus 'predicted_{target_column}'
        and, for regression, 'prediction_error'.
        """
        prediction_col = f"predicted_{target_column}"

        # -----------------------------------------------
        # Prepare feature matrix
        # -----------------------------------------------

        # Keep only the feature columns used during training
        missing_features = [column for column in feature_columns if column not in df.columns]
        if missing_features:
            raise ValueError(
                "Cannot generate predictions because required feature columns are missing: "
                + ", ".join(map(str, missing_features[:10]))
            )
        X = df[feature_columns].copy()

        # -----------------------------------------------
        # Transform features
        # -----------------------------------------------

        X_transformed = preprocessor.transform(X)

        # -----------------------------------------------
        # Generate predictions
        # -----------------------------------------------

        raw_predictions = model.predict(X_transformed)

        # -----------------------------------------------
        # Build output DataFrame
        # -----------------------------------------------

        output = df.copy()
        output[prediction_col] = raw_predictions

        # An arithmetic residual only makes sense for regression targets.
        if target_type == "regression" and target_column in output.columns:
            try:
                actual = pd.to_numeric(output[target_column], errors="coerce")
                predicted = pd.to_numeric(output[prediction_col], errors="coerce")
                if actual.notna().any() and predicted.notna().any():
                    output["prediction_error"] = actual - predicted
            except Exception:
                pass  # Not a regression target or unsuitable for arithmetic

        # -----------------------------------------------
        # Save predictions
        # -----------------------------------------------

        if predictions_path is not None:
            predictions_path = Path(predictions_path)
            predictions_path.parent.mkdir(parents=True, exist_ok=True)
            output.to_csv(predictions_path, index=False)

        # -----------------------------------------------
        # Logs
        # -----------------------------------------------

        print()
        print("=" * 60)
        print("PREDICTIONS GENERATED")
        print("=" * 60)
        print(f"Rows predicted   : {len(output)}")
        print(f"Target           : {target_column}")
        print(f"Prediction column: {prediction_col}")
        if predictions_path is not None:
            print(f"Saved to         : {predictions_path}")
        print()

        return output

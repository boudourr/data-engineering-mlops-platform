"""
trainer.py
----------

Generic ML model trainer.

Works with any tabular dataset. Target column, target type (regression vs
classification), and features are supplied at runtime — nothing is
hard-coded.
"""

from __future__ import annotations

import joblib
from dataclasses import dataclass
from typing import List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.linear_model import LinearRegression, LogisticRegression

from mlops.config import (
    FEATURES_PATH,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    RANDOM_STATE,
    TEST_SIZE,
)


@dataclass
class TrainResult:
    """Structured output from a training run."""

    model: object
    preprocessor: object
    X_test: pd.DataFrame
    y_test: pd.Series
    feature_columns: List[str]
    numerical_features: List[str]
    categorical_features: List[str]
    training_samples: int
    testing_samples: int
    target_column: str
    target_type: str
    model_type: str


class ModelTrainer:
    """Train a scikit-learn model for any tabular dataset."""

    # ==================================================
    # Detect Feature Types
    # ==================================================

    MAX_CARDINALITY = 50
    MAX_TOTAL_FEATURES = 2000

    def detect_features(
        self,
        df: pd.DataFrame,
        target_column: str,
    ):
        """
        Split columns into numerical and categorical features.

        The target column is excluded from both lists.
        - High-cardinality categorical columns (> MAX_CARDINALITY unique)
          are dropped to prevent memory explosion during one-hot encoding.
        - Numeric columns that look like identifiers (very high unique ratio)
          are also dropped since they add no predictive signal.
        """
        n_rows = len(df)
        feature_cols = [c for c in df.columns if c != target_column]

        def is_identifier(series) -> bool:
            non_null = series.dropna()
            if len(non_null) == 0:
                return False
            unique_ratio = series.nunique(dropna=True) / len(non_null)
            return unique_ratio > 0.95

        numerical = []
        categorical = []

        for c in feature_cols:
            series = df[c]
            if pd.api.types.is_numeric_dtype(series):
                if is_identifier(series):
                    continue
                numerical.append(c)
            else:
                if series.nunique(dropna=True) <= self.MAX_CARDINALITY:
                    categorical.append(c)

        # Keep the input width bounded for generic warehouse exports.  The
        # limit is applied here (rather than only documented as a constant)
        # so an unusually wide table cannot exhaust memory before training.
        selected_features = numerical + categorical
        if len(selected_features) > self.MAX_TOTAL_FEATURES:
            selected_features = selected_features[:self.MAX_TOTAL_FEATURES]
            selected = set(selected_features)
            numerical = [column for column in numerical if column in selected]
            categorical = [column for column in categorical if column in selected]
            print(
                f"Limited model inputs to {self.MAX_TOTAL_FEATURES:,} features "
                "to keep memory use bounded."
            )

        return numerical, categorical

    # ==================================================
    # Build Preprocessor
    # ==================================================

    def build_preprocessor(
        self,
        numerical_features: List[str],
        categorical_features: List[str],
    ) -> ColumnTransformer:
        """
        Build a ColumnTransformer that handles numerical and categorical
        features independently.
        """
        transformers = []

        if numerical_features:
            num_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ])
            transformers.append(("num", num_pipeline, numerical_features))

        if categorical_features:
            cat_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=True,
                        max_categories=self.MAX_CARDINALITY,
                    ),
                ),
            ])
            transformers.append(("cat", cat_pipeline, categorical_features))

        return ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            # Keep one-hot data sparse even when the encoded matrix happens
            # to be relatively dense.  This prevents a large dense allocation
            # when a warehouse has many categorical columns.
            sparse_threshold=1.0,
        )

    # ==================================================
    # Select Model
    # ==================================================

    def select_model(self, target_type: str, dataset_size: int = 0):
        """Return an appropriate sklearn estimator for the target type."""
        # Fast fallback for large datasets (>= 50,000 rows)
        if dataset_size >= 50000:
             print("Dataset >= 50,000 rows. Using lightweight linear models.")
             if target_type == "regression":
                 return LinearRegression()
             return LogisticRegression(random_state=RANDOM_STATE, n_jobs=-1, max_iter=1000)

        # Default random forest
        if target_type == "regression":
            return RandomForestRegressor(
                n_estimators=100,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        return RandomForestClassifier(
            n_estimators=100,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    # ==================================================
    # Train
    # ==================================================

    def train(
        self,
        df: pd.DataFrame,
        target_column: str,
        target_type: str,
        save_paths: dict = None
    ) -> TrainResult:
        """
        Train a model on *df* predicting *target_column*.

        Parameters
        ----------
        df:
            Clean DataFrame (output of DataLoader.prepare_dataset).
        target_column:
            Name of the column to predict.
        target_type:
            'regression' or 'classification'.
        save_paths:
            Dictionary of paths to save artifacts. If None, uses legacy global paths.

        Returns
        -------
        TrainResult dataclass with trained model, preprocessor, test split,
        and metadata.
        """
        # -----------------------------------------------
        # Separate X and y
        # -----------------------------------------------

        y = df[target_column]

        # -----------------------------------------------
        # Detect feature types
        # -----------------------------------------------

        numerical_features, categorical_features = self.detect_features(
            df, target_column
        )

        feature_columns = numerical_features + categorical_features
        if not feature_columns:
            raise ValueError(
                "No usable model features were found after excluding identifiers, "
                "high-cardinality categories, and the target column."
            )

        # Do not carry discarded warehouse columns into the split.  Apart
        # from reducing memory, this ensures the prediction schema exactly
        # matches the preprocessor's input schema.
        X = df[feature_columns].copy()

        print(f"Numerical features  : {len(numerical_features)}")
        print(f"Categorical features: {len(categorical_features)}")

        # -----------------------------------------------
        # Build preprocessor
        # -----------------------------------------------

        preprocessor = self.build_preprocessor(
            numerical_features, categorical_features
        )

        # -----------------------------------------------
        # Select model
        # -----------------------------------------------

        model = self.select_model(target_type, len(df))
        model_type = type(model).__name__

        # -----------------------------------------------
        # Train / Test Split
        # -----------------------------------------------

        stratify = None
        if target_type == "classification":
            try:
                # Stratify only if every class has >= 2 members
                if y.value_counts().min() >= 2:
                    stratify = y
            except Exception:
                pass

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=stratify,
        )

        # -----------------------------------------------
        # Fit preprocessor on training data
        # -----------------------------------------------

        X_train_transformed = preprocessor.fit_transform(X_train)

        # -----------------------------------------------
        # Train model on transformed training data
        # -----------------------------------------------

        model.fit(X_train_transformed, y_train)

        # -----------------------------------------------
        # Save artifacts
        # -----------------------------------------------

        m_path = save_paths["model"] if save_paths else MODEL_PATH
        p_path = save_paths["preprocessor"] if save_paths else PREPROCESSOR_PATH
        f_path = save_paths["features"] if save_paths else FEATURES_PATH

        joblib.dump(model, m_path)
        joblib.dump(preprocessor, p_path)
        joblib.dump(feature_columns, f_path)

        # -----------------------------------------------
        # Logs
        # -----------------------------------------------

        print()
        print("=" * 60)
        print("MODEL TRAINED SUCCESSFULLY")
        print("=" * 60)
        print(f"Target column    : {target_column}")
        print(f"Target type      : {target_type}")
        print(f"Model type       : {model_type}")
        print(f"Training samples : {len(X_train)}")
        print(f"Testing samples  : {len(X_test)}")
        print(f"Total features   : {len(feature_columns)}")
        print()
        print(f"Model saved to         : {m_path}")
        print(f"Preprocessor saved to  : {p_path}")
        print(f"Feature list saved to  : {f_path}")
        print()

        return TrainResult(
            model=model,
            preprocessor=preprocessor,
            X_test=X_test,
            y_test=y_test,
            feature_columns=feature_columns,
            numerical_features=numerical_features,
            categorical_features=categorical_features,
            training_samples=len(X_train),
            testing_samples=len(X_test),
            target_column=target_column,
            target_type=target_type,
            model_type=model_type,
        )



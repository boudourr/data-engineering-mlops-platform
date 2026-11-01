"""
config.py
---------

Generic configuration for the MLOps pipeline.

All paths are dataset-independent.  Target column, model type, and feature
names are determined at runtime by the user and the pipeline — never
hard-coded here.
"""

from pathlib import Path

# ==========================================================
# Project Directories
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FOLDER = PROJECT_ROOT / "models"

PREDICTION_FOLDER = PROJECT_ROOT / "predictions"

# Create folders automatically
MODEL_FOLDER.mkdir(parents=True, exist_ok=True)
PREDICTION_FOLDER.mkdir(parents=True, exist_ok=True)

# ==========================================================
# Generic Output Artifact Paths
# ==========================================================

def get_run_paths(run_id: str) -> dict:
    """Return run-specific paths for MLOps artifacts."""
    run_model_folder = MODEL_FOLDER / run_id
    run_prediction_folder = PREDICTION_FOLDER / run_id
    
    run_model_folder.mkdir(parents=True, exist_ok=True)
    run_prediction_folder.mkdir(parents=True, exist_ok=True)
    
    return {
        "model": run_model_folder / "model.pkl",
        "preprocessor": run_model_folder / "preprocessor.pkl",
        "features": run_model_folder / "feature_columns.pkl",
        "metadata": run_model_folder / "metadata.json",
        "predictions": run_prediction_folder / "predictions.csv",
    }

# Fallbacks for legacy callers
MODEL_PATH = MODEL_FOLDER / "model.pkl"
PREPROCESSOR_PATH = MODEL_FOLDER / "preprocessor.pkl"
FEATURES_PATH = MODEL_FOLDER / "feature_columns.pkl"
METADATA_PATH = MODEL_FOLDER / "metadata.json"
PREDICTIONS_PATH = PREDICTION_FOLDER / "predictions.csv"

# ==========================================================
# Machine Learning Defaults
# ==========================================================

TEST_SIZE = 0.20

RANDOM_STATE = 42

# Threshold: if a numeric target has <= this many unique values
# it is treated as a classification problem.
CLASSIFICATION_UNIQUE_THRESHOLD = 20
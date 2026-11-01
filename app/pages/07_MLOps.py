"""MLOps page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.run_context import get_current_run
from core.ui_helpers import (
    display_dataset_summary,
    display_result_table,
    display_schema,
    initialize_session_state,
    page_header,
    preview_dataset,
    section_title,
    show_execution_result,
)
from mlops.pipeline import MLOpsPipeline
from mlops.config import MODEL_PATH, FEATURES_PATH, PREDICTIONS_PATH


def main() -> None:
    """Render the MLOps dashboard."""
    st.set_page_config(
        page_title="MLOps | Modern Data Engineering Platform",
        page_icon=":robot_face:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"mlops_results": None, "target_column": None})

    page_header(
        "MLOps",
        "Train a predictive model from the warehouse output, evaluate its performance, and inspect predictions.",
        icon=":material/smart_toy:",
    )
    
    run_context = get_current_run()

    if not run_context:
        st.warning("No active run context found. Falling back to default Olist execution. Please upload a dataset in Data Upload.")

    render_pipeline_controls(run_context)
    st.divider()
    render_outputs(run_context)


def load_warehouse_data(run_context) -> tuple[pd.DataFrame | None, list[str]]:
    """Load data from warehouse for training."""
    gold_dir = Path(run_context.gold_dir) if run_context else PROJECT_ROOT / "data" / "gold"
    
    # Simple heuristic: try to find a Fact table, or if not, use the first generic table, else fall back to customers
    candidates = list(gold_dir.glob("Fact_*.csv"))
    if not candidates:
        candidates = list(gold_dir.glob("*.csv"))
        
    if not candidates:
        return None, []
        
    df = pd.read_csv(candidates[0])
    return df, list(df.columns)

def render_pipeline_controls(run_context) -> None:
    """Render the MLOps pipeline controls and execution status."""
    section_title(
        "Model Training",
        "Select a target column and run the MLOps pipeline to build, evaluate, and save a predictive model.",
    )
    
    df, columns = load_warehouse_data(run_context)
    
    if df is None:
        st.error("No warehouse data found. Please run the Warehouse pipeline first.")
        return
        
    target_column = st.selectbox(
        "Select Target Column for Prediction", 
        options=columns,
        index=len(columns)-1 if columns else 0
    )
    
    st.session_state.target_column = target_column

    if st.button("Run MLOps pipeline", type="primary", use_container_width=True):
        with st.spinner("Training model and generating predictions..."):
            result = run_mlops_pipeline(df, target_column, run_context)
        st.session_state.mlops_results = result
        show_execution_result(result)

    results_payload = st.session_state.get("mlops_results")
    if results_payload:
        st.caption(f"Last run: {results_payload.get('message', 'No message available')}")


def render_outputs(run_context) -> None:
    """Render generated model artifacts and predictions if they exist."""
    section_title("Generated Outputs")

    if run_context:
        from mlops.config import get_run_paths
        paths = get_run_paths(run_context.run_id)
        m_path = paths["model"]
        f_path = paths["features"]
        pred_path = paths["predictions"]
    else:
        m_path = MODEL_PATH
        f_path = FEATURES_PATH
        pred_path = PREDICTIONS_PATH
        
    artifacts = [
        ("Model", m_path),
        ("Feature columns", f_path),
        ("Predictions", pred_path),
    ]

    available_artifacts = []
    for label, path in artifacts:
        resolved = Path(path)
        if resolved.exists():
            available_artifacts.append((label, resolved))

    if not available_artifacts:
        st.info("No MLOps outputs have been generated yet. Run the pipeline to create them.")
        return

    display_result_table(
        [
            {
                "Artifact": label,
                "Path": str(path),
                "Exists": path.exists(),
                "Size (bytes)": path.stat().st_size if path.exists() else 0,
            }
            for label, path in available_artifacts
        ]
    )

    if pred_path.exists():
        selected_prediction = st.selectbox(
            "Inspect prediction output",
            options=[None, pred_path],
            format_func=lambda path: "Select a file" if path is None else path.name,
            key="mlops_selected_predictions",
        )
        if selected_prediction is not None:
            render_prediction_preview(selected_prediction)


def render_prediction_preview(path: Path) -> None:
    """Preview the generated predictions file."""
    section_title(f"{path.name} Preview")

    try:
        dataframe = pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read {path.name}: {exc}")
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


def run_mlops_pipeline(df: pd.DataFrame, target_column: str, run_context) -> dict[str, Any]:
    """Run the existing MLOps pipeline and return a user-friendly result summary."""
    previous_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        pipeline = MLOpsPipeline()
        run_id = run_context.run_id if run_context else None
        result = pipeline.run(dataframe=df, target_column=target_column, dataset_name="warehouse_data", run_id=run_id)
    except Exception as exc:
        return {
            "status": "failed",
            "message": f"MLOps pipeline failed: {exc}",
            "error": str(exc),
        }
    finally:
        os.chdir(previous_cwd)

    metrics = result.get("metrics", {}) if isinstance(result, dict) else {}
    
    if run_context:
        from mlops.config import get_run_paths
        paths = get_run_paths(run_context.run_id)
        pred_path = paths["predictions"]
        mod_path = paths["model"]
    else:
        pred_path = PREDICTIONS_PATH
        mod_path = MODEL_PATH
        
    return {
        "status": "success",
        "message": "MLOps pipeline completed successfully.",
        "metrics": metrics,
        "predictions_path": str(pred_path),
        "model_path": str(mod_path),
    }


if __name__ == "__main__":
    main()

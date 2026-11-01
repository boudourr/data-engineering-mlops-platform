"""Data quality page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Optional

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.data_manager import DataManager, DatasetRecord
from core.ui_helpers import (
    display_dataset_summary,
    display_result_table,
    display_schema,
    initialize_session_state,
    page_header,
    preview_dataset,
    section_title,
)
from etl.validator import DataValidator
from profiling.quality import DataQualityAnalyzer


def main() -> None:
    """Render the data quality dashboard."""
    st.set_page_config(
        page_title="Data Quality | Modern Data Engineering Platform",
        page_icon=":memo:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"data_quality_results": None})
    data_manager = DataManager(config.uploads_directory)

    page_header(
        "Data Quality",
        "Measure profile-derived quality dimensions and ETL validation results for your datasets.",
        icon=":material/fact_check:",
    )

    render_dataset_selection(data_manager)
    st.divider()
    render_quality_controls(data_manager)
    st.divider()
    render_quality_results()


def render_dataset_selection(data_manager: DataManager) -> None:
    """Render the saved-dataset picker and input preview."""
    section_title(
        "Available Datasets",
        "Choose a dataset to assess for completeness, uniqueness, missingness, and validation issues.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        st.info("No saved datasets are available yet. Upload datasets on the Data Upload page first.")
        return

    selected_dataset = st.selectbox(
        "Select a dataset",
        options=[None, *datasets],
        format_func=lambda dataset: "Select a dataset" if dataset is None else dataset.filename,
        key="data_quality_selected_dataset",
    )

    if selected_dataset is None:
        st.info("Select a dataset to inspect and evaluate.")
        return

    render_dataset_inspector(data_manager, selected_dataset)


def render_dataset_inspector(data_manager: DataManager, dataset: DatasetRecord) -> None:
    """Show input dataset metadata and a preview."""
    section_title("Input Dataset")
    display_result_table(asdict(dataset))

    dataframe, error = load_dataset_safely(data_manager, dataset)
    if error:
        st.warning(error)
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


def render_quality_controls(data_manager: DataManager) -> None:
    """Run both profiling-based and ETL validation-based quality checks."""
    section_title(
        "Quality Checks",
        "Evaluate the selected dataset with both generic profiling scores and ETL validation rules.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        return

    selected_dataset = st.session_state.get("data_quality_selected_dataset")
    if selected_dataset is None:
        st.info("Choose a dataset before running data quality checks.")
        return

    primary_key_input = st.text_input(
        "Primary key (optional, comma-separated)",
        key="data_quality_primary_key",
    )
    required_columns_input = st.text_input(
        "Required columns (optional, comma-separated)",
        key="data_quality_required_columns",
    )

    if st.button("Run quality checks", type="primary", use_container_width=True):
        dataframe, error = load_dataset_safely(data_manager, selected_dataset)
        if error:
            st.error(error)
            return

        with st.spinner(f"Assessing {selected_dataset.filename}..."):
            primary_keys = [column.strip() for column in primary_key_input.split(",") if column.strip()]
            required_columns = [column.strip() for column in required_columns_input.split(",") if column.strip()]

            profiling_analyzer = DataQualityAnalyzer(dataframe=dataframe, primary_key=primary_keys[0] if primary_keys else None)
            profiling_results = profiling_analyzer.run()

            validator = DataValidator(
                dataframe=dataframe,
                table_name=selected_dataset.filename,
                primary_key=primary_keys,
                required_columns=required_columns,
            )
            validation_report = validator.validate()

            st.session_state.data_quality_results = {
                "dataset": asdict(selected_dataset),
                "profiling_results": profiling_results,
                "validation_report": validation_report,
            }

        st.success("Quality checks completed successfully.")


def render_quality_results() -> None:
    """Render the latest quality results in a tabbed layout."""
    section_title("Quality Results")

    results_payload = st.session_state.get("data_quality_results")
    if not results_payload:
        st.info("Run data quality checks to inspect missingness, validity, and data quality scores.")
        return

    profiling_results = results_payload.get("profiling_results")
    validation_report = results_payload.get("validation_report")

    profiling_tab, validation_tab = st.tabs(["Profiling Metrics", "ETL Validation"])

    with profiling_tab:
        if isinstance(profiling_results, Mapping):
            render_profile_quality(profiling_results)
        else:
            st.info("No profiling quality metrics were generated.")

    with validation_tab:
        if isinstance(validation_report, Mapping):
            render_validation_quality(validation_report)
        else:
            st.info("No ETL validation results were generated.")


def render_profile_quality(results: Mapping[str, Any]) -> None:
    """Render the profiling-based quality views."""
    for key in ("missing_values", "missing_percentage", "empty_strings", "quality_summary"):
        value = results.get(key)
        if value is None:
            continue
        if isinstance(value, pd.DataFrame):
            st.subheader(key.replace("_", " ").title())
            st.dataframe(value, use_container_width=True, hide_index=True)
        else:
            display_result_table({key: value})

    if results.get("duplicate_rows") is not None:
        st.metric("Duplicate Rows", int(results.get("duplicate_rows")))
    if results.get("duplicate_primary_keys") is not None:
        st.metric("Duplicate Primary Keys", int(results.get("duplicate_primary_keys")))


def render_validation_quality(report: Mapping[str, Any]) -> None:
    """Render ETL validation outcomes and calculated quality score."""
    if report.get("quality_score") is not None:
        st.metric("Validation Quality Score", int(report.get("quality_score")))

    display_result_table(report)


def load_dataset_safely(
    data_manager: DataManager,
    dataset: DatasetRecord,
) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a saved dataset and return ``(dataframe, error_message)``."""
    try:
        return data_manager.load_dataset(dataset.dataset_id), None
    except Exception as exc:
        return None, f"Could not load the selected dataset: {exc}"


if __name__ == "__main__":
    main()

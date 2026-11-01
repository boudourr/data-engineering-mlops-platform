"""Profiling page for the Generic Modern Data Engineering Platform."""

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
from profiling.profiler import DataProfiler


def main() -> None:
    """Render the dataset profiling dashboard."""
    st.set_page_config(
        page_title="Profiling | Modern Data Engineering Platform",
        page_icon=":microscope:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"profiling_results": None})
    data_manager = DataManager(config.uploads_directory)

    page_header(
        "Profiling",
        "Inspect dataset shape, quality, statistics, and frequencies before downstream processing.",
        icon=":material/biotech:",
    )

    render_dataset_selection(data_manager)
    st.divider()
    render_profiling_controls(data_manager)
    st.divider()
    render_profiling_results()


def render_dataset_selection(data_manager: DataManager) -> None:
    """Render the saved-dataset picker and preview."""
    section_title(
        "Available Datasets",
        "Choose a dataset that was saved from the upload workflow.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        st.info("No saved datasets are available yet. Upload datasets on the Data Upload page first.")
        return

    selected_dataset = st.selectbox(
        "Select a dataset",
        options=[None, *datasets],
        format_func=lambda dataset: "Select a dataset" if dataset is None else dataset.filename,
        key="profiling_selected_dataset",
    )

    if selected_dataset is None:
        st.info("Select a dataset to inspect and profile.")
        return

    render_dataset_inspector(data_manager, selected_dataset)


def render_dataset_inspector(data_manager: DataManager, dataset: DatasetRecord) -> None:
    """Show dataset metadata and a preview before profiling."""
    section_title("Dataset Inspector")
    display_result_table(asdict(dataset))

    dataframe, error = load_dataset_safely(data_manager, dataset)
    if error:
        st.warning(error)
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


def render_profiling_controls(data_manager: DataManager) -> None:
    """Render profiling options and execute the profiler."""
    section_title(
        "Profiling Controls",
        "Configure the profiling run and inspect the generated results.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        return

    selected_dataset = st.session_state.get("profiling_selected_dataset")
    if selected_dataset is None:
        st.info("Choose a dataset before running profiling.")
        return

    primary_key = st.text_input("Primary key (optional)", key="profiling_primary_key")
    date_columns_input = st.text_input(
        "Date columns (optional, comma-separated)",
        key="profiling_date_columns",
    )
    date_columns = [column.strip() for column in date_columns_input.split(",") if column.strip()]

    if st.button("Run profiling", type="primary", use_container_width=True):
        dataframe, error = load_dataset_safely(data_manager, selected_dataset)
        if error:
            st.error(error)
            return

        with st.spinner(f"Profiling {selected_dataset.filename}..."):
            profiler = DataProfiler(
                dataframe=dataframe,
                primary_key=primary_key or None,
                table_name=selected_dataset.filename,
                date_columns=date_columns,
                export=False,
            )
            results = profiler.run()

        st.session_state.profiling_results = {
            "dataset": asdict(selected_dataset),
            "results": results,
        }
        st.success("Profiling completed successfully.")


def render_profiling_results() -> None:
    """Render the latest profiling results in an interactive layout."""
    section_title("Profiling Results")

    results_payload = st.session_state.get("profiling_results")
    if not results_payload:
        st.info("Run profiling to view dataset quality and statistical insights.")
        return

    results = results_payload.get("results")
    if not isinstance(results, Mapping):
        st.warning("The profiling engine returned an unexpected payload.")
        return

    metadata = results.get("metadata", {})
    statistics = results.get("statistics", {})
    quality = results.get("quality", {})
    frequency = results.get("frequency", {})
    outliers = results.get("outliers", {})

    overview_tab, statistics_tab, quality_tab, frequency_tab, outliers_tab = st.tabs(
        ["Overview", "Statistics", "Quality", "Frequency", "Outliers"]
    )

    with overview_tab:
        if metadata:
            st.subheader("Dataset Overview")
            display_profile_value(metadata.get("dimensions"), "Dimensions")
            display_profile_value(metadata.get("schema"), "Schema")
            display_profile_value(metadata.get("memory_usage"), "Memory Usage")
            display_profile_value(metadata.get("unique_values"), "Unique Values")
            display_profile_value(metadata.get("cardinality"), "Cardinality")
        else:
            st.info("No metadata was generated.")

    with statistics_tab:
        if statistics:
            display_profile_value(statistics.get("descriptive_statistics"), "Descriptive Statistics")
            display_profile_value(statistics.get("variance"), "Variance")
            display_profile_value(statistics.get("standard_deviation"), "Standard Deviation")
            display_profile_value(statistics.get("median"), "Median")
            display_profile_value(statistics.get("mode"), "Mode")
            display_profile_value(statistics.get("skewness"), "Skewness")
            display_profile_value(statistics.get("kurtosis"), "Kurtosis")
            display_profile_value(statistics.get("categorical_summary"), "Categorical Summary")
        else:
            st.info("No statistical summaries were generated.")

    with quality_tab:
        if quality:
            display_profile_value(quality.get("missing_values"), "Missing Values")
            display_profile_value(quality.get("missing_percentage"), "Missing Percentage")
            display_profile_value(quality.get("empty_strings"), "Empty Strings")
            display_profile_value(quality.get("quality_summary"), "Quality Summary")
            if quality.get("duplicate_rows") is not None:
                st.metric("Duplicate Rows", int(quality.get("duplicate_rows")))
            if quality.get("duplicate_primary_keys") is not None:
                st.metric("Duplicate Primary Keys", int(quality.get("duplicate_primary_keys")))
        else:
            st.info("No data quality results were generated.")

    with frequency_tab:
        if frequency:
            display_profile_value(frequency.get("summary"), "Frequency Summary")
            display_profile_value(frequency.get("cardinality"), "Frequency Cardinality")
            frequency_tables = frequency.get("frequency_tables", {})
            if isinstance(frequency_tables, Mapping) and frequency_tables:
                for column_name, table in frequency_tables.items():
                    with st.expander(f"{column_name} frequency table"):
                        display_profile_value(table, None)
        else:
            st.info("No frequency reports were generated.")

    with outliers_tab:
        if outliers:
            display_profile_value(outliers.get("summary"), "Outlier Summary")
            details = outliers.get("details", {})
            if isinstance(details, Mapping) and details:
                for column_name, detail in details.items():
                    with st.expander(f"{column_name} outlier details"):
                        display_profile_value(detail.get("IQR"), "IQR")
                        display_profile_value(detail.get("Z-Score"), "Z-Score")
        else:
            st.info("No outlier results were generated.")


def load_dataset_safely(
    data_manager: DataManager,
    dataset: DatasetRecord,
) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a saved dataset and return ``(dataframe, error_message)``."""
    try:
        return data_manager.load_dataset(dataset.dataset_id), None
    except Exception as exc:
        return None, f"Could not load the selected dataset: {exc}"


def display_profile_value(value: Any, heading: Optional[str]) -> None:
    """Render a profiling artifact using Streamlit dataframes when possible."""
    if heading:
        st.subheader(heading)

    if value is None:
        st.info("No values are available for this section.")
        return

    if isinstance(value, pd.DataFrame):
        st.dataframe(value, use_container_width=True, hide_index=True)
        return

    if isinstance(value, pd.Series):
        frame = value.to_frame(name="Value").reset_index()
        frame = frame.rename(columns={frame.columns[0]: "Metric"})
        st.dataframe(frame, use_container_width=True, hide_index=True)
        return

    if isinstance(value, Mapping):
        display_result_table(value)
        return

    display_result_table({"value": value})


if __name__ == "__main__":
    main()

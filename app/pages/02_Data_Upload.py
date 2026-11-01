"""Generic data-upload page for the Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, List, Optional

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
    display_file_list,
    display_result_table,
    display_schema,
    initialize_session_state,
    page_header,
    preview_dataset,
    safe_read_csv,
    section_title,
)


def main() -> None:
    """Render the data upload and dataset inspection page."""
    st.set_page_config(
        page_title="Data Upload | Modern Data Engineering Platform",
        page_icon=":inbox_tray:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"saved_datasets": []})
    data_manager = DataManager(config.uploads_directory)

    page_header(
        "Data Upload",
        "Upload, validate, save, and inspect generic datasets before pipeline execution.",
    )

    render_upload_section(data_manager)
    st.divider()

    render_saved_dataset_section(data_manager)


def render_upload_section(data_manager: DataManager) -> None:
    """Render upload controls and previews for newly selected files."""
    section_title(
        "Upload Datasets",
        "Supported formats are CSV, JSON, Parquet, XLSX, and XLS. CSV files can be previewed before saving.",
    )

    uploaded_files = st.file_uploader(
        "Choose dataset files",
        type=["csv", "json", "parquet", "xlsx", "xls"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Choose one or more datasets to begin.")
        return

    display_file_list(uploaded_files)
    st.divider()

    preview_new_uploads(uploaded_files)

    if st.button("Save uploaded datasets", type="primary", use_container_width=True):
        records = save_uploads(data_manager, uploaded_files)
        if records:
            st.session_state.uploaded_files = [record.path for record in records]
            st.session_state.saved_datasets = [asdict(record) for record in records]
            st.toast(f"✅ {len(records)} dataset(s) saved successfully.")


def preview_new_uploads(uploaded_files: List[Any]) -> None:
    """Preview selected upload files where a safe inline preview is available."""
    section_title("Selected File Preview")

    for uploaded_file in uploaded_files:
        with st.expander(uploaded_file.name, expanded=len(uploaded_files) == 1):
            extension = Path(uploaded_file.name).suffix.lower()
            if extension != ".csv":
                st.info("Preview is available after saving for this file type.")
                continue

            dataframe, error = safe_read_csv(uploaded_file)
            if error:
                st.warning(error)
                continue

            display_dataset_summary(dataframe)
            preview_dataset(dataframe, rows=config.preview_row_limit)
            display_schema(dataframe)


def save_uploads(data_manager: DataManager, uploaded_files: List[Any]) -> List[DatasetRecord]:
    """Validate and save uploaded files with user-facing feedback."""
    records: List[DatasetRecord] = []
    for uploaded_file in uploaded_files:
        try:
            record = data_manager.save_uploaded_file(
                uploaded_file,
                max_size_bytes=config.max_upload_size_bytes,
            )
        except Exception as exc:
            st.error(f"Could not save {uploaded_file.name}: {exc}")
            continue

        records.append(record)
    return records


def render_saved_dataset_section(data_manager: DataManager) -> None:
    """Render previously saved datasets and a selected-dataset inspector."""
    section_title("Saved Datasets")

    datasets = data_manager.list_datasets()
    if not datasets:
        st.info("No saved datasets are available yet.")
        return

    display_result_table([asdict(dataset) for dataset in datasets])

    selected = st.selectbox(
        "Inspect saved dataset",
        options=[None, *datasets],
        format_func=lambda dataset: "Select a dataset" if dataset is None else dataset.filename,
        key="data_upload_selected_dataset",
    )

    if selected is None:
        return

    render_dataset_inspector(data_manager, selected)


def render_dataset_inspector(data_manager: DataManager, dataset: DatasetRecord) -> None:
    """Load and inspect one saved dataset defensively."""
    section_title("Dataset Inspector")
    display_result_table(asdict(dataset))

    dataframe, error = load_dataset_safely(data_manager, dataset)
    if error:
        st.warning(error)
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


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


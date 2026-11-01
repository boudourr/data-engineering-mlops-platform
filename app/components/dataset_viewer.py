"""Reusable Streamlit component for browsing generic datasets.

This module keeps dataset display independent of any business domain.  It can
show an in-memory DataFrame, load a selected dataset through ``DataManager``, or
display metadata for uploaded files.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pandas as pd
import streamlit as st

from app.core.ui_helpers import (
    display_dataset_summary,
    display_file_list,
    display_schema,
    preview_dataset,
)


def render_dataset_viewer(
    dataframe: Optional[pd.DataFrame] = None,
    *,
    title: str = "Dataset viewer",
    preview_rows: int = 10,
    show_summary: bool = True,
    show_schema: bool = True,
    show_preview: bool = True,
    key_prefix: str = "dataset_viewer",
) -> None:
    """Render summary, preview, and schema tabs for a generic DataFrame."""
    st.markdown(f"### {title}")

    if dataframe is None:
        st.info("No dataset is selected.")
        return
    if not isinstance(dataframe, pd.DataFrame):
        st.warning("The selected object is not a pandas DataFrame.")
        return

    tabs: List[Tuple[str, Any]] = []
    if show_summary:
        tabs.append(("Summary", lambda: display_dataset_summary(dataframe)))
    if show_preview:
        tabs.append(("Preview", lambda: _render_preview_tab(dataframe, preview_rows, key_prefix)))
    if show_schema:
        tabs.append(("Schema", lambda: display_schema(dataframe)))

    if not tabs:
        st.info("No dataset views are enabled.")
        return

    rendered_tabs = st.tabs([name for name, _ in tabs])
    for tab, (_, renderer) in zip(rendered_tabs, tabs):
        with tab:
            renderer()


def render_dataset_selector(
    datasets: Sequence[Any],
    *,
    label: str = "Dataset",
    key: str = "selected_dataset",
    include_empty: bool = True,
) -> Optional[Any]:
    """Render a generic dataset selector and return the selected dataset object."""
    choices = list(datasets or [])
    if not choices:
        st.info("No datasets are available.")
        return None

    options: List[Optional[Any]] = [None, *choices] if include_empty else choices
    selected = st.selectbox(
        label,
        options=options,
        format_func=lambda item: "Select a dataset" if item is None else _dataset_label(item),
        key=key,
    )
    return selected


def render_managed_dataset_viewer(
    data_manager: Any,
    *,
    title: str = "Available datasets",
    preview_rows: int = 10,
    key_prefix: str = "managed_dataset_viewer",
    read_options: Optional[Mapping[str, Any]] = None,
) -> Optional[pd.DataFrame]:
    """Render dataset selection, metadata, and preview using a manager object.

    The manager is expected to expose ``list_datasets`` and ``load_dataset``.
    This matches ``app.core.data_manager.DataManager`` while keeping the
    component easy to test with lightweight stand-ins.
    """
    st.markdown(f"### {title}")

    datasets = _safe_list_datasets(data_manager)
    selected = render_dataset_selector(
        datasets,
        key=f"{key_prefix}_selected_dataset",
    )
    if selected is None:
        return None

    metadata = dataset_to_record(selected)
    if metadata:
        display_dataset_records([metadata], title="Selected dataset")

    dataset_ref = (metadata.get("dataset_id") or metadata.get("path")) if metadata else selected
    dataframe, error = _safe_load_dataset(data_manager, dataset_ref, dict(read_options or {}))
    if error:
        st.error(error)
        return None

    render_dataset_viewer(
        dataframe,
        title="Dataset details",
        preview_rows=preview_rows,
        key_prefix=f"{key_prefix}_details",
    )
    return dataframe


def display_dataset_records(
    datasets: Sequence[Any],
    *,
    title: str = "Datasets",
) -> None:
    """Display dataset metadata as a compact table."""
    records = [dataset_to_record(item) for item in datasets or []]
    records = [record for record in records if record]
    if not records:
        st.info("No dataset metadata is available.")
        return

    st.markdown(f"#### {title}")
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)


def display_uploaded_files(
    files: Optional[Sequence[Any]],
    *,
    title: str = "Uploaded files",
) -> None:
    """Render uploaded file metadata using the shared file-list helper."""
    st.markdown(f"### {title}")
    display_file_list(files)


def dataset_to_record(dataset: Any) -> Dict[str, Any]:
    """Convert a dataset-like object into table-friendly metadata."""
    if dataset is None:
        return {}
    if is_dataclass(dataset):
        return {str(key): value for key, value in asdict(dataset).items()}
    if isinstance(dataset, Mapping):
        return {str(key): value for key, value in dataset.items()}
    if isinstance(dataset, (str, Path)):
        path = Path(dataset)
        return {
            "filename": path.name,
            "path": str(path),
            "extension": path.suffix.lower(),
        }

    record: Dict[str, Any] = {}
    for attribute in ("dataset_id", "filename", "name", "path", "extension", "size_bytes", "uploaded_at"):
        if hasattr(dataset, attribute):
            record[attribute] = getattr(dataset, attribute)
    return record


def _render_preview_tab(dataframe: pd.DataFrame, preview_rows: int, key_prefix: str) -> None:
    """Render preview controls and data for one DataFrame."""
    max_rows = max(1, int(preview_rows))
    row_count = st.number_input(
        "Rows to preview",
        min_value=1,
        max_value=max(1, min(len(dataframe), 1000)),
        value=min(max_rows, max(1, len(dataframe))) if len(dataframe) else 1,
        key=f"{key_prefix}_preview_rows",
    )
    preview_dataset(dataframe, rows=int(row_count))


def _safe_list_datasets(data_manager: Any) -> Sequence[Any]:
    """Return datasets from a manager without leaking exceptions to the page."""
    if data_manager is None or not hasattr(data_manager, "list_datasets"):
        st.warning("A dataset manager with list_datasets is required.")
        return []
    try:
        return list(data_manager.list_datasets())
    except Exception as exc:
        st.error(f"Could not list datasets: {exc}")
        return []


def _safe_load_dataset(
    data_manager: Any,
    dataset_ref: Any,
    read_options: Mapping[str, Any],
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a dataset through a manager and return ``(dataframe, error)``."""
    if data_manager is None or not hasattr(data_manager, "load_dataset"):
        return None, "A dataset manager with load_dataset is required."
    try:
        dataframe = data_manager.load_dataset(dataset_ref, **read_options)
    except Exception as exc:
        return None, f"Could not load the selected dataset: {exc}"
    if not isinstance(dataframe, pd.DataFrame):
        return None, "The selected dataset did not load as a pandas DataFrame."
    return dataframe, None


def _dataset_label(dataset: Any) -> str:
    """Return a readable label for a dataset selector."""
    record = dataset_to_record(dataset)
    for key in ("filename", "name", "dataset_id", "path"):
        value = record.get(key)
        if value:
            return str(value)
    return str(dataset)


def dataset_viewer(**kwargs: Any) -> None:
    """Alias for :func:`render_dataset_viewer`."""
    render_dataset_viewer(**kwargs)

"""Reusable Streamlit component for browsing generated reports.

The helpers in this module are intentionally report-domain agnostic.  They can
display filesystem reports, mapping/dataclass metadata, and common text-based
report formats without assuming fixed names, folders, tables, or columns.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pandas as pd
import streamlit as st

from app.core.ui_helpers import display_result_table


PREVIEWABLE_EXTENSIONS = {".csv", ".json", ".md", ".markdown", ".txt", ".log"}


def render_report_viewer(
    reports: Optional[Sequence[Any]] = None,
    *,
    title: str = "Report viewer",
    key_prefix: str = "report_viewer",
    preview_rows: int = 25,
) -> Optional[Any]:
    """Render report selection, metadata, preview, and download controls."""
    st.markdown(f"### {title}")

    available_reports = list(reports or [])
    if not available_reports:
        st.info("No reports are available yet.")
        return None

    selected = render_report_selector(
        available_reports,
        key=f"{key_prefix}_selected_report",
    )
    if selected is None:
        return None

    metadata = report_to_record(selected)
    if metadata:
        display_report_records([metadata], title="Selected report")

    path = _record_path(metadata)
    if path is None:
        _render_non_file_report(selected)
        return selected

    preview_report(path, preview_rows=preview_rows)
    render_report_download(path, key=f"{key_prefix}_download")
    return selected


def render_report_selector(
    reports: Sequence[Any],
    *,
    label: str = "Report",
    key: str = "selected_report",
    include_empty: bool = True,
) -> Optional[Any]:
    """Render a generic report selector and return the selected report object."""
    choices = list(reports or [])
    if not choices:
        st.info("No reports are available.")
        return None

    options: List[Optional[Any]] = [None, *choices] if include_empty else choices
    return st.selectbox(
        label,
        options=options,
        format_func=lambda item: "Select a report" if item is None else _report_label(item),
        key=key,
    )


def display_report_records(
    reports: Sequence[Any],
    *,
    title: str = "Reports",
) -> None:
    """Display report metadata as a compact table."""
    records = [report_to_record(report) for report in reports or []]
    records = [record for record in records if record]
    if not records:
        st.info("No report metadata is available.")
        return

    st.markdown(f"#### {title}")
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)


def preview_report(path: Any, *, preview_rows: int = 25) -> None:
    """Preview a supported report file, falling back to download guidance."""
    report_path = Path(path).expanduser()
    if not report_path.is_file():
        st.warning("The selected report file is not available.")
        return

    extension = report_path.suffix.lower()
    st.markdown("#### Preview")
    if extension not in PREVIEWABLE_EXTENSIONS:
        st.info("This report type is available for download but cannot be previewed here.")
        return

    content, error = _safe_read_text(report_path)
    if error:
        st.warning(error)
        return

    if extension == ".csv":
        _preview_csv(report_path, preview_rows)
    elif extension == ".json":
        _preview_json(content)
    elif extension in {".md", ".markdown"}:
        st.markdown(content)
    else:
        st.text_area("Content", value=content, height=320, disabled=True)


def render_report_download(path: Any, *, label: str = "Download report", key: str = "download_report") -> None:
    """Render a download button for a local report file."""
    report_path = Path(path).expanduser()
    if not report_path.is_file():
        return

    try:
        data = report_path.read_bytes()
    except OSError as exc:
        st.warning(f"Could not prepare the report download: {exc}")
        return

    st.download_button(
        label,
        data=data,
        file_name=report_path.name,
        mime=_guess_mime_type(report_path),
        key=key,
    )


def report_to_record(report: Any) -> Dict[str, Any]:
    """Convert a report-like object into table-friendly metadata."""
    if report is None:
        return {}
    if is_dataclass(report):
        return {str(key): value for key, value in asdict(report).items()}
    if isinstance(report, Mapping):
        return {str(key): value for key, value in report.items()}
    if isinstance(report, (str, Path)):
        path = Path(report)
        record: Dict[str, Any] = {
            "name": path.name,
            "path": str(path),
            "extension": path.suffix.lower(),
        }
        if path.is_file():
            record["size_bytes"] = path.stat().st_size
            record["modified_at"] = pd.Timestamp(path.stat().st_mtime, unit="s").isoformat()
        return record

    record: Dict[str, Any] = {}
    for attribute in ("report_id", "name", "title", "path", "extension", "size_bytes", "created_at", "updated_at"):
        if hasattr(report, attribute):
            record[attribute] = getattr(report, attribute)
    return record


def _render_non_file_report(report: Any) -> None:
    """Display a report object that is metadata or structured content only."""
    if isinstance(report, pd.DataFrame):
        display_result_table(report)
    elif isinstance(report, Mapping):
        display_result_table(report)
    else:
        st.write(report)


def _preview_csv(path: Path, preview_rows: int) -> None:
    """Preview the first rows of a CSV report."""
    try:
        dataframe = pd.read_csv(path, nrows=max(1, int(preview_rows)))
    except Exception as exc:
        st.warning(f"Could not preview the CSV report: {exc}")
        return
    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def _preview_json(content: str) -> None:
    """Preview JSON content using Streamlit's structured renderer."""
    try:
        st.json(json.loads(content))
    except json.JSONDecodeError:
        st.text_area("Content", value=content, height=320, disabled=True)


def _safe_read_text(path: Path) -> Tuple[str, Optional[str]]:
    """Read text content from a report and return ``(content, error)``."""
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1"), None
        except OSError as exc:
            return "", f"Could not read the report: {exc}"
    except OSError as exc:
        return "", f"Could not read the report: {exc}"


def _record_path(record: Mapping[str, Any]) -> Optional[Path]:
    """Extract a usable path from a report metadata record."""
    value = record.get("path") or record.get("file_path") or record.get("location")
    if not value:
        return None
    return Path(str(value))


def _report_label(report: Any) -> str:
    """Return a readable label for a report selector."""
    record = report_to_record(report)
    for key in ("title", "name", "filename", "report_id", "path"):
        value = record.get(key)
        if value:
            return str(value)
    return str(report)


def _guess_mime_type(path: Path) -> str:
    """Return a reasonable MIME type for common report formats."""
    extension = path.suffix.lower()
    return {
        ".csv": "text/csv",
        ".json": "application/json",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".html": "text/html",
        ".htm": "text/html",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".log": "text/plain",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
    }.get(extension, "application/octet-stream")


def report_viewer(**kwargs: Any) -> Optional[Any]:
    """Alias for :func:`render_report_viewer`."""
    return render_report_viewer(**kwargs)


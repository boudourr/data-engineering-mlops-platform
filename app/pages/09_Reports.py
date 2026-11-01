"""Reports page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, List

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.ui_helpers import initialize_session_state, page_header, section_title


def main() -> None:
    """Render the reports dashboard."""
    st.set_page_config(
        page_title="Reports | Modern Data Engineering Platform",
        page_icon=":page_facing_up:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"selected_report_path": None})

    page_header(
        "Reports",
        "Inspect generated platform reports and exported monitoring artifacts.",
        icon=":material/description:",
    )

    render_report_browser()


def render_report_browser() -> None:
    """Discover and display report files from the platform's report locations."""
    section_title(
        "Available Reports",
        "Browse JSON, CSV, and other generated artifacts from the platform workflows.",
    )

    report_paths = discover_report_files()
    if not report_paths:
        st.info("No reports have been generated yet. Run the monitoring sweep or other pipeline steps to create artifacts.")
        return

    sorted_paths = sorted(report_paths, key=lambda path: path.stat().st_mtime, reverse=True)
    selected_path = st.selectbox(
        "Select a report",
        options=sorted_paths,
        format_func=lambda path: path.name,
        key="selected_report_path",
    )

    if selected_path is None:
        return

    render_report_details(selected_path)


def discover_report_files() -> List[Path]:
    """Collect report files from the configured report directories and known monitoring output locations."""
    from core.run_context import get_current_run
    run_context = get_current_run()
    
    if run_context:
        directories = [Path(run_context.reports_dir)]
    else:
        directories = [config.reports_directory, PROJECT_ROOT / "monitoring" / "reports"]
        
    discovered: List[Path] = []
    seen: set[Path] = set()
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in {".json", ".csv", ".parquet", ".txt", ".html"}:
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    discovered.append(resolved)
    return discovered


def render_report_details(report_path: Path) -> None:
    """Render the selected report file with a size summary and content preview."""
    st.subheader(report_path.name)
    try:
        size_kb = report_path.stat().st_size / 1024
    except OSError:
        size_kb = None

    metadata_columns = st.columns(3)
    metadata_columns[0].metric("Location", report_path.parent.name)
    metadata_columns[1].metric("Type", report_path.suffix.lower() or "file")
    metadata_columns[2].metric("Size", f"{size_kb:.1f} KB" if size_kb is not None else "Unknown")

    st.caption(str(report_path))

    suffix = report_path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            st.json(payload)
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Could not preview the JSON report: {exc}")
    elif suffix == ".csv":
        try:
            dataframe = pd.read_csv(report_path)
            st.dataframe(dataframe, use_container_width=True, hide_index=True)
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Could not preview the CSV report: {exc}")
    elif suffix == ".parquet":
        try:
            dataframe = pd.read_parquet(report_path)
            st.dataframe(dataframe, use_container_width=True, hide_index=True)
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Could not preview the Parquet report: {exc}")
    else:
        try:
            st.code(report_path.read_text(encoding="utf-8"), language="text")
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Could not preview the report: {exc}")


if __name__ == "__main__":
    main()

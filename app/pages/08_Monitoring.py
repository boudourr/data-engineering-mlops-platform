"""Monitoring page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

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
    display_result_table,
    initialize_session_state,
    page_header,
    section_title,
    status_badge,
)
from monitoring.monitor import PlatformMonitor, GenericPlatformMonitor


def main() -> None:
    """Render the monitoring dashboard."""
    st.set_page_config(
        page_title="Monitoring | Modern Data Engineering Platform",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"monitoring_results": None})

    page_header(
        "Monitoring",
        "Run the existing platform monitoring sweep to review ETL, warehouse, and MLOps health.",
        icon=":material/monitoring:",
    )
    
    run_context = get_current_run()
    
    if not run_context:
        st.warning("No active run context found. Falling back to default Olist execution. Please upload a dataset in Data Upload.")

    render_monitoring_controls(run_context)
    st.divider()
    render_monitoring_results(run_context)


def render_monitoring_controls(run_context) -> None:
    """Render the controls for launching a monitoring run."""
    section_title(
        "Run Monitoring",
        "Execute the built-in monitoring suite and capture the latest platform health snapshot.",
    )

    if st.button("Run monitoring sweep", type="primary", use_container_width=True):
        run_monitoring(run_context)


def run_monitoring(run_context) -> None:
    """Execute the monitoring module and store its report in session state."""
    with st.spinner("Running monitoring sweep..."):
        try:
            original_cwd = Path.cwd()
            os.chdir(PROJECT_ROOT)
            try:
                if run_context:
                    monitor = GenericPlatformMonitor(run_context)
                else:
                    monitor = PlatformMonitor()
                results = monitor.run()
            finally:
                os.chdir(original_cwd)
        except Exception as exc:  # pragma: no cover - UI fallback
            st.session_state.monitoring_results = {
                "status": "FAILED",
                "message": f"Monitoring failed: {exc}",
            }
            st.error(f"Monitoring failed: {exc}")
            return

    st.session_state.monitoring_results = results
    st.success("Monitoring completed successfully.")


def render_monitoring_results(run_context) -> None:
    """Render the latest monitoring outcome and generated reports."""
    section_title("Latest Monitoring Results")

    results = st.session_state.get("monitoring_results")
    if not results:
        st.info("Run the monitoring sweep to inspect platform health and generated reports.")
        return

    if isinstance(results, Mapping):
        overall_status = str(results.get("overall_status") or results.get("status") or "unknown")
        status_badge(overall_status, label=f"Overall platform status: {overall_status}")

        metrics_columns = st.columns(4)
        metrics_columns[0].metric("Overall", overall_status)
        metrics_columns[1].metric("ETL", str((results.get("etl") or {}).get("status") or "unknown"))
        metrics_columns[2].metric("Warehouse", str((results.get("warehouse") or {}).get("status") or "unknown"))
        metrics_columns[3].metric("MLOps", str((results.get("mlops") or {}).get("status") or "unknown"))

        tabs = st.tabs(["Summary", "ETL", "Warehouse", "MLOps", "Reports"])

        with tabs[0]:
            display_result_table(results)

        with tabs[1]:
            display_result_table(results.get("etl") or {})

        with tabs[2]:
            display_result_table(results.get("warehouse") or {})

        with tabs[3]:
            display_result_table(results.get("mlops") or {})

        with tabs[4]:
            render_report_artifacts(run_context)
    else:
        st.warning("The latest monitoring result could not be displayed.")


def render_report_artifacts(run_context) -> None:
    """Render the latest JSON/CSV monitoring reports if they exist."""
    if run_context:
        reports_dir = Path(run_context.reports_dir)
    else:
        reports_dir = PROJECT_ROOT / "monitoring" / "reports"
        
    json_path = reports_dir / "monitoring_report.json"
    csv_path = reports_dir / "monitoring_report.csv"

    if not json_path.exists() and not csv_path.exists():
        st.info("No monitoring reports have been generated yet.")
        return

    report_files = []
    if json_path.exists():
        report_files.append(json_path)
    if csv_path.exists():
        report_files.append(csv_path)

    for artifact_path in report_files:
        if artifact_path.suffix.lower() == ".json":
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                st.subheader(artifact_path.name)
                st.json(payload)
            except Exception as exc:  # pragma: no cover - UI fallback
                st.warning(f"Could not preview {artifact_path.name}: {exc}")
        elif artifact_path.suffix.lower() == ".csv":
            try:
                dataframe = pd.read_csv(artifact_path)
                st.subheader(artifact_path.name)
                st.dataframe(dataframe, use_container_width=True, hide_index=True)
            except Exception as exc:  # pragma: no cover - UI fallback
                st.warning(f"Could not preview {artifact_path.name}: {exc}")


if __name__ == "__main__":
    main()

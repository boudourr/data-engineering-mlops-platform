"""Overview page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.pipeline_controls import render_pipeline_controls
from core.config import config
from core.pipeline_manager import PipelineManager
from core.ui_helpers import (
    display_file_list,
    display_result_table,
    health_message,
    initialize_session_state,
    page_header,
    pipeline_status_grid,
    section_title,
    show_execution_result,
)


WORKFLOW_STAGES = (
    ("Upload", "Datasets are collected and stored generically."),
    ("Profiling", "Data structure and quality are inspected."),
    ("ETL", "Raw data is transformed into an analytics-ready layer."),
    ("Warehouse", "Curated outputs are prepared for BI and downstream use."),
    ("MLOps", "Model lifecycle tasks can be triggered when available."),
    ("Monitoring", "Platform health and pipeline behavior are checked."),
    ("Reports", "Generated outputs are surfaced for review."),
)


def main() -> None:
    """Render the overview dashboard page."""
    st.set_page_config(
        page_title="Overview | Modern Data Engineering Platform",
        page_icon=":bar_chart:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"reports": []})
    manager = PipelineManager(project_root=PROJECT_ROOT)

    page_header(
        "Overview",
        "Monitor the generic data platform from one dashboard.",
    )

    render_health_section(manager)
    st.divider()

    render_status_section(manager)
    st.divider()

    render_workflow_section()
    st.divider()

    render_quick_actions(manager)
    st.divider()

    render_workspace_summary()


def render_health_section(manager: PipelineManager) -> None:
    """Render the platform health summary."""
    section_title("Platform Health")
    health_message(manager.overall_status())


def render_status_section(manager: PipelineManager) -> None:
    """Render current pipeline stage statuses."""
    section_title("Pipeline Status")
    statuses = manager.get_status()
    if statuses:
        pipeline_status_grid(statuses, columns=4)
    else:
        st.info("No pipeline status is available yet.")


def render_workflow_section() -> None:
    """Render the generic lifecycle workflow."""
    section_title("Platform Workflow")
    columns = st.columns(len(WORKFLOW_STAGES))
    for column, (label, description) in zip(columns, WORKFLOW_STAGES):
        with column:
            st.markdown(
                f"""
                <div style="
                    border:1px solid #333842;
                    border-radius:8px;
                    padding:14px;
                    min-height:120px;
                    text-align:center;
                ">
                    <div style="font-weight:700; margin-bottom:8px;">{label}</div>
                    <div style="font-size:12px; color:#8f98a8;">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_quick_actions(manager: PipelineManager) -> None:
    """Render quick pipeline controls and execute selected actions."""
    action_payload = render_pipeline_controls(
        stages=(
            "Full pipeline",
            "Profiling",
            "ETL",
            "Warehouse",
            "MLOps",
            "Monitoring",
            "Reports",
            "Power BI",
        ),
        key_prefix="overview",
        title="Quick Actions",
    )

    action = action_payload.get("action")
    stage = str(action_payload.get("stage", "Full pipeline"))
    if not action:
        return

    if action == "reset":
        st.session_state.last_overview_action = {
            "status": "success",
            "message": "Overview action state was reset.",
        }
        show_execution_result(st.session_state.last_overview_action)
        return

    if action == "stop":
        st.session_state.last_overview_action = {
            "status": "warning",
            "message": "Stop was requested. Connect this action to a running backend service when available.",
            "stage": stage,
        }
        show_execution_result(st.session_state.last_overview_action)
        return

    result = run_selected_stage(manager, stage)
    st.session_state.last_overview_action = result
    show_execution_result(result)


def render_workspace_summary() -> None:
    """Render uploaded-file, report, and path summaries."""
    left_column, middle_column, right_column = st.columns(3)

    with left_column:
        section_title("Uploaded Files")
        display_file_list(st.session_state.get("uploaded_files", []))

    with middle_column:
        section_title("Recent Result")
        result = st.session_state.get("last_overview_action")
        if result:
            display_result_table(result)
        else:
            st.info("No recent action has been recorded.")

    with right_column:
        section_title("Runtime Paths")
        display_result_table(
            {
                "uploads": str(config.uploads_directory),
                "warehouse": str(config.warehouse_directory),
                "reports": str(config.reports_directory),
            }
        )


def run_selected_stage(manager: PipelineManager, stage: str) -> Dict[str, Any]:
    """Run the manager method that matches a selected overview stage."""
    method = stage_method(manager, stage)
    if method is None:
        return {
            "status": "warning",
            "message": f"No quick action is available for {stage}.",
            "stage": stage,
        }

    with st.spinner(f"Running {stage}..."):
        try:
            result = method()
        except Exception as exc:
            return {
                "status": "failed",
                "message": f"{stage} failed.",
                "error": str(exc),
            }

    if isinstance(result, Mapping):
        return dict(result)
    return {
        "status": "success",
        "message": f"{stage} completed successfully.",
        "result": result,
    }


def stage_method(manager: PipelineManager, stage: str) -> Optional[Callable[[], Any]]:
    """Return the manager method for a selected stage name."""
    methods = {
        "Full pipeline": manager.run_all,
        "Profiling": manager.run_profiling,
        "ETL": manager.run_etl,
        "Warehouse": manager.run_warehouse,
        "MLOps": manager.run_mlops,
        "Monitoring": manager.run_monitoring,
        "Reports": manager.generate_reports,
        "Power BI": manager.prepare_powerbi,
    }
    return methods.get(stage)


if __name__ == "__main__":
    main()


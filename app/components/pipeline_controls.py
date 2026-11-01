"""Reusable controls for starting and managing generic pipeline runs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Dict, Optional

import streamlit as st


DEFAULT_STAGES = (
    "Full pipeline",
    "Profiling",
    "ETL",
    "Warehouse",
    "MLOps",
    "Monitoring",
    "Reports",
)


def render_pipeline_controls(
    stages: Optional[Sequence[str]] = None,
    *,
    disabled: bool = False,
    key_prefix: str = "pipeline",
    title: str = "Pipeline controls",
) -> Dict[str, Any]:
    """Render pipeline actions and return the selected action payload.

    The returned dictionary contains ``action`` (``run``, ``rerun``, ``stop``,
    ``reset``, or ``None``) and the selected ``stage``.  This keeps UI concerns
    separate from execution logic handled by a pipeline manager.
    """
    available_stages = tuple(stages or DEFAULT_STAGES)
    if not available_stages:
        raise ValueError("At least one pipeline stage is required.")

    st.markdown(f"### {title}")
    stage = st.selectbox(
        "Stage",
        options=available_stages,
        key=f"{key_prefix}_stage",
        disabled=disabled,
    )
    run_column, rerun_column, stop_column, reset_column = st.columns(4)
    with run_column:
        run_clicked = st.button("Run", key=f"{key_prefix}_run", disabled=disabled, type="primary")
    with rerun_column:
        rerun_clicked = st.button("Rerun", key=f"{key_prefix}_rerun", disabled=disabled)
    with stop_column:
        stop_clicked = st.button("Stop", key=f"{key_prefix}_stop", disabled=disabled)
    with reset_column:
        reset_clicked = st.button("Reset", key=f"{key_prefix}_reset", disabled=disabled)

    action: Optional[str] = None
    for name, clicked in (
        ("run", run_clicked),
        ("rerun", rerun_clicked),
        ("stop", stop_clicked),
        ("reset", reset_clicked),
    ):
        if clicked:
            action = name
            break
    return {"action": action, "stage": stage}


def pipeline_controls(**kwargs: Any) -> Dict[str, Any]:
    """Alias for :func:`render_pipeline_controls`."""
    return render_pipeline_controls(**kwargs)


"""Navigation and context sidebar for the Streamlit platform interface."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional

import streamlit as st


DEFAULT_NAVIGATION = (
    "Overview",
    "Data Upload",
    "Profiling",
    "ETL",
    "Warehouse",
    "MLOps",
    "Monitoring",
    "Reports",
    "Power BI",
    "System Info",
)


def render_sidebar(
    *,
    title: str = "Modern Data Engineering Platform",
    navigation: Optional[Sequence[str]] = None,
    current_page: Optional[str] = None,
    health: Optional[Any] = None,
    pipeline_status: Optional[Mapping[str, Any]] = None,
) -> str:
    """Render the application sidebar and return the selected navigation item.

    Parameters are optional so the component can be used on the first page load
    before a dataset or pipeline has been initialized. ``current_page`` is used
    as the initial selection when it is present in ``navigation``.
    """
    items = tuple(navigation or DEFAULT_NAVIGATION)
    if not items:
        raise ValueError("Sidebar navigation must contain at least one item.")
    initial_index = items.index(current_page) if current_page in items else 0

    with st.sidebar:
        st.markdown(f"## {title}")
        st.caption("Generic data workflow workspace")
        st.divider()
        selected = st.radio(
            "Navigate",
            options=items,
            index=initial_index,
            key="sidebar_navigation",
            label_visibility="collapsed",
        )

        if health is not None or pipeline_status:
            st.divider()
            st.markdown("### Runtime status")
            if health is not None:
                st.caption(f"Health: {_display_value(health)}")
            if pipeline_status:
                completed = sum(
                    1 for value in pipeline_status.values()
                    if _status_text(value) in {"success", "completed", "complete", "ok"}
                )
                st.caption(f"Pipeline stages: {completed}/{len(pipeline_status)} completed")

        st.divider()
        st.caption("Use the pages to inspect, run, and monitor your data workflows.")
    return selected


def sidebar_navigation(**kwargs: Any) -> str:
    """Backward-compatible alias for :func:`render_sidebar`."""
    return render_sidebar(**kwargs)


def _status_text(value: Any) -> str:
    """Extract a lowercase status string from scalar or mapping input."""
    if isinstance(value, Mapping):
        value = value.get("status", "")
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def _display_value(value: Any) -> str:
    """Create a concise display value without exposing large nested objects."""
    if isinstance(value, Mapping):
        value = value.get("status", value.get("health", "unknown"))
    return str(value or "unknown").replace("_", " ").title()


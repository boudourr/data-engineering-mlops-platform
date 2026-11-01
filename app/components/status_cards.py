"""Reusable premium status-card components for Streamlit pages."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any, Optional

import streamlit as st

from app.core.ui_helpers import normalize_status


_COLORS = {
    "success": ("#059669", "check_circle", "Completed"),
    "running": ("#2563EB", "sync", "Running"),
    "pending": ("#64748B", "schedule", "Pending"),
    "warning": ("#D97706", "warning", "Warning"),
    "failed": ("#DC2626", "error", "Failed"),
    "unknown": ("#64748B", "help", "Unknown"),
}


def status_card(
    title: str,
    status: Any,
    *,
    detail: Optional[str] = None,
    metric: Optional[Any] = None,
) -> None:
    """Render one polished status card with an optional metric and detail."""
    normalized = normalize_status(status)
    color, icon, label = _COLORS[normalized]
    metric_html = (
        f"<div style='font-size:1.5rem; line-height:1.15; font-weight:750; color:#0F172A'>{escape(str(metric))}</div>"
        if metric is not None
        else ""
    )
    detail_html = (
        f"<div style='margin-top:.42rem; color:#64748B; font-size:.8rem; line-height:1.4'>{escape(str(detail))}</div>"
        if detail
        else ""
    )
    st.markdown(
        f"""
<div style='border:1px solid #E2E8F0; border-radius:14px; padding:1rem 1.05rem;
            min-height:118px; margin-bottom:.7rem; background:#FFFFFF;
            box-shadow:0 2px 8px rgba(15,23,42,.045)'>
  <div style='display:flex; align-items:center; justify-content:space-between; gap:.75rem'>
    <div style='font-weight:700; color:#334155; font-size:.88rem'>{escape(str(title))}</div>
    <span class='material-symbols-outlined' style='color:{color}; font-size:1.25rem'>{icon}</span>
  </div>
  <div style='display:inline-flex; align-items:center; gap:.35rem; color:{color}; background:{color}12;
              border-radius:999px; padding:.25rem .55rem; font-size:.73rem; font-weight:700; margin:.7rem 0 .45rem'>
    <span style='width:6px; height:6px; border-radius:50%; background:{color}; display:inline-block'></span>{label}
  </div>
  {metric_html}{detail_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def status_cards_grid(
    statuses: Mapping[str, Any],
    *,
    columns: int = 3,
    details: Optional[Mapping[str, str]] = None,
    metrics: Optional[Mapping[str, Any]] = None,
) -> None:
    """Render named statuses in rows of premium cards."""
    if not statuses:
        st.info("No status information is available.")
        return
    column_count = max(1, int(columns))
    entries = list(statuses.items())
    for start in range(0, len(entries), column_count):
        row = st.columns(column_count)
        for column, (name, value) in zip(row, entries[start : start + column_count]):
            with column:
                status_card(
                    str(name),
                    value,
                    detail=details.get(name) if details else None,
                    metric=metrics.get(name) if metrics else None,
                )


def health_card(health: Any, *, title: str = "Platform health", detail: Optional[str] = None) -> None:
    """Render a single card for an overall health value or health record."""
    if isinstance(health, Mapping):
        detail = detail or health.get("message")
        health = health.get("status", health.get("health", "unknown"))
    status_card(title, health, detail=str(detail) if detail else None)


def pipeline_status_cards(statuses: Mapping[str, Any], *, columns: int = 3) -> None:
    """Convenience wrapper for displaying pipeline stage statuses."""
    status_cards_grid(statuses, columns=columns)

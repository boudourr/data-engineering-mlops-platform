"""
kpi_generator.py
----------------

Reusable Streamlit KPI card components for the BI dashboard.

KPIs are rendered as styled metric cards, grouped into four categories:
    dataset    – rows, columns, quality stats
    numerical  – sums, averages, etc.
    categorical – unique counts, top values
    temporal   – date ranges

No dataset-specific logic is present.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Category metadata
# ─────────────────────────────────────────────────────────────────────────────

_CATEGORY_META: Dict[str, Dict[str, str]] = {
    "dataset": {
        "label": "📋 Dataset Overview",
        "color": "#4f8ef7",
    },
    "numerical": {
        "label": "🔢 Numerical Metrics",
        "color": "#22c55e",
    },
    "categorical": {
        "label": "🏷️ Categorical Metrics",
        "color": "#f59e0b",
    },
    "temporal": {
        "label": "📅 Temporal Metrics",
        "color": "#a78bfa",
    },
}

_CARDS_PER_ROW = 4


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def render_kpis(kpis: List[Dict[str, Any]]) -> None:
    """
    Render all KPI cards grouped by category.

    Parameters
    ----------
    kpis:
        List of KPI dicts as produced by ``BIGenerator.generate_kpis()``.
        Required keys: ``title``, ``value``.
        Optional keys: ``format``, ``category``, ``icon``, ``subtitle``.
    """
    if not kpis:
        st.info("No KPIs could be generated for this dataset.")
        return

    # Group by category
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for kpi in kpis:
        cat = str(kpi.get("category", "dataset"))
        grouped.setdefault(cat, []).append(kpi)

    # Render each category in order
    for cat in ["dataset", "numerical", "categorical", "temporal"]:
        group = grouped.get(cat, [])
        if not group:
            continue

        meta = _CATEGORY_META.get(cat, {"label": cat.title(), "color": "#4F46E5"})
        st.markdown(
            f"""
<div style="
    border-left: 3px solid {meta['color']};
    padding-left: 0.6rem;
    margin: 1.2rem 0 0.5rem 0;
">
    <span style="font-size:0.8rem; font-weight:700; color:{meta['color']}; text-transform:uppercase; letter-spacing:0.06em;">{meta['label']}</span>
</div>""",
            unsafe_allow_html=True,
        )

        _render_kpi_row(group)

    # Render any uncategorised KPIs
    unknown = {k: v for k, v in grouped.items()
               if k not in _CATEGORY_META}
    for cat, group in unknown.items():
        st.markdown(f"**{cat.title()}**")
        _render_kpi_row(group)


def render_kpi_card(kpi: Dict[str, Any]) -> None:
    """Render a single KPI as a Streamlit metric widget."""
    title = str(kpi.get("title", "Metric"))
    value = kpi.get("value", "—")
    icon = str(kpi.get("icon", ""))
    subtitle = kpi.get("subtitle")
    fmt = kpi.get("format", "text")

    display_value = _format_value(value, fmt)

    # Prefix icon in label if present
    label = f"{icon} {title}" if icon else title

    with st.container(border=True):
        st.metric(label=label, value=display_value)
        if subtitle:
            st.caption(str(subtitle))

# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_kpi_row(kpis: List[Dict[str, Any]]) -> None:
    """Render a list of KPIs in rows of up to _CARDS_PER_ROW columns."""
    for start in range(0, len(kpis), _CARDS_PER_ROW):
        row = kpis[start : start + _CARDS_PER_ROW]
        cols = st.columns(len(row))
        for col, kpi in zip(cols, row):
            with col:
                render_kpi_card(kpi)


def _format_value(value: Any, fmt: str) -> str:
    """Convert a raw KPI value to a display string."""
    if value is None:
        return "—"
    try:
        if fmt == "integer":
            return f"{int(value):,}"
        if fmt == "decimal":
            return f"{float(value):,.2f}"
        if fmt == "percent":
            return f"{float(value):.1f}%"
        if fmt == "date":
            return str(value)
    except (TypeError, ValueError):
        pass
    return str(value)
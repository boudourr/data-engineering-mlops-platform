"""
dashboard.py
------------

Orchestrator component for the generic BI dashboard layout.

``render_bi_dashboard`` assembles every section of the dashboard from an
analysis result produced by ``BIGenerator.analyze()``.  No column names or
business logic from any specific dataset are present here.

Sections rendered
-----------------
1. Dataset Overview    — metric row
2. Detected Schema     — expandable column-type table
3. Key Metrics         — styled KPI cards (grouped by category)
4. Data Trends         — temporal + numerical line charts
5. Categorical Analysis — bar / pie / count charts
6. Numerical Analysis  — histogram / scatter / box / heatmap
7. Data Explorer       — interactive, filterable DataFrame
8. Download            — export current dataset as CSV
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from components.chart_generator import render_charts
from components.kpi_generator import render_kpis


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def render_bi_dashboard(
    df: pd.DataFrame,
    dataset_name: str,
    analysis: Dict[str, Any],
    *,
    show_explorer: bool = True,
    show_download: bool = True,
) -> None:
    """
    Render the complete BI dashboard for ``df``.

    Parameters
    ----------
    df:
        The DataFrame to visualise.
    dataset_name:
        Human-readable name shown in section titles.
    analysis:
        Dict returned by ``BIGenerator.analyze()``.
    show_explorer:
        Whether to render the interactive Data Explorer table.
    show_download:
        Whether to render the CSV download button.
    """
    summary: Dict[str, Any] = analysis.get("summary", {})
    profile: Dict[str, Any] = analysis.get("profile", {})
    kpis: List[Dict[str, Any]] = analysis.get("kpis", [])
    charts: List[Dict[str, Any]] = analysis.get("charts", [])

    # ── 1. Dataset Overview ───────────────────────────────────────────────────
    _render_overview(summary)

    st.divider()

    # ── 2. Detected Schema ────────────────────────────────────────────────────
    _render_schema(df, profile)

    st.divider()

    # ── 3. Key Metrics ────────────────────────────────────────────────────────
    with st.container(border=True):
        _section_header("📌 Key Metrics", "Automatically generated from detected column types.")
        render_kpis(kpis)

    st.divider()

    # ── 4–6. Charts (organised by section inside render_charts) ───────────────
    _section_header(
        "📊 Automatically Generated Dashboard",
        "Charts are selected and titled dynamically from the detected dataset structure.",
    )
    render_charts(df, charts)

    st.divider()

    # ── 7. Data Explorer ──────────────────────────────────────────────────────
    if show_explorer:
        with st.container(border=True):
            _render_explorer(df)
        st.divider()

    # ── 8. Download ───────────────────────────────────────────────────────────
    if show_download:
        _render_download(df, dataset_name)


# ─────────────────────────────────────────────────────────────────────────────
# Section renderers
# ─────────────────────────────────────────────────────────────────────────────

def _render_overview(summary: Dict[str, Any]) -> None:
    """Render the dataset-level metric row."""
    _section_header("🗂️ Dataset Overview")

    metrics = [
        ("Rows",         f"{summary.get('rows', 0):,}"),
        ("Columns",      f"{summary.get('columns', 0):,}"),
        ("Numerical",    str(summary.get("numerical_columns", 0))),
        ("Categorical",  str(summary.get("categorical_columns", 0))),
        ("Date / Time",  str(summary.get("datetime_columns", 0))),
        ("Missing Values", f"{summary.get('missing_values', 0):,} "
                           f"({summary.get('missing_pct', 0.0):.1f}%)"),
        ("Duplicate Rows", f"{summary.get('duplicate_rows', 0):,}"),
    ]

    # Render in a single row (truncate if too many)
    display_metrics = metrics[:7]
    cols = st.columns(len(display_metrics))
    for col, (label, value) in zip(cols, display_metrics):
        with col:
            with st.container(border=True):
                st.metric(label, value)


def _render_schema(
    df: pd.DataFrame,
    profile: Dict[str, Any],
) -> None:
    """Render an expandable table showing detected column types."""
    with st.expander("🔎 Detected Column Types", expanded=False):
        col_a, col_b = st.columns(2)

        with col_a:
            _column_type_block("🔢 Numerical", profile.get("numerical", []))
            _column_type_block("📅 Date / Time", profile.get("datetime", []))
            _column_type_block("🆔 Identifiers", profile.get("identifier", []))

        with col_b:
            _column_type_block("🏷️ Categorical", profile.get("categorical", []))
            _column_type_block("☑️ Boolean", profile.get("boolean", []))

        st.markdown("---")
        st.markdown("**Full Schema**")
        _render_schema_table(df)


def _column_type_block(header: str, columns: List[str]) -> None:
    """Render a small list of column names under a type header."""
    st.markdown(f"**{header}** ({len(columns)})")
    if columns:
        for col in columns:
            st.markdown(f"&nbsp;&nbsp;&nbsp;`{col}`", unsafe_allow_html=True)
    else:
        st.caption("None detected.")


def _render_schema_table(df: pd.DataFrame) -> None:
    """Display dtype, null count, and cardinality for every column."""
    total = len(df)
    missing = df.isna().sum()
    schema = pd.DataFrame({
        "Column": df.columns.astype(str),
        "Dtype": df.dtypes.astype(str).values,
        "Non-null": df.notna().sum().values,
        "Missing": missing.values,
        "Missing %": (
            (missing / total * 100).round(2).values
            if total else [0] * len(df.columns)
        ),
        "Unique": df.nunique(dropna=True).values,
    })
    st.dataframe(schema, use_container_width=True, hide_index=True)


def _render_explorer(df: pd.DataFrame) -> None:
    """Render an interactive, searchable DataFrame explorer."""
    _section_header("🔍 Data Explorer", "Inspect the dataset interactively.")

    # Search filter
    search_term = st.text_input(
        "Search / filter rows",
        placeholder="Type to filter across all columns…",
        key="bi_explorer_search",
    )

    if search_term:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        display_df = df[mask]
        st.caption(f"Showing {len(display_df):,} of {len(df):,} rows matching '{search_term}'")
    else:
        display_df = df
        st.caption(f"Showing all {len(df):,} rows")

    st.dataframe(display_df, use_container_width=True, height=460)


def _render_download(df: pd.DataFrame, dataset_name: str) -> None:
    """Render a CSV download button for the current dataset."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in dataset_name)
    st.download_button(
        label="⬇️ Download as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{safe_name}_export.csv",
        mime="text/csv",
        use_container_width=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layout helpers
# ─────────────────────────────────────────────────────────────────────────────

def _section_header(title: str, caption: Optional[str] = None) -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)

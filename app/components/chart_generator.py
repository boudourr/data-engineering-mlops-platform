"""
chart_generator.py
------------------

Generic chart rendering engine for the BI dashboard.

Charts are driven entirely by the specification dicts produced by
``BIGenerator.generate_chart_recommendations()``.  No column names or
business logic are hard-coded here.

Supported chart types
---------------------
line        DATE + NUMERICAL  →  line chart (aggregated by date)
bar         CATEGORICAL + NUMERICAL  →  horizontal bar chart (top-N)
histogram   NUMERICAL  →  distribution histogram
scatter     NUMERICAL + NUMERICAL  →  scatter plot
count       CATEGORICAL  →  value-frequency bar chart
pie         LOW-CARDINALITY CATEGORICAL  →  pie chart
box         NUMERICAL  →  box-and-whisker plot
heatmap     MULTIPLE NUMERICAL  →  correlation heatmap
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_TOP_N_BAR = 15          # maximum categories in bar / count charts
_HISTOGRAM_BINS = 30     # number of bins in histograms
_CHART_HEIGHT = 380      # px height for all charts (keeps layout uniform)

_SECTION_ORDER = ["trends", "categorical", "numerical", "correlation"]

# Professional colour palette — mirrors design tokens in ui_helpers.py
_PALETTE = [
    "#4F46E5",  # indigo-600
    "#7C3AED",  # violet-600
    "#06B6D4",  # cyan-500
    "#10B981",  # emerald-500
    "#F59E0B",  # amber-500
    "#EF4444",  # rose-500
    "#3B82F6",  # blue-500
    "#8B5CF6",  # violet-500
    "#14B8A6",  # teal-500
    "#F97316",  # orange-500
]

# Shared Plotly layout overrides applied to every figure
_PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", color="#0F172A"),
    paper_bgcolor="rgba(0,0,0,0)",   # transparent so the Streamlit card shows through
    plot_bgcolor="#F8FAFC",
    margin=dict(t=45, b=30, l=10, r=10),
    title_font=dict(size=13, color="#0F172A", family="Inter, sans-serif"),
    title_x=0,
    colorway=_PALETTE,
    xaxis=dict(
        gridcolor="#E2E8F0",
        linecolor="#E2E8F0",
        tickfont=dict(size=11, color="#64748B"),
        title_font=dict(size=11, color="#64748B"),
    ),
    yaxis=dict(
        gridcolor="#E2E8F0",
        linecolor="#E2E8F0",
        tickfont=dict(size=11, color="#64748B"),
        title_font=dict(size=11, color="#64748B"),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#64748B"),
    ),
)

_SECTION_META: Dict[str, Dict[str, str]] = {
    "trends": {
        "label": "📈 Data Trends",
        "description": "How numerical values evolve over time.",
    },
    "categorical": {
        "label": "🏷️ Categorical Analysis",
        "description": "Distribution and composition of categorical columns.",
    },
    "numerical": {
        "label": "🔢 Numerical Analysis",
        "description": "Distributions, outliers, and relationships between numerical columns.",
    },
    "correlation": {
        "label": "🔗 Correlation Analysis",
        "description": "Linear relationships between all numerical columns.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def render_charts(
    dataframe: pd.DataFrame,
    charts: List[Dict[str, Any]],
    *,
    charts_per_row: int = 2,
) -> None:
    """
    Render all charts organised into labelled sections.

    Parameters
    ----------
    dataframe:
        The DataFrame to visualise.
    charts:
        List of chart dicts from ``BIGenerator.generate_chart_recommendations()``.
    charts_per_row:
        Number of charts displayed side-by-side in each row.
    """
    if not charts:
        st.info("No suitable visualisations were found for this dataset.")
        return

    if not _PLOTLY_AVAILABLE:
        st.warning(
            "Plotly is not installed. Install it with `pip install plotly` "
            "to enable rich interactive charts. Falling back to basic charts."
        )
        _render_charts_basic(dataframe, charts, charts_per_row)
        return

    # Group charts by section
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for chart in charts:
        section = str(chart.get("section", "numerical"))
        grouped.setdefault(section, []).append(chart)

    active_sections = []
    for section in _SECTION_ORDER:
        if grouped.get(section):
            active_sections.append(section)

    if active_sections:
        tabs = st.tabs([_SECTION_META[s]["label"] for s in active_sections])
        for tab, section in zip(tabs, active_sections):
            with tab:
                meta = _SECTION_META[section]
                if meta.get("description"):
                    st.caption(meta["description"])
                st.markdown("<br>", unsafe_allow_html=True)
                _render_chart_grid(dataframe, grouped[section], charts_per_row)


def render_chart(dataframe: pd.DataFrame, chart: Dict[str, Any]) -> None:
    """Render a single chart from its specification dict."""
    chart_type = str(chart.get("type", ""))
    title = str(chart.get("title", "Visualisation"))

    if not _PLOTLY_AVAILABLE:
        _render_chart_basic(dataframe, chart)
        return

    try:
        fig = _build_figure(dataframe, chart_type, chart, title)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Unsupported chart type: {chart_type}")
    except Exception as exc:
        st.warning(f"Could not generate '{title}': {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure builders
# ─────────────────────────────────────────────────────────────────────────────

def _apply_theme(fig: Any, height: int = _CHART_HEIGHT) -> Any:
    """Apply the shared professional theme to any Plotly figure."""
    fig.update_layout(height=height, **_PLOTLY_LAYOUT)
    return fig

def _build_figure(
    df: pd.DataFrame,
    chart_type: str,
    spec: Dict[str, Any],
    title: str,
) -> Optional[Any]:
    """Dispatch to the appropriate Plotly figure builder."""

    if chart_type == "line":
        return _line_chart(df, spec, title)

    if chart_type == "bar":
        return _bar_chart(df, spec, title)

    if chart_type == "histogram":
        return _histogram(df, spec, title)

    if chart_type == "scatter":
        return _scatter(df, spec, title)

    if chart_type == "count":
        return _count_chart(df, spec, title)

    if chart_type == "pie":
        return _pie_chart(df, spec, title)

    if chart_type == "box":
        return _box_chart(df, spec, title)

    if chart_type == "heatmap":
        return _heatmap(df, spec, title)

    return None


def _line_chart(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    x_col = spec["x"]
    y_col = spec["y"]

    data = df[[x_col, y_col]].copy()
    data[x_col] = pd.to_datetime(data[x_col], errors="coerce")
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna()

    if data.empty:
        return _empty_figure(title)

    data = (
        data.groupby(x_col, as_index=False)[y_col]
        .sum()
        .sort_values(x_col)
    )

    fig = px.line(data, x=x_col, y=y_col, title=title, markers=True,
                  color_discrete_sequence=_PALETTE)
    fig.update_traces(line=dict(width=2.5), marker=dict(size=4))
    return _apply_theme(fig)


def _bar_chart(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    x_col = spec["x"]
    y_col = spec["y"]

    data = df[[x_col, y_col]].copy()
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna()

    if data.empty:
        return _empty_figure(title)

    data = (
        data.groupby(x_col, as_index=False)[y_col]
        .sum()
        .sort_values(y_col, ascending=False)
        .head(_TOP_N_BAR)
    )

    fig = px.bar(data, x=y_col, y=x_col, orientation="h", title=title,
                 color=y_col, color_continuous_scale=["#818CF8", "#4F46E5", "#3730A3"])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    return _apply_theme(fig)


def _histogram(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    col = spec["column"]
    data = pd.to_numeric(df[col], errors="coerce").dropna()

    if data.empty:
        return _empty_figure(title)

    fig = px.histogram(data, nbins=_HISTOGRAM_BINS, title=title,
                       color_discrete_sequence=["#4F46E5"])
    fig.update_traces(marker_line_color="#3730A3", marker_line_width=0.5)
    fig.update_layout(bargap=0.05, xaxis_title=col, yaxis_title="Count", showlegend=False)
    return _apply_theme(fig)


def _scatter(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    x_col = spec["x"]
    y_col = spec["y"]

    data = df[[x_col, y_col]].copy()
    data[x_col] = pd.to_numeric(data[x_col], errors="coerce")
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna()

    if data.empty:
        return _empty_figure(title)

    if len(data) > 5000:
        data = data.sample(5000, random_state=42)

    fig = px.scatter(data, x=x_col, y=y_col, title=title, opacity=0.65,
                     color_discrete_sequence=["#4F46E5"])
    fig.update_traces(marker=dict(size=6, line=dict(width=0.5, color="#3730A3")))
    return _apply_theme(fig)


def _count_chart(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    col = spec["column"]
    counts = (
        df[col].astype(str)
        .value_counts()
        .head(_TOP_N_BAR)
        .reset_index()
    )
    counts.columns = [col, "count"]

    if counts.empty:
        return _empty_figure(title)

    fig = px.bar(counts, x="count", y=col, orientation="h", title=title,
                 color="count", color_continuous_scale=["#C7D2FE", "#4F46E5"])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    return _apply_theme(fig)


def _pie_chart(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    col = spec["column"]
    counts = df[col].astype(str).value_counts().reset_index()
    counts.columns = [col, "count"]

    if counts.empty:
        return _empty_figure(title)

    fig = px.pie(counts, names=col, values="count", title=title,
                 color_discrete_sequence=_PALETTE)
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      marker=dict(line=dict(color="#FFFFFF", width=2)))
    return _apply_theme(fig)


def _box_chart(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    col = spec["column"]
    data = pd.to_numeric(df[col], errors="coerce").dropna()

    if data.empty:
        return _empty_figure(title)

    fig = px.box(data, title=title, points="outliers",
                 color_discrete_sequence=["#4F46E5"])
    fig.update_layout(yaxis_title=col, showlegend=False)
    return _apply_theme(fig)


def _heatmap(df: pd.DataFrame, spec: Dict[str, Any], title: str) -> Any:
    cols = spec.get("columns", [])
    if not cols:
        return _empty_figure(title)

    numeric_df = df[cols].apply(pd.to_numeric, errors="coerce").dropna()

    if numeric_df.shape[1] < 2 or numeric_df.empty:
        return _empty_figure(title)

    corr = numeric_df.corr().round(2)

    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale=["#EDE9FE", "#7C3AED", "#4F46E5"],
        zmin=-1,
        zmax=1,
        title=title,
        aspect="auto",
    )
    return _apply_theme(fig, height=max(_CHART_HEIGHT, len(cols) * 40 + 80))


# ─────────────────────────────────────────────────────────────────────────────
# Layout helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_chart_grid(
    df: pd.DataFrame,
    charts: List[Dict[str, Any]],
    charts_per_row: int,
) -> None:
    """Display charts in a grid of ``charts_per_row`` columns."""
    for i in range(0, len(charts), charts_per_row):
        row = charts[i : i + charts_per_row]
        cols = st.columns(len(row))
        for col, chart in zip(cols, row):
            with col:
                render_chart(df, chart)


def _empty_figure(title: str) -> Any:
    """Return a placeholder figure when data is insufficient."""
    fig = go.Figure()
    fig.update_layout(
        title=f"{title} — no data",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": "Not enough data to display this chart.",
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 13, "color": "#94A3B8"},
        }],
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: basic Streamlit charts (when Plotly is unavailable)
# ─────────────────────────────────────────────────────────────────────────────

def _render_charts_basic(
    df: pd.DataFrame,
    charts: List[Dict[str, Any]],
    charts_per_row: int,
) -> None:
    for i in range(0, len(charts), charts_per_row):
        row = charts[i : i + charts_per_row]
        cols = st.columns(len(row))
        for col, chart in zip(cols, row):
            with col:
                st.caption(chart.get("title", "Visualisation"))
                _render_chart_basic(df, chart)


def _render_chart_basic(df: pd.DataFrame, chart: Dict[str, Any]) -> None:
    """Minimal fallback renderer using native Streamlit chart functions."""
    chart_type = chart.get("type", "")
    try:
        if chart_type == "line":
            x, y = chart["x"], chart["y"]
            data = df[[x, y]].copy()
            data[x] = pd.to_datetime(data[x], errors="coerce")
            data[y] = pd.to_numeric(data[y], errors="coerce")
            data = data.dropna().groupby(x)[y].sum().sort_index()
            st.line_chart(data)

        elif chart_type in {"bar", "count"}:
            col = chart.get("column") or chart.get("x")
            y_col = chart.get("y")
            if y_col and col:
                data = df[[col, y_col]].copy()
                data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
                data = data.dropna().groupby(col)[y_col].sum().sort_values(ascending=False).head(15)
            else:
                data = df[col].astype(str).value_counts().head(15)
            st.bar_chart(data)

        elif chart_type == "histogram":
            col = chart["column"]
            data = pd.to_numeric(df[col], errors="coerce").dropna()
            st.bar_chart(data.value_counts(bins=20, sort=False))

        elif chart_type == "scatter":
            x, y = chart["x"], chart["y"]
            data = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
            st.scatter_chart(data, x=x, y=y)

        elif chart_type in {"pie", "box", "heatmap"}:
            st.info(f"Chart type '{chart_type}' requires Plotly.")

    except Exception as exc:
        st.warning(f"Could not render chart: {exc}")
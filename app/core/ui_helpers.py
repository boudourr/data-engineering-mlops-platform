"""Reusable Streamlit presentation helpers for the data engineering platform.

The functions in this module deliberately describe data in general terms.  They
do not assume a particular source system, dataset, schema, or pipeline layout.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import pandas as pd
import streamlit as st


_STATUS_DETAILS = {
    "success": {"label": "Completed", "icon": "✅", "color": "#198754"},
    "running": {"label": "Running", "icon": "🔄", "color": "#0d6efd"},
    "pending": {"label": "Pending", "icon": "⏳", "color": "#6c757d"},
    "warning": {"label": "Warning", "icon": "⚠️", "color": "#d97706"},
    "failed": {"label": "Failed", "icon": "❌", "color": "#dc3545"},
    "unknown": {"label": "Unknown", "icon": "❔", "color": "#6c757d"},
}


def inject_global_css() -> None:
    """
    Inject the global professional CSS design system.
    """
    st.markdown(
        """
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet" />
<style>
/* ═══════════════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════════════ */
:root {
    --primary:        #4F46E5;   /* indigo-600  */
    --primary-light:  #818CF8;   /* indigo-400  */
    --primary-dark:   #3730A3;   /* indigo-800  */
    --accent:         #7C3AED;   /* violet-600  */
    --success:        #10B981;   /* emerald-500 */
    --warning:        #F59E0B;   /* amber-500   */
    --danger:         #EF4444;   /* rose-500    */
    --info:           #06B6D4;   /* cyan-500    */
    --bg:             #F1F5F9;   /* slate-100   */
    --bg-card:        #FFFFFF;
    --bg-sidebar:     #1E293B;   /* slate-800   */
    --text:           #0F172A;   /* slate-900   */
    --text-muted:     #64748B;   /* slate-500   */
    --border:         #E2E8F0;   /* slate-200   */
    --shadow-sm:      0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
    --shadow-md:      0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.06);
    --shadow-lg:      0 10px 15px rgba(0,0,0,.06), 0 4px 6px rgba(0,0,0,.05);
    --radius:         12px;
    --radius-sm:      8px;
}
/* ═══════════════════════════════════════════════════════════════════════
   GLOBAL PAGE
   ═══════════════════════════════════════════════════════════════════════ */
.stApp {
    background-color: var(--bg) !important;
}
/* remove extra top padding Streamlit adds */
.block-container {
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   SIDEBAR  — dark professional rail
   ═══════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: radial-gradient(circle at 20% 0%, #334155 0%, #1E293B 32%, #0F172A 100%) !important;
    border-right: 1px solid #334155 !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: .55rem !important;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #94A3B8 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #F1F5F9 !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}
/* Sidebar nav links (multipage) */
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
    padding: .35rem .65rem .85rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] > ul {
    gap: .18rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] span {
    font-size: .86rem !important;
}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
    border-radius: 10px !important;
    padding: .58rem .72rem !important;
    margin-bottom: 3px !important;
    color: #CBD5E1 !important;
    border: 1px solid transparent !important;
    transition: background .15s ease, transform .15s ease, border-color .15s ease;
}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,.08) !important;
    color: #F8FAFC !important;
    border-color: rgba(255,255,255,.08) !important;
    transform: translateX(2px);
}
section[data-testid="stSidebar"] a[aria-current="page"] {
    background: linear-gradient(90deg, rgba(99,102,241,.9), rgba(124,58,237,.58)) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border: 1px solid rgba(199,210,254,.3) !important;
    box-shadow: 0 6px 16px rgba(15,23,42,.28) !important;
}
.sidebar-brand-card {
    margin: .3rem .8rem .75rem;
    padding: .9rem;
    border: 1px solid rgba(165,180,252,.25);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(99,102,241,.26), rgba(124,58,237,.12));
}
.sidebar-brand-card .brand-title {
    color: #F8FAFC !important;
    font-weight: 750;
    font-size: .88rem;
    letter-spacing: -.01em;
}
.sidebar-brand-card .brand-copy {
    margin-top: .25rem;
    color: #CBD5E1 !important;
    font-size: .72rem;
    line-height: 1.45;
}
.sidebar-workspace-card {
    margin: .25rem .8rem .7rem;
    padding: .75rem .85rem;
    border-radius: 12px;
    background: rgba(255,255,255,.045);
    border: 1px solid rgba(148,163,184,.16);
}
.sidebar-workspace-card .eyebrow {
    color: #94A3B8 !important;
    font-size: .65rem;
    font-weight: 750;
    letter-spacing: .1em;
}
.sidebar-workspace-card .value {
    color: #F8FAFC !important;
    margin-top: .22rem;
    font-size: .78rem;
    font-weight: 650;
}
/* ═══════════════════════════════════════════════════════════════════════
   METRIC CARDS  — accent top border per category colour
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: 3px solid var(--primary) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.1rem 0.8rem !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
div[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-2px);
}
div[data-testid="metric-container"] label {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   CONTAINERS WITH BORDER  — professional card look
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: var(--shadow-md) !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   TABS  — clean pill nav
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stTabs"] button[role="tab"] {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    padding: 0.5rem 1.2rem !important;
    transition: color 0.15s, background 0.15s;
}
div[data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--primary) !important;
    background: rgba(79,70,229,0.06) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
    background: transparent !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════════════ */
button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 2px 8px rgba(79,70,229,0.35) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.45) !important;
}
button[kind="secondary"] {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--border) !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease, color 0.15s ease !important;
}
button[kind="secondary"]:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   SELECT BOX / TEXT INPUT / TEXT AREA
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] > div,
div[data-testid="stTextInput"] > div,
div[data-testid="stTextArea"] > div {
    border-radius: var(--radius-sm) !important;
}
div[data-testid="stSelectbox"] > div:focus-within,
div[data-testid="stTextInput"] > div:focus-within,
div[data-testid="stTextArea"] > div:focus-within {
    box-shadow: 0 0 0 3px rgba(79,70,229,0.2) !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   EXPANDER
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--bg-card) !important;
    box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--text) !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   ALERTS / BANNER MESSAGES
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border-left-width: 4px !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   DATAFRAME / TABLE
   ═══════════════════════════════════════════════════════════════════════ */
div[data-testid="stDataFrame"] > div {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   DIVIDER
   ═══════════════════════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}
/* ═══════════════════════════════════════════════════════════════════════
   PROGRESS BAR
   ═══════════════════════════════════════════════════════════════════════ */
div[role="progressbar"] > div {
    background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
    border-radius: 999px !important;
}
</style>
        """,
        unsafe_allow_html=True
    )


def page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """Render a styled gradient page heading with an optional subtitle."""
    inject_global_css()
    render_sidebar_context()
    
    icon_html = ""
    if icon:
        if icon.startswith(":material/") and icon.endswith(":"):
            mat_icon = icon.replace(":material/", "").replace(":", "")
            icon_html = f"<span class='material-symbols-outlined' style='vertical-align: bottom; margin-right: 0.4rem; font-size: 2.2rem;'>{mat_icon}</span>"
        else:
            icon_html = f"<span style='margin-right:0.4rem'>{icon}</span>"
            
    st.markdown(
        f"""
<div style="
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    border-radius: 16px;
    padding: 1.6rem 2rem 1.5rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 20px rgba(79,70,229,0.25);
">
    <h1 style="
        display: flex; align-items: center;
        margin:0; padding:0;
        color:#FFFFFF;
        font-size:1.9rem;
        font-weight:800;
        letter-spacing:-0.02em;
        line-height:1.2;
    ">{icon_html}{title}</h1>
    {"" if not subtitle else f'<p style="margin:0.45rem 0 0 0; padding:0; color:rgba(255,255,255,0.75); font-size:0.9rem; font-weight:400;">{subtitle}</p>'}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_context() -> None:
    """Render a compact, consistent context area beneath native page navigation."""
    with st.sidebar:
        st.markdown(
            """
<div class="sidebar-brand-card">
  <div style="display:flex; align-items:center; gap:.45rem;">
    <span class="material-symbols-outlined" style="color:#C7D2FE !important; font-size:1.2rem;">hub</span>
    <span class="brand-title">Data Operations</span>
  </div>
  <div class="brand-copy">A focused workspace for every stage of your data lifecycle.</div>
</div>
<div class="sidebar-workspace-card">
  <div class="eyebrow">WORKSPACE STATUS</div>
  <div class="value"><span style="color:#34D399 !important;">●</span> Ready for a new run</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def section_title(title: str, description: Optional[str] = None) -> None:
    """Render a section heading with a coloured left-border accent."""
    st.markdown(
        f"""
<div style="
    border-left: 4px solid #4F46E5;
    padding-left: 0.75rem;
    margin: 1.4rem 0 0.3rem 0;
">
    <h3 style="
        margin:0; padding:0;
        color:#0F172A;
        font-size:1.05rem;
        font-weight:700;
        letter-spacing:-0.01em;
    ">{title}</h3>
    {"" if not description else f'<p style="margin:0.2rem 0 0 0; padding:0; color:#64748B; font-size:0.82rem;">{description}</p>'}
</div>
        """,
        unsafe_allow_html=True,
    )


def normalize_status(status: Any) -> str:
    """Return a supported, canonical status name for arbitrary input."""
    if isinstance(status, bool):
        return "success" if status else "failed"
    value = str(status or "unknown").strip().lower().replace("_", " ").replace("-", " ")
    aliases = {
        "complete": "success", "completed": "success", "done": "success", "ok": "success",
        "passed": "success", "healthy": "success", "active": "running", "in progress": "running",
        "queued": "pending", "not started": "pending", "skipped": "pending",
        "warn": "warning", "degraded": "warning", "error": "failed", "failure": "failed",
        "unsuccessful": "failed", "not available": "unknown", "": "unknown",
    }
    return aliases.get(value, value if value in _STATUS_DETAILS else "unknown")


def status_badge(status: Any, label: Optional[str] = None) -> None:
    """Render a small, color-coded badge for a status value."""
    normalized = normalize_status(status)
    details = _STATUS_DETAILS[normalized]
    text = label or details["label"]
    st.markdown(
        f"<span style='color:{details['color']}; font-weight:600'>{details['icon']} {text}</span>",
        unsafe_allow_html=True,
    )


def status_message(status: Any, message: str) -> None:
    """Show a Streamlit message whose severity reflects ``status``."""
    normalized = normalize_status(status)
    if normalized == "success":
        st.toast(f"✅ {message}")
    elif normalized == "failed":
        st.error(message)
    elif normalized == "warning":
        st.warning(message)
    else:
        st.toast(f"ℹ️ {message}")


def pipeline_status_grid(statuses: Mapping[str, Any], columns: int = 3) -> None:
    """Display named pipeline statuses in a responsive grid."""
    if not statuses:
        st.info("No pipeline status is available yet.")
        return
    columns = max(1, int(columns))
    for start in range(0, len(statuses), columns):
        row = st.columns(columns)
        for column, (name, value) in zip(row, list(statuses.items())[start : start + columns]):
            with column:
                st.markdown(f"**{name}**")
                status_badge(value)


def health_message(health: Any, message: Optional[str] = None) -> None:
    """Present a high-level health indicator, accepting a value or mapping."""
    if isinstance(health, Mapping):
        status = health.get("status", health.get("health", "unknown"))
        message = message or str(health.get("message", "System health updated."))
    else:
        status = health
        message = message or "System health updated."
    status_message(status, message)


def initialize_session_state(defaults: Optional[Mapping[str, Any]] = None) -> None:
    """Set missing Streamlit session-state keys without overwriting user state."""
    base_defaults = {
        "uploaded_files": [],
        "pipeline_status": {},
        "current_dataset": None,
        "execution_results": {},
        "health_status": "unknown",
    }
    if defaults:
        base_defaults.update(defaults)
    for key, value in base_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_button(label: str = "Run", *, key: Optional[str] = None, disabled: bool = False,
               help_text: Optional[str] = None, use_container_width: bool = False) -> bool:
    """Render and return a standard primary action button."""
    return st.button(label, key=key, type="primary", disabled=disabled, help=help_text,
                     use_container_width=use_container_width)


def flatten_result(value: Any, parent_key: str = "", separator: str = ".") -> dict[str, Any]:
    """Flatten nested mappings and sequences into a single-row, table-friendly mapping."""
    flattened: dict[str, Any] = {}
    if isinstance(value, Mapping):
        for key, item in value.items():
            child_key = f"{parent_key}{separator}{key}" if parent_key else str(key)
            flattened.update(flatten_result(item, child_key, separator))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        flattened[parent_key or "value"] = ", ".join(map(str, value))
    else:
        flattened[parent_key or "value"] = value
    return flattened


def display_result_table(result: Any, *, hide_index: bool = True) -> None:
    """Display a DataFrame, a collection of records, or a flattened result safely."""
    if result is None:
        st.info("No result is available.")
        return
    try:
        if isinstance(result, pd.DataFrame):
            table = result
        elif isinstance(result, Mapping):
            table = pd.DataFrame([flatten_result(result)])
        elif isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
            table = pd.DataFrame([flatten_result(item) if isinstance(item, Mapping) else {"value": item} for item in result])
        else:
            table = pd.DataFrame({"value": [result]})
        st.dataframe(table, use_container_width=True, hide_index=hide_index)
    except Exception as exc:
        st.warning(f"The result could not be displayed as a table: {exc}")


def show_execution_result(result: Any, success_message: str = "Execution completed.") -> None:
    """Show an execution outcome and its available details."""
    if result is None:
        st.info("No execution result is available.")
        return
    status = result.get("status", result.get("success", "unknown")) if isinstance(result, Mapping) else "success"
    message = result.get("message", success_message) if isinstance(result, Mapping) else success_message
    status_message(status, str(message))
    if isinstance(result, Mapping):
        details = {key: value for key, value in result.items() if key not in {"status", "success", "message"}}
        if details:
            display_result_table(details)
    elif isinstance(result, pd.DataFrame):
        display_result_table(result)


def display_dataset_summary(dataframe: Optional[pd.DataFrame]) -> None:
    """Display general dimensions and memory use for a dataset."""
    if dataframe is None:
        st.info("No dataset is selected.")
        return
    rows, fields = dataframe.shape
    memory = int(dataframe.memory_usage(deep=True).sum())
    units = ("B", "KB", "MB", "GB")
    size, unit = float(memory), units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    metric_columns = st.columns(3)
    metric_columns[0].metric("Rows", f"{rows:,}")
    metric_columns[1].metric("Columns", f"{fields:,}")
    metric_columns[2].metric("Memory", f"{size:.1f} {unit}")


def preview_dataset(dataframe: Optional[pd.DataFrame], rows: int = 10) -> None:
    """Show the first ``rows`` records of a dataset without modifying it."""
    if dataframe is None or dataframe.empty:
        st.info("No rows are available to preview.")
        return
    st.dataframe(dataframe.head(max(1, int(rows))), use_container_width=True, hide_index=True)


def display_schema(dataframe: Optional[pd.DataFrame]) -> None:
    """Display inferred field types and basic completeness statistics."""
    if dataframe is None:
        st.info("No schema is available.")
        return
    total_rows = len(dataframe)
    missing = dataframe.isna().sum()
    schema = pd.DataFrame({
        "Field": dataframe.columns.astype(str),
        "Data type": dataframe.dtypes.astype(str).values,
        "Non-null values": dataframe.notna().sum().values,
        "Missing values": missing.values,
        "Missing (%)": ((missing / total_rows * 100) if total_rows else 0).round(2).values,
        "Unique values": dataframe.nunique(dropna=True).values,
    })
    st.dataframe(schema, use_container_width=True, hide_index=True)


def safe_read_csv(source: Any, **read_csv_kwargs: Any) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read a CSV source and return ``(dataframe, error_message)`` instead of raising."""
    try:
        if source is None:
            return None, "Please select a CSV file first."
        if hasattr(source, "seek"):
            source.seek(0)
        return pd.read_csv(source, **read_csv_kwargs), None
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        return None, f"Could not read the CSV file: {exc}"


def display_file_list(files: Optional[Sequence[Any]]) -> None:
    """Display a compact table for uploaded files or filesystem paths."""
    if not files:
        st.info("No files have been uploaded.")
        return
    records = []
    for file in files:
        path = Path(str(file)) if isinstance(file, (str, Path)) else None
        name = getattr(file, "name", path.name if path else "Unnamed file")
        size = getattr(file, "size", path.stat().st_size if path and path.exists() else None)
        mime_type = getattr(file, "type", path.suffix.lstrip(".") if path else "")
        records.append({"Name": name, "Size (bytes)": size, "Type": mime_type})
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)

"""
09_BI_Dashboard.py
------------------

Generic BI & Analytics Dashboard page.

This page is DATASET-INDEPENDENT.  It works with any structured dataset,
regardless of domain.  Olist is supported only as a test dataset through
the same generic code path as any other dataset.

Workflow
--------
1. User selects a data source tier (Gold / Silver / Uploads)
2. User picks one dataset from that tier
3. Dataset is loaded into a pandas DataFrame
4. BIGenerator profiles the DataFrame automatically
5. Dashboard is rendered with dynamically generated KPIs and charts
6. Optional: user can embed their own Power BI report URL

Nothing in this page assumes specific column names or business logic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Path setup — must run before any project imports
# ─────────────────────────────────────────────────────────────────────────────

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

for _p in (str(APP_ROOT), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ─────────────────────────────────────────────────────────────────────────────
# Project imports
# ─────────────────────────────────────────────────────────────────────────────

try:
    from core.bi_generator import BIGenerator, SourceTier
    from core.config import config
    from core.ui_helpers import initialize_session_state, page_header, section_title
    from components.dashboard import render_bi_dashboard
except ImportError as exc:
    st.error("Required project modules could not be imported.")
    st.code(str(exc))
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BI & Analytics | Modern Data Engineering Platform",
    page_icon=":bar_chart:",
    layout="wide",
)

config.create_directories()
initialize_session_state({
    "bi_dataframe": None,
    "bi_dataset_name": None,
    "bi_analysis": None,
})


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions (defined at top so they can be called anywhere below)
# ─────────────────────────────────────────────────────────────────────────────

def _safe_load(path: Path) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a dataset file and return (DataFrame, error_message)."""
    try:
        return BIGenerator.load_dataframe(path), None
    except Exception as exc:
        return None, str(exc)


def _render_structure_badges(df: pd.DataFrame) -> None:
    """
    Show a quick badge row describing the dataset column composition.
    Uses BIGenerator temporarily to classify column types.
    """
    try:
        gen = BIGenerator(dataframe=df, dataset_name="")
        p = gen.profile
        badges = [
            ("📋 Rows",        f"{p.rows:,}"),
            ("📐 Columns",     str(p.columns)),
            ("🔢 Numerical",   str(len(p.numerical))),
            ("🏷️ Categorical", str(len(p.categorical))),
            ("📅 Date/Time",   str(len(p.datetime))),
            ("⚠️ Missing",     f"{p.missing_values:,} ({p.missing_pct:.1f}%)"),
        ]
        cols = st.columns(len(badges))
        for col, (label, value) in zip(cols, badges):
            col.metric(label, value)
    except Exception:
        # Fallback — raw shape only
        col_a, col_b = st.columns(2)
        col_a.metric("Rows", f"{len(df):,}")
        col_b.metric("Columns", str(len(df.columns)))


def _render_powerbi_section() -> None:
    """
    Optional Power BI embed section.

    Collapsed by default.  Activates only when the user voluntarily pastes
    their own Power BI embed URL.  No Olist-specific URL is hard-coded.
    """
    with st.expander("🔗 Optional: Power BI Integration", expanded=False):
        st.markdown(
            """
            **Power BI** can complement the native dashboard above when you have a
            dedicated Power BI report configured for your dataset.

            **Steps to embed your report:**
            1. Publish the report to the Power BI service.
            2. Open the report → **File → Embed report → Website or portal**.
            3. Copy the embed URL and paste it below.
            """
        )

        embed_url = st.text_input(
            "Power BI embed URL",
            placeholder="https://app.powerbi.com/reportEmbed?reportId=…",
            key="bi_powerbi_url",
        )

        if embed_url and embed_url.startswith("https://"):
            iframe_height = st.slider(
                "Report height (px)",
                min_value=400,
                max_value=1200,
                value=700,
                step=50,
                key="bi_powerbi_height",
            )
            st.components.v1.iframe(embed_url, height=iframe_height, scrolling=True)
        elif embed_url:
            st.warning("Please enter a valid HTTPS embed URL.")
        else:
            st.caption(
                "Paste a Power BI embed URL above to display your report here. "
                "This field is optional — the native dashboard above works for any dataset."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────

page_header(
    "BI & Analytics Dashboard",
    "Automatic dashboard generation — works with any uploaded dataset.",
    icon=":material/dashboard:",
)

st.markdown(
    "The dashboard is generated **dynamically** from the structure of the selected dataset. "
    "No column names, KPIs, or chart types are hard-coded — everything is discovered automatically."
)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Dataset selection
# ─────────────────────────────────────────────────────────────────────────────

section_title(
    "Dataset Selection",
    "Choose which dataset to analyse. The platform automatically lists the most processed "
    "version available (Gold → Silver → Uploads).",
)

tiers: List[SourceTier] = BIGenerator.discover_source_tiers(PROJECT_ROOT)

if not tiers:
    st.info(
        "No datasets are available yet. "
        "Upload a dataset on the **Data Upload** page, or run the **ETL / Warehouse** pipeline first."
    )
    _render_powerbi_section()
    st.stop()

# ── Tier selector ──────────────────────────────────────────────────────────
tier_labels = [t.label for t in tiers]
selected_tier_label = st.selectbox(
    "Data source tier",
    options=tier_labels,
    index=0,
    help=(
        "Gold = warehouse output (most processed), "
        "Silver = cleaned ETL output, "
        "Uploads = raw files."
    ),
    key="bi_tier_selector",
)

selected_tier: SourceTier = next(t for t in tiers if t.label == selected_tier_label)

# ── File selector within the chosen tier ──────────────────────────────────
file_options = selected_tier.datasets
file_labels = [f.name for f in file_options]

selected_file_name = st.selectbox(
    "Dataset file",
    options=file_labels,
    index=0,
    key="bi_file_selector",
)
selected_file_path: Path = next(f for f in file_options if f.name == selected_file_name)

st.caption(f"📁 `{selected_file_path}`")

# ── Action buttons ─────────────────────────────────────────────────────────
col_load, col_clear = st.columns([3, 1])
with col_load:
    load_clicked = st.button(
        "📂 Load Dataset",
        type="primary",
        use_container_width=True,
        key="bi_load_btn",
    )
with col_clear:
    if st.button("🗑️ Clear", use_container_width=True, key="bi_clear_btn"):
        st.session_state["bi_dataframe"] = None
        st.session_state["bi_dataset_name"] = None
        st.session_state["bi_analysis"] = None
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Load and cache the dataset
# ─────────────────────────────────────────────────────────────────────────────

if load_clicked:
    with st.spinner(f"Loading {selected_file_name}…"):
        df_loaded, load_error = _safe_load(selected_file_path)

    if load_error:
        st.error(f"Could not load **{selected_file_name}**: {load_error}")
    elif df_loaded is None or df_loaded.empty:
        st.warning("The selected file is empty or could not be parsed.")
    else:
        st.session_state["bi_dataframe"] = df_loaded
        st.session_state["bi_dataset_name"] = selected_file_name
        st.session_state["bi_analysis"] = None   # invalidate cached analysis
        st.success(
            f"✅ Loaded **{selected_file_name}** — "
            f"{len(df_loaded):,} rows × {len(df_loaded.columns)} columns"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Retrieve the active DataFrame
# ─────────────────────────────────────────────────────────────────────────────

df: Optional[pd.DataFrame] = st.session_state.get("bi_dataframe")
dataset_name: str = str(st.session_state.get("bi_dataset_name") or "Dataset")

if df is None:
    st.info("Select a dataset above and click **Load Dataset** to generate the dashboard.")
    st.divider()
    _render_powerbi_section()
    st.stop()

if df.empty:
    st.error("The loaded dataset is empty. Please select a different file.")
    st.stop()

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Dataset structure preview
# ─────────────────────────────────────────────────────────────────────────────

section_title(
    "Dataset Structure",
    f"Auto-detected column profile for **{dataset_name}**.",
)
_render_structure_badges(df)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Generate dashboard button
# ─────────────────────────────────────────────────────────────────────────────

generate_clicked = st.button(
    "⚡ Generate Dashboard",
    type="primary",
    use_container_width=True,
    key="bi_generate_btn",
)

# Use cached analysis or regenerate on button click
analysis: Optional[Dict[str, Any]] = st.session_state.get("bi_analysis")

if generate_clicked or analysis is None:
    with st.spinner("Analysing dataset and generating dashboard…"):
        try:
            generator = BIGenerator(dataframe=df, dataset_name=dataset_name)
            analysis = generator.analyze()
            st.session_state["bi_analysis"] = analysis
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.exception(exc)
            st.stop()

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Render the complete BI dashboard
# ─────────────────────────────────────────────────────────────────────────────

render_bi_dashboard(
    df=df,
    dataset_name=dataset_name,
    analysis=analysis,
    show_explorer=True,
    show_download=True,
)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Optional Power BI section (always at the bottom)
# ─────────────────────────────────────────────────────────────────────────────

_render_powerbi_section()

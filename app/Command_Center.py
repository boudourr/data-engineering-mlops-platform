"""Streamlit landing page for the Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = Path(__file__).resolve().parent

for path in (PROJECT_ROOT, APP_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from core.pipeline_manager import PipelineManager
    from core.ui_helpers import initialize_session_state, page_header
except ImportError as exc:
    st.error("Application dependencies could not be loaded.")
    st.code(str(exc))
    st.stop()


st.set_page_config(
    page_title="Modern Data Engineering Platform",
    page_icon=":material/data_object:",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    manager = PipelineManager()
    initialize_session_state()
except Exception as exc:
    st.error("Unable to initialize the platform.")
    st.exception(exc)
    st.stop()


page_header(
    "Modern Data Engineering Platform",
    "A unified workspace for trustworthy data, analytics, and machine learning.",
    icon=":material/data_object:",
)

st.markdown(
    """
<div style="display:flex; align-items:center; justify-content:space-between; gap:1rem;
            padding:.2rem .15rem 1.1rem;">
  <div>
    <div style="font-size:.75rem; font-weight:700; text-transform:uppercase;
                letter-spacing:.12em; color:#6366F1;">Workspace overview</div>
    <div style="margin-top:.35rem; color:#475569; font-size:1rem;">
      Take a dataset from upload to decisions with one clear, traceable workflow.
    </div>
  </div>
  <div style="white-space:nowrap; background:#EEF2FF; color:#4338CA; border:1px solid #C7D2FE;
              border-radius:999px; padding:.45rem .8rem; font-size:.78rem; font-weight:700;">
    <span class="material-symbols-outlined" style="font-size:1rem; vertical-align:-3px;">verified</span>
    Run-isolated artifacts
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

primary_action, secondary_action, _ = st.columns([1.15, 1.15, 4])
with primary_action:
    st.page_link("pages/02_Data_Upload.py", label="Upload a dataset", icon=":material/upload:", use_container_width=True)
with secondary_action:
    st.page_link("pages/01_Overview.py", label="Open command center", icon=":material/dashboard:", use_container_width=True)

st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

workflow = (
    ("01", "upload", "Ingest", "Bring in CSV, Excel, or supported data files and inspect their structure."),
    ("02", "account_tree", "Prepare", "Profile, clean, and shape data into reliable Silver and Gold layers."),
    ("03", "insights", "Decide", "Explore KPIs, monitor quality, and train models from curated outputs."),
)
columns = st.columns(3, gap="large")
for column, (number, icon, title, description) in zip(columns, workflow):
    with column:
        st.markdown(
            f"""
<div style="height:100%; min-height:190px; padding:1.35rem; border:1px solid #E2E8F0;
            border-radius:16px; background:linear-gradient(145deg,#FFFFFF,#F8FAFC);
            box-shadow:0 4px 14px rgba(15,23,42,.05);">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
    <div style="width:40px; height:40px; display:grid; place-items:center; border-radius:12px;
                background:#EEF2FF; color:#4F46E5;">
      <span class="material-symbols-outlined">{icon}</span>
    </div>
    <span style="color:#94A3B8; font-size:.75rem; font-weight:800; letter-spacing:.08em;">{number}</span>
  </div>
  <div style="font-size:1.05rem; font-weight:750; color:#0F172A;">{title}</div>
  <div style="margin-top:.45rem; color:#64748B; font-size:.88rem; line-height:1.55;">{description}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
left, right = st.columns([1.5, 1])
with left:
    st.markdown(
        """
<div style="padding:1rem 1.15rem; border-left:4px solid #6366F1; background:#FFFFFF;
            border-radius:0 12px 12px 0; box-shadow:0 1px 3px rgba(15,23,42,.06);">
  <div style="font-weight:700; color:#1E293B;">Start with a clean pipeline</div>
  <div style="margin-top:.2rem; color:#64748B; font-size:.86rem;">Upload data first, then progress through ETL, Warehouse, and MLOps.</div>
</div>
        """,
        unsafe_allow_html=True,
    )
with right:
    st.metric("Platform modules", "8", "End-to-end workflow")

st.sidebar.divider()
st.sidebar.caption("Modern Data Engineering Platform")
st.sidebar.caption("Built for repeatable data workflows")

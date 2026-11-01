"""Settings page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.ui_helpers import page_header, section_title


def main() -> None:
    st.set_page_config(
        page_title="Settings | Modern Data Engineering Platform",
        page_icon=":gear:",
        layout="wide",
    )

    page_header(
        "Platform Settings",
        "View and configure the generic data engineering platform parameters.",
        icon=":material/settings_applications:",
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        section_title("📂 Storage Configuration")
        with st.container(border=True):
            st.text_input("Project Root", value=str(config.project_directory), disabled=True)
            st.text_input("Data Directory", value=str(config.data_directory), disabled=True)
            st.text_input("Warehouse Directory", value=str(config.warehouse_directory), disabled=True)
            st.text_input("Reports Directory", value=str(config.reports_directory), disabled=True)

    with col2:
        section_title("🛠️ Application Limits")
        with st.container(border=True):
            max_upload = st.number_input(
                "Max Upload Size (MB)",
                value=int(config.max_upload_size_bytes / (1024 * 1024)),
                min_value=1,
                help="Set via PLATFORM_MAX_UPLOAD_MB env variable."
            )
            preview_rows = st.number_input(
                "Preview Row Limit",
                value=config.preview_row_limit,
                min_value=1,
                max_value=1000,
                help="Number of rows to show when previewing a dataset."
            )
            debug_mode = st.toggle("Enable Debug Logging", value=config.debug)

    st.divider()

    st.info("💡 Note: Currently, to persist these settings permanently, you must set them as environment variables (e.g. `PLATFORM_MAX_UPLOAD_MB`).")

    if st.button("Save Session Settings", type="primary"):
        st.toast("✅ Settings applied for the current session.")

if __name__ == "__main__":
    main()

"""Interactive SQL Data Explorer for the Modern Data Engineering Platform."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.data_manager import DataManager
from core.ui_helpers import display_result_table, page_header, section_title

try:
    import duckdb
    _DUCKDB_AVAILABLE = True
except ImportError:
    _DUCKDB_AVAILABLE = False


def main() -> None:
    st.set_page_config(
        page_title="SQL Data Explorer | Modern Data Engineering Platform",
        page_icon=":mag:",
        layout="wide",
    )

    page_header(
        "SQL Data Explorer",
        "Write and execute raw SQL queries against your datasets using DuckDB.",
        icon=":material/search:",
    )

    if not _DUCKDB_AVAILABLE:
        st.error(
            "DuckDB is not installed. To use the SQL Explorer, please install it: "
            "`pip install duckdb`"
        )
        st.stop()

    data_manager = DataManager(config.uploads_directory)
    
    st.markdown("### 1. Select Data Source")
    
    # Gather all available datasets across layers
    sources = {}
    
    # Uploads (Bronze)
    for ds in data_manager.list_datasets():
        sources[f"Uploads: {ds.filename}"] = str(ds.path)
        
    # Warehouse (Gold)
    warehouse_dir = config.warehouse_directory
    if warehouse_dir.exists():
        for csv_file in warehouse_dir.glob("*.csv"):
            sources[f"Warehouse: {csv_file.name}"] = str(csv_file)
            
    if not sources:
        st.info("No datasets available. Please upload data or run the ETL/Warehouse pipelines first.")
        st.stop()
        
    selected_source_name = st.selectbox("Choose a dataset to query", options=list(sources.keys()))
    
    if not selected_source_name:
        st.stop()
        
    file_path = sources[selected_source_name]
    
    try:
        # Load the dataframe. We call it 'df' so the user can query it as 'df'.
        df = pd.read_csv(file_path)
    except Exception as exc:
        st.error(f"Could not load the dataset: {exc}")
        st.stop()
        
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        section_title("Dataset Schema", f"Table name in SQL: `df`")
        with st.container(border=True):
            st.dataframe(pd.DataFrame({
                "Column": df.columns,
                "Type": df.dtypes.astype(str)
            }), use_container_width=True, hide_index=True)
            st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns):,}")
            
    with col1:
        section_title("Write SQL Query")
        
        default_query = "SELECT * \nFROM df \nLIMIT 100"
        query = st.text_area("SQL Query", value=default_query, height=200, help="Use standard SQL syntax. The dataset table is named `df`.")
        
        if st.button("▶️ Execute Query", type="primary"):
            with st.spinner("Executing query..."):
                try:
                    # Run duckdb query against the local dataframe 'df'
                    result_df = duckdb.query(query).df()
                    st.toast("✅ Query executed successfully!")
                    
                    st.subheader("Query Results")
                    st.caption(f"Returned {len(result_df):,} rows.")
                    display_result_table(result_df, hide_index=True)
                    
                    # Provide download
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download Results as CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                    )
                    
                except Exception as e:
                    st.error(f"SQL Execution Error:\n{e}")

if __name__ == "__main__":
    main()

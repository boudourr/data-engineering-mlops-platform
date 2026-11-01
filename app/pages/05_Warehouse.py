"""Warehouse page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.run_context import get_current_run, update_run_status
from core.ui_helpers import (
    display_dataset_summary,
    display_result_table,
    display_schema,
    initialize_session_state,
    page_header,
    preview_dataset,
    section_title,
    show_execution_result,
)
from warehouse.warehouse_pipeline import WarehousePipeline
from warehouse.schema_inference import InferredSchema


def main() -> None:
    """Render the warehouse generation dashboard."""
    st.set_page_config(
        page_title="Warehouse | Modern Data Engineering Platform",
        page_icon=":package:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"warehouse_results": None, "inferred_schema": None})

    page_header(
        "Warehouse",
        "Dynamically infer and build the Gold layer from cleaned silver datasets.",
        icon=":material/warehouse:",
    )

    render_current_run()
    st.divider()
    render_schema_detection()
    st.divider()
    render_available_tables()


def render_schema_detection() -> None:
    """Render interactive schema detection and generation."""
    section_title(
        "Schema Inference",
        "Analyze Silver data from all runs and propose an analytical structure.",
    )

    run_context = get_current_run()
    if not run_context:
        st.warning("No dataset has been uploaded. Please upload a dataset and run ETL first.")
        return

    available_tables = discover_all_silver_tables()
    if not available_tables:
        st.info("No silver tables found. Please run ETL first.")
        return

    st.markdown("**Available Silver Tables:**")
    selected_tables = st.multiselect(
        "Select tables for schema inference",
        options=list(available_tables.keys()),
        default=list(available_tables.keys()),
        key="warehouse_selected_tables",
    )

    if not selected_tables:
        st.info("Select at least one table for schema inference.")
        return

    if st.button("Detect Schema", type="secondary"):
        with st.spinner("Analyzing relationships and detecting schema..."):
            try:
                pipeline = WarehousePipeline()
                schema = pipeline.infer_schema_from_tables(
                    {name: available_tables[name] for name in selected_tables}
                )
                st.session_state.inferred_schema = schema.to_dict()
                st.toast("✅ Schema detected successfully.")
            except Exception as e:
                st.error(f"Failed to detect schema: {e}")

    schema_dict = st.session_state.get("inferred_schema")
    if schema_dict:
        schema = InferredSchema.from_dict(schema_dict)
        st.subheader("Proposed Star Schema")
        
        st.markdown(f"**Fact Table:** `{schema.fact_table_name}` (Source: `{schema.fact_source_table}`)")
        
        st.markdown("**Measures:**")
        st.write(", ".join(schema.measures) if schema.measures else "None detected")
        
        st.markdown("**Dimensions:**")
        dim_data = [
            {
                "Dimension Name": d.name,
                "Source Table": d.source_table,
                "Primary Key": d.primary_key,
                "Is Date": "Yes" if d.is_date_dimension else "No"
            }
            for d in schema.dimensions
        ]
        display_result_table(dim_data)

        if st.button("Generate Data Warehouse", type="primary", use_container_width=True):
            with st.spinner("Building warehouse tables..."):
                result = run_warehouse_pipeline(schema)
            st.session_state.warehouse_results = result
            show_execution_result(result)

    results_payload = st.session_state.get("warehouse_results")
    if results_payload:
        st.caption(f"Last run: {results_payload.get('message', 'No message available')}")


def render_available_tables() -> None:
    """List generated warehouse tables and allow inspection of a selected file."""
    section_title("Generated Tables")

    tables = discover_warehouse_tables()
    if not tables:
        st.info("No warehouse tables have been generated yet. Build the warehouse to create the Gold layer.")
        return

    table_rows = [
        {
            "Name": table.name,
            "Path": str(table),
            "Size (bytes)": table.stat().st_size,
        }
        for table in tables
    ]
    display_result_table(table_rows)

    selected_table = st.selectbox(
        "Inspect warehouse table",
        options=[None, *tables],
        format_func=lambda table: "Select a table" if table is None else table.name,
        key="warehouse_selected_table",
    )

    if selected_table is None:
        return

    render_table_inspector(selected_table)


def render_table_inspector(table_path: Path) -> None:
    """Preview and summarize a generated warehouse table."""
    section_title(f"{table_path.name} Preview")

    try:
        with open(table_path, "rb") as f:
            st.download_button(
                label=f"⬇️ Download {table_path.name}",
                data=f,
                file_name=table_path.name,
                mime="text/csv",
            )
        dataframe = pd.read_csv(table_path)
    except Exception as exc:
        st.error(f"Could not read {table_path.name}: {exc}")
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


def run_warehouse_pipeline(schema: InferredSchema) -> dict[str, Any]:
    """Run the warehouse generation."""
    previous_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        pipeline = WarehousePipeline()
        result = pipeline.generate(schema)
    except Exception as exc:
        return {
            "status": "failed",
            "message": f"Warehouse generation failed: {exc}",
            "error": str(exc),
            "generated_tables": discover_warehouse_tables(),
        }
    finally:
        os.chdir(previous_cwd)

    tables = discover_warehouse_tables()
    result["generated_tables"] = tables
    if str(result.get("status", "")).lower() == "success":
        update_run_status("Warehouse", "success")
    return result


def discover_warehouse_tables() -> list[Path]:
    """Return CSV tables generated only for the active run."""
    run_context = get_current_run()
    if not run_context:
        return []
    gold_dir = Path(run_context.gold_dir)
    if not gold_dir.is_dir():
        return []
    return sorted((path.resolve() for path in gold_dir.glob("*.csv") if path.is_file()), key=lambda item: item.name)


def discover_all_silver_tables() -> dict[str, pd.DataFrame]:
    """Discover all silver tables from all runs and return as a dictionary."""
    run_context = get_current_run()
    if not run_context:
        return {}

    runs_base_dir = Path(run_context.silver_dir).parent.parent
    dataframes = {}
    parquet_stems = set()

    for run_dir in runs_base_dir.iterdir():
        if not run_dir.is_dir():
            continue
        silver_dir = run_dir / "silver"
        if not silver_dir.is_dir():
            continue
        for file in silver_dir.glob("*.parquet"):
            if file.stem not in dataframes:
                dataframes[file.stem] = pd.read_parquet(file)
                parquet_stems.add(file.stem)
        for file in silver_dir.glob("*.csv"):
            if file.stem in parquet_stems or file.stem in dataframes:
                continue
            try:
                dataframes[file.stem] = pd.read_csv(file)
            except Exception:
                continue

    return dataframes


def render_current_run() -> None:
    """Show the isolated dataset paths used by this warehouse run."""
    run_context = get_current_run()
    if not run_context:
        st.warning("No dataset has been uploaded. Please upload a dataset and run ETL first.")
        return

    display_result_table({
        "Current Dataset": run_context.dataset_name,
        "Run ID": run_context.run_id,
        "Silver Data": run_context.silver_dir,
        "Gold Output": run_context.gold_dir,
        "ETL Status": run_context.pipeline_status.get("ETL", "not started"),
    })


if __name__ == "__main__":
    main()

"""ETL page for the Generic Modern Data Engineering Platform."""

from __future__ import annotations

import ast
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.data_manager import DataManager, DatasetRecord
from core.run_context import create_run, save_run_manifest, set_current_run
from core.ui_helpers import (
    display_dataset_summary,
    display_result_table,
    display_schema,
    initialize_session_state,
    page_header,
    preview_dataset,
    section_title,
)
from etl.load import Loader
from etl.transformer import BaseTransformer
from etl.validator import DataValidator


def main() -> None:
    """Render the ETL workflow page."""
    st.set_page_config(
        page_title="ETL | Modern Data Engineering Platform",
        page_icon=":gear:",
        layout="wide",
    )

    config.create_directories()
    initialize_session_state({"etl_results": None})
    data_manager = DataManager(config.uploads_directory)

    page_header(
        "ETL",
        "Clean, validate, and transform uploaded datasets into a silver-layer output.",
        icon=":material/settings:",
    )

    render_dataset_selection(data_manager)
    st.divider()
    render_etl_controls(data_manager)
    st.divider()
    render_etl_results()


def render_dataset_selection(data_manager: DataManager) -> None:
    """Render the saved-dataset picker and input preview."""
    section_title(
        "Available Datasets",
        "Choose a saved dataset to validate and transform.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        st.info("No saved datasets are available yet. Upload datasets on the Data Upload page first.")
        return

    selected_dataset = st.selectbox(
        "Select a dataset",
        options=[None, *datasets],
        format_func=lambda dataset: "Select a dataset" if dataset is None else dataset.filename,
        key="etl_selected_dataset",
    )

    if selected_dataset is None:
        st.info("Select a dataset to inspect and transform.")
        return

    render_dataset_inspector(data_manager, selected_dataset)


def render_dataset_inspector(data_manager: DataManager, dataset: DatasetRecord) -> None:
    """Show input dataset metadata and a preview."""
    section_title("Input Dataset")
    display_result_table(asdict(dataset))

    dataframe, error = load_dataset_safely(data_manager, dataset)
    if error:
        st.warning(error)
        return

    display_dataset_summary(dataframe)
    preview_dataset(dataframe, rows=config.preview_row_limit)
    display_schema(dataframe)


def render_etl_controls(data_manager: DataManager) -> None:
    """Render ETL options and execute the transformation pipeline."""
    section_title(
        "ETL Controls",
        "Configure the validation and cleaning rules before writing a silver-layer output.",
    )

    datasets = data_manager.list_datasets()
    if not datasets:
        return

    selected_dataset = st.session_state.get("etl_selected_dataset")
    if selected_dataset is None:
        st.info("Choose a dataset before running ETL.")
        return

    # Streamlit preserves widget values between reruns. Reset the generated
    # table name when the selected dataset changes so one dataset can never be
    # written using a previous dataset's table name.
    if st.session_state.get("etl_output_dataset_id") != selected_dataset.dataset_id:
        st.session_state.etl_output_dataset_id = selected_dataset.dataset_id
        st.session_state.etl_output_name = selected_dataset.filename
        st.session_state.etl_batch_primary_id = selected_dataset.dataset_id
        st.session_state.etl_batch_datasets = [selected_dataset]

    if st.session_state.get("etl_batch_primary_id") != selected_dataset.dataset_id:
        st.session_state.etl_batch_primary_id = selected_dataset.dataset_id
        st.session_state.etl_batch_datasets = [selected_dataset]

    selected_datasets = st.multiselect(
        "Tables in this warehouse dataset",
        options=datasets,
        format_func=lambda dataset: dataset.filename,
        help="Select every uploaded table that belongs to this dataset. They will be cleaned into one isolated run and detected together by Warehouse.",
        key="etl_batch_datasets",
    )
    if not selected_datasets:
        st.info("Select at least one table to run ETL.")
        return

    output_name = st.text_input(
        "Output table name",
        key="etl_output_name",
    )
    primary_key_input = st.text_input(
        "Primary key (optional, comma-separated)",
        key="etl_primary_key",
    )
    required_columns_input = st.text_input(
        "Required columns (optional, comma-separated)",
        key="etl_required_columns",
    )
    date_columns_input = st.text_input(
        "Additional date columns (optional, comma-separated)",
        help="Date-like columns are detected automatically. Use this only when a column name does not indicate that it contains dates.",
        key="etl_date_columns",
    )
    fillna_input = st.text_input(
        "Fill missing values (optional, e.g. column=value;column2=0)",
        key="etl_fillna",
    )

    if st.button("Run ETL", type="primary", use_container_width=True):
        dataframe, error = load_dataset_safely(data_manager, selected_dataset)
        if error:
            st.error(error)
            return

        with st.spinner(f"Transforming {selected_dataset.filename}..."):
            try:
                st.session_state.etl_results = run_etl_batch(
                    data_manager=data_manager,
                    datasets=selected_datasets,
                    primary_dataset=selected_dataset,
                    primary_output_name=output_name,
                    primary_keys=[column.strip() for column in primary_key_input.split(",") if column.strip()],
                    required_columns=[column.strip() for column in required_columns_input.split(",") if column.strip()],
                    date_columns=[column.strip() for column in date_columns_input.split(",") if column.strip()],
                    fillna_strategy=parse_fillna_strategy(fillna_input),
                )
                st.toast("✅ ETL completed successfully.")
            except Exception as exc:
                st.session_state.etl_results = {
                    "dataset": asdict(selected_dataset),
                    "error": str(exc),
                }
                st.error(f"ETL failed: {exc}")


def run_etl_batch(
    data_manager: DataManager,
    datasets: list[DatasetRecord],
    primary_dataset: DatasetRecord,
    primary_output_name: str,
    primary_keys: list[str],
    required_columns: list[str],
    date_columns: list[str],
    fillna_strategy: dict[str, Any],
) -> dict[str, Any]:
    """Clean all tables selected for one dataset into a shared, isolated run."""
    if primary_dataset not in datasets:
        datasets = [primary_dataset, *datasets]

    run_label = primary_dataset.filename if len(datasets) == 1 else f"{primary_dataset.filename} + {len(datasets) - 1} tables"
    run_context = create_run(
        dataset_name=run_label,
        dataset_path=primary_dataset.path,
        dataset_id=primary_dataset.dataset_id,
    )
    loader = Loader(output_dir=run_context.get_dir("silver"))
    transformer = BaseTransformer()
    table_results = []
    primary_dataframe: Optional[pd.DataFrame] = None

    for dataset in datasets:
        dataframe, error = load_dataset_safely(data_manager, dataset)
        if error:
            raise ValueError(error)

        is_primary = dataset.dataset_id == primary_dataset.dataset_id
        table_name = primary_output_name if is_primary else dataset.filename
        table_name = sanitize_dataset_name(table_name)
        validator = DataValidator(
            dataframe=dataframe,
            table_name=table_name,
            primary_key=primary_keys if is_primary else [],
            required_columns=required_columns if is_primary else [],
        )
        validation_report = validator.validate()
        transformed_dataframe = transformer.transform(
            df=dataframe,
            dataset_name=table_name,
            datetime_columns=date_columns if is_primary else [],
            fillna_strategy=fillna_strategy if is_primary else {},
        )
        if is_primary:
            primary_dataframe = transformed_dataframe

        raw_path = run_context.get_dir("raw") / Path(dataset.path).name
        raw_path.write_bytes(Path(dataset.path).read_bytes())
        csv_path = loader.save_csv(transformed_dataframe, table_name)
        parquet_path = loader.save_parquet(transformed_dataframe, table_name)
        table_results.append({
            "dataset": asdict(dataset),
            "table": table_name,
            "validation_report": validation_report,
            "output_path": str(csv_path),
            "typed_output_path": str(parquet_path),
            "rows": len(transformed_dataframe),
            "columns": len(transformed_dataframe.columns),
        })

    run_context.pipeline_status["ETL"] = "success"
    set_current_run(run_context)
    save_run_manifest(run_context)
    primary_result = next(item for item in table_results if item["dataset"]["dataset_id"] == primary_dataset.dataset_id)
    return {
        **primary_result,
        "run_id": run_context.run_id,
        "dataset": asdict(primary_dataset),
        "output_dataframe": primary_dataframe,
        "tables": table_results,
    }


def render_etl_results() -> None:
    """Render the latest ETL result summary and preview."""
    section_title("ETL Results")

    results_payload = st.session_state.get("etl_results")
    if not results_payload:
        st.info("Run ETL to view validation, output path, and transformed data.")
        return

    if "error" in results_payload:
        st.error(results_payload["error"])
        return

    validation_report = results_payload.get("validation_report")
    output_dataframe = results_payload.get("output_dataframe")
    output_path = results_payload.get("output_path")
    typed_output_path = results_payload.get("typed_output_path")

    if validation_report:
        display_result_table(validation_report)
    else:
        st.info("No validation report was generated.")

    table_results = results_payload.get("tables", [])
    if table_results:
        st.subheader("Tables Included in This Run")
        display_result_table([
            {
                "Table": item["table"],
                "Rows": item["rows"],
                "Columns": item["columns"],
                "Silver CSV": item["output_path"],
            }
            for item in table_results
        ])

    if output_path:
        st.caption(f"Saved to: {output_path}")
        if typed_output_path:
            st.caption(f"Typed Silver data: {typed_output_path}")
        try:
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Silver Data (CSV)",
                    data=f,
                    file_name=Path(output_path).name,
                    mime="text/csv",
                )
        except Exception:
            pass

    if isinstance(output_dataframe, pd.DataFrame):
        st.subheader("Transformed Data Preview")
        preview_dataset(output_dataframe, rows=config.preview_row_limit)
        display_dataset_summary(output_dataframe)
        display_schema(output_dataframe)
    else:
        st.info("No transformed dataset is available to preview.")


def load_dataset_safely(
    data_manager: DataManager,
    dataset: DatasetRecord,
) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a saved dataset and return ``(dataframe, error_message)``."""
    try:
        return data_manager.load_dataset(dataset.dataset_id), None
    except Exception as exc:
        return None, f"Could not load the selected dataset: {exc}"


def parse_fillna_strategy(fillna_input: str) -> dict[str, Any]:
    """Parse a semicolon-separated ``column=value`` list into a fillna strategy."""
    strategy: dict[str, Any] = {}
    for chunk in fillna_input.split(";"):
        piece = chunk.strip()
        if not piece or "=" not in piece:
            continue
        column, value = piece.split("=", 1)
        column = column.strip()
        value_text = value.strip()
        if not column or not value_text:
            continue
        try:
            parsed_value = ast.literal_eval(value_text)
        except (ValueError, SyntaxError):
            parsed_value = value_text
        strategy[column] = parsed_value
    return strategy


def sanitize_dataset_name(value: str) -> str:
    """Create a safe, filesystem-friendly ETL table name."""
    sanitized = Path(str(value or "dataset")).stem.strip().lower()
    sanitized = "".join(character if character.isalnum() else "_" for character in sanitized)
    sanitized = sanitized.strip("_") or "dataset"
    return sanitized


if __name__ == "__main__":
    main()

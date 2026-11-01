"""Prepare one-click Power BI dashboard assets from uploaded datasets."""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = PROJECT_ROOT / "app"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.config import config
from core.data_manager import DataManager, DatasetRecord


DASHBOARDS_DIRECTORY = PROJECT_ROOT / "dashboards"
EXPORT_DIRECTORY = DASHBOARDS_DIRECTORY / "generated"
DATA_DIRECTORY = DASHBOARDS_DIRECTORY / "data"
LATEST_DATASET_PATH = DATA_DIRECTORY / "current_dataset.csv"
LATEST_MANIFEST_PATH = EXPORT_DIRECTORY / "latest_manifest.json"


def prepare_powerbi(dataset_id: Optional[str] = None) -> dict[str, Any]:
    """Generate a Power BI package for a selected or latest uploaded dataset."""
    try:
        from core.run_context import get_current_run
        run_context = get_current_run()
    except ImportError:
        run_context = None

    if run_context:
        dataset_path = Path(run_context.dataset_path)
        dataset_name = _safe_stem(dataset_path.stem)
        import pandas as pd
        dataframe = pd.read_csv(dataset_path)
        
        # Output to run context directories
        out_dir = Path(run_context.reports_dir)
        data_out_dir = out_dir / "data"
        export_out_dir = out_dir / "generated"
        dataset_source_path = str(dataset_path)
        dataset_filename = dataset_path.name
        ds_id = run_context.run_id
    else:
        data_manager = DataManager(config.uploads_directory)
        selected_dataset = _resolve_dataset(data_manager, dataset_id)
        dataframe = data_manager.load_dataset(selected_dataset.dataset_id)
        dataset_name = _safe_stem(Path(selected_dataset.filename).stem)
        
        out_dir = DASHBOARDS_DIRECTORY
        data_out_dir = DATA_DIRECTORY
        export_out_dir = EXPORT_DIRECTORY
        dataset_source_path = selected_dataset.path
        dataset_filename = selected_dataset.filename
        ds_id = selected_dataset.dataset_id

    data_out_dir.mkdir(parents=True, exist_ok=True)
    export_out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    dataset_export_path = data_out_dir / f"{dataset_name}_{timestamp}.csv"
    manifest_path = export_out_dir / f"{dataset_name}_{timestamp}.json"
    latest_dataset_path = data_out_dir / "current_dataset.csv"
    latest_manifest_path = export_out_dir / "latest_manifest.json"

    dataframe.to_csv(latest_dataset_path, index=False)
    dataframe.to_csv(dataset_export_path, index=False)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_id": ds_id,
        "dataset_filename": dataset_filename,
        "dataset_source_path": dataset_source_path,
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "latest_dataset_path": str(latest_dataset_path),
        "dataset_export_path": str(dataset_export_path),
        "dataset_columns": [str(column) for column in dataframe.columns],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    latest_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "message": "Power BI dashboard package was generated successfully without a static template.",
        "dataset_id": ds_id,
        "dataset_filename": dataset_filename,
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "dataset_export_path": str(dataset_export_path),
        "latest_dataset_path": str(latest_dataset_path),
        "manifest_path": str(manifest_path),
    }


def run_powerbi() -> dict[str, Any]:
    """Alias used by pipeline manager and legacy callers."""
    return prepare_powerbi()


def main() -> dict[str, Any]:
    """CLI-friendly entrypoint."""
    return prepare_powerbi()


def _resolve_dataset(data_manager: DataManager, dataset_id: Optional[str]) -> DatasetRecord:
    """Resolve the selected dataset or fall back to the latest uploaded dataset."""
    if dataset_id:
        return data_manager.get_dataset(dataset_id)

    datasets = data_manager.list_datasets()
    if not datasets:
        raise FileNotFoundError(
            "No uploaded datasets were found. Upload a dataset first from the Data Upload page."
        )
    return datasets[0]


def _safe_stem(value: str) -> str:
    """Create a filesystem-safe stem for generated output names."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return cleaned or "dataset"

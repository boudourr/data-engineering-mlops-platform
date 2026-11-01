"""
run_context.py
--------------

Centralized tracking of the current platform execution run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from core.config import config


@dataclass
class RunContext:
    run_id: str
    dataset_name: str
    dataset_path: str
    
    # Run specific directories
    raw_dir: str
    silver_dir: str
    gold_dir: str
    models_dir: str
    predictions_dir: str
    reports_dir: str
    powerbi_dir: str
    
    ml_target: Optional[str] = None
    pipeline_status: Dict[str, str] = None
    created_at: str = ""

    def __post_init__(self):
        if self.pipeline_status is None:
            self.pipeline_status = {}
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def get_dir(self, name: str) -> Path:
        """Helper to get a Path object for a specific directory."""
        return Path(getattr(self, f"{name}_dir"))


def create_run(dataset_name: str, dataset_path: str, dataset_id: str) -> RunContext:
    """Create a new run context."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{dataset_id[:8]}"
    
    base_dir = config.data_directory / "runs" / run_id
    
    context = RunContext(
        run_id=run_id,
        dataset_name=dataset_name,
        dataset_path=str(dataset_path),
        raw_dir=str(base_dir / "raw"),
        silver_dir=str(base_dir / "silver"),
        gold_dir=str(base_dir / "gold"),
        models_dir=str(config.project_directory / "models" / run_id),
        predictions_dir=str(config.project_directory / "predictions" / run_id),
        reports_dir=str(config.project_directory / "reports" / run_id),
        powerbi_dir=str(config.project_directory / "powerbi" / run_id),
    )
    
    # Create the directories
    for dir_name in ["raw_dir", "silver_dir", "gold_dir", "models_dir", "predictions_dir", "reports_dir", "powerbi_dir"]:
        path = context.get_dir(dir_name.replace("_dir", ""))
        path.mkdir(parents=True, exist_ok=True)
        
    return context


def get_current_run() -> Optional[RunContext]:
    """Retrieve the current run context from session state."""
    if "current_run_context" in st.session_state:
        context_data = st.session_state.current_run_context
        if isinstance(context_data, dict):
             return RunContext(**context_data)
        return context_data
    return None


def set_current_run(run_context: RunContext) -> None:
    """Set the current run context in session state."""
    st.session_state.current_run_context = asdict(run_context)


def clear_run() -> None:
    """Clear the current run from session state."""
    if "current_run_context" in st.session_state:
        del st.session_state.current_run_context


def update_run_status(stage: str, status: str) -> None:
    """Update the status of a pipeline stage in the current run."""
    run = get_current_run()
    if run:
        run.pipeline_status[stage] = status
        set_current_run(run)


def save_run_manifest(run_context: RunContext) -> None:
    """Save the run manifest to the reports directory."""
    manifest_path = run_context.get_dir("reports") / "run_manifest.json"
    manifest_path.write_text(json.dumps(asdict(run_context), indent=4), encoding="utf-8")

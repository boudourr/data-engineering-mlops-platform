"""Generic bridge between the Streamlit UI and backend pipeline services.

The manager intentionally avoids dataset-specific logic.  Each method first
looks for a compatible callable in known project modules.  When no backend is
available yet, it returns a clear warning instead of breaking the interface.
"""

from __future__ import annotations

from collections.abc import Mapping
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


PipelineResult = Dict[str, Any]


class PipelineManager:
    """Coordinate generic platform actions for the Streamlit interface."""

    DEFAULT_STATUS: Dict[str, str] = {
        "Profiling": "not_started",
        "ETL": "not_started",
        "Warehouse": "not_started",
        "MLOps": "not_started",
        "Monitoring": "not_started",
        "Reports": "not_started",
        "Power BI": "not_started",
    }

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2])
        self._status: Dict[str, Any] = dict(self.DEFAULT_STATUS)
        self._last_result: Optional[PipelineResult] = None

    def get_status(self) -> Dict[str, Any]:
        """Return the latest known status for every generic pipeline stage."""
        return dict(self._status)

    def overall_status(self) -> PipelineResult:
        """Return an overall health/status record for the platform."""
        values = {str(value).lower() for value in self._status.values()}
        if "failed" in values:
            status = "failed"
        elif "running" in values:
            status = "running"
        elif values and values.issubset({"success", "completed", "complete"}):
            status = "success"
        elif any(value in values for value in {"warning", "not_implemented"}):
            status = "warning"
        else:
            status = "not_started"

        return {
            "status": status,
            "message": "Platform status is derived from available pipeline stage results.",
            "updated_at": _utc_now(),
        }

    def run_all(self) -> PipelineResult:
        """Run all generic stages in lifecycle order."""
        results = {
            "profiling": self.run_profiling(),
            "etl": self.run_etl(),
            "warehouse": self.run_warehouse(),
            "mlops": self.run_mlops(),
            "monitoring": self.run_monitoring(),
            "reports": self.generate_reports(),
            "power_bi": self.prepare_powerbi(),
        }
        status = "failed" if any(_status_of(result) == "failed" for result in results.values()) else "success"
        return self._record_result(
            "Complete Platform",
            status,
            "Complete platform execution finished.",
            results=results,
        )

    def run(self) -> PipelineResult:
        """Alias for :meth:`run_all`."""
        return self.run_all()

    def run_profiling(self) -> PipelineResult:
        """Run or request dataset profiling."""
        return self._run_stage(
            "Profiling",
            [
                ("profiling.profile", ("run_profiling", "profile", "main")),
                ("src.profiling.profile", ("run_profiling", "profile", "main")),
            ],
        )

    def profile(self) -> PipelineResult:
        """Alias for :meth:`run_profiling`."""
        return self.run_profiling()

    def run_etl(self) -> PipelineResult:
        """Run or request the ETL/Silver pipeline."""
        return self._run_stage(
            "ETL",
            [
                ("etl.pipeline", ("run_etl", "run_etl_pipeline", "main")),
                ("src.etl.pipeline", ("run_etl", "run_etl_pipeline", "main")),
            ],
        )

    def run_etl_pipeline(self) -> PipelineResult:
        """Alias for :meth:`run_etl`."""
        return self.run_etl()

    def etl(self) -> PipelineResult:
        """Alias for :meth:`run_etl`."""
        return self.run_etl()

    def run_warehouse(self) -> PipelineResult:
        """Run or request the warehouse/Gold pipeline."""
        return self._run_stage(
            "Warehouse",
            [
                ("warehouse.pipeline", ("run_warehouse", "run_data_warehouse", "main")),
                ("src.warehouse.pipeline", ("run_warehouse", "run_data_warehouse", "main")),
            ],
        )

    def run_data_warehouse(self) -> PipelineResult:
        """Alias for :meth:`run_warehouse`."""
        return self.run_warehouse()

    def warehouse(self) -> PipelineResult:
        """Alias for :meth:`run_warehouse`."""
        return self.run_warehouse()

    def run_mlops(self) -> PipelineResult:
        """Run or request the MLOps workflow."""
        return self._run_stage(
            "MLOps",
            [
                ("mlops.pipeline", ("run_mlops", "main")),
                ("src.mlops.pipeline", ("run_mlops", "main")),
            ],
        )

    def mlops(self) -> PipelineResult:
        """Alias for :meth:`run_mlops`."""
        return self.run_mlops()

    def run_monitoring(self) -> PipelineResult:
        """Run or request platform monitoring."""
        return self._run_stage(
            "Monitoring",
            [
                ("monitoring.pipeline", ("run_monitoring", "monitor", "main")),
                ("src.monitoring.pipeline", ("run_monitoring", "monitor", "main")),
            ],
        )

    def monitor(self) -> PipelineResult:
        """Alias for :meth:`run_monitoring`."""
        return self.run_monitoring()

    def monitoring(self) -> PipelineResult:
        """Alias for :meth:`run_monitoring`."""
        return self.run_monitoring()

    def generate_reports(self) -> PipelineResult:
        """Run or request report generation."""
        return self._run_stage(
            "Reports",
            [
                ("reports.generator", ("generate_reports", "run_reports", "main")),
                ("src.reports.generator", ("generate_reports", "run_reports", "main")),
            ],
        )

    def run_reports(self) -> PipelineResult:
        """Alias for :meth:`generate_reports`."""
        return self.generate_reports()

    def reports(self) -> PipelineResult:
        """Alias for :meth:`generate_reports`."""
        return self.generate_reports()

    def prepare_powerbi(self) -> PipelineResult:
        """Run or request Power BI data preparation."""
        return self._run_stage(
            "Power BI",
            [
                ("powerbi.prepare", ("prepare_powerbi", "run_powerbi", "main")),
                ("src.powerbi.prepare", ("prepare_powerbi", "run_powerbi", "main")),
            ],
        )

    def run_powerbi(self) -> PipelineResult:
        """Alias for :meth:`prepare_powerbi`."""
        return self.prepare_powerbi()

    def powerbi(self) -> PipelineResult:
        """Alias for :meth:`prepare_powerbi`."""
        return self.prepare_powerbi()

    def _run_stage(self, stage: str, candidates: Iterable[Tuple[str, Iterable[str]]]) -> PipelineResult:
        """Run the first importable backend function for a stage."""
        self._status[stage] = "running"
        callable_result = self._find_callable(candidates)
        if callable_result is None:
            self._status[stage] = "warning"
            return self._record_result(
                stage,
                "warning",
                f"{stage} backend is not implemented yet.",
            )

        module_name, function_name, function = callable_result
        try:
            result = function()
        except Exception as exc:
            self._status[stage] = "failed"
            return self._record_result(
                stage,
                "failed",
                f"{stage} failed while calling {module_name}.{function_name}.",
                error=str(exc),
            )

        self._status[stage] = "success"
        if isinstance(result, dict):
            merged = {
                "stage": stage,
                "status": result.get("status", "success"),
                "message": result.get("message", f"{stage} completed successfully."),
                "called": f"{module_name}.{function_name}",
                "updated_at": _utc_now(),
            }
            merged.update({key: value for key, value in result.items() if key not in merged})
            self._last_result = merged
            return merged

        return self._record_result(
            stage,
            "success",
            f"{stage} completed successfully.",
            called=f"{module_name}.{function_name}",
            result=result,
        )

    def _find_callable(
        self,
        candidates: Iterable[Tuple[str, Iterable[str]]],
    ) -> Optional[Tuple[str, str, Callable[..., Any]]]:
        """Find the first available callable from module/function candidates."""
        for module_name, function_names in candidates:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue

            for function_name in function_names:
                function = getattr(module, function_name, None)
                if callable(function):
                    return module_name, function_name, function
        return None

    def _record_result(self, stage: str, status: str, message: str, **details: Any) -> PipelineResult:
        """Store and return a normalized pipeline result."""
        result: PipelineResult = {
            "stage": stage,
            "status": status,
            "message": message,
            "updated_at": _utc_now(),
        }
        result.update(details)
        self._last_result = result
        return result


def _status_of(result: Mapping[str, Any]) -> str:
    """Extract a normalized status string from a result mapping."""
    return str(result.get("status", "unknown")).strip().lower()


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


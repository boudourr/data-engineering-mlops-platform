"""Central configuration for the Modern Data Engineering Platform.

Configuration is intentionally domain-neutral. Environment variables can alter
locations and limits without requiring changes to pages or pipeline code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


APP_DIRECTORY = Path(__file__).resolve().parents[1]
PROJECT_DIRECTORY = APP_DIRECTORY.parent


def _path_from_environment(variable: str, default: Path) -> Path:
    """Return an absolute path from an environment variable or a default."""
    configured = os.getenv(variable)
    return Path(configured).expanduser().resolve() if configured else default.resolve()


def _integer_from_environment(variable: str, default: int, minimum: int = 0) -> int:
    """Read a bounded integer environment variable, falling back safely."""
    try:
        value = int(os.getenv(variable, str(default)))
        return max(minimum, value)
    except ValueError:
        return default


def _boolean_from_environment(variable: str, default: bool = False) -> bool:
    """Read a conventional boolean environment variable."""
    value = os.getenv(variable)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PlatformConfig:
    """Resolved application settings and filesystem locations."""

    project_directory: Path
    app_directory: Path
    data_directory: Path
    uploads_directory: Path
    processed_directory: Path
    warehouse_directory: Path
    reports_directory: Path
    logs_directory: Path
    max_upload_size_bytes: int
    preview_row_limit: int
    debug: bool

    def create_directories(self) -> None:
        """Create writable runtime directories when the application starts."""
        for directory in (
            self.data_directory,
            self.uploads_directory,
            self.processed_directory,
            self.warehouse_directory,
            self.reports_directory,
            self.logs_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def paths(self) -> Dict[str, Path]:
        """Expose named runtime paths for callers that prefer a mapping."""
        return {
            "project": self.project_directory,
            "app": self.app_directory,
            "data": self.data_directory,
            "uploads": self.uploads_directory,
            "processed": self.processed_directory,
            "warehouse": self.warehouse_directory,
            "reports": self.reports_directory,
            "logs": self.logs_directory,
        }


def load_config() -> PlatformConfig:
    """Build a configuration instance from environment variables and defaults.

    Supported variables are ``PLATFORM_DATA_DIR``, ``PLATFORM_UPLOADS_DIR``,
    ``PLATFORM_PROCESSED_DIR``, ``PLATFORM_WAREHOUSE_DIR``,
    ``PLATFORM_REPORTS_DIR``, ``PLATFORM_LOGS_DIR``, ``PLATFORM_MAX_UPLOAD_MB``,
    ``PLATFORM_PREVIEW_ROWS``, and ``PLATFORM_DEBUG``.
    """
    data_directory = _path_from_environment("PLATFORM_DATA_DIR", PROJECT_DIRECTORY / "data")
    max_upload_megabytes = _integer_from_environment("PLATFORM_MAX_UPLOAD_MB", 200, minimum=1)
    return PlatformConfig(
        project_directory=PROJECT_DIRECTORY.resolve(),
        app_directory=APP_DIRECTORY.resolve(),
        data_directory=data_directory,
        uploads_directory=_path_from_environment("PLATFORM_UPLOADS_DIR", data_directory / "uploads"),
        processed_directory=_path_from_environment("PLATFORM_PROCESSED_DIR", data_directory / "processed"),
        warehouse_directory=_path_from_environment("PLATFORM_WAREHOUSE_DIR", data_directory / "warehouse"),
        reports_directory=_path_from_environment("PLATFORM_REPORTS_DIR", PROJECT_DIRECTORY / "reports"),
        logs_directory=_path_from_environment("PLATFORM_LOGS_DIR", PROJECT_DIRECTORY / "logs"),
        max_upload_size_bytes=max_upload_megabytes * 1024 * 1024,
        preview_row_limit=_integer_from_environment("PLATFORM_PREVIEW_ROWS", 10, minimum=1),
        debug=_boolean_from_environment("PLATFORM_DEBUG"),
    )


config = load_config()


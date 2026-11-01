"""Generic dataset storage, validation, and loading utilities.

``DataManager`` is intentionally independent of any particular business domain.
It stores uploaded files locally, generates safe identifiers, and exposes a
small API suitable for Streamlit pages and pipeline services.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Mapping, Optional, Tuple, Union

import pandas as pd


PathLike = Union[str, Path]


@dataclass(frozen=True)
class DatasetRecord:
    """Serializable metadata for one stored dataset."""

    dataset_id: str
    filename: str
    path: str
    extension: str
    size_bytes: int
    uploaded_at: str


class DataManager:
    """Manage locally stored, user-provided datasets.

    Parameters
    ----------
    storage_dir:
        Directory used for uploaded dataset files and their metadata.  It is
        created when the manager is initialized.
    """

    SUPPORTED_EXTENSIONS = {".csv", ".json", ".parquet", ".xlsx", ".xls"}

    def __init__(self, storage_dir: PathLike = "data/uploads") -> None:
        self.storage_dir = Path(storage_dir).expanduser().resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.storage_dir / "datasets.json"

    def validate_file(self, filename: str, size_bytes: Optional[int] = None,
                      max_size_bytes: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validate a filename and optional file size before it is stored."""
        clean_name = Path(filename or "").name
        if not clean_name or clean_name in {".", ".."}:
            return False, "A valid file name is required."
        if Path(clean_name).suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            formats = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            return False, f"Unsupported file type. Supported types: {formats}."
        if size_bytes is not None and size_bytes <= 0:
            return False, "The selected file is empty."
        if max_size_bytes is not None and size_bytes is not None and size_bytes > max_size_bytes:
            return False, f"The selected file exceeds the {max_size_bytes:,}-byte limit."
        return True, None

    def save_uploaded_file(self, uploaded_file: Any, *, filename: Optional[str] = None,
                           max_size_bytes: Optional[int] = None) -> DatasetRecord:
        """Persist an uploaded file and return its generated dataset record.

        The object may be a Streamlit ``UploadedFile`` or any binary file-like
        object with a ``read`` method. Existing files are never overwritten.
        """
        source_name = filename or getattr(uploaded_file, "name", "")
        content = self._read_upload_bytes(uploaded_file)
        valid, error = self.validate_file(source_name, len(content), max_size_bytes)
        if not valid:
            raise ValueError(error)

        safe_name = self._safe_filename(source_name)
        dataset_id = self._make_dataset_id(safe_name, content)
        destination = self.storage_dir / f"{dataset_id}{Path(safe_name).suffix.lower()}"
        destination.write_bytes(content)
        record = DatasetRecord(
            dataset_id=dataset_id,
            filename=safe_name,
            path=str(destination),
            extension=destination.suffix.lower(),
            size_bytes=len(content),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        records = self._load_metadata()
        records[dataset_id] = asdict(record)
        self._save_metadata(records)
        return record

    def list_datasets(self) -> List[DatasetRecord]:
        """Return all known datasets, newest upload first."""
        records = [self._record_from_dict(item) for item in self._load_metadata().values()]
        return sorted(records, key=lambda item: item.uploaded_at, reverse=True)

    def get_dataset(self, dataset_id: str) -> DatasetRecord:
        """Return metadata for a dataset identifier or raise ``KeyError``."""
        record = self._load_metadata().get(dataset_id)
        if record is None:
            raise KeyError(f"Dataset '{dataset_id}' was not found.")
        return self._record_from_dict(record)

    def get_dataset_path(self, dataset_id: str) -> Path:
        """Return the validated local path for a stored dataset."""
        path = Path(self.get_dataset(dataset_id).path).resolve()
        if self.storage_dir not in path.parents or not path.is_file():
            raise FileNotFoundError(f"The stored file for dataset '{dataset_id}' is unavailable.")
        return path

    def load_dataset(self, dataset: Union[str, PathLike], **read_options: Any) -> pd.DataFrame:
        """Load a stored dataset ID or an explicit supported path into a DataFrame."""
        path = self.get_dataset_path(dataset) if isinstance(dataset, str) and dataset in self._load_metadata() else Path(dataset).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file was not found: {path}")
        extension = path.suffix.lower()
        if extension == ".csv":
            return pd.read_csv(path, **read_options)
        if extension == ".json":
            return pd.read_json(path, **read_options)
        if extension == ".parquet":
            return pd.read_parquet(path, **read_options)
        if extension in {".xlsx", ".xls"}:
            return pd.read_excel(path, **read_options)
        raise ValueError(f"Unsupported dataset type: {extension}")

    def dataset_summary(self, dataset: Union[str, PathLike], **read_options: Any) -> Dict[str, Any]:
        """Return generic dimensions and data-quality counts for a dataset."""
        dataframe = self.load_dataset(dataset, **read_options)
        return {
            "rows": int(len(dataframe)),
            "columns": int(len(dataframe.columns)),
            "missing_values": int(dataframe.isna().sum().sum()),
            "duplicate_rows": int(dataframe.duplicated().sum()),
            "memory_bytes": int(dataframe.memory_usage(deep=True).sum()),
        }

    def remove_dataset(self, dataset_id: str) -> bool:
        """Remove a stored dataset and its metadata. Returns whether it existed."""
        records = self._load_metadata()
        raw_record = records.pop(dataset_id, None)
        if raw_record is None:
            return False
        path = Path(raw_record["path"]).resolve()
        if self.storage_dir in path.parents and path.is_file():
            path.unlink()
        self._save_metadata(records)
        return True

    @staticmethod
    def _read_upload_bytes(uploaded_file: Any) -> bytes:
        """Read binary upload content while restoring the stream position when possible."""
        if uploaded_file is None or not hasattr(uploaded_file, "read"):
            raise ValueError("Please provide a readable uploaded file.")
        position: Optional[int] = None
        try:
            if hasattr(uploaded_file, "tell"):
                position = uploaded_file.tell()
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            content = uploaded_file.read()
        finally:
            if position is not None and hasattr(uploaded_file, "seek"):
                uploaded_file.seek(position)
        if isinstance(content, str):
            return content.encode("utf-8")
        if not isinstance(content, bytes):
            raise ValueError("Uploaded file content must be bytes or text.")
        return content

    @staticmethod
    def _safe_filename(filename: str) -> str:
        """Return a portable filename with no directory components."""
        candidate = Path(filename).name.strip()
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(candidate).stem).strip("._") or "dataset"
        extension = re.sub(r"[^A-Za-z0-9.]", "", Path(candidate).suffix).lower()
        return f"{stem}{extension}"

    @staticmethod
    def _make_dataset_id(filename: str, content: bytes) -> str:
        """Generate a readable, collision-resistant identifier from file content."""
        stem = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-") or "dataset"
        digest = hashlib.sha256(content).hexdigest()[:12]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{stem}-{timestamp}-{digest}"

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load metadata defensively; an unreadable registry behaves as empty."""
        if not self.metadata_path.is_file():
            return {}
        try:
            payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_metadata(self, records: Mapping[str, Mapping[str, Any]]) -> None:
        """Write metadata atomically to reduce the chance of a partial registry."""
        temporary_path = self.metadata_path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        temporary_path.replace(self.metadata_path)

    @staticmethod
    def _record_from_dict(record: Mapping[str, Any]) -> DatasetRecord:
        """Create a ``DatasetRecord`` from persisted metadata."""
        return DatasetRecord(
            dataset_id=str(record["dataset_id"]),
            filename=str(record["filename"]),
            path=str(record["path"]),
            extension=str(record["extension"]),
            size_bytes=int(record["size_bytes"]),
            uploaded_at=str(record["uploaded_at"]),
        )

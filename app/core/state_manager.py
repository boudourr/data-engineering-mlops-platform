"""
state_manager.py
----------------

Centralized, generic application-state management for the Streamlit
Modern Data Engineering Platform.

This module is dataset-independent and can be used by all Streamlit pages.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional


class StateManager:
    """
    Manage platform state in a mapping, normally ``st.session_state``.

    A custom mapping can be supplied for testing or non-Streamlit callers.
    """

    DEFAULTS: Dict[str, Any] = {
        "uploaded_files": [],
        "pipeline_status": {},
        "current_dataset": None,
        "execution_results": {},
        "health_status": "unknown",
    }

    def __init__(
        self,
        state: Optional[MutableMapping[str, Any]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
    ) -> None:

        if state is None:
            try:
                import streamlit as st
            except ImportError as exc:
                raise RuntimeError(
                    "Provide a state mapping when Streamlit is unavailable."
                ) from exc

            state = st.session_state

        self._state = state

        self._defaults = deepcopy(self.DEFAULTS)

        if defaults:
            self._defaults.update(deepcopy(dict(defaults)))

        self.initialize()

    # ==========================================================
    # Initialization
    # ==========================================================

    def initialize(self) -> None:
        """Create missing managed keys without replacing existing values."""

        for key, value in self._defaults.items():

            if key not in self._state:
                self._state[key] = deepcopy(value)

    # ==========================================================
    # Generic State Access
    # ==========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a state value."""

        return self._state.get(key, default)

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Store a state value."""

        if not key or not isinstance(key, str):
            raise ValueError(
                "State keys must be non-empty strings."
            )

        self._state[key] = value

    def snapshot(
        self,
        keys: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return a defensive copy of the managed state.
        """

        selected = (
            keys
            if keys is not None
            else self._defaults.keys()
        )

        return {
            key: deepcopy(self._state[key])
            for key in selected
            if key in self._state
        }

    # ==========================================================
    # Dataset Management
    # ==========================================================

    def set_current_dataset(
        self,
        dataset: Any,
    ) -> None:
        """Set the currently selected dataset."""

        self._state["current_dataset"] = dataset

    def get_current_dataset(self) -> Any:
        """Return the currently selected dataset."""

        return self._state.get(
            "current_dataset"
        )

    # ==========================================================
    # Uploaded Files
    # ==========================================================

    def add_uploaded_file(
        self,
        file_info: Any,
    ) -> None:
        """
        Add uploaded-file metadata.

        Duplicate entries are ignored.
        """

        files = list(
            self._state.get(
                "uploaded_files",
                [],
            )
        )

        if file_info not in files:
            files.append(file_info)

        self._state["uploaded_files"] = files

    def remove_uploaded_file(
        self,
        file_info: Any,
    ) -> bool:
        """
        Remove uploaded-file metadata.

        Returns True when the file existed.
        """

        files = list(
            self._state.get(
                "uploaded_files",
                [],
            )
        )

        try:
            files.remove(file_info)

        except ValueError:
            return False

        self._state["uploaded_files"] = files

        return True

    def get_uploaded_files(self) -> list:
        """Return all uploaded-file metadata."""

        return deepcopy(
            self._state.get(
                "uploaded_files",
                [],
            )
        )

    # ==========================================================
    # Pipeline Status
    # ==========================================================

    def update_pipeline_status(
        self,
        stage: str,
        status: Any,
        **details: Any,
    ) -> Dict[str, Any]:
        """
        Record the status of a pipeline stage.

        Example stages:

        - upload
        - profiling
        - etl
        - silver
        - warehouse
        - gold
        - power_bi
        - mlops
        - monitoring
        """

        if not stage or not stage.strip():
            raise ValueError(
                "A pipeline stage name is required."
            )

        statuses = dict(
            self._state.get(
                "pipeline_status",
                {},
            )
        )

        entry: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        entry.update(details)

        statuses[stage.strip()] = entry

        self._state["pipeline_status"] = statuses

        return deepcopy(entry)

    def get_pipeline_status(
        self,
        stage: Optional[str] = None,
    ) -> Any:
        """Return one stage or all pipeline statuses."""

        statuses = self._state.get(
            "pipeline_status",
            {},
        )

        if stage is not None:
            return deepcopy(
                statuses.get(stage)
            )

        return deepcopy(statuses)

    # ==========================================================
    # Overall Health
    # ==========================================================

    def set_health_status(
        self,
        status: Any,
        message: Optional[str] = None,
        **details: Any,
    ) -> Dict[str, Any]:
        """
        Set the overall platform health.

        Typical values:

        - HEALTHY
        - WARNING
        - FAILED
        """

        health: Dict[str, Any] = {
            "status": status,
            "message": message,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        health.update(details)

        self._state["health_status"] = health

        return deepcopy(health)

    def get_health_status(self) -> Any:
        """Return the current platform health."""

        return deepcopy(
            self._state.get(
                "health_status",
                "unknown",
            )
        )

    # ==========================================================
    # Execution Results
    # ==========================================================

    def record_execution(
        self,
        name: str,
        result: Any,
    ) -> Dict[str, Any]:
        """
        Store an execution result.

        Example:

        record_execution(
            "etl",
            {
                "status": "SUCCESS",
                "rows": 99441
            }
        )
        """

        if not name or not name.strip():
            raise ValueError(
                "An execution name is required."
            )

        results = dict(
            self._state.get(
                "execution_results",
                {},
            )
        )

        record = {
            "result": result,
            "recorded_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        results[name.strip()] = record

        self._state["execution_results"] = results

        return deepcopy(record)

    def get_execution_result(
        self,
        name: Optional[str] = None,
    ) -> Any:
        """Return one execution result or all results."""

        results = self._state.get(
            "execution_results",
            {},
        )

        if name is not None:
            return deepcopy(
                results.get(name)
            )

        return deepcopy(results)

    # ==========================================================
    # Reset
    # ==========================================================

    def clear_managed_state(self) -> None:
        """
        Reset only the state owned by this manager.

        Other Streamlit session-state variables remain untouched.
        """

        for key, value in self._defaults.items():
            self._state[key] = deepcopy(value)
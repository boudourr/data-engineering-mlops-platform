"""
bi_generator.py
---------------

Generic BI / dashboard intelligence engine.

This module analyses ANY pandas DataFrame and determines:
- Column types (numerical, categorical, datetime, boolean, identifier)
- Dataset quality statistics
- Categorised KPI candidates
- Chart candidates tagged by section

No dataset-specific business logic is used anywhere in this module.
Olist is supported only as a test dataset through the same generic path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DatasetProfile:
    """Detected structure and quality metrics of a dataset."""

    rows: int
    columns: int

    numerical: List[str] = field(default_factory=list)
    categorical: List[str] = field(default_factory=list)
    datetime: List[str] = field(default_factory=list)
    boolean: List[str] = field(default_factory=list)
    identifier: List[str] = field(default_factory=list)

    missing_values: int = 0
    missing_pct: float = 0.0
    duplicate_rows: int = 0
    memory_bytes: int = 0


@dataclass
class SourceTier:
    """One tier of available datasets (Gold, Silver, Uploads)."""

    label: str          # e.g. "Gold Layer"
    priority: int       # lower = prefer
    datasets: List[Path] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────

class BIGenerator:
    """
    Generic BI generator — completely independent of any dataset domain.

    Parameters
    ----------
    dataframe:
        Any pandas DataFrame.
    dataset_name:
        Human-readable name shown in the dashboard header.
    """

    # Maximum number of charts in any one section to avoid overwhelming UI
    MAX_CHARTS_PER_SECTION = 4
    # Categorical columns with more unique values than this are skipped for bar/pie
    HIGH_CARDINALITY_THRESHOLD = 50
    # Pie charts only when cardinality is at or below this
    PIE_MAX_CARDINALITY = 8

    def __init__(
        self,
        dataframe: pd.DataFrame,
        dataset_name: str = "Dataset",
    ) -> None:
        if dataframe is None:
            raise ValueError("dataframe cannot be None.")
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame.")

        self.df = dataframe.copy()
        self.dataset_name = str(dataset_name or "Dataset")
        self.profile = self._profile_dataset()

    # ─────────────────────────────────────────────────────────────────────────
    # Dataset profiling
    # ─────────────────────────────────────────────────────────────────────────

    def _profile_dataset(self) -> DatasetProfile:
        """Classify every column by its semantic type."""

        numerical: List[str] = []
        categorical: List[str] = []
        datetime_cols: List[str] = []
        boolean: List[str] = []
        identifier: List[str] = []

        for col in self.df.columns:
            series = self.df[col]

            if pd.api.types.is_bool_dtype(series):
                boolean.append(col)
                continue

            if pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
                continue

            if pd.api.types.is_numeric_dtype(series):
                if self._is_identifier(col, series):
                    identifier.append(col)
                else:
                    numerical.append(col)
                continue

            # Object / string columns — try datetime detection first
            if self._looks_like_datetime(series, col):
                datetime_cols.append(col)
                continue

            categorical.append(col)

        total_cells = self.df.size
        missing = int(self.df.isna().sum().sum())

        return DatasetProfile(
            rows=len(self.df),
            columns=len(self.df.columns),
            numerical=numerical,
            categorical=categorical,
            datetime=datetime_cols,
            boolean=boolean,
            identifier=identifier,
            missing_values=missing,
            missing_pct=round(missing / total_cells * 100, 2) if total_cells else 0.0,
            duplicate_rows=int(self.df.duplicated().sum()),
            memory_bytes=int(self.df.memory_usage(deep=True).sum()),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Type-detection helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_identifier(col: str, series: pd.Series) -> bool:
        """Return True when a numeric column is more likely an ID than a measure."""
        name = str(col).lower()
        id_keywords = {"id", "identifier", "code", "key", "uuid", "num", "no", "index", "seq"}
        if any(kw in name for kw in id_keywords):
            return True
        if len(series) > 0:
            unique_ratio = series.nunique(dropna=True) / len(series)
            if unique_ratio > 0.95 and series.nunique(dropna=True) > 20:
                return True
        return False

    @staticmethod
    def _looks_like_datetime(series: pd.Series, col: str) -> bool:
        """Heuristic: try to parse an object column as datetime."""
        name = str(col).lower()
        date_keywords = {
            "date", "time", "timestamp", "created", "updated",
            "year", "month", "day", "dt", "at",
        }
        if not any(kw in name for kw in date_keywords):
            return False
        try:
            converted = pd.to_datetime(series, errors="coerce")
            return converted.notna().mean() >= 0.70
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Return a flat dict of dataset overview statistics."""
        p = self.profile
        return {
            "dataset_name": self.dataset_name,
            "rows": p.rows,
            "columns": p.columns,
            "numerical_columns": len(p.numerical),
            "categorical_columns": len(p.categorical),
            "datetime_columns": len(p.datetime),
            "boolean_columns": len(p.boolean),
            "identifier_columns": len(p.identifier),
            "missing_values": p.missing_values,
            "missing_pct": p.missing_pct,
            "duplicate_rows": p.duplicate_rows,
            "memory_bytes": p.memory_bytes,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # KPI generation
    # ─────────────────────────────────────────────────────────────────────────

    def generate_kpis(self) -> List[Dict[str, Any]]:
        """
        Produce a list of KPI dicts from the detected column types.

        Each KPI dict contains:
            title    – display label
            value    – raw value
            format   – 'integer' | 'decimal' | 'percent' | 'text' | 'date'
            category – 'dataset' | 'numerical' | 'categorical' | 'temporal'
            icon     – emoji prefix
            subtitle – optional context string
        """
        kpis: List[Dict[str, Any]] = []

        # ── Dataset-level KPIs ─────────────────────────────────────────────
        kpis += self._dataset_kpis()

        # ── Numerical KPIs ─────────────────────────────────────────────────
        kpis += self._numerical_kpis()

        # ── Categorical KPIs ───────────────────────────────────────────────
        kpis += self._categorical_kpis()

        # ── Temporal KPIs ──────────────────────────────────────────────────
        kpis += self._temporal_kpis()

        return kpis

    def _dataset_kpis(self) -> List[Dict[str, Any]]:
        p = self.profile
        return [
            {
                "title": "Total Rows",
                "value": p.rows,
                "format": "integer",
                "category": "dataset",
                "icon": "📋",
                "subtitle": "Records in dataset",
            },
            {
                "title": "Total Columns",
                "value": p.columns,
                "format": "integer",
                "category": "dataset",
                "icon": "📐",
                "subtitle": f"{len(p.numerical)} numerical, {len(p.categorical)} categorical",
            },
            {
                "title": "Missing Values",
                "value": p.missing_values,
                "format": "integer",
                "category": "dataset",
                "icon": "⚠️",
                "subtitle": f"{p.missing_pct:.1f}% of all cells",
            },
            {
                "title": "Duplicate Rows",
                "value": p.duplicate_rows,
                "format": "integer",
                "category": "dataset",
                "icon": "🔁",
                "subtitle": "Exact-match duplicates",
            },
        ]

    def _numerical_kpis(self) -> List[Dict[str, Any]]:
        """Generate Sum / Mean / Min / Max / Median for the top numerical columns."""
        kpis: List[Dict[str, Any]] = []
        for col in self.profile.numerical[:4]:   # cap at 4 columns
            series = pd.to_numeric(self.df[col], errors="coerce").dropna()
            if series.empty:
                continue
            col_label = _label(col)
            kpis += [
                {
                    "title": f"Sum of {col_label}",
                    "value": float(series.sum()),
                    "format": "decimal",
                    "category": "numerical",
                    "icon": "∑",
                    "subtitle": col_label,
                },
                {
                    "title": f"Average {col_label}",
                    "value": float(series.mean()),
                    "format": "decimal",
                    "category": "numerical",
                    "icon": "〜",
                    "subtitle": f"Min {series.min():,.2f} · Max {series.max():,.2f}",
                },
            ]
        return kpis

    def _categorical_kpis(self) -> List[Dict[str, Any]]:
        """Generate unique count + top value for the first categorical columns."""
        kpis: List[Dict[str, Any]] = []
        for col in self.profile.categorical[:3]:
            series = self.df[col].dropna().astype(str)
            if series.empty:
                continue
            col_label = _label(col)
            n_unique = series.nunique()
            top_val = series.mode().iloc[0] if not series.mode().empty else "—"
            kpis += [
                {
                    "title": f"Unique {col_label}",
                    "value": n_unique,
                    "format": "integer",
                    "category": "categorical",
                    "icon": "🏷️",
                    "subtitle": f"Top: {str(top_val)[:30]}",
                },
            ]
        return kpis

    def _temporal_kpis(self) -> List[Dict[str, Any]]:
        """Generate date-range KPIs for the first datetime column."""
        kpis: List[Dict[str, Any]] = []
        for col in self.profile.datetime[:2]:
            series = pd.to_datetime(self.df[col], errors="coerce").dropna()
            if series.empty:
                continue
            col_label = _label(col)
            kpis += [
                {
                    "title": f"Earliest {col_label}",
                    "value": str(series.min().date()),
                    "format": "text",
                    "category": "temporal",
                    "icon": "📅",
                    "subtitle": col_label,
                },
                {
                    "title": f"Latest {col_label}",
                    "value": str(series.max().date()),
                    "format": "text",
                    "category": "temporal",
                    "icon": "📅",
                    "subtitle": f"Span: {(series.max() - series.min()).days} days",
                },
            ]
        return kpis

    # ─────────────────────────────────────────────────────────────────────────
    # Chart recommendations
    # ─────────────────────────────────────────────────────────────────────────

    def generate_chart_recommendations(self) -> List[Dict[str, Any]]:
        """
        Build a list of chart specification dicts.

        Each dict contains:
            type     – chart type key used by chart_generator
            title    – dynamically generated from column names
            section  – 'trends' | 'categorical' | 'numerical' | 'correlation'
            x, y     – column names (where applicable)
            column   – single column name (where applicable)
        """
        charts: List[Dict[str, Any]] = []

        num = self.profile.numerical
        cat = self.profile.categorical
        dates = self.profile.datetime

        # ── Trends section: Date + Numerical → Line chart ──────────────────
        if dates and num:
            for d in dates[:2]:
                for n in num[:self.MAX_CHARTS_PER_SECTION // 2]:
                    charts.append({
                        "type": "line",
                        "section": "trends",
                        "title": f"{_label(n)} over {_label(d)}",
                        "x": d,
                        "y": n,
                    })

        # ── Categorical section ─────────────────────────────────────────────
        for c in cat[:self.MAX_CHARTS_PER_SECTION]:
            n_unique = self.df[c].nunique(dropna=True)

            if n_unique > self.HIGH_CARDINALITY_THRESHOLD:
                # Too many categories — skip bar/pie, only show a small count chart
                continue

            if n_unique <= self.PIE_MAX_CARDINALITY:
                charts.append({
                    "type": "pie",
                    "section": "categorical",
                    "title": f"Composition of {_label(c)}",
                    "column": c,
                })
            else:
                charts.append({
                    "type": "count",
                    "section": "categorical",
                    "title": f"Top {_label(c)} values",
                    "column": c,
                })

        # ── Categorical × Numerical → Horizontal bar ───────────────────────
        if cat and num:
            for c in cat[:2]:
                n_unique = self.df[c].nunique(dropna=True)
                if n_unique > self.HIGH_CARDINALITY_THRESHOLD:
                    continue
                for n in num[:2]:
                    charts.append({
                        "type": "bar",
                        "section": "categorical",
                        "title": f"{_label(n)} by {_label(c)}",
                        "x": c,
                        "y": n,
                    })

        # ── Numerical section: Histograms ───────────────────────────────────
        for n in num[:self.MAX_CHARTS_PER_SECTION]:
            charts.append({
                "type": "histogram",
                "section": "numerical",
                "title": f"Distribution of {_label(n)}",
                "column": n,
            })

        # ── Numerical section: Box plots ────────────────────────────────────
        for n in num[:2]:
            charts.append({
                "type": "box",
                "section": "numerical",
                "title": f"{_label(n)} — Spread & Outliers",
                "column": n,
            })

        # ── Numerical section: Scatter plot ─────────────────────────────────
        if len(num) >= 2:
            charts.append({
                "type": "scatter",
                "section": "numerical",
                "title": f"{_label(num[1])} vs {_label(num[0])}",
                "x": num[0],
                "y": num[1],
            })

        # ── Correlation section: Heatmap ─────────────────────────────────────
        if len(num) >= 3:
            charts.append({
                "type": "heatmap",
                "section": "correlation",
                "title": "Correlation Matrix",
                "columns": num[:12],   # limit to keep heatmap readable
            })

        return charts

    # ─────────────────────────────────────────────────────────────────────────
    # Complete analysis
    # ─────────────────────────────────────────────────────────────────────────

    def analyze(self) -> Dict[str, Any]:
        """Run the full BI analysis and return a single result dict."""
        return {
            "summary": self.get_summary(),
            "profile": {
                "numerical": self.profile.numerical,
                "categorical": self.profile.categorical,
                "datetime": self.profile.datetime,
                "boolean": self.profile.boolean,
                "identifier": self.profile.identifier,
            },
            "kpis": self.generate_kpis(),
            "charts": self.generate_chart_recommendations(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Dataset resolver
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def discover_source_tiers(project_root: Path) -> List[SourceTier]:
        """
        Scan the project for available datasets, grouped by processing tier.

        Returns tiers ordered by priority (Gold first).
        The caller can present these tiers to the user for selection.
        """
        from core.run_context import get_current_run
        run_context = get_current_run()

        tiers: List[SourceTier] = []

        if run_context:
            # Use run-specific paths
            gold_dir = Path(run_context.gold_dir)
            silver_dir = Path(run_context.silver_dir)
            # Uploads still usually come from the global uploads directory
            uploads_dir = project_root / "data" / "uploads"
        else:
            # Fallback to static paths
            gold_dir = project_root / "data" / "gold"
            silver_dir = project_root / "data" / "silver"
            uploads_dir = project_root / "data" / "uploads"

        # Gold layer
        gold_files = _csv_files_in(gold_dir)
        if gold_files:
            tiers.append(SourceTier(label="Gold Layer (Warehouse)", priority=1, datasets=gold_files))

        # Silver layer
        silver_files = _csv_files_in(silver_dir)
        if silver_files:
            tiers.append(SourceTier(label="Silver Layer (Cleaned)", priority=2, datasets=silver_files))

        # Uploads
        upload_files = _csv_files_in(uploads_dir)
        if upload_files:
            tiers.append(SourceTier(label="Uploaded Files (Raw)", priority=3, datasets=upload_files))

        return tiers

    @staticmethod
    def load_dataframe(path: Path) -> pd.DataFrame:
        """Load a CSV, JSON, Parquet or Excel file into a DataFrame."""
        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        if ext == ".json":
            return pd.read_json(path)
        if ext == ".parquet":
            return pd.read_parquet(path)
        if ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        raise ValueError(f"Unsupported file extension: {ext}")


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _label(col: str) -> str:
    """Convert a column name to a human-readable label."""
    return str(col).replace("_", " ").replace("-", " ").title()


def _csv_files_in(directory: Path) -> List[Path]:
    """Return sorted CSV/Parquet/JSON files in a directory, or an empty list."""
    if not directory.is_dir():
        return []
    extensions = {".csv", ".parquet", ".json", ".xlsx", ".xls"}
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )
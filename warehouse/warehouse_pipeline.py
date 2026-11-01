"""
warehouse_pipeline.py
---------------------

Generate the complete Gold Layer
from the Silver Layer using dynamic schema inference.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from warehouse.schema_inference import SchemaInferenceEngine, InferredSchema
from warehouse.warehouse_generator import WarehouseGenerator

# Allow imports from app
APP_ROOT = Path(__file__).resolve().parents[1] / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
    
from core.run_context import get_current_run

class WarehousePipeline:

    def __init__(self, dataframes: Dict[str, pd.DataFrame] = None, output_dir: Path = None):
        self.dataframes = dataframes
        self.output_dir = output_dir

    def infer_schema(self) -> InferredSchema:
        """
        Public method for the UI to run schema inference and present it to the user.
        """
        if not self.dataframes:
            self._load_from_run_context()
            
        engine = SchemaInferenceEngine(self.dataframes)
        return engine.infer()

    def infer_schema_from_tables(self, dataframes: Dict[str, pd.DataFrame]) -> InferredSchema:
        """
        Public method for the UI to run schema inference with selected tables.
        """
        self.dataframes = dataframes
        engine = SchemaInferenceEngine(self.dataframes)
        return engine.infer()

    def generate(self, schema: InferredSchema) -> Dict[str, Any]:
        """
        Public method for the UI to run the generator with the approved schema.
        """
        if not self.dataframes:
            self._load_from_run_context()
            
        generator = WarehouseGenerator(self.dataframes, schema, self.output_dir)
        return generator.run()

    def run(self) -> Dict[str, Any]:
        """
        Runs the full pipeline end-to-end (used by CLI or non-interactive mode).
        """
        schema = self.infer_schema()
        return self.generate(schema)

    def _load_from_run_context(self):
        run_context = get_current_run()

        if not run_context:
            raise ValueError(
                "No active dataset found. Please upload and process a dataset before creating the warehouse."
            )
        if run_context.pipeline_status.get("ETL") not in {"success", "completed", "complete"}:
            raise ValueError("The dataset has not been processed yet. Please run ETL before creating the warehouse.")

        self.output_dir = Path(run_context.gold_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect silver tables from ALL runs in the runs directory
        # This ensures all tables from the same uploaded dataset are included
        runs_base_dir = Path(run_context.silver_dir).parent.parent
        self.dataframes = {}
        parquet_stems = set()
        
        for run_dir in runs_base_dir.iterdir():
            if not run_dir.is_dir():
                continue
            silver_dir = run_dir / "silver"
            if not silver_dir.is_dir():
                continue
            for file in silver_dir.glob("*.parquet"):
                if file.stem not in self.dataframes:
                    self.dataframes[file.stem] = pd.read_parquet(file)
                    parquet_stems.add(file.stem)
            for file in silver_dir.glob("*.csv"):
                if file.stem in parquet_stems or file.stem in self.dataframes:
                    continue
                self.dataframes[file.stem] = self._restore_datetime_columns(pd.read_csv(file))
            
        if not self.dataframes:
            raise ValueError(
                "No processed dataset was found. Please run the ETL pipeline first."
            )

    @staticmethod
    def _restore_datetime_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Restore date-like CSV fields for schema inference and warehouse output."""
        date_hints = (
            "date", "time", "timestamp", "datetime", "created", "updated",
            "modified", "start", "end", "birth", "hire", "dob",
        )
        for column in dataframe.columns:
            series = dataframe[column]
            if pd.api.types.is_numeric_dtype(series):
                continue
            if not any(hint in str(column).lower() for hint in date_hints):
                continue
            values = series.dropna()
            if values.empty:
                continue
            parsed = pd.to_datetime(series, errors="coerce")
            if float(parsed.notna().mean()) >= 0.8:
                dataframe[column] = parsed
        return dataframe

def main():
    pipeline = WarehousePipeline()
    pipeline.run()

if __name__ == "__main__":
    main()

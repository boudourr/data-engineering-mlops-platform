"""
warehouse_generator.py
----------------------

Generates a data warehouse (Gold Layer) based on an inferred star schema.
"""
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any
import json
from warehouse.schema_inference import InferredSchema


class WarehouseGenerator:
    def __init__(self, dataframes: Dict[str, pd.DataFrame], schema: InferredSchema, output_dir: Path):
        self.dataframes = dataframes
        self.schema = schema
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_tables: List[Path] = []
        self.metadata = {
            "fact_table": self.schema.fact_table_name,
            "dimensions": {},
            "measures": self.schema.measures,
        }

    def run(self) -> Dict[str, Any]:
        print("=" * 60)
        print("STARTING GENERIC DATA WAREHOUSE GENERATION")
        print("=" * 60)

        fact_df = self.dataframes[self.schema.fact_source_table].copy()

        # Build dimensions
        for dim in self.schema.dimensions:
            if dim.is_date_dimension:
                date_col = dim.columns[0]
                self._build_date_dim(fact_df[date_col].dropna(), dim.name, dim.primary_key)
                
                # Link date dimension to fact table
                fact_df[dim.primary_key] = pd.to_datetime(fact_df[date_col], errors='coerce').dt.strftime("%Y%m%d").fillna(0).astype(int)
            else:
                dim_df = self.dataframes[dim.source_table]
                self._build_dimension(dim_df, dim.name, dim.primary_key, dim.columns)
                
            self.metadata["dimensions"][dim.name] = {
                "primary_key": dim.primary_key,
                "columns": dim.columns,
                "is_date": dim.is_date_dimension
            }

        # Build fact table
        self._build_fact_table(fact_df, self.schema.fact_table_name)

        # Save metadata
        self._save_metadata()

        print("=" * 60)
        print("GENERIC DATA WAREHOUSE CREATED SUCCESSFULLY")
        print("=" * 60)

        return {
            "status": "SUCCESS",
            "message": "Warehouse tables were built successfully.",
            "generated_tables": self.generated_tables,
            "metadata": self.metadata
        }

    def _build_date_dim(self, series: pd.Series, dim_name: str, primary_key: str):
        full_dates = pd.to_datetime(series, errors='coerce').dt.normalize().unique()
        dim_date = pd.DataFrame({"full_date": full_dates}).dropna()
        
        dim_date[primary_key] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
        dim_date["year"] = dim_date["full_date"].dt.year
        dim_date["quarter"] = dim_date["full_date"].dt.quarter
        dim_date["month"] = dim_date["full_date"].dt.month
        dim_date["month_name"] = dim_date["full_date"].dt.month_name()
        dim_date["day"] = dim_date["full_date"].dt.day
        dim_date["week_of_year"] = dim_date["full_date"].dt.isocalendar().week.astype(int)
        
        self._save_table(dim_date, dim_name)

    def _build_dimension(self, df: pd.DataFrame, name: str, pk: str, columns: List[str]):
        # Depending on if it's a generated ID or existing
        dim_df = df[columns].dropna(subset=[pk] if pk in columns else columns).drop_duplicates().copy()
        
        # If the primary key is not naturally in the columns (e.g. we extracted a categorical column)
        if pk not in dim_df.columns:
            dim_df.insert(0, pk, range(1, len(dim_df) + 1))
            # Also, we would need to map this back to the fact table if it came from the same source!
            # Since this engine handles multi-table (where PK is naturally present) or single-table,
            # we need to ensure the linkage. For simplicity, in single-table, we might just keep
            # the original categorical value in the Fact table for now, or perform a join.
            # (In a fully robust engine, we'd replace the categorical column in the fact table with the new PK).
            
        self._save_table(dim_df, name)

    def _build_fact_table(self, df: pd.DataFrame, name: str):
        self._save_table(df, name)

    def _save_table(self, df: pd.DataFrame, name: str):
        path = self.output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        self.generated_tables.append(path)
        print(f"OK {name}")

    def _save_metadata(self):
        path = self.output_dir / "warehouse_metadata.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=4)
        print("OK warehouse_metadata.json")

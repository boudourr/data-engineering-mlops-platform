"""
schema_inference.py
-------------------

Dynamically infers a star schema from a given dataset or set of datasets.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any
import pandas as pd
from collections import defaultdict


@dataclass
class InferredDimension:
    name: str
    source_table: str
    columns: List[str]
    primary_key: str
    is_date_dimension: bool = False


@dataclass
class InferredSchema:
    fact_table_name: str
    fact_source_table: str
    dimensions: List[InferredDimension] = field(default_factory=list)
    measures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_table_name": self.fact_table_name,
            "fact_source_table": self.fact_source_table,
            "dimensions": [
                {
                    "name": d.name,
                    "source_table": d.source_table,
                    "columns": d.columns,
                    "primary_key": d.primary_key,
                    "is_date_dimension": d.is_date_dimension,
                }
                for d in self.dimensions
            ],
            "measures": self.measures,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferredSchema":
        dimensions = [
            InferredDimension(
                name=d["name"],
                source_table=d["source_table"],
                columns=d["columns"],
                primary_key=d["primary_key"],
                is_date_dimension=d.get("is_date_dimension", False)
            )
            for d in data.get("dimensions", [])
        ]
        return cls(
            fact_table_name=data.get("fact_table_name", "fact_events"),
            fact_source_table=data.get("fact_source_table", ""),
            dimensions=dimensions,
            measures=data.get("measures", [])
        )


class SchemaInferenceEngine:
    """
    Infers star schemas from a dictionary of DataFrames.
    """

    def __init__(self, dataframes: Dict[str, pd.DataFrame]):
        self.dataframes = dataframes

    def infer(self) -> InferredSchema:
        if not self.dataframes:
            raise ValueError("No dataframes provided for schema inference.")

        if len(self.dataframes) == 1:
            return self._infer_single_table()
        else:
            return self._infer_multi_table()

    def _infer_single_table(self) -> InferredSchema:
        source_name = list(self.dataframes.keys())[0]
        df = self.dataframes[source_name]

        dimensions: List[InferredDimension] = []
        measures = []
        
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        
        # Date dimension heuristic
        if not date_cols:
            for c in df.columns:
                if df[c].dtype == "object":
                    if any(kw in c.lower() for kw in ["date", "time", "timestamp"]):
                        try:
                            pd.to_datetime(df[c])
                            date_cols.append(c)
                        except Exception:
                            pass
                            
        if date_cols:
            primary_date = date_cols[0]
            dimensions.append(
                InferredDimension(
                    name="dim_date",
                    source_table=source_name,
                    columns=[primary_date],
                    primary_key="id_date",
                    is_date_dimension=True
                )
            )

        categorical_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and c not in date_cols]
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in date_cols]

        # Detect measures vs identifiers
        for num_col in numeric_cols:
            if not self._is_identifier(num_col, df[num_col]):
                measures.append(num_col)

        # Build categorical dimensions
        for cat_col in categorical_cols:
            if df[cat_col].nunique() < 50:
                dim_name = f"dim_{cat_col.lower()}"
                dimensions.append(
                    InferredDimension(
                        name=dim_name,
                        source_table=source_name,
                        columns=[cat_col],
                        primary_key=f"sk_{cat_col}_id"
                    )
                )
                
        fact_name = source_name.replace("_clean", "").lower()
        if not fact_name.startswith("fact_"):
            fact_name = f"fact_{fact_name}"

        return InferredSchema(
            fact_table_name=fact_name,
            fact_source_table=source_name,
            dimensions=dimensions,
            measures=measures
        )

    def _infer_multi_table(self) -> InferredSchema:
        scores = {}
        for name, df in self.dataframes.items():
            id_count = sum(1 for c in df.columns if self._is_identifier(c, df[c]))
            scores[name] = len(df) * (id_count + 1)
            
        fact_source_table = max(scores, key=scores.get)
        fact_df = self.dataframes[fact_source_table]
        
        dimensions: List[InferredDimension] = []
        measures = []
        
        for dim_source, df in self.dataframes.items():
            if dim_source == fact_source_table:
                continue
            
            id_cols = [c for c in df.columns if self._is_identifier(c, df[c])]
            pk = id_cols[0] if id_cols else df.columns[0]
            
            dim_name = f"dim_{dim_source.replace('_clean', '').lower()}"
            dimensions.append(
                InferredDimension(
                    name=dim_name,
                    source_table=dim_source,
                    columns=list(df.columns),
                    primary_key=pk
                )
            )
            
        date_cols = [c for c in fact_df.columns if pd.api.types.is_datetime64_any_dtype(fact_df[c])]
        if not date_cols:
            for c in fact_df.columns:
                if fact_df[c].dtype == "object" and any(kw in c.lower() for kw in ["date", "time", "timestamp"]):
                    date_cols.append(c)
                    
        if date_cols:
            dimensions.append(
                InferredDimension(
                    name="dim_date",
                    source_table=fact_source_table,
                    columns=[date_cols[0]],
                    primary_key="id_date",
                    is_date_dimension=True
                )
            )

        numeric_cols = [c for c in fact_df.columns if pd.api.types.is_numeric_dtype(fact_df[c]) and c not in date_cols]
        for num_col in numeric_cols:
            if not self._is_identifier(num_col, fact_df[num_col]):
                measures.append(num_col)
                
        fact_name = fact_source_table.replace('_clean', '').lower()
        if not fact_name.startswith("fact_"):
            fact_name = f"fact_{fact_name}"

        return InferredSchema(
            fact_table_name=fact_name,
            fact_source_table=fact_source_table,
            dimensions=dimensions,
            measures=measures
        )

    def _is_identifier(self, col: str, series: pd.Series) -> bool:
        name = str(col).lower()
        id_keywords = {"id", "identifier", "code", "key", "uuid", "num", "no", "index", "seq"}
        if any(kw in name for kw in id_keywords):
            return True
        if len(series) > 0:
            unique_ratio = series.nunique(dropna=True) / len(series)
            if unique_ratio > 0.95 and series.nunique(dropna=True) > 20:
                return True
        return False

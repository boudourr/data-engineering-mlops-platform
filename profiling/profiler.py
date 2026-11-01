"""
===========================================================
Data Profiler Engine
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Main profiling engine responsible for orchestrating
all profiling analyses.

This class:
    • Collects dataset metadata
    • Executes all analyzers
    • Optionally exports reports
    • Returns one unified profiling dictionary
===========================================================
"""

import pandas as pd

from profiling.statistics import StatisticsAnalyzer
from profiling.quality import DataQualityAnalyzer
from profiling.frequency import FrequencyAnalyzer
from profiling.outliers import OutlierAnalyzer
from profiling.integrity import IntegrityAnalyzer
from profiling.reports import ReportGenerator


class DataProfiler:

    def __init__(
        self,
        dataframe: pd.DataFrame,
        primary_key: str = None,
        table_name: str = "",
        date_columns: list = None,
        export: bool = False
    ):

        self.df = dataframe
        self.primary_key = primary_key
        self.table_name = table_name
        self.date_columns = date_columns if date_columns else []
        self.export = export

    # =====================================================
    # Dataset Information
    # =====================================================

    def dataset_dimensions(self):

        rows, columns = self.df.shape

        return {

            "Rows": rows,

            "Columns": columns

        }

    # =====================================================

    def schema(self):

        return pd.DataFrame({

            "Column": self.df.columns,

            "Data Type": self.df.dtypes.astype(str).values

        })

    # =====================================================

    def memory_usage(self):

        memory = self.df.memory_usage(deep=True)

        return pd.DataFrame({

            "Column": memory.index,

            "Memory (Bytes)": memory.values,

            "Memory (KB)": (memory.values / 1024).round(2),

            "Memory (MB)": (memory.values / (1024 ** 2)).round(4)

        })

    # =====================================================

    def unique_values(self):

        return pd.DataFrame({

            "Column": self.df.columns,

            "Unique Values": self.df.nunique().values

        })

    # =====================================================

    def cardinality(self):

        cardinality = (

            self.df.nunique()

            / len(self.df)

        ).round(4)

        return pd.DataFrame({

            "Column": cardinality.index,

            "Cardinality": cardinality.values

        })

    # =====================================================
    # Main Profiling Engine
    # =====================================================

    def run(self):

        # -------------------------------------------------
        # Dataset Metadata
        # -------------------------------------------------

        dimensions = self.dataset_dimensions()

        schema = self.schema()

        memory = self.memory_usage()

        unique = self.unique_values()

        cardinality = self.cardinality()

        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        statistics = StatisticsAnalyzer(self.df)

        statistics_results = statistics.run()

        # -------------------------------------------------
        # Data Quality
        # -------------------------------------------------

        quality = DataQualityAnalyzer(

            dataframe=self.df,

            primary_key=self.primary_key

        )

        quality_results = quality.run()

        # -------------------------------------------------
        # Frequency
        # -------------------------------------------------

        frequency = FrequencyAnalyzer(self.df)

        frequency_results = frequency.run()

        # -------------------------------------------------
        # Outliers
        # -------------------------------------------------

        outliers = OutlierAnalyzer(self.df)

        outlier_results = outliers.run()

        # -------------------------------------------------
        # Integrity
        # -------------------------------------------------

        integrity_results = None

        # Integrity checks require parent-child tables.
        # They will be executed during the Automated ETL
        # phase where relationships are available.

        # -------------------------------------------------
        # Collect Results
        # -------------------------------------------------

        results = {

            "metadata": {

                "table_name": self.table_name,

                "dimensions": dimensions,

                "schema": schema,

                "memory_usage": memory,

                "unique_values": unique,

                "cardinality": cardinality

            },

            "statistics": statistics_results,

            "quality": quality_results,

            "frequency": frequency_results,

            "outliers": outlier_results,

            "integrity": integrity_results

        }

        # -------------------------------------------------
        # Export Reports
        # -------------------------------------------------

        if self.export:

            report = ReportGenerator()

            export_reports = {

                "schema": schema,

                "memory_usage": memory,

                "unique_values": unique,

                "cardinality": cardinality,

                "quality_summary": quality_results["quality_summary"],

                "statistics_summary": statistics_results["descriptive_statistics"]

            }

            report.export_all(export_reports)

        # -------------------------------------------------
        # Return Results
        # -------------------------------------------------

        return results
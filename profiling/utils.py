"""
===========================================================
Utilities Module
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
This module contains reusable utility functions shared
across the profiling framework.
===========================================================
"""

import pandas as pd
import numpy as np


class ProfilingUtils:
    """
    Utility methods used throughout the profiling framework.
    """

    @staticmethod
    def memory_usage(df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns memory usage for each column.
        """
        memory = df.memory_usage(deep=True)

        return pd.DataFrame({
            "Column": memory.index,
            "Memory (Bytes)": memory.values,
            "Memory (KB)": (memory.values / 1024).round(2),
            "Memory (MB)": (memory.values / (1024 ** 2)).round(4)
        })


    @staticmethod
    def dataframe_dimensions(df: pd.DataFrame) -> dict:
        """
        Returns dataset dimensions.
        """
        rows, columns = df.shape

        return {
            "Rows": rows,
            "Columns": columns
        }


    @staticmethod
    def data_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns column data types.
        """
        return pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str).values
        })


    @staticmethod
    def unique_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns number of unique values.
        """
        return pd.DataFrame({
            "Column": df.columns,
            "Unique Values": df.nunique().values
        })


    @staticmethod
    def cardinality(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates cardinality.
        """

        cardinality = (
            df.nunique() / len(df)
        ).round(4)

        return pd.DataFrame({
            "Column": cardinality.index,
            "Cardinality": cardinality.values
        })


    @staticmethod
    def numeric_columns(df: pd.DataFrame):
        """
        Returns numeric columns.
        """
        return df.select_dtypes(include=np.number).columns.tolist()


    @staticmethod
    def categorical_columns(df: pd.DataFrame):
        """
        Returns categorical columns.
        """
        return df.select_dtypes(include="object").columns.tolist()


    @staticmethod
    def datetime_columns(df: pd.DataFrame):
        """
        Returns datetime columns.
        """
        return df.select_dtypes(
            include=["datetime64[ns]"]
        ).columns.tolist()


    @staticmethod
    def convert_to_datetime(df: pd.DataFrame, columns: list):
        """
        Converts columns to datetime.
        """
        for column in columns:

            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

        return df


    @staticmethod
    def calculate_percentage(part: int, total: int):
        """
        Returns percentage.
        """

        if total == 0:
            return 0

        return round((part / total) * 100, 2)


    @staticmethod
    def separator(length: int = 70):
        """
        Prints a separator.
        """
        print("=" * length)


    @staticmethod
    def title(text: str):
        """
        Prints formatted section title.
        """
        ProfilingUtils.separator()
        print(text.upper())
        ProfilingUtils.separator()
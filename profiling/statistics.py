"""
===========================================================
Statistics Analyzer
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Performs descriptive statistical analysis on numerical
and categorical columns.
===========================================================
"""

import pandas as pd
import numpy as np


class StatisticsAnalyzer:

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    # ======================================================
    # Numeric Columns
    # ======================================================

    def numeric_columns(self):
        """Return numeric columns."""
        return self.df.select_dtypes(include=np.number).columns.tolist()

    # ======================================================

    def descriptive_statistics(self):
        """Return descriptive statistics for numeric columns."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.DataFrame()

        return self.df[numeric].describe().T

    # ======================================================

    def variance(self):
        """Variance of numeric columns."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.Series(dtype=float)

        return self.df[numeric].var()

    # ======================================================

    def standard_deviation(self):
        """Standard deviation."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.Series(dtype=float)

        return self.df[numeric].std()

    # ======================================================

    def median(self):
        """Median."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.Series(dtype=float)

        return self.df[numeric].median()

    # ======================================================

    def mode(self):
        """Mode."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.DataFrame()

        return self.df[numeric].mode()

    # ======================================================

    def skewness(self):
        """Skewness."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.Series(dtype=float)

        return self.df[numeric].skew()

    # ======================================================

    def kurtosis(self):
        """Kurtosis."""

        numeric = self.numeric_columns()

        if len(numeric) == 0:
            return pd.Series(dtype=float)

        return self.df[numeric].kurt()

    # ======================================================
    # Categorical Columns
    # ======================================================

    def categorical_columns(self):
        """Return categorical columns."""

        return self.df.select_dtypes(include="object").columns.tolist()

    # ======================================================

    def categorical_summary(self):
        """Summary of categorical columns."""

        categorical = self.categorical_columns()

        summary = []

        for col in categorical:

            summary.append({

                "Column": col,

                "Unique Values": self.df[col].nunique(),

                "Most Frequent": self.df[col].mode(dropna=True).iloc[0]
                if not self.df[col].mode().empty else None,

                "Frequency": self.df[col].value_counts(dropna=False).iloc[0]

            })

        return pd.DataFrame(summary)

    # ======================================================
    # Complete Report
    # ======================================================

    def run(self):
        """
        Generate complete statistical report.
        """

        return {

            "descriptive_statistics":
                self.descriptive_statistics(),

            "variance":
                self.variance(),

            "standard_deviation":
                self.standard_deviation(),

            "median":
                self.median(),

            "mode":
                self.mode(),

            "skewness":
                self.skewness(),

            "kurtosis":
                self.kurtosis(),

            "categorical_summary":
                self.categorical_summary()

        }
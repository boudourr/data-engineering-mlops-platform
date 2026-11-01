"""
===========================================================
Outlier Analyzer
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Detects outliers in numerical columns using:
- IQR Method
- Z-Score Method
===========================================================
"""

import pandas as pd
import numpy as np


class OutlierAnalyzer:

    def __init__(self, dataframe: pd.DataFrame):

        self.df = dataframe

    # =====================================================
    # Numeric Columns
    # =====================================================

    def numeric_columns(self):

        return self.df.select_dtypes(include=np.number).columns.tolist()

    # =====================================================
    # IQR Method
    # =====================================================

    def iqr(self, column):

        if column not in self.df.columns:
            return None

        q1 = self.df[column].quantile(0.25)
        q3 = self.df[column].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        outliers = self.df[
            (self.df[column] < lower) |
            (self.df[column] > upper)
        ]

        return {

            "Column": column,

            "Method": "IQR",

            "Lower Bound": lower,

            "Upper Bound": upper,

            "Outliers": len(outliers),

            "Outlier Percentage":
                round(
                    len(outliers) / len(self.df) * 100,
                    2
                )

        }

    # =====================================================
    # Z-Score Method
    # =====================================================

    def zscore(self, column, threshold=3):

        if column not in self.df.columns:
            return None

        mean = self.df[column].mean()
        std = self.df[column].std()

        if std == 0:
            return {

                "Column": column,

                "Method": "Z-Score",

                "Outliers": 0

            }

        z_scores = (
            self.df[column] - mean
        ) / std

        outliers = self.df[
            abs(z_scores) > threshold
        ]

        return {

            "Column": column,

            "Method": "Z-Score",

            "Threshold": threshold,

            "Outliers": len(outliers),

            "Outlier Percentage":
                round(
                    len(outliers) / len(self.df) * 100,
                    2
                )

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        results = []

        for column in self.numeric_columns():

            results.append(self.iqr(column))

        return pd.DataFrame(results)

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        report = {}

        for column in self.numeric_columns():

            report[column] = {

                "IQR": self.iqr(column),

                "Z-Score": self.zscore(column)

            }

        return {

            "summary": self.summary(),

            "details": report

        }
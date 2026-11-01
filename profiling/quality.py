"""
===========================================================
Data Quality Analyzer
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Performs data quality assessment including:
- Missing values
- Missing percentages
- Duplicate rows
- Duplicate primary keys
- Empty strings
- Completeness
- Uniqueness
- Overall data quality score
===========================================================
"""

import pandas as pd
import numpy as np


class DataQualityAnalyzer:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 primary_key: str = None):

        self.df = dataframe
        self.primary_key = primary_key

    # =====================================================
    # Missing Values
    # =====================================================

    def missing_values(self):

        return pd.DataFrame({

            "Column": self.df.columns,

            "Missing Values": self.df.isnull().sum().values

        })

    # =====================================================

    def missing_percentage(self):

        return pd.DataFrame({

            "Column": self.df.columns,

            "Missing (%)":
                (
                    self.df.isnull().mean() * 100
                ).round(2).values

        })

    # =====================================================
    # Empty Strings
    # =====================================================

    def empty_strings(self):

        results = []

        for column in self.df.select_dtypes(include="object"):

            empty = (
                self.df[column]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            results.append({

                "Column": column,

                "Empty Strings": empty

            })

        return pd.DataFrame(results)

    # =====================================================
    # Duplicate Rows
    # =====================================================

    def duplicate_rows(self):

        return int(self.df.duplicated().sum())

    # =====================================================
    # Duplicate Primary Keys
    # =====================================================

    def duplicate_primary_keys(self):

        if self.primary_key is None:

            return None

        if self.primary_key not in self.df.columns:

            return None

        return int(

            self.df[self.primary_key]

            .duplicated()

            .sum()

        )

    # =====================================================
    # Completeness
    # =====================================================

    def completeness_score(self):

        total_cells = self.df.shape[0] * self.df.shape[1]

        missing_cells = self.df.isnull().sum().sum()

        score = (

            (1 - (missing_cells / total_cells))

            * 100

        )

        return round(score, 2)

    # =====================================================
    # Uniqueness
    # =====================================================

    def uniqueness_score(self):

        duplicate_rows = self.duplicate_rows()

        score = (

            (1 - duplicate_rows / len(self.df))

            * 100

        )

        return round(score, 2)

    # =====================================================
    # Validity
    # =====================================================

    def validity_score(self):
        """
        Placeholder for future validation rules.
        """

        return 100.0

    # =====================================================
    # Consistency
    # =====================================================

    def consistency_score(self):
        """
        Placeholder for future consistency checks.
        """

        return 100.0

    # =====================================================
    # Overall Quality Score
    # =====================================================

    def overall_quality_score(self):

        completeness = self.completeness_score()

        uniqueness = self.uniqueness_score()

        validity = self.validity_score()

        consistency = self.consistency_score()

        score = (

            completeness * 0.35 +

            uniqueness * 0.25 +

            validity * 0.20 +

            consistency * 0.20

        )

        return round(score, 2)

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        return pd.DataFrame({

            "Metric": [

                "Completeness",

                "Uniqueness",

                "Validity",

                "Consistency",

                "Overall Quality Score"

            ],

            "Score": [

                self.completeness_score(),

                self.uniqueness_score(),

                self.validity_score(),

                self.consistency_score(),

                self.overall_quality_score()

            ]

        })

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        return {

            "missing_values":
                self.missing_values(),

            "missing_percentage":
                self.missing_percentage(),

            "empty_strings":
                self.empty_strings(),

            "duplicate_rows":
                self.duplicate_rows(),

            "duplicate_primary_keys":
                self.duplicate_primary_keys(),

            "quality_summary":
                self.summary()

        }
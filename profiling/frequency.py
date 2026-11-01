"""
===========================================================
Frequency Analyzer
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Analyzes categorical columns by computing:
- Frequency counts
- Frequency percentages
- Top values
- Least frequent values
- Cardinality
===========================================================
"""

import pandas as pd


class FrequencyAnalyzer:

    def __init__(self, dataframe: pd.DataFrame):

        self.df = dataframe

    # =====================================================
    # Categorical Columns
    # =====================================================

    def categorical_columns(self):
        """
        Return all categorical columns.
        """
        return self.df.select_dtypes(include=["object", "category"]).columns.tolist()

    # =====================================================
    # Frequency Table
    # =====================================================

    def frequency(self, column: str):

        if column not in self.df.columns:
            return pd.DataFrame()

        freq = self.df[column].value_counts(dropna=False)

        percentage = (
            self.df[column]
            .value_counts(normalize=True, dropna=False)
            * 100
        ).round(2)

        result = pd.DataFrame({
            "Value": freq.index,
            "Count": freq.values,
            "Percentage (%)": percentage.values
        })

        return result

    # =====================================================
    # Top Values
    # =====================================================

    def top_values(self, column: str, top_n: int = 10):

        return self.frequency(column).head(top_n)

    # =====================================================
    # Bottom Values
    # =====================================================

    def bottom_values(self, column: str, bottom_n: int = 10):

        return self.frequency(column).tail(bottom_n)

    # =====================================================
    # Cardinality
    # =====================================================

    def cardinality(self):

        result = []

        total_rows = len(self.df)

        for column in self.df.columns:

            unique = self.df[column].nunique(dropna=True)

            result.append({

                "Column": column,

                "Unique Values": unique,

                "Cardinality (%)": round(
                    unique / total_rows * 100,
                    2
                )

            })

        return pd.DataFrame(result)

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        summary = []

        for column in self.categorical_columns():

            vc = self.df[column].value_counts(dropna=False)

            summary.append({

                "Column": column,

                "Unique Values": self.df[column].nunique(),

                "Most Frequent Value": vc.index[0],

                "Frequency": vc.iloc[0]

            })

        return pd.DataFrame(summary)

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        results = {}

        for column in self.categorical_columns():

            results[column] = self.frequency(column)

        return {

            "summary": self.summary(),

            "cardinality": self.cardinality(),

            "frequency_tables": results

        }
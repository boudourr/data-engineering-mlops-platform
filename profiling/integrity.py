"""
===========================================================
Integrity Analyzer
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Performs referential integrity checks between
parent and child datasets.
===========================================================
"""

import pandas as pd


class IntegrityAnalyzer:

    def __init__(self):
        pass

    # =====================================================
    # Foreign Key Validation
    # =====================================================

    def check_foreign_key(
        self,
        parent_df: pd.DataFrame,
        child_df: pd.DataFrame,
        parent_key: str,
        foreign_key: str
    ):
        """
        Validate foreign key relationship.
        """

        parent_values = set(parent_df[parent_key].dropna())

        invalid_records = child_df[
            ~child_df[foreign_key].isin(parent_values)
        ]

        return {

            "Parent Table": parent_key,

            "Foreign Key": foreign_key,

            "Child Records": len(child_df),

            "Invalid Records": len(invalid_records),

            "Integrity (%)":
                round(
                    (
                        1 -
                        len(invalid_records) /
                        len(child_df)
                    ) * 100,
                    2
                ),

            "Status":
                "PASS"
                if len(invalid_records) == 0
                else "FAIL"

        }

    # =====================================================
    # Missing Parent Records
    # =====================================================

    def missing_parent_records(
        self,
        parent_df,
        child_df,
        parent_key,
        foreign_key
    ):
        """
        Return child records without matching parent.
        """

        return child_df[
            ~child_df[foreign_key]
            .isin(parent_df[parent_key])
        ]

    # =====================================================
    # Orphan Records
    # =====================================================

    def orphan_records(
        self,
        parent_df,
        child_df,
        parent_key,
        foreign_key
    ):
        """
        Alias for missing parent records.
        """

        return self.missing_parent_records(
            parent_df,
            child_df,
            parent_key,
            foreign_key
        )

    # =====================================================
    # Duplicate Primary Keys
    # =====================================================

    def duplicate_primary_keys(
        self,
        parent_df,
        primary_key
    ):

        duplicates = parent_df[
            parent_df[primary_key]
            .duplicated(keep=False)
        ]

        return duplicates

    # =====================================================
    # Duplicate Foreign Keys
    # =====================================================

    def duplicate_foreign_keys(
        self,
        child_df,
        foreign_key
    ):
        """
        Duplicate foreign keys are usually expected
        in transactional tables, but this function
        reports their frequency.
        """

        duplicates = (
            child_df[foreign_key]
            .value_counts()
            .reset_index()
        )

        duplicates.columns = [
            "Foreign Key",
            "Occurrences"
        ]

        return duplicates

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        parent_df,
        child_df,
        parent_key,
        foreign_key
    ):

        return pd.DataFrame([

            self.check_foreign_key(
                parent_df,
                child_df,
                parent_key,
                foreign_key
            )

        ])

    # =====================================================
    # Run
    # =====================================================

    def run(
        self,
        parent_df,
        child_df,
        parent_key,
        foreign_key
    ):

        return {

            "integrity":

                self.summary(

                    parent_df,

                    child_df,

                    parent_key,

                    foreign_key

                ),

            "orphan_records":

                self.orphan_records(

                    parent_df,

                    child_df,

                    parent_key,

                    foreign_key

                ),

            "duplicate_primary_keys":

                self.duplicate_primary_keys(

                    parent_df,

                    parent_key

                ),

            "duplicate_foreign_keys":

                self.duplicate_foreign_keys(

                    child_df,

                    foreign_key

                )

        }
"""
validator.py
------------

Data validation module.

Responsibilities
----------------
- Validate dataset structure
- Validate primary keys
- Detect duplicates
- Detect missing values
- Validate required columns
- Validate data types
- Compute a data quality score
"""

import pandas as pd

from etl.logger import get_logger


class DataValidator:

    """
    Validate a dataset before transformation.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        primary_key: list[str] | None = None,
        required_columns: list[str] | None = None
    ):

        self.df = dataframe

        self.table_name = table_name

        self.primary_key = primary_key or []

        self.required_columns = required_columns or []

        self.logger = get_logger(self.__class__.__name__)

        self.report = {}

    # =====================================================
    # Empty Dataset
    # =====================================================

    def check_empty_dataset(self):

        empty = self.df.empty

        self.report["empty_dataset"] = empty

        if empty:

            self.logger.warning(
                f"{self.table_name}: Dataset is empty."
            )

    # =====================================================
    # Missing Values
    # =====================================================

    def check_missing_values(self):

        missing = self.df.isnull().sum()

        missing = missing[missing > 0]

        self.report["missing_values"] = missing.to_dict()

    # =====================================================
    # Duplicate Rows
    # =====================================================

    def check_duplicate_rows(self):

        duplicates = int(
            self.df.duplicated().sum()
        )

        self.report["duplicate_rows"] = duplicates

    # =====================================================
    # Primary Key Validation
    # =====================================================

    def check_primary_key(self):

        if not self.primary_key:

            self.report["duplicate_primary_keys"] = None

            return

        duplicates = int(

            self.df
            .duplicated(subset=self.primary_key)
            .sum()

        )

        self.report["duplicate_primary_keys"] = duplicates

    # =====================================================
    # Required Columns
    # =====================================================

    def check_required_columns(self):

        missing_columns = [

            column

            for column in self.required_columns

            if column not in self.df.columns

        ]

        self.report[
            "missing_required_columns"
        ] = missing_columns

    # =====================================================
    # Data Types
    # =====================================================

    def check_data_types(self):

        self.report["data_types"] = (

            self.df

            .dtypes

            .astype(str)

            .to_dict()

        )

    # =====================================================
    # Quality Score
    # =====================================================

    def calculate_quality_score(self):

        score = 100

        if self.report["empty_dataset"]:

            score -= 50

        if self.report["missing_values"]:

            score -= 10

        if self.report["duplicate_rows"] > 0:

            score -= 10

        duplicate_pk = self.report["duplicate_primary_keys"]

        if duplicate_pk is not None:

            if duplicate_pk > 0:

                score -= 20

        if self.report["missing_required_columns"]:

            score -= 20

        score = max(score, 0)

        self.report["quality_score"] = score

    # =====================================================
    # Validation Pipeline
    # =====================================================

    def validate(self):

        self.logger.info(

            f"Validating table: {self.table_name}"

        )

        self.check_empty_dataset()

        self.check_missing_values()

        self.check_duplicate_rows()

        self.check_primary_key()

        self.check_required_columns()

        self.check_data_types()

        self.calculate_quality_score()

        self.logger.info(

            f"{self.table_name} validation completed."

        )

        return self.report
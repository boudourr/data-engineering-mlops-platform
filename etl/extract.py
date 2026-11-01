"""
extract.py
----------

Extract module for the Automated ETL Pipeline.

Responsibilities
----------------
- Load CSV datasets from the Bronze layer.
- Validate file existence.
- Return Pandas DataFrames.
- Log extraction events.
"""

from pathlib import Path

import pandas as pd

from etl.config import RAW_DATA_DIR
from etl.logger import get_logger


class Extractor:
    """
    Handles extraction of datasets from the raw data layer.
    """

    def __init__(self):

        self.logger = get_logger(self.__class__.__name__)

    # ======================================================
    # Internal Utilities
    # ======================================================

    def _get_file_path(self, filename: str) -> Path:
        """
        Build the absolute path of a dataset.
        """

        return RAW_DATA_DIR / filename

    # ======================================================
    # CSV Extraction
    # ======================================================

    def read_csv(
        self,
        filename: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load a CSV file from the raw data directory.

        Parameters
        ----------
        filename : str
            CSV filename.

        kwargs :
            Additional arguments passed to pandas.read_csv().

        Returns
        -------
        pandas.DataFrame
        """

        filepath = self._get_file_path(filename)

        if not filepath.exists():

            self.logger.error(
                f"Dataset not found: {filepath}"
            )

            raise FileNotFoundError(
                f"Dataset not found:\n{filepath}"
            )

        self.logger.info(
            f"Loading dataset: {filename}"
        )

        try:

            df = pd.read_csv(
                filepath,
                **kwargs
            )

            self.logger.info(
                f"{filename} loaded successfully "
                f"({df.shape[0]} rows, {df.shape[1]} columns)"
            )

            return df

        except Exception as e:

            self.logger.exception(
                f"Error while loading {filename}"
            )

            raise e

    # ======================================================
    # Preview Dataset
    # ======================================================

    def preview(
        self,
        filename: str,
        rows: int = 5
    ) -> pd.DataFrame:
        """
        Preview the first rows of a dataset.
        """

        df = self.read_csv(filename)

        return df.head(rows)

    # ======================================================
    # Dataset Information
    # ======================================================

    def get_shape(
        self,
        filename: str
    ) -> tuple:
        """
        Return dataset dimensions.
        """

        df = self.read_csv(filename)

        return df.shape

    # ======================================================
    # List Available Datasets
    # ======================================================

    def list_datasets(self) -> list[str]:
        """
        List every CSV available in the raw folder.
        """

        datasets = sorted(
            [
                file.name
                for file in RAW_DATA_DIR.glob("*.csv")
            ]
        )

        self.logger.info(
            f"{len(datasets)} datasets detected."
        )

        return datasets
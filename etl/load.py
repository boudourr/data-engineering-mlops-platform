"""
load.py
-------

Load module for the Automated ETL Pipeline.

Responsibilities
----------------
- Save transformed datasets
- Write data to the Silver layer
- Create destination folders automatically
- Log loading operations
"""

from pathlib import Path

import pandas as pd

from etl.config import SILVER_DATA_DIR
from etl.logger import get_logger


class Loader:
    """
    Load transformed datasets into the Silver layer.
    """

    def __init__(self, output_dir: Path | None = None):

        self.logger = get_logger(self.__class__.__name__)
        # The Streamlit workflow supplies the current run's Silver directory.
        # Keep the legacy location only for explicit, standalone ETL use.
        self.output_dir = Path(output_dir) if output_dir else SILVER_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # =====================================================
    # Build Output Path
    # =====================================================

    def _build_output_path(
        self,
        dataset_name: str
    ) -> Path:
        """
        Build the output file path.
        """

        return self.output_dir / f"{dataset_name}_clean.csv"

    # =====================================================
    # Save CSV
    # =====================================================

    def save_csv(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        index: bool = False
    ) -> Path:
        """
        Save a DataFrame into the Silver layer.

        Parameters
        ----------
        df : pandas.DataFrame
            Cleaned dataset.

        dataset_name : str
            Dataset name.

        index : bool
            Save DataFrame index.

        Returns
        -------
        pathlib.Path
            Saved file path.
        """

        output_path = self._build_output_path(
            dataset_name
        )

        try:

            df.to_csv(
                output_path,
                index=index,
                encoding="utf-8"
            )

            self.logger.info(
                f"Dataset saved successfully: {output_path.name}"
            )

            self.logger.info(
                f"Rows: {len(df)} | Columns: {len(df.columns)}"
            )

            return output_path

        except Exception as e:

            self.logger.exception(
                f"Failed to save {dataset_name}"
            )

            raise e

    def save_parquet(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        index: bool = False,
    ) -> Path:
        """Save the typed Silver representation for downstream processing."""
        output_path = self.output_dir / f"{dataset_name}_clean.parquet"
        try:
            df.to_parquet(output_path, index=index)
            self.logger.info(f"Typed dataset saved successfully: {output_path.name}")
            return output_path
        except Exception as error:
            self.logger.exception(f"Failed to save typed dataset {dataset_name}")
            raise error

    # =====================================================
    # Verify Output
    # =====================================================

    def file_exists(
        self,
        dataset_name: str
    ) -> bool:
        """
        Check whether the cleaned dataset exists.
        """

        return self._build_output_path(
            dataset_name
        ).exists()

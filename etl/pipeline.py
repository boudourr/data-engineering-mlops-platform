"""
pipeline.py
-----------

Central orchestration module for the Automated ETL Pipeline.

Workflow
--------
Bronze (Raw CSV)
        │
        ▼
    Extract
        │
        ▼
    Validate
        │
        ▼
   Transform
        │
        ▼
      Load
        │
        ▼
Silver Layer
"""

from etl.config import TABLES
from etl.extract import Extractor
from etl.validator import DataValidator
from etl.transformer import BaseTransformer
from etl.load import Loader
from etl.logger import get_logger


class ETLPipeline:

    def __init__(self):

        self.logger = get_logger("ETLPipeline")

        self.extractor = Extractor()
        self.transformer = BaseTransformer()
        self.loader = Loader()

        self.success = []
        self.failed = []

    # =====================================================
    # Process One Dataset
    # =====================================================

    def process_dataset(
        self,
        dataset_name: str,
        config: dict
    ) -> None:

        self.logger.info("=" * 70)
        self.logger.info(f"Processing dataset : {dataset_name}")

        try:

            # -------------------------------------------------
            # Extract
            # -------------------------------------------------

            df = self.extractor.read_csv(
                config["file"]
            )

            # -------------------------------------------------
            # Validate
            # -------------------------------------------------

            validator = DataValidator(
                dataframe=df,
                table_name=dataset_name,
                primary_key=config.get("primary_key", []),
                required_columns=config.get(
                    "required_columns",
                    []
                )
            )

            report = validator.validate()

            self.logger.info(
                f"Quality Score : {report['quality_score']}/100"
            )

            # -------------------------------------------------
            # Transform
            # -------------------------------------------------

            df = self.transformer.transform(
                df=df,
                dataset_name=dataset_name,
                datetime_columns=config.get(
                    "datetime_columns",
                    []
                ),
                fillna_strategy=config.get(
                    "fillna",
                    {}
                )
            )

            # -------------------------------------------------
            # Load
            # -------------------------------------------------

            self.loader.save_csv(
                df=df,
                dataset_name=dataset_name
            )

            self.success.append(dataset_name)

            self.logger.info(
                f"{dataset_name} completed successfully."
            )

        except Exception as error:

            self.failed.append(dataset_name)

            self.logger.exception(
                f"{dataset_name} failed.\n{error}"
            )

    # =====================================================
    # Run Entire Pipeline
    # =====================================================

    def run(self):

        self.logger.info("=" * 70)
        self.logger.info("STARTING ETL PIPELINE")
        self.logger.info("=" * 70)

        for dataset_name, config in TABLES.items():

            self.process_dataset(
                dataset_name,
                config
            )

        self.summary()

    # =====================================================
    # Pipeline Summary
    # =====================================================

    def summary(self):

        self.logger.info("=" * 70)
        self.logger.info("ETL PIPELINE FINISHED")
        self.logger.info("=" * 70)

        self.logger.info(
            f"Datasets Processed : {len(TABLES)}"
        )

        self.logger.info(
            f"Successful : {len(self.success)}"
        )

        self.logger.info(
            f"Failed : {len(self.failed)}"
        )

        if self.success:

            self.logger.info(
                "Successful datasets:"
            )

            for dataset in self.success:

                self.logger.info(f"   ✓ {dataset}"
                )

        if self.failed:

            self.logger.warning(
                "Failed datasets:"
            )

            for dataset in self.failed:

                self.logger.warning(
                    f"   ✗ {dataset}"
                )
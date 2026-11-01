"""
platform_pipeline.py
--------------------

Master orchestration pipeline for the
Modern Data Engineering Platform.

Workflow:

1. Automated ETL Pipeline
2. Data Warehouse Generation
3. MLOps Pipeline
4. Platform Monitoring
"""

from etl.pipeline import ETLPipeline
from warehouse.warehouse_pipeline import WarehousePipeline
from mlops.pipeline import MLOpsPipeline
from monitoring.monitor import PlatformMonitor


class PlatformPipeline:

    def __init__(self):

        # ==============================================
        # Initialize pipelines
        # ==============================================

        self.etl = ETLPipeline()

        self.warehouse = WarehousePipeline()

        self.mlops = MLOpsPipeline()

        self.monitor = PlatformMonitor()

    # ==============================================
    # Run Complete Platform
    # ==============================================

    def run(self):

        print()
        print("=" * 80)
        print("STARTING MODERN DATA ENGINEERING PLATFORM")
        print("=" * 80)

        # ==================================================
        # STEP 1 — AUTOMATED ETL
        # ==================================================

        print()
        print("=" * 80)
        print("STEP 1/4 — AUTOMATED ETL PIPELINE")
        print("=" * 80)

        self.etl.run()

        print()
        print("✓ ETL PIPELINE COMPLETED")
        print("✓ Silver Layer generated")

        # ==================================================
        # STEP 2 — DATA WAREHOUSE
        # ==================================================

        print()
        print("=" * 80)
        print("STEP 2/4 — DATA WAREHOUSE GENERATION")
        print("=" * 80)

        self.warehouse.run()

        print()
        print("✓ DATA WAREHOUSE COMPLETED")
        print("✓ Gold Layer generated")

        # ==================================================
        # STEP 3 — MLOPS
        # ==================================================

        print()
        print("=" * 80)
        print("STEP 3/4 — MLOPS PIPELINE")
        print("=" * 80)

        self.mlops.run()

        print()
        print("✓ MLOPS PIPELINE COMPLETED")
        print("✓ Model trained")
        print("✓ Model evaluated")
        print("✓ Predictions generated")

        # ==================================================
        # STEP 4 — MONITORING
        # ==================================================

        print()
        print("=" * 80)
        print("STEP 4/4 — PLATFORM MONITORING")
        print("=" * 80)

        monitoring_results = self.monitor.run()

        print()
        print("✓ PLATFORM MONITORING COMPLETED")

        # ==================================================
        # FINAL PLATFORM STATUS
        # ==================================================

        print()
        print("=" * 80)
        print("MODERN DATA ENGINEERING PLATFORM COMPLETED")
        print("=" * 80)

        print()
        print("Pipeline Status:")
        print("✓ ETL Pipeline")
        print("✓ Silver Layer")
        print("✓ Data Warehouse")
        print("✓ Gold Layer")
        print("✓ MLOps Pipeline")
        print("✓ Model Training")
        print("✓ Model Evaluation")
        print("✓ Predictions")
        print("✓ Monitoring")

        print()
        print("=" * 80)

        return monitoring_results


# ======================================================
# Main
# ======================================================

def main():

    pipeline = PlatformPipeline()

    pipeline.run()


if __name__ == "__main__":
    main()
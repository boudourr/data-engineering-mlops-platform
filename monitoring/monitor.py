"""
monitor.py
----------

Monitoring utilities for the Modern Data Engineering Platform.

Monitors:
- ETL execution
- Data quality
- Data Warehouse
- MLOps results

Generates:
- monitoring_report.json
- monitoring_report.csv

Overall platform status:
- HEALTHY
- WARNING
- FAILED
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd


class PlatformMonitor:

    def __init__(self):

        # =====================================================
        # Paths
        # =====================================================

        self.silver = Path("data/silver")
        self.gold = Path("data/gold")
        self.predictions = Path("predictions")

        self.reports = (
            Path(__file__).resolve().parent / "reports"
        )

        # Create reports directory
        self.reports.mkdir(
            parents=True,
            exist_ok=True
        )

    # =====================================================
    # ETL Monitoring
    # =====================================================

    def monitor_etl(self):

        print()
        print("=" * 60)
        print("ETL MONITORING")
        print("=" * 60)

        datasets = [
            "customers_clean.csv",
            "orders_clean.csv",
            "order_items_clean.csv",
            "products_clean.csv",
            "sellers_clean.csv",
            "order_payments_clean.csv",
            "order_reviews_clean.csv",
            "category_clean.csv"
        ]

        successful = 0
        failed = 0

        total_missing = 0
        total_duplicates = 0

        dataset_results = {}

        for dataset in datasets:

            path = self.silver / dataset

            if path.exists():

                try:

                    df = pd.read_csv(path)

                    rows = len(df)
                    columns = len(df.columns)

                    missing = int(
                        df.isna().sum().sum()
                    )

                    duplicates = int(
                        df.duplicated().sum()
                    )

                    successful += 1

                    total_missing += missing
                    total_duplicates += duplicates

                    # Determine dataset status
                    if duplicates > 0:
                        status = "WARNING"
                    else:
                        status = "SUCCESS"

                    dataset_results[dataset] = {
                        "status": status,
                        "rows": rows,
                        "columns": columns,
                        "missing_values": missing,
                        "duplicates": duplicates
                    }

                    print(
                        f"✓ {dataset:<30} "
                        f"Rows: {rows:<8} "
                        f"Missing: {missing:<6} "
                        f"Duplicates: {duplicates}"
                    )

                except Exception as error:

                    failed += 1

                    dataset_results[dataset] = {
                        "status": "FAILED",
                        "rows": None,
                        "columns": None,
                        "missing_values": None,
                        "duplicates": None,
                        "error": str(error)
                    }

                    print(
                        f"✗ {dataset:<30} "
                        f"ERROR: {error}"
                    )

            else:

                failed += 1

                dataset_results[dataset] = {
                    "status": "FAILED",
                    "rows": None,
                    "columns": None,
                    "missing_values": None,
                    "duplicates": None
                }

                print(
                    f"✗ {dataset:<30} "
                    f"NOT FOUND"
                )

        # ETL overall status
        if failed > 0:
            status = "FAILED"

        elif total_duplicates > 0:
            status = "WARNING"

        else:
            status = "SUCCESS"

        print()
        print(f"Datasets monitored : {len(datasets)}")
        print(f"Successful         : {successful}")
        print(f"Failed             : {failed}")
        print(f"Total missing      : {total_missing}")
        print(f"Total duplicates   : {total_duplicates}")
        print(f"ETL status         : {status}")

        return {
            "status": status,
            "datasets_monitored": len(datasets),
            "successful": successful,
            "failed": failed,
            "total_missing_values": total_missing,
            "total_duplicates": total_duplicates,
            "datasets": dataset_results
        }

    # =====================================================
    # Data Warehouse Monitoring
    # =====================================================

    def monitor_warehouse(self):

        print()
        print("=" * 60)
        print("DATA WAREHOUSE MONITORING")
        print("=" * 60)

        tables = [
            "Dim_customers.csv",
            "Dim_products.csv",
            "Dim_sellers.csv",
            "Dim_payments.csv",
            "Dim_orders.csv",
            "Dim_date.csv",
            "Fact_sales.csv"
        ]

        results = {}

        successful = 0
        failed = 0

        for table in tables:

            path = self.gold / table

            if path.exists():

                try:

                    df = pd.read_csv(path)

                    rows = len(df)
                    columns = len(df.columns)

                    successful += 1

                    results[table] = {
                        "status": "SUCCESS",
                        "rows": rows,
                        "columns": columns
                    }

                    print(
                        f"✓ {table:<25} "
                        f"Rows: {rows}"
                    )

                except Exception as error:

                    failed += 1

                    results[table] = {
                        "status": "FAILED",
                        "rows": None,
                        "columns": None,
                        "error": str(error)
                    }

                    print(
                        f"✗ {table:<25} "
                        f"ERROR: {error}"
                    )

            else:

                failed += 1

                results[table] = {
                    "status": "FAILED",
                    "rows": None,
                    "columns": None
                }

                print(
                    f"✗ {table:<25} "
                    f"NOT FOUND"
                )

        # Check Fact table
        fact_rows = None

        if "Fact_sales.csv" in results:

            fact_rows = results[
                "Fact_sales.csv"
            ]["rows"]

        if failed > 0:

            status = "FAILED"

        elif fact_rows == 0:

            status = "WARNING"

        else:

            status = "SUCCESS"

        print()
        print(f"Tables monitored : {len(tables)}")
        print(f"Successful       : {successful}")
        print(f"Failed           : {failed}")
        print(f"Warehouse status : {status}")

        return {
            "status": status,
            "tables_monitored": len(tables),
            "successful": successful,
            "failed": failed,
            "tables": results
        }

    # =====================================================
    # MLOps Monitoring
    # =====================================================

    def monitor_mlops(self):

        print()
        print("=" * 60)
        print("MLOPS MONITORING")
        print("=" * 60)

        prediction_file = (
            self.predictions /
            "sales_predictions.csv"
        )

        if not prediction_file.exists():

            print("✗ Prediction file not found")

            return {
                "status": "FAILED",
                "predictions": 0,
                "actual_target_available": False,
                "predictions_available": False
            }

        try:

            df = pd.read_csv(
                prediction_file
            )

        except Exception as error:

            print(
                f"✗ Unable to read prediction file: "
                f"{error}"
            )

            return {
                "status": "FAILED",
                "predictions": 0,
                "error": str(error)
            }

        prediction_count = len(df)

        print("✓ Prediction file found")
        print(
            f"✓ Predictions : "
            f"{prediction_count}"
        )

        actual_available = (
            "payment_value" in df.columns
        )

        prediction_available = (
            "predicted_payment_value"
            in df.columns
        )

        error_available = (
            "prediction_error"
            in df.columns
        )

        if actual_available:

            print(
                "✓ Actual target available"
            )

        else:

            print(
                "✗ Actual target unavailable"
            )

        if prediction_available:

            print(
                "✓ Predictions available"
            )

        else:

            print(
                "✗ Predictions unavailable"
            )

        result = {
            "status": "SUCCESS",
            "predictions": prediction_count,
            "actual_target_available":
                actual_available,
            "predictions_available":
                prediction_available
        }

        # -------------------------------------------------
        # Prediction errors
        # -------------------------------------------------

        if error_available:

            mean_error = float(
                df["prediction_error"]
                .mean()
            )

            absolute_error = float(
                df["prediction_error"]
                .abs()
                .mean()
            )

            print(
                f"✓ Mean prediction error : "
                f"{mean_error:.4f}"
            )

            print(
                f"✓ Mean absolute error   : "
                f"{absolute_error:.4f}"
            )

            result[
                "mean_prediction_error"
            ] = mean_error

            result[
                "mean_absolute_error"
            ] = absolute_error

        # -------------------------------------------------
        # MLOps status
        # -------------------------------------------------

        if not actual_available:

            result["status"] = "WARNING"

        elif not prediction_available:

            result["status"] = "FAILED"

        elif prediction_count == 0:

            result["status"] = "WARNING"

        else:

            result["status"] = "SUCCESS"

        print(
            f"MLOps status : "
            f"{result['status']}"
        )

        return result

    # =====================================================
    # Determine Overall Platform Status
    # =====================================================

    def determine_overall_status(
        self,
        etl_status,
        warehouse_status,
        mlops_status
    ):

        statuses = [
            etl_status["status"],
            warehouse_status["status"],
            mlops_status["status"]
        ]

        # Any FAILED → platform FAILED
        if "FAILED" in statuses:

            return "FAILED"

        # Any WARNING → platform WARNING
        if "WARNING" in statuses:

            return "WARNING"

        # Everything successful
        return "HEALTHY"

    # =====================================================
    # Generate Flat CSV Report
    # =====================================================

    def generate_csv_report(
        self,
        report
    ):

        rows = []

        timestamp = report[
            "execution_timestamp"
        ]

        # -------------------------------------------------
        # ETL summary
        # -------------------------------------------------

        etl = report["etl"]

        rows.append({
            "timestamp": timestamp,
            "component": "ETL",
            "item": "Overall",
            "status": etl["status"],
            "rows": None,
            "missing_values":
                etl["total_missing_values"],
            "duplicates":
                etl["total_duplicates"]
        })

        for dataset, data in etl[
            "datasets"
        ].items():

            rows.append({
                "timestamp": timestamp,
                "component": "ETL",
                "item": dataset,
                "status": data["status"],
                "rows": data["rows"],
                "missing_values":
                    data["missing_values"],
                "duplicates":
                    data["duplicates"]
            })

        # -------------------------------------------------
        # Warehouse
        # -------------------------------------------------

        warehouse = report[
            "warehouse"
        ]

        rows.append({
            "timestamp": timestamp,
            "component": "Warehouse",
            "item": "Overall",
            "status": warehouse["status"],
            "rows": None,
            "missing_values": None,
            "duplicates": None
        })

        for table, data in warehouse[
            "tables"
        ].items():

            rows.append({
                "timestamp": timestamp,
                "component": "Warehouse",
                "item": table,
                "status": data["status"],
                "rows": data["rows"],
                "missing_values": None,
                "duplicates": None
            })

        # -------------------------------------------------
        # MLOps
        # -------------------------------------------------

        mlops = report["mlops"]

        rows.append({
            "timestamp": timestamp,
            "component": "MLOps",
            "item": "Overall",
            "status": mlops["status"],
            "rows": mlops.get(
                "predictions"
            ),
            "missing_values": None,
            "duplicates": None
        })

        csv_df = pd.DataFrame(rows)

        csv_path = (
            self.reports /
            "monitoring_report.csv"
        )

        csv_df.to_csv(
            csv_path,
            index=False
        )

        return csv_path

    # =====================================================
    # Save Monitoring Reports
    # =====================================================

    def save_reports(
        self,
        etl_status,
        warehouse_status,
        mlops_status
    ):

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        overall_status = (
            self.determine_overall_status(
                etl_status,
                warehouse_status,
                mlops_status
            )
        )

        report = {

            "execution_timestamp":
                timestamp,

            "overall_status":
                overall_status,

            "etl":
                etl_status,

            "warehouse":
                warehouse_status,

            "mlops":
                mlops_status
        }

        # -------------------------------------------------
        # JSON
        # -------------------------------------------------

        json_path = (
            self.reports /
            "monitoring_report.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=4
            )

        # -------------------------------------------------
        # CSV
        # -------------------------------------------------

        csv_path = self.generate_csv_report(
            report
        )

        print()
        print("=" * 60)
        print("MONITORING REPORTS")
        print("=" * 60)

        print(
            f"✓ JSON report : {json_path}"
        )

        print(
            f"✓ CSV report  : {csv_path}"
        )

        print(
            f"✓ Overall status : "
            f"{overall_status}"
        )

        return report

    # =====================================================
    # Full Monitoring
    # =====================================================

    def run(self):

        print()
        print("=" * 70)
        print("PLATFORM MONITORING")
        print("=" * 70)

        # -------------------------------------------------
        # ETL
        # -------------------------------------------------

        etl_status = (
            self.monitor_etl()
        )

        # -------------------------------------------------
        # Data Warehouse
        # -------------------------------------------------

        warehouse_status = (
            self.monitor_warehouse()
        )

        # -------------------------------------------------
        # MLOps
        # -------------------------------------------------

        mlops_status = (
            self.monitor_mlops()
        )

        # -------------------------------------------------
        # Save Reports
        # -------------------------------------------------

        report = self.save_reports(
            etl_status,
            warehouse_status,
            mlops_status
        )

        print()
        print("=" * 70)
        print("MONITORING COMPLETED")
        print("=" * 70)

        print(
            f"Overall Platform Status: "
            f"{report['overall_status']}"
        )

        return report


# =========================================================
# Generic Platform Monitor
# =========================================================

class GenericPlatformMonitor:
    def __init__(self, run_context):
        self.run_context = run_context
        self.silver = Path(run_context.silver_dir)
        self.gold = Path(run_context.gold_dir)
        self.predictions = Path(run_context.predictions_dir)
        self.reports = Path(run_context.reports_dir)
        self.reports.mkdir(parents=True, exist_ok=True)
        self.models = Path(run_context.models_dir)

    def monitor_etl(self):
        print("\n" + "=" * 60 + "\nETL MONITORING\n" + "=" * 60)
        datasets = [f.name for f in self.silver.glob("*.csv")] if self.silver.exists() else []
        
        successful = 0
        failed = 0
        total_missing = 0
        total_duplicates = 0
        dataset_results = {}

        if not datasets:
            print("No datasets found in silver layer.")
            return {
                "status": "WARNING",
                "datasets_monitored": 0,
                "successful": 0,
                "failed": 0,
                "total_missing_values": 0,
                "total_duplicates": 0,
                "datasets": {}
            }

        for dataset in datasets:
            path = self.silver / dataset
            try:
                df = pd.read_csv(path)
                rows = len(df)
                columns = len(df.columns)
                missing = int(df.isna().sum().sum())
                duplicates = int(df.duplicated().sum())
                successful += 1
                total_missing += missing
                total_duplicates += duplicates
                status = "WARNING" if duplicates > 0 else "SUCCESS"
                dataset_results[dataset] = {
                    "status": status,
                    "rows": rows,
                    "columns": columns,
                    "missing_values": missing,
                    "duplicates": duplicates
                }
                print(f"✓ {dataset:<30} Rows: {rows:<8} Missing: {missing:<6} Duplicates: {duplicates}")
            except Exception as error:
                failed += 1
                dataset_results[dataset] = {
                    "status": "FAILED",
                    "rows": None,
                    "columns": None,
                    "missing_values": None,
                    "duplicates": None,
                    "error": str(error)
                }
                print(f"✗ {dataset:<30} ERROR: {error}")

        if failed > 0:
            status = "FAILED"
        elif total_duplicates > 0:
            status = "WARNING"
        else:
            status = "SUCCESS"

        print(f"\nDatasets monitored : {len(datasets)}\nSuccessful         : {successful}\nFailed             : {failed}\nTotal missing      : {total_missing}\nTotal duplicates   : {total_duplicates}\nETL status         : {status}")
        return {
            "status": status,
            "datasets_monitored": len(datasets),
            "successful": successful,
            "failed": failed,
            "total_missing_values": total_missing,
            "total_duplicates": total_duplicates,
            "datasets": dataset_results
        }

    def monitor_warehouse(self):
        print("\n" + "=" * 60 + "\nDATA WAREHOUSE MONITORING\n" + "=" * 60)
        tables = [f.name for f in self.gold.glob("*.csv")] if self.gold.exists() else []
        
        results = {}
        successful = 0
        failed = 0

        if not tables:
            print("No tables found in warehouse.")
            return {
                "status": "WARNING",
                "tables_monitored": 0,
                "successful": 0,
                "failed": 0,
                "tables": {}
            }

        for table in tables:
            path = self.gold / table
            try:
                df = pd.read_csv(path)
                rows = len(df)
                columns = len(df.columns)
                successful += 1
                results[table] = {
                    "status": "SUCCESS",
                    "rows": rows,
                    "columns": columns
                }
                print(f"✓ {table:<25} Rows: {rows}")
            except Exception as error:
                failed += 1
                results[table] = {
                    "status": "FAILED",
                    "rows": None,
                    "columns": None,
                    "error": str(error)
                }
                print(f"✗ {table:<25} ERROR: {error}")

        status = "FAILED" if failed > 0 else "SUCCESS"
        print(f"\nTables monitored : {len(tables)}\nSuccessful       : {successful}\nFailed           : {failed}\nWarehouse status : {status}")
        return {
            "status": status,
            "tables_monitored": len(tables),
            "successful": successful,
            "failed": failed,
            "tables": results
        }

    def monitor_mlops(self):
        print("\n" + "=" * 60 + "\nMLOPS MONITORING\n" + "=" * 60)
        prediction_file = self.predictions / "predictions.csv"
        metadata_file = self.models / "metadata.json"

        if not prediction_file.exists():
            print("✗ Prediction file not found")
            return {
                "status": "WARNING", # Warning because MLOps might not have been run yet
                "predictions": 0,
                "actual_target_available": False,
                "predictions_available": False
            }
            
        try:
            df = pd.read_csv(prediction_file)
            target_column = "target"
            prediction_column = "prediction"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    target_column = metadata.get("target_column")
                    prediction_column = metadata.get("prediction_column")
                    
        except Exception as error:
            print(f"✗ Unable to read prediction file: {error}")
            return {
                "status": "FAILED",
                "predictions": 0,
                "error": str(error)
            }

        prediction_count = len(df)
        print("✓ Prediction file found")
        print(f"✓ Predictions : {prediction_count}")

        actual_available = target_column in df.columns
        prediction_available = prediction_column in df.columns
        
        # Calculate error if possible
        if actual_available and prediction_available:
             try:
                 df["prediction_error"] = df[prediction_column] - df[target_column]
             except:
                 pass # Might be categorical

        error_available = "prediction_error" in df.columns

        print("✓ Actual target available" if actual_available else "✗ Actual target unavailable")
        print("✓ Predictions available" if prediction_available else "✗ Predictions unavailable")

        result = {
            "status": "SUCCESS",
            "predictions": prediction_count,
            "actual_target_available": actual_available,
            "predictions_available": prediction_available
        }

        if error_available:
            mean_error = float(df["prediction_error"].mean())
            absolute_error = float(df["prediction_error"].abs().mean())
            print(f"✓ Mean prediction error : {mean_error:.4f}")
            print(f"✓ Mean absolute error   : {absolute_error:.4f}")
            result["mean_prediction_error"] = mean_error
            result["mean_absolute_error"] = absolute_error

        if not prediction_available:
            result["status"] = "FAILED"
        elif prediction_count == 0:
            result["status"] = "WARNING"

        print(f"MLOps status : {result['status']}")
        return result

    def determine_overall_status(self, etl_status, warehouse_status, mlops_status):
        statuses = [etl_status["status"], warehouse_status["status"], mlops_status["status"]]
        if "FAILED" in statuses:
            return "FAILED"
        if "WARNING" in statuses:
            return "WARNING"
        return "HEALTHY"

    def save_reports(self, etl_status, warehouse_status, mlops_status):
        timestamp = datetime.now(timezone.utc).isoformat()
        overall_status = self.determine_overall_status(etl_status, warehouse_status, mlops_status)
        report = {
            "execution_timestamp": timestamp,
            "overall_status": overall_status,
            "etl": etl_status,
            "warehouse": warehouse_status,
            "mlops": mlops_status
        }
        
        json_path = self.reports / "monitoring_report.json"
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)
            
        print("\n" + "=" * 60 + "\nMONITORING REPORTS\n" + "=" * 60)
        print(f"✓ JSON report : {json_path}")
        print(f"✓ Overall status : {overall_status}")
        return report

    def run(self):
        print("\n" + "=" * 70 + "\nPLATFORM MONITORING\n" + "=" * 70)
        etl_status = self.monitor_etl()
        warehouse_status = self.monitor_warehouse()
        mlops_status = self.monitor_mlops()
        report = self.save_reports(etl_status, warehouse_status, mlops_status)
        print("\n" + "=" * 70 + "\nMONITORING COMPLETED\n" + "=" * 70)
        print(f"Overall Platform Status: {report['overall_status']}")
        return report


# =========================================================
# Standalone Execution
# =========================================================

if __name__ == "__main__":
    import sys
    APP_ROOT = Path(__file__).resolve().parents[1] / "app"
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))
        
    try:
        from core.run_context import get_current_run
        run_context = get_current_run()
    except Exception:
        run_context = None

    if run_context:
        monitor = GenericPlatformMonitor(run_context)
    else:
        monitor = PlatformMonitor()
        
    monitor.run()
"""
config.py
---------

Central configuration file for the Automated ETL Pipeline.

This module defines:
- Project paths
- Data layer paths
- Dataset metadata
- Validation rules
- Transformation rules
"""

from pathlib import Path

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================
# DATA LAYERS
# ==========================================================

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DATA_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DATA_DIR = PROJECT_ROOT / "data" / "gold"

# ==========================================================
# LOGS
# ==========================================================

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "etl.log"

# ==========================================================
# CREATE DIRECTORIES IF THEY DON'T EXIST
# ==========================================================

SILVER_DATA_DIR.mkdir(parents=True, exist_ok=True)
GOLD_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# DATASET CONFIGURATION
# ==========================================================

# Optional development fixture only. It is never selected by the application.
EXAMPLE_TABLES = {

    # ------------------------------------------------------
    # Customers
    # ------------------------------------------------------

    "customers": {

        "file": "customers.csv",

        "primary_key": ["customer_id"],

        "required_columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state"
        ],

        "datetime_columns": [],

        "fillna": {}

    },

    # ------------------------------------------------------
    # Orders
    # ------------------------------------------------------

    "orders": {

        "file": "orders.csv",

        "primary_key": ["order_id"],

        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp"
        ],

        "datetime_columns": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ],

        "fillna": {}

    },

    # ------------------------------------------------------
    # Order Items
    # ------------------------------------------------------

    "order_items": {

        "file": "order_items.csv",

        "primary_key": [
            "order_id",
            "order_item_id"
        ],

        "required_columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id"
        ],

        "datetime_columns": [
            "shipping_limit_date"
        ],

        "fillna": {}

    },

    # ------------------------------------------------------
    # Products
    # ------------------------------------------------------

    "products": {

        "file": "products.csv",

        "primary_key": [
            "product_id"
        ],

        "required_columns": [
            "product_id"
        ],

        "datetime_columns": [],

        "fillna": {

            "product_category_name": "Unknown"

        }

    },

    # ------------------------------------------------------
    # Sellers
    # ------------------------------------------------------

    "sellers": {

        "file": "sellers.csv",

        "primary_key": [
            "seller_id"
        ],

        "required_columns": [
            "seller_id"
        ],

        "datetime_columns": [],

        "fillna": {}

    },

    # ------------------------------------------------------
    # Payments
    # ------------------------------------------------------

    "order_payments": {

        "file": "order_payments.csv",

        "primary_key": [
            "order_id",
            "payment_sequential"
        ],

        "required_columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_value"
        ],

        "datetime_columns": [],

        "fillna": {

            "payment_type": "not_defined"

        }

    },

    # ------------------------------------------------------
    # Reviews
    # ------------------------------------------------------

    "order_reviews": {

        "file": "order_reviews.csv",

        "primary_key": [
            "review_id",
            "order_id"
        ],

        "required_columns": [
            "review_id",
            "order_id"
        ],

        "datetime_columns": [
            "review_creation_date",
            "review_answer_timestamp"
        ],

        "fillna": {}

    },

    # ------------------------------------------------------
    # Category
    # ------------------------------------------------------

    "category": {

        "file": "category.csv",

        "primary_key": [
            "product_category_name"
        ],

        "required_columns": [
            "product_category_name",
            "product_category_name_english"
        ],

        "datetime_columns": [],

        "fillna": {}

    }

}

# Production pipelines receive the user's selected dataset and run context from
# the UI; there is intentionally no preconfigured dataset fallback.
TABLES = {}

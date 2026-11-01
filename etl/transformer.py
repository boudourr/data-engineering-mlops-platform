"""
transformer.py
--------------

Business Transformation Module
"""

import pandas as pd

from etl.logger import get_logger


class BaseTransformer:

    DATE_NAME_HINTS = (
        "date", "time", "at" ,"timestamp", "datetime", "created", "updated",
        "modified", "start", "end", "birth", "hire", "dob",
    )
    IDENTIFIER_NAME_HINTS = ("id", "identifier", "code", "zip", "postal", "phone", "account", "number")

    def __init__(self):

        self.logger = get_logger(self.__class__.__name__)

    # =====================================================
    # Generic Cleaning
    # =====================================================

    def remove_duplicates(self, df):

        before = len(df)

        df = df.drop_duplicates()

        self.logger.info(
            f"Removed {before - len(df)} duplicate rows."
        )

        return df

    def convert_datetime(self, df, columns):

        for column in columns:

            if column in df.columns:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

        return df

    def fill_missing_values(self, df, strategy):

        for column, value in strategy.items():

            if column in df.columns:

                df[column] = df[column].fillna(value)

        return df

    def clean_text(self, df):

        text_columns = df.select_dtypes(
            include="object"
        ).columns

        for column in text_columns:

            df[column] = (

                df[column]

                .astype("string")

                .str.strip()

                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )

            )

        return df

    # =====================================================
    # Customers
    # =====================================================

    def transform_customers(self, df):

        df["customer_location"] = (

            df["customer_city"]

            + ", "

            + df["customer_state"]

        )

        return df

    # =====================================================
    # Sellers
    # =====================================================

    def transform_sellers(self, df):

        df["seller_location"] = (

            df["seller_city"]

            + ", "

            + df["seller_state"]

        )

        return df

    # =====================================================
    # Orders
    # =====================================================

    def transform_orders(self, df):

        purchase = df["order_purchase_timestamp"]

        df["purchase_year"] = purchase.dt.year

        df["purchase_month"] = purchase.dt.month

        df["purchase_day"] = purchase.dt.day

        df["purchase_hour"] = purchase.dt.hour

        df["purchase_weekday"] = purchase.dt.day_name()

        if "order_delivered_customer_date" in df.columns:

            df["delivery_time_days"] = (

                df["order_delivered_customer_date"]

                -

                df["order_purchase_timestamp"]

            ).dt.days

        if (
            "order_estimated_delivery_date" in df.columns
            and
            "order_delivered_customer_date" in df.columns
        ):

            df["estimated_delay_days"] = (

                df["order_delivered_customer_date"]

                -

                df["order_estimated_delivery_date"]

            ).dt.days

        return df

    # =====================================================
    # Payments
    # =====================================================

    def transform_payments(self, df):

        df["is_installment"] = (

            df["payment_installments"] > 1

        )

        df["payment_value_category"] = pd.cut(

            df["payment_value"],

            bins=[0, 50, 150, float("inf")],

            labels=[

                "Low",

                "Medium",

                "High"

            ]

        )

        return df

    # =====================================================
    # Products
    # =====================================================

    def transform_products(self, df):

        if {

            "product_length_cm",

            "product_height_cm",

            "product_width_cm"

        }.issubset(df.columns):

            df["product_volume_cm3"] = (

                df["product_length_cm"]

                *

                df["product_height_cm"]

                *

                df["product_width_cm"]

            )

        if {

            "product_weight_g",

            "product_volume_cm3"

        }.issubset(df.columns):

            df["product_density"] = (

                df["product_weight_g"]

                /

                df["product_volume_cm3"]

            )

        return df

    # =====================================================
    # Reviews
    # =====================================================

    def transform_reviews(self, df):

        if "review_comment_message" in df.columns:

            df["review_length"] = (

                df["review_comment_message"]

                .fillna("")

                .str.len()

            )

        if {

            "review_creation_date",

            "review_answer_timestamp"

        }.issubset(df.columns):

            df["review_response_days"] = (

                df["review_answer_timestamp"]

                -

                df["review_creation_date"]

            ).dt.days

        return df

    # =====================================================
    # Main Transformation
    # =====================================================

    def transform(

        self,

        df,

        dataset_name,

        datetime_columns=None,

        fillna_strategy=None

    ):

        self.logger.info(
            "Starting transformation..."
        )

        df = self.remove_duplicates(df)

        requested_date_columns = datetime_columns or []
        detected_date_columns = self.detect_datetime_columns(df)
        date_columns = list(dict.fromkeys([*requested_date_columns, *detected_date_columns]))
        df = self.convert_datetime(df, date_columns)

        df = self.infer_scalar_types(df)

        df = self.fill_missing_values(
            df,
            fillna_strategy or {}
        )

        df = self.clean_text(df)

        # Do not dispatch to business-domain transformations by dataset name.
        # A user dataset may legitimately be called "customers" or "orders"
        # without having the columns of an old example dataset.

        self.logger.info(
            "Transformation completed."
        )

        return df

    def infer_scalar_types(self, df):
        """Infer booleans and numbers from text without corrupting identifiers."""
        for column in df.select_dtypes(include=["object", "string"]).columns:
            name = str(column).lower()
            values = df[column].dropna().astype("string").str.strip()
            if values.empty:
                continue

            normalized = values.str.lower()
            if normalized.isin({"true", "false", "yes", "no", "y", "n", "0", "1"}).all():
                mapping = {"true": True, "yes": True, "y": True, "1": True, "false": False, "no": False, "n": False, "0": False}
                df[column] = normalized.map(mapping).astype("boolean")
                continue

            if any(hint in name for hint in self.IDENTIFIER_NAME_HINTS):
                continue
            numeric = pd.to_numeric(values, errors="coerce")
            if float(numeric.notna().mean()) < 0.95 or values.str.match(r"[+-]?0\d+").any():
                continue
            if (numeric.dropna() % 1 == 0).all():
                df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
            else:
                df[column] = pd.to_numeric(df[column], errors="coerce").astype("Float64")
        return df

    def detect_datetime_columns(self, df, minimum_success_rate=0.8):
        """Find string columns whose names and values consistently indicate dates."""
        detected = []
        for column in df.columns:
            series = df[column]
            if pd.api.types.is_datetime64_any_dtype(series):
                detected.append(column)
                continue
            if pd.api.types.is_numeric_dtype(series):
                continue
            if not any(hint in str(column).lower() for hint in self.DATE_NAME_HINTS):
                continue
            values = series.dropna()
            if values.empty:
                continue
            parsed = pd.to_datetime(values, errors="coerce")
            if float(parsed.notna().mean()) >= minimum_success_rate:
                detected.append(column)
        return detected

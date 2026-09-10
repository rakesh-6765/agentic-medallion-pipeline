"""Build lazy Gold frames from typed Silver frames; persistence is the caller's job."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Mapping
from uuid import uuid4

from .sql_resources import render_sql

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


def _valid_dimension(frame: DataFrame, key: str) -> DataFrame:
    from pyspark.sql import Window, functions as F

    # Silver already rejects duplicates. This also prevents accidental fan-out if
    # a caller supplies a partially validated dimension (including PASS/FAIL pairs).
    return (
        frame.withColumn("_gold_key_count", F.count("*").over(Window.partitionBy(key)))
        .where(
            (F.col("quality_check_result") == "PASS")
            & F.col(key).isNotNull()
            & (F.col("_gold_key_count") == 1)
        )
        .drop("_gold_key_count")
    )


def _join_eligible(
    orders: DataFrame, customers: DataFrame, products: DataFrame
) -> DataFrame:
    from pyspark.sql import functions as F

    return (
        orders.where(
            (F.col("quality_check_result") == "PASS")
            & (F.col("order_status") == "Completed")
        )
        .alias("o")
        .join(customers.alias("c"), F.col("o.customer_id") == F.col("c.customer_id"))
        .join(products.alias("p"), F.col("o.product_id") == F.col("p.product_id"))
        .select(
            "o.order_id",
            "o.customer_id",
            "o.product_id",
            "o.order_date",
            "o.quantity",
            "o.unit_price",
            "o.total_amount",
            "p.product_name",
            "p.category",
            "c.country",
        )
    )


def eligible_sales(silver: Mapping[str, DataFrame]) -> DataFrame:
    """Join PASS Completed orders to unique PASS customers and products.

    Columns: order_id/customer_id/product_id (int), order_date (date), quantity
    (int), unit_price/total_amount (decimal(18,2)), product_name/category/country
    (string). No source lifetime_value, customer name, or email is exposed.
    """
    return _join_eligible(
        silver["orders"],
        _valid_dimension(silver["customers"], "customer_id"),
        _valid_dimension(silver["products"], "product_id"),
    )


def _threshold_literal(value: Decimal) -> str:
    if (
        not isinstance(value, Decimal)
        or not value.is_finite()
        or value <= 0
        or value > Decimal("9999999999999999.99")
        or value != value.quantize(Decimal("0.01"))
    ):
        raise ValueError("high_value_threshold must be a positive DECIMAL(18,2)")
    return format(value, ".2f")


def build_gold_tables(
    spark: SparkSession,
    silver: Mapping[str, DataFrame],
    *,
    high_value_threshold: Decimal = Decimal("1000.00"),
) -> dict[str, DataFrame]:
    """Return sales_by_product, revenue_by_customer, daily_weekly_trends and
    customer_segmentation as lazy DataFrames.

    Unique, session-local views are deliberately retained: Spark Connect can
    resolve SQL plans only when an action runs. Do not drop these views or close
    their session until all returned frames have been consumed/persisted. The
    parent runner owns session lifecycle and full-refresh persistence.
    """
    threshold = _threshold_literal(high_value_threshold)
    customers = _valid_dimension(silver["customers"], "customer_id")
    products = _valid_dimension(silver["products"], "product_id")
    eligible = _join_eligible(silver["orders"], customers, products)
    prefix = f"medallion_gold_{uuid4().hex}"
    inputs = {
        "valid_products": products,
        "valid_customers": customers,
        "eligible_sales": eligible,
    }
    views = {name: f"{prefix}_{name}" for name in inputs}
    for name, frame in inputs.items():
        frame.createOrReplaceTempView(views[name])

    gold = {}
    for key, resource, required in (
        (
            "sales_by_product",
            "01_sales_by_product.sql",
            ("valid_products", "eligible_sales"),
        ),
        (
            "revenue_by_customer",
            "02_revenue_by_customer.sql",
            ("valid_customers", "eligible_sales"),
        ),
        (
            "daily_weekly_trends",
            "03_daily_weekly_trends.sql",
            ("eligible_sales",),
        ),
    ):
        gold[key] = spark.sql(
            render_sql(
                "medallion.gold",
                resource,
                identifiers={name: views[name] for name in required},
            )
        )
    customer_view = f"{prefix}_customer_revenue"
    gold["revenue_by_customer"].createOrReplaceTempView(customer_view)
    gold["customer_segmentation"] = spark.sql(
        render_sql(
            "medallion.gold",
            "04_customer_segmentation.sql",
            identifiers={"customer_revenue": customer_view},
            decimals={"high_value_threshold": threshold},
        )
    )
    return gold

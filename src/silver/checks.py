from datetime import date
from functools import reduce
from operator import and_

from pyspark.sql import Column, DataFrame, Window, functions as F

from medallion.contracts import FIELDS, PRIMARY_KEYS


def all_of(expressions: list[Column]) -> Column:
    return reduce(and_, expressions, F.lit(True))


def present_or_valid(expression: Column) -> Column:
    # Missing/malformed values belong to completeness/types, not business rules.
    return F.coalesce(expression, F.lit(True))


def prepare_types(frame: DataFrame, table: str) -> DataFrame:
    fields = FIELDS[table]
    metadata = [name for name in frame.columns if name not in fields]
    cleaned = {
        name: F.regexp_replace(F.col(name), r"(?U)^\s+|\s+$", "")
        for name in fields
    }
    normalized = frame.select(
        *[
            F.when(F.length(value) > 0, value).alias(name)
            for name, value in cleaned.items()
        ],
        *[F.col(name) for name in metadata],
        F.struct(*[F.col(name) for name in fields]).alias("_raw"),
    )
    completeness = all_of(
        [F.col(name).isNotNull() for name in fields if name != "payment_date"]
    )
    validations = []
    parsed = []
    for name, dtype in fields.items():
        source = F.col(name)
        if dtype == "string":
            value = F.lower(source) if name == "email" else source
        else:
            value = F.expr(f"try_cast(`{name}` as {dtype})")
            pattern = {
                "int": r"^[+-]?\d+$",
                "date": r"^\d{4}-\d{2}-\d{2}$",
                "decimal(18,2)": r"^[+-]?\d+(\.\d{1,2})?$",
            }[dtype]
            validations.append(
                source.isNull() | (source.rlike(pattern) & value.isNotNull())
            )
        parsed.append(value.alias(name))
    return normalized.select(
        *parsed,
        *[F.col(name) for name in metadata],
        "_raw",
        completeness.alias("quality_completeness"),
        all_of(validations).alias("quality_type_validation"),
    )


def add_uniqueness(frame: DataFrame, table: str) -> DataFrame:
    key = F.col(PRIMARY_KEYS[table])
    return frame.withColumn(
        "quality_uniqueness",
        key.isNull() | (F.count(F.lit(1)).over(Window.partitionBy(key)) == 1),
    )


def add_referential_integrity(
    frame: DataFrame, table: str, prepared: dict[str, DataFrame]
) -> DataFrame:
    if table != "orders":
        return frame.withColumn("quality_referential_integrity", F.lit(True))
    for parent, key in (("customers", "customer_id"), ("products", "product_id")):
        known = f"_known_{key}"
        parents = (
            prepared[parent]
            .select(F.col(key).alias(known))
            .where(F.col(known).isNotNull())
            .distinct()
        )
        frame = frame.join(parents, frame[key] == parents[known], "left")
    return frame.withColumn(
        "quality_referential_integrity",
        (F.col("customer_id").isNull() | F.col("_known_customer_id").isNotNull())
        & (F.col("product_id").isNull() | F.col("_known_product_id").isNotNull()),
    ).drop("_known_customer_id", "_known_product_id")


def add_business_logic(frame: DataFrame, table: str, as_of_date: date) -> DataFrame:
    col = F.col
    checks = [col(PRIMARY_KEYS[table]) > 0]
    if table == "customers":
        checks += [
            col("email").rlike(r"(?U)^[^@\s]+@[^@\s]+\.[^@\s]+$"),
            col("signup_date") <= F.lit(as_of_date),
            col("customer_segment").isin("Premium", "Standard", "Basic"),
            col("lifetime_value") >= 0,
        ]
    elif table == "products":
        checks += [
            col("price") >= 0,
            col("cost") >= 0,
            col("price") >= col("cost"),
            col("stock_quantity") >= 0,
            col("reorder_level") >= 0,
        ]
    elif table == "orders":
        checks += [
            col("customer_id") > 0,
            col("product_id") > 0,
            col("order_date") <= F.lit(as_of_date),
            col("quantity") > 0,
            col("unit_price") >= 0,
            col("total_amount") >= 0,
            col("total_amount") == col("quantity") * col("unit_price"),
            col("order_status").isin("Pending", "Completed", "Cancelled"),
            (col("order_status") != "Completed") | col("payment_date").isNotNull(),
            col("payment_date") >= col("order_date"),
            col("payment_date") <= F.lit(as_of_date),
        ]
    else:
        raise ValueError(f"Unknown source table: {table}")
    return frame.withColumn(
        "quality_business_logic", all_of([present_or_valid(check) for check in checks])
    )

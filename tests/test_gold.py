from datetime import date
from decimal import Decimal

import pytest

from medallion.contracts import FIELDS
from medallion.gold import build_gold_tables, eligible_sales
from medallion.gold.sql_resources import render_sql


def _frame(spark, name, rows):
    schema = ", ".join(f"{key} {value}" for key, value in FIELDS[name].items())
    return spark.createDataFrame(rows, schema + ", quality_check_result string")


def _silver(spark):
    def customer(key, quality="PASS"):
        return (
            key, f"Private customer {key}", f"private{key}@example.test",
            "US", date(2020, 1, 1), ("Premium", "Standard", "Basic")[key % 3],
            Decimal("99999.99"), quality,
        )

    def product(key, name, category, quality="PASS"):
        return (
            key, name, category, Decimal("20.00"), Decimal("10.00"), 100, 5, quality
        )

    def order(
        key, customer_id, product_id, day, amount, quantity=1,
        status="Completed", quality="PASS",
    ):
        total = Decimal(amount)
        return (
            key, customer_id, day, product_id, quantity,
            total / quantity, total, status, day, quality,
        )

    return {
        "customers": _frame(
            spark, "customers",
            [customer(key) for key in (1, 2, 3, 4, 7, 8, 9)]
            + [customer(5, "FAIL"), customer(6, "FAIL"), customer(6, "FAIL")],
        ),
        "products": _frame(
            spark, "products",
            [
                product(1, "Widget", "Tools"), product(2, "Gadget", "Tools"),
                product(3, "No sales", "Other"), product(4, "Invalid", "Other", "FAIL"),
                product(5, "Duplicate", "Other", "FAIL"),
                product(5, "Duplicate", "Other", "FAIL"),
            ],
        ),
        "orders": _frame(
            spark, "orders",
            [
                order(1, 1, 1, date(2026, 1, 4), "600.00", quantity=2),
                order(2, 1, 2, date(2026, 1, 5), "400.00"),
                order(3, 2, 1, date(2026, 1, 5), "10.00", quantity=2),
                order(4, 2, 1, date(2026, 1, 6), "20.00"),
                order(5, 3, 1, date(2026, 1, 12), "99.99"),
                order(6, 7, 1, date(2026, 1, 12), "13.00", status="Cancelled"),
                order(7, 8, 1, date(2026, 1, 12), "14.00", quality="FAIL"),
                order(8, 9, 4, date(2026, 1, 12), "15.00"),
                order(9, 5, 1, date(2026, 1, 12), "16.00"),
                order(10, 6, 1, date(2026, 1, 12), "17.00"),
                order(11, 9, 5, date(2026, 1, 12), "18.00"),
                order(12, 404, 1, date(2026, 1, 12), "19.00"),
                order(13, 1, 404, date(2026, 1, 12), "20.00"),
                order(14, 1, 1, date(2026, 1, 12), "21.00", status="Pending"),
            ],
        ),
    }


@pytest.mark.integration
def test_gold_exact_revenue_quality_filters_zero_dimensions_and_segments(spark):
    silver = _silver(spark)
    gold = build_gold_tables(spark, silver)
    eligible = eligible_sales(silver).collect()
    assert {row.order_id for row in eligible} == {1, 2, 3, 4, 5}
    assert sum(row.total_amount for row in eligible) == Decimal("1129.99")
    assert "email" not in eligible[0].asDict()
    assert set(gold) == {
        "sales_by_product", "revenue_by_customer",
        "daily_weekly_trends", "customer_segmentation",
    }
    required = {
        "sales_by_product": {
            "product_id", "product_name", "category", "total_orders",
            "total_revenue", "avg_order_value",
        },
        "revenue_by_customer": {
            "customer_id", "customer_name", "customer_segment", "total_orders",
            "total_revenue", "avg_order_value", "lifetime_value_actual",
        },
        "customer_segmentation": {
            "segment_type", "customer_count", "avg_revenue", "total_revenue",
        },
    }
    for name, fields in required.items():
        assert fields <= set(gold[name].columns)
    products = {row.product_id: row for row in gold["sales_by_product"].collect()}
    assert set(products) == {1, 2, 3}
    assert products[1].total_revenue == Decimal("729.99")
    assert products[1].total_orders == 4
    assert products[1].total_quantity == 6
    assert products[1].avg_order_value == Decimal("182.50")
    assert products[2].total_revenue == Decimal("400.00")
    assert products[3].total_orders == 0
    assert products[3].total_quantity == 0
    assert products[3].total_revenue == products[3].avg_order_value == Decimal("0.00")
    customers = {
        row.customer_id: row for row in gold["revenue_by_customer"].collect()
    }
    assert set(customers) == {1, 2, 3, 4, 7, 8, 9}
    assert customers[1].total_orders == 2
    assert customers[1].customer_name == "Private customer 1"
    assert customers[1].customer_segment == "Standard"
    assert customers[2].customer_segment == "Basic"
    assert customers[3].customer_segment == "Premium"
    assert customers[1].total_revenue == Decimal("1000.00")
    assert customers[1].lifetime_value_actual == Decimal("1000.00")
    assert customers[1].avg_order_value == Decimal("500.00")
    assert customers[1].first_order_date == date(2026, 1, 4)
    assert customers[1].last_order_date == date(2026, 1, 5)
    assert customers[4].first_order_date is None
    assert customers[4].last_order_date is None
    assert customers[4].avg_order_value == Decimal("0.00")
    assert all(row.lifetime_value_actual == row.total_revenue for row in customers.values())

    trends = {
        (row.period_type, row.period_start): row
        for row in gold["daily_weekly_trends"].collect()
    }
    assert len(trends) == 7
    assert trends[("daily", date(2026, 1, 5))].total_revenue == Decimal("410.00")
    assert trends[("daily", date(2026, 1, 5))].total_customers == 2
    weekly = {
        day: row for (grain, day), row in trends.items() if grain == "weekly"
    }
    assert {day: row.total_revenue for day, row in weekly.items()} == {
        date(2025, 12, 29): Decimal("600.00"),
        date(2026, 1, 5): Decimal("430.00"),
        date(2026, 1, 12): Decimal("99.99"),
    }
    assert all(day.weekday() == 0 for day in weekly)
    segments = {
        row.segment_type: row for row in gold["customer_segmentation"].collect()
    }
    assert {name: row.customer_count for name, row in segments.items()} == {
        "High-Value": 1, "Repeat": 1, "One-Time": 1, "Inactive": 4,
    }
    assert segments["High-Value"].total_revenue == Decimal("1000.00")
    assert segments["Repeat"].total_revenue == Decimal("30.00")
    assert segments["Repeat"].avg_order_value == Decimal("15.00")
    assert segments["Repeat"].avg_revenue == Decimal("30.00")
    assert segments["Inactive"].total_revenue == Decimal("0.00")
    assert segments["Inactive"].avg_order_value == Decimal("0.00")
    assert sum(row.customer_count for row in segments.values()) == len(customers)
    for rows in (
        products.values(), customers.values(), segments.values(),
        (row for (grain, _), row in trends.items() if grain == "daily"),
        weekly.values(),
    ):
        rows = list(rows)
        assert sum(row.total_revenue for row in rows) == Decimal("1129.99")
        assert sum(row.total_orders for row in rows) == 5
    for frame in gold.values():
        assert frame.schema["total_revenue"].dataType.simpleString() == "decimal(38,2)"
        assert frame.schema["avg_order_value"].dataType.simpleString() == "decimal(38,2)"
    assert gold["customer_segmentation"].schema["avg_revenue"].dataType.simpleString() == "decimal(38,2)"
    assert "customer_segment" not in gold["customer_segmentation"].columns


@pytest.mark.integration
def test_empty_input_and_nonempty_zero_sales_dimensions(spark):
    empty = {name: _frame(spark, name, []) for name in FIELDS}
    gold = build_gold_tables(spark, empty)
    assert gold["sales_by_product"].count() == 0
    assert gold["revenue_by_customer"].count() == 0
    assert gold["daily_weekly_trends"].count() == 0
    segments = gold["customer_segmentation"].collect()
    assert len(segments) == 4
    assert all(row.customer_count == row.total_orders == 0 for row in segments)
    assert all(
        row.total_revenue == row.avg_order_value == row.avg_revenue
        == Decimal("0.00") for row in segments
    )
    silver = _silver(spark)
    silver["orders"] = empty["orders"]
    populated = build_gold_tables(spark, silver)
    assert populated["sales_by_product"].count() == 3
    segments = {
        row.segment_type: row for row in populated["customer_segmentation"].collect()
    }
    assert segments["Inactive"].customer_count == 7
    assert all(
        segments[name].customer_count == 0 for name in ("High-Value", "Repeat", "One-Time")
    )


@pytest.mark.integration
def test_lazy_builds_do_not_collide_and_threshold_changes_partition(spark):
    silver = _silver(spark)
    first = build_gold_tables(spark, silver, high_value_threshold=Decimal("30.00"))
    second = build_gold_tables(spark, silver, high_value_threshold=Decimal("1000.01"))
    second_segments = {
        row.segment_type: row.customer_count
        for row in second["customer_segmentation"].collect()
    }
    first_segments = {
        row.segment_type: row.customer_count
        for row in first["customer_segmentation"].collect()
    }
    assert second_segments == {
        "High-Value": 0, "Repeat": 2, "One-Time": 1, "Inactive": 4,
    }
    assert first_segments == {
        "High-Value": 3, "Repeat": 0, "One-Time": 0, "Inactive": 4,
    }


@pytest.mark.integration
def test_duplicate_dimension_guard_cannot_fan_out_even_if_misflagged(spark):
    from pyspark.sql import functions as F

    silver = _silver(spark)
    duplicate_product = silver["products"].where("product_id = 1")
    silver["products"] = silver["products"].unionByName(duplicate_product)
    duplicate_customer = silver["customers"].where("customer_id = 1").withColumn(
        "quality_check_result", F.lit("FAIL")
    )
    silver["customers"] = silver["customers"].unionByName(duplicate_customer)
    assert eligible_sales(silver).count() == 0
    gold = build_gold_tables(spark, silver)
    assert {row.product_id for row in gold["sales_by_product"].collect()} == {2, 3}
    assert 1 not in {
        row.customer_id for row in gold["revenue_by_customer"].collect()
    }


@pytest.mark.parametrize(
    "threshold",
    [
        Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity"),
        Decimal("0.001"), Decimal("10000000000000000"), 1000, "1000.00",
    ],
)
def test_threshold_validation_precedes_spark_access(threshold):
    with pytest.raises(ValueError, match="positive DECIMAL"):
        build_gold_tables(None, {}, high_value_threshold=threshold)


def test_sql_resource_strict_substitution():
    sql = render_sql(
        "medallion.gold", "01_sales_by_product.sql",
        identifiers={"valid_products": "c.s.products", "eligible_sales": "safe_view"},
    )
    assert "`c`.`s`.`products`" in sql
    assert "`safe_view`" in sql
    assert "{{" not in sql
    for unsafe in ("x; DROP TABLE y", "x`", "a.b.c.d", "x --comment", ""):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            render_sql(
                "medallion.gold", "01_sales_by_product.sql",
                identifiers={"valid_products": unsafe, "eligible_sales": "safe"},
            )
    with pytest.raises(ValueError, match="replacement names"):
        render_sql(
            "medallion.gold", "01_sales_by_product.sql",
            identifiers={"valid_products": "safe"},
        )
    with pytest.raises(ValueError, match="Unknown SQL resource"):
        render_sql("medallion.gold", "../contracts.py", identifiers={})
    with pytest.raises(ValueError, match="Unsafe SQL decimal"):
        render_sql(
            "medallion.gold", "04_customer_segmentation.sql",
            identifiers={"customer_revenue": "safe"},
            decimals={"high_value_threshold": "1.00 OR 1=1"},
        )

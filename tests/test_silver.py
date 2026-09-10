from decimal import Decimal

import pytest
from pyspark.sql import functions as F

from medallion.contracts import CHECKS
from medallion.silver.create_silver_tables import create_silver_tables
from medallion.silver.report import quality_report

pytestmark = pytest.mark.integration


def test_customers_are_preserved_and_all_duplicate_members_flagged(raw_factory):
    raw = raw_factory(customers=[
        {"customer_id": "1", "email": " USER@EXAMPLE.COM "},
        {"customer_id": "2", "email": None},
        {"customer_id": "3"},
        {"customer_id": "3"},
        {"customer_id": "4", "signup_date": "2026-02-30"},
        {"customer_id": "5", "country": "   "},
        {"customer_id": "6", "customer_segment": "Unknown"},
        {"customer_id": "7", "lifetime_value": "2.001"},
        {"customer_id": "8", "signup_date": "2027-01-01"},
    ])
    rows = create_silver_tables(raw)["customers"].orderBy("customer_id").collect()
    assert len(rows) == 9
    assert rows[0].quality_check_result == "PASS"
    assert rows[0].email == "user@example.com"
    assert rows[0]._raw.email == " USER@EXAMPLE.COM "
    assert rows[0].lifetime_value == Decimal("0.00")
    expected = [
        [], ["completeness"], ["uniqueness"], ["uniqueness"],
        ["type_validation"], ["completeness"], ["business_logic"],
        ["type_validation"], ["business_logic"],
    ]
    assert [row.quality_failures for row in rows] == expected
    assert all(isinstance(row[f"quality_{check}"], bool) for row in rows for check in CHECKS)


def test_whitespace_normalization_includes_tabs_and_unicode(raw_factory):
    blanks = ["\t", "\r\n", "\u00a0", " \t\u00a0 "]
    raw = raw_factory(
        customers=[
            {"customer_id": str(index), "customer_name": blank, "country": blank}
            for index, blank in enumerate(blanks, start=1)
        ] + [
            {"customer_id": "5", "customer_name": "\tExample\u00a0", "country": "\u00a0AE\t"},
            {"customer_id": "6", "email": "user\u00a0@example.com"},
        ],
        products=[
            {"product_id": str(index), "category": blank}
            for index, blank in enumerate(blanks, start=1)
        ] + [{"product_id": "5", "category": "\tBooks\u00a0"}],
        orders=[],
    )
    silver = create_silver_tables(raw)
    customers = silver["customers"].orderBy("customer_id").collect()
    products = silver["products"].orderBy("product_id").collect()
    for row, blank in zip(customers[:4], blanks):
        assert row.customer_name is None and row.country is None
        assert row._raw.customer_name == blank
        assert row.quality_failures == ["completeness"]
    assert all(row.category is None and row.quality_failures == ["completeness"] for row in products[:4])
    assert customers[4].customer_name == "Example"
    assert customers[4].country == "AE"
    assert customers[4].quality_check_result == "PASS"
    assert customers[5].quality_failures == ["business_logic"]
    assert products[4].category == "Books"
    assert products[4].quality_check_result == "PASS"


def test_order_checks_are_independent_and_row_preserving(raw_factory):
    cases = [
        ({}, []),
        ({"customer_id": None}, ["completeness"]),
        ({"product_id": None}, ["completeness"]),
        ({"customer_id": "999"}, ["referential_integrity"]),
        ({"product_id": "999"}, ["referential_integrity"]),
        ({"quantity": "bad"}, ["type_validation"]),
        ({"quantity": "0", "total_amount": "0.00"}, ["business_logic"]),
        ({"total_amount": "21.00"}, ["business_logic"]),
        ({"payment_date": None}, ["business_logic"]),
        ({"order_status": "Pending", "payment_date": None}, []),
        ({"order_status": "Cancelled", "payment_date": None}, []),
        ({"unit_price": "10.001"}, ["type_validation"]),
        ({"payment_date": "2026-01-09"}, ["business_logic"]),
        ({"order_date": "bad"}, ["type_validation"]),
        ({"quantity": "2147483648"}, ["type_validation"]),
    ]
    raw = raw_factory(orders=[
        {"order_id": str(index), **changes}
        for index, (changes, _) in enumerate(cases, start=1)
    ])
    rows = create_silver_tables(raw)["orders"].orderBy("order_id").collect()
    assert len(rows) == len(cases)
    assert [row.quality_failures for row in rows] == [expected for _, expected in cases]
    assert rows[5].quantity is None
    assert rows[5]._raw.quantity == "bad"


def test_referential_existence_is_distinct_from_parent_quality(raw_factory):
    raw = raw_factory(
        customers=[{}, {"customer_id": "1", "email": None}],
        orders=[{}, {"order_id": "1"}],
    )
    silver = create_silver_tables(raw)
    rows = silver["orders"].collect()
    assert len(rows) == 2
    assert all(row.quality_referential_integrity for row in rows)
    assert all(row.quality_failures == ["uniqueness"] for row in rows)


def test_product_business_and_type_checks(raw_factory):
    raw = raw_factory(products=[
        {},
        {"product_id": "2", "cost": "11.00"},
        {"product_id": "3", "stock_quantity": "-1"},
        {"product_id": "4", "price": "not-money"},
        {"product_id": "5", "product_name": None},
    ])
    rows = create_silver_tables(raw)["products"].orderBy("product_id").collect()
    assert [r.quality_failures for r in rows] == [
        [], ["business_logic"], ["business_logic"], ["type_validation"], ["completeness"],
    ]


def test_report_denominators_thresholds_and_empty_inputs(raw_factory):
    raw = raw_factory(customers=[{}, {"customer_id": "2", "email": None}])
    rows = quality_report(create_silver_tables(raw), run_id="test").collect()
    assert len(rows) == 18
    metrics = {(r.table_name, r.check_name): r for r in rows}
    email = metrics["customers", "completeness"]
    assert (email.rows_total, email.rows_passed, email.rows_failed, email.pct_passed) == (2, 1, 1, 50.0)
    assert not email.threshold_passed
    empty = create_silver_tables(raw_factory(customers=[], orders=[], products=[]))
    empty_rows = quality_report(empty, run_id="empty").collect()
    assert len(empty_rows) == 18
    assert all(r.rows_total == 0 and r.pct_passed is None and not r.threshold_passed for r in empty_rows)


def test_report_enforces_strict_threshold_boundaries(spark):
    frames = {}
    for table, count, failure in (
        ("customers", 100, "completeness"),
        ("orders", 1000, "referential_integrity"),
        ("products", 1, None),
    ):
        frame = spark.range(count)
        for check in CHECKS:
            frame = frame.withColumn(
                f"quality_{check}", F.col("id") != 0 if check == failure else F.lit(True)
            )
        frames[table] = frame.withColumn(
            "quality_check_result",
            F.when((F.col("id") == 0) & F.lit(failure is not None), "FAIL").otherwise("PASS"),
        )
    metrics = {
        (row.table_name, row.check_name): row
        for row in quality_report(frames, run_id="boundary").collect()
    }
    assert metrics["customers", "completeness"].pct_passed == 99.0
    assert not metrics["customers", "completeness"].threshold_passed
    assert metrics["orders", "referential_integrity"].pct_passed == 99.9
    assert not metrics["orders", "referential_integrity"].threshold_passed
    assert metrics["products", "uniqueness"].threshold_passed

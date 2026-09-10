import csv
import json
from collections import Counter
from decimal import Decimal

import pytest
from pyspark.errors import AnalysisException
from pyspark.sql import functions as F

from medallion.config import PipelineConfig
from medallion.data_generation.generate_sample_data import generate_sample_data
from medallion.pipeline import run_pipeline
from medallion.storage import CatalogStore, LocalStore

pytestmark = pytest.mark.integration


def generated_source_oracle(source):
    """Independent revenue oracle for generator snapshots with the listed faults."""
    rows = {}
    for table in ("customers", "orders", "products"):
        with (source / f"{table}.csv").open(newline="") as handle:
            rows[table] = list(csv.DictReader(handle))
    customer_counts = Counter(row["customer_id"] for row in rows["customers"])
    order_counts = Counter(row["order_id"] for row in rows["orders"])
    customers = {
        row["customer_id"] for row in rows["customers"]
        if row["email"] and customer_counts[row["customer_id"]] == 1
    }
    products = {row["product_id"] for row in rows["products"]}
    eligible = [
        row for row in rows["orders"]
        if order_counts[row["order_id"]] == 1
        and row["customer_id"] in customers
        and row["product_id"] in products
        and row["order_status"] == "Completed"
    ]
    return len(eligible), sum((Decimal(row["total_amount"]) for row in eligible), Decimal(0))


def test_persisted_pipeline_detects_exact_injections_and_reruns(spark, tmp_path):
    source = tmp_path / "data"
    expected = generate_sample_data(source, customers=100, orders=1000, products=20)
    store = LocalStore(spark, tmp_path / "output")
    config = PipelineConfig(str(source))
    first = run_pipeline(spark, config, store, run_id="first")
    assert first["status"] == "SUCCESS"
    assert first["rows"]["bronze"] == {"customers": 100, "orders": 1000, "products": 20}
    assert first["rows"]["silver"] == first["rows"]["bronze"]
    overall = {
        row["table_name"]: row["rows_failed"]
        for row in first["quality_metrics"] if row["check_name"] == "overall"
    }
    assert overall == {
        name: expected["expected_direct_failing_rows"][name]
        for name in ("customers", "orders", "products")
    }
    assert overall == {"customers": 70, "orders": 420, "products": 0}
    assert first["reconciliation"]["reconciled"]
    breakdown = first["reconciliation"]
    expected_count, expected_revenue = generated_source_oracle(source)
    assert breakdown["eligible_completed_orders"] == expected_count
    assert Decimal(breakdown["eligible_revenue"]) == expected_revenue
    assert sum(breakdown[key] for key in (
        "silver_failed_orders", "excluded_dimension_orders",
        "excluded_status_orders", "eligible_completed_orders",
    )) == 1000
    second = run_pipeline(spark, config, store, run_id="second")
    assert second["rows"] == first["rows"]
    assert second["reconciliation"] == first["reconciliation"]
    assert store.read("bronze", "orders").select("_run_id").distinct().first()[0] == "second"
    assert store.read("silver", "orders").where(F.col("quality_check_result") == "FAIL").count() == 420
    assert json.loads((store.root / "run_manifest.json").read_text())["run_id"] == "second"


def test_operational_failure_does_not_retain_a_success_manifest(spark, tmp_path):
    store = LocalStore(spark, tmp_path / "output")
    store.manifest({"run_id": "previous", "status": "SUCCESS"})
    with pytest.raises(AnalysisException, match="PATH_NOT_FOUND"):
        run_pipeline(spark, PipelineConfig(str(tmp_path / "missing")), store, run_id="failed")
    document = json.loads((store.root / "run_manifest.json").read_text())
    assert document["run_id"] == "failed"
    assert document["status"] == "RUNNING"
    assert "finished_at" not in document


def test_store_refuses_unowned_output_directory(spark, tmp_path):
    (tmp_path / "valuable.txt").write_text("do not overwrite")
    with pytest.raises(ValueError, match="unowned"):
        LocalStore(spark, tmp_path)
    assert (tmp_path / "valuable.txt").read_text() == "do not overwrite"


def test_catalog_store_validates_identifiers_before_executing_sql(spark):
    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        CatalogStore(spark, catalog="workspace;DROP SCHEMA x")

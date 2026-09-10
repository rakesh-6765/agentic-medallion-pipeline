"""Execute and reconcile persisted layer snapshots."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pyspark.sql import DataFrame, SparkSession, functions as F

from medallion.bronze.ingest_all import ingest_all
from medallion.config import PipelineConfig
from medallion.contracts import TABLES
from medallion.gold.create_gold_tables import build_gold_tables
from medallion.silver.create_silver_tables import create_silver_tables
from medallion.silver.report import quality_report
from medallion.storage import Store

LOG = logging.getLogger(__name__)


def _total(frame: DataFrame, column: str) -> Decimal:
    value = frame.agg(F.sum(column).alias("total")).first()["total"]
    return Decimal(0) if value is None else value


def reconcile(silver: dict[str, DataFrame], gold: dict[str, DataFrame]) -> dict:
    orders = silver["orders"]
    passed = orders.where(F.col("quality_check_result") == "PASS")
    customers = silver["customers"].where(F.col("quality_check_result") == "PASS")
    products = silver["products"].where(F.col("quality_check_result") == "PASS")
    linked = passed.join(
        customers.select("customer_id"), "customer_id", "left_semi"
    ).join(products.select("product_id"), "product_id", "left_semi")
    eligible = linked.where(F.col("order_status") == "Completed")
    counts = {
        "source_orders": orders.count(),
        "silver_pass_orders": passed.count(),
        "valid_dimension_orders": linked.count(),
        "eligible_completed_orders": eligible.count(),
    }
    counts["silver_failed_orders"] = counts["source_orders"] - counts["silver_pass_orders"]
    counts["excluded_dimension_orders"] = (
        counts["silver_pass_orders"] - counts["valid_dimension_orders"]
    )
    counts["excluded_status_orders"] = (
        counts["valid_dimension_orders"] - counts["eligible_completed_orders"]
    )
    expected = _total(eligible, "total_amount")
    actual = {
        "sales_by_product": _total(gold["sales_by_product"], "total_revenue"),
        "revenue_by_customer": _total(gold["revenue_by_customer"], "total_revenue"),
        "customer_segmentation": _total(gold["customer_segmentation"], "total_revenue"),
        **{
            f"{grain}_trends": _total(
                gold["daily_weekly_trends"].where(F.col("period_type") == grain),
                "total_revenue",
            )
            for grain in ("daily", "weekly")
        },
    }
    for name, value in actual.items():
        if value != expected:
            raise AssertionError(f"{name} revenue {value} does not reconcile to {expected}")
    for name in ("sales_by_product", "revenue_by_customer"):
        if _total(gold[name], "total_orders") != counts["eligible_completed_orders"]:
            raise AssertionError(f"{name} order counts do not reconcile")
    if _total(gold["customer_segmentation"], "customer_count") != customers.count():
        raise AssertionError("Customer segmentation does not partition valid customers")
    return {
        **counts,
        "eligible_revenue": str(expected),
        "gold_revenue": {name: str(value) for name, value in actual.items()},
        "reconciled": True,
    }


def run_pipeline(
    spark: SparkSession,
    config: PipelineConfig,
    store: Store,
    *,
    run_id: str | None = None,
) -> dict:
    started = datetime.now(timezone.utc)
    run_id = run_id or str(uuid4())
    manifest = {
        "run_id": run_id,
        "status": "RUNNING",
        "started_at": started.isoformat(),
        "as_of_date": config.as_of_date.isoformat(),
        "high_value_threshold": str(config.high_value_threshold),
        "source_dir": config.source_dir,
        "spark_version": spark.version,
        "dashboard_status": "NOT_REQUESTED",
    }
    store.manifest(manifest)
    raw = ingest_all(spark, config.source_dir, run_id=run_id, ingested_at=started)
    bronze = {name: store.write("bronze", name, raw[name]) for name in TABLES}
    bronze_counts = {name: frame.count() for name, frame in bronze.items()}
    LOG.info("Bronze persisted: %s", bronze_counts)
    checked = create_silver_tables(bronze, as_of_date=config.as_of_date)
    silver = {name: store.write("silver", name, checked[name]) for name in TABLES}
    silver_counts = {name: frame.count() for name, frame in silver.items()}
    if silver_counts != bronze_counts:
        raise AssertionError("Silver must retain every Bronze row")
    metrics = store.write("silver", "quality_metrics", quality_report(silver, run_id=run_id))
    computed = build_gold_tables(
        spark, silver, high_value_threshold=config.high_value_threshold
    )
    gold = {name: store.write("gold", name, frame) for name, frame in computed.items()}
    reconciliation = reconcile(silver, gold)
    manifest.update(
        status="SUCCESS",
        finished_at=datetime.now(timezone.utc).isoformat(),
        rows={
            "bronze": bronze_counts,
            "silver": silver_counts,
            "gold": {name: frame.count() for name, frame in gold.items()},
        },
        quality_metrics=[
            row.asDict() for row in metrics.orderBy("table_name", "check_name").collect()
        ],
        reconciliation=reconciliation,
    )
    store.manifest(manifest)
    LOG.info("Pipeline reconciled: %s", reconciliation)
    return manifest

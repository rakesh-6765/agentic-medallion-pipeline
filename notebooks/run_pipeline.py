# Databricks notebook source
# MAGIC %md
# MAGIC # Synthetic e-commerce medallion pipeline
# MAGIC Attach serverless compute. Install the project wheel in the notebook
# MAGIC environment (no `[local]` extras), or run `%pip install -e ..` from this
# MAGIC notebook in a Git folder, then restart Python before running these cells.
# MAGIC Source CSVs must already be uploaded to the selected Unity Catalog volume.
# MAGIC This notebook overwrites only the configured exercise layer tables.

# COMMAND ----------
from datetime import date
from decimal import Decimal

from medallion.config import PipelineConfig
from medallion.pipeline import run_pipeline
from medallion.storage import CatalogStore

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("prefix", "medallion")
dbutils.widgets.text("source_path", "/Volumes/workspace/medallion_source/raw")
dbutils.widgets.text("as_of_date", "2026-01-31")
dbutils.widgets.text("high_value_threshold", "1000.00")

# COMMAND ----------
spark.sql("SET TIME ZONE 'UTC'")
config = PipelineConfig(
    source_dir=dbutils.widgets.get("source_path"),
    as_of_date=date.fromisoformat(dbutils.widgets.get("as_of_date")),
    high_value_threshold=Decimal(dbutils.widgets.get("high_value_threshold")),
)
store = CatalogStore(
    spark,
    catalog=dbutils.widgets.get("catalog"),
    prefix=dbutils.widgets.get("prefix"),
)
manifest = run_pipeline(spark, config, store)
display(store.read("silver", "quality_metrics").orderBy("table_name", "check_name"))
display(store.read("gold", "sales_by_product").orderBy("total_revenue", ascending=False))
display(store.read("gold", "customer_segmentation"))
print(manifest)

# COMMAND ----------
# MAGIC %md
# MAGIC Build the AI/BI dashboard using `src/dashboard/DASHBOARD_GUIDE.md` and
# MAGIC `src/dashboard/dashboard_queries.sql`. Verify the persisted run manifest
# MAGIC is SUCCESS and save your actual workspace/dashboard evidence.

# Unity Catalog ingestion and managed layers

These are setup instructions, **not evidence of a completed Databricks run**.
`notebooks/run_pipeline.py` is the Databricks entrypoint. It uses
`medallion.pipeline.run_pipeline` with `CatalogStore`, and owns credentials,
Spark lifecycle, run metadata, reconciliation, Delta persistence and the success
manifest.

## 1. Choose an authorized catalog and dedicated schemas

Use an existing Unity Catalog catalog exposed by your workspace. Do not assume
you can create a catalog or provision a metastore in Free Edition. Ask the owner
for the required privileges if the operation is denied; do not hard-code broad
`GRANT` statements or credentials.

Review `schema.sql`, replace `REPLACE_WITH_CATALOG` consistently, and adjust
`medallion_source`, `medallion_bronze`, `medallion_silver`, `medallion_gold` if
these are not dedicated to this exercise. The three layer schemas match
`CatalogStore`'s default `prefix="medallion"`. If changing the notebook's `prefix`
widget, change these three layer schema names to `<prefix>_<layer>` consistently.
Run the reviewed statements in a Databricks SQL editor/notebook on supported
compute. `IF NOT EXISTS` is rerunnable but does **not** repair a mismatched schema.
All tables use managed Delta with no custom `LOCATION`; Unity Catalog chooses
the catalog/schema managed storage. The source volume is a separate managed
volume, not a managed-table location.

Typical required privileges (have the workspace administrator verify your exact
setup): `USE CATALOG`, `USE SCHEMA`, `CREATE SCHEMA` to create schemas, `CREATE
VOLUME` to create a volume, `READ VOLUME`/`WRITE VOLUME` for source files,
`CREATE TABLE` for tables, and appropriate `SELECT`/`MODIFY`/ownership rights for
the pipeline's replacement policy. Existing workspace defaults may already
provide these. Dashboard viewers also need the appropriate sharing, data, and
warehouse permissions chosen by the dashboard publisher.

## 2. Upload source CSVs into a volume

The generator supplies `customers.csv`, `orders.csv`, `products.csv` and its
manifest. Upload them with **Catalog → catalog → medallion_source → raw →
Upload**. A run-specific subdirectory is recommended:

```text
/Volumes/YOUR_CATALOG/medallion_source/raw/input_run_001/customers.csv
/Volumes/YOUR_CATALOG/medallion_source/raw/input_run_001/orders.csv
/Volumes/YOUR_CATALOG/medallion_source/raw/input_run_001/products.csv
```

Set the notebook `catalog` widget to the chosen catalog, `prefix` to `medallion`
(or your reviewed replacement), and `source_path` to
`/Volumes/YOUR_CATALOG/medallion_source/raw/input_run_001`. If uploading directly
to the volume root instead, omit `/input_run_001`. The notebook default catalog
`workspace` is only a convenience example; use the catalog actually authorized
in your workspace. The file headers and
their order must match `src/contracts.py`; do not use UI schema inference to
preconvert Bronze. Bronze must preserve raw strings so intentional malformed
values remain auditable.

Use Unity Catalog volumes on Free Edition/serverless. **Do not assume DBFS root,
FileStore, `/dbfs`, DBFS mounts, RDD APIs or a local JVM handle are available.**
External S3 paths are alternatives only when already configured through authorized
Unity Catalog external locations and supported by the parent loader. Local
repository paths are not cloud paths. Upload code/package dependencies separately
using the parent notebook's documented installation method.

## 3. Run the notebook against its existing Spark session

Use the notebook-provided `spark`; do not create or stop a SparkContext, change
Spark master, install local Java, access `.rdd`/`_jvm`, or require `.cache()`.
The parent runner should:

1. Ingest the three files with raw string schemas and source/run metadata.
2. Write managed Bronze tables (`customers`, `orders`, `products`).
3. Build and persist all row-preserving Silver tables and quality reports.
4. Pass typed Silver frames to `build_gold_tables(spark, silver, ...)`.
5. Persist Gold as managed Delta tables and reconcile the persisted eligible order
   counts and exact decimal revenue with all four outputs (daily and weekly
   separately, selecting the `period_type` column).
6. Record the successful run manifest **only after all writes and validations
   succeed**. Individual Delta table writes are transactional; this sequence of
   tables is not an atomic multi-table transaction.

Table persistence is an intentional full-refresh snapshot, conceptually:

```python
# Example only: the parent runner implements naming validation and write policy.
# Execute only for the dedicated exercise catalog/schema after reviewing targets.
frame.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("YOUR_CATALOG.medallion_gold.sales_by_product")
```

Never point managed table storage into the ingestion volume. No merge/upsert or
CDC semantics are claimed. Rerun replaces a layer snapshot rather than appending
duplicate business keys. Preserve run IDs/timestamps in the parent manifest and
metadata according to the parent persistence contract. If a job fails halfway,
do not publish a dashboard mixing run snapshots; inspect/retry the full refresh.

## 4. Verify and build the dashboard

After an actual cloud run, inspect tables in Catalog Explorer and execute counts,
quality checks, revenue reconciliation, zero-sales dimension checks and the
four-segment partition. Use `DESCRIBE DETAIL` on a persisted table to verify
its actual Delta format/storage metadata, not an assumption inferred from local
Parquet tests. Record actual run IDs, paths/table names, runtime, date and results
in project evidence; do not prefill “passed”.

Follow `src/dashboard/DASHBOARD_GUIDE.md` for the exact dataset SQL and
visualization/filter bindings. Do not sum overlapping daily/weekly grains.
Required Gold column names are `avg_order_value` in product/customer outputs,
`customer_name` and the source `customer_segment` in customer revenue, and
derived `segment_type`, `customer_count`, `avg_revenue`, `total_revenue` in
segmentation. Source Premium/Standard/Basic values are distinct from derived
High-Value/Repeat/One-Time/Inactive values. The required dashboard charts are
top-10 product revenue bars, aggregated customer revenue histogram bins, and a
segmentation pie; category and trend charts are additional. Customer names stay
in the Gold table and are never embedded in dashboard datasets.
If downloading or publishing generated HTML, confirm aggregate sales metrics are
appropriate to share; no raw customer PII is required by the renderer.

## Official references

Consulted 2026-09-09:

- [Manage files and upload to volumes](https://docs.databricks.com/aws/en/volumes/volume-files)
- [Create and manage volumes](https://docs.databricks.com/aws/en/volumes/utility-commands)
- [CREATE SCHEMA](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-schema)
- [Serverless limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations)

Cloud provider-specific URLs describe the documented capabilities; confirm your
workspace edition, permissions and current UI before execution.

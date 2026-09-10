from datetime import datetime

from pyspark.sql import DataFrame, SparkSession, functions as F

from medallion.contracts import FIELDS, TABLES


def ingest_table(
    spark: SparkSession,
    source_dir: str,
    table: str,
    *,
    run_id: str,
    ingested_at: datetime,
) -> DataFrame:
    if table not in FIELDS:
        raise ValueError(f"Unknown source table: {table}")
    path = f"{source_dir.rstrip('/')}/{table}.csv"
    frame = (
        spark.read.option("header", "true")
        .option("inferSchema", "false")
        .option("escape", '"')
        .option("multiLine", "true")
        .option("mode", "FAILFAST")
        .option("ignoreLeadingWhiteSpace", "false")
        .option("ignoreTrailingWhiteSpace", "false")
        .option("nullValue", "")
        .csv(path)
    )
    expected = list(FIELDS[table])
    if frame.columns != expected:
        raise ValueError(
            f"{table}.csv header mismatch: expected {expected}, got {frame.columns}"
        )
    return (
        frame.withColumn("_source_file", F.lit(path))
        .withColumn("_ingested_at", F.lit(ingested_at).cast("timestamp"))
        .withColumn("_run_id", F.lit(run_id))
    )


def ingest_all(
    spark: SparkSession, source_dir: str, *, run_id: str, ingested_at: datetime
) -> dict[str, DataFrame]:
    return {
        table: ingest_table(
            spark, source_dir, table, run_id=run_id, ingested_at=ingested_at
        )
        for table in TABLES
    }

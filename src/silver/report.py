from functools import reduce

from pyspark.sql import DataFrame, functions as F

from medallion.contracts import CHECKS, TABLES

THRESHOLDS = {
    "completeness": (99.0, ">"),
    "uniqueness": (100.0, ">="),
    "type_validation": (100.0, ">="),
    "referential_integrity": (99.9, ">"),
    "business_logic": (100.0, ">="),
    "overall": (100.0, ">="),
}


def quality_report(silver: dict[str, DataFrame], *, run_id: str) -> DataFrame:
    reports = []
    for table in TABLES:
        predicates = {check: F.col(f"quality_{check}") for check in CHECKS}
        predicates["overall"] = F.col("quality_check_result") == "PASS"
        counts = silver[table].agg(
            F.count(F.lit(1)).alias("rows_total"),
            *[
                F.count(F.when(predicate, 1)).alias(check)
                for check, predicate in predicates.items()
            ],
        )
        expanded = counts.select(
            "rows_total",
            F.explode(
                F.array(
                    *[
                        F.struct(
                            F.lit(check).alias("check_name"),
                            F.col(check).alias("rows_passed"),
                            F.lit(THRESHOLDS[check][0]).alias("threshold_pct"),
                            F.lit(THRESHOLDS[check][1]).alias("threshold_operator"),
                        )
                        for check in predicates
                    ]
                )
            ).alias("metric"),
        ).select("rows_total", "metric.*")
        percentage = F.when(
            F.col("rows_total") > 0, F.col("rows_passed") * 100.0 / F.col("rows_total")
        )
        passes = F.when(
            F.col("threshold_operator") == ">",
            percentage > F.col("threshold_pct"),
        ).otherwise(percentage >= F.col("threshold_pct"))
        reports.append(
            expanded.withColumn("table_name", F.lit(table))
            .withColumn("run_id", F.lit(run_id))
            .withColumn("rows_failed", F.col("rows_total") - F.col("rows_passed"))
            .withColumn("pct_passed", F.round(percentage, 6))
            .withColumn("threshold_passed", F.coalesce(passes, F.lit(False)))
        )
    return reduce(lambda left, right: left.unionByName(right), reports)

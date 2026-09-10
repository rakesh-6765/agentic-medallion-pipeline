from datetime import date

from pyspark.sql import DataFrame, functions as F

from medallion.contracts import AS_OF_DATE, CHECKS, TABLES
from medallion.silver.checks import (
    add_business_logic,
    add_referential_integrity,
    add_uniqueness,
    all_of,
    prepare_types,
)


def create_silver_tables(
    bronze: dict[str, DataFrame], *, as_of_date: date = AS_OF_DATE
) -> dict[str, DataFrame]:
    prepared = {table: prepare_types(bronze[table], table) for table in TABLES}
    result = {}
    for table in TABLES:
        frame = add_uniqueness(prepared[table], table)
        frame = add_referential_integrity(frame, table, prepared)
        frame = add_business_logic(frame, table, as_of_date)
        frame = frame.withColumn(
            "quality_failures",
            F.filter(
                F.array(
                    *[
                        F.when(~F.col(f"quality_{check}"), F.lit(check))
                        for check in CHECKS
                    ]
                ),
                lambda item: item.isNotNull(),
            ),
        )
        result[table] = frame.withColumn(
            "quality_check_result",
            F.when(
                all_of([F.col(f"quality_{check}") for check in CHECKS]), F.lit("PASS")
            ).otherwise(F.lit("FAIL")),
        )
    return result

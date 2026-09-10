import csv
from datetime import datetime, timezone

import pytest
from py4j.protocol import Py4JJavaError
from pyspark.sql import functions as F

from medallion.bronze.ingest_all import ingest_table
from medallion.contracts import FIELDS

pytestmark = pytest.mark.integration


def write_source(path, header, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def ingest(spark, directory):
    return ingest_table(
        spark, str(directory), "customers", run_id="raw-test",
        ingested_at=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize("name", [" Name ", 'John "JJ" Doe, Jr.', r"Path\Name", "John\nDoe"])
def test_bronze_preserves_lexical_values_and_metadata(spark, tmp_path, name):
    source = ["001", name, " USER@EXAMPLE.COM ", "AE", "bad-date", "Basic", "02.000"]
    write_source(tmp_path / "customers.csv", FIELDS["customers"], [source])
    frame = ingest(spark, tmp_path)
    row = frame.first()
    assert [row[name] for name in FIELDS["customers"]] == source
    assert row._run_id == "raw-test"
    assert row._source_file == str(tmp_path / "customers.csv")
    assert frame.select(F.col("_ingested_at").cast("long")).first()[0] == int(
        datetime(2026, 1, 31, tzinfo=timezone.utc).timestamp()
    )


def test_header_mismatch_is_rejected(spark, tmp_path):
    write_source(tmp_path / "customers.csv", ["customer_id", "wrong"], [["1", "x"]])
    with pytest.raises(ValueError, match="header mismatch"):
        ingest(spark, tmp_path)


def test_malformed_csv_record_is_rejected(spark, tmp_path):
    write_source(tmp_path / "customers.csv", FIELDS["customers"], [["1", "too-few-fields"]])
    with pytest.raises(Py4JJavaError, match="MALFORMED"):
        ingest(spark, tmp_path).collect()

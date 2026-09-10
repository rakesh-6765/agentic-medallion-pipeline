import pytest
from pyspark.sql.types import StringType, StructField, StructType

from medallion.contracts import FIELDS
from medallion.runtime import local_spark


@pytest.fixture(scope="session")
def spark():
    session = local_spark("medallion-tests")
    yield session
    session.stop()


@pytest.fixture
def raw_factory(spark):
    defaults = {
        "customers": {
            "customer_id": "1", "customer_name": "Test Customer",
            "email": "customer@example.com", "country": "AE",
            "signup_date": "2025-01-01", "customer_segment": "Standard",
            "lifetime_value": "0.00",
        },
        "products": {
            "product_id": "1", "product_name": "Test Product", "category": "Books",
            "price": "10.00", "cost": "5.00", "stock_quantity": "10", "reorder_level": "2",
        },
        "orders": {
            "order_id": "1", "customer_id": "1", "order_date": "2026-01-10",
            "product_id": "1", "quantity": "2", "unit_price": "10.00",
            "total_amount": "20.00", "order_status": "Completed", "payment_date": "2026-01-11",
        },
    }

    def factory(**overrides):
        frames = {}
        for table, fields in FIELDS.items():
            rows = [{**defaults[table], **row} for row in overrides.get(table, [{}])]
            schema = StructType([StructField(name, StringType()) for name in fields])
            frames[table] = spark.createDataFrame(
                [tuple(row[name] for name in fields) for row in rows], schema
            )
        return frames

    return factory

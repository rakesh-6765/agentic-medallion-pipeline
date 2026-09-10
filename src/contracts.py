"""Source schemas shared by generation, ingestion, and validation."""

from datetime import date

AS_OF_DATE = date(2026, 1, 31)
SEED = 42
TABLES = ("customers", "orders", "products")
FIELDS = {
    "customers": {
        "customer_id": "int",
        "customer_name": "string",
        "email": "string",
        "country": "string",
        "signup_date": "date",
        "customer_segment": "string",
        "lifetime_value": "decimal(18,2)",
    },
    "orders": {
        "order_id": "int",
        "customer_id": "int",
        "order_date": "date",
        "product_id": "int",
        "quantity": "int",
        "unit_price": "decimal(18,2)",
        "total_amount": "decimal(18,2)",
        "order_status": "string",
        "payment_date": "date",
    },
    "products": {
        "product_id": "int",
        "product_name": "string",
        "category": "string",
        "price": "decimal(18,2)",
        "cost": "decimal(18,2)",
        "stock_quantity": "int",
        "reorder_level": "int",
    },
}
PRIMARY_KEYS = {
    "customers": "customer_id",
    "orders": "order_id",
    "products": "product_id",
}
CHECKS = (
    "completeness",
    "uniqueness",
    "type_validation",
    "referential_integrity",
    "business_logic",
)

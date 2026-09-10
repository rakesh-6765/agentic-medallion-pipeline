"""Output-shape checks independent of the implementation's own SQL tests."""

from medallion.gold.create_gold_tables import build_gold_tables
from medallion.silver.create_silver_tables import create_silver_tables


def test_gold_includes_every_business_column_in_the_brief(spark, raw_factory):
    gold = build_gold_tables(spark, create_silver_tables(raw_factory()))
    required = {
        "sales_by_product": {
            "product_id", "product_name", "category", "total_orders",
            "total_revenue", "avg_order_value",
        },
        "revenue_by_customer": {
            "customer_id", "customer_name", "customer_segment", "total_orders",
            "total_revenue", "avg_order_value", "lifetime_value_actual",
        },
        "customer_segmentation": {
            "segment_type", "customer_count", "avg_revenue", "total_revenue",
        },
        "daily_weekly_trends": {
            "period_type", "period_start", "total_orders", "total_revenue",
        },
    }
    assert set(gold) == set(required)
    for table, columns in required.items():
        assert columns <= set(gold[table].columns), f"{table} must match the exercise contract"

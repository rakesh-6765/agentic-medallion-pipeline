from datetime import date
from decimal import Decimal
import importlib
from importlib.resources import files
import json
from pathlib import Path
import re
import shutil
from uuid import uuid4

import pytest

from medallion.dashboard import (
    dashboard_datasets,
    dashboard_queries,
    render_dashboard,
)


@pytest.fixture
def dashboard_output():
    # Keep test artifacts inside this repository, never system temporary paths.
    directory = Path(__file__).parent / f".dashboard-test-{uuid4().hex}"
    directory.mkdir()
    try:
        yield directory / "dashboard.html"
    finally:
        shutil.rmtree(directory)


def _gold(spark):
    return {
        "sales_by_product": spark.createDataFrame(
            [
                (1, "Widget", "Tools", 2, 3, Decimal("1000.00"), Decimal("500.00")),
                (2, "Gadget", "Tools", 1, 1, Decimal("12.34"), Decimal("12.34")),
                (3, "No sales", "Other", 0, 0, Decimal("0.00"), Decimal("0.00")),
            ],
            "product_id int, product_name string, category string, total_orders long, "
            "total_quantity long, total_revenue decimal(38,2), avg_order_value decimal(38,2)",
        ),
        "revenue_by_customer": spark.createDataFrame(
            [
                (1, "Private customer 1", "Premium", 2, Decimal("1000.00"), Decimal("500.00"), Decimal("1000.00")),
                (2, "Private customer 2", "Basic", 1, Decimal("12.34"), Decimal("12.34"), Decimal("12.34")),
                (3, "Private customer 3", "Standard", 0, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
            ],
            "customer_id int, customer_name string, customer_segment string, total_orders long, "
            "total_revenue decimal(38,2), avg_order_value decimal(38,2), lifetime_value_actual decimal(38,2)",
        ),
        "daily_weekly_trends": spark.createDataFrame(
            [
                ("daily", date(2026, 1, 5), 3, 2, 4, Decimal("1012.34"), Decimal("337.45")),
                ("weekly", date(2026, 1, 5), 3, 2, 4, Decimal("1012.34"), Decimal("337.45")),
            ],
            "period_type string, period_start date, total_orders long, total_customers long, "
            "total_quantity long, total_revenue decimal(38,2), avg_order_value decimal(38,2)",
        ),
        "customer_segmentation": spark.createDataFrame(
            [
                ("High-Value", 1, 1, 2, Decimal("1000.00"), Decimal("1000.00"), Decimal("500.00")),
                ("Repeat", 2, 0, 0, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
                ("One-Time", 3, 1, 1, Decimal("12.34"), Decimal("12.34"), Decimal("12.34")),
                ("Inactive", 4, 1, 0, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
            ],
            "segment_type string, segment_order int, customer_count long, total_orders long, "
            "total_revenue decimal(38,2), avg_revenue decimal(38,2), "
            "avg_order_value decimal(38,2)",
        ),
    }


@pytest.mark.integration
def test_dashboard_resource_queries_execute_and_reconcile(spark, dashboard_output):
    gold = _gold(spark)
    frames = dashboard_datasets(gold)
    rows = {name: frame.collect() for name, frame in frames.items()}
    assert set(rows) == {
        "products", "categories", "trends", "segments", "customer_revenue_distribution",
    }
    assert [row.product_id for row in rows["products"]] == [1, 2, 3]
    categories = {row.category: row for row in rows["categories"]}
    assert categories["Tools"].total_revenue == Decimal("1012.34")
    assert categories["Tools"].total_orders == 3
    assert categories["Other"].total_revenue == Decimal("0.00")
    assert sum(row.total_revenue for row in rows["products"]) == sum(
        row.total_revenue for row in rows["categories"]
    )
    assert {row.period_type for row in rows["trends"]} == {"daily", "weekly"}
    assert sum(row.customer_count for row in rows["segments"]) == 3
    histogram = rows["customer_revenue_distribution"]
    assert [row.customer_count for row in histogram] == [2, 0, 1, 0, 0]
    assert sum(row.customer_count for row in histogram) == 3
    assert sum(row.total_revenue for row in histogram) == Decimal("1012.34")
    assert not {"customer_id", "customer_name", "customer_segment", "email"} & set(
        frames["customer_revenue_distribution"].columns
    )
    result = render_dashboard(gold, dashboard_output, run_id="fixture-run")
    assert result == {
        "path": str(dashboard_output.resolve()), "run_id": "fixture-run",
        "chart_count": 5,
        "dataset_rows": {
            "products": 3, "categories": 2, "trends": 2, "segments": 4,
            "customer_revenue_distribution": 5,
        },
        "total_revenue": "1012.34", "total_orders": 3, "offline": True,
    }
    html = dashboard_output.read_text(encoding="utf-8")
    assert 'id="products-chart"' in html
    assert 'id="categories-chart"' in html
    assert 'id="trends-chart"' in html
    assert 'id="segments-chart"' in html
    assert 'id="histogram-chart"' in html
    assert html.count('role="img"') == 5
    assert html.count('class="bar-row"') == 6
    assert html.count('class="histogram-bin"') == 5
    assert html.count('class="pie-segment"') == 4
    assert 'data-chart-type="histogram"' in html
    assert 'data-chart-type="pie"' in html
    assert 'Customer segmentation pie chart' in html
    assert 'Customer revenue distribution histogram' in html
    assert 'Private customer' not in html
    assert 'Premium' not in html
    assert "1,012.34" in html


@pytest.mark.integration
def test_customer_histogram_boundaries_zero_revenue_and_empty_input(spark):
    gold = _gold(spark)
    amounts = [
        "0.00", "0.01", "499.99", "500.00", "999.99", "1000.00",
        "1499.99", "1500.00", "1999.99", "2000.00", "999999.99",
    ]
    gold["revenue_by_customer"] = spark.createDataFrame(
        [(index, Decimal(amount)) for index, amount in enumerate(amounts)],
        "customer_id int, total_revenue decimal(38,2)",
    )
    rows = dashboard_datasets(gold)["customer_revenue_distribution"].collect()
    assert [row.bin_order for row in rows] == [0, 1, 2, 3, 4]
    assert [row.customer_count for row in rows] == [3, 2, 2, 2, 2]
    assert [row.lower_bound for row in rows] == [
        Decimal("0.00"), Decimal("500.00"), Decimal("1000.00"),
        Decimal("1500.00"), Decimal("2000.00"),
    ]
    assert [row.upper_bound for row in rows] == [
        Decimal("500.00"), Decimal("1000.00"), Decimal("1500.00"),
        Decimal("2000.00"), None,
    ]
    assert sum(row.customer_count for row in rows) == len(amounts)
    assert sum(row.total_revenue for row in rows) == sum(map(Decimal, amounts))
    gold["revenue_by_customer"] = gold["revenue_by_customer"].limit(0)
    empty = dashboard_datasets(gold)["customer_revenue_distribution"].collect()
    assert len(empty) == 5
    assert all(row.customer_count == 0 and row.total_revenue == Decimal("0.00") for row in empty)


def test_dashboard_queries_are_strict_and_package_resources_exist():
    query = dashboard_queries(
        {
            "sales_by_product": "catalog.gold.sales_by_product",
            "revenue_by_customer": "catalog.gold.revenue_by_customer",
            "daily_weekly_trends": "catalog.gold.daily_weekly_trends",
            "customer_segmentation": "catalog.gold.customer_segmentation",
        }
    )
    assert len(query) == 5
    assert all(sql.startswith(("SELECT", "WITH")) for sql in query.values())
    assert all("{{" not in sql and ";" not in sql for sql in query.values())
    assert "`catalog`.`gold`.`sales_by_product`" in query["products"]
    assert "GROUP BY category" in query["categories"]
    assert "`catalog`.`gold`.`revenue_by_customer`" in query["customer_revenue_distribution"]
    assert "COUNT(c.customer_id) AS customer_count" in query["customer_revenue_distribution"]
    assert "c.total_revenue >= b.lower_bound" in query["customer_revenue_distribution"]
    assert "c.total_revenue < b.upper_bound" in query["customer_revenue_distribution"]
    assert "SELECT *" not in "".join(query.values())
    with pytest.raises(ValueError):
        dashboard_queries(
            {
                "sales_by_product": "catalog.gold.sales; DROP TABLE users",
                "revenue_by_customer": "customers",
                "daily_weekly_trends": "trends",
                "customer_segmentation": "segments",
            }
        )
    assert files("medallion.dashboard").joinpath("dashboard_queries.sql").is_file()
    for name in (
        "01_sales_by_product.sql", "02_revenue_by_customer.sql",
        "03_daily_weekly_trends.sql", "04_customer_segmentation.sql",
    ):
        assert files("medallion.gold").joinpath(name).is_file()


def _fake_datasets():
    payload = '</script><script>alert("not executable")</script>&<b>name</b>'
    return {
        "products": [
            {
                "product_id": 1, "product_name": payload, "category": "<Tools>",
                "total_orders": 1, "total_quantity": 1,
                "total_revenue": Decimal("12.34"), "avg_order_value": Decimal("12.34"),
            }
        ],
        "categories": [
            {
                "category": "<Tools>", "total_orders": 1, "total_quantity": 1,
                "total_revenue": Decimal("12.34"),
            }
        ],
        "trends": [
            {
                "period_type": "daily", "period_start": date(2026, 1, 5),
                "total_orders": 1, "total_customers": 1, "total_quantity": 1,
                "total_revenue": Decimal("12.34"), "avg_order_value": Decimal("12.34"),
            }
        ],
        "segments": [
            {
                "segment_type": name, "segment_order": index,
                "customer_count": 1 if name == "One-Time" else 0,
                "total_orders": 1 if name == "One-Time" else 0,
                "total_revenue": Decimal("12.34") if name == "One-Time" else Decimal("0.00"),
                "avg_revenue": Decimal("12.34") if name == "One-Time" else Decimal("0.00"),
                "avg_order_value": Decimal("12.34") if name == "One-Time" else Decimal("0.00"),
            }
            for index, name in enumerate(("High-Value", "Repeat", "One-Time", "Inactive"), 1)
        ],
        "customer_revenue_distribution": [
            {
                "bin_order": index, "revenue_bin": f"{index*500}–<{(index+1)*500}" if index < 4 else "2000+",
                "lower_bound": Decimal(index * 500),
                "upper_bound": Decimal((index + 1) * 500) if index < 4 else None,
                "customer_count": 1 if index == 0 else 0,
                "total_revenue": Decimal("12.34") if index == 0 else Decimal("0.00"),
            }
            for index in range(5)
        ],
    }


def _patch_datasets(monkeypatch, data):
    class FakeRow:
        def __init__(self, value):
            self.value = value

        def asDict(self, recursive=False):
            return self.value

    class FakeFrame:
        def __init__(self, values):
            self.values = values

        def collect(self):
            return [FakeRow(value) for value in self.values]

    module = importlib.import_module("medallion.dashboard.render")
    monkeypatch.setattr(
        module, "dashboard_datasets",
        lambda gold: {name: FakeFrame(rows) for name, rows in data.items()},
    )


def test_html_escaping_accessibility_offline_and_real_filter_logic(monkeypatch, dashboard_output):
    data = _fake_datasets()
    _patch_datasets(monkeypatch, data)
    result = render_dashboard({}, dashboard_output, run_id='<img src=x onerror="bad">')
    html = dashboard_output.read_text(encoding="utf-8")
    assert result["total_revenue"] == "12.34"
    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=&quot;bad&quot;&gt;" in html
    assert '</script><script>alert("not executable")' not in html
    assert "&lt;Tools&gt;" in html
    payload = re.search(
        r'<script id="dashboard-data" type="application/json">(.*?)</script>',
        html, flags=re.DOTALL,
    ).group(1)
    decoded = json.loads(payload)
    assert decoded["products"][0]["product_name"] == data["products"][0]["product_name"]
    assert decoded["products"][0]["total_revenue"] == "12.34"
    assert decoded["trends"][0]["period_start"] == "2026-01-05"
    assert '<label for="category-filter">' in html
    assert '<label for="product-filter">' in html
    assert '<label for="grain-filter">' in html
    assert 'aria-live="polite"' in html
    assert 'scope="col"' in html and 'scope="row"' in html
    assert "row.category === category.value" in html
    assert "String(row.product_id) === product.value" in html
    assert "row.period_type === grain.value" in html
    assert "sum + cents(row.total_revenue)" in html
    assert "textContent" in html and "innerHTML" not in html
    assert '<script src=' not in html and "<link " not in html
    assert "fetch(" not in html and "XMLHttpRequest" not in html
    assert "https://" not in html and "http://" not in html
    assert "connect-src 'none'" in html
    assert "Entire snapshot; product/category filters do not apply." in html
    for rows in decoded.values():
        for row in rows:
            assert not {"email", "customer_id", "customer_name", "customer_segment"} & row.keys()


def test_dashboard_empty_datasets_are_explicit_not_null(monkeypatch, dashboard_output):
    _patch_datasets(monkeypatch, {name: [] for name in _fake_datasets()})
    result = render_dashboard({}, dashboard_output, run_id="empty")
    html = dashboard_output.read_text(encoding="utf-8")
    assert result["total_revenue"] == "0.00"
    assert result["total_orders"] == 0
    assert html.count("No matching data.</p>") == 3
    assert "No valid customers; all four segment counts are zero." in html
    assert html.count('class="pie-segment"') == 4
    assert "Revenue 0.00" in html


def test_top_ten_product_bars_keep_all_products_available_for_filters(monkeypatch, dashboard_output):
    data = _fake_datasets()
    data["products"] = [
        {
            "product_id": index, "product_name": f"Product {index}",
            "category": "Tools" if index % 2 else "Other", "total_orders": 1,
            "total_quantity": 1, "total_revenue": Decimal(26 - index),
            "avg_order_value": Decimal(26 - index),
        }
        for index in range(1, 26)
    ]
    _patch_datasets(monkeypatch, data)
    render_dashboard({}, dashboard_output, run_id="top-ten")
    html = dashboard_output.read_text(encoding="utf-8")
    section = re.search(
        r'<div id="products-chart">(.*?)</section>', html, flags=re.DOTALL
    ).group(1)
    assert section.count('class="bar-row"') == 10
    assert section.count('<th scope="row">') == 25
    assert 'data-visible-limit="10"' in section
    assert "draw('products-chart', rows, 'product_name', 'total_revenue', true, 10)" in html


def test_segmentation_is_an_actual_pie_and_histogram_has_five_ordered_bins(monkeypatch, dashboard_output):
    data = _fake_datasets()
    for row, count in zip(data["segments"], (2, 1, 1, 0)):
        row["customer_count"] = count
    _patch_datasets(monkeypatch, data)
    render_dashboard({}, dashboard_output, run_id="chart-semantics")
    html = dashboard_output.read_text(encoding="utf-8")
    pie = re.search(r'<div id="segments-chart">(.*?)</section>', html, re.DOTALL).group(1)
    assert '<svg class="segmentation-pie"' in pie
    assert 'pathLength="100"' in pie
    arcs = [
        tuple(map(Decimal, values))
        for values in re.findall(r'stroke-dasharray="([\d.]+) ([\d.]+)"', pie)
    ]
    assert arcs == [
        (Decimal("50"), Decimal("50")), (Decimal("25"), Decimal("75")),
        (Decimal("25"), Decimal("75")), (Decimal("0"), Decimal("100")),
    ]
    assert pie.count('<th scope="row">') == 4
    assert 'class="bar-row"' not in pie
    histogram = re.search(r'<div id="histogram-chart">(.*?)</section>', html, re.DOTALL).group(1)
    assert '<svg class="histogram"' in histogram
    assert re.findall(r'data-bin-order="(\d+)"', histogram) == ["0", "1", "2", "3", "4"]
    assert histogram.count('<th scope="row">') == 5


def test_dashboard_requires_an_html_file_target(dashboard_output):
    with pytest.raises(ValueError, match=".html"):
        render_dashboard({}, dashboard_output.parent, run_id="bad-target")

# Gold dashboards: offline HTML and Databricks AI/BI

## Verification status

The local renderer and SQL are implemented, with automated fixture assertions.
**No Databricks dashboard import, publish, workspace query, or cloud execution is
claimed here.** The steps below require execution in your workspace. No Lakeview
JSON is supplied: this project has not verified an official import schema and
does not invent an ostensibly importable artifact. Save a genuine workspace
export after building and verifying the dashboard if an import artifact is needed.

## Local dashboard

```python
from pathlib import Path
from medallion.gold import build_gold_tables
from medallion.dashboard import render_dashboard

gold = build_gold_tables(spark, silver)
result = render_dashboard(gold, Path("output/dashboard.html"), run_id="your-run-id")
print(result)
```

Open the resulting HTML file directly in a browser. It is a single offline file:
inline CSS/JavaScript, populated initial charts, expandable accessible data tables,
no external fonts, libraries, CDN, or network request. A Content Security Policy
also disables network connections. Only aggregated Gold fields are embedded;
customer names, email addresses, customer IDs and order records are not exported.
Do not share the HTML if even these aggregates are confidential.

The return value contains `path`, `run_id`, `chart_count` (5), `dataset_rows`,
`total_revenue` (exact decimal string), `total_orders`, and `offline` (true).
Amounts are source currency units: the source has no currency column and this
implementation does not assume USD or perform currency conversion.

The three required charts are **top-10 product revenue bars**, a **customer revenue
distribution histogram**, and a **customer segmentation pie/donut**. Additional
category bars and daily/weekly trends provide context. The histogram is an actual
SVG column histogram, and the segmentation chart is an actual segmented SVG
donut—not bar charts relabelled as histogram/pie.

**Filter scope is deliberate and visible.** Category and Product controls change
the product bars, category bars, matching-product count, eligible-order count,
and revenue summary. The product dropdown is constrained by the selected category.
The trend grain control selects either daily or Monday-start weekly revenue.
The histogram, trends and customer segments remain the entire snapshot and are explicitly
labelled as unaffected by product/category selection. The Gold trend and segment
tables do not retain product-level detail, so pretending to cross-filter them
would be incorrect. Product bars show the **top 10** matching products, category
bars the top 20 selected categories; their tables include all matching rows.
The product dataset deliberately retains every valid product so filters can
recompute a category's own top 10 rather than filter a pre-truncated global list.
Trends show the latest 20 nonempty periods. A missing
date means no eligible sales, not a generated zero-filled calendar.

Histogram bins are `[0,500)`, `[500,1000)`, `[1000,1500)`, `[1500,2000)`, and
`[2000,+∞)` in source currency units. Lower bounds are inclusive; upper bounds are
exclusive. The last, explicitly labelled column is an overflow bin. All five rows
exist even with zero customers. Every valid customer—including zero-revenue
inactive customers—falls in exactly one bin. Aggregation happens **inside Spark**,
against `revenue_by_customer`; only bin boundaries, labels, counts and total
revenues reach the browser. Automated tests cover zero, values immediately below
boundaries, exact boundaries, overflow and empty input.

The pie uses derived `segment_type` and `customer_count`, displays all four
segments in its legend/data table, and uses a neutral empty ring when the customer
total is zero. It must not use the source `customer_segment` enum.

## Reuse the exact SQL datasets on Databricks

`dashboard_queries.sql` contains five real read-only queries, separated by
`-- dataset: NAME` comments. The `{{...}}` markers are **application placeholders**,
not Databricks parameter syntax. Substitute verified fully-qualified Gold table
names, preferably using the strict renderer:

```python
from medallion.dashboard import dashboard_queries

queries = dashboard_queries({
    "sales_by_product": "YOUR_CATALOG.medallion_gold.sales_by_product",
    "revenue_by_customer": "YOUR_CATALOG.medallion_gold.revenue_by_customer",
    "daily_weekly_trends": "YOUR_CATALOG.medallion_gold.daily_weekly_trends",
    "customer_segmentation": "YOUR_CATALOG.medallion_gold.customer_segmentation",
})
for name, query in queries.items():
    print(f"\n-- {name}\n{query}")
```

Use actual catalog/schema identifiers containing letters, digits or underscores
(leading letter/underscore) with this strict renderer. It intentionally rejects
SQL fragments, backticks, quotes, wildcards, and unsupported identifier characters.
If your workspace names require other characters, manually quote verified names
in the SQL editor rather than weakening substitution validation.

1. Run `notebooks/run_pipeline.py` against the supplied notebook Spark session.
   This entrypoint calls `medallion.pipeline.run_pipeline` with `CatalogStore`.
   The examples above match its default `prefix="medallion"`; change
   `medallion_gold` consistently if using another prefix.
   Verify the successful run manifest and all four managed Gold tables. The local
   Parquet run does **not** prove Delta or cloud execution.
2. In **Dashboards**, create an AI/BI dashboard and select an available SQL
   warehouse. In **Data → Add SQL dataset**, add each printed query separately
   under its exact dataset name: `products`, `categories`, `trends`, `segments`,
   `customer_revenue_distribution`.
   Preview results and confirm the displayed columns contain aggregates only.
3. For correctly filtered **top-10** behavior in the cloud, define an additional
   dataset `products_top10` using the following parameterized query. Also replace
   `products` with the same query **without `LIMIT 10`**. This is the cloud-specific
   parameterized version of the bundled product dataset; the other four SQL
   datasets are unchanged. Using a field filter after a globally limited dataset
   would not recompute the top 10 within a selected category.

   ```sql
   SELECT product_id, product_name, category, total_orders, total_quantity,
          total_revenue, avg_order_value
   FROM YOUR_CATALOG.medallion_gold.sales_by_product
   WHERE (:selected_category = '__ALL__' OR category = :selected_category)
     AND (:selected_product = -1 OR product_id = :selected_product)
   ORDER BY total_revenue DESC, product_id
   LIMIT 10
   ```

   In both datasets, configure `selected_category` as String with default
   `__ALL__`, and `selected_product` as Integer with default `-1`. These sentinels
   mean no restriction; generated category names never equal `__ALL__` and
   generated product IDs are positive. Native `:parameter` values are bound by
   Databricks, never interpolated into SQL. The `{{table_name}}` placeholders in
   bundled SQL are unrelated to these native parameters.

4. Add the following canvas visualizations. Use **SUM** only where stated; do not
   average precomputed averages. Label revenue as “source currency units”.

| Widget title | Dataset | Exact visualization binding |
|---|---|---|
| Top 10 products by revenue | `products_top10` | Bar: category axis `product_name` with `product_id` as an additional grouping/detail field, value axis `SUM(total_revenue)`; sort revenue descending |
| Customer revenue distribution | `customer_revenue_distribution` | Pre-binned histogram: vertical Bar, X `revenue_bin`, Y `SUM(customer_count)`, sorted `bin_order` ascending; preserve the five labelled bins, minimize gaps, label last bin “2000+ (overflow)” |
| Revenue by category | `products` | Bar: category axis `category`, value axis `SUM(total_revenue)`; sort descending |
| Selected revenue | `products` | Counter: `SUM(total_revenue)` |
| Selected eligible orders | `products` | Counter: `SUM(total_orders)` |
| Revenue over time | `trends` | Line: X `period_start` (date), Y `SUM(total_revenue)`, sort date ascending |
| Customer segmentation | `segments` | Pie (or donut style): category/color `segment_type`, angle/value `SUM(customer_count)`; legend and companion table include all four segments |

The cloud histogram uses the Bar renderer for **already binned frequencies**.
Do not apply a histogram transform to the five counts: that would calculate the
distribution of bin counts rather than customer revenues. Add a companion table
with `revenue_bin`, `lower_bound`, `upper_bound`, `customer_count` for exact
boundaries. Likewise add `segment_type`, `customer_count`, `avg_revenue`,
`total_revenue` as a companion pie table so zero-member segments stay visible.
The category chart deliberately binds to `products`, **not** the already rolled-up
`categories` dataset, so both Product and Category filters work without losing
detail. `categories` is a supplemental SQL dataset for reconciliation or an explicitly
unfiltered reference table (`category`, `total_orders`, `total_revenue`).

5. Create a **Category** parameter filter bound to **selected_category in both
   products and products_top10**, and a **Product ID** parameter filter bound to
   **selected_product in both datasets**. Supply actual category names/IDs plus
   the documented all-values sentinels using single-value choices or parameter
   entry widgets available in your workspace UI. Label the defaults “All
   categories (__ALL__)” and “All products (-1)”. These bindings update top-10
   bars, category bars and counters; they do not affect the histogram, trends or
   segments. Do not bind these controls as post-query field filters instead.
6. To guarantee trends never combine overlapping grains, create separate pages:
   - “Daily”: `trends` line widget has a **widget-level static filter**
     `period_type = daily`.
   - “Weekly”: `trends` line widget has a **widget-level static filter**
     `period_type = weekly`.
   Optionally replace the two pages with a **single-select** `trends.period_type` filter
   defaulted to `daily`, but only if the UI can disallow “All” and simultaneous
   values. Never publish a chart that can sum both grains.
7. Label histogram/segment/trend charts “Entire snapshot; product/category filters do not
   apply”. Segments use eligible snapshot revenue and the pipeline's configured
   threshold, not the source lifetime value. The default threshold is 1000.00.
8. Before publishing, test one category, one product, reset, and both grains.
   Verify product revenue = customer revenue = each separate trend grain =
   segment revenue; segment customer counts sum to valid unique customers. Do not
   sum daily and weekly rows together. Check the category query independently
   against the unfiltered product query grouped by category. Histogram counts
   must equal valid customer count, histogram revenue must equal customer revenue,
   and pie counts must sum to the same valid customer count. Verify 500.00 is
   in the second bin, not the first, and every zero-revenue customer is in the
   first bin. Verify no more than 10 product bars after each filter change.
9. Publish with appropriate dataset/warehouse permissions. Record dashboard URL,
   run ID, timestamp, warehouse/runtime, screenshots and actual verification
   results in the parent project's evidence artifacts. Leave them unfilled until
   execution. A genuine export from this dashboard may then be retained as an
   import artifact, with sensitive catalog names reviewed first.

## API / integration contract

`build_gold_tables(spark, silver, *, high_value_threshold=Decimal("1000.00"))`
returns these unpersisted DataFrames:

| Key | Columns |
|---|---|
| `sales_by_product` | `product_id` int, `product_name` string, `category` string, `total_orders` bigint, `total_quantity` bigint, `total_revenue` decimal(38,2), `avg_order_value` decimal(38,2) |
| `revenue_by_customer` | `customer_id` int, `customer_name` string, `customer_segment` string (**source** Premium/Standard/Basic), `country` string, `total_orders` bigint, `total_revenue` decimal(38,2), `lifetime_value_actual` decimal(38,2), `avg_order_value` decimal(38,2), `first_order_date` date, `last_order_date` date |
| `daily_weekly_trends` | `period_type` string (`daily`/`weekly`), `period_start` date, `total_orders` bigint, `total_customers` bigint, `total_quantity` bigint, `total_revenue` decimal(38,2), `avg_order_value` decimal(38,2) |
| `customer_segmentation` | `segment_type` string (**derived** High-Value/Repeat/One-Time/Inactive), `segment_order` int, `customer_count` bigint, `total_orders` bigint, `total_revenue` decimal(38,2), `avg_revenue` decimal(38,2), `avg_order_value` decimal(38,2) |

Customer names are retained only in the required Gold customer table, never in a
dashboard payload. The **source** `customer_segment` is preserved unchanged in
that table; it is not the **derived** `segment_type`. `avg_revenue` is segment
revenue divided by its valid-customer count; `avg_order_value` is eligible revenue
divided by eligible-order count. Empty denominators return exact decimal zero.

Silver must contain the typed source fields from `contracts.py` and
`quality_check_result` strings. PASS orders, PASS customers, PASS products and
`order_status = 'Completed'` are all required. Duplicate dimension members are
excluded, never arbitrarily deduplicated. Zero-sales valid products/customers
remain; inactive customers have null first/last dates and zero money/averages.
Segments always contain four rows, even for an entirely empty input. Thresholds
must be positive, finite `Decimal` values representable exactly as decimal(18,2).

`eligible_sales(silver)` exposes `order_id`, `customer_id`, `product_id`,
`order_date`, `quantity`, `unit_price`, `total_amount`, `product_name`, `category`,
`country`. Use its count/sum for parent reconciliation and exclusions. It has no
temporary views. The builder's SQL views and `dashboard_datasets(gold)` views
are uniquely named, **session-local**, and deliberately retained until session
end. Spark Connect defers name resolution: dropping these views while lazy frames
are still in use could invalidate returned plans. Parent code should finish
actions/persistence before ending the session and reload persisted tables for
long-lived use. No RDD, JVM internals, global views or cache APIs are required.

## Official references

Consulted 2026-09-09; workspace UI and availability can differ:

- [Define AI/BI datasets](https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/datasets)
- [Filter scope, field bindings and widget filters](https://docs.databricks.com/aws/en/dashboards/manage/filters)
- [Native query parameters and filter bindings](https://docs.databricks.com/aws/en/dashboards/manage/filters/parameters)
- [Bar and pie visualization types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)
- [Serverless API/storage limitations and deferred Spark Connect resolution](https://docs.databricks.com/aws/en/compute/serverless/limitations)

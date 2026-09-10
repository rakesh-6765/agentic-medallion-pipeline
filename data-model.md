# Data model and contracts

`src/contracts.py` is the source of truth for ordered CSV headers. Each table has
exactly these fields, in the listed order. Source cells are strings in Bronze;
the types below describe Silver.

| Table / default rows | Ordered fields and Silver types |
|---|---|
| `customers` / 10,000 | `customer_id INT`, `customer_name STRING`, `email STRING`, `country STRING`, `signup_date DATE`, `customer_segment STRING`, `lifetime_value DECIMAL(18,2)` |
| `orders` / 100,000 | `order_id INT`, `customer_id INT`, `order_date DATE`, `product_id INT`, `quantity INT`, `unit_price DECIMAL(18,2)`, `total_amount DECIMAL(18,2)`, `order_status STRING`, `payment_date DATE` |
| `products` / 500 | `product_id INT`, `product_name STRING`, `category STRING`, `price DECIMAL(18,2)`, `cost DECIMAL(18,2)`, `stock_quantity INT`, `reorder_level INT` |

Primary keys: `customers.customer_id`, `orders.order_id`, `products.product_id`.
Foreign keys: `orders.customer_id → customers.customer_id`,
`orders.product_id → products.product_id`. They are validation contracts, not
claims of enforced physical database PK/FK constraints.

All source fields are required except `payment_date`; a Completed order must
nevertheless have a payment date under the business check. Physical typed fields
may be null for invalid rows because Silver retains those rows instead of
asserting impossible `NOT NULL` constraints.

## Layer-added columns

- Bronze: `_source_file STRING`, `_ingested_at TIMESTAMP`, `_run_id STRING`.
  Empty CSV cells become null; malformed lexical values remain unchanged.
  Double-quote CSV escaping matches `csv.writer`; quoted multiline cells are
  supported. CSV quoting syntax is decoded while embedded quotes in actual field
  values are retained.
- Silver retains this metadata and `_raw STRUCT` containing original source
  strings. Unicode edge whitespace (including tabs/NBSP) is removed before
  completeness/type processing, whitespace-only values become null, and email
  is lowercased. Whitespace inside emails is rejected with Unicode-aware matching.
  Parsing/normalization never overwrites raw evidence.
- Silver: `quality_completeness`, `quality_uniqueness`,
  `quality_type_validation`, `quality_referential_integrity`,
  `quality_business_logic` are non-null booleans.
- `quality_failures ARRAY<STRING>` names the failed checks;
  `quality_check_result STRING` is `PASS` only when all five checks pass.

## Gold grains and measures

All revenue uses Completed orders with PASS on the order and both unique
dimensions. Source `customer_segment` is a membership tier
(`Premium`, `Standard`, `Basic`), distinct from the four derived Gold segments.
Source `lifetime_value` is not copied as actual revenue.

| Table | Grain / columns |
|---|---|
| `sales_by_product` | One valid unique product: product ID/name/category; `total_orders`, `total_quantity`, `total_revenue`, `avg_order_value` |
| `revenue_by_customer` | One valid unique customer: `customer_id`, `customer_name`, source `customer_segment`, `country`; `total_orders`, `total_revenue`, `lifetime_value_actual`, `avg_order_value`, `first_order_date`, `last_order_date` |
| `daily_weekly_trends` | One nonempty `(period_type, period_start)`; period type `daily` or `weekly`; `total_orders`, distinct `total_customers`, `total_quantity`, `total_revenue`, `avg_order_value` |
| `customer_segmentation` | Four ordered derived segments: `segment_type`, `segment_order`, `customer_count`, `total_orders`, `total_revenue`, `avg_revenue`, `avg_order_value` |

Counts/summed quantities are BIGINT; aggregate money/averages are
`DECIMAL(38,2)`. Zero-sales valid products/customers retain zero measures;
inactive customer first/last dates are null. Trends do not invent zero-filled
dates. Weekly periods start Monday. Never sum both trend grains or average
precomputed averages to compute a weighted overall average.

Segment precedence is High-Value (revenue ≥ configurable `1000.00` default), Repeat
(≥2 eligible orders), One-Time (1), then Inactive (0). Every valid customer belongs
to exactly one segment; all four segment rows exist even with empty input.

The HTML dashboard uses aggregate-only datasets. Its customer-revenue histogram
groups valid customers into `[0,500)`, `[500,1000)`, `[1000,1500)`, `[1500,2000)`,
and `[2000,∞)` bins, including inactive customers. Customer names and membership
tiers remain in the required customer Gold table and are not embedded in HTML;
only aggregate histogram bins are exported.

## Reporting and manifests

`silver.quality_metrics` contains 18 rows: five checks plus overall for each source
table. Fields: `run_id`, `table_name`, `check_name`, `rows_total`, `rows_passed`,
`rows_failed`, `pct_passed`, `threshold_pct`, `threshold_operator`,
`threshold_passed`. See [quality semantics](data-quality-strategy.md).

The generation manifest records parameters, row counts, CSV hashes/sizes,
injected faults, affected CSV line numbers, duplicate donor mappings, and expected
direct failures. The run manifest records run/config/runtime metadata, status,
layer counts, quality metrics, and reconciled eligibility/revenue. Neither is a
substitute for workspace evidence or participant review.

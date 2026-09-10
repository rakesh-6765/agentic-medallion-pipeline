# Implementation plan

## Scope and decisions

Build a standalone, repeatable batch pipeline, not an extension of the DataOps
agent repository. Use synthetic data only. No credentials, real customer data,
git commits, or invented personal reflections.

The supplied guide contains conflicting counts. This implementation covers all
five named Silver checks (completeness, uniqueness, types, referential integrity,
business logic) and all four named Gold outputs (products, customers, trends,
segments). The specifically enumerated corruptions total **460 injected events**,
not approximately 700. Keep the exact requested file sizes in rows: 10,000
customers, 100,000 orders, 500 products. Replace selected row IDs to introduce
duplicates rather than append records. Flag every member of a duplicated key,
not an arbitrary survivor; this yields 490 directly failing rows for the default
disjoint injections. Record these distinctions in a generation manifest and tests.

## Execution contract

- Python 3.12; shared PySpark DataFrame and SQL transformations.
- Local: managed Java 21 dependency, Spark 4.0, Parquet snapshots, local HTML
  dashboard. This validates transformations and persistence, not Delta transactions.
- Databricks: use the notebook-provided Spark session, Unity Catalog volumes
  (recommended for Free Edition), and managed Delta tables. Also accept accessible
  S3/DBFS source paths on workspaces that support them.
- No claim of a successful cloud run without workspace execution evidence.
- Full-refresh snapshots are intentional. Each run has an ID and UTC timestamp;
  rerunning replaces the same layer tables, rather than accumulating duplicates.
  Multi-table refreshes are not atomic. The current manifest starts as RUNNING;
  SUCCESS is written only after persistence and reconciliation. Dashboard status
  is tracked separately, so pipeline success does not imply a rendered dashboard.
- Fix the synthetic as-of date to 2026-01-31 by default and seed to 42.

## Data contract

Bronze reads every source column as a string, preserving raw lexical values,
including malformed values for Silver validation. Empty CSV cells are represented
as null. Add only source path, ingestion timestamp, and run ID metadata. Reject
missing/unexpected/reordered headers and malformed CSV records.

Silver retains every row and a `_raw` struct of original source values. Trim
strings, convert empty/whitespace-only values to null, and safely parse the declared
integer/date/decimal types. Money uses DECIMAL(18,2); malformed values and excess
fractional precision fail type validation. All source fields are required except
payment_date. All five flags are non-null booleans; `quality_check_result` is PASS
only if all checks pass, and `quality_failures` identifies failing checks.

Uniqueness flags all repeated primary keys. Referential checks test parent-key
existence, not parent quality; null/malformed keys are owned by completeness/types.
Gold additionally requires PASS on the order AND both dimensions, so a duplicate
or invalid dimension cannot multiply or leak into revenue. Publish excluded-order
counts separately from direct Silver failures.

Revenue counts Completed orders only, summing total_amount. Product and customer
outputs include valid dimensions with zero eligible sales. Customer segments are
mutually exclusive, in this order: High-Value (revenue >= 1000.00), Repeat (2+ eligible
orders), One-Time (1), Inactive (0). Threshold is configurable and strictly positive.
Source customer_segment remains Premium/Standard/Basic; it is not the derived
Gold segment_type. Actual lifetime value is eligible revenue in the supplied snapshot, not a claim of
complete historical revenue. Trends contain daily and Monday-start weekly grains;
never sum both grains together.

Quality reports include per-table/check denominators, pass/fail counts and
percentages, plus explicit threshold results. Completeness must be >99%,
referential integrity >99.9%, and uniqueness/types/business logic 100%.
Intentional defects produce failed thresholds without hiding rows or aborting the
exercise; operational/input errors raise exceptions.

## Delivery sequence

1. Establish package, configuration, deterministic schemas and this plan.
2. Build seeded generator, exact fault injection, manifest and generator tests.
3. Build Bronze ingestion, row-preserving Silver checks and quality reporting.
4. Build four Gold SQL outputs, dashboard queries, and actual product bar,
   customer revenue histogram and segmentation pie charts (plus trends).
5. Wire local CLI and Databricks notebook, setup SQL and full-refresh persistence.
6. Validate hand-calculated fixtures, every check, default injection counts,
   cross-layer revenue reconciliation, reruns and full-size local execution.
7. Write setup/design/test/debugging/AI artifacts using actual evidence. Leave
   participant identity, personal judgments and cloud evidence clearly unfilled.

## Validation and completion

Use pytest (the project's test runner), then execute the default-size pipeline.
Inspect persisted Bronze/Silver/Gold, quality report, reconciliation, manifest and
dashboard. Open the dashboard in a browser. Document exact commands and results.
Do not fabricate an imported Databricks dashboard, successful cloud execution,
past prompts, participant decisions or commit history.

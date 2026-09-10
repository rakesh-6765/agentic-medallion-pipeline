-- REVIEW-AND-REPLACE TEMPLATE, not an automatically executed migration.
-- Replace every REPLACE_WITH_CATALOG with your EXISTING, authorized Unity Catalog
-- catalog. Defaults match notebooks/run_pipeline.py with prefix='medallion'.
-- If changing prefix, rename the medallion_bronze/silver/gold schemas consistently.
-- Choose dedicated schema names if these schemas already contain unrelated data.
-- No DROP, TRUNCATE, GRANT, credential, external LOCATION, or DBFS-root dependency.

CREATE SCHEMA IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_source`
COMMENT 'Medallion source-file volumes';
CREATE SCHEMA IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_bronze`
COMMENT 'Full-refresh raw lexical source snapshots with ingestion metadata';
CREATE SCHEMA IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_silver`
COMMENT 'Row-preserving typed snapshots with deterministic quality flags';
CREATE SCHEMA IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_gold`
COMMENT 'Quality-aware Completed-order analytics';

CREATE VOLUME IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_source`.`raw`
COMMENT 'Synthetic CSV ingestion inputs and generation manifest';

-- Gold contracts. The runner creates Bronze/Silver from the shared source
-- contract and writes all layer tables as managed Delta, without LOCATION.
-- These IF NOT EXISTS statements do not alter incompatible existing schemas;
-- inspect them before any intentional full-refresh overwrite.
CREATE TABLE IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_gold`.`sales_by_product` (
    product_id INT,
    product_name STRING,
    category STRING,
    total_orders BIGINT,
    total_quantity BIGINT,
    total_revenue DECIMAL(38, 2),
    avg_order_value DECIMAL(38, 2)
) USING DELTA
COMMENT 'Unique valid products including zero-sales products; eligible orders only';

CREATE TABLE IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_gold`.`revenue_by_customer` (
    customer_id INT,
    customer_name STRING,
    customer_segment STRING,
    country STRING,
    total_orders BIGINT,
    total_revenue DECIMAL(38, 2),
    lifetime_value_actual DECIMAL(38, 2),
    avg_order_value DECIMAL(38, 2),
    first_order_date DATE,
    last_order_date DATE
) USING DELTA
COMMENT 'Unique valid customers with source segment; lifetime value covers only the supplied snapshot';

CREATE TABLE IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_gold`.`daily_weekly_trends` (
    period_type STRING,
    period_start DATE,
    total_orders BIGINT,
    total_customers BIGINT,
    total_quantity BIGINT,
    total_revenue DECIMAL(38, 2),
    avg_order_value DECIMAL(38, 2)
) USING DELTA
COMMENT 'Separate daily and Monday-start weekly grains; never sum both grains';

CREATE TABLE IF NOT EXISTS `REPLACE_WITH_CATALOG`.`medallion_gold`.`customer_segmentation` (
    segment_type STRING,
    segment_order INT,
    customer_count BIGINT,
    total_orders BIGINT,
    total_revenue DECIMAL(38, 2),
    avg_revenue DECIMAL(38, 2),
    avg_order_value DECIMAL(38, 2)
) USING DELTA
COMMENT 'Four exhaustive prioritized segments, including zero-member segments';

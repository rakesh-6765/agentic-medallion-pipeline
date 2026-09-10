-- Select a single grain when plotting or summing; daily and weekly overlap.
WITH periods AS (
    SELECT 'daily' AS period_type, order_date AS period_start,
           order_id, customer_id, quantity, total_amount
    FROM {{eligible_sales}}
    UNION ALL
    SELECT 'weekly' AS period_type,
           CAST(DATE_TRUNC('WEEK', order_date) AS DATE) AS period_start,
           order_id, customer_id, quantity, total_amount
    FROM {{eligible_sales}}
)
SELECT
    period_type,
    period_start,
    COUNT(order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    COALESCE(SUM(CAST(quantity AS BIGINT)), CAST(0 AS BIGINT)) AS total_quantity,
    COALESCE(SUM(total_amount), CAST(0 AS DECIMAL(38, 2))) AS total_revenue,
    CASE WHEN COUNT(order_id) = 0 THEN CAST(0 AS DECIMAL(38, 2))
         ELSE CAST(SUM(total_amount) / COUNT(order_id) AS DECIMAL(38, 2))
    END AS avg_order_value
FROM periods
GROUP BY period_type, period_start

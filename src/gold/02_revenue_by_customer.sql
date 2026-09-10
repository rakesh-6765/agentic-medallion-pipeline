-- Snapshot lifetime value is computed revenue, never the source lifetime_value.
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.country,
    COUNT(e.order_id) AS total_orders,
    COALESCE(SUM(e.total_amount), CAST(0 AS DECIMAL(38, 2))) AS total_revenue,
    COALESCE(SUM(e.total_amount), CAST(0 AS DECIMAL(38, 2))) AS lifetime_value_actual,
    CASE WHEN COUNT(e.order_id) = 0 THEN CAST(0 AS DECIMAL(38, 2))
         ELSE CAST(SUM(e.total_amount) / COUNT(e.order_id) AS DECIMAL(38, 2))
    END AS avg_order_value,
    MIN(e.order_date) AS first_order_date,
    MAX(e.order_date) AS last_order_date
FROM {{valid_customers}} c
LEFT JOIN {{eligible_sales}} e ON e.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_segment, c.country

-- The ordered rules form an exhaustive partition of valid customers.
WITH segment_names AS (
    SELECT 'High-Value' AS segment_type, 1 AS segment_order
    UNION ALL SELECT 'Repeat', 2
    UNION ALL SELECT 'One-Time', 3
    UNION ALL SELECT 'Inactive', 4
),
classified AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        CASE
            WHEN total_revenue >= CAST({{high_value_threshold}} AS DECIMAL(18, 2))
                THEN 'High-Value'
            WHEN total_orders >= 2 THEN 'Repeat'
            WHEN total_orders = 1 THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type
    FROM {{customer_revenue}}
)
SELECT
    s.segment_type,
    s.segment_order,
    COUNT(c.customer_id) AS customer_count,
    COALESCE(SUM(c.total_orders), CAST(0 AS BIGINT)) AS total_orders,
    COALESCE(SUM(c.total_revenue), CAST(0 AS DECIMAL(38, 2))) AS total_revenue,
    CASE WHEN COUNT(c.customer_id) = 0 THEN CAST(0 AS DECIMAL(38, 2))
         ELSE CAST(SUM(c.total_revenue) / COUNT(c.customer_id) AS DECIMAL(38, 2))
    END AS avg_revenue,
    CASE WHEN COALESCE(SUM(c.total_orders), 0) = 0 THEN CAST(0 AS DECIMAL(38, 2))
         ELSE CAST(SUM(c.total_revenue) / SUM(c.total_orders) AS DECIMAL(38, 2))
    END AS avg_order_value
FROM segment_names s
LEFT JOIN classified c ON c.segment_type = s.segment_type
GROUP BY s.segment_type, s.segment_order

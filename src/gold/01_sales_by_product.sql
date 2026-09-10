-- One row per unique PASS product, including products without eligible sales.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(e.order_id) AS total_orders,
    COALESCE(SUM(CAST(e.quantity AS BIGINT)), CAST(0 AS BIGINT)) AS total_quantity,
    COALESCE(SUM(e.total_amount), CAST(0 AS DECIMAL(38, 2))) AS total_revenue,
    CASE WHEN COUNT(e.order_id) = 0 THEN CAST(0 AS DECIMAL(38, 2))
         ELSE CAST(SUM(e.total_amount) / COUNT(e.order_id) AS DECIMAL(38, 2))
    END AS avg_order_value
FROM {{valid_products}} p
LEFT JOIN {{eligible_sales}} e ON e.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category

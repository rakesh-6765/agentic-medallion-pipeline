-- dataset: products
SELECT product_id, product_name, category, total_orders, total_quantity,
       total_revenue, avg_order_value
FROM {{sales_by_product}}
ORDER BY total_revenue DESC, product_id;

-- dataset: categories
SELECT category,
       SUM(total_orders) AS total_orders,
       SUM(total_quantity) AS total_quantity,
       COALESCE(SUM(total_revenue), CAST(0 AS DECIMAL(38, 2))) AS total_revenue
FROM {{sales_by_product}}
GROUP BY category
ORDER BY total_revenue DESC, category;

-- dataset: trends
SELECT period_type, period_start, total_orders, total_customers, total_quantity,
       total_revenue, avg_order_value
FROM {{daily_weekly_trends}}
ORDER BY period_type, period_start;

-- dataset: segments
SELECT segment_type, segment_order, customer_count, total_orders,
       total_revenue, avg_revenue, avg_order_value
FROM {{customer_segmentation}}
ORDER BY segment_order;

-- dataset: customer_revenue_distribution
WITH bins AS (
    SELECT 0 AS bin_order, '0–<500' AS revenue_bin,
           CAST(0 AS DECIMAL(18, 2)) AS lower_bound,
           CAST(500 AS DECIMAL(18, 2)) AS upper_bound
    UNION ALL SELECT 1, '500–<1000', 500.00, 1000.00
    UNION ALL SELECT 2, '1000–<1500', 1000.00, 1500.00
    UNION ALL SELECT 3, '1500–<2000', 1500.00, 2000.00
    UNION ALL SELECT 4, '2000+', 2000.00, CAST(NULL AS DECIMAL(18, 2))
)
SELECT b.bin_order, b.revenue_bin, b.lower_bound, b.upper_bound,
       COUNT(c.customer_id) AS customer_count,
       COALESCE(SUM(c.total_revenue), CAST(0 AS DECIMAL(38, 2))) AS total_revenue
FROM bins b
LEFT JOIN {{revenue_by_customer}} c
    ON c.total_revenue >= b.lower_bound
    AND (c.total_revenue < b.upper_bound OR b.upper_bound IS NULL)
GROUP BY b.bin_order, b.revenue_bin, b.lower_bound, b.upper_bound
ORDER BY b.bin_order;

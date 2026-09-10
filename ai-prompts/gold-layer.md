# Prompt record — Gold

**Origin:** Overall user request U2. No separate human SQL/Gold prompt.

**Assistant-generated delegated prompt summary (A4, Gold scope):** Implement all
four named Gold outputs using shared typed Silver contracts. Require Completed
orders and PASS across orders/customers/products; protect joins from duplicate
dimension fan-out; preserve valid zero-sales dimensions. Compute exact revenue,
snapshot lifetime value, daily/Monday-start weekly trends, and mutually exclusive
segments with High-Value precedence at the configurable 1000.00 default.

**AI output / decisions:** Four SQL resources and a shared Python builder:
`sales_by_product`, `revenue_by_customer`, `daily_weekly_trends`,
`customer_segmentation`. Exact decimal measures and valid-dimension filtering
are explicit; session-local SQL views remain available until lazy plans are
materialized. No runtime SQL is synthesized from free-form user input.

**Validation status:** The analytics agent reported **21 Gold/dashboard tests
passed in 15.53s** after acceptance corrections. The later **63-test unified
suite** passed persisted fixture reconciliation/rerun and the coordinator's
independent acceptance test; see [test evidence](../test-strategy.md).
Initial `grain` was corrected to the required
`period_type`. Coordinator acceptance follow-up also required `avg_order_value`,
customer name/source membership tier, and `segment_type`/`avg_revenue`.
These corrections have focused-test evidence; full-size integration and cloud
execution are not inferred from it.
The subsequent full-default local run independently supplied integration
evidence: **30,077 eligible orders**, **11,720,321.50 revenue** across every Gold
output and each separate trend grain; an independent CSV oracle agreed.
Gold row counts were 500 products, 9,930 customers, 419 trend rows, and 4 segments.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | I used the delivered Gold outputs through the `workspace.medallion_gold` target; no separate aggregation-rule modification or rejection was recorded |
| Rationale and any participant modifications | The outputs support product/customer revenue, trends and segments; filtering to Completed orders and valid dimensions was defined in the AI-generated implementation |
| Independent participant validation | I ran the cloud pipeline and built dashboard charts; hand-calculated fixtures and the 11,720,321.50 revenue oracle are assistant-run local evidence, not my independently measured cloud totals |

# Prompt record — dashboard

**Origin:** Overall user request U2. No separate human visualization prompt.

**Assistant-generated delegated prompt summary (A4, dashboard scope):** Supply
real dashboard SQL datasets, a locally rendered HTML dashboard, tests, and
Databricks AI/BI construction instructions. Consume Gold aggregates, expose
honest product/category and trend-grain controls, and do not claim a cloud
dashboard exists without executing it.

**AI output / decisions:** The initial renderer had four generic charts.
Coordinator acceptance review required the missing customer-revenue histogram
and segmentation pie, plus top-10 product bars. The revised renderer has those
three required views plus category bars and time trends. This correction was an
assistant-generated follow-up task, not participant feedback.

Product/category controls affect product-based summaries; the histogram, trends,
and segments remain snapshot-wide. Daily and weekly periods are not combined.
Customer revenue is binned inside Spark; the renderer does not export customer
names, emails, IDs, or order-level records.

The [dashboard guide](../src/dashboard/DASHBOARD_GUIDE.md) documents real SQL
datasets and widget/filter bindings. An unverified import JSON was not invented;
a genuine export can be saved after a workspace dashboard actually exists.

**Validation status:** The analytics agent reported **21 corrected Gold/dashboard
tests passed in 15.53s**. The histogram bins are aggregated inside Spark, include
inactive zero-revenue customers once, and feed an SVG histogram; segmentation
uses an actual SVG pie/donut plus an accessible four-row table.
The focused tests cover histogram zero/boundary/overflow/empty cases, top-10 bar
limits, donut arc proportions/table rows, exact output schemas, and absence of
customer-level payload. Node `--check` of the embedded JavaScript also passed.
These tests also passed within the **63-test unified suite**. Full-size
rendering later completed with `dashboard_status=SUCCESS` and persisted HTML.
The coordinator's actual browser checks then passed: five charts, real histogram/
donut SVGs, Books filter (83 products/4,962 orders/2,024,922.75), Travel Journal
0330 (1/63/42,902.45), latest 20 Monday-start weekly periods, 9,930 customers in
both histogram/segments, and reset to 500/30,077/11,720,321.50.
See [test strategy](../test-strategy.md). No Databricks dataset
execution, import, publish, URL, or screenshot has been supplied. Local HTML is
not cloud execution evidence.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | Pending |
| Rationale and any participant modifications | Pending |
| Independent participant validation | Pending |

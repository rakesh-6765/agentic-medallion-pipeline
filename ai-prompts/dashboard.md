# Prompt record — dashboard

**Origin:** Overall user request U2, followed by the actual Databricks
query-generation troubleshooting request recorded below.

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
See [test strategy](../test-strategy.md). These are historical local checks;
the participant's later cloud completion report is recorded separately below.

## Participant follow-up: 2026-09-10

**Prompt summary:** The participant said `run_pipeline` had succeeded on
Databricks, supplied the four-table `workspace.medallion_gold` mapping to
`dashboard_queries`, and reported
`ValueError: SQL replacement names must match placeholders exactly`.

**Assistant response and changes:** The exact call generated all five datasets
from current source and the rebuilt wheel. The assistant explained the loaded
template/key mismatch, suggested inspecting module/resource paths and
placeholders, and documented force-reinstallation plus a Python restart.
The shared renderer now reports the loaded resource and missing/unexpected keys.
Regression tests cover older, fully rendered and otherwise mismatched templates.
The assistant also generated ready-to-paste SQL as an alternative to package
refresh. Strict placeholder validation was retained, not bypassed.

**Verified outcome:** 25 targeted Gold/dashboard tests passed; isolated wheel
query generation passed. The precise stale/edited-file cause inside the notebook
was not observed, and the participant did not identify which remediation they
used. They subsequently confirmed the entire project ran end to end on
Databricks and a dashboard was created. No cloud URL/export/metrics were supplied.

**Cleanup:** The duplicate generated SQL and local wheel were removed only after
cloud completion was reported. Canonical SQL templates and rebuild/render
instructions remain in the project.

**Subsequent screenshot review and participant decision:** The participant
supplied four Databricks screenshots, including a published dashboard view.
The assistant identified more than ten products in the top-ten chart, a
category-revenue donut instead of a customer-segmentation pie, and nonnumeric
histogram bin ordering. The participant explicitly accepted this divergence
from the original ask and requested documentation rather than further changes.
The [evidence index](../evidence/README.md) links each screenshot and records the
differences. This is participant acceptance, not evidence of assessor approval
or exact compliance with every original visualization requirement.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | I accepted my cloud dashboard with the three documented differences instead of requesting the proposed visualization corrections |
| Rationale and any participant modifications | I stated this degree of divergence was acceptable; I did not provide an additional technical rationale or claim assessor approval |
| Independent participant validation | I ran the project, created/published the dashboard and supplied four screenshots; detailed cloud metrics, filter interaction and reviewer access are not proven by those screenshots |

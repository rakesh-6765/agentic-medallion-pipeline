# Submission evidence

## Local execution: observed by the implementing assistant

| File | Provenance |
|---|---|
| [local-tests-2026-09-09.xml](local-tests-2026-09-09.xml) | Full suite: 67 tests passed on 2026-09-09; retained from the actual pytest JUnit report |
| [dashboard-tests-2026-09-10.xml](dashboard-tests-2026-09-10.xml) | Follow-up: 25 Gold/dashboard tests passed after the SQL-template diagnostic improvement; overlaps the full suite, so do not add the counts |
| [local-run-manifest.json](local-run-manifest.json) | Actual successful full-size local run `2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7`; only the two machine-specific file paths were normalized to repository-relative paths |
| [local-quality-report.json](local-quality-report.json) | Original 18 quality metrics from that full-size run |
| [local-dashboard.png](local-dashboard.png) | Actual earlier local browser capture, run `c82b5ef7-ad01-41b2-878f-27cdb076f0d6`; unchanged business figures, not a Databricks screenshot |

The JUnit reports retain test names, outcomes and timings. Hostname metadata was
removed for portability. Local Parquet/HTML outputs and environments are
reproducible and were removed during submission cleanup; these compact evidence
files and all test source files remain.

## Databricks execution: reported by the participant

On **2026-09-10**, the participant confirmed running the whole project end to end
on Databricks and creating a dashboard. This is recorded as completed participant
execution, not an assistant-observed cloud run.

The submitted query-generation example targets these Gold tables:

- `workspace.medallion_gold.sales_by_product`
- `workspace.medallion_gold.revenue_by_customer`
- `workspace.medallion_gold.daily_weekly_trends`
- `workspace.medallion_gold.customer_segmentation`

## Databricks dashboard screenshots: supplied and inspected

The participant supplied these screenshots on **2026-09-10**. They show
`Sales Analytics Dashboard 2026-09-10 13:39:25` in Databricks:

| Screenshot | Visible evidence |
|---|---|
| [Dashboard overview](<Screenshot 2026-09-10 at 1.47.12 PM.png>) | Dashboard editor with product revenue, customer revenue distribution and category revenue charts |
| [Customer revenue distribution](<Screenshot 2026-09-10 at 2.13.56 PM.png>) | Five revenue bins plotted by customer count; labels appear in lexical rather than numeric bin order |
| [Sales by category](<Screenshot 2026-09-10 at 2.14.44 PM.png>) | Revenue donut grouped by product category, not customer segment |
| [Product revenue, published view](<Screenshot 2026-09-10 at 2.14.56 PM.png>) | Chart titled "Top 10 Products by Revenue" showing more than ten products; the browser address ends in `/published` |

These screenshots substantiate a rendered dashboard and its published view.
They do not establish reviewer permissions, interactive filter behavior, exact
cloud reconciliation totals or a successful notebook run ID.

### Participant-accepted differences from the original brief

After the assistant identified the following differences, the participant
explicitly stated on **2026-09-10**: "this much divergence from original ask is
accepted" and authorized updating this evidence record.

1. The product revenue chart displays more than the requested top ten products.
2. The supplied donut shows sales by product category rather than customer
   segmentation. No customer-segmentation pie is visible in these screenshots.
3. The histogram bins are not in numeric order; `500–<1000` appears last.

These are accepted by the participant for the submission, not corrections to the
original brief or an assertion of assessor approval. The code still includes
customer-segmentation output and the intended dashboard queries; the screenshots
document the actual cloud visualization configuration without relabeling it.

The candidate information supplied by the participant records approximately
three minutes for execution. This is a reported duration, not an engine/runtime
version or a timestamped execution log. Free Edition is visible in the supplied
screenshots. Cloud run ID, engine/runtime version and metric exports remain to
be supplied if available. Do not reuse local run IDs/figures as cloud evidence. Reviewer access
must be checked separately; a published-view screenshot does not prove access
for someone outside the participant's workspace.

See [your remaining action items](../submission-checklist.md).

# Reflection

First-person draft prepared with AI at my request on 2026-09-10, based on my
recorded actions and project evidence. It distinguishes my execution from the
assistant's implementation/testing and does not claim an independent line-by-line
review or measured learning gain.

## What I built

I delivered an AI-assisted e-commerce medallion pipeline with synthetic customers,
orders and products, Bronze ingestion, Silver data-quality flags, Gold analytics
and a Databricks dashboard. I configured the setup for my `workspace` catalog,
ran the project end to end on Databricks, created and published the dashboard,
and supplied screenshots.

The implementation contains five quality checks and four Gold outputs to cover
the named requirements despite inconsistent summary counts in the exercise.
My cloud dashboard differs from the intended visual design in three ways: it
shows more than ten products, uses a category-revenue donut instead of a
customer-segmentation pie, and orders revenue-bin labels nonnumerically. I
explicitly accepted those differences and kept them visible in the evidence
rather than claiming an exact match to the brief.

## How I used AI across the lifecycle

I supplied the exercise guide and asked for an implementation plan and a separate
project. I used an AI assistant through the Copilot SDK in VS Code, not Cursor.
The assistant generated the implementation, tests and initial documents, performed
local validation, and used delegated agents for generation, analytics and review.
Those delegated prompts were not additional prompts written by me.

My directly recorded work was configuring the Databricks target, running the
project, creating the dashboard, reporting a SQL-placeholder error, supplying
cloud screenshots, accepting the disclosed visualization differences and asking
for submission cleanup and documentation.

## What AI helped with most

AI provided the coordinated implementation and supporting artifacts: deterministic
data with known faults, shared source schemas, row-preserving checks, decimal
aggregations, tests, package setup and debugging records. It also helped explain
the evidence needed for submission and the difference between accepting a
suggestion and merely running generated code.

I have not measured time saved or productivity improvement, so I do not assign a
percentage or claim that the work was faster by a particular amount.

## What AI got wrong

The documented implementation needed corrections. The first generator used
derived personas in the source membership-tier field. Initial Gold/dashboard
outputs did not match all required columns and chart types. Review also found
CSV quote handling and Unicode whitespace issues.

The assistant identified and corrected those implementation problems with
regression tests. I do not present its findings as bugs I independently discovered.
The distinction matters because successful code generation and a passing early
test run did not guarantee that the complete requirement had been met.

## How I validated the output

I ran the project on Databricks and confirmed that it completed and produced a
dashboard. I supplied actual screenshots, including a published view.

The assistant performed the local automated checks: a 67-test full-suite run,
followed by a 25-test Gold/dashboard run after diagnostic improvements. These
counts overlap. The preserved local run reports 490 directly failing source rows
retained in Silver and 11,720,321.50 eligible revenue from 30,077 orders.
I cite these as local assistant-generated test evidence, not as my independently
measured Databricks totals. My screenshots do not prove every data-quality rule,
filter interaction or viewer permission.

## Debugging experience

After the Databricks pipeline ran, I reported the error
`SQL replacement names must match placeholders exactly` from the dashboard
query helper. The assistant verified my four-table mapping locally and in the
wheel, improved diagnostics and offered package-refresh instructions and rendered
SQL. I subsequently confirmed end-to-end completion and dashboard creation.

The record does not identify which remediation I used or the exact mismatched
file in my notebook environment. I therefore do not claim a confirmed stale-wheel
root cause. This incident shows why deployed resource files and import locations
matter, not just the code displayed in a notebook.

## What I would improve next

My next steps would be to capture the actual Databricks run metadata and quality
results alongside the screenshots, and check reviewer access. For a stricter
visual match, I would limit the product chart to ten rows, add the customer
segmentation pie and sort histogram bins by their numeric order.

Before production use, I would review business definitions with stakeholders,
add a publication gate for a consistent multi-table snapshot, plan monitoring
and recovery, and decide whether incremental ingestion is needed. The exercise's
full-refresh implementation is not a claim of production readiness.

## Reusable workflow

I would reuse the following process: provide the brief and schemas, record
assumptions, implement in small layers, validate known faults and hand-calculated
results, review exact output shapes, then test in the target workspace. I would
keep prompt summaries, observed failures and actual evidence together, and
distinguish my decisions from assistant-generated suggestions.

My main takeaway from the documented work is that working execution, correct
business logic, faithful visualizations and adequate evidence are separate checks.
I should not use success in one as proof of all the others.

## Time and evidence limits

I recorded approximately three minutes for execution in my candidate information;
that is an execution-duration statement, not the Databricks Runtime version or
my total project effort. I have not supplied a total effort log, exact cloud run
ID or independently verified cloud reconciliation export.

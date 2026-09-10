# My submission answers

First-person draft prepared with AI at my request on 2026-09-10. The actual
submission form and its field limits have not been provided; these answers follow
the question themes in the exercise guide. They need my final approval before
being submitted as my account.

- **Name:** Rakesh Choudhary
- **Role:** Senior Data Engineer, 4.8 years of experience
- **Project:** E-commerce medallion data pipeline
- **Repository:** https://github.com/rakesh-6765/agentic-medallion-pipeline
- **Primary AI tool:** AI assistant using the Copilot SDK in VS Code

## 1. My understanding of the problem

I needed a pipeline that ingests customer, order and product CSVs, keeps the raw
data available, identifies quality problems, and produces reliable analytics.
Bronze preserves the source values and ingestion metadata. Silver converts types,
checks quality and flags bad rows without deleting them. Gold aggregates only
eligible Completed orders linked to valid customers and products. The dashboard
uses those business outputs rather than raw unvalidated records.

The brief has inconsistent counts, so the implementation covers all five named
quality checks and all four named Gold outputs. The specified data corruptions
amount to 460 injections; because both members of each duplicate pair fail,
local validation identifies 490 directly failing rows. These are different
quantities, not an unexplained attempt to reach approximately 700 defects.

## 2. How I used AI across the lifecycle

I supplied the exercise guide and asked AI for a plan and a separate project.
AI generated the code, tests and initial documentation and performed local
validation and code review. I configured the Databricks catalog, ran the project
end to end, created and published the dashboard, reported a dashboard-query
exception and supplied screenshots. I later asked for cleanup and first-person
documentation based on that record.

I used Copilot in VS Code, not Cursor. The prompt records distinguish my requests
from the assistant's delegated tasks. I am not claiming that I independently
wrote the implementation or performed every test recorded by the assistant.

## 3. Key design and implementation decisions

The delivered design uses raw string Bronze columns so invalid source values are
not lost before validation. Silver retains a raw-value structure and explicit
quality flags, making failures inspectable. All duplicate-key members are flagged
rather than selecting an arbitrary survivor. Gold requires valid dimensions as
well as a valid order, avoiding revenue multiplication from duplicate joins.
Money uses decimal arithmetic, and daily and weekly totals are never added together.

I used these AI-proposed choices for the exercise and changed the setup target to
my `workspace` catalog. The pipeline is a full-refresh batch implementation;
multi-table publication is not atomic. Source currency and complete historical
lifetime value are not inferred from the available fields.

## 4. My testing and validation approach

The assistant's automated validation covers known data defects, type and precision
errors, duplicate and orphan behavior, empty inputs, zero-sale dimensions,
aggregation calculations, output columns and repeatable persisted runs. The
preserved reports show 67 tests in the full suite and 25 in a later focused
Gold/dashboard suite; those suites overlap.

The local full-size run was independently reconciled against a CSV calculation:
30,077 eligible orders and 11,720,321.50 revenue, with 490 bad rows retained in
Silver. I keep those as local test results, not cloud measurements.

My own target-environment validation was successfully running the whole project
on Databricks and creating/publishing the dashboard. I supplied screenshots.
I have not attached a cloud run ID, runtime-version record or detailed cloud
metric export, so I do not claim those were independently verified by the assistant.

## 5. How I validated or challenged AI output

I did not rely only on generated code: I exercised the project in Databricks and
reported the exact dashboard helper call and exception when it failed. The
assistant reproduced that call against source and the wheel successfully, improved
template mismatch diagnostics and offered package-refresh steps and rendered SQL.
I later confirmed successful completion, but the recorded exchange does not
identify which remediation resolved my notebook environment.

The assistant's review also corrected source-tier values, Gold/chart contracts,
CSV quoting and Unicode whitespace behavior. I attribute those findings to AI.
When the assistant reviewed my actual dashboard screenshots, it highlighted
three differences from the brief. I chose to accept and disclose those
differences rather than request additional chart changes.

## 6. What I would improve next

I would add a cloud quality/reconciliation export and run metadata to complement
the screenshots, verify reviewer access and check filter behavior. For an exact
visual match, I would restrict the product chart to ten rows, add a customer
segmentation pie and sort the histogram by numeric bin order.

For production use, I would confirm business rules and thresholds with
stakeholders, define monitoring and recovery, implement a consistent publication
gate and assess incremental ingestion. The current solution is an exercise,
not a claim that production operational requirements are complete.

## 7. Responsible AI use and reusable lessons

I used synthetic data and kept credentials and real customer records out of the
project inputs. Prompt summaries, failures, fixes and evidence remain in the
repository. I distinguish assistant-generated work, my actions and the evidence
for each claim, and I do not report an unmeasured productivity improvement.

The reusable lesson illustrated by this work is to validate at several levels:
source contracts, data quality, calculations, exact output requirements and the
target workspace. A passing local test run does not prove that a deployed
dashboard has the intended configuration or reviewer permissions.

## Disclosure: cloud dashboard differences I accepted

My screenshots show more than ten products in the chart titled "Top 10", a
category-revenue donut rather than customer segmentation, and revenue bins in
nonnumeric order. I explicitly accepted this degree of divergence and asked that
it be recorded. I do not claim that my acceptance changes the original brief or
constitutes approval from the assessment reviewer.

Supporting material: [reflection](reflection.md), [tool workflow](tool-workflow.md),
[decision record](code-review-notes.md), [prompt history](ai-prompts/session-history.md)
and [evidence](evidence/README.md).

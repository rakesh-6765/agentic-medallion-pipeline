# My AI usage summary

First-person draft prepared with AI at my request on 2026-09-10. This describes
recorded work; it is not a claim of unrecorded independent review or final form
submission.

## My contribution

I supplied the exercise brief, requested an implementation plan and a separate
project, and approved the project location. I configured the Databricks catalog
as `workspace`, ran the project end to end, created and published the dashboard,
and supplied four screenshots. I reported the dashboard-query placeholder issue
and later confirmed successful execution.

I accepted the disclosed differences between my cloud dashboard and the brief:
more than ten products, a category-revenue donut instead of customer segmentation,
and nonnumeric histogram-bin ordering. I asked for these to be documented rather
than corrected. I also requested repository cleanup and first-person submission
drafts based on the actual work.

## AI contribution

The coordinating assistant created the plan, package/runtime setup, Bronze and
Silver code, storage/orchestration and core tests. Delegated agents implemented
the generator, Gold SQL, local dashboard and documentation. The assistant ran
local tests, reconciled persisted outputs, checked the browser dashboard, and
used a specialist to review the code.

The first implementation needed corrections to source segment values, Gold
fields/chart types, CSV quoting and Unicode whitespace handling. These were
assistant-originated findings and fixes, not bugs I claim to have independently
found. The prompt records preserve that distinction.

## Decisions and iteration

I used the delivered five-check/four-output design for the exercise; the detailed
rule choices originated with AI. My specific recorded changes/decisions include
the workspace catalog configuration and accepting the cloud visualization
differences. Where no independent technical review or participant rejection was
recorded, the documentation says so instead of manufacturing one.

During dashboard setup, AI verified my table mapping locally and in the wheel,
added resource-path/missing-key diagnostics, documented package refresh and
produced rendered SQL. A stale or modified cloud resource was a possible cause,
not a root cause observed in my workspace. I did not record the exact remediation.

## Validation evidence

- The assistant's historical full suite passed 67 tests.
- A subsequent Gold/dashboard suite passed 25 tests after diagnostic changes;
  this overlaps the full suite and is not an additional 25 distinct end-to-end tests.
- The assistant's local full-size run retained 490 directly failing rows and
  reconciled 30,077 eligible orders to revenue of 11,720,321.50.
- I confirmed end-to-end execution in Databricks and supplied screenshots showing
  an actual published dashboard.

Local counts, revenue and run IDs remain labeled local. I have not supplied a
cloud metric export, exact notebook run ID, engine/runtime version or evidence
of external reviewer access. My recorded three-minute execution duration is not
the Databricks Runtime version or a measure of total exercise effort.

## Responsible use and limitations

I used synthetic data and did not need to share real customer records. I keep AI
task summaries separate from my prompts and the assistant's test work separate
from my execution. I do not claim an AI-authorship percentage, time saved or
productivity improvement without measurements.

The project is an exercise implementation with documented full-refresh limits,
not a production-readiness certification. My acceptance of dashboard differences
is not an assertion that the assessor has accepted those differences.

## Handoff

The source, tests, seed data, lockfile, prompt records and compact evidence remain
in the repository. Reproducible local environments/builds/outputs were removed.
My identity and role come from the candidate details I supplied. First-person
reflection, decision records and [form-answer drafts](submission-answers.md) are
prepared; I still need to approve the wording and complete account-bound actions
listed in [the submission checklist](submission-checklist.md).

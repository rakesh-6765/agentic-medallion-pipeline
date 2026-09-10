# My AI tool workflow

First-person draft prepared with AI at my request from the recorded workflow.
Implementation and local test actions performed by the assistant are attributed
to it rather than presented as my independent work.

## Primary tool and project context

I used an AI assistant through the Copilot SDK in VS Code. I supplied the exercise
guide and asked for an implementation plan and a separate project. I approved
the project location rather than adding this exercise to the neighboring agent
repository. I have not supplied other AI-tool activity.

The assistant used the guide, shared schemas, design notes and existing files as
context. It maintained specialized implementation tasks and prompt summaries.
I do not claim that I wrote those delegated prompts or that all context documents
were automatically loaded by a tool-specific rules engine.

## Requirements and design

I asked AI to turn the brief into a plan and implementation. The delivered design
covers all five named Silver checks and four named Gold outputs. It distinguishes
460 fault injections from 490 directly failing rows, and source membership tiers
from derived customer segments.

I used that implementation for the exercise. I have not documented a separate
review of every design rule; [my decision record](code-review-notes.md) explains
the assumptions and their technical rationale without inventing earlier approvals.

## Code generation

AI generated the Python/PySpark pipeline, SQL templates, deterministic generator,
local dashboard, notebook entrypoint and tests. I configured the setup SQL for
the `workspace` catalog and ran the pipeline in Databricks. I used the delivered
query workflow to build the dashboard, then supplied actual screenshots.

## Validation, testing and data quality

The assistant performed local tests and full-size persistence/reconciliation
checks. The [evidence index](evidence/README.md) preserves the 67-test full-suite
report and later 25-test Gold/dashboard report. Their counts overlap.

The validation approach checks known injected defects, all duplicate members,
row retention, types, referential integrity and business logic. Gold uses only
Completed orders with valid orders and dimensions, avoiding duplicate fan-out.
Independent local CSV calculations cross-check the Spark revenue/count totals.

My target-environment validation was running the whole project successfully on
Databricks and creating/publishing the dashboard. I keep that evidence separate
from local measurements and do not relabel the local test results as cloud tests
I personally executed.

## Debugging and iteration

I reported the dashboard placeholder exception with the exact code I ran. AI
checked that mapping, improved mismatch diagnostics and suggested inspecting the
loaded package resources before reinstalling and restarting notebook Python.
It also supplied rendered SQL as an alternative. I subsequently confirmed
successful end-to-end execution, but did not record the precise remediation used.

The assistant's earlier implementation corrections are retained in
[debugging notes](debugging-notes.md). For the cloud dashboard, I explicitly
accepted the three visual differences it identified; those are documented
instead of silently redefining the original requirements.

## Responsible use and information boundaries

I used synthetic data for this exercise. I would not put real customer PII,
passwords, API tokens, production secrets or unnecessary internal records into
AI prompts. The sample email domain is `example.com`, and local dashboard exports
contain aggregates rather than customer-level data.

My screenshots do contain workspace/browser context. Before sharing outside the
intended assessment audience, I need to check that those details and access
settings are appropriate. I do not equate possession of a screenshot with public
permission to access the workspace.

## Production reuse

I would reuse the separation of contracts, raw ingestion, flagged validation and
quality-aware analytics, along with repeatable tests and explicit evidence.
Before production deployment, I would obtain business-rule approval, define
alerting/recovery and consistent snapshot publication, and assess incremental
processing and access controls. Current full refreshes are not multi-table atomic.

## What worked and what needs improvement

The useful output was an integrated project with code, tests, documentation and
known-fault data rather than disconnected snippets. What needed improvement was
exact acceptance checking: the initial generated fields/charts and two parsing
edge cases required correction. My remaining evidence gap is detailed cloud run
metadata and metric exports; I should also validate reviewer access.

## Tool-specific artifacts

I used Copilot, not Cursor. The analogous artifacts are
[project context](tool-specific/copilot-workflow/project-context.md),
[specification](tool-specific/copilot-workflow/spec.md),
[instructions](tool-specific/copilot-workflow/instructions.md), and
[task breakdown](tool-specific/copilot-workflow/task-breakdown.md).
They describe the actual implementation workflow; they are not invented Cursor
history. Approval of Copilot as the assessment's alternative tool is not evidenced
in this repository and must be confirmed with the organizer.

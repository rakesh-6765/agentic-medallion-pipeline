# Code-review notes

## Review provenance

This document records **assistant inspection and implementation decisions**.
Participant execution, catalog changes and explicit dashboard-divergence
acceptance are recorded below; no independent line-by-line code review is claimed.
Test outcomes are linked to
[test evidence](test-strategy.md), not invented reviewer sign-offs.

Latest status: the **code-review specialist found two verified bugs in staged
code**. The coordinator corrected both and added regressions; the final suite
passed **67 tests in 28.97s**, and the full run/wheel succeeded. The targeted
specialist recheck confirmed both findings resolved and found no significant
issues in those fixes. This was not an initially clean review.
An initial commit now exists; this finalization created no new commits.
Specialist findings are distinct from participant
review or approval.

Documentation inspection read the plan, contracts, configuration, CLI/runtime,
pipeline/storage, Bronze/Silver implementation, generator notes/source, and
Gold/dashboard contracts. Files owned by other implementing agents were not
modified by the documentation agent.

## Concrete integration findings

| Finding at inspection | Consequence | Disposition |
|---|---|---|
| Initial generator serialized `Inactive`, `One-Time`, `Repeat`, `High-Value` instead of required `Premium`, `Standard`, `Basic` | Generated customers would all fail business logic rather than the expected 70 direct failures | Generator corrected and snapshot regenerated; generator and persisted Spark fixture checks passed within the unified 63 tests |
| Initial Gold trends exposed `grain`; pipeline required `period_type` | Reconciliation would fail on an unresolved column | Gold/dashboard aligned to `period_type`; persisted fixture reconciliation/rerun passed within the unified 63 tests |
| Coordinator acceptance review found missing exact Gold aliases/customer fields | Working aggregations still did not satisfy the requested output contract | Corrected SQL and independent `tests/test_acceptance.py` passed within the unified 63 tests |
| Initial dashboard omitted required customer-revenue histogram and segmentation pie | Generic charts did not fulfill the requested visualizations | Renderer now includes histogram/pie and top-10 product bars; focused 21/unified 63 tests and actual browser visual/filter/reset checks passed |
| Specialist: Spark's default backslash escape disagreed with `csv.writer` doubled quotes | A valid field such as `John "JJ" Doe` could be corrupted on Bronze ingestion | Explicit double-quote escape and quoted multiline support; doubled-quote/newline regressions passed within final 67 tests; specialist confirmed resolved |
| Specialist: Spark `trim` did not remove tabs/NBSP and email whitespace matching was not Unicode-aware | Whitespace-only required fields could evade completeness; invalid email whitespace could evade the business rule | Unicode edge normalization/raw preservation and email whitespace rejection; regressions passed within final 67 tests; specialist confirmed resolved |

These are observed code mismatches, not fabricated failed-run output. Update
their disposition only after inspecting the correction and its validation.

### Actual assistant-level rejected suggestion

A sibling agent proposed expanding Silver's enum to accept the accidentally
serialized Gold personas. The coordinator rejected that proposal because the
source contract explicitly requires Premium/Standard/Basic; the generator was
corrected instead. This is recorded AI-to-AI review, not invented participant
acceptance/rejection. The first-person records below distinguish my recorded
decisions from implementation choices made by the assistant.

## Assistant review checklist

| Area | Inspection conclusion / gate |
|---|---|
| Raw preservation | CSV doubled quotes/quoted newlines and Unicode normalization/raw/email regressions passed within final 67 tests |
| Duplicate safety | All members flagged; distinct referential key sets and valid unique Gold dimensions avoid fan-out |
| SQL boundaries | Identifiers and decimal placeholders are validated; template SQL is not arbitrary model-generated runtime SQL |
| Financial measures | Decimal money and Completed/PASS eligibility; reconciliation required before pipeline success |
| Operational safety | Explicit Parquet/Delta stores, ownership check, RUNNING/SUCCESS states; multi-table atomicity not claimed |
| Dashboard meaning | Product/category filters cannot honestly filter preaggregated snapshot-wide histogram/trends/segments |
| Data exposure | Synthetic sources only; rendered aggregates do not need names/email/order details |
| Verification boundary | Full suite 67 passed, subsequent SQL/dashboard suite 25 passed; both specialist findings resolved; cloud run/dashboard completion reported by participant on 2026-09-10, detailed cloud evidence pending |

## Participant decision register

Record your judgment of significant AI suggestions:

- **Accepted:** Used the suggestion unchanged; explain why it fits the requirement.
- **Changed:** Modified the suggestion; describe the change and its reason.
- **Rejected:** Did not use the suggestion; explain why and what you used instead.

Not every activity needs all three categories. If no suggestion was rejected,
say so only if that reflects your actual review. An assistant correcting its own
code is not a participant rejection. Example wording is not evidence of a decision.

### Decisions supported by the recorded interaction

| Decision / action | Recorded disposition | Evidence and limits |
|---|---|---|
| Build a standalone project with an implementation plan | Accepted / explicitly requested | Participant requested a plan and separate solution and approved the proposed project location |
| Configure setup SQL for the actual catalog | Changed | The participant's existing staged change replaced `REPLACE_WITH_CATALOG` with `workspace`; their dashboard query example also used `workspace.medallion_gold` |
| Use the delivered pipeline and dashboard workflow on Databricks | Used and validated end to end | Participant confirmed the complete project ran and a dashboard was created; this does not imply detailed acceptance of every rule or edge case |
| Finalize submission documents and remove generated local clutter | Accepted / explicitly authorized | Participant requested completion of pending documentation, identification of their action items and cleanup |
| Keep the current cloud dashboard instead of applying the proposed chart corrections | Accepted current differences / declined further changes | I explicitly accepted the displayed product count, category donut and bin ordering; these remain disclosed rather than claimed compliant |

### My technical decision record

First-person draft requested by me on 2026-09-10. "Used as delivered" records my
use of the implementation, not an invented independent approval of each rule.
The technical explanations describe the delivered behavior. They do not imply
that I originally specified those choices or independently tested each edge case.

| Decision | Accepted / changed / rejected | Participant rationale / change |
|---|---|---|
| Cover five Silver checks and four Gold outputs | Used as delivered | I ran the implementation covering all named checks/outputs, rather than only the inconsistent summary counts; AI selected this scope |
| Treat 460 injections as 490 directly flagged rows | Used as delivered | I retain the distinction: replacing 30 IDs creates duplicate pairs whose 60 members fail uniqueness; the 490 total comes from local validation, not a cloud measurement I supplied |
| Reject all duplicate members rather than keep one | Used as delivered | The pipeline flags every repeated key member and retains the raw rows; I have not documented a separate deduplication-policy review |
| Require valid dimensions and Completed status for Gold | Used as delivered | Gold excludes invalid joins and non-Completed orders; I have not supplied independent stakeholder approval of this business definition |
| Segment priority and 1000.00 threshold | Used as delivered | The exercise implementation applies High-Value first, then Repeat, One-Time and Inactive; the threshold is configurable and is not claimed to be a production policy |
| Local Parquet measurements vs cloud Delta run | Ran the cloud target | I confirmed the Databricks end-to-end run and supplied published-dashboard screenshots; assistant-run local tests and totals remain separately attributed |
| Source/model assumptions and currency interpretation | Used the synthetic exercise scope | I am not claiming currency conversion, tax/refund handling or complete historical lifetime value from this source snapshot |
| Generated code, tests, dashboard, and documentation | Used AI output; configured and executed the cloud project | I changed the catalog to `workspace`, reported the dashboard error, supplied screenshots and authorized documentation/cleanup; I do not claim a line-by-line independent code review |
| Proposed corrections to the cloud visualizations | Accepted the existing divergence instead | I explicitly accepted more than ten displayed products, category rather than segment donut grouping, and nonnumeric bin order; I did not give a further technical rationale |

No additional participant rejection is invented to fill a category. The
activity-specific [prompt records](ai-prompts/session-history.md) use the same
attribution; this draft still needs my final wording approval before submission.

# Code-review notes

## Review provenance

This document records **assistant inspection and implementation decisions**.
No participant review or independent human approval has been supplied.
Test outcomes are linked to
[test evidence](test-strategy.md), not invented reviewer sign-offs.

Latest status: the **code-review specialist found two verified bugs in staged
code**. The coordinator corrected both and added regressions; the final suite
passed **67 tests in 28.97s**, and the full run/wheel succeeded. The targeted
specialist recheck confirmed both findings resolved and found no significant
issues in those fixes. This was not an initially clean review.
There are no reported commits. Specialist findings are distinct from participant
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
acceptance/rejection. Participant fields below remain pending.

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
| Verification boundary | Final post-fix suite 67 passed and full-default rerun SUCCESS; earlier browser PASS and saved screenshot; both specialist findings resolved; cloud unverified |

## Participant decision register

These fields belong to the participant. Blank/pending is intentional.

| Decision | Accepted / changed / rejected | Participant rationale / change |
|---|---|---|
| Cover five Silver checks and four Gold outputs | Pending | Pending |
| Treat 460 injections as 490 directly flagged rows | Pending | Pending |
| Reject all duplicate members rather than keep one | Pending | Pending |
| Require valid dimensions and Completed status for Gold | Pending | Pending |
| Segment priority and 1000.00 threshold | Pending | Pending |
| Local Parquet proof vs unexecuted cloud Delta path | Pending | Pending |
| Source/model assumptions and currency interpretation | Pending | Pending |
| Generated code, tests, dashboard, and documentation | Pending | Pending |

No approval is inferred from the user's authorization to create a project.

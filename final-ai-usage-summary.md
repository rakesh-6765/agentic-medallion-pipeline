# AI usage summary

**Status: implementation record, not final participant sign-off.**

## Actual inputs and tool

The user supplied an AI Capability Exercise guide, requested
“Create a implementation Plan, Build this solution in a separate project”,
and approved the standalone path. The primary tool was an AI assistant using
the Copilot SDK in VS Code. Cursor was not used; the equivalent project artifacts
are explained in [tool workflow](tool-workflow.md).

## Work performed with AI

| Responsibility | Actual AI contribution |
|---|---|
| Coordinating assistant | Plan/contracts, package/CLI/runtime, Bronze, Silver, storage, orchestration, core tests, environment debugging |
| Generator agent | Deterministic generator, explicit fault injection/manifests, full source files, generation tests/notes |
| Gold/dashboard agent | SQL aggregations, eligible-sales contract, local dashboard and cloud dashboard instructions, targeted tests |
| Documentation agent | Root technical/workflow artifacts, prompt summaries, evidence boundaries, participant-pending fields |

Delegated prompts were assistant-authored, not additional user requests.
Their summaries and known outcomes are in [session history](ai-prompts/session-history.md)
and the layer-specific prompt files. No unrecorded past prompts, commits,
participant reviews, or cloud execution have been fabricated.

## Validation and limitations

The final post-fix unified local suite passed **67 tests in 28.97s**, with zero
failures/errors/skips in the inspected JUnit report. It includes corrected
generation, core checks, Gold/dashboard tests, independent exact-column and
strict-threshold acceptance, and persisted Spark fixture/rerun validation.
Earlier focused results and real failures remain recorded in
[test strategy](test-strategy.md) and [debugging notes](debugging-notes.md);
overlapping test counts are not added together.

The final full-default CLI run `2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7` succeeded
with **30,077 eligible orders**,
**11,720,321.50 reconciled revenue**, **490 direct failed source rows**, and
pipeline/dashboard `SUCCESS`. The manifest, 18-row quality report, and HTML
persisted; an independent CSV oracle matched count/revenue. Actual browser
visual/filter/reset checks passed, including the histogram, segmentation donut,
Books/product filters, weekly periods, and customer coverage. Exact observations
are recorded in test strategy. These are local results, not cloud execution.

Specialist review subsequently found two verified bugs: incompatible CSV quote
escaping and incomplete Unicode whitespace handling. The coordinator corrected
Bronze escaping and Silver normalization/email matching while preserving raw
evidence, and added regressions, including valid quoted newlines. The final **67-test**
suite, full-default rerun, and wheel rebuild succeeded. Earlier 63-test results
and the interim 66-test expectation are historical. The targeted specialist
recheck confirmed both findings resolved. The screenshot retains the earlier
verified run ID; the final run has the same business figures.

The assistant resolved count ambiguities, selected all-member duplicate handling,
explicit Gold eligibility, deterministic dates/thresholds, and separate local/
cloud storage. These are implementation decisions; the user's path approval
does not constitute acceptance of every technical choice.

An actual assistant-level rejection is recorded: the coordinator rejected a
sibling's suggestion to weaken Silver's source enum and corrected the generator
instead. This must not be attributed to the participant.

## Required participant completion

- Identity/role and actual involvement: **Pending**.
- Accepted/changed/rejected AI suggestions and reasons: **Pending**.
- Independent code/results review: **Pending**.
- Personal reflection and any time/effort accounting: **Pending**.
- Databricks run/dashboard evidence and actual permissions: **Not supplied**.
- Final submission approval: **Pending**.

No percentage of AI authorship, productivity gain, saved time, or participant
learning is claimed without evidence. Specialist review found the two issues
described above; regressions passed and the specialist confirmed both resolved.
No git commits are claimed.

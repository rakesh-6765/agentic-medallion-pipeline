# Tool workflow

## What was actually used

The primary tool was an **AI assistant using the Copilot SDK in VS Code**, with
file inspection, patching, terminal commands, official documentation lookup, and
delegated implementation agents. The assistant—not the participant—selected the
implementation details recorded in [design notes](design-notes.md).
Exact model/version metadata is not asserted.

The user supplied the guide, requested a plan plus a separately located solution,
and approved the proposed project path. No layer-specific human prompts,
participant code-review decisions, or personal reflections were supplied.
[Session history](ai-prompts/session-history.md) separates those user inputs from
assistant-authored task summaries.

## Execution pattern

1. Clarify scope/location; record the approved standalone boundary.
2. Define schemas and explicitly resolve conflicting requirement counts.
3. Delegate deterministic generation and Gold/dashboard work in separate scopes.
   The coordinating assistant owns packaging, runtime, Bronze, Silver,
   orchestration, and integration tests.
4. Restore dependencies, smoke-test Spark, and run focused tests. Investigate
   actual failures rather than claiming that generated code is already verified.
5. Delegate documentation using actual prompts, inspected code, and test evidence.
6. Reconcile persisted outputs, validate the dashboard, and distinguish local
   proof from still-required Databricks evidence.
7. Hand over participant-owned review/reflection fields; do not fill them by proxy.

## Equivalent project guidance

The guide's Cursor-specific artifacts do not apply because Cursor was not used.
Their purpose is covered without falsely claiming a Cursor session:

- [Project context](tool-specific/copilot-workflow/project-context.md)
- [Specification](tool-specific/copilot-workflow/spec.md)
- [Working instructions](tool-specific/copilot-workflow/instructions.md)
- [Task breakdown](tool-specific/copilot-workflow/task-breakdown.md)

These are human-readable Copilot workflow artifacts, **not** a claim that this
directory was automatically loaded by VS Code, Copilot, or a Cursor rules engine.
They were written during implementation; they are not reconstructed pre-session
instructions.

## Provenance and guardrails

- Prompt logs are summaries where indicated, as permitted by the user; summaries
  of delegated prompts are labelled assistant-generated.
- Only synthetic data is used. No credentials or real customer information belong
  in prompts, CSVs, HTML, or repository evidence.
- Terminal/test evidence is credited to the implementing assistant/agent. It does
  not imply independent participant review.
- `uv.lock` records dependencies. Git initialization, if present, does not imply
  a commit, staged submission, or participant approval.
- Local Parquet and offline HTML are never described as cloud Delta or a published
  Databricks dashboard.

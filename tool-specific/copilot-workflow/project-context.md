# Copilot workflow — project context

This artifact records project context for the **AI assistant using the Copilot SDK
in VS Code**. It is not a Cursor file and does not claim automatic instruction
loading. It was written during implementation, not before the user's request.

## Authorized project

Standalone root:
`/Users/rakesh-maf/Documents/repos/databricks-medallion-pipeline`.
Do not integrate it into the neighboring agent repository. The user approved
this location after requesting a plan and complete separate solution.
Participant identity/role and Databricks credentials were not supplied.

## System shape

- Python package `medallion`, source under `src/`; Python 3.12 local environment.
- Seeded synthetic e-commerce CSVs; no real customer data or services.
- Raw Bronze → complete-row typed Silver → four SQL Gold outputs.
- Local Spark/Parquet/HTML and notebook-supplied Spark/managed Delta are distinct.
- Plan and acceptance details: [`implementation-plan.md`](../../implementation-plan.md),
  [`requirements-analysis.md`](../../requirements-analysis.md).
- Contracts and safeguards: [`data-model.md`](../../data-model.md),
  [`data-quality-strategy.md`](../../data-quality-strategy.md).

## Evidence boundary

Inspect/test actual behavior before claiming success. Keep agent-generated task
summaries distinct from user prompts. Participant decisions/reflections and cloud
execution remain pending until provided or actually performed with authorization.
Never infer a participant name from the filesystem path.

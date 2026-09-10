# Submission checklist and participant action items

Updated **2026-09-10**. My project implementation, repository cleanup and
first-person submission drafts are complete. AI prepared the drafts at my request
using my supplied details and recorded actions; my final approval and the
account-bound submission actions below have not been performed by the assistant.

## Completed

- [x] Generator, three seed CSVs and deterministic generation manifest.
- [x] Raw Bronze ingestion, five Silver checks, retained bad rows and quality report.
- [x] Four Gold outputs, dashboard SQL and required bar/histogram/pie visualizations.
- [x] Databricks pipeline and dashboard: participant confirmed end-to-end completion.
- [x] Source/setup instructions, schemas, tests and technical lifecycle documents.
- [x] Actual AI prompt summaries, including Databricks troubleshooting and cleanup.
- [x] Local evidence retained, duplicate outputs/environments/caches removed.
- [x] Specialist findings corrected; 67-test full run and subsequent 25-test
      SQL/dashboard validation recorded separately.
- [x] My candidate details populated from the information I supplied; three-minute
      execution duration distinguished from an unknown engine/runtime version.
- [x] First-person [reflection](reflection.md), [workflow](tool-workflow.md),
      [AI usage summary](final-ai-usage-summary.md) and decision records drafted.
- [x] [Copy-ready answers](submission-answers.md) prepared for the guide's question
      themes; actual form fields/limits were not supplied.
- [x] Four Databricks screenshots indexed, including published view; the three
      visualization differences I accepted are explicitly disclosed.

## Actions that require my account, additional evidence or final approval

1. **Approve the first-person wording.** The drafts do not claim that I personally
   ran the local tests, independently discovered the assistant's bugs or reviewed
   every implementation detail. I need to confirm the proposed explanations and
   future improvements accurately represent my views. I should add any material
   work or prompts outside this recorded session.

2. **Attach cloud run details if available.** I have supplied dashboard evidence
   and confirmed completion, but have not supplied an exact notebook run ID,
   engine/runtime version or quality/revenue export. These cannot be reconstructed
   from screenshots or copied from the local run. The evidence index records this
   limitation; a specific screenshot/export file format is not mandated by the guide.

3. **Verify permissions and tool acceptance.** I need to check that my reviewer
   can access the repository and any shared dashboard, and that Copilot is an
   approved alternative for the exercise. The published view is visible in my
   screenshot, but the assistant has not tested access using a reviewer account.
   I also need to verify any required filters; screenshots alone do not prove
   interaction behavior.

4. **Review, commit and push using my authorized identity.** The configured remote
   is [agentic-medallion-pipeline](https://github.com/rakesh-6765/agentic-medallion-pipeline).
   The assistant has staged the changes and preserved my initial commit; it has
   not created a new commit or pushed this handoff. I need to use the required TTN
   identity and check that screenshots/browser details are appropriate to share.

5. **Submit through the actual form.** The form URL, field limits, account session
   and agreed deadline have not been supplied. My [answer drafts](submission-answers.md)
   are ready to adapt/paste. A repository URL and an intended submission date are
   not proof that the form was submitted.

These are concrete external limits, not unfinished code or blank reflection
templates. The assistant has not invented missing identifiers, account approvals,
personal review conclusions or a submission receipt.

## Reproducing removed local artifacts

The cleanup does not remove implementation or test coverage. From the project
root, recreate the optional local environment and outputs with:

```bash
uv sync --extra local --extra dev
.venv/bin/medallion setup-java
.venv/bin/python -m pytest -q
.venv/bin/medallion run
```

Use `uv build --wheel` if a fresh Databricks wheel is needed. Generated SQL
duplicates were removed; render the canonical packaged queries following the
[dashboard guide](src/dashboard/DASHBOARD_GUIDE.md).

# Databricks medallion pipeline

A standalone, synthetic e-commerce batch project: deterministic CSVs → raw Bronze
→ row-preserving, quality-checked Silver → four SQL Gold outputs → dashboard.
It implements the supplied AI Capability Exercise without reproducing its brief.

**Current status (2026-09-10):** the participant confirmed successful end-to-end
execution on Databricks and creation of the dashboard. Local results below were
directly verified by the assistant; cloud execution is participant-reported.
Four actual cloud screenshots are attached, including a published view; their
three participant-accepted visualization differences are disclosed. Cloud run
details, reviewer access and final wording approval remain separate.
See [your submission action items](submission-checklist.md) and the
[evidence index](evidence/README.md).

**Final post-fix verification:** **67 tests passed in 28.97s**, including CSV
doubled quotes/quoted newlines, Unicode whitespace, persistence/rerun, and
independent acceptance checks. Full-default run
`2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7` succeeded with **30,077 eligible orders**,
**11,720,321.50 revenue**, and pipeline/dashboard `SUCCESS`; the wheel rebuilt
successfully. Earlier actual browser checks passed for all five charts,
filtering, weekly periods, and reset. The specialist confirmed both review
findings are resolved. The saved screenshot records that earlier verified run;
its figures match the final run. Local success is not cloud proof.

## Run locally

Use Python 3.12 and `uv`, from this project directory:

```bash
uv sync --extra local --extra dev
.venv/bin/medallion setup-java
.venv/bin/medallion generate
.venv/bin/medallion run
.venv/bin/python -m pytest -q
```

On the implementation machine, `uv` is
`/opt/homebrew/opt/uv/bin/uv`; use that absolute executable if it is not on `PATH`.
`uv.lock` records the dependency resolution. Local environments and generated
outputs were removed during submission cleanup; these commands recreate them.
`setup-java` explicitly downloads a full JDK 21 into `.venv`, not a global install.
Local Spark binds both worker and driver Python to the active interpreter.
Do not install the `local` extra into a Databricks runtime.
Use the installed `.venv/bin/medallion` entrypoint after syncing: a plain `uv run`
can resync without the selected extras. If using `uv run`, repeat
`--extra local --extra dev` explicitly.

Defaults: seed `42`, as-of date `2026-01-31`, high-value threshold `1000.00`;
10,000 customers, 100,000 orders, and 500 products. Use
`.venv/bin/medallion generate --help` and `.venv/bin/medallion run --help` for
overrides. A small, clean development snapshot:

```bash
.venv/bin/medallion generate --output data/clean-example \
  --customers 12 --orders 60 --products 8 --clean
.venv/bin/medallion run --source data/clean-example --output artifacts/clean-example
```

The full generator deliberately injects **460 events**, producing **490 directly
failing rows** when every member of a duplicate key fails. This is not 700 events.
Quality threshold failures are expected and reported; invalid input, persistence
errors, or failed reconciliation are not silently converted into success.

## Persisted outputs and safe reruns

```text
data/{customers,orders,products}.csv
data/generation-manifest.json
artifacts/local/
  bronze/{customers,orders,products}/                 # Parquet directories
  silver/{customers,orders,products,quality_metrics}/ # Parquet directories
  gold/{sales_by_product,revenue_by_customer,
        daily_weekly_trends,customer_segmentation}/  # Parquet directories
  run_manifest.json
  quality_report.json
  dashboard.html
```

Open `artifacts/local/dashboard.html` after a successful local command. It is an
offline report, not an exported Databricks dashboard. Its five charts include
top-10 product bars, a customer-revenue histogram, a segmentation pie, category
bars, and trends. Product/category filters do not cross-filter snapshot-wide
histogram, trends, or segments.

Reruns replace full snapshots, rather than append. **Serialize runs**: neither
multi-table publication nor source-file refresh is globally atomic. An unmarked,
nonempty local output directory is refused; never create an ownership marker to
bypass that check. Keep original or deliberately edited input snapshots separate.

The pipeline writes a `RUNNING` manifest before processing and `SUCCESS` only
after persisted layers reconcile. `dashboard_status` starts `NOT_REQUESTED`;
the local CLI changes it to `RUNNING` then `SUCCESS` while rendering HTML, before
writing `quality_report.json`. Pipeline `SUCCESS` alone does **not** prove those
local presentation steps completed. Check dashboard status, command exit status,
and both files.

## Run on Databricks — requires your workspace

1. Choose an accessible catalog and permissions to create schemas/tables and read
   a source volume. Review the setup scripts in [`database/`](database/).
2. Upload the three CSVs to a Unity Catalog volume. The default source path is
   `/Volumes/workspace/medallion_source/raw`.
3. Install this project from a Git folder using editable installation, or install
   a built wheel, **without local extras**. Restart notebook Python if requested.
4. Import/open [`notebooks/run_pipeline.py`](notebooks/run_pipeline.py), using the
   supplied `spark` session. Widgets default to `catalog=workspace`,
   `prefix=medallion`, `as_of_date=2026-01-31`,
   `high_value_threshold=1000.00`, and the source path above.
5. Verify managed Delta tables in `<catalog>.<prefix>_{bronze,silver,gold}`.
   Inspect `<catalog>.<prefix>_silver.run_manifest` and `quality_metrics`.
   `SUCCESS` proves pipeline reconciliation, not dashboard publication.
6. Follow the [dashboard guide](src/dashboard/DASHBOARD_GUIDE.md); save actual
   workspace query, dashboard, runtime, run ID, and verification evidence.

For the wheel route, build locally with `uv build --wheel`. Upload
`dist/databricks_medallion_pipeline-0.1.0-py3-none-any.whl` to your source volume.
In a Databricks notebook, replace `YOUR_CATALOG` below with the authorized catalog:

```python
%pip install /Volumes/YOUR_CATALOG/medallion_source/raw/databricks_medallion_pipeline-0.1.0-py3-none-any.whl
```

Then run `dbutils.library.restartPython()` in a separate cell before running the
pipeline notebook cells. The wheel includes the SQL templates, not the CSVs;
upload the three source files separately as described above.

Free Edition is serverless-only. Use Spark DataFrame/SQL APIs compatible with
Spark Connect, not local JVM/RDD assumptions. Legacy DBFS access is limited and
outbound internet is restricted to trusted domains; a volume and uploaded wheel
avoid depending on arbitrary downloads. Other source locations work only when
the chosen workspace can access them—there is no automatic cloud-to-local fallback.
Official references:
[serverless limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations),
[Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## Reading and artifact index

| Topic | Artifact |
|---|---|
| Scope, decisions, sequence | [Implementation plan](implementation-plan.md), [requirements](requirements-analysis.md) |
| Architecture and contracts | [Design](design-notes.md), [data model](data-model.md), [quality strategy](data-quality-strategy.md) |
| Verification and issues | [Validation results](validation-results.md), [tests](test-strategy.md), [debugging](debugging-notes.md), [review notes](code-review-notes.md) |
| Generator details | [Generation notes](src/data_generation/DATA_GENERATION_NOTES.md), [seed-data notes](database/seed-data-notes.md) |
| Tool context and provenance | [Workflow](tool-workflow.md), [prompt history](ai-prompts/session-history.md), [Copilot files](tool-specific/copilot-workflow/project-context.md) |
| First-person submission drafts | [Candidate information](candidate-info.md), [reflection](reflection.md), [AI usage summary](final-ai-usage-summary.md), [form answers](submission-answers.md) |

The source directory is installed as the Python package `medallion`; use package
imports, not `python src/pipeline.py`.

## Submission status

- [x] Full post-fix suite: 67 passed; [preserved JUnit report](evidence/local-tests-2026-09-09.xml).
- [x] Subsequent SQL/dashboard validation: 25 passed; [follow-up report](evidence/dashboard-tests-2026-09-10.xml).
- [x] Full-size local run and persisted outputs verified; see `test-strategy.md`.
- [x] All 18 quality metrics, exclusions, and Gold reconciliation checked.
- [x] Browser visual/filter/reset checks passed; actual results in `test-strategy.md`.
- [x] Final post-review full run and wheel rebuild verified.
- [x] Retain actual browser evidence and resolve both specialist findings.
- [x] Databricks end-to-end run and dashboard creation confirmed by participant.
- [x] Attach supplied cloud dashboard screenshots and disclose accepted differences.
- [x] Populate supplied identity/role and draft first-person reflection/decisions.
- [x] Prepare first-person form answers with explicit AI/work attribution.
- [ ] Confirm final wording, organizer tool acceptance and reviewer access.
- [ ] Add cloud run details if available; local figures are not cloud measurements.
- [ ] Review the staged project files, then create and publish the desired commits.
- [ ] Submit through the actual assessment form; no submission receipt is claimed.

Specialist review found two bugs; fixes and regressions passed final validation.
The targeted recheck confirmed both findings resolved, with no significant issues
in the reviewed fixes. Changes are staged for owner review; this cleanup created
no commits or remote pushes and preserved the existing initial commit.
Runtime dependencies and local outputs were removed, not source/tests/seed data.
Compact evidence remains in [evidence](evidence/README.md).

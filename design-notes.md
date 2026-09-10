# Design notes

## Flow and boundaries

```text
seed + as-of date
       ↓
CSV sources + generation manifest
       ↓
Bronze: raw strings + source/run/time metadata
       ↓
Silver: typed values + original _raw + five flags + PASS/FAIL
       ├── quality metrics, including failed thresholds
       ↓
PASS Completed orders joined to unique PASS dimensions
       ↓
four Gold SQL tables → reconciliation → pipeline SUCCESS
       ├── local: offline HTML + quality_report.json (subsequent CLI steps)
       └── cloud: dashboard construction/publish is a separate workspace step
```

`src/` is installed as package `medallion`. The same DataFrame/SQL transformations
serve local and Databricks entrypoints; storage is explicit:

| Concern | Local | Databricks |
|---|---|---|
| Spark lifecycle | CLI creates/stops local Spark | Notebook's supplied `spark` |
| Runtime | Python 3.12, Spark 4.0.4, isolated full JDK 21.0.12.1+1 verified locally | Workspace-managed runtime/serverless |
| Source | Local CSV paths | Accessible volume recommended |
| Storage | Overwritten Parquet directories | Overwritten managed Delta tables |
| Manifest | JSON file | Silver `run_manifest` table |
| Dashboard | Offline HTML after pipeline | Workspace AI/BI instructions; not yet executed |

There is no fallback from cloud Delta to local Parquet, permissive CSV parsing,
failed casts to invented defaults, or bad quality to a claimed clean dataset.

## Intentional source-layout deviation

One shared `src/bronze/ingest_all.py` handles all three source tables. Public
helpers in `src/silver/checks.py` implement the five named checks, with
`create_silver_tables.py` orchestrating them. Separate numbered wrapper files
are not duplicated merely to mirror an illustrative layout. The functional
coverage remains three Bronze tables and all five Silver checks; focused core
tests verify that shared implementation.

## Assistant implementation decisions

- Preserve bad data rather than deduplicate or drop it. Bronze remains lexical;
  Silver records `_raw`, parsed values, and independent explanations.
- Use exact decimal money, strict date/numeric lexical checks, and UTC Spark
  timezone. Null/malformed values primarily fail completeness/types rather than
  generate misleading referential errors.
- Match `csv.writer` doubled-quote escaping and support quoted multiline fields
  in Bronze. Normalize Unicode edge whitespace before Silver completeness while
  preserving `_raw`; reject whitespace inside emails using Unicode-aware matching.
  These are actual post-review corrections, not claims that the earlier suite
  already covered them.
- A duplicated dimension key is never resolved by an arbitrary survivor.
  Referential existence is checked against distinct parent keys, avoiding fan-out.
  Gold independently requires valid unique dimensions to protect revenue.
- Aggregate Gold SQL over eligible sales; retain valid zero-sales customers and
  products. Recompute customer lifetime value from the supplied snapshot.
- Keep daily and Monday-start weekly trends in one table with an explicit grain.
  Treat each grain as a separate revenue reconciliation, never sum both.
- Validate table identifiers and positive finite `DECIMAL(18,2)` thresholds.
  SQL placeholders are controlled application substitutions, not free-form queries.
- Keep lazy SQL temporary views session-local until materialization/session end;
  serverless Spark Connect may resolve names at action time.
- Re-read persisted layer snapshots for downstream work and reconciliation.
  An in-memory success alone is insufficient evidence of persistence.

## Operations and failure semantics

The generator protects unrelated/altered files using its known manifest and
hashes. The local store refuses nonempty directories without its ownership marker.
These controls reduce accidental overwrite; they are not concurrency locks.

Each pipeline run gets a UUID and UTC timestamps. The manifest begins `RUNNING`
and changes to `SUCCESS` after all layer writes and reconciliation. An interrupted
run can leave mixed snapshots and a non-success manifest; serialize runs and
rerun deliberately from intact input. Individual Delta writes do not provide
global atomicity across the pipeline.

The implementation leaves an unfinished `RUNNING` marker on failure rather than
inventing a successful completion or claiming a rollback.

The local CLI renders its dashboard and JSON quality export after pipeline
success. `dashboard_status` is `NOT_REQUESTED` for the pipeline/cloud entrypoint,
then `RUNNING` → `SUCCESS` when the local renderer runs. A rendering/export failure
can coexist with a `SUCCESS` pipeline manifest. JSON export occurs after dashboard
status is updated, so also verify the complete CLI exit status and output files.

## Trade-offs and future work

Full refresh and small local parallelism favor inspectability over scale.
Production work would require access controls, scheduling/locking, source
versioning, retention, incremental semantics, observability, and cross-table
publication design. None is claimed implemented by this exercise.

All choices above are assistant-authored; participant accepted/changed/rejected
decisions remain pending in [review notes](code-review-notes.md).

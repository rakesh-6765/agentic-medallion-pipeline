# Requirements analysis

## Scope

Summarize—not reproduce—the supplied non-graded AI Capability Exercise: build a
synthetic e-commerce medallion pipeline, surface data-quality outcomes, produce
analytical outputs/dashboard, validate results, and preserve honest AI-workflow
artifacts. The guide's 20/60/20 distribution is organizational guidance, not a
grade claimed by this project.

The user requested exactly:

> Create a implementation Plan, Build this solution in a separate project

The user subsequently approved the proposed standalone path. No narrower
technical choices or participant review conclusions were supplied.

## Traceability

| Requirement | Implementation / evidence | Acceptance condition |
|---|---|---|
| Deterministic synthetic sources | `src/data_generation/`, `data/generation-manifest.json` | Exact row counts, repeatable hashes, deliberate faults enumerated |
| Bronze landing | `src/bronze/` | All source fields strings; lexical values and metadata retained; malformed input rejected |
| Silver quality and cleaning | `src/silver/` | All source rows retained; typed fields plus raw struct; five non-null quality flags |
| Quality reporting | `silver.quality_metrics`; local JSON | Denominators, pass/fail counts, strict thresholds, empty-data semantics |
| Product/customer analytics | Gold SQL 01/02 | Unique valid dimensions, including zero-sales members; eligible counts and money |
| Time trends and segmentation | Gold SQL 03/04 | Separate daily/weekly grains and exhaustive ordered segment rules |
| Dashboard | `src/dashboard/` | Required top-10 product bar, customer-revenue histogram, segmentation pie; additional category/trend views with honest filter scope |
| Repeatable execution | CLI, notebook, storage, manifests | Persisted layers reconcile; safe full refresh; clear failure status |
| Validation and AI artifacts | `tests/`, root docs, `ai-prompts/` | Actual evidence separated from planned work and participant judgments |
| Databricks delivery | Notebook, setup SQL, dashboard guide | Actual workspace execution/publish evidence still required |

The source layout deliberately shares one Bronze ingestion module across three
tables and public Silver check helpers across all five checks, rather than
duplicating numbered wrappers. This minor structural deviation preserves
functional coverage; see [design notes](design-notes.md).

## Ambiguities resolved by the assistant

| Ambiguity | Implementation decision | Participant disposition |
|---|---|---|
| Summary count conflicts with named Silver checks | Implement all **five** named checks | Pending |
| Summary count conflicts with named Gold aggregations | Implement all **four** named outputs | Pending |
| Approximate 700 defects vs enumerated faults | Use **460 injected events**; explain **490 flagged rows** | Pending |
| Duplicate rows vs fixed source sizes | Replace IDs in existing rows; fail every group member | Pending |
| Revenue eligibility | `Completed` order and `PASS` order/customer/product | Pending |
| Segment overlap/boundaries | High-Value ≥1000 first; Repeat ≥2; One-Time 1; Inactive 0 | Pending |
| Cloud access unavailable | Validate locally with Parquet; provide unexecuted managed-Delta path | Pending |
| Cursor-specific workflow | Copilot-equivalent documents, not invented Cursor usage | Pending |

## Assumptions and exclusions

- Default as-of date is fixed at `2026-01-31`, seed at `42`; runs do not silently
  substitute today's date.
- Revenue is `total_amount` in unspecified source currency units. No exchange
  rates, taxes, refunds, or complete historical lifetime value are inferred.
- Input contains one product per order record; there is no separate order-line
  table or change-data-capture feed.
- Source customer membership tiers are Premium/Standard/Basic, distinct from the
  four revenue/order-based Gold segments.
- This is a batch full refresh, not streaming, incremental merges, or a
  multi-table transaction. Runs must be serialized.
- Intentional quality defects fail thresholds without terminating the exercise;
  input, environment, persistence, and reconciliation errors must remain visible.
- Missing workspace credentials, permissions, or infrastructure do not authorize
  an invented cloud run. No git commit is part of the approved scope.

Participant review of these assumptions remains pending.

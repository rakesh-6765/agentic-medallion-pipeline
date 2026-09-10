# Copilot workflow — task breakdown

Assistant-authored implementation decomposition; not a participant time log.
Statuses describe the evidence available when documentation was written.

| Work package | Actual owner | Deliverable / dependency | Status |
|---|---|---|---|
| Scope and contracts | Coordinator | Standalone plan, package/config/schema boundaries | Implemented; participant review pending |
| Source generation | `synthetic-data` agent | Generator, manifest, full sources, tests/notes | Corrected source tiers; 14 generator tests passed |
| Bronze and Silver | Coordinator | Ingestion, five checks, quality report | Included in the 63-passing unified suite, including strict-threshold boundaries |
| Storage/runtime/orchestration | Coordinator | Local and catalog stores, CLI/notebook, reconciliation | Persisted fixture/rerun and safe-failure tests passed within the unified 63 tests |
| Gold and dashboards | `analytics-dashboard` agent | Four SQL Gold tables, renderer/datasets/guide/tests | Acceptance corrections completed; focused 21/unified 63 tests and actual browser checks passed |
| Lifecycle documentation | `lifecycle-docs` agent / coordinator | Root docs, true prompt summaries, Copilot-equivalent files | Complete, including final 67-test/run/wheel evidence, actual earlier-run screenshot and resolved review findings |
| Integrated validation | Coordinator | Full suite, full-size persisted run/rerun, browser checks | Final 67 tests, full CLI rerun and wheel passed; browser PASS and actual screenshot retained with original run ID |
| Specialist review | Code-review specialist / coordinator | Review staged implementation changes and correct findings | Both CSV/Unicode findings confirmed resolved in targeted recheck; regressions passed within final 67 tests; no commits |
| Databricks verification | Authorized workspace operator | Real managed-Delta run and dashboard evidence | Not executed / credentials and permissions not supplied |
| Human acceptance | Participant | Identity, decisions, personal reflection, submission review | Pending |

Dependencies: schemas precede generation/layers; persisted valid Silver precedes
Gold; Gold precedes dashboard data; integrated verification precedes a completion
claim. Documentation can proceed alongside implementation but must not convert
unfinished work into reported success.

Raised cross-scope issues are tracked in
[review notes](../../code-review-notes.md). Current command/evidence status belongs
in [test strategy](../../test-strategy.md), rather than an invented commit history.

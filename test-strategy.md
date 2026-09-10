# Test strategy and evidence

**Final post-fix status:** **67 tests passed in 28.97s** after the two verified
CSV/Unicode review fixes, including a valid quoted-newline regression. Final run
`2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7` and wheel rebuild succeeded. JUnit and
manifest were independently inspected. Earlier 63-test evidence and the interim
66-test expectation are historical, not the final result. The specialist
confirmed both findings resolved; the actual screenshot retains its original
verified run ID. See also
[consolidated validation results](validation-results.md).

## Commands

After local setup in [README](README.md):

```bash
# Focused source/core verification
.venv/bin/python -m pytest -q tests/test_generation.py tests/test_config.py \
  tests/test_bronze.py tests/test_silver.py

# Gold and presentation
.venv/bin/python -m pytest -q tests/test_gold.py tests/test_dashboard.py

# Persisted integration and independently specified output columns
.venv/bin/python -m pytest -q tests/test_pipeline.py tests/test_acceptance.py

# Final regression gate, after integration
.venv/bin/python -m pytest -q --tb=short --junitxml=artifacts/test-results.xml

# Full-size persistence and dashboard gate
.venv/bin/medallion generate
.venv/bin/medallion run
```

These are commands to run, not assertions that every command below has already
completed. Do not run overlapping Spark test/pipeline processes against the same
outputs.

## Coverage and acceptance

| Area | What must be demonstrated |
|---|---|
| Generator | Exact 10,000/100,000/500 rows; seeded byte/hash repeatability; 460 events/490 direct failures; valid Premium/Standard/Basic source tiers; disjoint duplicates; no unintended orphans; clean small/empty inputs; protected refresh |
| Configuration | Valid identifiers; positive, finite, representable money threshold; explicit source/date settings |
| Bronze | Original lexical strings/whitespace; doubled-quote CSV escaping and quoted multiline cells; metadata instant; header and malformed-row rejection |
| Silver | Every named check; Unicode edge-whitespace normalization/raw preservation; Unicode whitespace inside email rejected; all duplicate members; safe casts/overflow/precision; parent existence vs parent quality |
| Quality report | Total/pass/fail counts; strict threshold boundaries; empty denominator returns null percentage and false threshold |
| Gold | Hand-calculated eligible counts/revenue; zero-sales dimensions; invalid-dimension exclusion; exact segment boundaries; distinct grains; nonmultiplying joins |
| Dashboard | Top-10 product bar, binned revenue histogram, segmentation pie; extra category/trend views; correct filters/grain control; empty states; escaping and no sensitive detail exports |
| End to end | Persisted layer counts; all Gold revenue reconciliations; manifest transitions; rerun stability; complete local presentation outputs |
| Databricks | Authorized notebook/Delta persistence, serverless compatibility, quality/reconciliation checks, and published dashboard evidence |

A passing test suite is not sufficient to establish cloud permissions, a correct
workspace deployment, or human acceptance.

`tests/test_pipeline.py` adds a 100-customer/1,000-order/20-product fixture with
the exact 70/420/0 direct failures, persisted revenue/exclusion reconciliation,
second-run snapshot stability with refreshed run metadata, and refusal to
overwrite an unowned output directory. It also checks that operational failure
replaces a previous SUCCESS manifest with an unfinished RUNNING marker and
validates catalog identifiers. These assertions passed in the **63-test unified
suite**.

The coordinator also added an independent exact-Gold-column acceptance test and
a quality-report boundary test: exactly 99% completeness or 99.9% referential
integrity must fail. Both passed in the unified suite.

## Observed evidence — implementation session 2026-09-09

Evidence is attributed to the implementing assistant/agents, not to participant
execution or an independent reviewer.

| Validation | Observed result | Scope / limitation |
|---|---|---|
| Initial generator pytest | **13 passed in 1.17s** | Before the source-tier integration correction |
| Corrected generator pytest | **14 passed in 1.11s** | Added source-tier regression coverage; reported in generator notes |
| Configuration + corrected generator | **28 passed in 1.15s** | Coordinator-reported: `tests/test_config.py tests/test_generation.py`; includes source enum and strict date/Decimal configuration validation |
| Full default generation | Corrected CSVs and manifest persisted; counts and SHA-256 verified | Source generation only, not pipeline execution |
| Local Spark smoke | **Spark 4.0.4 started successfully** | Full JDK **21.0.12.1+1** installed through `install-jdk`; macOS Java-home normalization applied |
| First core pytest | **15 passed, 6 failed** | Five worker/driver Python mismatches; one timestamp assertion |
| Earlier core rerun | **21 passed in 14.67s** | Coordinator-reported: `tests/test_config.py tests/test_bronze.py tests/test_silver.py --tb=short`; predates the new boundary/acceptance tests |
| Wheel packaging | **Initial and final rebuild succeeded** | Coordinator verified all four Gold SQL resources plus dashboard SQL were included |
| Corrected Gold/dashboard pytest | **21 passed in 15.53s** | Agent-reported: `.venv/bin/python -m pytest -q tests/test_gold.py tests/test_dashboard.py`; after required aliases, histogram/pie, and top-10 corrections |
| Embedded dashboard JavaScript syntax | **Node `--check` passed** | Analytics agent-reported syntax validation; not browser interaction/cloud evidence |
| Persisted pipeline/acceptance tests | **Passed within the 63-test suite** | Includes 100/1,000/20 fixture rerun, exact failures, manifest/output-directory safety, and independent Gold columns |
| Pre-review regression suite | **63 passed in 26.60s** | `.venv/bin/python -m pytest -q --tb=short --junitxml=artifacts/test-results.xml`; zero failures, errors, or skips before the latest added regressions |
| Final post-review suite | **67 passed in 28.97s** | Includes doubled-quote/valid quoted-newline CSV and Unicode whitespace/raw/email regressions; zero failures/errors/skips |
| Full-size local pipeline | **SUCCESS**, including dashboard status | `.venv/bin/medallion run`; persisted manifest/report/HTML inspected; results below |
| Browser/dashboard interaction | **PASS**, coordinator-verified on actual HTML | Five charts, actual SVG histogram/donut, category/product filters, Monday-start weekly periods, totals, and reset |
| Databricks notebook / dashboard | **Not executed / no evidence supplied** | Requires participant workspace and permissions |

Detailed generator hashes and the independent generator segment calculation are
in [generation notes](src/data_generation/DATA_GENERATION_NOTES.md). That Python
calculation is not mislabeled as a Spark result.

The final [JUnit report](artifacts/test-results.xml) was inspected: **67 tests**,
zero errors/failures/skips, **28.971 seconds** (28.97s in the console summary).
The earlier inspected report had 63 tests/26.597s and has been replaced. Focused
runs overlap the suite; their counts must not be added together.

The coordinator's independent standard-library CSV calculation matched the
completed full-default Spark run: **30,077 eligible Completed orders** and
**11,720,321.50 revenue**. This agreement is local evidence, not a Databricks run.

## Verified final full-default local execution

Command: `.venv/bin/medallion run`, reported successful by the coordinator.
The documentation agent independently inspected
[`artifacts/local/run_manifest.json`](artifacts/local/run_manifest.json),
[`quality_report.json`](artifacts/local/quality_report.json), and the persisted
HTML file's presence/size.

| Item | Observed result |
|---|---|
| Run ID | `2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7` |
| Runtime / statuses | Spark 4.0.4; pipeline `SUCCESS`; dashboard `SUCCESS` |
| Pipeline UTC start / finish | `2026-09-09T12:28:52.352500+00:00` / `2026-09-09T12:29:00.932363+00:00` |
| Bronze and Silver counts | Each retains 10,000 customers, 100,000 orders, 500 products |
| Direct Silver failures | Customers 70; orders 420; products 0; total **490** |
| Gold row counts | Products 500; customers 9,930; combined daily/weekly trend rows 419; segments 4 |
| Quality report | All 18 metrics independently verified by coordinator; JSON also inspected |
| Order eligibility | 100,000 = 420 direct quality failures + 537 dimension exclusions + 68,966 non-Completed exclusions + **30,077 eligible orders** |
| Revenue reconciliation | **11,720,321.50** in products, customers, segments, and each separate daily/weekly grain |
| Independent reference | Standard-library CSV oracle agrees with eligible count and exact revenue |
| Dashboard | `artifacts/local/dashboard.html` persisted with dashboard SUCCESS; five charts; earlier actual browser visual/filter checks passed |

The timestamps above delimit the pipeline; local rendering/export occurs
afterward and is not assigned an invented duration.
The earlier run `c82b5ef7-ad01-41b2-878f-27cdb076f0d6` had the same layer counts,
quality outcomes, eligibility, and revenue. The final rerun confirms those
business results remained stable after the specialist fixes.

## Actual browser verification

The coordinator exercised the persisted HTML, not a mock screenshot or unrendered
template. Reported results:

| Check | Observed result |
|---|---|
| Visual structure | All five charts present; actual SVG revenue histogram and segmentation pie/donut visually checked |
| Category `Books` | **83 products**, **4,962 eligible orders**, **2,024,922.75 revenue** |
| Selected `Travel Journal 0330` | **1 product**, **63 eligible orders**, **42,902.45 revenue** |
| Weekly control | Displays the latest **20** nonempty Monday-start weekly periods |
| Customer coverage | Histogram and segment counts each sum to **9,930** |
| Segment pie counts | High-Value **2,481**; Repeat **2,481**; One-Time **2,484**; Inactive **2,484** |
| Reset | Restores **500 products**, **30,077 orders**, **11,720,321.50 revenue** |

These are actual local browser results from the pre-review run. The saved
[local dashboard screenshot](evidence/local-dashboard.png) records run
`c82b5ef7-ad01-41b2-878f-27cdb076f0d6`, not a newly captured final-run image.
The final run has identical business figures, and the renderer did not change
between these runs. The consolidated record is [validation results](validation-results.md).
No dashboard publish/import or Databricks query is inferred.

## Remaining evidence / completion

- Full suite, 2026-09-09: command above; **67 passed in 28.97s**, no failures/errors/skips.
- Snapshot rerun: **verified in the persisted fixture and final full-default run**;
  business results are unchanged from the earlier full-default run.
- Actual browser visual/filter/reset checks: **PASS**, as recorded above.
- Specialist review: **two verified bugs found and corrected**; regressions added,
  final suite passed; targeted specialist recheck **confirmed both resolved**.
- Post-review full suite/default run and final wheel: **Verified successful**.
- Screenshot: **Actual earlier-run evidence retained**, with its run identity explicit.
- Cloud workspace/runtime/warehouse, run ID and dashboard URL/export: **Pending**.

The contract and specialist corrections are covered by the final passing suite
and successful full-default rerun. Earlier actual browser results are preserved;
the targeted review found no significant issues in the corrected code.
Cloud execution remains unverified.

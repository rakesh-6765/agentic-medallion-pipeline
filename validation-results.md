# Local validation results

Observed on **2026-09-09**, not a claim of Databricks execution.

**2026-09-10 update:** the participant confirmed the whole project ran end to end
on Databricks and a dashboard was created. Cloud measurements/identifiers have
not been supplied; the numbers below remain explicitly local.

After SQL-template diagnostic improvements, **25 targeted Gold/dashboard tests
passed in 16.04s** on 2026-09-10. The exact four-table workspace mapping also
generated all five queries from an isolated wheel import.
See the [preserved evidence index](evidence/README.md).

## Reproducible commands and environment

```bash
.venv/bin/python -m pytest -q --tb=short --junitxml=artifacts/test-results.xml
.venv/bin/medallion run
uv build --wheel --quiet
```

- **67 tests passed in 28.97 seconds** after the final corrections.
- Python 3.12.13, PySpark 4.0.4, isolated full JDK 21.0.12.1+1.
- Final local run: `2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7`.
- Pipeline status: SUCCESS. Dashboard status: SUCCESS.
- Wheel build succeeded, including all Gold and dashboard SQL resources.
- Actual JUnit reports, run manifest, quality report and browser screenshot are
  preserved in [evidence](evidence/README.md). Reproducible Parquet/HTML outputs,
  local environments, builds and duplicate generated SQL were removed during
  submission cleanup; the commands above recreate them after README setup.

## Persisted row counts

| Source | Bronze | Silver | Directly failing Silver rows |
|---|---:|---:|---:|
| Customers | 10,000 | 10,000 | 70 |
| Orders | 100,000 | 100,000 | 420 |
| Products | 500 | 500 | 0 |

No source rows were deleted from Silver. The enumerated 460 fault injections
produce 490 directly failing rows because both members of each duplicate pair
are flagged.

| Gold output | Rows |
|---|---:|
| Sales by product | 500 |
| Revenue by customer | 9,930 |
| Daily/weekly trends | 419 |
| Customer segmentation | 4 |

## Quality and financial reconciliation

| Check | Customers passed | Orders passed | Products passed |
|---|---:|---:|---:|
| Completeness | 99.5% | 99.7% | 100% |
| Uniqueness | 99.8% | 99.96% | 100% |
| Type validation | 100% | 100% | 100% |
| Referential integrity | 100% | 99.92% | 100% |
| Business logic | 100% | 100% | 100% |
| Overall | 99.3% | 99.58% | 100% |

Uniqueness thresholds intentionally fail. Pipeline execution success does not
mean all input data is clean. Non-applicable referential checks on dimensions
pass; null/malformed foreign keys belong to completeness/type checks.

The 100,000 orders reconcile into disjoint groups:

- 420 directly failed Silver validation.
- 537 additional orders reference a quality-invalid dimension.
- 68,966 remaining valid linked orders are not Completed.
- **30,077 orders contribute eligible revenue of 11,720,321.50**.

An independent standard-library CSV oracle agrees with the eligible count and
revenue. Product, customer, segmentation, daily and weekly revenue totals each
agree with this value. Daily and weekly totals are checked separately, never
summed together. Integration tests execute a second persisted refresh and verify
unchanged business results and replacement run IDs, not appended duplicates.

## Browser evidence

The [actual local dashboard screenshot](evidence/local-dashboard.png) records the
earlier verified run `c82b5ef7-ad01-41b2-878f-27cdb076f0d6`; it is not relabeled as
a final-run capture. HTML can be regenerated at `artifacts/local/dashboard.html`.
The renderer is unchanged, and both runs have identical business figures. Five charts render,
including the required product bar chart, revenue histogram and segmentation
pie/donut. Browser checks verified:

- Books filter: 83 products, 4,962 orders, revenue 2,024,922.75.
- Product 330: one product, 63 orders, revenue 42,902.45.
- Weekly selection: the displayed latest 20 periods all start on Monday.
- Histogram bins contain exactly 9,930 customers, including zero revenue.
- Segments contain 2,481 High-Value, 2,481 Repeat, 2,484 One-Time and 2,484
  Inactive customers, totaling 9,930.
- Reset restores all 500 products and revenue 11,720,321.50.
- Histogram and segmentation totals are unaffected by scoped product/category
  filters, as the UI explicitly states.

## Corrections proven by tests

The specialist confirmed both CSV/whitespace review findings resolved and found
no significant issues in the targeted recheck of their fixes and regressions.

- Source tiers are Premium/Standard/Basic, distinct from derived Gold segments.
- Required Gold column names and the histogram/pie chart types are independently
  checked, rather than accepting similar-looking substitute outputs.
- CSV doubled quotes, embedded commas, backslashes and quoted newlines round-trip
  through Bronze unchanged.
- Tabs, line breaks and Unicode nonbreaking spaces cannot bypass completeness;
  the original values remain in `_raw`.
- Exact 99% completeness and 99.9% referential rates fail their strict `>` gates.
- Malformed types, orphan keys, all duplicate members, business-rule failures,
  empty tables, zero-sale dimensions and monetary precision have regression tests.

## Still requires participant/workspace action

The participant already confirmed successful Databricks execution and dashboard
creation. Attach actual cloud runtime/run details, quality/reconciliation output
and dashboard evidence; confirm publication/reviewer access as appropriate.
Complete personal details, participant acceptance/rejection judgments and an
authentic reflection. Review the staged files and create/publish commits yourself.
See the consolidated [participant action items](submission-checklist.md).

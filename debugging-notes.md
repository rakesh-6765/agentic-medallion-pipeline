# Debugging notes

Only problems observed during this implementation are recorded. This is not a
fictional participant debugging diary.

| Observed failure | Diagnosis | Assistant action | Verification |
|---|---|---|---|
| First `uv sync` failed while building the editable package | Declared package directories had not yet been created | Create the package directories, then retry dependency sync | Dependency setup subsequently completed |
| Initial JDK setup could not start Spark | `jdk4py`'s slim Java 21 runtime lacked `jdk.incubator.vector` | Replace it with `install-jdk`; explicitly download a full JDK 21 under `.venv` | Local Spark 4.0.4 smoke subsequently passed |
| Downloaded macOS JDK root was not the executable Java home | JDK bundle requires `Contents/Home` normalization | Normalize stored/resolved Java home when the bundle layout exists | Same Spark smoke passed after normalization |
| Five of the first six core-test failures | Spark workers launched Python 3.9 while the driver used Python 3.12 | Bind `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` to `sys.executable` | Core rerun: 21 passed, coordinator-reported |
| Remaining initial core failure asserted a UTC-naive Python timestamp | Collected timestamp presentation followed local timezone; the stored instant was correct | Assert the Unix epoch instant instead of a timezone-dependent naive object | Included in the 21-passing core rerun |

Initial core outcome: **15 passed, 6 failed**. Verified rerun:
**21 passed in 14.67s**, using
`.venv/bin/python -m pytest -q tests/test_config.py tests/test_bronze.py tests/test_silver.py --tb=short`.
This is core-test evidence, not evidence that all Gold/integration/cloud tests passed.

## Integration issues raised during documentation inspection

The initial generator serialized internal revenue personas instead of the
required Premium/Standard/Basic source tiers. The implementing agent corrected
that mapping, regenerated the default snapshot, and reported **14 tests passed
in 1.11s**, including source-enum and clean lifetime-value regression checks.
Orders/products bytes and all non-segment customer fields remained unchanged.
The corrected data also passed persisted Spark fixture integration within the
later 63-test unified suite.

An agent's proposed workaround—relax Silver's enum to accept the incorrect source
labels—was rejected by the coordinator. Fixing the generator preserved the brief's
source contract; this was assistant review, not a participant decision.

Initial Gold SQL exposed `grain` while orchestration required `period_type`.
The SQL/dashboard were aligned to `period_type`. The coordinator's acceptance
review also identified missing required Gold aliases/customer fields and
dashboard histogram/pie visualizations. After correction, the analytics agent
reported **21 focused Gold/dashboard tests passed in 15.53s**. The subsequent
unified suite passed **63 tests in 26.60s**, including independent acceptance and
persisted fixture/rerun checks. Full-default run/browser evidence is maintained
separately in [test strategy](test-strategy.md).

## Specialist review findings after the 63-test run

1. **CSV escape mismatch:** Spark's default backslash escape did not match
   `csv.writer`'s doubled-quote convention, corrupting a valid name such as
   `John "JJ" Doe`. The coordinator explicitly set double-quote escaping and
   enabled quoted multiline fields in Bronze; a regression was added.
2. **Unicode whitespace:** Spark's default `trim` missed tabs/nonbreaking spaces.
   The coordinator added Unicode-aware edge normalization before completeness,
   preserving original `_raw` values, and Unicode-aware rejection of whitespace
   inside email addresses. Regressions were added.

These were actual verified specialist findings, not hypothetical improvements
or an initially clean review. A further valid quoted-newline regression raised
the interim 66-test expectation to the final **67 passed in 28.97s**. The
post-fix full-default run `2ce291e3-e2d0-41bf-8f3b-271cfdfc92f7` and wheel rebuild
succeeded with unchanged business results. This final evidence supersedes the
earlier 63-test state. The specialist's targeted recheck confirmed both findings
resolved, with no significant issues in the corrected code. The actual screenshot
from the earlier verified run is retained with its original run identity.

## Databricks dashboard placeholder follow-up: 2026-09-10

The participant reported the SQL replacement-name error after the Databricks
pipeline succeeded. Their exact four-table mapping works against current source
and an isolated wheel import. The assistant added template-path and
missing/unexpected-key diagnostics, regression tests, inspection/reinstallation
instructions and rendered SQL as an alternative.

The mismatch happens before Spark SQL executes. An older/edited/shadowed package
resource was a plausible cause, not a confirmed inspection of their environment.
The participant later confirmed end-to-end cloud execution/dashboard creation but
did not specify which remediation they used. The 25-test Gold/dashboard suite
passed after these changes; its report is preserved under `evidence/`.

## Runbook for subsequent problems

These are diagnostic steps, **not** additional incidents claimed to have occurred:

1. For Java startup errors, run `.venv/bin/medallion setup-java` and inspect the
   virtualenv's Java-home marker; do not silently switch to a slim JRE.
2. For worker version errors, confirm the driver and workers use the same
   virtualenv Python before investigating data transformations.
3. For rejected CSVs, inspect exact headers, record field counts, and encoding.
   Preserve rejected input; do not enable permissive parsing to hide corruption.
4. For quality differences, compare `_raw`, individual flags, and manifest fault
   lines. Distinguish parent existence from parent quality and Gold eligibility.
5. For incomplete reruns, inspect manifest status and serialize a deliberate
   refresh from intact sources. Never claim a multi-table rollback occurred.
6. For a `SUCCESS` pipeline manifest without dashboard files, inspect the local
   CLI's later rendering/export error and exit status.
7. For cloud errors, verify actual volume/catalog privileges and current serverless
   restrictions. Local success is not a cloud connectivity fallback.

The participant's first-person debugging account is drafted in
[reflection](reflection.md). It records the reported cloud error and successful
outcome, but not an unprovided root cause or personal time spent on diagnosis.

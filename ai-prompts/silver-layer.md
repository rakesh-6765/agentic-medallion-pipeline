# Prompt record — Silver

**Origin:** Overall user request U2; no separate human Silver prompt.

**Assistant implementation-task summary (not a verbatim prompt):** Implement all
five named checks despite the guide's inconsistent summary count. Preserve every
row and raw field evidence, normalize/parse declared types safely, emit explicit
quality flags/failure names, and report per-table/check metrics with the stated
strict thresholds. Keep referential existence distinct from parent quality.

**AI output / decisions:** Typed Silver plus `_raw`, trimmed strings/lowercased
email, integer/date/decimal validation, all-member duplicate failure, distinct
parent-key joins, as-of-aware business checks, and an 18-row quality report.
Thresholds: completeness >99%, referential integrity >99.9%, all other checks
100%; empty denominator returns null percentage and false threshold.

**Validation:** Core fixtures cover checks, type/precision/overflow cases,
duplicate safety, parent existence, row preservation, and empty-data reporting.
The coordinator reported 21 core tests passing after interpreter/assertion fixes.
This is not a claim that the full generated snapshot has been reconciled.

**Follow-up:** The initial generator incorrectly emitted internal personas as
source segments. It was corrected to the required Premium/Standard/Basic tiers
already validated by Silver; 14 generator tests passed. No weakening of the
Silver enum was needed. Full generated-snapshot integration remains separate.
The later **63-test unified suite** passed Silver, exact threshold boundaries,
and persisted fixture assertions for 70 customer/420 order failures.
The full-default run then preserved all **110,500 source rows**, measured exactly
**70 customer + 420 order failures**, and produced the independently checked
18-metric quality report. This is local execution evidence, not a cloud run.

**Later specialist feedback / assistant correction:** Spark `trim` left tabs and
NBSP at field edges, allowing whitespace-only fields to escape completeness.
The coordinator added Unicode-aware edge normalization before checks while
preserving `_raw`, and Unicode-aware whitespace rejection inside email addresses.
Regressions were added and passed within the final **67-test** suite; the
full-default rerun also succeeded with unchanged quality/count/revenue results.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | Pending |
| Rationale and any participant modifications | Pending |
| Independent participant validation | Pending |

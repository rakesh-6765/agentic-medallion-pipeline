# Copilot workflow — implementation specification

Human-readable tool-equivalent specification; not an automatically loaded
configuration or a record of participant approval.

## Acceptance contract

1. Default data has exactly 10,000 customers, 100,000 orders, and 500 products,
   seed 42, as-of 2026-01-31, reproducible source hashes, and valid source
   Premium/Standard/Basic membership tiers.
2. Implement explicitly enumerated 460 injections. Duplicate replacements keep
   source sizes fixed and require all-member failure, yielding 490 direct failures.
3. Bronze uses strict ordered headers, raw strings, and ingestion provenance.
4. Silver retains every row and `_raw`, parses safely, and emits all five checks.
   Exact thresholds: >99% completeness, >99.9% referential, 100% other checks.
   Empty table percentage is null and threshold outcome false.
5. Gold includes only Completed/PASS orders linked to PASS unique dimensions.
   Product/customer dimensions retain zero-sales members.
6. Gold covers product sales, customer revenue, daily/weekly trends, and customer
   segmentation. Default ordered segments: High-Value ≥1000, Repeat ≥2 orders,
   One-Time 1, Inactive 0. Revenue and order eligibility use the same snapshot.
7. Reconcile persisted layers and each independent Gold revenue grain before
   pipeline success. Report direct failures and additional exclusions separately.
8. Render local offline dashboard outputs; provide executable cloud instructions
   without pretending they were executed. Required visualizations are top-10
   product revenue bars, a customer-revenue histogram, and a segmentation pie;
   category/trend charts are additional views.

## Non-goals / constraints

No real data, secrets, arbitrary runtime SQL, silent cloud-to-local fallback,
invented dashboard import schema, streaming/CDC, global snapshot transaction, or
automatic commit/submission. Serialize runs. User judgments and personal
reflections remain user-owned.

See the authoritative [data contract](../../data-model.md) and
[design notes](../../design-notes.md) for detail.

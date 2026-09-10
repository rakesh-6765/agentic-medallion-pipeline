# Seed data

Use the checked-in synthetic files under [`data/`](../data/): 10,000 customers,
100,000 orders and 500 products. The reproducible seed is 42 and the as-of date is
2026-01-31. No real customer records are included.

The [generation manifest](../data/generation-manifest.json) contains configuration,
CSV SHA-256 hashes, actual row counts and injection locations. The
[generation notes](../src/data_generation/DATA_GENERATION_NOTES.md) explain the
460 injected events and 490 directly failing rows, duplicate semantics, synthetic
source tiers, internal personas and regeneration safeguards.

Regenerate from the repository root after installing the package:

```bash
.venv/bin/medallion generate
```

Unchanged arguments reproduce identical files on the supported Python runtime.
Deliberately edited generated files are protected from overwrite; preserve them
in a separate directory before regenerating the default seed.

For Databricks, upload the three CSVs and manifest to the reviewed Unity Catalog
volume described in [setup notes](setup-notes.md). The notebook's `source_path`
must point at their containing directory. CSV source cells must not be pre-cleaned
or converted by an upload wizard: raw values belong in Bronze and their validation
belongs in Silver. The manifest documents provenance; the pipeline also accepts
ordinary CSV inputs and does not require a generator manifest.

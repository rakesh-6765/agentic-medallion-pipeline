# Deterministic synthetic source data

## Usage

The generator uses the Python standard library only. Install the project editable
using the root project's setup instructions, then run from the project root:

```bash
python -m medallion.data_generation.generate_sample_data --output-dir data
```

The public API lives in the module, not the package initializer:

```python
from datetime import date
from pathlib import Path

from medallion.data_generation.generate_sample_data import generate_sample_data

manifest = generate_sample_data(Path("data"))
clean = generate_sample_data(
    Path("data/clean-example"),
    customers=12,
    orders=60,
    products=8,
    seed=7,
    as_of_date=date(2025, 6, 30),
    inject_issues=False,
)
```

Defaults are **10,000 customers, 100,000 orders, 500 products**, seed **42**, and
as-of date **2026-01-31**, with issue injection enabled. The function returns the
same dictionary serialized to `generation-manifest.json`. CLI overrides include
`--customers`, `--orders`, `--products`, `--seed`, `--as-of-date YYYY-MM-DD`, and
`--no-inject-issues`.

## Files and repeatability

- `customers.csv`, `orders.csv`, and `products.csv` have exactly the requested data
  row counts and the column order declared in `medallion.contracts.FIELDS`.
- CSV encoding is UTF-8 with LF line endings; nulls are empty cells.
- No current date, timestamp, external service, Faker dependency, or real customer
  data is used. All email addresses use the reserved domain `example.com`.
- A private `random.Random(seed)` instance leaves the process-wide random state
  unchanged. Identical arguments reproduce identical CSV **and manifest bytes**
  within the supported Python runtime. Output directory paths are not recorded in
  the manifest.
- The manifest includes configuration, actual row counts, each CSV's SHA-256 and
  byte size, exact injected counts, the affected CSV line numbers, duplicate donor
  mappings, and the expected direct failing-row counts. Line numbers include the
  header; data starts on line 2. Hashes cover CSV bytes, not the manifest itself.
- Existing unrelated files are preserved. Refreshing known generated outputs is
  intentional, but an existing CSV without a recognized generation manifest, an
  altered CSV, an unknown manifest, or a symlink target is rejected. To regenerate
  deliberately edited data, move the edited snapshot elsewhere first.
- All output bytes are constructed before file publication. Exclusive-create
  `.pending` files in the chosen output directory are cleaned up after each write;
  a pre-existing pending file is never overwritten. Publication replaces the
  manifest last. Refreshing the four files is **not a multi-file transaction**:
  interrupted publication can require moving the partial snapshot aside.

## Exact deliberate faults

| Table | Fault | Injection events | Direct failing rows |
|---|---|---:|---:|
| customers | Null email | 50 | 50 |
| customers | Duplicate customer ID | 10 | 20 |
| orders | Null customer ID | 100 | 100 |
| orders | Null product ID | 200 | 200 |
| orders | Orphan customer ID | 50 | 50 |
| orders | Orphan product ID | 30 | 30 |
| orders | Duplicate order ID | 20 | 40 |
| **Total** | | **460** | **490** |

Duplicate injection changes an existing recipient row's ID to a donor row's ID.
It does not append rows. Each donor is unique, is not a recipient, and has no other
same-table injected fault. Every duplicate group contains exactly two rows;
uniqueness must flag **both**, not choose a survivor. Fault row sets, including
donors, are disjoint within each table.

Customers are corrupted **before** order references are built. Orders choose only
customer IDs still present after replacement. Deliberate orphans use positive IDs
greater than the corresponding original maximum ID, so there are no accidental
orphans or confusion with removed customer IDs. Some orders legitimately reference
a present but quality-invalid customer; this is **not** a direct referential
failure. Gold must separately exclude orders with invalid dimensions.

Injection requires at least **70 customers, 420 orders, and 1 product** to allocate
all fault recipients and donors disjointly. Smaller requests raise an explicit
`ValueError` before outputs are created. With `inject_issues=False`, small or empty
tables are supported; nonempty orders still require both parent dimensions.

## Clean-data business rules and personas

Products have positive synthetic prices, `0 <= cost <= price`, and nonnegative
stock and reorder levels. Money is generated as integer cents and serialized with
exactly two fractional digits; no binary floating-point financial arithmetic is
used. Quantities are positive and every order satisfies
`total_amount == quantity * unit_price`.

Signup dates fall 730–366 days before the supplied as-of date. Order dates cover
the last 365 days through the as-of date, ensuring signup precedes every order,
including both copies of a duplicated customer ID. These relative bounds clamp at
`date.min`, so historical and boundary-date custom fixtures remain valid. Completed
orders always have a payment date; other statuses may have one. Any payment date
falls between the order date and the as-of date.

The four cyclic **internal personas** are Inactive, One-Time, Repeat, and High-Value.
When the requested volume permits, baseline completed orders establish one sale
for One-Time, two for Repeat, and at least 1000.00 revenue for High-Value. Subsequent
orders preserve those target categories; Inactive has no completed sales. Baseline
sales exclude quality-invalid customer IDs, and order injections avoid baseline
rows when enough other rows exist. This maintains broad, balanced segment coverage
in the full default snapshot without promising exact segment counts after quality
filtering or for tiny snapshots.

Source `customer_segment` contains only the required membership tiers **Premium,
Standard, and Basic**. Internal High-Value personas map to Premium, Repeat to
Standard, and One-Time/Inactive to Basic when customer rows are finalized. Both
members of a duplicated customer ID retain matching tiers and lifetime values.
All three source tiers are present in the default snapshot. These source tiers
are a different concept from the four **derived Gold segments**, which must be
calculated from quality-eligible completed sales, not copied from source labels.

Source `lifetime_value` records synthetic completed revenue before order corruption
and is never negative. Gold recalculates actual eligible snapshot revenue and
segments after all quality filtering; neither field claims complete real-world
historical value.

## Verification

`tests/test_generation.py` uses standard-library assertions and CSV parsing under
the project's existing pytest runner. It checks full default row and fault counts,
disjoint duplicate donors/recipients, absence of accidental foreign-key failures,
business invariants, deterministic bytes and hashes, safe refresh/collision
behavior, custom dates, small clean fixtures, required source membership tiers,
clean lifetime-value reconciliation, and balanced derived Gold segment coverage.
Test work files stay under the project's `data/` directory and are removed after
each run. Test execution evidence is reported only after the tests actually run.

Verified during implementation:

```text
.venv/bin/python -m pytest -q tests/test_generation.py
14 passed in 1.11s
```

The full default snapshot was generated with the module CLI and independently
checked against its manifest's row counts and SHA-256 hashes:

| File | Data rows | Bytes | SHA-256 |
|---|---:|---:|---|
| customers.csv | 10,000 | 823,095 | `569c27a396879d4fbe6cb0c3d2044df3e8144e568b3bd80146f4dc8e50b6161a` |
| orders.csv | 100,000 | 5,553,148 | `e074a04a461f1c4944ebcf0834a92241ecc3c701995550998fc95c01fdff0a3b` |
| products.csv | 500 | 26,362 | `13212ba8dc01456ef05d467214bd12563ac22f576c45ff465dee647373a75005` |

An independent standard-library calculation over quality-eligible completed sales
produced High-Value **2,481**, Repeat **2,481**, One-Time **2,484**, and Inactive
**2,484** customers. This verifies generator balance; it is not a claim that a
Spark or Databricks pipeline was executed.

An integration review caught an initial source-label mismatch: the first generator
version serialized internal personas into `customer_segment`. It now converts
those labels to the required source tiers before serialization. Regression tests
require all source labels to be valid and all three tiers to be present by default.
After regenerating through the existing manifest ownership checks, source counts
are Basic **5,003**, Standard **2,499**, and Premium **2,498**. Comparison with the
prior snapshot verified that customer lifetime values and all other non-segment
fields were unchanged, as were the entire orders and products files.

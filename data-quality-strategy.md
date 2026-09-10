# Data-quality strategy

## Five checks, no discarded evidence

Every Bronze row survives into Silver with original `_raw` values, parsed fields,
five booleans, `quality_failures`, and overall PASS/FAIL. Checks operate per row;
one row may fail multiple checks, so check failure counts must not be added to
infer the number of distinct failed rows.

| Check | Rule | Acceptance threshold |
|---|---|---|
| Completeness | All normalized source fields non-null except optional payment date | Strictly **>99%** |
| Uniqueness | Every member of a repeated parsed non-null primary key fails | **100%** |
| Type validation | Integer bounds/lexical form; real ISO dates; finite representable `DECIMAL(18,2)` with at most two fractional digits | **100%** |
| Referential integrity | Non-null parsed order foreign keys exist in distinct parent-key sets | Strictly **>99.9%** |
| Business logic | Entity-specific rules below | **100%** |

Normalization removes Unicode whitespace at field edges before completeness;
tabs/NBSP-only required fields therefore fail completeness. `_raw` preserves
those original characters. Email rules reject Unicode whitespace within an
address after edge normalization. These behaviors were corrected following
specialist findings; their regressions passed in the final **67-test** suite
recorded in [test strategy](test-strategy.md).

Null values fail required completeness, not type syntax; malformed non-null
values fail type validation. A null/malformed foreign key does not produce a
second orphan failure. Dimensions have a true referential flag because this
contract defines no parent relationship for them. Business predicates that
cannot be evaluated because of absent/invalid values do not erase the responsible
completeness/type failure.

Business rules include positive keys; source tiers Premium/Standard/Basic and
order statuses Pending/Completed/Cancelled; usable email shape; no future
signup/order/payment date relative to the
configured as-of date; nonnegative money, stock, and reorder quantities; product
price ≥ cost; positive order quantity; exact `total_amount = quantity × unit_price`;
and Completed orders requiring payment with `order_date ≤ payment_date ≤ as_of`.
Email shape validation is not a claim of address deliverability.

## Expected deliberate defects

| Source | Injection | Events | Directly failing rows |
|---|---|---:|---:|
| Customers | Missing email | 50 | 50 |
| Customers | Duplicate ID replacement | 10 | 20 |
| Orders | Missing customer ID | 100 | 100 |
| Orders | Missing product ID | 200 | 200 |
| Orders | Orphan customer ID | 50 | 50 |
| Orders | Orphan product ID | 30 | 30 |
| Orders | Duplicate ID replacement | 20 | 40 |
| **Total** | | **460** | **490** |

Default injections are disjoint, including duplicate donors. Expected direct
failures are customers **70**, orders **420**, products **0**; expected overall
passes are **9,930**, **99,580**, and **500** respectively. These are acceptance
expectations, not a replacement for measuring a completed Spark run. Parent keys
are prepared before order references, avoiding accidental additional orphans.

Expected check rates for default data are customer completeness **99.5%**,
customer uniqueness **99.8%**, order completeness **99.7%**, order uniqueness
**99.96%**, and order referential integrity **99.92%**. Thus completeness and
referential thresholds can pass while uniqueness/overall thresholds fail.
Additional type/business defects are exercised in tests, not silently added to
the enumerated source injections.

## Reporting and downstream policy

- Denominator is all rows in the table for every check. Report total, passed,
  failed, percentage, operator, threshold, and threshold result.
- Compare thresholds using unrounded percentages; display percentages rounded to
  six decimals. Exactly 99% completeness or 99.9% referential integrity **fails**.
- Empty data has percentage `null` and `threshold_passed=false`, never a fabricated
  100% pass. Overall quality additionally uses a 100% reporting threshold.
- Expected quality threshold failures are visible findings, not operational
  pipeline exceptions. No invalid rows are dropped or coerced into invented
  values to make thresholds green.
- Referential **existence** does not mean the parent itself passed quality.
  Gold requires PASS on the order, customer, and product, plus Completed status.
  Therefore Gold exclusions can exceed the **420 directly failing orders**.
- Reconciliation separates direct order failures, dimension-related exclusions,
  non-Completed exclusions, eligible order count, and exact eligible revenue.
  Product/customer/segment totals and each trend grain must match that revenue.

## Measured default-run outcome

Run `c82b5ef7-ad01-41b2-878f-27cdb076f0d6` measured the expected **70 customer,
420 order, and 0 product direct failures**. All 18 metrics were independently
checked by the coordinator; the persisted JSON was also inspected during
documentation. Uniqueness and overall thresholds fail for customers/orders as
intended; completeness/referential thresholds pass, and types/business checks
are 100%.

Gold excluded a further **537** Silver-PASS orders for dimension quality and
**68,966** non-Completed orders, leaving **30,077** eligible sales and
**11,720,321.50** reconciled revenue. These quantities partition the 100,000 source
orders; dimension/status exclusions are not added to the 490 direct source-row
failures. Actual browser histogram and segment counts each total **9,930** valid
customers. See [test strategy](test-strategy.md) for persisted/browser evidence
and the remaining cloud gate.

"""Generate deterministic CSV source snapshots, optionally with exact known faults."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from medallion.contracts import AS_OF_DATE, FIELDS, SEED, TABLES

GENERATOR = "medallion.data_generation.generate_sample_data"
MANIFEST_NAME = "generation-manifest.json"
MANIFEST_VERSION = 1
MIN_CUSTOMERS_WITH_ISSUES = 70
MIN_ORDERS_WITH_ISSUES = 420
INJECTED_COUNTS = {
    "customers": {"null_email": 50, "duplicate_customer_id": 10},
    "orders": {
        "null_customer_id": 100,
        "null_product_id": 200,
        "orphan_customer_id": 50,
        "orphan_product_id": 30,
        "duplicate_order_id": 20,
    },
    "products": {},
}
PERSONAS = ("Inactive", "One-Time", "Repeat", "High-Value")
SOURCE_SEGMENT_BY_PERSONA = {
    "Inactive": "Basic",
    "One-Time": "Basic",
    "Repeat": "Standard",
    "High-Value": "Premium",
}
FIRST_NAMES = (
    "Amelia", "Noah", "Olivia", "Liam", "Sofia", "Ethan", "Ava", "Arjun",
    "Mia", "Lucas", "Isabella", "Omar", "Chloe", "Leo", "Nora", "Hugo",
    "Aisha", "Oliver", "Hana", "Mateo", "Zoe", "Daniel", "Priya", "Samuel",
)
LAST_NAMES = (
    "Bennett", "Singh", "Garcia", "Williams", "Chen", "Martin", "Khan",
    "Anderson", "Patel", "Wilson", "Santos", "Kim", "Dubois", "Taylor",
    "Nakamura", "Thompson", "Ahmed", "Nguyen", "Rossi", "Clarke",
)
COUNTRIES = (
    "United States", "United Kingdom", "Canada", "Australia", "Germany",
    "France", "India", "Japan", "Singapore", "United Arab Emirates",
)
PRODUCT_CATALOG = (
    ("Electronics", ("Wireless Headphones", "Portable Speaker", "Desk Charger", "USB Hub")),
    ("Home & Kitchen", ("Storage Basket", "Coffee Grinder", "Desk Lamp", "Linen Set")),
    ("Clothing", ("Cotton Shirt", "Canvas Jacket", "Running Socks", "Wool Scarf")),
    ("Sports & Outdoors", ("Yoga Mat", "Trail Backpack", "Water Bottle", "Exercise Band")),
    ("Beauty", ("Skin Care Set", "Travel Kit", "Body Lotion", "Hair Brush")),
    ("Books", ("Travel Journal", "Cookbook", "Garden Guide", "Sketchbook")),
)


def _money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def _days_before(day: date, days: int) -> date:
    return date.fromordinal(max(1, day.toordinal() - days))


def _random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _validate_config(
    output_dir: Path,
    customers: int,
    orders: int,
    products: int,
    seed: int,
    as_of_date: date,
    inject_issues: bool,
) -> None:
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a pathlib.Path")
    for name, value in (("customers", customers), ("orders", orders), ("products", products)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(as_of_date) is not date:
        raise TypeError("as_of_date must be a datetime.date, not a datetime")
    if type(inject_issues) is not bool:
        raise TypeError("inject_issues must be a bool")
    if inject_issues and (
        customers < MIN_CUSTOMERS_WITH_ISSUES or orders < MIN_ORDERS_WITH_ISSUES or products < 1
    ):
        raise ValueError(
            "inject_issues=True requires at least 70 customers, 420 orders, and 1 product "
            "for disjoint faults and duplicate donors; use inject_issues=False for small fixtures"
        )
    if orders and (not customers or not products):
        raise ValueError("nonempty orders require at least 1 customer and 1 product")


def _products(count: int, rng: random.Random) -> tuple[list[dict[str, Any]], dict[int, int]]:
    rows = []
    prices = {}
    for product_id in range(1, count + 1):
        category, names = PRODUCT_CATALOG[(product_id - 1) % len(PRODUCT_CATALOG)]
        price = rng.randint(500, 29_999)
        cost = price * rng.randint(40, 80) // 100
        prices[product_id] = price
        rows.append({
            "product_id": product_id,
            "product_name": f"{rng.choice(names)} {product_id:04d}",
            "category": category,
            "price": _money(price),
            "cost": _money(cost),
            "stock_quantity": rng.randint(0, 500),
            "reorder_level": rng.randint(5, 60),
        })
    return rows, prices


def _customers(count: int, rng: random.Random, as_of_date: date) -> list[dict[str, Any]]:
    rows = []
    for customer_id in range(1, count + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        rows.append({
            "customer_id": customer_id,
            "customer_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}.{customer_id}@example.com",
            "country": rng.choice(COUNTRIES),
            "signup_date": _random_date(
                rng, _days_before(as_of_date, 730), _days_before(as_of_date, 366)
            ).isoformat(),
            "customer_segment": PERSONAS[(customer_id - 1) % len(PERSONAS)],
            "lifetime_value": "0.00",
        })
    return rows


def _inject_customer_issues(
    rows: list[dict[str, Any]], rng: random.Random,
) -> tuple[dict[str, Any], set[int]]:
    selected = rng.sample(range(len(rows)), MIN_CUSTOMERS_WITH_ISSUES)
    email_rows, recipients, donors = selected[:50], selected[50:60], selected[60:70]
    for index in email_rows:
        rows[index]["email"] = None
    replacements = []
    for recipient, donor in zip(recipients, donors):
        old_id, new_id = rows[recipient]["customer_id"], rows[donor]["customer_id"]
        rows[recipient]["customer_id"] = new_id
        rows[recipient]["customer_segment"] = rows[donor]["customer_segment"]
        replacements.append({
            "row_number": recipient + 2,
            "donor_row_number": donor + 2,
            "old_id": old_id,
            "new_id": new_id,
        })
    return {
        "null_email": {"row_numbers": [index + 2 for index in email_rows]},
        "duplicate_customer_id": {"replacements": replacements},
    }, {rows[index]["customer_id"] for index in selected}


def _orders(
    count: int,
    customer_rows: list[dict[str, Any]],
    prices: dict[int, int],
    rng: random.Random,
    as_of_date: date,
    bad_customer_ids: set[int],
) -> tuple[list[dict[str, Any]], int]:
    # Build references only after duplicate replacement: removed IDs must never leak into orders.
    personas = {row["customer_id"]: row["customer_segment"] for row in customer_rows}
    customer_ids, product_ids = sorted(personas), sorted(prices)
    baseline = []
    for customer_id in customer_ids:
        if customer_id in bad_customer_ids:
            continue
        segment = personas[customer_id]
        baseline.extend([customer_id] * (2 if segment == "Repeat" else int(segment != "Inactive")))
    rng.shuffle(baseline)
    baseline_count = min(count, len(baseline))
    completed_counts: dict[int, int] = defaultdict(int)
    revenue: dict[int, int] = defaultdict(int)
    rows = []
    for order_id in range(1, count + 1):
        is_baseline = order_id <= baseline_count
        customer_id = baseline[order_id - 1] if is_baseline else rng.choice(customer_ids)
        segment = personas[customer_id]
        product_id = rng.choice(product_ids)
        unit_price = prices[product_id]
        quantity = 1 if is_baseline else rng.randint(1, 5)
        if is_baseline and segment == "High-Value":
            quantity = (100_000 + unit_price - 1) // unit_price
        total_amount = quantity * unit_price
        status = "Completed" if is_baseline else rng.choices(
            ("Completed", "Pending", "Cancelled"), weights=(65, 23, 12), k=1,
        )[0]
        if status == "Completed" and (
            segment == "Inactive"
            or (segment == "One-Time" and completed_counts[customer_id] >= 1)
            or (segment in ("One-Time", "Repeat") and revenue[customer_id] + total_amount >= 100_000)
        ):
            status = rng.choice(("Pending", "Cancelled"))
        order_date = _random_date(rng, _days_before(as_of_date, 365), as_of_date)
        payment_date = None
        if status == "Completed" or rng.random() < 0.15:
            payment_date = (
                order_date + timedelta(days=rng.randint(0, min(5, (as_of_date - order_date).days)))
            ).isoformat()
        if status == "Completed":
            completed_counts[customer_id] += 1
            revenue[customer_id] += total_amount
        rows.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": order_date.isoformat(),
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": _money(unit_price),
            "total_amount": _money(total_amount),
            "order_status": status,
            "payment_date": payment_date,
        })
    for row in customer_rows:
        row["lifetime_value"] = _money(revenue[row["customer_id"]])
        # Source membership tiers are distinct from the personas driving completed sales.
        row["customer_segment"] = SOURCE_SEGMENT_BY_PERSONA[personas[row["customer_id"]]]
    return rows, baseline_count


def _inject_order_issues(
    rows: list[dict[str, Any]], rng: random.Random, customers: int, products: int,
    baseline_count: int,
) -> dict[str, Any]:
    # Protect persona-establishing sales whenever enough non-baseline rows are available.
    first_candidate = baseline_count if len(rows) - baseline_count >= MIN_ORDERS_WITH_ISSUES else 0
    selected = rng.sample(range(first_candidate, len(rows)), MIN_ORDERS_WITH_ISSUES)
    details: dict[str, Any] = {}
    offset = 0
    for name, field, count, orphan_start in (
        ("null_customer_id", "customer_id", 100, None),
        ("null_product_id", "product_id", 200, None),
        ("orphan_customer_id", "customer_id", 50, customers + 1),
        ("orphan_product_id", "product_id", 30, products + 1),
    ):
        indices = selected[offset:offset + count]
        for number, index in enumerate(indices):
            rows[index][field] = None if orphan_start is None else orphan_start + number
        details[name] = {"row_numbers": [index + 2 for index in indices]}
        offset += count
    recipients, donors = selected[offset:offset + 20], selected[offset + 20:offset + 40]
    replacements = []
    for recipient, donor in zip(recipients, donors):
        old_id, new_id = rows[recipient]["order_id"], rows[donor]["order_id"]
        rows[recipient]["order_id"] = new_id
        replacements.append({
            "row_number": recipient + 2,
            "donor_row_number": donor + 2,
            "old_id": old_id,
            "new_id": new_id,
        })
    details["duplicate_order_id"] = {"replacements": replacements}
    return details


def _csv_bytes(table: str, rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(FIELDS[table]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _check_output_files(output_dir: Path) -> None:
    if output_dir.is_symlink():
        raise FileExistsError(f"Refusing a symlink output directory: {output_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise FileExistsError(f"Output directory is not a directory: {output_dir}")
    targets = [output_dir / f"{table}.csv" for table in TABLES]
    manifest_path = output_dir / MANIFEST_NAME
    for path in [*targets, manifest_path]:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise FileExistsError(f"Refusing to overwrite a non-regular generated target: {path}")
    if not manifest_path.exists():
        if any(path.exists() for path in targets):
            raise FileExistsError("Existing CSV targets have no generation manifest; refusing overwrite")
        return
    try:
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        recognized = (
            isinstance(previous, dict)
            and previous.get("generator") == GENERATOR
            and previous.get("manifest_version") == MANIFEST_VERSION
            and isinstance(previous.get("files"), dict)
            and set(previous["files"]) == set(TABLES)
        )
        if not recognized:
            raise ValueError("unrecognized generation manifest")
        for table, path in zip(TABLES, targets):
            entry = previous["files"][table]
            if entry.get("path") != path.name:
                raise ValueError("unrecognized generated file path")
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
                raise ValueError(f"{path.name} was modified after generation")
    except (ValueError, TypeError, AttributeError) as exc:
        raise FileExistsError(f"Refusing to overwrite unknown or modified outputs: {exc}") from exc


def _write_outputs(output_dir: Path, payloads: dict[str, bytes]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for filename, content in payloads.items():
            destination = output_dir / filename
            pending = output_dir / f".{filename}.pending"
            with pending.open("xb") as handle:
                staged.append((pending, destination))
                handle.write(content)
        for pending, destination in staged:
            pending.replace(destination)
    finally:
        for pending, _ in staged:
            pending.unlink(missing_ok=True)


def generate_sample_data(
    output_dir: Path,
    *,
    customers: int = 10_000,
    orders: int = 100_000,
    products: int = 500,
    seed: int = SEED,
    as_of_date: date = AS_OF_DATE,
    inject_issues: bool = True,
) -> dict:
    """Write source CSVs and a reproducible manifest; refresh only recognized generated files.

    With injection enabled, sizes must be at least 70 customers, 420 orders, and 1 product.
    Counts include duplicate recipients: replacement never appends rows. Empty clean
    tables are supported, provided nonempty orders have both parent dimensions.
    """
    _validate_config(output_dir, customers, orders, products, seed, as_of_date, inject_issues)
    _check_output_files(output_dir)
    rng = random.Random(seed)
    product_rows, prices = _products(products, rng)
    customer_rows = _customers(customers, rng, as_of_date)
    injection_details: dict[str, Any] = {table: {} for table in TABLES}
    bad_customer_ids: set[int] = set()
    if inject_issues:
        injection_details["customers"], bad_customer_ids = _inject_customer_issues(customer_rows, rng)
    order_rows, baseline_count = _orders(
        orders, customer_rows, prices, rng, as_of_date, bad_customer_ids,
    )
    if inject_issues:
        injection_details["orders"] = _inject_order_issues(
            order_rows, rng, customers, products, baseline_count,
        )
    tables = {"customers": customer_rows, "orders": order_rows, "products": product_rows}
    payloads = {f"{table}.csv": _csv_bytes(table, tables[table]) for table in TABLES}
    counts = {
        table: {name: count if inject_issues else 0 for name, count in issues.items()}
        for table, issues in INJECTED_COUNTS.items()
    }
    manifest = {
        "generator": GENERATOR,
        "manifest_version": MANIFEST_VERSION,
        "config": {
            "customers": customers,
            "orders": orders,
            "products": products,
            "seed": seed,
            "as_of_date": as_of_date.isoformat(),
            "inject_issues": inject_issues,
        },
        "row_counts": {table: len(tables[table]) for table in TABLES},
        "files": {
            table: {
                "path": f"{table}.csv",
                "row_count": len(tables[table]),
                "size_bytes": len(payloads[f"{table}.csv"]),
                "sha256": hashlib.sha256(payloads[f"{table}.csv"]).hexdigest(),
            }
            for table in TABLES
        },
        "injected_counts": counts,
        "injected_events": sum(sum(issues.values()) for issues in counts.values()),
        "expected_direct_failing_rows": {
            "customers": 70 if inject_issues else 0,
            "orders": 420 if inject_issues else 0,
            "products": 0,
            "total": 490 if inject_issues else 0,
        },
        "injection_details": injection_details,
        "semantics": {
            "row_numbers": "One-based CSV physical line numbers, with the header on line 1.",
            "duplicate_events": (
                "Each event replaces one recipient ID with one distinct donor ID. "
                "Rows are not appended. Both members of every duplicated key fail uniqueness; "
                "donors and recipients are disjoint from all other same-table faults."
            ),
            "foreign_keys": (
                "Every non-null reference exists after customer ID replacement, except the "
                "50 explicit customer orphans and 30 explicit product orphans when injection is enabled. "
                "Parent quality is separate from parent-key existence."
            ),
            "direct_failures": (
                "Disjoint source-row failures: customer completeness 50, uniqueness 20; "
                "order completeness 300, referential integrity 80, uniqueness 40 when injected. "
                "Downstream order exclusions for invalid dimensions are additional, not injected events."
            ),
            "dates": (
                "Signup dates are 730 to 366 days before as_of_date; order dates cover its "
                "preceding 365 days through as_of_date. Bounds clamp at date.min. "
                "Payments, when present, are between the order date and as_of_date."
            ),
            "money": "Nonnegative integer-cent arithmetic serialized with exactly two decimal places.",
            "source_segments": (
                "Source customer_segment is Premium, Standard, or Basic. Internal High-Value "
                "personas map to Premium, Repeat to Standard, and One-Time/Inactive to Basic. "
                "Source tiers are distinct from Gold segments recalculated from eligible sales."
            ),
            "derived_personas": (
                "Balanced target personas use the 1000.00 High-Value threshold. "
                "Baseline completed sales establish personas when row counts permit; defects "
                "and small snapshots can change recomputed Gold segments. Source lifetime_value "
                "is completed snapshot revenue before order corruption, not historical revenue."
            ),
            "csv": "UTF-8, LF line endings, exact contract header order, empty cells represent null.",
            "refresh": (
                "Only files recognized by this generator's manifest with matching hashes are refreshed. "
                "The manifest is replaced last; the multi-file refresh is not transactional."
            ),
        },
    }
    payloads[MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    _write_outputs(output_dir, payloads)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--customers", type=int, default=10_000)
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--products", type=int, default=500)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=AS_OF_DATE)
    parser.add_argument("--no-inject-issues", action="store_true", help="Generate clean fixtures")
    args = parser.parse_args()
    try:
        manifest = generate_sample_data(
            args.output_dir, customers=args.customers, orders=args.orders, products=args.products,
            seed=args.seed, as_of_date=args.as_of_date, inject_issues=not args.no_inject_issues,
        )
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Generation failed: {exc}\n")
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "row_counts": manifest["row_counts"],
        "injected_events": manifest["injected_events"],
        "expected_direct_failing_rows": manifest["expected_direct_failing_rows"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

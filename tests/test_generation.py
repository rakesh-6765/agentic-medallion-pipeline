"""Generator contract tests; no Spark, network, or non-standard-library helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import unittest
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from medallion.contracts import AS_OF_DATE, FIELDS, TABLES
from medallion.data_generation.generate_sample_data import generate_sample_data


def _read_tables(directory: Path) -> dict[str, list[dict[str, str]]]:
    tables = {}
    for table in TABLES:
        with (directory / f"{table}.csv").open(encoding="utf-8", newline="") as handle:
            tables[table] = list(csv.DictReader(handle))
    return tables


def _duplicate_lines(rows: list[dict[str, str]], key: str) -> set[int]:
    counts = Counter(row[key] for row in rows)
    return {number for number, row in enumerate(rows, start=2) if counts[row[key]] > 1}


class TestGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.work = Path(__file__).resolve().parents[1] / "data" / f".generator-tests-{uuid4().hex}"
        cls.work.mkdir(parents=True)
        cls.addClassCleanup(shutil.rmtree, cls.work)
        cls.default_dir = cls.work / "default"
        cls.default_manifest = generate_sample_data(cls.default_dir)
        cls.tables = _read_tables(cls.default_dir)

    def output(self, name: str) -> Path:
        return self.work / self._testMethodName / name

    def assert_money(self, value: str) -> Decimal:
        self.assertIsNotNone(re.fullmatch(r"\d+\.\d{2}", value))
        result = Decimal(value)
        self.assertGreaterEqual(result, 0)
        return result

    def assert_business_rules(self, tables: dict[str, list[dict[str, str]]], as_of_date: date) -> None:
        signup_dates: dict[str, list[date]] = defaultdict(list)
        for row in tables["customers"]:
            signup = date.fromisoformat(row["signup_date"])
            signup_dates[row["customer_id"]].append(signup)
            self.assertLessEqual(signup, as_of_date)
            self.assert_money(row["lifetime_value"])
            self.assertIn(row["customer_segment"], {"Premium", "Standard", "Basic"})
            if row["email"]:
                self.assertTrue(row["email"].endswith("@example.com"))
            for field in FIELDS["customers"]:
                if field != "email":
                    self.assertTrue(row[field], field)
        product_prices = {}
        for row in tables["products"]:
            price, cost = self.assert_money(row["price"]), self.assert_money(row["cost"])
            self.assertGreaterEqual(price, cost)
            self.assertGreaterEqual(int(row["stock_quantity"]), 0)
            self.assertGreaterEqual(int(row["reorder_level"]), 0)
            product_prices[row["product_id"]] = price
            self.assertTrue(all(row[field] for field in FIELDS["products"]))
        for row in tables["orders"]:
            order_date = date.fromisoformat(row["order_date"])
            self.assertLessEqual(order_date, as_of_date)
            if row["customer_id"] in signup_dates:
                self.assertLessEqual(max(signup_dates[row["customer_id"]]), order_date)
            self.assertGreater(int(row["quantity"]), 0)
            unit_price, total = self.assert_money(row["unit_price"]), self.assert_money(row["total_amount"])
            self.assertEqual(total, int(row["quantity"]) * unit_price)
            if row["product_id"] in product_prices:
                self.assertEqual(unit_price, product_prices[row["product_id"]])
            self.assertIn(row["order_status"], ("Pending", "Completed", "Cancelled"))
            if row["order_status"] == "Completed":
                self.assertTrue(row["payment_date"])
            if row["payment_date"]:
                payment_date = date.fromisoformat(row["payment_date"])
                self.assertLessEqual(order_date, payment_date)
                self.assertLessEqual(payment_date, as_of_date)
            for field in FIELDS["orders"]:
                if field not in ("customer_id", "product_id", "payment_date"):
                    self.assertTrue(row[field], field)

    def test_full_default_counts_contract_and_manifest_hashes(self) -> None:
        manifest = self.default_manifest
        self.assertEqual(manifest["config"], {
            "customers": 10_000, "orders": 100_000, "products": 500,
            "seed": 42, "as_of_date": "2026-01-31", "inject_issues": True,
        })
        self.assertEqual(manifest["row_counts"], {"customers": 10_000, "orders": 100_000, "products": 500})
        self.assertEqual(manifest, json.loads(
            (self.default_dir / "generation-manifest.json").read_text(encoding="utf-8")
        ))
        for table in TABLES:
            with self.subTest(table=table):
                path = self.default_dir / f"{table}.csv"
                content = path.read_bytes()
                entry = manifest["files"][table]
                self.assertEqual(len(self.tables[table]), manifest["row_counts"][table])
                self.assertEqual(entry["row_count"], len(self.tables[table]))
                self.assertEqual(entry["size_bytes"], len(content))
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(entry["path"], path.name)
                self.assertNotIn(b"\r", content)
                self.assertEqual(content.split(b"\n", 1)[0].decode("utf-8").split(","), list(FIELDS[table]))
                self.assertTrue(content.endswith(b"\n"))
                self.assertTrue(all(set(row) == set(FIELDS[table]) for row in self.tables[table]))
        self.assertEqual(manifest["injected_counts"], {
            "customers": {"null_email": 50, "duplicate_customer_id": 10},
            "orders": {
                "null_customer_id": 100, "null_product_id": 200, "orphan_customer_id": 50,
                "orphan_product_id": 30, "duplicate_order_id": 20,
            },
            "products": {},
        })
        self.assertEqual(manifest["injected_events"], 460)
        self.assertEqual(manifest["expected_direct_failing_rows"], {
            "customers": 70, "orders": 420, "products": 0, "total": 490,
        })

    def test_exact_disjoint_faults_and_no_accidental_orphans(self) -> None:
        customers, orders, products = (self.tables[table] for table in TABLES)
        customer_ids = {row["customer_id"] for row in customers}
        product_ids = {row["product_id"] for row in products}
        faults = {
            "customers": {
                "null_email": {number for number, row in enumerate(customers, 2) if not row["email"]},
                "duplicate_customer_id": _duplicate_lines(customers, "customer_id"),
            },
            "orders": {
                "null_customer_id": {number for number, row in enumerate(orders, 2) if not row["customer_id"]},
                "null_product_id": {number for number, row in enumerate(orders, 2) if not row["product_id"]},
                "orphan_customer_id": {
                    number for number, row in enumerate(orders, 2)
                    if row["customer_id"] and row["customer_id"] not in customer_ids
                },
                "orphan_product_id": {
                    number for number, row in enumerate(orders, 2)
                    if row["product_id"] and row["product_id"] not in product_ids
                },
                "duplicate_order_id": _duplicate_lines(orders, "order_id"),
            },
        }
        details = self.default_manifest["injection_details"]
        for table, checks in faults.items():
            seen: set[int] = set()
            for name, lines in checks.items():
                with self.subTest(table=table, fault=name):
                    expected = self.default_manifest["injected_counts"][table][name]
                    self.assertEqual(len(lines), expected * (2 if name.startswith("duplicate") else 1))
                    self.assertFalse(seen & lines, "same-table fault rows must not overlap")
                    seen |= lines
                    if name.startswith("duplicate"):
                        replacements = details[table][name]["replacements"]
                        self.assertEqual(len(replacements), expected)
                        recorded = {
                            change[field] for change in replacements
                            for field in ("row_number", "donor_row_number")
                        }
                        key = "customer_id" if table == "customers" else "order_id"
                        values = Counter(row[key] for row in self.tables[table])
                        self.assertEqual({count for count in values.values() if count > 1}, {2})
                        for change in replacements:
                            self.assertEqual(
                                self.tables[table][change["row_number"] - 2][key], str(change["new_id"]),
                            )
                            self.assertEqual(
                                self.tables[table][change["donor_row_number"] - 2][key], str(change["new_id"]),
                            )
                            self.assertNotIn(str(change["old_id"]), values)
                            if table == "customers":
                                recipient = self.tables[table][change["row_number"] - 2]
                                donor = self.tables[table][change["donor_row_number"] - 2]
                                self.assertEqual(recipient["customer_segment"], donor["customer_segment"])
                                self.assertEqual(recipient["lifetime_value"], donor["lifetime_value"])
                    else:
                        recorded = set(details[table][name]["row_numbers"])
                    self.assertEqual(lines, recorded)
            self.assertEqual(len(seen), self.default_manifest["expected_direct_failing_rows"][table])
        removed_customer_ids = {
            str(change["old_id"])
            for change in details["customers"]["duplicate_customer_id"]["replacements"]
        }
        self.assertFalse(removed_customer_ids & {row["customer_id"] for row in orders})
        self.assertEqual(len(customer_ids), 9_990)
        self.assertEqual(len({row["order_id"] for row in orders}), 99_980)

    def test_full_default_business_rules(self) -> None:
        self.assert_business_rules(self.tables, AS_OF_DATE)
        self.assertEqual({row["order_status"] for row in self.tables["orders"]}, {
            "Pending", "Completed", "Cancelled",
        })
        self.assertTrue(any(not row["payment_date"] for row in self.tables["orders"]))
        self.assertTrue(any(
            row["payment_date"] and row["order_status"] != "Completed"
            for row in self.tables["orders"]
        ))

    def test_default_has_balanced_quality_eligible_segments(self) -> None:
        customers, orders = self.tables["customers"], self.tables["orders"]
        duplicate_customers = _duplicate_lines(customers, "customer_id")
        duplicate_orders = _duplicate_lines(orders, "order_id")
        valid_customer_ids = {
            row["customer_id"] for number, row in enumerate(customers, 2)
            if row["email"] and number not in duplicate_customers
        }
        product_ids = {row["product_id"] for row in self.tables["products"]}
        revenue: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        counts: Counter[str] = Counter()
        for number, row in enumerate(orders, 2):
            if (
                number not in duplicate_orders and row["customer_id"] in valid_customer_ids
                and row["product_id"] in product_ids and row["order_status"] == "Completed"
            ):
                revenue[row["customer_id"]] += Decimal(row["total_amount"])
                counts[row["customer_id"]] += 1
        segments: Counter[str] = Counter()
        for customer_id in valid_customer_ids:
            if revenue[customer_id] >= Decimal("1000.00"):
                segment = "High-Value"
            elif counts[customer_id] >= 2:
                segment = "Repeat"
            elif counts[customer_id] == 1:
                segment = "One-Time"
            else:
                segment = "Inactive"
            segments[segment] += 1
        self.assertEqual(set(segments), {"Inactive", "One-Time", "Repeat", "High-Value"})
        self.assertEqual(sum(segments.values()), 9_930)
        for count in segments.values():
            self.assertGreaterEqual(count, 2_400)
            self.assertLessEqual(count, 2_600)

    def test_source_segments_are_membership_tiers_not_gold_personas(self) -> None:
        customers = self.tables["customers"]
        self.assertEqual({row["customer_segment"] for row in customers}, {
            "Premium", "Standard", "Basic",
        })
        tiers_by_original_persona = ("Basic", "Basic", "Standard", "Premium")
        for row in customers:
            self.assertEqual(
                row["customer_segment"], tiers_by_original_persona[(int(row["customer_id"]) - 1) % 4],
            )
        output = self.output("clean-lifetime")
        generate_sample_data(output, customers=12, orders=60, products=6, inject_issues=False)
        clean = _read_tables(output)
        completed_revenue: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for row in clean["orders"]:
            if row["order_status"] == "Completed":
                completed_revenue[row["customer_id"]] += Decimal(row["total_amount"])
        for row in clean["customers"]:
            self.assertEqual(Decimal(row["lifetime_value"]), completed_revenue[row["customer_id"]])
            self.assertIn(row["customer_segment"], {"Premium", "Standard", "Basic"})

    def test_full_default_bytes_are_reproducible_and_rng_is_private(self) -> None:
        other = self.output("repeat")
        random_state = random.getstate()
        manifest = generate_sample_data(other)
        self.assertEqual(random.getstate(), random_state)
        self.assertEqual(manifest, self.default_manifest)
        for filename in ("customers.csv", "orders.csv", "products.csv", "generation-manifest.json"):
            self.assertEqual((other / filename).read_bytes(), (self.default_dir / filename).read_bytes())
        self.assertNotIn(str(other), (other / "generation-manifest.json").read_text(encoding="utf-8"))

    def test_refresh_is_identical_and_preserves_unrelated_files(self) -> None:
        output = self.output("refresh")
        first = generate_sample_data(output, customers=8, orders=20, products=4, inject_issues=False)
        sentinel = output / "owner-notes.txt"
        sentinel.write_text("not generated; preserve me", encoding="utf-8")
        original = {path.name: path.read_bytes() for path in output.iterdir()}
        second = generate_sample_data(output, customers=8, orders=20, products=4, inject_issues=False)
        self.assertEqual(first, second)
        self.assertEqual(original, {path.name: path.read_bytes() for path in output.iterdir()})
        changed = generate_sample_data(
            output, customers=9, orders=21, products=5, seed=99, inject_issues=False,
        )
        self.assertEqual(changed["row_counts"], {"customers": 9, "orders": 21, "products": 5})
        self.assertNotEqual(first["files"]["orders"]["sha256"], changed["files"]["orders"]["sha256"])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "not generated; preserve me")
        self.assertFalse(list(output.glob("*.pending")))
        self.assertFalse(list(output.glob(".*.pending")))

    def test_small_and_empty_clean_fixtures(self) -> None:
        for customers, orders, products in ((4, 4, 1), (1, 3, 1), (0, 0, 0), (3, 0, 0), (0, 0, 3)):
            with self.subTest(customers=customers, orders=orders, products=products):
                output = self.output(f"{customers}-{orders}-{products}")
                manifest = generate_sample_data(
                    output, customers=customers, orders=orders, products=products, inject_issues=False,
                )
                tables = _read_tables(output)
                self.assertEqual(manifest["row_counts"], {
                    "customers": customers, "orders": orders, "products": products,
                })
                self.assertEqual(manifest["injected_events"], 0)
                self.assertEqual(manifest["expected_direct_failing_rows"]["total"], 0)
                self.assertTrue(all(
                    count == 0 for issues in manifest["injected_counts"].values() for count in issues.values()
                ))
                self.assertEqual(manifest["injection_details"], {table: {} for table in TABLES})
                customer_ids = {row["customer_id"] for row in tables["customers"]}
                product_ids = {row["product_id"] for row in tables["products"]}
                self.assertTrue(all(
                    row["customer_id"] in customer_ids and row["product_id"] in product_ids
                    for row in tables["orders"]
                ))
                for table, key in (("customers", "customer_id"), ("orders", "order_id"), ("products", "product_id")):
                    self.assertEqual(len({row[key] for row in tables[table]}), len(tables[table]))
                    self.assertTrue(all(
                        row[field] for row in tables[table] for field in FIELDS[table]
                        if field != "payment_date"
                    ))
                self.assert_business_rules(tables, AS_OF_DATE)

    def test_minimum_injected_fixture_still_has_exact_failures(self) -> None:
        output = self.output("minimum")
        manifest = generate_sample_data(output, customers=70, orders=420, products=1)
        tables = _read_tables(output)
        self.assertEqual(manifest["injected_events"], 460)
        self.assertEqual(manifest["expected_direct_failing_rows"]["total"], 490)
        self.assertEqual(len(_duplicate_lines(tables["customers"], "customer_id")), 20)
        self.assertEqual(len(_duplicate_lines(tables["orders"], "order_id")), 40)
        customer_ids = {row["customer_id"] for row in tables["customers"]}
        product_ids = {row["product_id"] for row in tables["products"]}
        self.assertEqual(sum(
            bool(row["customer_id"]) and row["customer_id"] not in customer_ids for row in tables["orders"]
        ), 50)
        self.assertEqual(sum(
            bool(row["product_id"]) and row["product_id"] not in product_ids for row in tables["orders"]
        ), 30)
        self.assert_business_rules(tables, AS_OF_DATE)

    def test_custom_dates_including_python_boundaries(self) -> None:
        for as_of in (date(2000, 2, 29), date(2025, 6, 30), date.min, date.max):
            with self.subTest(as_of=as_of):
                output = self.output(as_of.isoformat())
                manifest = generate_sample_data(
                    output, customers=12, orders=60, products=6, as_of_date=as_of, inject_issues=False,
                )
                self.assertEqual(manifest["config"]["as_of_date"], as_of.isoformat())
                self.assert_business_rules(_read_tables(output), as_of)

    def test_invalid_sizes_and_types_are_rejected_before_writing(self) -> None:
        invalid = (
            {"customers": 69}, {"orders": 419}, {"products": 0}, {"customers": -1},
            {"orders": 1.5}, {"products": True}, {"seed": "42"}, {"inject_issues": "false"},
            {"as_of_date": "2026-01-31"}, {"as_of_date": datetime(2026, 1, 31)},
            {"customers": 0, "orders": 1, "products": 1, "inject_issues": False},
            {"customers": 1, "orders": 1, "products": 0, "inject_issues": False},
        )
        for index, config in enumerate(invalid):
            with self.subTest(config=config):
                output = self.output(str(index))
                with self.assertRaises((ValueError, TypeError)):
                    generate_sample_data(output, **config)
                self.assertFalse(output.exists())
        with self.assertRaises(TypeError):
            generate_sample_data("not-a-path", inject_issues=False)

    def test_unknown_modified_and_symlink_outputs_are_not_overwritten(self) -> None:
        config = {"customers": 4, "orders": 8, "products": 2, "inject_issues": False}
        unknown = self.output("unknown-csv")
        unknown.mkdir(parents=True)
        (unknown / "customers.csv").write_bytes(b"owner content\n")
        with self.assertRaises(FileExistsError):
            generate_sample_data(unknown, **config)
        self.assertEqual((unknown / "customers.csv").read_bytes(), b"owner content\n")
        self.assertEqual({path.name for path in unknown.iterdir()}, {"customers.csv"})

        malformed = self.output("unknown-manifest")
        malformed.mkdir()
        for content in (b"not json", b"[]", b"{}", b'{"generator": "another tool"}'):
            (malformed / "generation-manifest.json").write_bytes(content)
            with self.assertRaises(FileExistsError):
                generate_sample_data(malformed, **config)
            self.assertEqual((malformed / "generation-manifest.json").read_bytes(), content)

        modified = self.output("modified")
        generate_sample_data(modified, **config)
        (modified / "orders.csv").write_bytes(b"deliberately edited\n")
        before = {path.name: path.read_bytes() for path in modified.iterdir()}
        with self.assertRaises(FileExistsError):
            generate_sample_data(modified, **config)
        self.assertEqual(before, {path.name: path.read_bytes() for path in modified.iterdir()})

        symlinks = self.output("symlink")
        symlinks.mkdir()
        (symlinks / "customers.csv").symlink_to(unknown / "customers.csv")
        with self.assertRaises(FileExistsError):
            generate_sample_data(symlinks, **config)
        self.assertEqual((unknown / "customers.csv").read_bytes(), b"owner content\n")
        linked_directory = self.output("symlink-directory")
        linked_directory.symlink_to(unknown, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            generate_sample_data(linked_directory, **config)

    def test_pending_file_collision_preserves_unknown_file(self) -> None:
        output = self.output("collision")
        output.mkdir(parents=True)
        unknown_pending = output / ".orders.csv.pending"
        unknown_pending.write_bytes(b"owner content\n")
        with self.assertRaises(FileExistsError):
            generate_sample_data(output, customers=4, orders=8, products=2, inject_issues=False)
        self.assertEqual(unknown_pending.read_bytes(), b"owner content\n")
        self.assertEqual({path.name for path in output.iterdir()}, {unknown_pending.name})

    def test_cli_produces_small_clean_fixture(self) -> None:
        output = self.output("cli")
        result = subprocess.run(
            [
                sys.executable, "-m", "medallion.data_generation.generate_sample_data",
                "--output-dir", str(output), "--customers", "4", "--orders", "8", "--products", "2",
                "--seed", "7", "--as-of-date", "2024-02-29", "--no-inject-issues",
            ],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stderr, "")
        summary = json.loads(result.stdout)
        self.assertEqual(summary["row_counts"], {"customers": 4, "orders": 8, "products": 2})
        self.assertEqual(summary["injected_events"], 0)
        self.assert_business_rules(_read_tables(output), date(2024, 2, 29))

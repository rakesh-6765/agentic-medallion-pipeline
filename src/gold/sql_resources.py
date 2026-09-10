"""Strict substitution of trusted SQL resources, never arbitrary SQL fragments."""

from __future__ import annotations

from importlib.resources import files
import re
from typing import Mapping

_TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,15})\.[0-9]{2}")


def render_sql(
    package: str,
    resource: str,
    *,
    identifiers: Mapping[str, str],
    decimals: Mapping[str, str] | None = None,
) -> str:
    """Quote one-to-three-part identifiers and validate decimal-only literals.

    Callers select a bundled resource; replacement names must match its complete
    placeholder set exactly. Quotes, comments, SQL expressions and paths are not
    accepted as identifiers.
    """
    if package not in {"medallion.gold", "medallion.dashboard"}:
        raise ValueError("SQL must come from an approved package")
    allowed = {
        "medallion.gold": {
            "01_sales_by_product.sql",
            "02_revenue_by_customer.sql",
            "03_daily_weekly_trends.sql",
            "04_customer_segmentation.sql",
        },
        "medallion.dashboard": {"dashboard_queries.sql"},
    }
    if resource not in allowed[package]:
        raise ValueError("Unknown SQL resource")
    decimal_values = decimals or {}
    if identifiers.keys() & decimal_values.keys():
        raise ValueError("A replacement cannot be both identifier and decimal")
    resource_path = files(package).joinpath(resource)
    text = resource_path.read_text(encoding="utf-8")
    names = set(_TOKEN.findall(text))
    supplied = identifiers.keys() | decimal_values.keys()
    if names != supplied:
        raise ValueError(
            f"SQL replacement names must match placeholders exactly in {resource_path}. "
            f"Missing replacements: {sorted(names - supplied)}; "
            f"unexpected replacements: {sorted(supplied - names)}. "
            "Check the loaded SQL template and installed package; after updating "
            "a Databricks notebook installation, restart Python before importing again."
        )
    replacements = {}
    for name, identifier in identifiers.items():
        parts = identifier.split(".")
        if not 1 <= len(parts) <= 3 or not all(
            _IDENTIFIER.fullmatch(part) for part in parts
        ):
            raise ValueError(f"Unsafe SQL identifier for {name}")
        replacements[name] = ".".join(f"`{part}`" for part in parts)
    for name, value in decimal_values.items():
        if not _DECIMAL.fullmatch(value):
            raise ValueError(f"Unsafe SQL decimal for {name}")
        replacements[name] = value
    result = _TOKEN.sub(lambda match: replacements[match.group(1)], text)
    if "{{" in result or "}}" in result:
        raise ValueError("Malformed SQL placeholder")
    return result

"""Validated runtime configuration."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from medallion.contracts import AS_OF_DATE


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value


def money_threshold(value: str | Decimal) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("High-value threshold must be a decimal number") from exc
    if (
        not amount.is_finite()
        or amount <= 0
        or amount >= Decimal("10000000000000000")
        or amount.as_tuple().exponent < -2
    ):
        raise ValueError("High-value threshold must be positive DECIMAL(18,2)")
    return amount


@dataclass(frozen=True)
class PipelineConfig:
    source_dir: str
    as_of_date: date = AS_OF_DATE
    high_value_threshold: Decimal = Decimal("1000.00")

    def __post_init__(self) -> None:
        if not self.source_dir or not self.source_dir.strip():
            raise ValueError("source_dir must not be empty")
        if type(self.as_of_date) is not date:
            raise ValueError("as_of_date must be a date")
        if not isinstance(self.high_value_threshold, Decimal):
            raise ValueError("high_value_threshold must be a Decimal")
        money_threshold(self.high_value_threshold)

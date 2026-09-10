from decimal import Decimal
from datetime import datetime

import pytest

from medallion.config import PipelineConfig, identifier, money_threshold


@pytest.mark.parametrize("value", ["a;drop table x", "a.b", "a-b", "", "a`"])
def test_catalog_identifiers_reject_sql_fragments(value):
    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        identifier(value)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "0", "0.001", "1e20", "word"])
def test_invalid_thresholds_are_rejected(value):
    with pytest.raises(ValueError):
        money_threshold(value)


def test_configuration_validates_required_input():
    assert money_threshold("1000.00") == Decimal("1000")
    assert identifier("exercise_1") == "exercise_1"
    with pytest.raises(ValueError, match="source_dir"):
        PipelineConfig(" ")


def test_configuration_rejects_timestamp_as_date_and_untyped_money():
    with pytest.raises(ValueError, match="as_of_date"):
        PipelineConfig("data", as_of_date=datetime(2026, 1, 31))
    with pytest.raises(ValueError, match="must be a Decimal"):
        PipelineConfig("data", high_value_threshold="1000")

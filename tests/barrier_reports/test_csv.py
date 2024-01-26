import datetime
from decimal import Decimal

import pytest

from barrier_reports.csv import _transform_csv_value


@pytest.mark.parametrize(
    "value,expected_value",
    (
        (
            Decimal("2000000000000000000000000000000000000"),
            "2000000000000000000000000000000000000",
        ),
        (
            Decimal("200.00"),
            "200",
        ),
        (
            Decimal("200.0"),
            "200",
        ),
        (
            Decimal("200.8919"),
            "200.8919",
        ),
        (
            datetime.datetime(2010, 1, 1, 3, 3, 3),
            "2010-01-01",
        ),
        (
            1000,
            1000,
        ),
        (
            float(1000),
            float(1000),
        ),
        (
            "HELLO",
            "HELLO",
        ),
        (
            ["a", "b", "c"],
            "a; b; c",
        ),
        (
            ["a"],
            "a",
        ),
    ),
)
def test_transform_csv_value(value, expected_value):
    """Test transform csv value"""
    assert _transform_csv_value(value) == expected_value

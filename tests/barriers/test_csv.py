import datetime
from decimal import Decimal

import pytest

from api.barriers.csv import INCOMPLETE_CSV_MESSAGE, _transform_csv_value, csv_iterator


def _rows():
    for i in range(10):
        yield {"id": i}

    raise ValueError


def test_csv_iterator_with_error():
    """
    Tests that an error is appended to the CSV data is an error occurs during generation.

    This is as if the CSV data is being used as part of a streamed HTTP response, it will be to
    late to return an error status.
    """
    row = None

    with pytest.raises(ValueError):
        for row in csv_iterator(_rows(), {"id": "id"}):
            pass

    assert row == INCOMPLETE_CSV_MESSAGE


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

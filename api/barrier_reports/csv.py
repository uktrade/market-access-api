from datetime import datetime
from decimal import Decimal


def _transform_csv_row(row):
    return {key: _transform_csv_value(val) for key, val in row.items()}


def _transform_csv_value(value):
    """
    Transforms values before they are written to a CSV file for better compatibility with Excel.

    In particular, datetimes are formatted in a way that results in better compatibility with
    Excel. Lists are converted to comma separated strings. Other values are passed through
    unchanged (the csv module automatically formats None as an empty string).

    These transformations are specific to CSV files and won't necessarily apply to other file
    formats.
    """
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        normalized_value = value.normalize()
        return f"{normalized_value:f}"
    if isinstance(value, list):
        return "; ".join(str(x) for x in value)
    return value
